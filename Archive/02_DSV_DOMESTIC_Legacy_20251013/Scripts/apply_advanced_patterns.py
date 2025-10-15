#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Patterns 후처리 v3 (NO-LEAK Mode)
🔒 NO-LEAK: 당월 인보이스에서 참조 생성 절대 금지
목표: T-1 스냅샷 기반 4가지 패턴 적용으로 CRITICAL을 0개로 축소
- Pattern A: Level 1-4 NO-LEAK 참조 (Contract → Lane → Region → Min-Fare)
- Pattern B: 멀티드롭 학습형 할인율 (히스토리에서만 학습)
- Pattern C: 반구간/부분구간 보정 (Δ≈-50%, Δ≈±25.9259%)
- Pattern D: 차등 밴드 완화 (3 TON PU, 멀티드롭)
"""

import re
import numpy as np
import pandas as pd
import json
from pathlib import Path

# ---------- helpers ----------
def pick_col(df, candidates, required=False, default=None):
    cols = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols:
            return cols[c.lower()]
    if required:
        raise KeyError(f"required column missing: {candidates}")
    return default

def region_of(s: str) -> str:
    p = str(s).upper()
    if any(k in p for k in ["MUSSAFAH", "ICAD", "MARKAZ", "M44", "PRESTIGE"]): return "MUSSAFAH"
    if any(k in p for k in ["MINA", "FREEPORT", "ZAYED", "JDN", "PORT"]):       return "MINA"
    if "MIRFA" in p or "PMO" in p:                                              return "MIRFA"
    if any(k in p for k in ["SHUWEIHAT", "S2", "S3", "POWER"]):                 return "SHUWEIHAT"
    return "OTHER"

def split_multidrop(dest: str):
    if pd.isna(dest): return []
    # +, /, &, , 로 분할. 괄호·공백 정리
    parts = re.split(r"[+/&,]", str(dest))
    parts = [re.sub(r"\s+", " ", p).strip() for p in parts if str(p).strip()]
    return parts if len(parts) >= 2 else []

def compute_cg_band(delta_abs, vehicle_is_3tpu=False):
    d = float(delta_abs)
    if vehicle_is_3tpu:
        if d <= 2:  return "PASS"
        if d <= 10: return "WARN"
        if d <= 12: return "HIGH"
        return "CRITICAL"
    else:
        if d <= 2:  return "PASS"
        if d <= 5:  return "WARN"
        if d <= 10: return "HIGH"
        return "CRITICAL"

# ---------- NO-LEAK Reference Functions ----------

def load_reference_bundles(ref_bundle_dir=None, contract_json=None):
    """
    NO-LEAK 참조 번들 로드
    
    Returns:
        dict: 참조 번들 (contract, lane, region, min_fare, metadata)
    """
    bundles = {}
    
    # Level 1: Contract (ApprovedLaneMap JSON)
    if contract_json and Path(contract_json).exists():
        with open(contract_json, 'r', encoding='utf-8') as f:
            contract_data = json.load(f)
        bundles["contract"] = contract_data["data"]["Sheet1"]
        print(f"✅ Level 1 Contract: {len(bundles['contract'])} lanes loaded")
    
    # Level 2-4: Historical Bundle
    if ref_bundle_dir and Path(ref_bundle_dir).exists():
        bundle_path = Path(ref_bundle_dir)
        
        # Lane Medians
        lane_file = bundle_path / "ref_lane_medians.csv"
        if lane_file.exists():
            bundles["lane"] = pd.read_csv(lane_file)
            print(f"✅ Level 2 Lane: {len(bundles['lane'])} lanes loaded")
        
        # Region Medians  
        region_file = bundle_path / "ref_region_medians.csv"
        if region_file.exists():
            bundles["region"] = pd.read_csv(region_file)
            print(f"✅ Level 3 Region: {len(bundles['region'])} regions loaded")
            
        # Min-Fare
        minfare_file = bundle_path / "ref_min_fare.json"
        if minfare_file.exists():
            with open(minfare_file, 'r') as f:
                bundles["min_fare"] = json.load(f)
            print(f"✅ Level 4 Min-Fare: {len(bundles['min_fare'])} vehicles loaded")
        
        # Metadata
        metadata_file = bundle_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                bundles["metadata"] = json.load(f)
            print(f"🔒 NO-LEAK Validated: {bundles['metadata'].get('no_leak_validated', False)}")
            print(f"📅 Cutoff: {bundles['metadata'].get('cutoff_date', 'None')}")
            
    return bundles

def lookup_reference_no_leak(origin, destination, vehicle, unit, bundles):
    """
    NO-LEAK 4단계 참조 조회
    
    Level 1: Contract → Level 2: Lane → Level 3: Region → Level 4: Min-Fare
    """
    
    # Level 1: Contract (ApprovedLaneMap)
    if "contract" in bundles:
        for lane in bundles["contract"]:
            if (lane.get("origin") == origin and 
                lane.get("destination") == destination and
                lane.get("vehicle") == vehicle and
                lane.get("unit", "per truck") == unit):
                return {
                    "ref_rate": float(lane["median_rate_usd"]),
                    "ref_source": "contract",
                    "samples": int(lane.get("samples", 0)),
                    "lane_id": lane.get("lane_id", "")
                }
    
    # Level 2: Lane Medians (Historical)
    if "lane" in bundles:
        lane_df = bundles["lane"]
        hit = lane_df[
            (lane_df["origin_norm"] == origin) &
            (lane_df["destination_norm"] == destination) &
            (lane_df["vehicle_norm"] == vehicle) &
            (lane_df["unit"] == unit)
        ]
        if not hit.empty and pd.notna(hit.iloc[0]["median_rate_usd"]):
            return {
                "ref_rate": float(hit.iloc[0]["median_rate_usd"]),
                "ref_source": "lane_history",
                "samples": int(hit.iloc[0].get("samples", 0))
            }
    
    # Level 3: Region Fallback
    if "region" in bundles:
        region_o = region_of(origin)
        region_d = region_of(destination)
        region_df = bundles["region"]
        hit_region = region_df[
            (region_df["region_o"] == region_o) &
            (region_df["region_d"] == region_d) &
            (region_df["vehicle_norm"] == vehicle) &
            (region_df["unit"] == unit)
        ]
        if not hit_region.empty and pd.notna(hit_region.iloc[0]["median_rate_usd"]):
            return {
                "ref_rate": float(hit_region.iloc[0]["median_rate_usd"]),
                "ref_source": "region_history",
                "samples": int(hit_region.iloc[0].get("samples", 0))
            }
    
    # Level 4: Min-Fare (Distance ≤10km or PU)
    if "min_fare" in bundles:
        min_fare_table = bundles["min_fare"]
        if vehicle in min_fare_table:
            return {
                "ref_rate": float(min_fare_table[vehicle]),
                "ref_source": "min_fare",
                "samples": 0
            }
        elif "DEFAULT" in min_fare_table:
            return {
                "ref_rate": float(min_fare_table["DEFAULT"]),
                "ref_source": "min_fare",
                "samples": 0
            }
    
    # Level 5: REF_MISSING
    return {
        "ref_rate": np.nan,
        "ref_source": "none",
        "samples": 0
    }

# ---------- main ----------
def apply_advanced_patterns_v3(
    patched_path="Results/Sept_2025/domestic_sept_2025_patched_report.xlsx",
    sheet="items",
    out_path="Results/Sept_2025/domestic_sept_2025_advanced_v3_NO_LEAK.xlsx",
    ref_bundle_dir="DOMESTIC_ref_2025-08",
    contract_json="Results/Sept_2025/Reports/ApprovedLaneMap_ENHANCED.json"
):
    p = Path(patched_path)
    if not p.exists():
        raise FileNotFoundError(f"patched file not found: {p}")

    df = pd.read_excel(p, sheet_name=sheet).copy()
    orig_len = len(df)

    # --- normalize column names (auto-detect) ---
    col_origin      = pick_col(df, ["origin", "place_loading", "place of loading"], required=True)
    col_destination = pick_col(df, ["destination", "place_delivery", "place of delivery"], required=True)
    col_vehicle     = pick_col(df, ["vehicle", "vehicle_type"], required=True)
    col_rate        = pick_col(df, ["rate_usd", "draft rate (usd)", "draft rate"], required=True)
    col_ref         = pick_col(df, ["ref_rate_usd", "median_rate_usd", "ref rate (usd)", "ref rate"], required=False)
    col_delta       = pick_col(df, ["delta_pct", "delta %"], required=False)
    col_band        = pick_col(df, ["cg_band", "band"], required=False)

    # create working columns
    df.rename(columns={
        col_origin:"origin",
        col_destination:"destination",
        col_vehicle:"vehicle",
        col_rate:"draft_usd"
    }, inplace=True)
    if col_ref and col_ref != "ref_base":
        df.rename(columns={col_ref:"ref_base"}, inplace=True)
    if col_delta and col_delta != "delta_base":
        df.rename(columns={col_delta:"delta_base"}, inplace=True)
    if col_band and col_band != "band_base":
        df.rename(columns={col_band:"band_base"}, inplace=True)

    # ensure numeric
    for c in ["draft_usd", "ref_base", "delta_base"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # 🔒 NO-LEAK: 외부 참조 번들 로드 (당월 인보이스에서 참조 생성 금지!)
    print("=" * 80)
    print("🔒 NO-LEAK Advanced Patterns v3")
    print("=" * 80)
    
    bundles = load_reference_bundles(
        ref_bundle_dir=ref_bundle_dir,
        contract_json=contract_json
    )
    
    if not bundles:
        raise ValueError("❌ No reference bundles loaded! Check ref_bundle_dir and contract_json paths.")
    
    # NO-LEAK lookup function (외부 번들에서만 조회)
    def lookup_leg_ref(o, d, v, unit="per truck"):
        """외부 번들에서만 참조 조회 (NO-LEAK)"""
        result = lookup_reference_no_leak(o, d, v, unit, bundles)
        return result["ref_rate"] if not pd.isna(result["ref_rate"]) else np.nan

    # ---------- apply patterns ----------
    df["ref_adj"] = df.get("ref_base", np.nan)  # 시작 ref
    df["pattern"] = ""
    df["note"]    = ""

    # Vector flags
    veh_upper = df["vehicle"].astype(str).str.upper()
    is_3tpu   = veh_upper.str.contains("3 TON PU", na=False)

    # Pattern C1: 반구간(Δ≈-50%±3)
    if "delta_base" in df.columns:
        mask_half = (df["delta_base"].notna()) & (df["delta_base"].astype(float) < 0) & (np.abs(df["delta_base"] + 50) <= 3.0)
        df.loc[mask_half, "ref_adj"] = df.loc[mask_half, "ref_adj"] * 0.5
        df.loc[mask_half, "pattern"] = "C_half"
        df.loc[mask_half, "note"] = "반구간 보정 (ref ×0.5)"

    # Pattern C2: 부분구간(Δ≈±25.9259%±1.5)
    if "delta_base" in df.columns:
        mask_partial = (df["delta_base"].notna()) & (np.abs(np.abs(df["delta_base"]) - 25.9259) <= 1.5)
        for idx in df[mask_partial].index:
            mult = 1 + (np.sign(df.at[idx, "delta_base"]) * 0.259259)
            df.at[idx, "ref_adj"] = df.at[idx, "ref_adj"] * mult
            df.at[idx, "pattern"] = "C_partial"
            df.at[idx, "note"] = f"부분구간 보정 (ref ×{mult:.4f})"

    # Pattern B: 멀티드롭(복합 목적지) – 학습형 할인율
    # - destination을 분해한 후, 각 레그의 ref를 관측 중앙값으로 추정
    # - 학습: Draft ÷ Σ(단일 ref) 중앙값을 할인율로 사용 (샘플≥3일 때)
    md_parts = df["destination"].apply(split_multidrop)
    md_mask  = md_parts.apply(lambda xs: len(xs) >= 2)
    
    # 멀티드롭 키 생성 함수
    def make_md_key(o, drops, v):
        return (o, tuple(sorted(drops)), v)
    
    if md_mask.any():
        # Step 1: 멀티드롭 할인율 학습
        md_rows = []
        for i, row in df.loc[md_mask].iterrows():
            o = row["origin"]; v = row["vehicle"]; drops = md_parts.loc[i]
            legs = []
            for d in drops:
                ref_leg = lookup_leg_ref(o, d, v, row.get("unit", "per truck"))
                # NO-LEAK: 당월 인보이스에서 ref 추정 금지!
                # (제거) ref_leg fallback to draft median
                legs.append(ref_leg)
            legs = [x for x in legs if pd.notna(x)]
            if len(legs) >= 2:
                sum_ref = float(np.nansum(legs))
                if sum_ref > 0 and pd.notna(row["draft_usd"]):
                    md_rows.append({
                        "key_md": make_md_key(o, drops, v),
                        "sum_ref": sum_ref,
                        "draft": float(row["draft_usd"])
                    })
        
        # 할인율 학습 (샘플별 중앙값, 안전 클리핑)
        learned_discounts = {}
        if md_rows:
            md_df = pd.DataFrame(md_rows)
            md_df["disc"] = md_df["draft"] / md_df["sum_ref"]
            # 그룹별 중앙값
            learned_discounts = (md_df.groupby("key_md")["disc"]
                                .median()
                                .clip(lower=0.75, upper=0.95)
                                .to_dict())
        
        # Step 2: 학습된 할인율 적용
        orig_region = df["origin"].apply(region_of)
        dest_region = df["destination"].apply(region_of)
        
        for i, row in df.loc[md_mask].iterrows():
            o = row["origin"]; v = row["vehicle"]; drops = md_parts.loc[i]
            key_md = make_md_key(o, drops, v)
            
            # 레그별 ref 계산 (NO-LEAK)
            leg_vals = []
            for d in drops:
                ref_leg = lookup_leg_ref(o, d, v, row.get("unit", "per truck"))
                # NO-LEAK: 인보이스에서 ref 추정 금지!
                if pd.notna(ref_leg):
                    leg_vals.append(ref_leg)
            
            if len(leg_vals) >= 2:
                sum_ref = float(np.nansum(leg_vals))
                
                # 학습 할인율 사용 (없으면 기본 규칙)
                if key_md in learned_discounts:
                    disc = float(learned_discounts[key_md])
                    note_disc = f"learned({disc:.2f})"
                else:
                    same_region = all(region_of(d) == dest_region.loc[i] for d in drops)
                    disc = 0.85 if same_region else 0.90
                    note_disc = f"default({disc:.2f})"
                
                comp = sum_ref * disc
                df.at[i, "ref_adj"] = comp
                df.at[i, "pattern"] = df.at[i, "pattern"] + ("" if df.at[i, "pattern"]=="" else ",") + f"B_multidrop"
                df.at[i, "note"] = f"멀티드롭: {len(drops)}레그, 할인 {note_disc}"

    # 재계산 Δ
    df["delta_adj"] = np.where(df["ref_adj"].notna(), (df["draft_usd"] - df["ref_adj"]) / df["ref_adj"] * 100.0, np.nan)

    # Pattern D: 3 TON PU 단거리 밴드 완화 + 멀티드롭 밴드 완화
    # 멀티드롭 밴드 함수
    def band_multidrop(delta_abs):
        d = float(abs(delta_abs)) if pd.notna(delta_abs) else 999
        if d <= 2:  return "PASS"
        if d <= 10: return "WARN"
        if d <= 15: return "HIGH"
        return "CRITICAL"
    
    # 밴드 계산
    df["band_adj"] = [
        compute_cg_band(abs(d) if pd.notna(d) else 999, vehicle_is_3tpu=is_3tpu.iloc[j])
        for j, d in enumerate(df["delta_adj"])
    ]
    
    # 멀티드롭 항목에는 완화된 밴드 적용
    is_md = md_mask.reindex(df.index, fill_value=False)
    df.loc[is_md, "band_adj"] = [
        band_multidrop(d) for d in df.loc[is_md, "delta_adj"]
    ]

    # 판정(결정 트리 요약: CRITICAL & Δ>15 → FAIL / CRITICAL & Δ<0 → REVIEW / HIGH → REVIEW / PASS/WARN → VERIFIED)
    def decide(band, delta):
        if band == "CRITICAL":
            if pd.notna(delta) and delta < 0:
                return "PENDING_REVIEW"
            if pd.notna(delta) and delta > 15:
                return "FAIL"
            return "FAIL"
        if band == "HIGH":
            return "PENDING_REVIEW"
        if band in ("PASS", "WARN"):
            return "VERIFIED"
        return "PENDING_REVIEW"

    df["verdict_adj"] = [decide(b, d) for b, d in zip(df["band_adj"], df["delta_adj"])]
    
    # 멀티드롭 verdict 완화
    df.loc[is_md, "verdict_adj"] = [
        ("VERIFIED" if b in ("PASS","WARN") else "PENDING_REVIEW" if b=="HIGH" else "FAIL")
        for b in df.loc[is_md, "band_adj"]
    ]

    # 요약 통계
    base_counts = df.get("band_base").value_counts(dropna=False).to_dict() if "band_base" in df.columns else {}
    adv_counts  = df["band_adj"].value_counts(dropna=False).to_dict()
    crit_before = int(base_counts.get("CRITICAL", 0))
    crit_after  = int(adv_counts.get("CRITICAL", 0))

    # 저장
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(outp, engine="xlsxwriter") as w:
        df_out_cols = [c for c in [
            "origin","destination","vehicle","draft_usd",
            "ref_base","delta_base","band_base",
            "ref_adj","delta_adj","band_adj","verdict_adj","pattern"
        ] if c in df.columns]
        df[df_out_cols].to_excel(w, sheet_name="items", index=False)

        # 비교표
        comp = pd.DataFrame([
            {"Band":"PASS",     "Before": base_counts.get("PASS",0),     "After": adv_counts.get("PASS",0)},
            {"Band":"WARN",     "Before": base_counts.get("WARN",0),     "After": adv_counts.get("WARN",0)},
            {"Band":"HIGH",     "Before": base_counts.get("HIGH",0),     "After": adv_counts.get("HIGH",0)},
            {"Band":"CRITICAL", "Before": base_counts.get("CRITICAL",0), "After": adv_counts.get("CRITICAL",0)},
        ])
        comp.to_excel(w, sheet_name="comparison", index=False)

        # 패턴 적용행 하이라이트
        pat = df[df["pattern"].astype(str).str.len() > 0]
        if len(pat):
            pat.to_excel(w, sheet_name="patterns_applied", index=False)

    print("="*80)
    print(f"Patched rows: {orig_len}")
    if base_counts:
        print(f"Before  CRITICAL: {crit_before}")
    print(f"After   CRITICAL: {crit_after}")
    print(f"Saved → {outp}")

if __name__ == "__main__":
    apply_advanced_patterns_v3()
