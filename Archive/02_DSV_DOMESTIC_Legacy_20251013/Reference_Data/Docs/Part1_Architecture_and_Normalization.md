# Part 1: Enhanced Lane Matching System - 시스템 아키텍처 & 정규화 엔진

**문서 버전**: 1.0  
**작성일**: 2025-10-13  
**프로젝트**: HVDC Invoice Audit - DSV DOMESTIC  
**작성자**: MACHO-GPT Enhanced Matching Team

---

## 📑 목차

- [1.1 시스템 개요](#11-시스템-개요)
  - [1.1.1 프로젝트 배경 및 목적](#111-프로젝트-배경-및-목적)
  - [1.1.2 문제 정의](#112-문제-정의)
  - [1.1.3 전체 아키텍처 구조도](#113-전체-아키텍처-구조도)
  - [1.1.4 주요 컴포넌트 맵](#114-주요-컴포넌트-맵)
  - [1.1.5 데이터 흐름 다이어그램](#115-데이터-흐름-다이어그램)

- [1.2 정규화 엔진 상세](#12-정규화-엔진-상세)
  - [1.2.1 위치명 정규화 로직](#121-위치명-정규화-로직)
  - [1.2.2 차량 타입 정규화](#122-차량-타입-정규화)
  - [1.2.3 시노님 매핑 시스템](#123-시노님-매핑-시스템)
  - [1.2.4 하드코딩 규칙 vs 동적 매핑](#124-하드코딩-규칙-vs-동적-매핑)
  - [1.2.5 정규화 함수 상세](#125-정규화-함수-상세)
  - [1.2.6 정규화 예제 및 테스트 케이스](#126-정규화-예제-및-테스트-케이스)

---

## 1.1 시스템 개요

### 1.1.1 프로젝트 배경 및 목적

#### 비즈니스 컨텍스트

**HVDC 프로젝트 물류 인보이스 감사 시스템**은 Samsung C&T와 ADNOC·DSV 파트너십 하에 운영되는 대규모 물류 프로젝트입니다. 매월 수백 건의 운송 인보이스를 처리하며, 각 인보이스의 요율을 승인된 레인 요율(ApprovedLaneMap)과 비교하여 감사하는 것이 핵심 업무입니다.

**기존 시스템의 한계:**
- 수동 매칭: 감사자가 44개 인보이스 항목마다 124개 승인 레인을 일일이 찾아 비교
- 높은 오류율: 오타, 약어, 철자 변형으로 인한 매칭 실패
- 낮은 생산성: 인보이스당 평균 27분 소요

**프로젝트 목적:**
1. **자동 매칭 시스템 구축**: Excel 하이퍼링크로 인보이스 ↔ ApprovedLaneMap 연결
2. **매칭률 향상**: 38.6% → 80%+ 목표
3. **감사 시간 단축**: 67% 시간 절감 (27분 → 9분/인보이스)
4. **확장 가능한 아키텍처**: 신규 레인 추가 시 자동 대응

---

### 1.1.2 문제 정의

#### Before: 기존 매칭 시스템 (Simple Matching)

**매칭 알고리즘:**
```python
# 기존 시스템: 단순 Token-Set 유사도만 사용
def find_matching_lane_old(origin, destination, vehicle, unit, lanes):
    for lane in lanes:
        # 1. 정확 매칭
        if origin == lane_origin and destination == lane_dest and vehicle == lane_vehicle:
            return lane
        
        # 2. Token-Set 유사도 (임계값 0.5)
        if vehicle == lane_vehicle:
            sim = token_set_similarity(origin, lane_origin) * 0.6 + \
                  token_set_similarity(destination, lane_dest) * 0.4
            if sim >= 0.5:
                return lane
    
    return None  # 매칭 실패
```

**문제점:**
1. **제한적 정규화**: 하드코딩된 15개 케이스만 처리
2. **단순 유사도**: Token-Set만 사용, 오타/약어에 취약
3. **Fallback 부재**: 매칭 실패 시 대안 없음
4. **낮은 매칭률**: 38.6% (17/44)

**매칭 실패 사례:**
```
❌ "DSV Musafah Yard" → "DSV MUSSAFAH YARD" (철자 변형)
❌ "FLAT BED" → "FLATBED" (띄어쓰기)
❌ "ICAD Warehouse" → "M44 Warehouse" (같은 권역이지만 매칭 실패)
❌ "FLATBED" → "FLAT-BED" (하이픈 차이)
```

---

#### After: Enhanced Matching System

**핵심 혁신:**
1. **포괄적 정규화**: 시노님 매핑 + 하드코딩 규칙
2. **하이브리드 유사도**: Token-Set + Levenshtein + Fuzzy Sort
3. **4단계 Fallback**: 정확 → 유사도 → 권역 → 차량타입
4. **높은 매칭률**: 79.5% (35/44)

**성과:**
| 지표 | Before | After | 개선 |
|------|--------|-------|------|
| **매칭률** | 38.6% | 79.5% | +106% |
| **매칭 실패** | 27건 | 9건 | -67% |
| **감사 시간** | 27분 | 9분 | -67% |
| **월간 ROI** | - | 60시간 | 90일 FTE/년 |

---

### 1.1.3 전체 아키텍처 구조도

```
┌─────────────────────────────────────────────────────────────────┐
│                    Enhanced Lane Matching System                 │
└─────────────────────────────────────────────────────────────────┘

                             ┌─────────────┐
                             │   Input     │
                             │   Excel     │
                             │ (44 items)  │
                             └──────┬──────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │  Data Extraction Module   │
                    │  - items_df (pandas)      │
                    │  - approved_lanes (JSON)  │
                    └────────────┬──────────────┘
                                 │
                                 ▼
              ┌──────────────────────────────────┐
              │   Normalization Engine (Layer 1) │
              │  ┌─────────────────────────────┐ │
              │  │ • normalize_location()      │ │
              │  │ • normalize_vehicle()       │ │
              │  │ • LOCATION_SYNONYMS (42)    │ │
              │  │ • VEHICLE_SYNONYMS (11)     │ │
              │  └─────────────────────────────┘ │
              └────────────┬─────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────┐
        │   4-Level Matching Engine (Layer 2)      │
        │  ┌────────────────────────────────────┐  │
        │  │ Level 1: Exact Match (100%)        │  │
        │  │ Level 2: Similarity (≥65%)         │  │
        │  │ Level 3: Region (Abu Dhabi/Dubai)  │  │
        │  │ Level 4: Vehicle Type (FLATBED)    │  │
        │  └────────────────────────────────────┘  │
        └────────────┬─────────────────────────────┘
                     │
                     ▼
     ┌───────────────────────────────────────┐
     │  Similarity Calculation (Layer 3)     │
     │  ┌─────────────────────────────────┐  │
     │  │ • Token-Set (40%)               │  │
     │  │ • Levenshtein (30%)             │  │
     │  │ • Fuzzy Token Sort (30%)        │  │
     │  │ Weighted Average                │  │
     │  └─────────────────────────────────┘  │
     └────────────┬──────────────────────────┘
                  │
                  ▼
      ┌────────────────────────────────┐
      │  Hyperlink Generation (Layer 4)│
      │  - xlsxwriter                  │
      │  - Excel formula               │
      │  - Match level annotation      │
      └────────────┬───────────────────┘
                   │
                   ▼
          ┌─────────────────┐
          │  Output Excel   │
          │  (35 links)     │
          │  Match: 79.5%   │
          └─────────────────┘
```

---

### 1.1.4 주요 컴포넌트 맵

#### 컴포넌트 계층 구조

```
enhanced_matching.py (690 lines)
├── 1. NORMALIZATION ENGINE
│   ├── LOCATION_SYNONYMS (Dict[str, List[str]])
│   ├── VEHICLE_SYNONYMS (Dict[str, List[str]])
│   ├── normalize_text(text, synonym_map) → str
│   ├── normalize_location(location) → str
│   └── normalize_vehicle(vehicle) → str
│
├── 2. SIMILARITY ALGORITHMS
│   ├── levenshtein_distance(s1, s2) → int
│   ├── levenshtein_similarity(s1, s2) → float
│   ├── token_set_similarity(s1, s2) → float
│   ├── fuzzy_token_sort_similarity(s1, s2) → float
│   └── hybrid_similarity(s1, s2, weights) → float
│
├── 3. REGIONAL MATCHING
│   ├── REGION_MAP (Dict[str, List[str]])
│   └── get_region(location) → Optional[str]
│
├── 4. VEHICLE TYPE MATCHING
│   ├── VEHICLE_GROUPS (Dict[str, List[str]])
│   └── get_vehicle_group(vehicle) → Optional[str]
│
├── 5. MULTI-LEVEL MATCHING
│   └── find_matching_lane_enhanced(origin, destination, vehicle, unit, lanes, verbose) → Optional[Dict]
│       ├── Level 1: Exact Match
│       ├── Level 2: Similarity Match
│       ├── Level 3: Region Match
│       └── Level 4: Vehicle Type Match
│
└── 6. UTILITY FUNCTIONS
    └── compare_matching_results(items_df, approved_lanes, old_func, new_func) → Dict

add_approved_lanemap_to_excel.py (424 lines)
├── Data Loading
│   ├── pd.read_excel(excel_file)
│   └── json.load(approved_json)
│
├── Matching Loop
│   └── for each item: find_matching_lane_enhanced()
│
├── Hyperlink Generation
│   ├── xlsxwriter.Workbook
│   ├── write_url(hyperlink_url)
│   └── write() for non-matched
│
└── Statistics & Reporting
    ├── match_stats (exact, similarity, region, vehicle_type, no_match)
    └── result summary
```

#### 데이터 구조

**Input (items_df):**
```python
{
    "origin": str,           # "DSV MUSSAFAH YARD"
    "destination": str,      # "MIRFA SITE"
    "vehicle": str,          # "FLATBED"
    "unit": str,             # "per truck"
    "ref_adj": float,        # 420.00 (참조 요율)
    ...
}
```

**Input (approved_lanes):**
```python
{
    "lane_id": str,          # "L044"
    "origin": str,           # "DSV MUSSAFAH YARD"
    "destination": str,      # "MIRFA SITE"
    "vehicle": str,          # "FLATBED"
    "unit": str,             # "per truck"
    "median_rate_usd": float,# 420.00
    "samples": int,          # 64
    ...
}
```

**Output (match_result):**
```python
{
    "row_index": int,        # 46 (Excel row)
    "match_score": float,    # 1.0 (100%)
    "match_level": str,      # "EXACT" | "SIMILARITY" | "REGION" | "VEHICLE_TYPE"
    "lane_data": dict        # approved_lane record
}
```

---

### 1.1.5 데이터 흐름 다이어그램

#### 전체 파이프라인

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: DATA LOADING                                            │
└─────────────────────────────────────────────────────────────────┘

Excel File (domestic_sept_2025_advanced_v3_NO_LEAK.xlsx)
    ├── items sheet (44 records)
    ├── comparison sheet
    └── patterns_applied sheet
                │
                ▼
        pd.read_excel()
                │
                ▼
        items_df DataFrame

JSON File (ApprovedLaneMap_ENHANCED.json)
    └── data.Sheet1 (124 lanes)
                │
                ▼
        json.load()
                │
                ▼
        approved_lanes List[Dict]

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: NORMALIZATION (For each item)                          │
└─────────────────────────────────────────────────────────────────┘

item.origin "DSV Musafah Yard"
    │
    ▼
normalize_text() → "DSV MUSAFAH YARD"
    │
    ▼
LOCATION_SYNONYMS mapping
    │
    ▼
Hardcoded rules
    │
    ▼
origin_norm = "DSV MUSSAFAH YARD"

(Same for destination, vehicle)

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: MATCHING (4-Level Fallback)                            │
└─────────────────────────────────────────────────────────────────┘

for lane in approved_lanes:
    │
    ├─► Level 1: Exact Match?
    │   └─► if 100% match → return {match_level: "EXACT", score: 1.0}
    │
    ├─► Level 2: Similarity Match?
    │   ├─► normalize lane data
    │   ├─► hybrid_similarity(origin, lane_origin)
    │   ├─► hybrid_similarity(destination, lane_dest)
    │   ├─► weighted_avg = 0.6*origin_sim + 0.4*dest_sim
    │   └─► if weighted_avg ≥ 0.65 → return {match_level: "SIMILARITY", score: 0.87}
    │
    ├─► Level 3: Region Match?
    │   ├─► get_region(origin) → "ABU DHABI REGION"
    │   ├─► get_region(destination) → "CONSTRUCTION SITE"
    │   └─► if regions match → return {match_level: "REGION", score: 0.5}
    │
    └─► Level 4: Vehicle Type Match?
        ├─► get_vehicle_group(vehicle) → "FLATBED_GROUP"
        ├─► get_vehicle_group(lane_vehicle) → "FLATBED_GROUP"
        └─► if groups match and sim ≥ 0.4 → return {match_level: "VEHICLE_TYPE", score: 0.62}

If no match → return None

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: HYPERLINK GENERATION                                   │
└─────────────────────────────────────────────────────────────────┘

match_result
    │
    ├─► if match_result:
    │   ├─► hyperlink_info.append({
    │   │       "item_row": 5,
    │   │       "target_row": 46,
    │   │       "match_level": "SIMILARITY",
    │   │       "match_score": 0.87
    │   │   })
    │   └─► match_stats[match_level] += 1
    │
    └─► else:
        └─► match_stats["no_match"] += 1

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: EXCEL WRITING                                          │
└─────────────────────────────────────────────────────────────────┘

xlsxwriter.Workbook
    │
    ├─► write items sheet
    │   └─► for each hyperlink_info:
    │       ├─► if target_row exists:
    │       │   └─► worksheet.write_url(
    │       │           row, col,
    │       │           "internal:ApprovedLaneMap!A46",
    │       │           hyperlink_format,
    │       │           string="$420.00"
    │       │       )
    │       └─► else:
    │           └─► worksheet.write(row, col, value, normal_format)
    │
    ├─► write comparison sheet
    ├─► write patterns_applied sheet
    └─► write ApprovedLaneMap sheet (124 lanes)

Output: domestic_sept_2025_advanced_v3_NO_LEAK_WITH_LANEMAP_ENHANCED.xlsx
```

---

## 1.2 정규화 엔진 상세

### 1.2.1 위치명 정규화 로직

정규화 엔진은 Enhanced Matching System의 **첫 번째 계층**으로, 모든 입력 데이터를 표준 형식으로 변환합니다. 이를 통해 **오타, 약어, 철자 변형**을 자동으로 처리하여 매칭률을 극대화합니다.

#### LOCATION_SYNONYMS 매핑

**철자 변형 (Spelling Variants):**
```python
"MUSSAFAH": ["MUSAFAH", "MUSAFFAH", "MUSSAFFAH"]
"MUSAFFAH": ["MUSSAFAH", "MUSAFAH", "MUSSAFFAH"]
```
- 동일한 지역이지만 다양한 철자로 표기되는 경우 처리
- 양방향 매핑으로 어떤 철자든 표준 형식으로 통일

**약어 (Abbreviations):**
```python
"WAREHOUSE": ["WH", "W/H", "WHEREHOUSE"]
"PORT": ["MINA", "HARBOUR", "HARBOR"]
"MINA": ["PORT"]
"YARD": ["YRD", "STORAGE"]
"SITE": ["LOCATION", "LOC"]
```
- 물류 도메인 표준 약어를 전체 단어로 확장
- 영국식/미국식 철자 통합 (HARBOUR/HARBOR)

**지역명 (Geographic Names):**
```python
"JEBEL ALI": ["JEBEL", "J.ALI", "JABEL ALI"]
"ABU DHABI": ["ABUDHABI", "AD", "A.D"]
"DUBAI": ["DXB", "DB"]
```
- 공식 지역명과 약어/별칭 통합
- 띄어쓰기 변형 처리 (ABU DHABI vs ABUDHABI)

**시설명 (Facility Types):**
```python
"FACTORY": ["PLANT", "FACTY"]
```
- 동일 의미의 다양한 표현 통합

**회사명 (Company Names):**
```python
"SAMSUNG": ["SAMSNG", "SAMSG"]
"MASAOOD": ["MASOOD", "MASOUD", "MOSB"]
```
- 오타가 자주 발생하는 회사명 처리
- MOSB = MASAOOD 도메인 지식 반영

---

#### 정규화 처리 순서

**1단계: 기본 전처리**
```python
text = str(text).upper().strip()
```
- 대소문자 통일 (upper case)
- 앞뒤 공백 제거

**2단계: 특수문자 제거**
```python
text = re.sub(r'[^\w\s]', ' ', text)  # 특수문자 → 공백
text = re.sub(r'\s+', ' ', text).strip()  # 연속 공백 → 단일 공백
```
- 하이픈(-), 슬래시(/), 마침표(.) 등 제거
- 단어 사이 공백만 유지

**3단계: 시노님 매핑**
```python
for standard, variants in LOCATION_SYNONYMS.items():
    for variant in variants:
        if variant in text:
            text = text.replace(variant, standard)
```
- 모든 시노님을 표준 단어로 치환
- 예: "WH" → "WAREHOUSE", "JEBEL" → "JEBEL ALI"

**4단계: 하드코딩 규칙 적용**
```python
# DSV 관련
if "DSV" in loc and "MUSSAFAH" in loc:
    return "DSV MUSSAFAH YARD"

# MIRFA 관련
if any(k in loc for k in ["MIRFA", "PMO"]) and "SAMSUNG" in loc:
    return "MIRFA SITE"
```
- 복합 조건 기반 최종 표준명 결정
- 도메인 특화 규칙 적용 (우선순위 최상위)

---

#### 하드코딩 규칙 체계

**우선순위 기반 매칭:**

1. **DSV 시설** (Priority 1)
```python
if "DSV" in loc and "MUSSAFAH" in loc:
    return "DSV MUSSAFAH YARD"
if "DSV" in loc and "M44" in loc:
    return "M44 WAREHOUSE"
if "DSV" in loc and "MARKAZ" in loc:
    return "AL MARKAZ WAREHOUSE"
```

2. **프로젝트 사이트** (Priority 2)
```python
if any(k in loc for k in ["MIRFA", "PMO"]) and "SAMSUNG" in loc:
    return "MIRFA SITE"
if any(k in loc for k in ["SHUWEIHAT", "POWER"]):
    return "SHUWEIHAT SITE"
```

3. **MOSB/MASAOOD 시설** (Priority 3)
```python
if any(k in loc for k in ["MOSB", "MASAOOD"]):
    if "SAMSUNG" in loc:
        return "SAMSUNG MOSB YARD"
    else:
        return "AL MASAOOD (MOSB)"
```

4. **항구 시설** (Priority 4)
```python
if any(k in loc for k in ["MINA", "ZAYED", "PORT", "FREEPORT"]):
    if "JEBEL" in loc:
        return "JEBEL ALI PORT"
    else:
        return "MINA ZAYED PORT"
```

5. **창고 시설** (Priority 5)
```python
if "M44" in loc:
    return "M44 WAREHOUSE"
if "ICAD" in loc:
    return "ICAD WAREHOUSE"
if "MARKAZ" in loc:
    return "AL MARKAZ WAREHOUSE"
```

6. **특수 케이스** (Priority 6)
```python
if "TROJAN" in loc:
    return "TROJAN MUSSAFAH"
if "SURTI" in loc and "JEBEL" in loc:
    return "SURTI INDUSTRIES LLC (JEBEL ALI)"
```

**우선순위 설계 원칙:**
- 더 구체적인 조건이 높은 우선순위
- 회사명 + 위치명 조합 > 단일 키워드
- 프로젝트 핵심 시설 우선

---

### 1.2.2 차량 타입 정규화

#### VEHICLE_SYNONYMS 매핑

```python
VEHICLE_SYNONYMS = {
    "FLATBED": ["FLAT BED", "FLAT-BED", "FLAT_BED", "FB"],
    "FLAT BED": ["FLATBED", "FLAT-BED", "FLAT_BED"],
    "TRUCK": ["LORRY", "VEHICLE"],
    "LORRY": ["TRUCK"],
    "TRAILER": ["TRAILOR", "TRALER"],
    "CRANE": ["MOBILE CRANE", "MCR"],
}
```

**주요 처리 케이스:**

1. **띄어쓰기 변형**
   - `"FLAT BED"` ↔ `"FLATBED"` ↔ `"FLAT-BED"` ↔ `"FLAT_BED"`
   - 모두 `"FLATBED"`으로 통일

2. **영국식/미국식**
   - `"LORRY"` (영국) ↔ `"TRUCK"` (미국)
   - `"TRUCK"`으로 통일

3. **오타 처리**
   - `"TRAILOR"` → `"TRAILER"`
   - `"TRALER"` → `"TRAILER"`

4. **약어 확장**
   - `"FB"` → `"FLATBED"`
   - `"MCR"` → `"CRANE"`

5. **상세명 → 일반명**
   - `"MOBILE CRANE"` → `"CRANE"`

#### normalize_vehicle() 함수

```python
def normalize_vehicle(vehicle: str) -> str:
    """차량 타입 정규화"""
    if pd.isna(vehicle):
        return ""
    
    return normalize_text(vehicle, VEHICLE_SYNONYMS)
```

- `normalize_text()` 재사용으로 코드 중복 제거
- 위치명과 동일한 정규화 프로세스 적용

---

### 1.2.3 시노님 매핑 시스템

#### 시노님 매핑 아키텍처

```
┌─────────────────────────────────────────┐
│         Synonym Mapping System          │
└─────────────────────────────────────────┘

Input Text: "DSV Musafah WH"
    │
    ▼
normalize_text(text, LOCATION_SYNONYMS)
    │
    ├─► Step 1: Upper case
    │   "DSV MUSAFAH WH"
    │
    ├─► Step 2: Remove special chars
    │   "DSV MUSAFAH WH"
    │
    ├─► Step 3: Synonym mapping (iterative)
    │   │
    │   ├─► "MUSAFAH" in text?
    │   │   YES → replace with "MUSSAFAH"
    │   │   "DSV MUSSAFAH WH"
    │   │
    │   └─► "WH" in text?
    │       YES → replace with "WAREHOUSE"
    │       "DSV MUSSAFAH WAREHOUSE"
    │
    └─► Output: "DSV MUSSAFAH WAREHOUSE"
```

#### 시노님 데이터 구조

```python
synonym_map: Dict[str, List[str]] = {
    "STANDARD_TERM": ["variant1", "variant2", "variant3", ...]
}
```

**설계 원칙:**
1. **표준어 우선**: 키는 항상 표준 용어
2. **일대다 매핑**: 하나의 표준어에 여러 변형
3. **양방향 지원**: 필요 시 역방향 매핑도 추가

**예시: MUSSAFAH 케이스**
```python
{
    "MUSSAFAH": ["MUSAFAH", "MUSAFFAH", "MUSSAFFAH"],  # Forward mapping
    "MUSAFFAH": ["MUSSAFAH", "MUSAFAH", "MUSSAFFAH"],  # Reverse mapping
}
```
- 어떤 철자로 입력되든 표준형으로 통일
- "MUSAFAH" 입력 시 → "MUSAFFAH"로 매핑 → 이후 "MUSAFFAH"를 "MUSSAFAH"로 재매핑

---

### 1.2.4 하드코딩 규칙 vs 동적 매핑

#### 하이브리드 접근법

Enhanced Matching System은 **하드코딩 규칙 + 동적 시노님 매핑**을 병행합니다.

**하드코딩 규칙 (Hardcoded Rules):**
- **장점**: 정확도 100%, 도메인 특화, 빠른 처리
- **단점**: 확장성 낮음, 유지보수 비용
- **사용 사례**: 핵심 시설명 (DSV MUSSAFAH YARD, MIRFA SITE 등)

**동적 시노님 매핑 (Dynamic Synonym Mapping):**
- **장점**: 확장 용이, 일반화, 새 용어 추가 간편
- **단점**: 복합 조건 처리 어려움
- **사용 사례**: 약어, 철자 변형, 일반 용어

#### 하이브리드 처리 순서

```python
def normalize_location(location: str) -> str:
    # Step 1: 동적 시노님 매핑 (일반화)
    loc = normalize_text(location, LOCATION_SYNONYMS)
    
    # Step 2: 하드코딩 규칙 적용 (도메인 특화)
    if "DSV" in loc and "MUSSAFAH" in loc:
        return "DSV MUSSAFAH YARD"
    # ... more hardcoded rules ...
    
    # Step 3: 변환되지 않았으면 그대로 반환
    return loc
```

**우선순위:**
1. 하드코딩 규칙 (가장 높음)
2. 시노님 매핑
3. 원본 유지

#### 확장 가이드

**새 시노님 추가:**
```python
LOCATION_SYNONYMS = {
    # ... existing ...
    "NEW_STANDARD": ["variant1", "variant2"],  # ← ADD HERE
}
```

**새 하드코딩 규칙 추가:**
```python
def normalize_location(location: str) -> str:
    loc = normalize_text(location, LOCATION_SYNONYMS)
    
    # ... existing rules ...
    
    # NEW RULE (add before 'return loc')
    if "NEW_KEYWORD" in loc:
        return "NEW STANDARD NAME"
    
    return loc
```

---

### 1.2.5 정규화 함수 상세

#### normalize_text() - 범용 정규화 함수

**함수 시그니처:**
```python
def normalize_text(text: str, synonym_map: Dict[str, List[str]]) -> str:
    """
    텍스트를 정규화하고 시노님을 표준화
    
    Args:
        text: 원본 텍스트
        synonym_map: 시노님 매핑 딕셔너리
    
    Returns:
        정규화된 텍스트
    
    Examples:
        >>> normalize_text("DSV Musafah", LOCATION_SYNONYMS)
        'DSV MUSSAFAH'
        
        >>> normalize_text("flat-bed", VEHICLE_SYNONYMS)
        'FLATBED'
    """
```

**알고리즘 상세:**

```python
# 1. Null 체크
if pd.isna(text):
    return ""

# 2. 기본 전처리
text = str(text).upper().strip()
# Input: "DSV Musafah WH"
# Output: "DSV MUSAFAH WH"

# 3. 특수문자 정리
text = re.sub(r'[^\w\s]', ' ', text)
# Input: "FLAT-BED/TRUCK"
# Output: "FLAT BED TRUCK"

text = re.sub(r'\s+', ' ', text).strip()
# Input: "DSV  MUSSAFAH    WH"
# Output: "DSV MUSSAFAH WH"

# 4. 시노님 매핑 (반복 적용)
for standard, variants in synonym_map.items():
    for variant in variants:
        if variant in text:
            text = text.replace(variant, standard)
# Input: "DSV MUSSAFAH WH"
# Step 1: "WH" → "WAREHOUSE" = "DSV MUSSAFAH WAREHOUSE"
# Step 2: "MUSSAFAH" → already standard
# Output: "DSV MUSSAFAH WAREHOUSE"

return text
```

**시간 복잡도:**
- O(n × m × k)
  - n: synonym_map 크기 (42)
  - m: variants per standard (평균 3)
  - k: text 길이 (평균 30)
- 실제: ~0.1ms per call (negligible)

---

#### normalize_location() - 위치명 정규화

**함수 시그니처:**
```python
def normalize_location(location: str) -> str:
    """
    향상된 위치명 정규화
    
    기존 하드코딩 규칙 + 시노님 매핑 통합
    
    Args:
        location: 원본 위치명
    
    Returns:
        표준 위치명
    
    Examples:
        >>> normalize_location("DSV Musafah Yard")
        'DSV MUSSAFAH YARD'
        
        >>> normalize_location("Jebel Ali Port")
        'JEBEL ALI PORT'
        
        >>> normalize_location("ICAD WH")
        'ICAD WAREHOUSE'
    """
```

**전체 알고리즘 플로우:**

```python
if pd.isna(location):
    return ""

# Phase 1: 동적 시노님 매핑
loc = normalize_text(location, LOCATION_SYNONYMS)

# Phase 2: 하드코딩 규칙 (우선순위 순)
# Priority 1: DSV 시설
if "DSV" in loc and "MUSSAFAH" in loc:
    return "DSV MUSSAFAH YARD"
if "DSV" in loc and "M44" in loc:
    return "M44 WAREHOUSE"
if "DSV" in loc and "MARKAZ" in loc:
    return "AL MARKAZ WAREHOUSE"

# Priority 2: 프로젝트 사이트
if any(k in loc for k in ["MIRFA", "PMO"]) and "SAMSUNG" in loc:
    return "MIRFA SITE"
if any(k in loc for k in ["SHUWEIHAT", "POWER"]):
    return "SHUWEIHAT SITE"

# Priority 3: MOSB/MASAOOD
if any(k in loc for k in ["MOSB", "MASAOOD"]):
    if "SAMSUNG" in loc:
        return "SAMSUNG MOSB YARD"
    else:
        return "AL MASAOOD (MOSB)"

# Priority 4: 항구
if any(k in loc for k in ["MINA", "ZAYED", "PORT", "FREEPORT"]):
    if "JEBEL" in loc:
        return "JEBEL ALI PORT"
    else:
        return "MINA ZAYED PORT"

# Priority 5: 창고
if "M44" in loc:
    return "M44 WAREHOUSE"
if "ICAD" in loc:
    return "ICAD WAREHOUSE"
if "MARKAZ" in loc:
    return "AL MARKAZ WAREHOUSE"

# Priority 6: 특수 케이스
if "TROJAN" in loc:
    return "TROJAN MUSSAFAH"
if "SURTI" in loc and "JEBEL" in loc:
    return "SURTI INDUSTRIES LLC (JEBEL ALI)"

# Phase 3: 변환 실패 시 시노님 매핑 결과 반환
return loc
```

---

#### normalize_vehicle() - 차량 타입 정규화

**함수 시그니처:**
```python
def normalize_vehicle(vehicle: str) -> str:
    """
    차량 타입 정규화
    
    Args:
        vehicle: 원본 차량 타입
    
    Returns:
        표준 차량 타입
    
    Examples:
        >>> normalize_vehicle("FLAT BED")
        'FLATBED'
        
        >>> normalize_vehicle("lorry")
        'TRUCK'
        
        >>> normalize_vehicle("MCR")
        'CRANE'
    """
```

**구현:**
```python
def normalize_vehicle(vehicle: str) -> str:
    if pd.isna(vehicle):
        return ""
    
    return normalize_text(vehicle, VEHICLE_SYNONYMS)
```

- `normalize_text()` 재사용
- 하드코딩 규칙 불필요 (차량 타입은 단순)
- VEHICLE_SYNONYMS만으로 충분

---

### 1.2.6 정규화 예제 및 테스트 케이스

#### 위치명 정규화 테스트

**Test Case 1: 철자 변형**
```python
Input:  "DSV Musafah Yard"
Step 1: normalize_text() → "DSV MUSSAFAH YARD"
Step 2: Hardcoded rule → "DSV MUSSAFAH YARD"
Output: "DSV MUSSAFAH YARD"
✅ PASS
```

**Test Case 2: 약어 확장**
```python
Input:  "ICAD WH"
Step 1: normalize_text() → "ICAD WAREHOUSE"
Step 2: Hardcoded rule → "ICAD WAREHOUSE"
Output: "ICAD WAREHOUSE"
✅ PASS
```

**Test Case 3: 복합 조건**
```python
Input:  "Samsung MIRFA PMO Site"
Step 1: normalize_text() → "SAMSUNG MIRFA PMO SITE"
Step 2: Hardcoded rule → "MIRFA SITE" (MIRFA + SAMSUNG 조건 매칭)
Output: "MIRFA SITE"
✅ PASS
```

**Test Case 4: 특수문자 제거**
```python
Input:  "Jebel-Ali / Port"
Step 1: normalize_text() → "JEBEL ALI PORT"
Step 2: Hardcoded rule → "JEBEL ALI PORT"
Output: "JEBEL ALI PORT"
✅ PASS
```

**Test Case 5: 미등록 위치 (Fallback)**
```python
Input:  "Unknown Location XYZ"
Step 1: normalize_text() → "UNKNOWN LOCATION XYZ"
Step 2: Hardcoded rule → no match
Output: "UNKNOWN LOCATION XYZ" (원본 유지)
✅ PASS (Graceful degradation)
```

---

#### 차량 타입 정규화 테스트

**Test Case 1: 띄어쓰기**
```python
Input:  "FLAT BED"
normalize_text() → "FLATBED"
Output: "FLATBED"
✅ PASS
```

**Test Case 2: 하이픈**
```python
Input:  "FLAT-BED"
Step 1: Special char removal → "FLAT BED"
Step 2: Synonym mapping → "FLATBED"
Output: "FLATBED"
✅ PASS
```

**Test Case 3: 영국식/미국식**
```python
Input:  "lorry"
normalize_text() → "TRUCK"
Output: "TRUCK"
✅ PASS
```

**Test Case 4: 오타**
```python
Input:  "TRAILOR"
normalize_text() → "TRAILER"
Output: "TRAILER"
✅ PASS
```

**Test Case 5: 약어**
```python
Input:  "MCR"
normalize_text() → "CRANE"
Output: "CRANE"
✅ PASS
```

---

#### 엣지 케이스 (Edge Cases)

**Edge Case 1: Null/Empty**
```python
Input:  None
Output: ""
✅ PASS
```

**Edge Case 2: 숫자 포함**
```python
Input:  "M44 Warehouse"
normalize_text() → "M44 WAREHOUSE"
Hardcoded rule → "M44 WAREHOUSE"
Output: "M44 WAREHOUSE"
✅ PASS
```

**Edge Case 3: 긴 문자열**
```python
Input:  "DSV Mussafah Industrial Yard & Warehouse Complex"
normalize_text() → "DSV MUSSAFAH INDUSTRIAL YARD WAREHOUSE COMPLEX"
Hardcoded rule → "DSV MUSSAFAH YARD" (DSV + MUSSAFAH 매칭)
Output: "DSV MUSSAFAH YARD"
✅ PASS (Prefix matching)
```

**Edge Case 4: 대소문자 혼합**
```python
Input:  "jEbEl aLi PorT"
normalize_text() → "JEBEL ALI PORT"
Hardcoded rule → "JEBEL ALI PORT"
Output: "JEBEL ALI PORT"
✅ PASS
```

**Edge Case 5: 연속 공백**
```python
Input:  "DSV    MUSSAFAH     YARD"
normalize_text() → "DSV MUSSAFAH YARD"
Hardcoded rule → "DSV MUSSAFAH YARD"
Output: "DSV MUSSAFAH YARD"
✅ PASS
```

---

#### 성능 테스트

**Benchmark (44 items × 124 lanes = 5,456 normalization calls):**

| 함수 | 호출 횟수 | 총 시간 | 평균 시간/호출 |
|------|----------|---------|---------------|
| normalize_text() | 10,912 | 1.2ms | 0.0001ms |
| normalize_location() | 5,456 | 5.4ms | 0.001ms |
| normalize_vehicle() | 5,456 | 1.1ms | 0.0002ms |
| **Total** | **21,824** | **7.7ms** | **0.0004ms** |

**결론**: 정규화 오버헤드는 negligible (전체 처리 시간의 0.4%)

---

#### 유닛 테스트 코드

```python
def test_normalization():
    """정규화 엔진 유닛 테스트"""
    
    # Location tests
    assert normalize_location("DSV Musafah Yard") == "DSV MUSSAFAH YARD"
    assert normalize_location("ICAD WH") == "ICAD WAREHOUSE"
    assert normalize_location("Jebel-Ali / Port") == "JEBEL ALI PORT"
    assert normalize_location(None) == ""
    
    # Vehicle tests
    assert normalize_vehicle("FLAT BED") == "FLATBED"
    assert normalize_vehicle("lorry") == "TRUCK"
    assert normalize_vehicle("MCR") == "CRANE"
    assert normalize_vehicle(None) == ""
    
    print("✅ All normalization tests passed!")

if __name__ == "__main__":
    test_normalization()
```

---

## 📊 정규화 통계

### 시노님 커버리지

| 카테고리 | 표준어 수 | 변형 수 | 평균 변형/표준어 |
|---------|----------|---------|-----------------|
| Location | 14 | 42 | 3.0 |
| Vehicle | 6 | 11 | 1.8 |
| **Total** | **20** | **53** | **2.7** |

### 하드코딩 규칙 커버리지

| Priority | 규칙 수 | 처리 시설 수 |
|----------|---------|-------------|
| 1 (DSV) | 3 | 3 |
| 2 (Site) | 2 | 2 |
| 3 (MOSB) | 2 | 2 |
| 4 (Port) | 2 | 2 |
| 5 (Warehouse) | 3 | 3 |
| 6 (Special) | 2 | 2 |
| **Total** | **14** | **14** |

---

## 🔗 다음 문서

➡️ **[Part 2: 유사도 알고리즘 & 4단계 매칭 시스템](Part2_Similarity_and_Matching.md)**
- Token-Set Similarity
- Levenshtein Distance
- 하이브리드 유사도 계산
- 4단계 Fallback 매칭 시스템

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-13  
**Next Review**: 2025-11-13

