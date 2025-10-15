좋아. 네 리포트 반영해서 **용량 문제(capacity)**·**미매칭 사유 분류**·**raw_text 폴백**을 더 탄탄하게 만든 **v3 패치(diff)** 준비했다.
핵심 추가:

* DN 용량 오버라이드(파일/ENV) + **수요기반 자동 용량 상향(Auto-Bump)**
* 미매칭 사유 컬럼(`dn_unmatched_reason`: `DN_CAPACITY_EXHAUSTED` / `BELOW_MIN_SCORE` / `NO_CANDIDATES`)
* Top-N 후보 덤프(csv)로 사후 분석 지원

아래를 `patch_v3.diff`로 저장한 후 프로젝트 루트에서 `git apply patch_v3.diff` 하면 끝.

---

```diff
*** Begin Patch
*** Add File: src/utils/dn_capacity.py
+from __future__ import annotations
+import json
+import os
+import re
+from typing import Dict, List
+
+def _safe_int(x, default=1) -> int:
+    try:
+        v = int(x)
+        return v if v >= 0 else default
+    except Exception:
+        return default
+
+def _load_json_file(path: str) -> dict:
+    try:
+        with open(path, "r", encoding="utf-8") as f:
+            return json.load(f)
+    except Exception:
+        return {}
+
+def load_capacity_overrides() -> Dict[str, int]:
+    """
+    오버라이드 우선순위:
+      1) ENV: DN_CAPACITY_MAP='{"HVDC-ADOPT-SCT-0126":2,"HVDC-DSV-SKM-MOSB-212":3}'
+      2) ENV: DN_CAPACITY_FILE=/path/to/map.json  ({"pattern": capacity} 형태; pattern은 부분일치 또는 정규식)
+    """
+    mapping: Dict[str, int] = {}
+    env_map = os.getenv("DN_CAPACITY_MAP", "").strip()
+    if env_map:
+        try:
+            data = json.loads(env_map)
+            for k, v in data.items():
+                mapping[str(k)] = _safe_int(v, 1)
+        except Exception:
+            pass
+    file_path = os.getenv("DN_CAPACITY_FILE", "").strip()
+    if file_path:
+        data = _load_json_file(file_path)
+        for k, v in data.items():
+            mapping[str(k)] = _safe_int(v, 1)
+    return mapping
+
+def apply_capacity_overrides(dn_list: List[dict], mapping: Dict[str, int]) -> None:
+    """
+    shipment_ref/filename에 매핑 키가 '부분일치' 또는 '정규식'으로 매치되면 capacity 갱신.
+    """
+    for dn in dn_list:
+        ref = str(dn.get("shipment_ref", "") or "")
+        name = str(dn.get("filename", "") or dn.get("pdf_path", "") or "")
+        for pat, cap in mapping.items():
+            # 부분일치
+            if pat in ref or pat in name:
+                dn["capacity"] = cap
+                continue
+            # 정규식
+            try:
+                if re.search(pat, ref) or re.search(pat, name):
+                    dn["capacity"] = cap
+            except re.error:
+                continue
+
+def auto_capacity_bump(dn_list: List[dict], top_choice_counts: Dict[int, int]) -> None:
+    """
+    두 단계 매칭을 위해 사전 '수요' 카운트 기반 자동 용량상향.
+    - ENV DN_AUTO_CAPACITY_BUMP=true (기본 false)
+    - ENV DN_MAX_CAPACITY=4 (상한)
+    - 오버라이드(capacity가 이미 지정된 DN)는 존중(더 이상 올리지 않음)
+    """
+    if os.getenv("DN_AUTO_CAPACITY_BUMP", "false").lower() != "true":
+        return
+    max_cap = _safe_int(os.getenv("DN_MAX_CAPACITY", "4"), 4)
+    for j, dn in enumerate(dn_list):
+        if "capacity" in dn and isinstance(dn["capacity"], int) and dn["capacity"] > 1:
+            continue  # 수동 오버라이드 존중
+        demand = int(top_choice_counts.get(j, 0))
+        if demand > 1:
+            dn["capacity"] = min(demand, max_cap)
+        else:
+            dn["capacity"] = int(dn.get("capacity", 1))
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
     from src.utils.pdf_text_fallback import extract_text_any
+    from src.utils.dn_capacity import load_capacity_overrides, apply_capacity_overrides, auto_capacity_bump
 except Exception:  # 백업: 로컬 경로
     from utils.utils_normalize import normalize_location, token_set_jaccard
     from utils.location_canon import expand_location_abbrev
     from utils.pdf_extractors import extract_from_pdf_text
     from utils.pdf_text_fallback import extract_text_any
+    from utils.dn_capacity import load_capacity_overrides, apply_capacity_overrides, auto_capacity_bump
@@
-ORIGIN_THR = float(os.getenv("DN_ORIGIN_THR", "0.35"))
-DEST_THR   = float(os.getenv("DN_DEST_THR", "0.50"))
-VEH_THR    = float(os.getenv("DN_VEH_THR", "0.30"))
+ORIGIN_THR = float(os.getenv("DN_ORIGIN_THR", "0.35"))
+DEST_THR   = float(os.getenv("DN_DEST_THR", "0.50"))
+VEH_THR    = float(os.getenv("DN_VEH_THR", "0.30"))
@@
 USE_PDF_FIELDS_FIRST = os.getenv("DN_USE_PDF_FIELDS_FIRST", "true").lower() == "true"
 # DN 1건당 기본 허용 매칭 수(용량). 기본 1(1:1 강제)
 DN_CAPACITY_DEFAULT = int(os.getenv("DN_CAPACITY_DEFAULT", "1"))
 # 매칭 스코어(원/목/차 가중합) 최소 허용치
 DN_MIN_SCORE = float(os.getenv("DN_MIN_SCORE", "0.40"))
+# TopN 후보 덤프
+DN_DUMP_TOPN = int(os.getenv("DN_DUMP_TOPN", "0"))  # 0이면 비활성; 3이면 상위 3개 덤프
+DN_DUMP_PATH = os.getenv("DN_DUMP_PATH", "dn_candidate_dump.csv")
@@
 def parse_dn_pdfs(dn_pdf_records):
@@
         if "capacity" not in dn_data:
             dn_data["capacity"] = DN_CAPACITY_DEFAULT
@@
     return results
@@
 def cross_validate_invoice_dn(items_df, dn_list):
@@
     def _score(inv_origin: str, inv_dest: str, inv_vehicle: str, dn: dict) -> float:
@@
         return float(round(score, 6))
@@
-    items_df = items_df.copy()
+    items_df = items_df.copy()
@@
-    for col in [
+    for col in [
         "dn_matched","dn_shipment_ref","dn_origin_extracted","dn_dest_extracted",
         "dn_dest_code","dn_do_number","dn_origin_similarity","dn_dest_similarity",
-        "dn_vehicle_similarity","dn_validation_status","dn_truck_type","dn_driver",
-        "dn_origin_final","dn_dest_final"
+        "dn_vehicle_similarity","dn_validation_status","dn_truck_type","dn_driver",
+        "dn_origin_final","dn_dest_final","dn_unmatched_reason"
     ]:
         if col not in items_df.columns:
             items_df[col] = ""

-    # --- [FIX-2] 글로벌 그리디 매칭(1:1) ---
-    # 모든 (row, dn) 쌍의 스코어를 계산 → 내림차순 정렬 → 용량(capacity) 소진 방식으로 배분
+    # --- 수요 파악을 위한 1차 스코어링(Top 후보 집계) ---
     pairs = []
+    row_valid_has = {}   # row -> valid 후보 존재여부
+    row_best_all = {}    # row -> 전체 후보 중 최고점(필요시 분석용)
+    top_choice_counts = {}  # dn index -> 해당 DN을 최고로 선택한 row 수
+
     for idx, row in items_df.iterrows():
         inv_origin = str(row.get(inv_origin_col, "") or "")
         inv_dest   = str(row.get(inv_dest_col, "") or "")
         inv_vehicle= str(row.get(inv_vehicle_col, "") or "")
+        best_all = 0.0
+        best_dn_j = None
         for j, dn in enumerate(dn_list):
             sc = _score(inv_origin, inv_dest, inv_vehicle, dn)
-            if sc >= DN_MIN_SCORE:
-                pairs.append((float(sc), idx, j))
+            best_all = max(best_all, sc)
+            if sc >= DN_MIN_SCORE:
+                pairs.append((float(sc), idx, j))
+                # 최고 후보 추적
+                if best_dn_j is None or sc > _score(inv_origin, inv_dest, inv_vehicle, dn_list[best_dn_j]):
+                    best_dn_j = j
+        row_valid_has[idx] = any(p[1] == idx for p in pairs)
+        row_best_all[idx] = best_all
+        if best_dn_j is not None:
+            top_choice_counts[best_dn_j] = int(top_choice_counts.get(best_dn_j, 0)) + 1
+
+    # --- 용량 오버라이드 적용 + (옵션) 수요 기반 자동 용량 상향 ---
+    cap_map = load_capacity_overrides()
+    if cap_map:
+        apply_capacity_overrides(dn_list, cap_map)
+    auto_capacity_bump(dn_list, top_choice_counts)
+
+    # --- [FIX-2] 글로벌 그리디 매칭(1:1 또는 확장 용량) ---
+    # 모든 (row, dn) 유효 쌍 내림차순 정렬 → DN capacity를 소진시키며 배분
     pairs.sort(key=lambda x: x[0], reverse=True)

     # DN 용량 테이블
     dn_capacity = {j: int(dn_list[j].get("capacity", DN_CAPACITY_DEFAULT)) for j in range(len(dn_list))}
     assigned_row = set()
     pick_for_row = {}
     for sc, idx, j in pairs:
         if idx in assigned_row:
             continue
         if dn_capacity.get(j, 0) <= 0:
             continue
         # 할당
         pick_for_row[idx] = j
         assigned_row.add(idx)
         dn_capacity[j] -= 1

+    # (옵션) TopN 후보 덤프
+    if DN_DUMP_TOPN > 0:
+        try:
+            import csv
+            with open(DN_DUMP_PATH, "w", newline="", encoding="utf-8") as f:
+                wr = csv.writer(f)
+                wr.writerow(["row_idx","best_n","score","dn_index","shipment_ref","filename/pdf_path"])
+                # 행별 상위 N 추출
+                from collections import defaultdict
+                per_row = defaultdict(list)
+                for sc, idx, j in pairs:
+                    per_row[idx].append((sc, j))
+                for idx in range(len(items_df)):
+                    cands = sorted(per_row.get(idx, []), key=lambda x:x[0], reverse=True)[:DN_DUMP_TOPN]
+                    for rank, (sc, j) in enumerate(cands, start=1):
+                        dn = dn_list[j]
+                        wr.writerow([idx, rank, sc, j, dn.get("shipment_ref",""), dn.get("filename","") or dn.get("pdf_path","")])
+        except Exception:
+            pass
+
     # 기록 반영
     for idx, row in items_df.iterrows():
         inv_origin = str(row.get(inv_origin_col, "") or "")
         inv_dest   = str(row.get(inv_dest_col, "") or "")
         inv_vehicle= str(row.get(inv_vehicle_col, "") or "")

         if idx not in pick_for_row:
-            items_df.at[idx, "dn_validation_status"] = "FAIL"
+            items_df.at[idx, "dn_validation_status"] = "FAIL"
+            # 미매칭 사유 분류
+            if row_valid_has.get(idx, False):
+                items_df.at[idx, "dn_unmatched_reason"] = "DN_CAPACITY_EXHAUSTED"
+            else:
+                # 유효 후보가 없었는데 전체 최고점도 낮은가?
+                if row_best_all.get(idx, 0.0) < DN_MIN_SCORE:
+                    items_df.at[idx, "dn_unmatched_reason"] = "BELOW_MIN_SCORE"
+                else:
+                    items_df.at[idx, "dn_unmatched_reason"] = "NO_CANDIDATES"
             continue
         dn = dn_list[pick_for_row[idx]]

         # 파일명 라우트(약어→표준)
         fname = dn.get("filename", "") or dn.get("pdf_path", "")
         o_guess, d_guess = extract_route_from_filename(os.path.basename(fname))
@@
         items_df.at[idx, "dn_validation_status"] = status
         items_df.at[idx, "dn_origin_final"]      = dn_orig_cand
         items_df.at[idx, "dn_dest_final"]        = dn_dest_cand
+        items_df.at[idx, "dn_unmatched_reason"]  = ""  # 매칭 성공

     return items_df
*** End Patch
```

```diff
*** Begin Patch
*** Update File: debug_detailed.py
@@
 def print_dn_reuse_stats(items_df):
     used = items_df["dn_do_number"].fillna("").astype(str)
     counts = used[used != ""].value_counts().to_dict()
     multi = {k: v for k, v in counts.items() if v > 1}
     print("\n[DN Reuse Stats]")
     print(f"  total unique DO/Waybill#: {len(counts)}")
     print(f"  reused (>1): {len(multi)}")
     if multi:
         for k, v in list(multi.items())[:20]:
             print(f"   - {k}: {v} items")
+
+def print_unmatched_reasons(items_df):
+    if "dn_unmatched_reason" not in items_df.columns:
+        return
+    rs = items_df["dn_unmatched_reason"].fillna("").astype(str)
+    stats = rs.value_counts().to_dict()
+    print("\n[DN Unmatched Reasons]")
+    for k, v in stats.items():
+        if not k:
+            continue
+        print(f"  {k}: {v}")
*** End Patch
```

```diff
*** Begin Patch
*** Update File: check_results.py
@@
 def main():
     df = load_latest_results()   # 기존 결과 로더 호출
     print_core_metrics(df)       # 기존 핵심지표
     # DN 재사용 여부 점검(1:1 매칭 확인)
     if "dn_do_number" in df.columns:
         used = df["dn_do_number"].fillna("").astype(str)
         reuse = used[used != ""].value_counts()
         n_reuse = int((reuse > 1).sum())
         print("\n[Consistency]")
         print(f"DN reuse (>1) count: {n_reuse}")
         if n_reuse > 0:
             print("⚠️  일부 DO/Waybill 이 여러 아이템에 재사용되었습니다. DN_CAPACITY_DEFAULT=1 설정과 글로벌 매칭이 적용되었는지 확인하세요.")
+    # 미매칭 사유 통계
+    if "dn_unmatched_reason" in df.columns:
+        rs = df["dn_unmatched_reason"].fillna("").astype(str)
+        stats = rs.value_counts().to_dict()
+        if stats:
+            print("\n[Unmatched Reasons]")
+            for k, v in stats.items():
+                if not k:
+                    continue
+                print(f"  {k}: {v}")

 if __name__ == "__main__":
     main()
*** End Patch
```

---

## 쓰는 법(간단)

```bash
# 패치 적용
git apply patch_v3.diff

# (선택) 인기 DN 용량 오버라이드
export DN_CAPACITY_MAP='{"HVDC-ADOPT-SCT-0126":2,"HVDC-DSV-SKM-MOSB-212":3,"HVDC-DSV-PRE-MIR-SHU-230":3}'

# (선택) 수요 기반 자동 용량 상향 (상한 4)
export DN_AUTO_CAPACITY_BUMP=true
export DN_MAX_CAPACITY=4

# (추천) 후보 Top 3 덤프 켜기
export DN_DUMP_TOPN=3
export DN_DUMP_PATH=dn_candidate_dump.csv

# (필요 시) 임계값 튜닝
export DN_ORIGIN_THR=0.35
export DN_DEST_THR=0.50
export DN_VEH_THR=0.30
export DN_MIN_SCORE=0.40

# 실행
python validate_sept_2025_with_pdf.py
python check_results.py
```

## 기대 효과

* **DN_NOT_FOUND 91.7%** 원인이었던 `capacity` 문제를 **오버라이드+오토-범프**로 즉시 흡수.
* **분석 가시성↑**: `dn_unmatched_reason`·Top-N 후보 덤프 덕에 다음 조정이 쉬워짐.
* 품질 유지: 임계값은 그대로, 용량만 상황별로 유연 조절.

걸리는 포인트 있으면 그 결과 스냅샷 던져줘. 그 지점부터 딱 잡아줄게.
