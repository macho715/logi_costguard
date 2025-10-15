# 개발 가이드 (Development Guide)

**프로젝트**: 9월 2025 DSV Domestic Invoice 검증 시스템
**대상**: 개발자, 유지보수 담당자
**버전**: PATCH4 (v4.0)

---

## 🛠️ 개발 환경 설정

### 필수 패키지
```bash
pip install pandas openpyxl
```

### 선택 패키지 (성능 향상)
```bash
pip install PyMuPDF      # PDF 추출 15~35배 빠름
pip install python-Levenshtein  # 유사도 계산 10배 빠름
```

### 개발 도구
```bash
pip install pytest       # 테스트
pip install black        # 코드 포맷팅
pip install pylint       # 린팅
```

---

## 📂 코드 구조

```
02_DSV_DOMESTIC/
├── validate_domestic_with_pdf.py    # 메인 스크립트 (1,548 lines)
├── enhanced_matching.py             # Enhanced Lane Matching
│
└── src/utils/                       # 유틸리티 모듈
    ├── __init__.py
    ├── utils_normalize.py           # 정규화, token_set_jaccard
    ├── location_canon.py            # 약어 확장
    ├── pdf_extractors.py            # PDF 필드 추출
    ├── pdf_text_fallback.py         # PDF 텍스트 다층 폴백
    └── dn_capacity.py               # DN Capacity 관리
```

---

## 🔧 주요 함수 수정 가이드

### 1. 유사도 임계값 조정
**파일**: `validate_domestic_with_pdf.py`
```python
# Line 29-31
DN_ORIGIN_THR = float(os.getenv("DN_ORIGIN_THR", "0.27"))
DN_DEST_THR = float(os.getenv("DN_DEST_THR", "0.50"))
DN_VEH_THR = float(os.getenv("DN_VEH_THR", "0.30"))
```

### 2. DN Capacity 기본값 변경
**파일**: `src/utils/dn_capacity.py`
```python
# Line 115
max_cap = _safe_int(os.getenv("DN_MAX_CAPACITY", "16"), 16)
```

### 3. PDF 추출 우선순위 변경
**파일**: `src/utils/pdf_text_fallback.py`
```python
# Line 101
for fn in (_try_pymupdf, _try_pypdf, _try_pdfminer, _try_pdftotext):
    # 순서 변경 가능
```

---

## 🧪 테스트

### 단위 테스트
```python
# test_utils.py
import pytest
from src.utils.utils_normalize import token_set_jaccard

def test_token_set_jaccard():
    assert token_set_jaccard("DSV MOSB", "MOSB DSV") == 1.0
    assert token_set_jaccard("ABC", "XYZ") == 0.0
```

### 통합 테스트
```bash
# 전체 파이프라인 실행
python validate_domestic_with_pdf.py

# 결과 검증
python verify_final_v2.py
```

---

## 🐛 디버깅

### 로그 활성화
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### DN 매칭 디버그
```python
# validate_domestic_with_pdf.py
# Line 730 근처에 추가
print(f"DEBUG: DN {j} - demand={demand}, capacity={cap}, gap={gap}")
```

---

## 📝 코딩 규약

### 함수 네이밍
- 동사로 시작: `extract_`, `calculate_`, `validate_`
- 명확한 의미: `token_set_jaccard` (O), `tsj` (X)

### 주석
- Docstring 필수 (함수 설명, Args, Returns)
- 복잡한 로직은 인라인 주석

### 타입 힌트
```python
def normalize_location(s: str) -> str:
    pass
```

---

## 🔄 새 기능 추가

### 예시: 새 유사도 알고리즘 추가

1. **함수 작성** (`src/utils/utils_normalize.py`):
```python
def cosine_similarity(a: str, b: str) -> float:
    # 구현
    pass
```

2. **통합** (`validate_domestic_with_pdf.py`):
```python
from src.utils.utils_normalize import cosine_similarity

# 점수 계산 시 사용
score = cosine_similarity(item.origin, dn.origin)
```

3. **테스트**:
```python
def test_cosine_similarity():
    assert cosine_similarity("ABC", "ABC") == 1.0
```

---

## 📊 성능 최적화

### 병렬 PDF 파싱
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(parse_dn_pdf, pdf_files)
```

### 캐싱
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def normalize_location(s: str) -> str:
    # 캐싱으로 속도 향상
    pass
```

---

## 🔒 보안

### PII 보호
```python
# 운전사 이름 등 개인정보 마스킹
driver_name = "***REDACTED***"
```

### NDA 준수
- Supporting Documents 외부 공유 금지
- 가격 정보 기밀 유지

---

**문서 버전**: 1.0
**작성일**: 2025-10-13 22:51:00

