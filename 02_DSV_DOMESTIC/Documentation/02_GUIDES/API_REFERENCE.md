# API 레퍼런스 (API Reference)

**프로젝트**: 9월 2025 DSV Domestic Invoice 검증 시스템
**버전**: PATCH4 (v4.0)
**작성일**: 2025-10-13

---

## 📘 Core Functions

### validate_sept_2025_with_pdf.py

#### main()
```python
def main():
    """
    메인 검증 파이프라인

    Steps:
        1. Supporting Documents 스캔
        2. DN PDF 파싱
        3. Cross-Document 검증
        4. Excel 파일 생성
        5. 종합 리포트 생성

    Returns:
        None (파일 생성)

    Output Files:
        - domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_*.xlsx
        - SEPT_2025_COMPLETE_VALIDATION_REPORT.md
        - dn_supply_demand.csv (옵션)
        - dn_candidate_dump.csv (옵션)
    """
```

#### cross_validate_invoice_dn()
```python
def cross_validate_invoice_dn(
    items_df: pd.DataFrame,
    dns: List[dict]
) -> dict:
    """
    Invoice ↔ DN 크로스 검증 (1:1 그리디 매칭)

    Args:
        items_df: 인보이스 데이터 (44 rows)
        dns: DN 리스트 (33 DNs)

    Returns:
        {
            "results": List[dict],  # 44개 검증 결과
            "summary": dict         # 통계 요약
        }

    Algorithm:
        1. 모든 (invoice, DN) 쌍의 점수 계산
        2. 점수 기준 내림차순 정렬
        3. 그리디 할당 (capacity 존중)
        4. 미매칭 사유 분류

    Score Formula:
        0.45 * origin_sim + 0.45 * dest_sim + 0.10 * vehicle_sim

    Thresholds:
        - DN_ORIGIN_THR: 0.27
        - DN_DEST_THR: 0.50
        - DN_VEH_THR: 0.30
        - DN_MIN_SCORE: 0.40
    """
```

---

## 📘 src/utils/utils_normalize.py

#### normalize_location()
```python
def normalize_location(s: str) -> str:
    """위치명 정규화"""
    # Args, Returns 생략 (위 참조)
```

#### token_set_jaccard()
```python
def token_set_jaccard(a: str, b: str) -> float:
    """
    토큰 집합 Jaccard 유사도

    Time Complexity: O(n) where n = |tokens|
    Space Complexity: O(n)

    Performance:
        - 1,000 calls: ~0.01초
        - 10,000 calls: ~0.1초
    """
```

---

## 📘 src/utils/location_canon.py

#### expand_location_abbrev()
```python
def expand_location_abbrev(s: str) -> str:
    """
    약어 확장

    Mappings:
        16개 패턴 (정규식 기반)

    Example:
        "DSV" → "DSV MUSSAFAH"
        "MOSB" → "SAMSUNG MOSB"
    """
```

---

## 📘 src/utils/pdf_text_fallback.py

#### extract_text_any()
```python
def extract_text_any(pdf_path: str) -> str:
    """
    PDF 텍스트 추출 (4-layer fallback)

    Backends:
        1. PyMuPDF (fitz) - 0.5초/파일
        2. pypdf - 1초/파일
        3. pdfminer.six - 2초/파일
        4. pdftotext - 3초/파일

    Fallback Logic:
        각 백엔드를 순차 시도
        텍스트가 추출되면 즉시 반환
        모두 실패 시 빈 문자열
    """
```

---

## 📘 src/utils/pdf_extractors.py

#### extract_from_pdf_text()
```python
def extract_from_pdf_text(raw_text: str) -> dict:
    """
    PDF 본문에서 필드 추출

    Returns:
        {
            "destination": str,        # "Destination:" 이전 줄
            "loading_point": str,      # Description 키워드
            "waybill_no": str,         # "Waybill No." 패턴
            "destination_code": str    # "Destination Code:" 패턴
        }

    Extraction Accuracy:
        - Destination: 97.1%
        - Loading Point: 47.3%
        - Waybill No: 90%+
        - Destination Code: 85%+
    """
```

---

## 📘 src/utils/dn_capacity.py

#### load_capacity_overrides()
```python
def load_capacity_overrides() -> Dict[str, int]:
    """
    Capacity 오버라이드 로드

    Source Priority:
        1. DN_CAPACITY_MAP (JSON string)
        2. DN_CAPACITY_FILE (JSON file)

    Return Example:
        {
            "HVDC-ADOPT-SCT-0126": 16,
            "HVDC-DSV-PRE-MIR-SHU-230": 7
        }
    """
```

#### apply_capacity_overrides()
```python
def apply_capacity_overrides(
    dn_list: List[dict],
    mapping: Dict[str, int]
) -> None:
    """
    DN에 capacity 적용 (in-place 수정)

    Match Method:
        - 부분 일치 (shipment_ref 또는 filename)
        - 정규식 지원

    Side Effect:
        dn_list가 직접 수정됨
    """
```

#### auto_capacity_bump()
```python
def auto_capacity_bump(
    dn_list: List[dict],
    top_choice_counts: Dict[int, int]
) -> None:
    """
    자동 용량 증가

    Condition:
        DN_AUTO_CAPACITY_BUMP=true

    Logic:
        if demand > 1 and capacity == 1:
            capacity = min(demand, DN_MAX_CAPACITY)

    Side Effect:
        dn_list가 직접 수정됨
    """
```

---

## 📐 데이터 구조

### DN 객체
```python
{
    "meta": {
        "shipment_ref_from_folder": str,  # "HVDC-ADOPT-SCT-0126"
        "filename": str,                  # "HVDC-ADOPT-SCT-0126_DN.pdf"
        "pdf_path": str                   # 전체 경로
    },
    "data": {
        "destination": str,
        "loading_point": str,
        "waybill_no": str,
        "destination_code": str,
        "capacity": int,                 # PATCH3
        "truck_type": str,
        "driver_name": str
    },
    "raw_text": str                      # PDF 원본 텍스트
}
```

### Validation Result
```python
{
    "invoice_index": int,
    "dn_found": bool,
    "matched_shipment_ref": str,
    "matches": {
        "dn_origin_extracted": str,
        "dn_dest_extracted": str,
        "origin_similarity": float,
        "dest_similarity": float,
        "vehicle_similarity": float,
        "validation_status": "PASS|WARN|FAIL",
        "unmatched_reason": str         # PATCH3
    },
    "issues": List[dict]
}
```

---

## 🔢 상수

### 임계값
```python
DN_ORIGIN_THR = 0.27    # Origin 유사도
DN_DEST_THR = 0.50      # Destination 유사도
DN_VEH_THR = 0.30       # Vehicle 유사도
DN_MIN_SCORE = 0.40     # 최소 매칭 점수
```

### Capacity
```python
DN_CAPACITY_DEFAULT = 1   # 기본 용량
DN_MAX_CAPACITY = 16      # 최대 용량 (PATCH4)
```

### 점수 가중치
```python
ORIGIN_WEIGHT = 0.45
DEST_WEIGHT = 0.45
VEHICLE_WEIGHT = 0.10
```

---

## 📊 성능 벤치마크

### 함수별 처리 시간
| 함수 | 인보이스 1건 | 전체 44건 |
|------|-------------|----------|
| `normalize_location()` | <0.001초 | <0.044초 |
| `token_set_jaccard()` | <0.001초 | <0.044초 |
| `extract_text_any()` (PyMuPDF) | 0.5초 | 16.5초 |
| `cross_validate_invoice_dn()` | N/A | 2초 |
| **전체 파이프라인** | N/A | **약 8분** |

---

**문서 버전**: 1.0
**작성일**: 2025-10-13 22:53:00
**Status**: ✅ Complete
