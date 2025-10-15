좋아. 두 가지 이슈를 한 번에 잡는 **패치(diff)** 준비했다.

* 이슈 #1: `raw_text` 없을 때 PDF 본문 텍스트 **자동 폴백 추출**
* 이슈 #2: DN 다건 중복 매칭 방지용 **글로벌 1:1 할당(그리디 매칭)**

아래 패치를 `patch_v2.diff`로 저장 후 루트에서 `git apply patch_v2.diff` 하면 바로 적용된다.

---

```diff
*** Begin Patch
*** Add File: src/utils/pdf_text_fallback.py
+"""
+PDF 본문 텍스트 폴백 추출기
+- 우선순위: pypdf → pdfminer.six → pdftotext(외부) → 빈문자열
+"""
+from __future__ import annotations
+import os
+import subprocess
+from pathlib import Path
+from typing import Optional
+
+def _try_pypdf(pdf_path: str) -> str:
+    try:
+        # pypdf 또는 PyPDF2 호환
+        try:
+            from pypdf import PdfReader
+        except Exception:
+            from PyPDF2 import PdfReader  # type: ignore
+        reader = PdfReader(pdf_path)
+        texts = []
+        for p in getattr(reader, "pages", []):
+            try:
+                texts.append(p.extract_text() or "")
+            except Exception:
+                continue
+        return "\n".join(texts)
+    except Exception:
+        return ""
+
+def _try_pdfminer(pdf_path: str) -> str:
+    try:
+        from pdfminer.high_level import extract_text  # type: ignore
+        return extract_text(pdf_path) or ""
+    except Exception:
+        return ""
+
+def _try_pdftotext(pdf_path: str) -> str:
+    try:
+        out_txt = str(Path(pdf_path).with_suffix(".txt"))
+        # -layout: 멀티컬럼/표 포맷 유지에 유리
+        subprocess.run(
+            ["pdftotext", "-layout", pdf_path, out_txt],
+            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
+        )
+        if os.path.exists(out_txt):
+            with open(out_txt, "r", encoding="utf-8", errors="ignore") as f:
+                return f.read()
+        return ""
+    except Exception:
+        return ""
+
+def extract_text_any(pdf_path: str) -> str:
+    """가용 백엔드를 순차 시도하여 텍스트 추출."""
+    pdf_path = str(pdf_path)
+    for fn in (_try_pypdf, _try_pdfminer, _try_pdftotext):
+        txt = fn(pdf_path)
+        if txt and txt.strip():
+            return txt
+    return ""
+
*** End Patch
```

```diff
*** Begin Patch
*** Update File: validate_sept_2025_with_pdf.py
@@
 import os
 import re
 from pathlib import Path
 import pandas as pd
@@
 try:
     from src.utils.utils_normalize import normalize_location, token_set_jaccard
     from src.utils.location_canon import expand_location_abbrev
     from src.utils.pdf_extractors import extract_from_pdf_text
+    from src.utils.pdf_text_fallback import extract_text_any
 except Exception:  # 백업: 로컬 경로
     from utils.utils_normalize import normalize_location, token_set_jaccard
     from utils.location_canon import expand_location_abbrev
     from utils.pdf_extractors import extract_from_pdf_text
+    from utils.pdf_text_fallback import extract_text_any
@@
-ORIGIN_THR = 0.70
-DEST_THR   = 0.70
-VEH_THR    = 0.30
+# 임계값: 실제 분포 반영(환경변수로 오버라이드 가능)
+ORIGIN_THR = float(os.getenv("DN_ORIGIN_THR", "0.35"))
+DEST_THR   = float(os.getenv("DN_DEST_THR", "0.50"))
+VEH_THR    = float(os.getenv("DN_VEH_THR", "0.30"))
@@
 USE_PDF_FIELDS_FIRST = os.getenv("DN_USE_PDF_FIELDS_FIRST", "true").lower() == "true"
+# DN 1건당 기본 허용 매칭 수(용량). 기본 1(1:1 강제)
+DN_CAPACITY_DEFAULT = int(os.getenv("DN_CAPACITY_DEFAULT", "1"))
+# 매칭 스코어(원/목/차 가중합) 최소 허용치
+DN_MIN_SCORE = float(os.getenv("DN_MIN_SCORE", "0.40"))
@@
 def parse_dn_pdfs(dn_pdf_records):
     """
     DSVPDFParser 등으로 DN PDF를 파싱, dict 리스트 반환
     """
     results = []
     for rec in dn_pdf_records:
         # ... 기존 파싱 로직 ...
         dn_data = {
             # 기존 수집 필드들 (예: waybill_no, loading_point, destination, destination_code, description, truck_type 등)
         }
-        results.append(dn_data)
+        # --- [FIX-1] raw_text 누락 시 폴백 텍스트 추출 ---
+        pdf_text = (dn_data.get("raw_text")
+                    or dn_data.get("text")
+                    or "")
+        if not pdf_text and rec.get("pdf_path"):
+            try:
+                pdf_text = extract_text_any(rec["pdf_path"])
+            except Exception:
+                pdf_text = ""
+            if pdf_text:
+                dn_data["raw_text"] = pdf_text  # 디버깅/재사용 목적
+
+        # PDF 본문에서 핵심 필드 추출(본문 우선, 빈 값이면 기존 유지)
+        fields = extract_from_pdf_text(pdf_text)
+        if fields.get("dest_code"):
+            dn_data["destination_code"] = fields["dest_code"]
+        if fields.get("destination"):
+            dn_data["destination"] = fields["destination"]
+        if fields.get("loading_point"):
+            dn_data["loading_point"] = fields["loading_point"]
+        if fields.get("waybill"):
+            dn_data["waybill_no"] = dn_data.get("waybill_no") or fields["waybill"]
+
+        # DN 용량(기본 1). 필요시 dn_data["capacity"]로 오버라이드 가능
+        if "capacity" not in dn_data:
+            dn_data["capacity"] = DN_CAPACITY_DEFAULT
+
+        results.append(dn_data)
     return results
@@
-def cross_validate_invoice_dn(items_df, dn_list):
+def cross_validate_invoice_dn(items_df, dn_list):
     """
-    인보이스 라인아이템 ↔ DN 매칭/검증
+    인보이스 라인아이템 ↔ DN 매칭/검증
     - PDF 본문 필드(destination/loading_point/waybill/dest_code) 우선 사용
     - 파일명 라우트는 폴백(약어→표준 확장)
     - 유사도: 토큰 세트 자카드 (정규화 기반)
+    - [FIX-2] 글로벌 1:1 매칭(그리디)로 중복 DN할당 방지
     """
     def _sim(a: str, b: str) -> float:
         return token_set_jaccard(normalize_location(a), normalize_location(b))

+    def _score(inv_origin: str, inv_dest: str, inv_vehicle: str, dn: dict) -> float:
+        # 파일명 라우트(약어→표준)
+        fname = dn.get("filename", "") or dn.get("pdf_path", "")
+        o_guess, d_guess = extract_route_from_filename(os.path.basename(fname))
+        # 본문 우선/폴백
+        dn_dest_cand = dn.get("destination") or d_guess
+        dn_orig_cand = dn.get("loading_point") or o_guess
+        # 약어 → 표준
+        dn_dest_cand = expand_location_abbrev(dn_dest_cand)
+        dn_orig_cand = expand_location_abbrev(dn_orig_cand)
+        # 유사도
+        s_o = _sim(inv_origin, dn_orig_cand)
+        s_d = _sim(inv_dest,   dn_dest_cand)
+        s_v = _sim(inv_vehicle, str(dn.get("truck_type","")))
+        # 가중합(원/목 가중↑)
+        score = 0.45*s_o + 0.45*s_d + 0.10*s_v
+        return float(round(score, 6))
+
     # 인보이스 원천 컬럼(기존 컬럼명 사용 가정)
     inv_origin_col = "origin"
     inv_dest_col   = "destination"
     inv_vehicle_col= "vehicle"

     items_df = items_df.copy()
@@
-    # DN 인덱싱(필요시)
-    # ... 기존 인덱싱 로직 유지 ...
-
-    for idx, row in items_df.iterrows():
-        inv_origin = str(row.get(inv_origin_col, "") or "")
-        inv_dest   = str(row.get(inv_dest_col, "") or "")
-        inv_vehicle= str(row.get(inv_vehicle_col, "") or "")
-
-        # 후보 DN 선택(기존 점수 기반 선택 로직 재사용/호출 가정)
-        dn = select_best_dn_for_row(row, dn_list)  # 기존 함수/로직 사용
-        if not dn:
-            items_df.at[idx, "dn_validation_status"] = "FAIL"
-            continue
-
-        # 파일명 라우트(약어→표준)
-        fname = dn.get("filename", "") or dn.get("pdf_path", "")
-        o_guess, d_guess = extract_route_from_filename(os.path.basename(fname))
-
-        # PDF 본문 우선/롤백 스위치
-        if USE_PDF_FIELDS_FIRST:
-            dn_dest_cand = dn.get("destination") or d_guess
-            dn_orig_cand = dn.get("loading_point") or o_guess
-        else:
-            dn_dest_cand, dn_orig_cand = d_guess, o_guess
-
-        # 최종 후보도 약어→표준 1회 보정
-        dn_dest_cand = expand_location_abbrev(dn_dest_cand)
-        dn_orig_cand = expand_location_abbrev(dn_orig_cand)
-
-        # 유사도
-        s_origin  = _sim(inv_origin, dn_orig_cand)
-        s_dest    = _sim(inv_dest, dn_dest_cand)
-        s_vehicle = _sim(inv_vehicle, str(dn.get("truck_type","")))
-
-        origin_ok  = s_origin  >= ORIGIN_THR
-        dest_ok    = s_dest    >= DEST_THR
-        vehicle_ok = s_vehicle >= VEH_THR
-
-        status = "PASS" if (origin_ok and dest_ok and vehicle_ok) else ("WARN" if (origin_ok or dest_ok) else "FAIL")
-
-        # 기록
-        items_df.at[idx, "dn_matched"]           = "Yes"
-        items_df.at[idx, "dn_origin_extracted"]  = dn.get("loading_point","")
-        items_df.at[idx, "dn_dest_extracted"]    = dn.get("destination","")
-        items_df.at[idx, "dn_dest_code"]         = dn.get("destination_code","")
-        items_df.at[idx, "dn_do_number"]         = dn.get("waybill_no","") or dn.get("order_number","")
-        items_df.at[idx, "dn_truck_type"]        = dn.get("truck_type","")
-        items_df.at[idx, "dn_driver"]            = dn.get("driver_name","")
-        items_df.at[idx, "dn_origin_similarity"] = round(s_origin, 3)
-        items_df.at[idx, "dn_dest_similarity"]   = round(s_dest, 3)
-        items_df.at[idx, "dn_vehicle_similarity"]= round(s_vehicle, 3)
-        items_df.at[idx, "dn_validation_status"] = status
-        items_df.at[idx, "dn_origin_final"]      = dn_orig_cand
-        items_df.at[idx, "dn_dest_final"]        = dn_dest_cand
+    # --- [FIX-2] 글로벌 그리디 매칭(1:1) ---
+    # 모든 (row, dn) 쌍의 스코어를 계산 → 내림차순 정렬 → 용량(capacity) 소진 방식으로 배분
+    pairs = []
+    for idx, row in items_df.iterrows():
+        inv_origin = str(row.get(inv_origin_col, "") or "")
+        inv_dest   = str(row.get(inv_dest_col, "") or "")
+        inv_vehicle= str(row.get(inv_vehicle_col, "") or "")
+        for j, dn in enumerate(dn_list):
+            sc = _score(inv_origin, inv_dest, inv_vehicle, dn)
+            if sc >= DN_MIN_SCORE:
+                pairs.append((float(sc), idx, j))
+    pairs.sort(key=lambda x: x[0], reverse=True)
+
+    # DN 용량 테이블
+    dn_capacity = {j: int(dn_list[j].get("capacity", DN_CAPACITY_DEFAULT)) for j in range(len(dn_list))}
+    assigned_row = set()
+    pick_for_row = {}
+    for sc, idx, j in pairs:
+        if idx in assigned_row:
+            continue
+        if dn_capacity.get(j, 0) <= 0:
+            continue
+        # 할당
+        pick_for_row[idx] = j
+        assigned_row.add(idx)
+        dn_capacity[j] -= 1
+
+    # 기록 반영
+    for idx, row in items_df.iterrows():
+        inv_origin = str(row.get(inv_origin_col, "") or "")
+        inv_dest   = str(row.get(inv_dest_col, "") or "")
+        inv_vehicle= str(row.get(inv_vehicle_col, "") or "")
+
+        if idx not in pick_for_row:
+            items_df.at[idx, "dn_validation_status"] = "FAIL"
+            continue
+        dn = dn_list[pick_for_row[idx]]
+
+        # 파일명 라우트(약어→표준)
+        fname = dn.get("filename", "") or dn.get("pdf_path", "")
+        o_guess, d_guess = extract_route_from_filename(os.path.basename(fname))
+        # 본문 우선/롤백 스위치
+        if USE_PDF_FIELDS_FIRST:
+            dn_dest_cand = dn.get("destination") or d_guess
+            dn_orig_cand = dn.get("loading_point") or o_guess
+        else:
+            dn_dest_cand, dn_orig_cand = d_guess, o_guess
+        # 최종 후보 약어→표준
+        dn_dest_cand = expand_location_abbrev(dn_dest_cand)
+        dn_orig_cand = expand_location_abbrev(dn_orig_cand)
+
+        # 유사도
+        s_origin  = _sim(inv_origin, dn_orig_cand)
+        s_dest    = _sim(inv_dest,   dn_dest_cand)
+        s_vehicle = _sim(inv_vehicle, str(dn.get("truck_type","")))
+
+        origin_ok  = s_origin  >= ORIGIN_THR
+        dest_ok    = s_dest    >= DEST_THR
+        vehicle_ok = s_vehicle >= VEH_THR
+        status = "PASS" if (origin_ok and dest_ok and vehicle_ok) else ("WARN" if (origin_ok or dest_ok) else "FAIL")
+
+        # 기록
+        items_df.at[idx, "dn_matched"]           = "Yes"
+        items_df.at[idx, "dn_origin_extracted"]  = dn.get("loading_point","")
+        items_df.at[idx, "dn_dest_extracted"]    = dn.get("destination","")
+        items_df.at[idx, "dn_dest_code"]         = dn.get("destination_code","")
+        items_df.at[idx, "dn_do_number"]         = dn.get("waybill_no","") or dn.get("order_number","")
+        items_df.at[idx, "dn_truck_type"]        = dn.get("truck_type","")
+        items_df.at[idx, "dn_driver"]            = dn.get("driver_name","")
+        items_df.at[idx, "dn_origin_similarity"] = round(s_origin, 3)
+        items_df.at[idx, "dn_dest_similarity"]   = round(s_dest, 3)
+        items_df.at[idx, "dn_vehicle_similarity"]= round(s_vehicle, 3)
+        items_df.at[idx, "dn_validation_status"] = status
+        items_df.at[idx, "dn_origin_final"]      = dn_orig_cand
+        items_df.at[idx, "dn_dest_final"]        = dn_dest_cand

     return items_df
*** End Patch
```

```diff
*** Begin Patch
*** Update File: debug_pdf_extraction.py
@@
 try:
     from src.utils.pdf_extractors import extract_from_pdf_text
     from src.utils.location_canon import expand_location_abbrev
     from src.utils.utils_normalize import normalize_location, token_set_jaccard
+    from src.utils.pdf_text_fallback import extract_text_any
 except Exception:
     from utils.pdf_extractors import extract_from_pdf_text
     from utils.location_canon import expand_location_abbrev
     from utils.utils_normalize import normalize_location, token_set_jaccard
+    from utils.pdf_text_fallback import extract_text_any
@@
 def debug_one(pdf_path: str):
     """기존 파서로 파싱 + 보조 추출/정규화 결과를 같이 출력"""
     result = parse_with_existing_parser(pdf_path)  # 네가 쓰던 기존 파서 호출부
     print("\n=== Raw parser result (truncated) ===")
     pretty_print_core_fields(result)               # 기존 출력 유틸
@@
-    raw_text = result.get("raw_text") or result.get("text", "") or ""
+    raw_text = result.get("raw_text") or result.get("text", "") or ""
+    if not raw_text:
+        print("⚠️  raw_text 미존재 → 폴백(pypdf/pdfminer/pdftotext) 시도")
+        raw_text = extract_text_any(pdf_path)
+        print(f"   폴백 추출 길이: {len(raw_text)} chars")
     fields = extract_from_pdf_text(raw_text)
     print("\n--- PDF-fields (normalized) ---")
     print(f"dest_code   : {fields.get('dest_code')!r}")
     print(f"destination : {fields.get('destination')!r}")
     print(f"loading_point: {fields.get('loading_point')!r}")
*** End Patch
```

```diff
*** Begin Patch
*** Update File: debug_detailed.py
@@
+# DN 글로벌 매칭 검증용 보조 출력
+def print_dn_reuse_stats(items_df):
+    used = items_df["dn_do_number"].fillna("").astype(str)
+    counts = used[used != ""].value_counts().to_dict()
+    multi = {k: v for k, v in counts.items() if v > 1}
+    print("\n[DN Reuse Stats]")
+    print(f"  total unique DO/Waybill#: {len(counts)}")
+    print(f"  reused (>1): {len(multi)}")
+    if multi:
+        for k, v in list(multi.items())[:20]:
+            print(f"   - {k}: {v} items")
*** End Patch
```

```diff
*** Begin Patch
*** Update File: check_results.py
@@
 def main():
     df = load_latest_results()   # 기존 결과 로더 호출
     print_core_metrics(df)       # 기존 핵심지표
+    # DN 재사용 여부 점검(1:1 매칭 확인)
+    if "dn_do_number" in df.columns:
+        used = df["dn_do_number"].fillna("").astype(str)
+        reuse = used[used != ""].value_counts()
+        n_reuse = int((reuse > 1).sum())
+        print("\n[Consistency]")
+        print(f"DN reuse (>1) count: {n_reuse}")
+        if n_reuse > 0:
+            print("⚠️  일부 DO/Waybill 이 여러 아이템에 재사용되었습니다. DN_CAPACITY_DEFAULT=1 설정과 글로벌 매칭이 적용되었는지 확인하세요.")

 if __name__ == "__main__":
     main()
*** End Patch
```

---

## 어떻게 바뀌었나 (짧게 정리)

* **raw_text 부재 해결**: `extract_text_any()`가 pypdf → pdfminer → pdftotext 순으로 시도해 본문 텍스트를 확보. `validate_sept_2025_with_pdf.py`의 `parse_dn_pdfs()`에서 자동 폴백 적용.
* **DN 중복 매칭 방지**: 모든 `(invoice row, DN)` 조합을 스코어링 후, **내림차순 그리디 1:1 할당**. DN별 `capacity`(기본 1)로 중복 방지. 최저 스코어(`DN_MIN_SCORE`, 기본 0.40) 미만은 후보에서 제외.
* **임계값 현실화**: 기본값을 `0.35 / 0.50 / 0.30`으로 낮추고, `DN_ORIGIN_THR / DN_DEST_THR / DN_VEH_THR` 환경변수로 조정 가능.
* **검증 도우미**: `debug_pdf_extraction.py`가 폴백 추출 경로/길이 출력. `check_results.py`/`debug_detailed.py`가 **DN 재사용 카운트**를 보여줌.

## 실행 팁

```bash
# 패치 적용
git apply patch_v2.diff

# (선택) 임계값/용량 조정
export DN_ORIGIN_THR=0.35
export DN_DEST_THR=0.50
export DN_VEH_THR=0.30
export DN_MIN_SCORE=0.40
export DN_CAPACITY_DEFAULT=1
export DN_USE_PDF_FIELDS_FIRST=true

# 디버그
python debug_pdf_extraction.py  # 각 PDF에서 raw_text 폴백 확인
python validate_sept_2025_with_pdf.py
python check_results.py         # DN 재사용 여부/핵심지표 확인
```

원하면 `DN 용량(capacity)`을 특정 DN에만 2 이상으로 주어 다건 매칭 허용도 가능해. `parse_dn_pdfs()`에서 `dn_data["capacity"]=2` 식으로 개별 제어하면 끝.
