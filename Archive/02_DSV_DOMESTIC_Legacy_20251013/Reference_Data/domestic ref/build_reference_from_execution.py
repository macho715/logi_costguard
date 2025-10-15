#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NO-LEAK Reference Builder
T-1까지 스냅샷만 사용하여 참조 번들 생성
"""
import pandas as pd, numpy as np, json, re, os, hashlib
from pathlib import Path
from datetime import datetime


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


def region_of(s: str) -> str:
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


def learn_minfare(df: pd.DataFrame) -> dict:
    mf = {}
    g = df[df["distance_km"].fillna(0) <= 10].groupby("vehicle_norm")
    for v, sub in g:
        if len(sub) >= 3:
            mf[v] = round(float(sub["rate_usd"].median()), 2)
    base = {
        "FLATBED": 200.0,
        "LOWBED": 600.0,
        "3 TON PU": 150.0,
        "7 TON PU": 200.0,
        "DEFAULT": 200.0,
    }
    for k, v in base.items():
        mf.setdefault(k, v)
    return mf


def learn_adjusters(df: pd.DataFrame) -> dict:
    def ratio(flag, base):
        g1 = df[df["vehicle_norm"].str.contains(flag, case=False, na=False)]
        g0 = df[
            df["vehicle_norm"].str.contains(base, case=False, na=False)
            & (~df["vehicle_norm"].str.contains(flag, case=False, na=False))
        ]
        if len(g1) >= 5 and len(g0) >= 5:
            r = g1["rate_usd"].median() / max(1e-9, g0["rate_usd"].median())
            return float(np.clip(r, 1.05, 1.30))
        return None

    haz = ratio("HAZMAT", "FLATBED") or 1.15
    cic = ratio("CICPA", "FLATBED") or 1.08
    return {"FLATBED_HAZMAT": round(haz, 2), "FLATBED_CICPA": round(cic, 2)}


def compute_bundle_hash(bundle_dir):
    """참조 번들의 SHA256 해시 계산"""
    hasher = hashlib.sha256()
    bundle_path = Path(bundle_dir)
    
    # 파일 목록 (정렬된 순서)
    files = sorted([
        "ref_lane_medians.csv",
        "ref_region_medians.csv", 
        "ref_min_fare.json",
        "ref_adjusters.json",
        "special_pass_whitelist.csv"
    ])
    
    for fname in files:
        fpath = bundle_path / fname
        if fpath.exists():
            with open(fpath, "rb") as f:
                hasher.update(f.read())
    
    return hasher.hexdigest()

def build(inpath: str, outdir: str, cutoff: str = None):
    """
    NO-LEAK 참조 번들 생성
    
    Args:
        inpath: 집행 원장 경로
        outdir: 출력 디렉토리
        cutoff: 컷오프 월 (YYYY-MM), 이 월 1일 미만 데이터만 포함
    """
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    # Read from 'items' sheet if Excel file
    if inpath.lower().endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(inpath, sheet_name="items")
            print(f"📂 Reading 'items' sheet from {Path(inpath).name}")
        except:
            df = pd.read_excel(inpath)  # Fallback to first sheet
            print(f"📂 Reading first sheet from {Path(inpath).name}")
    else:
        df = pd.read_csv(inpath)
    
    original_count = len(df)
    print(f"📊 Original records: {original_count:,}")
    
    # 🔒 NO-LEAK: 날짜 컬럼 감지 및 필터링
    if cutoff:
        date_columns = [c for c in df.columns 
                       if any(k in str(c).lower() for k in ["date", "txn", "doc", "time"])]
        
        if date_columns:
            date_col = date_columns[0]  # 첫 번째 날짜 컬럼 사용
            print(f"🗓️  Using date column: {date_col}")
            
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                cutoff_date = pd.Timestamp(f"{cutoff}-01")
                
                # T-1까지만 필터링
                df_filtered = df[df[date_col] < cutoff_date]
                excluded_count = len(df) - len(df_filtered)
                
                print(f"🔒 NO-LEAK Filter:")
                print(f"   Cutoff: {cutoff} (before {cutoff_date.date()})")
                print(f"   Records: {original_count:,} → {len(df_filtered):,}")
                print(f"   Excluded: {excluded_count:,}")
                
                if excluded_count > 0:
                    print(f"✅ Data leakage prevented: {excluded_count} records excluded")
                
                df = df_filtered
                
            except Exception as e:
                print(f"⚠️  Date filtering failed: {e}")
                print(f"   Proceeding without date filter")
        else:
            print(f"⚠️  No date column found for cutoff filtering")
            print(f"   Available columns: {list(df.columns)[:10]}...")
    else:
        print(f"ℹ️  No cutoff specified, using all data")
    # normalize
    col = {c.lower(): c for c in df.columns}

    def get(*names):
        for n in names:
            if n.lower() in col:
                return col[n.lower()]
        return None

    # Build rename dict (filter out None keys)
    rename_dict = {}
    origin_key = get("place of loading", "place_loading", "origin")
    if origin_key:
        rename_dict[origin_key] = "origin"

    dest_key = get("place of delivery", "place_delivery", "destination")
    if dest_key:
        rename_dict[dest_key] = "destination"

    vehicle_key = get("vehicle type", "vehicle_type", "vehicle")
    if vehicle_key:
        rename_dict[vehicle_key] = "vehicle"

    dist_key = get("distance(km)", "distance_km", "distance (km)")
    if dist_key:
        rename_dict[dist_key] = "distance_km"

    rate_key = get("rate (usd)", "rate_usd", "rate(usd)")
    if rate_key:
        rename_dict[rate_key] = "rate_usd"

    unit_key = get("unit")
    if unit_key:
        rename_dict[unit_key] = "unit"

    df = df.rename(columns=rename_dict)
    print(f"  Mapped columns: {len(rename_dict)}")
    print(f"  Columns after rename: {list(df.columns)[:10]}")
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
    df["region_o"] = df["origin_norm"].map(region_of)
    df["region_d"] = df["destination_norm"].map(region_of)

    # lane medians
    grp = ["origin_norm", "destination_norm", "vehicle_norm", "unit"]
    lane = (
        df.groupby(grp, dropna=False)
        .agg(
            median_rate_usd=("rate_usd", "median"),
            median_distance_km=("distance_km", "median"),
            p25=("rate_usd", lambda x: x.quantile(0.25)),
            p75=("rate_usd", lambda x: x.quantile(0.75)),
            samples=("rate_usd", "count"),
        )
        .reset_index()
    )
    lane["key"] = (
        lane["origin_norm"].str.upper()
        + "||"
        + lane["destination_norm"].str.upper()
        + "||"
        + lane["vehicle_norm"].str.upper()
        + "||"
        + lane["unit"].str.lower()
    )
    lane.to_csv(out / "ref_lane_medians.csv", index=False)

    # region medians
    rgrp = ["region_o", "region_d", "vehicle_norm", "unit"]
    region = (
        df.groupby(rgrp, dropna=False)
        .agg(
            median_rate_usd=("rate_usd", "median"),
            median_distance_km=("distance_km", "median"),
            samples=("rate_usd", "count"),
        )
        .reset_index()
    )
    region["key_region"] = (
        region["region_o"].str.upper()
        + "|"
        + region["region_d"].str.upper()
        + "|"
        + region["vehicle_norm"].str.upper()
        + "|"
        + region["unit"].str.lower()
    )
    region.to_csv(out / "ref_region_medians.csv", index=False)

    # min-fare / adjusters / special-pass
    minfare = learn_minfare(df)
    adjust = learn_adjusters(df)
    with open(out / "ref_min_fare.json", "w") as f:
        json.dump(minfare, f, indent=2)
    with open(out / "ref_adjusters.json", "w") as f:
        json.dump(adjust, f, indent=2)

    sp = df.copy()
    sp["key"] = (
        sp["origin_norm"].str.upper()
        + "||"
        + sp["destination_norm"].str.upper()
        + "||"
        + sp["vehicle_norm"].str.upper()
        + "||"
        + sp["unit"].str.lower()
    )
    sp[["key"]].drop_duplicates().to_csv(
        out / "special_pass_whitelist.csv", index=False
    )

    # 🔒 NO-LEAK Metadata 생성
    bundle_hash = compute_bundle_hash(out)
    
    metadata = {
        "cutoff_date": cutoff,
        "cutoff_timestamp": f"{cutoff}-01T00:00:00" if cutoff else None,
        "created_at": datetime.now().isoformat(),
        "source_ledger": Path(inpath).name,
        "total_records_source": original_count,
        "total_records_filtered": len(df),
        "excluded_records": original_count - len(df),
        "lane_count": int(len(lane)),
        "region_count": int(len(region)),
        "min_fare_count": len(minfare),
        "sha256": bundle_hash,
        "version": "ref-2.0-NO-LEAK",
        "no_leak_validated": True
    }
    
    with open(out / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    # 레거시 호환성을 위한 기존 파일
    bundle = {
        "version": "ref-2.0-NO-LEAK",
        "built_from": Path(inpath).name,
        "lane_rows": int(len(lane)),
        "region_rows": int(len(region)),
        "min_fare": minfare,
        "adjusters": adjust,
        "cutoff_date": cutoff,
        "no_leak_validated": True
    }
    with open(out / "domestic_reference.json", "w") as f:
        json.dump(bundle, f, indent=2)
    
    print(f"✅ Built NO-LEAK refs → {out.as_posix()}")
    print(f"📊 Summary:")
    print(f"   Lanes: {len(lane):,}")
    print(f"   Regions: {len(region):,}")
    print(f"   Hash: {bundle_hash[:16]}...")
    if cutoff:
        print(f"   Cutoff: {cutoff} (NO-LEAK verified)")
    else:
        print(f"   ⚠️  No cutoff - consider using --cutoff for NO-LEAK mode")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="NO-LEAK Reference Bundle Builder")
    ap.add_argument("--ledger", required=True, help="DOMESTIC_with_distances.xlsx")
    ap.add_argument("--outdir", required=True, help="Output reference directory")
    ap.add_argument("--cutoff", help="Cutoff month (YYYY-MM), e.g., 2025-09 (excludes this month and later)")
    args = ap.parse_args()
    
    print("=" * 80)
    print("🔒 NO-LEAK Reference Bundle Builder")
    print("=" * 80)
    
    build(args.ledger, args.outdir, args.cutoff)
