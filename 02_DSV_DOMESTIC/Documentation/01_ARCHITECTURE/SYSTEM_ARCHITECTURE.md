# 시스템 아키텍처 (System Architecture)

**프로젝트**: 9월 2025 DSV Domestic Invoice 검증 시스템
**버전**: PATCH4 (v4.0) + Hybrid Integration
**작성일**: 2025-10-14 (업데이트)

---

## 📐 시스템 전체 구조

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INPUT LAYER                                       │
├─────────────────────────────────────────────────────────────────────┤
│  1. Invoice Excel (44 items)                                         │
│     - SCNT HVDC DRAFT INVOICE FOR DOMESTIC DELIVERY SEPTEMBER 2025   │
│                                                                       │
│  2. ApprovedLaneMap JSON (124 lanes)                                 │
│     - ApprovedLaneMap_ENHANCED.json                                  │
│                                                                       │
│  3. Supporting Documents (36 DN PDFs)                                │
│     - Data/DSV 202509/SCNT Domestic (Sept 2025) - Supporting        │
│       Documents/                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  PROCESSING LAYER                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────┐          │
│  │  COMPONENT 1: Enhanced Lane Matching                   │          │
│  │  - 4-level fallback (Exact → Similarity → Region →    │          │
│  │    Vehicle)                                            │          │
│  │  - Normalization (location, vehicle)                  │          │
│  │  - Hybrid similarity (Token-Set + Levenshtein + Fuzzy)│          │
│  │  - Result: 79.5% matching (35/44)                     │          │
│  └────────────────────────────────────────────────────────┘          │
│                              ↓                                        │
│  ┌────────────────────────────────────────────────────────┐          │
│  │  COMPONENT 2: Hybrid PDF Parsing & Extraction (NEW)   │          │
│  │  - Intelligent Routing: Docling (local) / ADE (cloud) │          │
│  │  - Multi-layer fallback: PyMuPDF → pypdf →           │          │
│  │    pdfminer → pdftotext                              │          │
│  │  - Field extraction: Origin, Destination, Vehicle,    │          │
│  │    Destination Code, DO #                            │          │
│  │  - Unified IR (Intermediate Representation)          │          │
│  │  - Result: 91.7% parsing success (33/36)             │          │
│  └────────────────────────────────────────────────────────┘          │
│                              ↓                                        │
│  ┌────────────────────────────────────────────────────────┐          │
│  │  COMPONENT 3: Cross-Document Validation                │          │
│  │  - 1:1 Greedy Matching Algorithm                      │          │
│  │  - Similarity calculation (Origin 0.27, Dest 0.50,    │          │
│  │    Vehicle 0.30)                                       │          │
│  │  - DN Capacity System (Auto-bump, MAX_CAP=16)        │          │
│  │  - Result: 95.5% matching (42/44)                     │          │
│  └────────────────────────────────────────────────────────┘          │
│                              ↓                                        │
│  ┌────────────────────────────────────────────────────────┐          │
│  │  COMPONENT 4: Validation Status Classification         │          │
│  │  - PASS: All thresholds met (47.7%)                   │          │
│  │  - WARN: Partial match (47.7%)                        │          │
│  │  - FAIL: No match (0%)                                │          │
│  │  - Unmatched reason: CAPACITY_EXHAUSTED,              │          │
│  │    BELOW_MIN_SCORE, NO_CANDIDATES                     │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER                                      │
├─────────────────────────────────────────────────────────────────────┤
│  1. Final Excel (1 file, latest only)                                │
│     - domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_*.xlsx           │
│     - 25+ columns with Hybrid metadata                              │
│                                                                       │
│  2. Reports (34 documents)                                           │
│     - SEPT_2025_COMPLETE_VALIDATION_REPORT.md                        │
│     - Supply-Demand Analysis CSV                                     │
│     - Top-N Candidate Dump CSV                                       │
│                                                                       │
│  3. ARCHIVE (NEW - 2025-10-14 정리)                                  │
│     - logs/ (17 files)                                               │
│     - excel_history/ (9 previous versions)                          │
│     - reports_history/ (5 documents)                                │
│     - backups/ (1 backup)                                           │
│     - temp/ (2 temporary files)                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 주요 컴포넌트

### 1. Enhanced Lane Matching
**파일**: `enhanced_matching.py`

**역할**: 인보이스 항목을 ApprovedLaneMap과 매칭

**알고리즘**:
```python
def find_matching_lane_enhanced(item, lane_map):
    # Level 1: Exact Match
    if exact_match(item, lane_map):
        return lane, "Exact"

    # Level 2: Similarity Match (≥0.65)
    if similarity_match(item, lane_map, threshold=0.65):
        return lane, "Similarity"

    # Level 3: Region Match
    if region_match(item, lane_map):
        return lane, "Region"

    # Level 4: Vehicle Type Match
    if vehicle_type_match(item, lane_map):
        return lane, "Vehicle"

    return None, "No Match"
```

**성과**: 79.5% (35/44)

---

### 2. Hybrid PDF Parsing & Extraction (NEW)
**파일**:
- `Core_Systems/hybrid_pdf_integration.py`
- `src/utils/pdf_text_fallback.py`
- `src/utils/pdf_extractors.py`

**역할**: DN PDF에서 필드 추출 (Intelligent Routing)

**Hybrid Routing**:
```python
def parse_dn_with_routing(pdf_path, shipment_ref):
    # 1. Intelligent Routing Decision
    routing_decision = router.route_document(pdf_path, doc_type="DN")

    # 2. Parse with selected engine
    if routing_decision.engine == "DOCLING":
        result = docling_parser.parse(pdf_path)  # Local
    else:
        result = ade_parser.parse(pdf_path)      # Cloud (ADE)

    # 3. Convert to Unified IR
    unified_data = to_unified_ir(result)

    # 4. Convert to DOMESTIC format
    domestic_data = to_domestic_format(unified_data)

    return domestic_data
```

**다층 폴백**:
```python
def extract_text_any(pdf_path):
    for extractor in [
        _try_pymupdf,      # 1순위: 15~35배 빠름
        _try_pypdf,        # 2순위: 경량
        _try_pdfminer,     # 3순위: 복잡한 레이아웃
        _try_pdftotext     # 4순위: 외부 도구
    ]:
        text = extractor(pdf_path)
        if text:
            return text
    return ""
```

**추출 필드**:
- Origin (Loading Point)
- Destination
- Vehicle Type
- Destination Code
- DO # (Delivery Order)

**Hybrid 특징**:
- Intelligent routing (Docling/ADE)
- Unified IR (engine-agnostic)
- Budget management (ADE cost control)
- Routing metadata tracking

**성과**: 91.7% (33/36)

---

### 3. Cross-Document Validation
**파일**: `validate_sept_2025_with_pdf.py` (cross_validate_invoice_dn 함수)

**역할**: 인보이스 ↔ DN 매칭 및 검증

**1:1 그리디 매칭**:
```python
def cross_validate_invoice_dn(items_df, dns):
    # 1. 모든 (invoice, DN) 쌍의 점수 계산
    candidates = []
    for invoice in items:
        for dn in dns:
            score = calculate_score(invoice, dn)
            candidates.append((score, invoice, dn))

    # 2. 점수 기준 정렬
    candidates.sort(reverse=True)

    # 3. 그리디 할당 (capacity 존중)
    for score, invoice, dn in candidates:
        if dn.capacity > 0 and invoice not in assigned:
            assign(invoice, dn)
            dn.capacity -= 1
```

**점수 공식**:
```
score = 0.45 * origin_sim + 0.45 * dest_sim + 0.10 * vehicle_sim
```

**성과**: 95.5% (42/44)

---

### 4. DN Capacity System
**파일**: `src/utils/dn_capacity.py`

**역할**: DN 용량 관리 및 자동 증가

**Auto-Bump 로직**:
```python
def auto_capacity_bump(dn_list, top_choice_counts):
    max_cap = int(os.getenv("DN_MAX_CAPACITY", "16"))

    for j, dn in enumerate(dn_list):
        # 수동 오버라이드 존중
        if dn.capacity > 1:
            continue

        # 수요 기반 증가
        demand = top_choice_counts.get(j, 0)
        if demand > 1:
            dn.capacity = min(demand, max_cap)
```

**성과**: 모든 DN gap=0 (100% 충족)

---

## 🔄 데이터 흐름

### 입력 → 처리 → 출력

```
┌─────────────────┐
│  Invoice Excel  │
│  (44 items)     │
└────────┬────────┘
         │
         ├──────────────────────────────────────┐
         │                                      │
         ▼                                      ▼
┌──────────────────┐                  ┌──────────────────┐
│ Enhanced Lane    │                  │  DN PDF Parsing  │
│ Matching         │                  │  (33 DNs)        │
│ (35/44 matched)  │                  │                  │
└────────┬─────────┘                  └────────┬─────────┘
         │                                      │
         └──────────┬───────────────────────────┘
                    ▼
         ┌─────────────────────┐
         │  Cross-Validation   │
         │  (1:1 Greedy)       │
         │  DN Capacity System │
         │  (42/44 matched)    │
         └──────────┬──────────┘
                    │
         ┌──────────┴───────────┬──────────────┐
         ▼                      ▼              ▼
┌──────────────┐    ┌──────────────────┐  ┌────────────┐
│ Final Excel  │    │ Supply-Demand    │  │  Reports   │
│ (25 columns) │    │ Analysis CSV     │  │  (MD)      │
└──────────────┘    └──────────────────┘  └────────────┘
```

---

## 🔗 모듈 간 의존성

```
validate_sept_2025_with_pdf.py (메인)
  │
  ├─► enhanced_matching.py
  │     └─► normalize_location(), hybrid_similarity()
  │
  ├─► src/utils/pdf_text_fallback.py
  │     └─► extract_text_any()
  │
  ├─► src/utils/pdf_extractors.py
  │     └─► extract_from_pdf_text()
  │
  ├─► src/utils/utils_normalize.py
  │     └─► normalize_location(), token_set_jaccard()
  │
  ├─► src/utils/location_canon.py
  │     └─► expand_location_abbrev()
  │
  └─► src/utils/dn_capacity.py
        └─► load_capacity_overrides(), apply_capacity_overrides(),
            auto_capacity_bump()
```

---

## ⚙️ 환경변수 설정

### 카테고리별 환경변수

```bash
# ===== PDF 추출 =====
DN_USE_PDF_FIELDS_FIRST=true   # PDF 본문 우선 (기본)

# ===== 유사도 임계값 =====
DN_ORIGIN_THR=0.27             # Origin 임계값
DN_DEST_THR=0.50               # Destination 임계값
DN_VEH_THR=0.30                # Vehicle 임계값
DN_MIN_SCORE=0.40              # 최소 매칭 점수

# ===== DN Capacity =====
DN_AUTO_CAPACITY_BUMP=true     # 자동 용량 증가
DN_MAX_CAPACITY=16             # 최대 용량
DN_CAPACITY_DEFAULT=1          # 기본 용량
DN_CAPACITY_MAP='{...}'        # 수동 오버라이드 (JSON)
DN_CAPACITY_FILE=/path/to.json # 오버라이드 파일

# ===== 분석 파일 =====
DN_DUMP_TOPN=3                 # Top-N 후보 덤프
DN_DUMP_PATH=dn_candidate_dump.csv
DN_DUMP_SUPPLY=true            # 수요-공급 분석
DN_DUMP_SUPPLY_PATH=dn_supply_demand.csv
```

---

## 🛠️ 기술 스택

### Core
- **Python**: 3.8+
- **pandas**: 데이터 처리
- **openpyxl**: Excel 읽기/쓰기

### PDF Processing
- **PyMuPDF (fitz)**: 1순위 추출 (빠르고 안정적)
- **pypdf/PyPDF2**: 2순위 추출 (경량)
- **pdfminer.six**: 3순위 추출 (복잡한 레이아웃)
- **pdftotext**: 4순위 추출 (외부 도구)

### Similarity Algorithms
- **Token-Set Jaccard**: 토큰 집합 유사도
- **Levenshtein Distance**: 편집 거리
- **Fuzzy Token Sort**: 토큰 순서 고려

### Utilities
- **re**: 정규식 (약어 확장, 필드 추출)
- **csv**: CSV 출력
- **json**: 설정 파일

---

## 📊 성능 특성

### 처리 성능
- **인보이스 44개 처리 시간**: 약 8분
- **PDF 파싱**: 약 0.5초/파일 (PyMuPDF)
- **매칭 연산**: O(N×M) where N=44, M=33

### 메모리 사용
- **인보이스 데이터**: < 1MB
- **DN 데이터**: < 10MB (PDF 텍스트 포함)
- **총 메모리**: < 100MB

### 확장성
- **인보이스**: 100개까지 선형 확장 가능
- **DN**: 100개까지 문제없음
- **병목**: PDF 파싱 (병렬 처리 가능)

---

## 🔒 보안 및 준수사항

### 데이터 보호
- **NDA**: Supporting Documents 외부 공유 금지
- **PII**: 개인정보 (운전사 이름 등) 보호
- **Confidential**: 계약서, 가격 정보 기밀

### 감사 추적
- **모든 매칭**: dn_matched, dn_shipment_ref 기록
- **미매칭 사유**: dn_unmatched_reason 명시
- **수요-공급**: dn_supply_demand.csv 보관

---

## 🎯 시스템 품질 목표

| 지표 | 목표 | 실제 달성 | Status |
|------|------|----------|--------|
| 매칭률 | ≥90% | **95.5%** | ✅ 초과 |
| FAIL 비율 | ≤5% | **0%** | ✅ 초과 |
| PDF 파싱 | ≥90% | **91.7%** | ✅ 달성 |
| Dest 유사도 | ≥0.90 | **0.971** | ✅ 초과 |
| 처리 시간 | ≤10분 | **8분** | ✅ 달성 |

---

## 📁 ARCHIVE 시스템 (NEW)

### 구조
```
ARCHIVE/
├── logs/                              # 로그 파일 보관 (17개)
│   ├── final_validation.log
│   ├── validation_results.txt
│   ├── validation_with_hybrid_columns.log
│   ├── validation_hybrid_test.log
│   └── Sept_2025_Logs/ (13개)         # 이전 실행 로그
├── excel_history/                     # 이전 Excel 버전 (9개)
│   └── domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_*.xlsx
├── reports_history/                   # 중복 리포트 (5개)
│   └── (이전 문서 보고서들)
├── backups/                           # 백업 파일 (1개)
│   └── validate_sept_2025_with_pdf.py.backup
└── temp/                              # 임시 파일 (2개)
    ├── dn_supply_demand.csv
    └── verify_final_v2.py
```

### 목적
- **이력 보존**: 모든 실행 로그 및 이전 버전 보관
- **클린 Production**: 루트 폴더에 최신 파일만 유지
- **감사 추적**: 모든 변경 이력 보존
- **롤백 지원**: 필요시 이전 버전 복원 가능

### 정리 효과 (2025-10-14)
- 루트 파일: 25개 → 9개 (64% 감소)
- Excel 파일: 10개 → 1개 (최신만 유지)
- 전체 정리율: 약 40% 파일 수 감소

---

## 🔄 Hybrid Integration (NEW)

### 아키텍처
```
┌─────────────────────────────────────┐
│     Hybrid PDF Integration          │
├─────────────────────────────────────┤
│                                      │
│  ┌──────────────┐  ┌──────────────┐ │
│  │   Docling    │  │  ADE (Cloud) │ │
│  │   (Local)    │  │              │ │
│  └──────────────┘  └──────────────┘ │
│         ↓                 ↓          │
│  ┌────────────────────────────────┐ │
│  │   Intelligent Router           │ │
│  │   - Rules-based routing        │ │
│  │   - Budget management          │ │
│  │   - Performance tracking       │ │
│  └────────────────────────────────┘ │
│         ↓                            │
│  ┌────────────────────────────────┐ │
│  │   Unified IR                   │ │
│  │   - Engine-agnostic format     │ │
│  │   - BBox information           │ │
│  │   - Confidence scores          │ │
│  └────────────────────────────────┘ │
│         ↓                            │
│  ┌────────────────────────────────┐ │
│  │   Data Adapters                │ │
│  │   - UnifiedIR ↔ DOMESTIC       │ │
│  │   - Schema validation          │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 주요 컴포넌트
1. **HybridPDFRouter**: Intelligent routing 결정
2. **Unified IR**: Engine-agnostic 중간 표현
3. **Data Adapters**: 형식 변환 계층
4. **Schema Validator**: 데이터 검증

### 통합 상태
- ✅ Core integration 완료
- ✅ DOMESTIC 시스템 통합
- ✅ Backward compatibility 유지
- ⏳ SHPT 시스템 통합 대기

---

## 🔮 향후 확장 계획

### Phase 2 (단기)
- PyMuPDF 필수 설치 (성능 최대화)
- DN 2개 추가 확보 (100% 목표)
- 월별 수요 패턴 분석
- Hybrid routing 최적화

### Phase 3 (중기)
- 다른 월 인보이스 적용 (10월, 11월)
- Dynamic capacity 알고리즘 고도화
- 병렬 처리 (PDF 파싱, 매칭)
- SHPT 시스템 Hybrid 통합 완료

### Phase 4 (장기)
- 실시간 검증 API
- 웹 대시보드
- ML 기반 유사도 학습
- Full ADE integration (cloud parsing)

---

**문서 버전**: 2.0 (Hybrid Integration + Cleanup)
**최종 업데이트**: 2025-10-14 09:00:00
**Status**: ✅ Production Ready with Hybrid Integration

