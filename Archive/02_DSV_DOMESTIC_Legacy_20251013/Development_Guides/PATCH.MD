diff --git a/src/utils/utils_normalize.py b/src/utils/utils_normalize.py
new file mode 100644
index 0000000..2b8a1e3
--- /dev/null
+++ b/src/utils/utils_normalize.py
@@ -0,0 +1,54 @@
+# -*- coding: utf-8 -*-
+# utils_normalize.py — structural
+import re
+from typing import Set
+
+# DN 문서 접두/기관 표기 등 비교에 불필요한 토큰
+STOPWORDS: Set[str] = {"CICPA", "PMO"}
+
+def _squash_spaces(s: str) -> str:

+ return re.sub(r"\s+", " ", s).strip()
+

+def normalize_location(s: str) -> str:

+ """
+ 지명/시설명을 비교 가능한 표준 문자열로 정규화:
+ - 대문자화
+ - 영숫자/공백만 유지
+ - 다중 공백 축소
+ - STOPWORDS 제거
+ """
+ if not s:
+ return ""
+ s = s.upper()
+ s = re.sub(r"[^A-Z0-9\s]", " ", s)
+ s = _squash_spaces(s)
+ toks = [t for t in s.split() if t and t not in STOPWORDS]
+ return " ".join(toks)
+

+def token_set_jaccard(a: str, b: str) -> float:

+ """
+ 간단·견고한 토큰 세트 자카드 유사도.
+ """
+ A, B = set(a.split()), set(b.split())
+ if not A or not B:
+ return 0.0
+ return len(A & B) / len(A | B)
  diff --git a/src/utils/location_canon.py b/src/utils/location_canon.py
  new file mode 100644
  index 0000000..7a2d0f9
  --- /dev/null
  +++ b/src/utils/location_canon.py
  @@ -0,0 +1,46 @@
  +# -*- coding: utf-8 -*-
  +# location_canon.py — structural
  +import re
  +from .utils_normalize import normalize_location
+

+# 약어/변형 → 표준 지명 매핑 (필요시 항목 추가)
+_LOCATION_MAP = {

+ r"^DSV$": "DSV MUSSAFAH",
+ r"^MOSB$": "SAMSUNG MOSB",
+ r"^(MIR|MIRFA)$": "MIRFA PMO SAMSUNG",
+ r"^PRE$": "AGILITY M44 WAREHOUSE",
+ r"^MARKAZ$": "DSV MARKAZ",
+ r"^(SKM|SAMSUNG)$": "SAMSUNG",
+ r"^(SHU|SHUWEIHAT)$": "SHUWEIHAT",
  +}
+

+def expand_location_abbrev(s: str) -> str:

+ """
+ 파일명 약어/짧은 토큰을 표준 지명으로 확장.
+ 입력이 이미 정규화된 전체명이라면 그대로 반환.
+ """
+ s_norm = normalize_location(s)
+ for pat, canon in _LOCATION_MAP.items():
+ if re.match(pat, s_norm):
+ return canon
+ return s_norm
  diff --git a/src/utils/pdf_extractors.py b/src/utils/pdf_extractors.py
  new file mode 100644
  index 0000000..a3d5b72
  --- /dev/null
  +++ b/src/utils/pdf_extractors.py
  @@ -0,0 +1,66 @@
  +# -*- coding: utf-8 -*-
  +# pdf_extractors.py — structural
  +import re
  +from .utils_normalize import normalize_location
+

+DEST_CODE_RX = re.compile(r"Destination\s*Code\s*:\s*([0-9]{6,14})", re.I)
+DEST_RX      = re.compile(r"Destination\s*:\s*([A-Za-z0-9\s\-/]+)", re.I)
+LOAD_RX      = re.compile(r"(Loading\s*Point|Loading\s*Address)\s*:\s*([A-Za-z0-9\s\-/]+)", re.I)
+WAYBILL_RX   = re.compile(r"Delivery\s*Note/Waybill#\s*:\s*([A-Za-z0-9\-]+)", re.I)
+
+def _extract_field(text: str, rx: re.Pattern, group_idx: int = 1) -> str:

+ m = rx.search(text or "")
+ return m.group(group_idx).strip() if m else ""
+

+def extract_from_pdf_text(pdf_text: str) -> dict:

+ """
+ DN PDF 원문 텍스트에서 고신뢰 필드 추출.
+ 반환값은 비교 가능한 정규화 형태(destination/loading_point) 포함.
+ """
+ dest_code = _extract_field(pdf_text, DEST_CODE_RX)
+ dest_raw  = _extract_field(pdf_text, DEST_RX)
+ load_raw  = _extract_field(pdf_text, LOAD_RX, 2)
+ waybill   = _extract_field(pdf_text, WAYBILL_RX)
+
+ return {
+ "dest_code": dest_code,
+ "destination": normalize_location(dest_raw),
+ "loading_point": normalize_location(load_raw),
+ "waybill": waybill,
+ }
  diff --git a/validate_sept_2025_with_pdf.py b/validate_sept_2025_with_pdf.py
  index 6c0b6a3..9e31d7b 100644
  --- a/validate_sept_2025_with_pdf.py
  +++ b/validate_sept_2025_with_pdf.py
  @@ -1,10 +1,28 @@

# -*- coding: utf-8 -*-

import os
 import re
 import json
-from pathlib import Path
+from pathlib import Path
 from typing import Dict, List, Tuple, Optional
-----------------------------------------------

+#
+# NEW: normalization & pdf-field utils
+from src.utils.utils_normalize import normalize_location, token_set_jaccard
+from src.utils.location_canon import expand_location_abbrev
+from src.utils.pdf_extractors import extract_from_pdf_text
+
+# ---- DN 매칭 임계값 (조정시 여기만 바꾸면 됨)
+ORIGIN_THR: float = 0.70
+DEST_THR: float   = 0.70
+VEH_THR: float    = 0.30
+
+# 운영 중 긴급 롤백용 플래그 (기본: PDF 본문 필드 우선)
+USE_PDF_FIELDS_FIRST: bool = os.getenv("DN_USE_PDF_FIELDS_FIRST", "true").lower() == "true"
+
@@
-def extract_route_from_filename(filename: str) -> Tuple[str, str]:

- # 기존 구현 ...
- # return origin, destination

+def extract_route_from_filename(filename: str) -> Tuple[str, str]:

+ """
+ 파일명에서 라우트 추출 + 약어 확장/정규화 적용.
+ 기존 구현의 패턴 매칭은 유지하고, 반환 직전에 expand 적용.
+ """
+ # === 기존 구현 시작 ===
+ # ... (원래의 정규식/파싱 로직 그대로)
+ origin, destination = "", ""
+ # === 기존 구현 끝 ===
+ return expand_location_abbrev(origin), expand_location_abbrev(destination)
  @@
  -def cross_validate_invoice_dn(items_df, dn_records, enhanced_matching):

- """
-

좋아, “제안한 패치(약어 확장+정규화+PDF 본문 우선 추출+간단 자카드 유사도)”를 **기존 3개 스크립트**에 **깨끗이** 붙이는 방법을 한 번에 정리해줄게. 아래 순서대로 하면 된다. (각 파일 구조와 주요 함수 시그니처는 네가 올린 스크립트 그대로 참고했어: `scan_supporting_documents / parse_dn_pdfs / extract_* / cross_validate_invoice_dn` in `validate_sept_2025_with_pdf.py`, 디버그 러너는 `debug_pdf_extraction.py`, 분포·임계값 분석은 `optimize_dn_threshold.py`   ).

또 커밋 시에는 우리 규율대로 **구조(Structural) → 행위(Behavioral)**로 분리해 커밋해. (TDD + Tidy First 가이드)

---

# 0) 브랜치 & 레이아웃

```bash
git checkout -b feat/dn-normalize-and-match
mkdir -p src/utils
```

---

# 1) 신규 유틸 추가(구조 변경 · structural)

### 1-1. `src/utils/utils_normalize.py`

```python
import re

STOPWORDS = {"CICPA", "PMO"}

def _squash(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def normalize_location(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"[^A-Za-z0-9\s]", " ", s.upper())
    s = _squash(s)
    toks = [t for t in s.split() if t not in STOPWORDS]
    return " ".join(toks)

def token_set_jaccard(a: str, b: str) -> float:
    A, B = set(a.split()), set(b.split())
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)
```

### 1-2. `src/utils/location_canon.py`

```python
import re
from .utils_normalize import normalize_location

_LOCATION_MAP = {
    r"^DSV$": "DSV MUSSAFAH",
    r"^MOSB$": "SAMSUNG MOSB",
    r"^(MIR|MIRFA)$": "MIRFA PMO SAMSUNG",
    r"^PRE$": "AGILITY M44 WAREHOUSE",
    r"^MARKAZ$": "DSV MARKAZ",
    r"^(SKM|SAMSUNG)$": "SAMSUNG",
    r"^(SHU|SHUWEIHAT)$": "SHUWEIHAT",
}

def expand_location_abbrev(s: str) -> str:
    s = normalize_location(s)
    for pat, canon in _LOCATION_MAP.items():
        if re.match(pat, s):
            return canon
    return s
```

### 1-3. `src/utils/pdf_extractors.py`

```python
import re
from .utils_normalize import normalize_location

DEST_CODE_RX = re.compile(r"Destination\s*Code\s*:\s*([0-9]{6,14})", re.I)
DEST_RX      = re.compile(r"Destination\s*:\s*([A-Za-z0-9\s\-/]+)", re.I)
LOAD_RX      = re.compile(r"(Loading\s*Point|Loading\s*Address)\s*:\s*([A-Za-z0-9\s\-/]+)", re.I)
WAYBILL_RX   = re.compile(r"Delivery\s*Note/Waybill#\s*:\s*([A-Za-z0-9\-]+)", re.I)

def extract_field(text: str, rx: re.Pattern, group_idx: int=1) -> str:
    m = rx.search(text)
    return m.group(group_idx).strip() if m else ""

def extract_from_pdf_text(pdf_text: str) -> dict:
    dest_code = extract_field(pdf_text, DEST_CODE_RX)
    dest_raw  = extract_field(pdf_text, DEST_RX)
    load_raw  = extract_field(pdf_text, LOAD_RX, 2)
    waybill   = extract_field(pdf_text, WAYBILL_RX)

    return {
        "dest_code": dest_code,
        "destination": normalize_location(dest_raw),
        "loading_point": normalize_location(load_raw),
        "waybill": waybill,
    }
```

> 위 3개 파일은 순수  **구조 변경** (리네임·추출·신규 파일)이라 `structural(utils): add normalizer, canon map, pdf extractors` 로 커밋.

---

# 2) `validate_sept_2025_with_pdf.py` 패치(행위 변경 · behavioral)

이 파일은 **매칭 로직의 품질을 올리는** 쪽이라 **행위 변경**으로 커밋한다. 주요 포인트:

* **PDF 본문 필드 우선** (Destination/Destination Code/Loading Point/Waybill) → 파일명 라우트는 폴백
* **약어 확장** (DSV, MOSB, MIR, PRE, MARKAZ, SKM/SHU 등)
* **정규화 + 토큰 자카드 유사도**로 간단·빠른 매칭
* **임계값** : Origin ≥ 0.70, Destination ≥ 0.70, Vehicle ≥ 0.30

### 2-1. 상단 import 추가

```python
# 기존 import 아래에 추가
from src.utils.utils_normalize import normalize_location, token_set_jaccard
from src.utils.location_canon import expand_location_abbrev
from src.utils.pdf_extractors import extract_from_pdf_text
```

(해당 파일의 파서·추출·교차검증 골격은 너가 올린 그대로 유지: `scan_supporting_documents`, `parse_dn_pdfs`, `extract_*`, `cross_validate_invoice_dn` 등. 이 위치에 새 유틸을 부착한다 )

### 2-2. 파일명 라우트 확장 보강

기존 `extract_route_from_filename()`이 반환한 `(origin, dest)`에 **약어 확장**을 바로 적용:

```python
def extract_route_from_filename(filename: str) -> tuple:
    # ... 기존 로직 유지 ...
    o, d = parsed_origin, parsed_dest  # 기존 계산 결과
    return expand_location_abbrev(o), expand_location_abbrev(d)
```

### 2-3. DN 본문 → 필드 우선 추출

`parse_dn_pdfs()` 결과에서  **원문 텍스트** (있으면)로 `extract_from_pdf_text()`를 호출해 **dest_code/destination/loading_point/waybill**를 받는다. (이 값들 중 존재하는 것을 매칭에 우선 사용)

### 2-4. 매칭 함수 내 정규화 + 간단 유사도

`cross_validate_invoice_dn()` 내부(또는 별도 `match_invoice_dn`)에서:

```python
ORIGIN_THR = 0.70
DEST_THR   = 0.70
VEH_THR    = 0.30

def _sim(a: str, b: str) -> float:
    return token_set_jaccard(normalize_location(a), normalize_location(b))

# 후보 선택
dn_dest_cand = expand_location_abbrev(dn_fields.get("destination") or dn_dest_guess)
dn_orig_cand = expand_location_abbrev(dn_fields.get("loading_point") or dn_origin_guess)

s_origin = _sim(invoice_origin, dn_orig_cand)
s_dest   = _sim(invoice_dest, dn_dest_cand)
s_vehicle= _sim(invoice_vehicle, dn_vehicle)

origin_ok = s_origin >= ORIGIN_THR
dest_ok   = s_dest   >= DEST_THR
vehicle_ok= s_vehicle>= VEH_THR

status = "PASS" if (origin_ok and dest_ok and vehicle_ok) else ("WARN" if (origin_ok or dest_ok) else "FAIL")
```

### 2-5. Excel 기록 컬럼 유지/보강

기존 컬럼(`dn_origin_similarity`, `dn_dest_similarity`, `dn_vehicle_similarity`, `dn_validation_status`)은 **그대로 유지**하고, 최종 비교에 사용된 **표준화된 Origin/Dest**를 기록:

```python
items_df["dn_origin_final"] = dn_orig_cand
items_df["dn_dest_final"]   = dn_dest_cand
```

> 이 변경은 **행위 변경**이므로:
>
> `behavioral(parser): prefer PDF fields; add abbrev+normalize; switch to token-set jaccard; tighten ORIGIN/DEST thresholds`

---

# 3) `debug_pdf_extraction.py` 패치(행위 변경 · behavioral)

현재 스크립트는 `DSVPDFParser`로 파싱한 후 주요 필드를 인쇄하고, 우리가 구현한 `extract_*` 함수도 테스트하고 있어. 여기에 **신규 유틸 사용**을 끼워 넣는다 :

### 3-1. 상단 import

```python
from src.utils.pdf_extractors import extract_from_pdf_text
from src.utils.location_canon import expand_location_abbrev
from src.utils.utils_normalize import normalize_location, token_set_jaccard
```

### 3-2. 파싱 후 보조 추출/정규화 출력

```python
raw_text = result.get("raw_text") or result.get("text", "")
fields = extract_from_pdf_text(raw_text)

print("\n🔎 PDF-fields (normalized):")
print(f"  dest_code: {fields['dest_code']!r}")
print(f"  destination: {fields['destination']!r}")
print(f"  loading_point: {fields['loading_point']!r}")
print(f"  waybill: {fields['waybill']!r}")

# 파일명 라우트(약어 확장)와 비교
o_guess, d_guess = extract_route_from_filename(filename)
o_guess = expand_location_abbrev(o_guess)
d_guess = expand_location_abbrev(d_guess)

print("\n🧭 Filename route (canonicalized):")
print(f"  origin_guess: {o_guess}")
print(f"  dest_guess  : {d_guess}")
```

> 이렇게 하면 샘플 3개 PDF에 대해 **본문 필드 vs 파일명 라우트**가 나란히 찍혀서, 매칭 로직이 제대로 먹는지 바로 볼 수 있어. (본 디버거의 테스트 골격은 올려준 그대로 재사용)

---

# 4) `optimize_dn_threshold.py` 점검(행위 유지 or 소폭 보강)

이 스크립트는 **엑셀 결과를 읽어 유사도 분포/임계값 시뮬레이션**을 뽑는 용도야. 우리가 `validate_sept_2025_with_pdf.py`에서 쓰는 **컬럼명(유사도 3종 + status)**은 그대로 유지하니, 로직은 대부분 변동 없음. 다만 **기본 권장 임계값 라벨**을 살짝 조정:

* “현재 임계값” 표시는 `0.70/0.70/0.30` 기준을 추가로 보여주고, 기존 텍스트는 보완하면 됨.
* 나머지 분포/시뮬은 현행 컬럼을 그대로 사용. (입출력 경로/시트명도 현재 코드대로 유지)

---

# 5) 안전장치(롤백·폴백)

운영 중 문제가 보이면 **환경변수 플래그** 하나로 과거 로직으로 되돌릴 수 있게 해두자.

```python
import os
USE_PDF_FIELDS_FIRST = os.getenv("DN_USE_PDF_FIELDS_FIRST", "true").lower() == "true"
# cross_validate_invoice_dn 내에서:
if USE_PDF_FIELDS_FIRST:
    dn_dest_cand = expand_location_abbrev(dn_fields.get("destination") or dn_dest_guess)
    dn_orig_cand = expand_location_abbrev(dn_fields.get("loading_point") or dn_origin_guess)
else:
    dn_dest_cand = d_guess_from_filename_only
    dn_orig_cand = o_guess_from_filename_only
```

---

# 6) 빠른 검증 루틴

```bash
# 1) 디버깅 프린트로 PDF 본문 → 추출 확인
python debug_pdf_extraction.py

# 2) 9월 엑셀 결과에 대한 분포·임계값 재검토
python optimize_dn_threshold.py
# "현재 임계값 (0.70/0.70/0.30)" 블록과 PASS/WARN/FAIL 변화 확인

# 3) 전체 파이프 실행 (기존 런북대로)
python validate_sept_2025_with_pdf.py  # 내부 scan→parse→cross-validate→엑셀 업데이트
```

각 스크립트의 **입출력 구조와 핵심 함수**는 네가 올린 버전을 존중해 그대로 사용하고, **정규화·약어 확장·자카드 유사도**만 덧댔다. (원본 스크립트 내부 함수 시그니처는 그대로: 디버거는 3개 샘플 PDF 파싱 및 필드 출력, 임계값 분석은 엑셀 `items` 시트의 `dn_*_similarity`를 읽어 통계/시뮬 출력)

---

# 7) 테스트(가벼운 단위 테스트 권장)

```
tests/
  test_normalize.py   # normalize_location/token_set_jaccard
  test_matcher.py     # 임계값 경계, 약어 확장 케이스
```

* 경계케이스: `"CICPA MIRFA PMO SAMSUNG"` → `MIRFA PMO SAMSUNG`
* 약어: `PRE`→`AGILITY M44 WAREHOUSE`, `MARKAZ`→`DSV MARKAZ`
* 유사도: `"DSV MUSSAFAH YARD"` vs `"DSV MUSSAFAH"` ≥ 0.70 판정

---

# 8) 커밋·PR 규율(요약)

* `structural(utils): add normalizer, canon map, pdf extractors`
* `behavioral(parser): feat: prefer PDF fields; abbrev+normalize; token-set jaccard; thr=0.70/0.70/0.30`
* `behavioral(debug): feat: show canonicalized route & pdf fields`
* `behavioral(analysis): chore: update threshold report blocks`

> 머지 전 체크: 모든 테스트 통과, 포맷·린트 패스, 느린 테스트는 분리 태깅. (TDD+Tidy First 가이드 준수)

---

## 기대 효과

* 파일명 약어만으로 0.09x에 머물던 Origin/Dest 유사도가 **0.80±**로 튀고, `PASS` 비율이  **의미 있게 상승** .
* PDF 본문 신뢰필드(`Destination Code`, `Destination`, `Loading Point`, `Waybill`)를 먼저 쓰므로  **오탐/누락 크게 감소** .
* 매칭식은 자카드 기반 단순화 → **속도·일관성** 개선.

---

### 참고(원본 스크립트 레퍼런스)

* DN 스캔/파싱/교차검증 골격: `validate_sept_2025_with_pdf.py`
* 3개 샘플 PDF 디버그 러너: `debug_pdf_extraction.py`
* 유사도 분포·임계값 분석: `optimize_dn_threshold.py`

---

필요하면, 위 변경을 **패치 파일(diff)** 형태로도 만들어 줄 수 있어. 지금은 “붙이는 법”을 한 번에 끝낼 수 있게 최소 침습으로 안내했다. 진행하면서 막히는 포인트 있으면 바로 알려줘—거기부터 같이 깔끔하게 풀자.
