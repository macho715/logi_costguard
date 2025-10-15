
(대상: `config_domestic_v2.json`, `domestic_validator_v2.py`, `run_domestic_audit_v2.py`)

---

# PATCH 0) `config_domestic_v2.json` (병합/추가)

아래 키들을 **기존 JSON에 병합**해. (동일 키 있으면 덮어쓰기)

```json
{
  "similarity": {
    "weights": { "origin": 0.35, "destination": 0.35, "vehicle": 0.10, "distance": 0.10, "rate": 0.10 },
    "distance_decay_km": 15.0,
    "rate_decay_pct": 30.0,
    "edge_threshold": 0.60,
    "dynamic": { "enabled": true, "min_threshold": 0.50, "use_distance": true }
  },
  "min_fare_model": {
    "enabled": true,
    "short_run_km": 10.0,
    "table": { "FLATBED": 200.0, "LOWBED": 600.0, "3 TON PU": 150.0, "7 TON PU": 200.0, "DEFAULT": 200.0 }
  },
  "region_rules": {
    "MUSSAFAH": ["MUSSAFAH", "ICAD", "MARKAZ", "M44"],
    "MINA": ["MINA", "FREEPORT", "ZAYED", "JDN"],
    "MIRFA": ["MIRFA"],
    "SHUWEIHAT": ["SHUWEIHAT", "S2", "S3"]
  },
  "fallbacks": {
    "use_region_pool": true,
    "km_tolerance": 15.0,
    "perkm_tolerance_pct": 30.0
  },
  "alias_suggestion": {
    "enabled": true,
    "min_similarity": 0.70
  }
}
```

---

# PATCH 1) `domestic_validator_v2.py` — 헬퍼 추가

▶️ **imports 아래**(기존 `import re` 없으면 추가) 이 블록을 **그대로 삽입**.

```python
import re

def _tok(s: str):
    return set(re.findall(r"[A-Za-z0-9]+", str(s).upper()))

def token_set_sim(a: str, b: str) -> float:
    A, B = _tok(a), _tok(b)
    if not A or not B: return 0.0
    return len(A & B) / len(A | B)

def trigram_sim(a: str, b: str) -> float:
    def grams(x: str):
        x = "  " + str(x).upper() + "  "
        return {x[i:i+3] for i in range(len(x)-2)}
    A, B = grams(a), grams(b)
    if not A or not B: return 0.0
    return len(A & B) / len(A | B)

def od_similarity(a: str, b: str) -> float:
    # 토큰세트 0.6 + 트리그램 0.4
    return 0.6 * token_set_sim(a, b) + 0.4 * trigram_sim(a, b)

def region_of(place: str, region_rules: dict | None = None) -> str:
    p = str(place).upper()
    if isinstance(region_rules, dict):
        for name, toks in region_rules.items():
            if any(t in p for t in toks):
                return name
    if "MUSSAFAH" in p or "ICAD" in p or "MARKAZ" in p or "M44" in p: return "MUSSAFAH"
    if "MINA" in p or "FREEPORT" in p or "ZAYED" in p or "JDN" in p:  return "MINA"
    if "MIRFA" in p: return "MIRFA"
    if "SHUWEIHAT" in p or "S2" in p or "S3" in p: return "SHUWEIHAT"
    return "OTHER"
```

---

# PATCH 2) `domestic_validator_v2.py` — **similarity_score** 교체

기존 `similarity_score` 함수 **전체를 아래로 교체**.

```python
def similarity_score(row, cand, weights, dist_decay_km, rate_decay_pct) -> float:
    # O/D는 부분일치 허용(od_similarity), 차량은 완전일치, 거리/요율 근접도는 감쇠
    s = 0.0
    s += weights["origin"]      * od_similarity(row["origin_norm"], cand["origin"])
    s += weights["destination"] * od_similarity(row["destination_norm"], cand["destination"])
    s += weights["vehicle"]     * (1.0 if str(row["vehicle"]).strip() == str(cand["vehicle"]).strip() else 0.0)

    # 거리 근접
    d_inv = row.get("distance_km", np.nan)
    d_ref = cand.get("median_distance_km", np.nan)
    if not pd.isna(d_inv) and not pd.isna(d_ref):
        diff = abs(float(d_inv) - float(d_ref))
        closeness = max(0.0, 1.0 - (diff / float(dist_decay_km)))
        s += weights["distance"] * closeness
    # 요율 근접
    r_inv = row.get("rate_usd", np.nan)
    r_ref = cand.get("median_rate_usd", np.nan)
    if not pd.isna(r_inv) and not pd.isna(r_ref) and r_ref != 0:
        diff_pct = abs((float(r_inv) - float(r_ref)) / float(r_ref)) * 100.0
        closeness = max(0.0, 1.0 - (diff_pct / float(rate_decay_pct)))
        s += weights["rate"] * closeness
    return s
```

---

# PATCH 3) `domestic_validator_v2.py` — **find_best_ref** 교체

기존 `find_best_ref` 함수 **전체를 아래로 교체**.
(동적 임계 + region 풀 + min-fare 순서로 보강)

```python
def find_best_ref(row, baseline_df, cfg) -> Tuple[float, dict]:
    W = cfg["similarity"]["weights"]
    dist_decay_km = cfg["similarity"]["distance_decay_km"]
    rate_decay_pct = cfg["similarity"]["rate_decay_pct"]
    thr_base = cfg["similarity"]["edge_threshold"]
    dyn = cfg["similarity"].get("dynamic", {})
    use_dyn = bool(dyn.get("enabled", False))
    min_thr = float(dyn.get("min_threshold", 0.50))

    # 1) Direct
    key = f'{row["origin_norm"]}||{row["destination_norm"]}||{row["vehicle"]}||{row.get("unit","per truck")}'
    direct = baseline_df[baseline_df["key"] == key]
    if not direct.empty:
        c = direct.iloc[0].to_dict()
        return float(c["median_rate_usd"]), {"method": "direct", "lane_id": c.get("lane_id")}

    # 2) Similarity within vehicle+unit
    pool = baseline_df[(baseline_df["vehicle"] == row["vehicle"]) & (baseline_df["unit"] == row.get("unit","per truck"))]
    if pool.empty:
        pool = baseline_df.copy()

    best = None
    best_score = -1.0
    for _, cand in pool.iterrows():
        score = similarity_score(row, cand, W, dist_decay_km, rate_decay_pct)
        # 동적 임계 (거리 가까우면 임계 낮춤: 0.55~0.60)
        thr = thr_base
        closeness = 0.0
        d_inv = row.get("distance_km", np.nan)
        d_ref = cand.get("median_distance_km", np.nan)
        if not pd.isna(d_inv) and not pd.isna(d_ref):
            diff = abs(float(d_inv) - float(d_ref))
            closeness = max(0.0, 1.0 - (diff / float(dist_decay_km)))
        if use_dyn:
            thr = max(min_thr, min(thr_base, 0.55 + 0.10 * (1.0 - closeness)))
        accept = (score >= thr) or (closeness >= 0.75 and score >= 0.50)
        if accept and score > best_score:
            best, best_score = cand, score
    if best is not None:
        return float(best["median_rate_usd"]), {"method": "similarity", "score": round(best_score, 3), "lane_id": best.get("lane_id")}

    # 3) Region pool fallback (거리±15km, $/km±30%)
    if cfg.get("fallbacks", {}).get("use_region_pool", True):
        ro = region_of(row["origin_norm"], cfg.get("region_rules"))
        rd = region_of(row["destination_norm"], cfg.get("region_rules"))
        pool = baseline_df[(baseline_df.get("region_o") == ro) &
                           (baseline_df.get("region_d") == rd) &
                           (baseline_df["vehicle"] == row["vehicle"]) &
                           (baseline_df["unit"] == row.get("unit","per truck"))]
        if not pool.empty:
            km_tol = float(cfg["fallbacks"].get("km_tolerance", 15.0))
            perkm_tol = float(cfg["fallbacks"].get("perkm_tolerance_pct", 30.0))
            inv_km = row.get("distance_km", np.nan)
            inv_perkm = (row.get("rate_usd", np.nan) / inv_km) if (not pd.isna(inv_km) and inv_km > 0) else np.nan

            if not pd.isna(inv_km):
                pool = pool[(pool["median_distance_km"].notna()) & (abs(pool["median_distance_km"] - inv_km) <= km_tol)]
            if not pd.isna(inv_perkm):
                pool = pool.assign(c_perkm = pool["median_rate_usd"] / pool["median_distance_km"]).dropna(subset=["c_perkm"])
                pool = pool[abs((pool["c_perkm"] - inv_perkm) / pool["c_perkm"] * 100.0) <= perkm_tol]

            if not pool.empty:
                cand = pool.iloc[(abs(pool["median_rate_usd"] - row.get("rate_usd", 0))).argsort().values[0]]
                return float(cand["median_rate_usd"]), {"method": "region_pool", "lane_id": cand.get("lane_id")}

    # 4) Min-Fare for short-run
    mf = cfg.get("min_fare_model", {})
    if mf.get("enabled", False):
        lim = float(mf.get("short_run_km", 10.0))
        table = mf.get("table", {})
        if pd.notna(row.get("distance_km")) and float(row["distance_km"]) <= lim:
            v = str(row["vehicle"]).upper()
            if v in table:
                return float(table[v]), {"method": "min_fare", "note": f"short_run≤{lim}km"}
            elif "DEFAULT" in table:
                return float(table["DEFAULT"]), {"method": "min_fare", "note": f"short_run≤{lim}km"}

    # 5) No reference
    return (np.nan, {"method": "none"})
```

---

# PATCH 4) `domestic_validator_v2.py` — baseline region/alias & artifact 확장

`validate_domestic()` 내부에서 **baseline 생성 직후** 아래 두 줄을 추가해 **지역 라벨**을 붙여줘.

```python
baseline["region_o"] = baseline["origin"].apply(lambda x: region_of(x, cfg.get("region_rules")))
baseline["region_d"] = baseline["destination"].apply(lambda x: region_of(x, cfg.get("region_rules")))
```

그리고 **함수 끝부분(artifact 만들기 직전)**에 **alias 제안**을 추가:

```python
def suggest_aliases(inv_df: pd.DataFrame, norm_map: dict, cfg: dict) -> pd.DataFrame:
    # 정규화 미적용(raw==norm)된 원천 텍스트에 대해 Canonical 후보 제안
    canon = set(norm_map.values()) if norm_map else set()
    raws = set()
    for col in ["origin", "destination"]:
        if col in inv_df.columns:
            raws.update([str(x).strip() for x in inv_df[col].dropna().unique()])
    rows = []
    min_sim = cfg.get("alias_suggestion", {}).get("min_similarity", 0.70)
    for raw in sorted(raws):
        normed = normalize_place(raw, norm_map)
        if str(normed).strip().lower() == str(raw).strip().lower():
            best, best_s = None, 0.0
            for c in canon:
                s = od_similarity(raw, c)
                if s > best_s:
                    best, best_s = c, s
            if best and best_s >= min_sim:
                rows.append({"raw_place": raw, "suggested": best, "similarity": round(best_s, 3)})
    return pd.DataFrame(rows)

# ...
alias_df = suggest_aliases(df, norm_map, cfg) if cfg.get("alias_suggestion", {}).get("enabled", True) else pd.DataFrame()
```

`artifact` 생성 시 **아래 키 추가**:

```python
"alias_suggestions": alias_df.head(50).to_dict(orient="records"),
```

---

# PATCH 5) `run_domestic_audit_v2.py` — alias 제안 저장

`proof` 작성 직후, **CSV 저장 로직**을 추가:

```python
# Proof artifact 저장 후 alias 제안 CSV도 함께 저장
alias = proof.get("artifact", {}).get("alias_suggestions")
if alias:
    import pandas as pd, os
    pd.DataFrame(alias).to_csv(os.path.join(args.outdir, "alias_suggestions.csv"), index=False)
```

---

## Smoke 테스트

```bash
python /mnt/data/domestic_audit_v2/run_domestic_audit_v2.py \
  --invoice "/mnt/data/Domestic_invoice_distance.xlsx" \
  --mapping "/mnt/data/mapping_update_20250819.xlsx" \
  --ledger  "/mnt/data/domestic result.xlsx" \
  --outdir  "/mnt/data/Results/Sept_2025_v2_patch"
```

* 기대: `LOW_SIMILARITY`가 유의미하게 감소, `domestic_audit_report_v2.xlsx` + `alias_suggestions.csv` 생성.

---

## 무엇이 달라지나 (체감 포인트)

* **부분일치**(토큰/트리그램)로 O/D 유사도↑ → 미매칭 감소.
* **동적 임계** + **region 풀** + **Min-Fare**로 **근거리/변형 표기**가 자동 흡수.
* 정기적으로 `alias_suggestions.csv` 승인만 해주면 **NormalizationMap**이 살아난다.

필요하면 위 블록들을 **완성 파일**로 묶어서도 줄 수 있어. 지금은 “붙여넣기”에 최적화된 형태로 끝냈다.
