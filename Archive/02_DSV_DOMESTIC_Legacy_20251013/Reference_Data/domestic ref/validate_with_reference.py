#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, json, re, os, hashlib
from pathlib import Path


def _tok(s: str):
    return set(re.findall(r"[A-Za-z0-9]+", str(s).upper()))


def token_set_sim(a, b):
    A, B = _tok(a), _tok(b)
    return 0.0 if not A or not B else len(A & B) / len(A | B)


def trigram_sim(a, b):
    def g(x):
        x = "  " + str(x).upper() + "  "
        return {x[i : i + 3] for i in range(len(x) - 2)}

    A, B = g(a), g(b)
    return 0.0 if not A or not B else len(A & B) / len(A | B)


def od_sim(a, b):
    return 0.6 * token_set_sim(a, b) + 0.4 * trigram_sim(a, b)


def region_of(s):
    p = str(s).upper()
    if any(k in p for k in ["MUSSAFAH", "ICAD", "MARKAZ", "M44", "PRESTIGE"]):
        return "MUSSAFAH"
    if any(k in p for k in ["MINA", "FREEPORT", "ZAYED", "JDN", "PORT"]):
        return "MINA"
    if "MIRFA" in p or "PMO" in p:
        return "MIRFA"
    if any(k in p for k in ["SHUWEIHAT", "S2", "S3", "POWER"]):
        return "SHUWEIHAT"
    return "OTHER"


def band(delta):
    if pd.isna(delta):
        return "UNKNOWN"
    d = abs(delta)
    return "PASS" if d <= 2 else "WARN" if d <= 5 else "HIGH" if d <= 10 else "CRITICAL"


def load_refs(refdir: str):
    base = Path(refdir)
    lane = pd.read_csv(base / "ref_lane_medians.csv")
    region = pd.read_csv(base / "ref_region_medians.csv")
    with open(base / "ref_min_fare.json", "r") as f:
        minfare = json.load(f)
    with open(base / "ref_adjusters.json", "r") as f:
        adjust = json.load(f)
    sp = pd.read_csv(base / "special_pass_whitelist.csv")
    return lane, region, minfare, adjust, set(sp["key"].astype(str))


def canon_place(s: str) -> str:
    if pd.isna(s):
        return ""
    u = str(s).upper()
    if "MUSSAFAH" in u and "YARD" in u:
        return "DSV Mussafah Yard"
    if "MIRFA" in u:
        return "MIRFA SITE"
    if "SHUWEIHAT" in u:
        return "SHUWEIHAT Site"
    if any(k in u for k in ["MINA", "FREEPORT", "ZAYED", "JDN"]):
        return "Mina Zayed Port"
    if any(k in u for k in ["MOSB", "MASAOOD"]):
        return "Al Masaood (MOSB)"
    if "M44" in u:
        return "M44 Warehouse"
    return str(s).strip().title()


def canon_vehicle(v: str) -> str:
    if pd.isna(v):
        return ""
    u = str(v).upper()
    if "FLATBED" in u and "CICPA" in u:
        return "FLATBED (CICPA)"
    if "FLATBED" in u and "HAZ" in u:
        return "FLATBED HAZMAT"
    if "FLATBED" in u:
        return "FLATBED"
    if "LOWBED" in u or u == "LB":
        return "LOWBED (23M)" if "23" in u else "LOWBED"
    if "PICKUP" in u or "PU" in u:
        return "7 TON PU" if "7" in u else "3 TON PU"
    return u


def adjust_rate(ref_rate: float, vehicle_norm: str, adjust: dict) -> float:
    v = str(vehicle_norm).upper()
    if "HAZMAT" in v:
        return round(ref_rate * float(adjust.get("FLATBED_HAZMAT", 1.15)), 2)
    if "CICPA" in v:
        return round(ref_rate * float(adjust.get("FLATBED_CICPA", 1.08)), 2)
    return ref_rate


def find_ref(row, lane, region, minfare):
    key = (
        str(row["origin_norm"]).upper()
        + "||"
        + str(row["destination_norm"]).upper()
        + "||"
        + str(row["vehicle_norm"]).upper()
        + "||"
        + str(row["unit"]).lower()
    )
    hit = lane[lane["key"] == key]
    if not hit.empty:
        c = hit.iloc[0]
        return (
            float(c["median_rate_usd"]),
            float(c.get("median_distance_km", np.nan)),
            "direct",
        )

    pool = lane[
        (lane["vehicle_norm"] == row["vehicle_norm"]) & (lane["unit"] == row["unit"])
    ]
    if pool.empty:
        pool = lane.copy()
    best = None
    score = -1.0
    for _, cand in pool.iterrows():
        s = (
            0.35 * od_sim(row["origin_norm"], cand["origin_norm"])
            + 0.35 * od_sim(row["destination_norm"], cand["destination_norm"])
            + 0.10 * (1.0 if row["vehicle_norm"] == cand["vehicle_norm"] else 0.0)
        )
        if pd.notna(row.get("distance_km")) and pd.notna(
            cand.get("median_distance_km")
        ):
            diff = abs(row["distance_km"] - cand["median_distance_km"])
            s += 0.10 * max(0, 1 - diff / 15.0)
        if (
            pd.notna(row.get("rate_usd"))
            and pd.notna(cand.get("median_rate_usd"))
            and cand["median_rate_usd"] != 0
        ):
            diffp = (
                abs(
                    (row["rate_usd"] - cand["median_rate_usd"])
                    / cand["median_rate_usd"]
                )
                * 100.0
            )
            s += 0.10 * max(0, 1 - diffp / 30.0)
        if s >= 0.60 and s > score:
            best = cand
            score = s
    if best is not None:
        return (
            float(best["median_rate_usd"]),
            float(best.get("median_distance_km", np.nan)),
            "similarity",
        )

    ro, rd = region_of(row["origin_norm"]), region_of(row["destination_norm"])
    poolr = region[
        (region["region_o"] == ro)
        & (region["region_d"] == rd)
        & (region["vehicle_norm"] == row["vehicle_norm"])
        & (region["unit"] == row["unit"])
    ]
    if not poolr.empty:
        c = poolr.sort_values("samples", ascending=False).iloc[0]
        return (
            float(c["median_rate_usd"]),
            float(c.get("median_distance_km", np.nan)),
            "region_pool",
        )

    if pd.notna(row.get("distance_km")) and row["distance_km"] <= 10:
        v = row["vehicle_norm"]
        rate = float(minfare.get(v, minfare.get("DEFAULT", 200.0)))
        return rate, np.nan, "min_fare"
    return np.nan, np.nan, "none"


def verify(invoice_path: str, refdir: str, outdir: str):
    lane, region, minfare, adjust, sp = load_refs(refdir)
    df = (
        pd.read_excel(invoice_path)
        if invoice_path.lower().endswith((".xlsx", ".xls"))
        else pd.read_csv(invoice_path)
    )
    m = {c.lower(): c for c in df.columns}

    def mapcol(dst, *cands):
        for c in cands:
            if c.lower() in m:
                return m[c.lower()]
        return None

    ren = {
        mapcol("origin", "place of loading", "origin"): "origin",
        mapcol("destination", "place of delivery", "destination"): "destination",
        mapcol("vehicle", "vehicle type", "vehicle"): "vehicle",
        mapcol("distance_km", "distance(km)"): "distance_km",
        mapcol("rate_usd", "rate (usd)"): "rate_usd",
        mapcol("unit", "unit"): "unit",
    }
    ren = {k: v for k, v in ren.items() if k}
    df = df.rename(columns=ren)
    for c in ["rate_usd", "distance_km"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "unit" not in df.columns:
        df["unit"] = "per truck"

    # Apply canonical mapping
    origin_col = "origin_norm" if "origin_norm" in df.columns else "origin"
    dest_col = "destination_norm" if "destination_norm" in df.columns else "destination"
    vehicle_col = "vehicle_norm" if "vehicle_norm" in df.columns else "vehicle"

    df["origin_norm"] = (
        df[origin_col].map(canon_place) if origin_col in df.columns else ""
    )
    df["destination_norm"] = (
        df[dest_col].map(canon_place) if dest_col in df.columns else ""
    )
    df["vehicle_norm"] = (
        df[vehicle_col].map(canon_vehicle) if vehicle_col in df.columns else ""
    )

    df["key"] = (
        df["origin_norm"].str.upper()
        + "||"
        + df["destination_norm"].str.upper()
        + "||"
        + df["vehicle_norm"].str.upper()
        + "||"
        + df["unit"].str.lower()
    )
    df["special_pass"] = df["key"].isin(sp).map({True: "SPECIAL_PASS", False: ""})

    refs = []
    dists = []
    methods = []
    for _, r in df.iterrows():
        rr, dd, mm = find_ref(r, lane, region, minfare)
        if not pd.isna(rr):
            rr = adjust_rate(rr, r["vehicle_norm"], adjust)
        refs.append(rr)
        dists.append(dd)
        methods.append(mm)
    df["ref_rate_usd"] = refs
    df["ref_distance_km"] = dists
    df["ref_method"] = methods

    df["delta_pct"] = np.where(
        df["ref_rate_usd"].notna(),
        (df["rate_usd"] - df["ref_rate_usd"]) / df["ref_rate_usd"] * 100.0,
        np.nan,
    )
    df["cg_band"] = df["delta_pct"].apply(band)

    def decide(row):
        if row["special_pass"] == "SPECIAL_PASS":
            return "SPECIAL_PASS"
        if pd.isna(row["cg_band"]) or row["cg_band"] == "UNKNOWN":
            return "PENDING_REVIEW"
        if row["cg_band"] == "CRITICAL" and row["delta_pct"] < 0:
            return "PENDING_REVIEW"
        if row["cg_band"] == "CRITICAL" and row["delta_pct"] > 15:
            return "FAIL"
        if row["cg_band"] == "CRITICAL":
            return "FAIL"
        if row["cg_band"] == "HIGH":
            return "PENDING_REVIEW"
        return "VERIFIED"

    df["verdict"] = df.apply(decide, axis=1)

    Path(outdir).mkdir(parents=True, exist_ok=True)
    items = Path(outdir) / "items.csv"
    df.to_csv(items, index=False)

    # recap + proof
    recap = [
        "P:: invoice-verify · join-ref · cost-guard",
        "R:: Δ≤2/5/10 · AutoFail>15 · FX fixed USD↔AED",
        f"I:: {{total:{len(df)}, pass:{int((df['cg_band']=='PASS').sum())}, warn:{int((df['cg_band']=='WARN').sum())}, high:{int((df['cg_band']=='HIGH').sum())}, critical:{int((df['cg_band']=='CRITICAL').sum())}}}",
        "S:: normalize→join(exact→sim≥0.60)→region→minfare→adjust→export",
        "M:: {items.csv, recap.card, proof.artifact.json}",
    ]
    art = {
        "artifact_id": f"DomesticRefVerify-{pd.Timestamp.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "counts": df["verdict"].value_counts(dropna=False).to_dict(),
        "bands": df["cg_band"].value_counts(dropna=False).to_dict(),
        "ref_methods": df["ref_method"].value_counts(dropna=False).to_dict(),
    }
    j = json.dumps(art, sort_keys=True).encode("utf-8")
    proof = {
        "recap_card": recap,
        "artifact": art,
        "sha256": hashlib.sha256(j).hexdigest(),
    }
    with open(Path(outdir) / "proof.artifact.json", "w", encoding="utf-8") as f:
        json.dump(proof, f, ensure_ascii=False, indent=2)

    print("\n".join(recap))
    print("Saved:", items.as_posix(), str(Path(outdir) / "proof.artifact.json"))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--invoice", required=True)
    ap.add_argument("--refdir", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    verify(args.invoice, args.refdir, args.outdir)
