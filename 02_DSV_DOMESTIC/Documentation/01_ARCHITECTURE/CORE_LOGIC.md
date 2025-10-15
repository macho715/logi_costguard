# 시스템 핵심 로직 (Core Logic)

**프로젝트**: 9월 2025 DSV Domestic Invoice 검증 시스템
**버전**: PATCH4 (v4.0)
**작성일**: 2025-10-13

---

## 📚 목차

1. [Enhanced Lane Matching](#1-enhanced-lane-matching)
2. [PDF 텍스트 추출](#2-pdf-텍스트-추출)
3. [PDF 필드 추출](#3-pdf-필드-추출)
4. [1:1 그리디 매칭](#4-11-그리디-매칭-알고리즘)
5. [DN Capacity 시스템](#5-dn-capacity-시스템)
6. [유사도 계산](#6-유사도-계산)
7. [검증 상태 분류](#7-검증-상태-분류)
8. [미매칭 사유 분류](#8-미매칭-사유-분류)

---

## 1. Enhanced Lane Matching

### 개요
인보이스 항목을 ApprovedLaneMap의 124개 레인과 매칭하는 4-level fallback 시스템

### 알고리즘

```python
def find_matching_lane_enhanced(item, lane_map, config):
    """
    4-level fallback 매칭 시스템

    Args:
        item: 인보이스 항목 (origin, destination, vehicle)
        lane_map: ApprovedLaneMap (124 레인)
        config: 설정 (임계값 등)

    Returns:
        (matched_lane, match_level) or (None, "No Match")
    """

    # Level 1: Exact Match (100% 일치)
    for lane in lane_map:
        if (normalize(item.origin) == normalize(lane.origin) and
            normalize(item.destination) == normalize(lane.destination) and
            normalize(item.vehicle) == normalize(lane.vehicle)):
            return lane, "Exact"

    # Level 2: Similarity Match (≥0.65)
    best_lane = None
    best_score = 0.65  # 임계값

    for lane in lane_map:
        origin_sim = hybrid_similarity(item.origin, lane.origin)
        dest_sim = hybrid_similarity(item.destination, lane.destination)
        vehicle_sim = hybrid_similarity(item.vehicle, lane.vehicle)

        # 가중 평균
        score = (origin_sim * 0.4 + dest_sim * 0.4 + vehicle_sim * 0.2)

        if score > best_score:
            best_score = score
            best_lane = lane

    if best_lane:
        return best_lane, "Similarity"

    # Level 3: Region Match (권역별)
    item_region = get_region(item.destination)
    for lane in lane_map:
        if (normalize(item.origin) == normalize(lane.origin) and
            get_region(lane.destination) == item_region):
            return lane, "Region"

    # Level 4: Vehicle Type Match (차량 타입)
    vehicle_cat = get_vehicle_category(item.vehicle)
    for lane in lane_map:
        if (normalize(item.origin) == normalize(lane.origin) and
            get_vehicle_category(lane.vehicle) == vehicle_cat):
            return lane, "Vehicle"

    return None, "No Match"
```

### 정규화 (Normalization)

```python
def normalize_location(s: str) -> str:
    """
    위치명 정규화

    Steps:
    1. 대문자 변환
    2. 특수문자 제거
    3. 공백 정리
    4. 불용어 제거 (CICPA, PMO)
    """
    s = s.upper()
    s = re.sub(r"[^A-Z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    stopwords = {"CICPA", "PMO"}
    tokens = [t for t in s.split() if t not in stopwords]

    return " ".join(tokens)
```

### 성과
- 매칭률: **79.5%** (35/44)
- Level 분포:
  - Exact: 20.5%
  - Similarity: 13.6%
  - Region: 31.8%
  - Vehicle: 13.6%
  - No Match: 20.5%

---

## 2. PDF 텍스트 추출

### 다층 폴백 시스템

```python
def extract_text_any(pdf_path: str) -> str:
    """
    4-layer fallback PDF 텍스트 추출

    Priority:
    1. PyMuPDF (fitz) - 가장 빠르고 안정적
    2. pypdf - 경량, 빠름
    3. pdfminer.six - 복잡한 레이아웃
    4. pdftotext - 외부 도구

    Returns:
        추출된 텍스트 (실패 시 빈 문자열)
    """
    pdf_path = str(pdf_path)

    for extractor in [_try_pymupdf, _try_pypdf,
                      _try_pdfminer, _try_pdftotext]:
        text = extractor(pdf_path)
        if text and text.strip():
            return text

    return ""
```

### PyMuPDF 추출 (PATCH4)

```python
def _try_pymupdf(pdf_path: str) -> str:
    """
    PyMuPDF를 사용한 텍스트 추출

    장점:
    - 15~35배 빠름
    - 다단 레이아웃 보존 우수
    - 표 혼합 문서 안정적
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        texts = []

        for page in doc:
            try:
                # 레이아웃 보존 모드
                t = page.get_text("text") or ""
                if not t.strip():
                    t = page.get_text() or ""
                texts.append(t)
            except Exception:
                continue

        doc.close()
        return "\n".join(texts)
    except Exception:
        return ""
```

### 성과
- 파싱 성공률: **91.7%** (33/36)
- 평균 추출 시간: 0.5초/파일 (PyMuPDF)
- 실패 3건: 텍스트 없음 (스캔 PDF 가능성)

---

## 3. PDF 필드 추출

### Destination 추출

```python
def extract_destination_from_text(raw_text: str) -> str:
    """
    PDF 본문에서 Destination 추출

    Strategy:
    "Destination:" 필드명의 **이전 줄**에서 값 추출
    (PDF 레이아웃 분석 결과 기반)
    """
    lines = raw_text.split("\n")

    for i, line in enumerate(lines):
        if "Destination:" in line and i > 0:
            # 이전 줄에서 값 추출
            prev_line = lines[i - 1].strip()

            # 필터링: 헤더/메타데이터 제외
            if any(x in prev_line.upper() for x in [
                "OFFLOADING", "ISSUED BY", "NOT NEGOTIABLE"
            ]):
                continue

            if prev_line:
                return expand_location_abbrev(prev_line)

    return ""
```

### Loading Point (Origin) 추출

```python
def extract_loading_point_from_text(raw_text: str) -> str:
    """
    Description 섹션에서 키워드 기반 추출

    Keywords:
    - MOSB, MIRFA, SHUWEIHAT, DSV, PRESTIGE, SAMSUNG, etc.
    """
    # Description 섹션 추출
    desc_match = re.search(
        r"Description[:\s]+(.{10,300})",
        raw_text,
        re.IGNORECASE | re.DOTALL
    )

    if not desc_match:
        return ""

    desc = desc_match.group(1)

    # 키워드 검색
    keywords = [
        "MOSB", "MIRFA", "SHUWEIHAT", "DSV", "PRESTIGE",
        "SAMSUNG", "AGILITY", "HAULER", "SAS", "MUSSAFAH"
    ]

    for kw in keywords:
        if kw in desc.upper():
            # 주변 문맥 추출 (±20자)
            idx = desc.upper().find(kw)
            context = desc[max(0, idx-20):idx+len(kw)+20]

            # "yard" 등 추가 정보 결합
            if "yard" in desc[idx:idx+30].lower():
                context += " YARD"

            return expand_location_abbrev(context)

    return ""
```

### 약어 확장

```python
def expand_location_abbrev(s: str) -> str:
    """
    약어를 전체 이름으로 확장

    Mappings (16개):
    - DSV → DSV MUSSAFAH
    - MOSB → SAMSUNG MOSB
    - MIR/MIRFA → MIRFA PMO SAMSUNG
    - PRE → AGILITY M44 WAREHOUSE
    - SHU/SHUWEIHAT → SHUWEIHAT
    - etc.
    """
    s_norm = normalize_location(s)

    patterns = {
        r"^DSV$": "DSV MUSSAFAH",
        r"^MOSB$": "SAMSUNG MOSB",
        r"^(MIR|MIRFA)$": "MIRFA PMO SAMSUNG",
        r"^PRE$": "AGILITY M44 WAREHOUSE",
        r"^(SHU|SHUWEIHAT)$": "SHUWEIHAT",
        # ... 11 more
    }

    for pattern, canonical in patterns.items():
        if re.match(pattern, s_norm):
            return canonical

    return s_norm
```

### 성과
- Destination 추출 정확도: **97.1%** (유사도 기준)
- Origin 추출 정확도: **47.3%** (복잡한 텍스트)
- Vehicle 추출 정확도: **98.5%**

---

## 4. 1:1 그리디 매칭 알고리즘

### 개요
각 DN을 최대 1개 인보이스와 매칭 (capacity 기반 확장 가능)

### 알고리즘

```python
def cross_validate_invoice_dn(items_df, dns, config):
    """
    1:1 그리디 매칭

    Steps:
    1. 모든 (invoice, DN) 쌍의 점수 계산
    2. 점수 기준 내림차순 정렬
    3. 그리디 할당 (capacity 존중)
    """

    # Step 1: 점수 계산
    candidates = []
    for i, item in items_df.iterrows():
        for j, dn in enumerate(dns):
            score = calculate_match_score(item, dn)

            if score >= config.DN_MIN_SCORE:
                candidates.append({
                    "invoice_idx": i,
                    "dn_idx": j,
                    "score": score
                })

    # Step 2: 정렬
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Step 3: 그리디 할당
    dn_capacity = {j: dn.capacity for j, dn in enumerate(dns)}
    assigned = {}

    for cand in candidates:
        i = cand["invoice_idx"]
        j = cand["dn_idx"]

        # 이미 할당되었거나 capacity 소진
        if i in assigned or dn_capacity[j] <= 0:
            continue

        # 할당
        assigned[i] = j
        dn_capacity[j] -= 1

    return assigned
```

### 점수 계산

```python
def calculate_match_score(item, dn):
    """
    매칭 점수 계산

    Formula:
    score = 0.45 * origin_sim + 0.45 * dest_sim + 0.10 * vehicle_sim

    Weight 설명:
    - Origin: 45% (중요)
    - Destination: 45% (중요)
    - Vehicle: 10% (보조)
    """
    origin_sim = token_set_jaccard(
        normalize_location(item.origin),
        normalize_location(dn.origin)
    )

    dest_sim = token_set_jaccard(
        normalize_location(item.destination),
        normalize_location(dn.destination)
    )

    vehicle_sim = token_set_jaccard(
        normalize_vehicle(item.vehicle),
        normalize_vehicle(dn.vehicle)
    )

    score = 0.45 * origin_sim + 0.45 * dest_sim + 0.10 * vehicle_sim

    return score
```

### 성과
- 매칭률: **95.5%** (42/44)
- 평균 점수: 0.59 (매칭된 항목)
- Capacity 활용률: 100% (gap=0)

---

## 5. DN Capacity 시스템

### Auto-Bump (자동 용량 증가)

```python
def auto_capacity_bump(dn_list, top_choice_counts):
    """
    수요 기반 자동 용량 증가

    Logic:
    1. 각 DN의 "Top-1 선택 횟수" (수요) 파악
    2. 수요 > 1이면 capacity를 수요만큼 증가
    3. 상한: DN_MAX_CAPACITY (기본 16)
    4. 수동 오버라이드는 존중
    """
    if not os.getenv("DN_AUTO_CAPACITY_BUMP") == "true":
        return

    max_cap = int(os.getenv("DN_MAX_CAPACITY", "16"))

    for j, dn in enumerate(dn_list):
        # 수동 오버라이드 존중
        if dn.capacity > 1:
            continue

        # 수요 확인
        demand = top_choice_counts.get(j, 0)

        if demand > 1:
            dn.capacity = min(demand, max_cap)
```

### 수동 오버라이드

```python
def apply_capacity_overrides(dn_list, mapping):
    """
    수동 capacity 설정

    Mapping Format:
    {
        "HVDC-ADOPT-SCT-0126": 16,
        "HVDC-DSV-PRE-MIR-SHU-230": 7
    }

    Match Method:
    - 부분 일치 (shipment_ref 또는 filename)
    - 정규식 지원
    """
    for dn in dn_list:
        ref = dn.shipment_ref
        name = dn.filename

        for pattern, cap in mapping.items():
            if pattern in ref or pattern in name:
                dn.capacity = cap
                break
```

### 성과 (PATCH4)
- 모든 DN gap=0 (100% 수요 충족)
- HVDC-ADOPT-SCT-0126: 수요 24 → capacity 24 ✅
- HVDC-DSV-PRE-MIR-214: 수요 9 → capacity 9 ✅
- DN_CAPACITY_EXHAUSTED: 12건 → 0건 (-100%)

---

## 6. 유사도 계산

### Token-Set Jaccard

```python
def token_set_jaccard(a: str, b: str) -> float:
    """
    토큰 집합 기반 Jaccard 유사도

    Formula:
    J(A, B) = |A ∩ B| / |A ∪ B|

    장점:
    - 순서 무관
    - 부분 일치 지원
    - 빠름 (O(n))
    """
    A = set(a.split())
    B = set(b.split())

    if not A or not B:
        return 0.0

    intersection = len(A & B)
    union = len(A | B)

    return intersection / union
```

### Hybrid Similarity

```python
def hybrid_similarity(a: str, b: str) -> float:
    """
    3가지 알고리즘 결합

    Weights:
    - Token-Set: 40%
    - Levenshtein: 30%
    - Fuzzy Token Sort: 30%
    """
    token_set = token_set_jaccard(a, b) * 0.4

    levenshtein = (1 - levenshtein_distance(a, b) / max(len(a), len(b))) * 0.3

    fuzzy = fuzzy_token_sort(a, b) / 100.0 * 0.3

    return token_set + levenshtein + fuzzy
```

### 성과
- Destination 평균 유사도: **0.971**
- Vehicle 평균 유사도: **0.985**
- Origin 평균 유사도: 0.473

---

## 7. 검증 상태 분류

### PASS/WARN/FAIL 기준

```python
def classify_validation_status(origin_sim, dest_sim, vehicle_sim):
    """
    검증 상태 분류

    PASS: 모든 필드가 임계값 충족
    WARN: 일부만 충족
    FAIL: 모두 미충족
    """
    origin_pass = origin_sim >= config.DN_ORIGIN_THR    # 0.27
    dest_pass = dest_sim >= config.DN_DEST_THR          # 0.50
    vehicle_pass = vehicle_sim >= config.DN_VEH_THR     # 0.30

    pass_count = sum([origin_pass, dest_pass, vehicle_pass])

    if pass_count == 3:
        return "PASS"
    elif pass_count >= 1:
        return "WARN"
    else:
        return "FAIL"
```

### 임계값 설정 근거

| 필드 | 임계값 | 근거 |
|------|--------|------|
| **Origin** | 0.27 | 낮은 추출 정확도 고려 |
| **Destination** | 0.50 | 높은 추출 정확도 (97.1%) |
| **Vehicle** | 0.30 | 보조 지표 |

### 성과
- PASS: 47.7% (21/44)
- WARN: 47.7% (21/44)
- FAIL: 0% (0/44) ✅

---

## 8. 미매칭 사유 분류

### 분류 로직

```python
def classify_unmatched_reason(item, candidates, top_choice_counts):
    """
    미매칭 사유 3가지 분류

    1. DN_CAPACITY_EXHAUSTED: 점수는 충분하나 capacity 소진
    2. BELOW_MIN_SCORE: 최고 점수가 임계값 미만
    3. NO_CANDIDATES: 유효한 DN 후보 없음
    """
    valid_candidates = [c for c in candidates if c.score >= DN_MIN_SCORE]

    if valid_candidates:
        # 유효 후보 있지만 미매칭 → capacity 소진
        return "DN_CAPACITY_EXHAUSTED"
    else:
        # 유효 후보 없음
        best_score = max([c.score for c in candidates], default=0.0)

        if best_score < DN_MIN_SCORE:
            return "BELOW_MIN_SCORE"
        else:
            return "NO_CANDIDATES"
```

### 통계 (PATCH4)

| 사유 | Before (PATCH3) | After (PATCH4) | 변화 |
|------|----------------|----------------|------|
| **DN_CAPACITY_EXHAUSTED** | 12건 (85.7%) | **0건** | **-100%** 🎉 |
| **BELOW_MIN_SCORE** | 2건 (14.3%) | 2건 | 유지 |
| **NO_CANDIDATES** | 0건 | 0건 | 유지 |

---

## 🎯 알고리즘 성능 요약

| 알고리즘 | 시간 복잡도 | 공간 복잡도 | 성과 |
|----------|------------|------------|------|
| **Enhanced Lane Matching** | O(N×M) | O(M) | 79.5% |
| **PDF 텍스트 추출** | O(P) | O(T) | 91.7% |
| **1:1 그리디 매칭** | O(N×M×log(N×M)) | O(N×M) | 95.5% |
| **Token-Set Jaccard** | O(n) | O(n) | 0.971 |
| **Auto-Bump** | O(M) | O(M) | gap=0 |

- N: 인보이스 수 (44)
- M: DN 수 (33) 또는 Lane 수 (124)
- P: PDF 페이지 수
- T: 텍스트 길이
- n: 토큰 수

---

**문서 버전**: 1.0
**작성일**: 2025-10-13 22:45:00
**Status**: ✅ Complete

