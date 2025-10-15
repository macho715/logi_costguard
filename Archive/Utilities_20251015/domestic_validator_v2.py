import os, json, hashlib, math
import re
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np

try:
    from sklearn.ensemble import IsolationForest

    SKLEARN_OK = True
except Exception:
    SKLEARN_OK = False


# ---------- PATCH 1: Helper functions ----------
def _tok(s: str):
    return set(re.findall(r"[A-Za-z0-9]+", str(s).upper()))


def token_set_sim(a: str, b: str) -> float:
    A, B = _tok(a), _tok(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def trigram_sim(a: str, b: str) -> float:
    def grams(x: str):
        x = "  " + str(x).upper() + "  "
        return {x[i : i + 3] for i in range(len(x) - 2)}

    A, B = grams(a), grams(b)
    if not A or not B:
        return 0.0
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
    if "MUSSAFAH" in p or "ICAD" in p or "MARKAZ" in p or "M44" in p:
        return "MUSSAFAH"
    if "MINA" in p or "FREEPORT" in p or "ZAYED" in p or "JDN" in p:
        return "MINA"
    if "MIRFA" in p:
        return "MIRFA"
    if "SHUWEIHAT" in p or "S2" in p or "S3" in p:
        return "SHUWEIHAT"
    return "OTHER"


# ---------- Utilities ----------
def sha256_of_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pii_mask(text: str, mask_char: str = "•") -> str:
    if not isinstance(text, str):
        return text
    # lightweight token masking: emails, phone-like digits
    t = text
    t = (
        pd.Series([t])
        .str.replace(
            r"[\w\.-]+@[\w\.-]+", lambda m: mask_char * len(m.group(0)), regex=True
        )
        .iloc[0]
    )
    t = (
        pd.Series([t])
        .str.replace(
            r"\b(\+?\d[\d\-\s]{6,}\d)\b",
            lambda m: mask_char * len(m.group(0)),
            regex=True,
        )
        .iloc[0]
    )
    return t


def abs_pct_diff(a: float, b: float) -> float:
    if b is None or b == 0 or pd.isna(b):
        return np.nan
    return (a - b) / b * 100.0


def band_of_delta(delta_pct: float, bands: Dict[str, float]) -> str:
    if pd.isna(delta_pct):
        return "UNKNOWN"
    ap = abs(delta_pct)
    if ap <= bands["pass"]:
        return "PASS"
    if ap <= bands["warn"]:
        return "WARN"
    if ap <= bands["high"]:
        return "HIGH"
    return "CRITICAL"


def winsorize_series(s: pd.Series, lower_q=0.05, upper_q=0.95) -> pd.Series:
    lo, hi = s.quantile(lower_q), s.quantile(upper_q)
    return s.clip(lower=lo, upper=hi)


# ---------- Loaders ----------
def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_mapping_excel(mapping_path: str) -> Dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(mapping_path)
    sheets = {}
    for name in [
        "NormalizationMap",
        "ApprovedLaneMap",
        "COST_GUARD_Standardized",
        "Unified_OD_Mapping_CG",
        "RefDestinationMap",
    ]:
        if name in xls.sheet_names:
            sheets[name] = pd.read_excel(mapping_path, sheet_name=name)
    return sheets


def build_normalizer(norm_df: pd.DataFrame) -> Dict[str, str]:
    m = {}
    if norm_df is None or norm_df.empty:
        return m
    for _, row in norm_df.iterrows():
        raw = str(row.get("raw_place", "")).strip()
        norm = str(row.get("normalized", "")).strip()
        if raw:
            m[raw.lower()] = norm
    return m


def normalize_place(v: str, norm_map: Dict[str, str]) -> str:
    if not isinstance(v, str):
        return v
    key = v.strip().lower()
    return norm_map.get(key, v.strip())


def canonicalize_od(df: pd.DataFrame, norm_map: Dict[str, str]) -> pd.DataFrame:
    df = df.copy()
    for col in ["origin", "destination", "origin_norm", "destination_norm"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
    df["origin_norm"] = df.get("origin_norm", df["origin"]).apply(
        lambda x: normalize_place(x, norm_map)
    )
    df["destination_norm"] = df.get("destination_norm", df["destination"]).apply(
        lambda x: normalize_place(x, norm_map)
    )
    return df


# ---------- Baseline builder ----------
def build_baseline_from_approved(approved_df: pd.DataFrame) -> pd.DataFrame:
    # Robustify: drop empties, winsorize rate & distance buckets
    df = approved_df.copy()
    for c in [
        "origin",
        "destination",
        "vehicle",
        "unit",
        "median_rate_usd",
        "median_distance_km",
    ]:
        if c not in df.columns:
            df[c] = np.nan
    df = df.dropna(
        subset=["origin", "destination", "vehicle", "unit", "median_rate_usd"]
    )
    # ensure types
    df["median_rate_usd"] = pd.to_numeric(df["median_rate_usd"], errors="coerce")
    df["median_distance_km"] = pd.to_numeric(df["median_distance_km"], errors="coerce")

    # winsorize medians per (vehicle, unit)
    def _win_grp(g):
        g = g.copy()
        g["median_rate_usd"] = winsorize_series(
            g["median_rate_usd"].astype(float)
        ).round(2)
        return g

    df = df.groupby(["vehicle", "unit"], group_keys=False).apply(_win_grp)
    # index for fast join
    df["key"] = (
        df["origin"].str.strip()
        + "||"
        + df["destination"].str.strip()
        + "||"
        + df["vehicle"].str.strip()
        + "||"
        + df["unit"].str.strip()
    )
    return df


# ---------- Similarity model ----------
def similarity_score(row, cand, weights, dist_decay_km, rate_decay_pct) -> float:
    # O/D는 부분일치 허용(od_similarity), 차량은 완전일치, 거리/요율 근접도는 감쇠
    s = 0.0
    s += weights["origin"] * od_similarity(row["origin_norm"], cand["origin"])
    s += weights["destination"] * od_similarity(
        row["destination_norm"], cand["destination"]
    )
    s += weights["vehicle"] * (
        1.0 if str(row["vehicle"]).strip() == str(cand["vehicle"]).strip() else 0.0
    )

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
        return float(c["median_rate_usd"]), {
            "method": "direct",
            "lane_id": c.get("lane_id"),
        }

    # 2) Similarity within vehicle+unit
    pool = baseline_df[
        (baseline_df["vehicle"] == row["vehicle"])
        & (baseline_df["unit"] == row.get("unit", "per truck"))
    ]
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
        return float(best["median_rate_usd"]), {
            "method": "similarity",
            "score": round(best_score, 3),
            "lane_id": best.get("lane_id"),
        }

    # 3) Region pool fallback (거리±15km, $/km±30%)
    if cfg.get("fallbacks", {}).get("use_region_pool", True):
        ro = region_of(row["origin_norm"], cfg.get("region_rules"))
        rd = region_of(row["destination_norm"], cfg.get("region_rules"))
        pool = baseline_df[
            (baseline_df.get("region_o") == ro)
            & (baseline_df.get("region_d") == rd)
            & (baseline_df["vehicle"] == row["vehicle"])
            & (baseline_df["unit"] == row.get("unit", "per truck"))
        ]
        if not pool.empty:
            km_tol = float(cfg["fallbacks"].get("km_tolerance", 15.0))
            perkm_tol = float(cfg["fallbacks"].get("perkm_tolerance_pct", 30.0))
            inv_km = row.get("distance_km", np.nan)
            inv_perkm = (
                (row.get("rate_usd", np.nan) / inv_km)
                if (not pd.isna(inv_km) and inv_km > 0)
                else np.nan
            )

            if not pd.isna(inv_km):
                pool = pool[
                    (pool["median_distance_km"].notna())
                    & (abs(pool["median_distance_km"] - inv_km) <= km_tol)
                ]
            if not pd.isna(inv_perkm):
                pool = pool.assign(
                    c_perkm=pool["median_rate_usd"] / pool["median_distance_km"]
                ).dropna(subset=["c_perkm"])
                pool = pool[
                    abs((pool["c_perkm"] - inv_perkm) / pool["c_perkm"] * 100.0)
                    <= perkm_tol
                ]

            if not pool.empty:
                cand = pool.iloc[
                    (abs(pool["median_rate_usd"] - row.get("rate_usd", 0)))
                    .argsort()
                    .values[0]
                ]
                return float(cand["median_rate_usd"]), {
                    "method": "region_pool",
                    "lane_id": cand.get("lane_id"),
                }

    # 4) Min-Fare for short-run
    mf = cfg.get("min_fare_model", {})
    if mf.get("enabled", False):
        lim = float(mf.get("short_run_km", 10.0))
        table = mf.get("table", {})
        if pd.notna(row.get("distance_km")) and float(row["distance_km"]) <= lim:
            v = str(row["vehicle"]).upper()
            if v in table:
                return float(table[v]), {
                    "method": "min_fare",
                    "note": f"short_run≤{lim}km",
                }
            elif "DEFAULT" in table:
                return float(table["DEFAULT"]), {
                    "method": "min_fare",
                    "note": f"short_run≤{lim}km",
                }

    # 5) No reference
    return (np.nan, {"method": "none"})


# ---------- Special zone router ----------
def build_special_key(origin_norm, destination_norm, vehicle, unit):
    return f"{origin_norm}||{destination_norm}||{vehicle}||{unit}"


def build_special_set(ledger_df: pd.DataFrame) -> set:
    if ledger_df is None or ledger_df.empty:
        return set()
    cols = {c.lower(): c for c in ledger_df.columns}
    # Try to map likely columns
    on = cols.get("origin_norm", cols.get("origin", None))
    dn = cols.get("destination_norm", cols.get("destination", None))
    v = cols.get("vehicle", None)
    u = cols.get("unit", None)
    special = set()
    if on and dn and v:
        if u is None and "unit" not in cols:
            u = "per truck"
        for _, r in ledger_df.iterrows():
            key = build_special_key(
                str(r[on]).strip(),
                str(r[dn]).strip(),
                str(r[v]).strip(),
                str(r.get(u, "per truck")).strip(),
            )
            special.add(key)
    return special


# ---------- PATCH 4: Alias suggestion ----------
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
        # Check if normalization happened
        normed_col = f"{col}_norm" if col in inv_df.columns else col
        # Simple check: if raw text is still raw after normalization
        if raw not in canon:
            best, best_s = None, 0.0
            for c in canon:
                s = od_similarity(raw, c)
                if s > best_s:
                    best, best_s = c, s
            if best and best_s >= min_sim:
                rows.append(
                    {
                        "raw_place": raw,
                        "suggested": best,
                        "similarity": round(best_s, 3),
                    }
                )
    return pd.DataFrame(rows)


# ---------- Main validation ----------
def validate_domestic(
    invoice_df: pd.DataFrame,
    mapping_path: str,
    config_path: str,
    executed_ledger_df: pd.DataFrame = None,
):
    cfg = load_config(config_path)
    sheets = load_mapping_excel(mapping_path)
    norm_map = build_normalizer(sheets.get("NormalizationMap", pd.DataFrame()))
    approved = sheets.get("ApprovedLaneMap", pd.DataFrame())

    # Normalize invoice rows
    df = invoice_df.copy()
    for col in ["rate_usd", "distance_km"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = canonicalize_od(df, norm_map)

    # Build baseline index
    baseline = build_baseline_from_approved(approved)

    # PATCH 4: baseline에 region 라벨 추가
    baseline["region_o"] = baseline["origin"].apply(
        lambda x: region_of(x, cfg.get("region_rules"))
    )
    baseline["region_d"] = baseline["destination"].apply(
        lambda x: region_of(x, cfg.get("region_rules"))
    )

    # Special zones from executed ledger
    special_set = (
        build_special_set(executed_ledger_df)
        if cfg.get("special_zone", {}).get("enabled", False)
        else set()
    )

    # Find ref & compute delta
    ref_rates = []
    ref_meta = []
    for _, row in df.iterrows():
        ref, meta = find_best_ref(row, baseline, cfg)
        ref_rates.append(ref)
        ref_meta.append(meta)
    df["ref_rate_usd"] = ref_rates
    df["ref_method"] = [m.get("method") for m in ref_meta]
    df["ref_lane_alias"] = [m.get("alias") for m in ref_meta]
    df["ref_lane_id"] = [m.get("lane_id") for m in ref_meta]
    df["delta_pct"] = df.apply(
        lambda r: abs_pct_diff(r["rate_usd"], r["ref_rate_usd"]), axis=1
    )

    # Bands
    bands = cfg["cost_guard_bands"]
    df["cg_band"] = df["delta_pct"].apply(lambda d: band_of_delta(d, bands))

    # Special pass override
    def _special_status(r):
        k = build_special_key(
            r["origin_norm"],
            r["destination_norm"],
            r["vehicle"],
            r["unit"] if "unit" in r else "per truck",
        )
        if k in special_set:
            return cfg["special_zone"]["label"]
        return None

    df["special_status"] = df.apply(_special_status, axis=1)

    # Final verdict
    def final_verdict(row):
        if row["special_status"]:
            return row["special_status"]
        band = row["cg_band"]
        if pd.isna(band) or band == "UNKNOWN":
            return "PENDING_REVIEW"
        if band == "CRITICAL" and row["delta_pct"] > cfg["autofail_threshold_pct"]:
            return "FAIL"
        if band in ["HIGH", "WARN"]:
            return "PENDING_REVIEW"
        return "VERIFIED"

    df["verdict"] = df.apply(final_verdict, axis=1)

    # IsolationForest anomaly
    if cfg["isoforest"]["enabled"] and SKLEARN_OK:
        feats = df[["rate_usd", "distance_km"]].copy()
        feats = feats.fillna(feats.median(numeric_only=True))
        try:
            iso = IsolationForest(
                contamination=cfg["isoforest"]["contamination"],
                n_estimators=cfg["isoforest"]["n_estimators"],
                random_state=cfg["isoforest"]["random_state"],
            )
            iso.fit(feats)
            df["anomaly"] = (iso.predict(feats) == -1).astype(int)
        except Exception:
            df["anomaly"] = 0
    else:
        df["anomaly"] = 0

    # Short-run flags
    sr = cfg["short_run_rules"]
    df["short_run_flag"] = np.where(
        df["distance_km"] <= sr["short_run_thresh_km"], 1, 0
    )
    df["fixed_cost_suspect"] = np.where(
        df["distance_km"] <= sr["fixed_cost_suspect_km"], 1, 0
    )

    # Risk score (Δ normalized to autofail threshold; cert/signature placeholders = 0)
    af_thr = cfg["autofail_threshold_pct"]

    def _risk(row):
        delta_norm = min(
            1.0,
            (abs(row["delta_pct"]) if not pd.isna(row["delta_pct"]) else 0.0) / af_thr,
        )
        anomaly = 1.0 if row.get("anomaly", 0) == 1 else 0.0
        cert_missing = 0.0
        sign_risk = 0.0
        w = cfg["risk_based_review"]["score_formula"]
        return round(
            delta_norm * w["delta_weight"]
            + anomaly * w["anomaly_weight"]
            + cert_missing * w["cert_weight"]
            + sign_risk * w["signature_weight"],
            3,
        )

    df["risk_score"] = df.apply(_risk, axis=1)
    df["rbr_trigger"] = (
        df["risk_score"] >= cfg["risk_based_review"]["trigger_threshold"]
    )

    # PRISM artifact
    recap = [
        "P:: invoice-verify · lane-join · Δ% compute",
        "R:: COST-GUARD Δ≤2/5/10 · AutoFail>15 · HallucinationBan",
        f"I:: {{sources:['Domestic_invoice_distance.xlsx','ExecutedLedger(domestic result.xlsx)','mapping_update_20250819.xlsx']}}",
        "S:: plan→normalize→join→score→export",
        "M:: {report.xlsx, proof.artifact(json, sha256)}",
    ]

    # PATCH 4: alias 제안 생성
    alias_df = (
        suggest_aliases(invoice_df, norm_map, cfg)
        if cfg.get("alias_suggestion", {}).get("enabled", True)
        else pd.DataFrame()
    )

    artifact = {
        "artifact_id": f"DomesticAudit-{pd.Timestamp.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "config_version": cfg.get("version"),
        "cost_guard": cfg.get("cost_guard_bands", {}),
        "autofail_pct": cfg.get("autofail_threshold_pct", 15.0),
        "similarity": cfg["similarity"],
        "special_zone_policy": cfg.get("special_zone", {}),
        "stats": {
            "total": int(df.shape[0]),
            "bands": df["cg_band"].value_counts(dropna=False).to_dict(),
            "verdicts": df["verdict"].value_counts(dropna=False).to_dict(),
        },
        "alias_suggestions": alias_df.head(50).to_dict(orient="records"),
    }
    artifact_bytes = json.dumps(artifact, ensure_ascii=False, sort_keys=True).encode(
        "utf-8"
    )
    proof_hash = sha256_of_bytes(artifact_bytes)

    return df, recap, artifact, proof_hash
