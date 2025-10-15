#!/usr/bin/env python3
"""
Distance Interpolation Solution
distance_km=0 문제 해결을 위한 거리 보간 및 재검증
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re


def _tok(s: str):
    """토큰 추출"""
    return set(re.findall(r"[A-Za-z0-9]+", str(s).upper()))


def token_set_sim(a: str, b: str) -> float:
    """Token-set similarity"""
    A, B = _tok(a), _tok(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def get_region(place: str) -> str:
    """장소를 Region으로 그룹화"""
    if pd.isna(place):
        return "OTHER"
    p = str(place).upper()

    if any(
        keyword in p for keyword in ["MUSSAFAH", "ICAD", "M44", "MARKAZ", "PRESTIGE"]
    ):
        return "MUSSAFAH"
    if any(keyword in p for keyword in ["MINA", "FREEPORT", "ZAYED", "JDN", "PORT"]):
        return "MINA"
    if any(keyword in p for keyword in ["MIRFA", "PMO"]):
        return "MIRFA"
    if any(keyword in p for keyword in ["SHUWEIHAT", "SHU", "S2", "S3", "POWER"]):
        return "SHUWEIHAT"
    if "MOSB" in p or "MASAOOD" in p:
        return "MOSB"

    return "OTHER"


def generate_key(origin, destination, vehicle, unit):
    """레인 키 생성"""
    return (
        str(origin).strip().upper()
        + "||"
        + str(destination).strip().upper()
        + "||"
        + str(vehicle).strip().upper()
        + "||"
        + str(unit).strip().lower()
    )


def interpolate_distance(row, approved_lanes_df):
    """
    distance_km=0인 경우 ApprovedLaneMap에서 거리 보간

    우선순위:
    1. Exact key match
    2. Region pool fallback (same region_o/region_d/vehicle/unit)
    3. None (vendor request needed)
    """
    # 이미 거리가 있으면 그대로
    if pd.notna(row.get("distance_km")) and row["distance_km"] > 0:
        return row["distance_km"], "original"

    # 1. Exact key match
    key = generate_key(
        row["origin_norm"], row["destination_norm"], row["vehicle_norm"], row["unit"]
    )

    exact_match = approved_lanes_df[approved_lanes_df["key"] == key]
    if not exact_match.empty and pd.notna(
        exact_match.iloc[0].get("median_distance_km")
    ):
        return exact_match.iloc[0]["median_distance_km"], "exact_match"

    # 2. Region pool fallback
    region_o = get_region(row["origin_norm"])
    region_d = get_region(row["destination_norm"])

    if region_o != "OTHER" and region_d != "OTHER":
        # Add region columns if not exist
        if "region_o" not in approved_lanes_df.columns:
            approved_lanes_df["region_o"] = approved_lanes_df["origin"].apply(
                get_region
            )
        if "region_d" not in approved_lanes_df.columns:
            approved_lanes_df["region_d"] = approved_lanes_df["destination"].apply(
                get_region
            )

        region_pool = approved_lanes_df[
            (approved_lanes_df["region_o"] == region_o)
            & (approved_lanes_df["region_d"] == region_d)
            & (approved_lanes_df["vehicle"] == row["vehicle_norm"])
            & (approved_lanes_df["unit"] == row["unit"])
        ]

        if not region_pool.empty:
            median_dist = region_pool["median_distance_km"].median()
            if pd.notna(median_dist):
                return median_dist, "region_pool"

    # 3. No interpolation possible
    return None, "vendor_needed"


def apply_min_fare(row, min_fare_table):
    """
    거리 ≤10km인 경우 Min-Fare 적용
    """
    if pd.notna(row.get("distance_km_filled")) and row["distance_km_filled"] <= 10:
        vehicle = str(row.get("vehicle_norm", "")).upper()
        return min_fare_table.get(vehicle, min_fare_table.get("DEFAULT", 200.0)), True

    return row.get("ref_rate_usd"), False


def apply_special_surcharge(row, ref_rate):
    """
    HAZMAT/CICPA 특수요율 가산
    """
    if pd.isna(ref_rate):
        return ref_rate, None

    vehicle = str(row.get("vehicle_norm", "")).upper()

    if "HAZMAT" in vehicle:
        return round(ref_rate * 1.15, 2), "HAZMAT_1.15"
    elif "CICPA" in vehicle:
        return round(ref_rate * 1.08, 2), "CICPA_1.08"

    return ref_rate, None


def classify_band(delta_abs):
    """COST-GUARD 밴드 분류"""
    if pd.isna(delta_abs):
        return "REF_MISSING"
    if delta_abs <= 2.0:
        return "PASS"
    elif delta_abs <= 5.0:
        return "WARN"
    elif delta_abs <= 10.0:
        return "HIGH"
    else:
        return "CRITICAL"


def main():
    print("=" * 80)
    print("Distance Interpolation Solution")
    print("=" * 80)

    # File paths
    base_dir = Path(__file__).parent
    results_dir = base_dir / "Results" / "Sept_2025" / "CSV"

    # Latest result (124 lanes)
    latest_csv = results_dir / "domestic_sept_2025_result_20251013_014944.csv"

    # ApprovedLaneMap (124 lanes)
    approved_lanes_file = base_dir / "DOMESTIC_with_distances.xlsx"

    if not latest_csv.exists():
        print(f"[ERROR] Result file not found: {latest_csv}")
        return

    if not approved_lanes_file.exists():
        print(f"[ERROR] ApprovedLaneMap file not found: {approved_lanes_file}")
        return

    print(f"\n[1/6] Loading data...")
    df = pd.read_csv(latest_csv)
    print(f"  Items: {len(df)}")

    approved_lanes_df = pd.read_excel(approved_lanes_file, sheet_name="ApprovedLaneMap")
    print(f"  ApprovedLaneMap lanes: {len(approved_lanes_df)}")

    # Add key column to approved lanes if not exists
    if "key" not in approved_lanes_df.columns:
        approved_lanes_df["key"] = approved_lanes_df.apply(
            lambda r: generate_key(
                r["origin"], r["destination"], r["vehicle"], r["unit"]
            ),
            axis=1,
        )

    # Filter distance_km=0 items
    zero_distance_mask = (df["distance_km"].isna()) | (df["distance_km"] == 0)
    zero_distance_count = zero_distance_mask.sum()
    print(f"\n[2/6] Identifying distance_km=0 items...")
    print(f"  Items with distance_km=0: {zero_distance_count}")

    # Interpolate distances
    print(f"\n[3/6] Interpolating distances...")
    distances_filled = []
    interpolation_methods = []

    for idx, row in df.iterrows():
        dist_filled, method = interpolate_distance(row, approved_lanes_df)
        distances_filled.append(dist_filled)
        interpolation_methods.append(method)

    df["distance_km_filled"] = distances_filled
    df["distance_interpolation_method"] = interpolation_methods

    # Count interpolation success
    interpolated_count = sum(
        1 for m in interpolation_methods if m in ["exact_match", "region_pool"]
    )
    print(f"  Interpolated: {interpolated_count} / {zero_distance_count}")
    print(f"  Vendor needed: {interpolation_methods.count('vendor_needed')}")

    # Min-Fare routing
    print(f"\n[4/6] Applying Min-Fare routing...")
    min_fare_table = {
        "FLATBED": 200.0,
        "LOWBED": 600.0,
        "3 TON PU": 150.0,
        "7 TON PU": 200.0,
        "DEFAULT": 200.0,
    }

    ref_rates_after_minfare = []
    min_fare_applied_flags = []

    for idx, row in df.iterrows():
        ref_after_minfare, is_minfare = apply_min_fare(row, min_fare_table)
        ref_rates_after_minfare.append(ref_after_minfare)
        min_fare_applied_flags.append(is_minfare)

    df["ref_rate_after_minfare"] = ref_rates_after_minfare
    df["min_fare_applied_new"] = min_fare_applied_flags

    minfare_count = sum(min_fare_applied_flags)
    print(f"  Min-Fare applied: {minfare_count} items")

    # Special vehicle surcharge
    print(f"\n[5/6] Applying HAZMAT/CICPA surcharges...")
    ref_rates_final = []
    surcharge_flags = []

    for idx, row in df.iterrows():
        ref_final, surcharge = apply_special_surcharge(
            row, row["ref_rate_after_minfare"]
        )
        ref_rates_final.append(ref_final)
        surcharge_flags.append(surcharge if surcharge else "none")

    df["ref_rate_usd_final"] = ref_rates_final
    df["surcharge_applied"] = surcharge_flags

    hazmat_count = surcharge_flags.count("HAZMAT_1.15")
    cicpa_count = surcharge_flags.count("CICPA_1.08")
    print(f"  HAZMAT surcharge: {hazmat_count} items")
    print(f"  CICPA surcharge: {cicpa_count} items")

    # Recalculate delta and band
    print(f"\n[6/6] Recalculating delta and bands...")
    df["delta_pct_new"] = df.apply(
        lambda r: (
            round(
                100.0
                * (r["rate_usd"] - r["ref_rate_usd_final"])
                / r["ref_rate_usd_final"],
                2,
            )
            if pd.notna(r["ref_rate_usd_final"]) and r["ref_rate_usd_final"] != 0
            else np.nan
        ),
        axis=1,
    )

    df["delta_abs_new"] = df["delta_pct_new"].abs()
    df["cg_band_new"] = df["delta_abs_new"].apply(classify_band)

    # Band comparison
    band_before = df["cg_band"].value_counts()
    band_after = df["cg_band_new"].value_counts()

    print("\n" + "=" * 80)
    print("Band Comparison")
    print("=" * 80)
    print("\nBefore (Original):")
    for band in ["PASS", "WARN", "HIGH", "CRITICAL", "REF_MISSING"]:
        count = band_before.get(band, 0)
        pct = count / len(df) * 100 if len(df) > 0 else 0
        print(f"  {band:12s}: {count:3d} ({pct:5.1f}%)")

    print("\nAfter (Distance Interpolation):")
    for band in ["PASS", "WARN", "HIGH", "CRITICAL", "REF_MISSING"]:
        count = band_after.get(band, 0)
        pct = count / len(df) * 100 if len(df) > 0 else 0
        print(f"  {band:12s}: {count:3d} ({pct:5.1f}%)")

    # Improvement
    critical_before = band_before.get("CRITICAL", 0)
    critical_after = band_after.get("CRITICAL", 0)
    improvement = critical_before - critical_after

    print(f"\nCRITICAL Change: {critical_before} → {critical_after} ({improvement:+d})")

    # Save results
    output_dir = base_dir / "Results" / "Sept_2025"
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

    # CSV
    output_csv = output_dir / "CSV" / f"domestic_sept_2025_interpolated_{timestamp}.csv"
    df.to_csv(output_csv, index=False)
    print(f"\n[OK] CSV saved: {output_csv.name}")

    # Excel
    output_excel = output_dir / f"domestic_sept_2025_interpolated_{timestamp}.xlsx"

    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="All_Items", index=False)

        # Summary sheet
        summary_data = {
            "Metric": [
                "Total Items",
                "PASS",
                "WARN",
                "HIGH",
                "CRITICAL",
                "",
                "Distance Interpolated",
                "Min-Fare Applied",
                "HAZMAT Surcharge",
                "CICPA Surcharge",
            ],
            "Before": [
                len(df),
                band_before.get("PASS", 0),
                band_before.get("WARN", 0),
                band_before.get("HIGH", 0),
                band_before.get("CRITICAL", 0),
                "",
                0,
                0,
                0,
                0,
            ],
            "After": [
                len(df),
                band_after.get("PASS", 0),
                band_after.get("WARN", 0),
                band_after.get("HIGH", 0),
                band_after.get("CRITICAL", 0),
                "",
                interpolated_count,
                minfare_count,
                hazmat_count,
                cicpa_count,
            ],
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        # CRITICAL items (new)
        critical_new = df[df["cg_band_new"] == "CRITICAL"].copy()
        if not critical_new.empty:
            critical_new.to_excel(writer, sheet_name="CRITICAL_After", index=False)

    print(f"[OK] Excel saved: {output_excel.name}")

    # Detailed improvement report
    print("\n" + "=" * 80)
    print("Improvement Details")
    print("=" * 80)

    improved_items = df[
        (df["cg_band"] == "CRITICAL") & (df["cg_band_new"] != "CRITICAL")
    ]

    print(f"\nImproved items (CRITICAL → other): {len(improved_items)}")
    if len(improved_items) > 0:
        for idx, row in improved_items.iterrows():
            print(f"  - {row['shipment_ref']}: {row['cg_band']} → {row['cg_band_new']}")
            print(
                f"    Distance: 0 → {row['distance_km_filled']:.1f}km ({row['distance_interpolation_method']})"
            )
            if row.get("min_fare_applied_new"):
                print(f"    Min-Fare applied: {row['ref_rate_usd_final']} USD")
            if row.get("surcharge_applied") != "none":
                print(f"    Surcharge: {row['surcharge_applied']}")

    # Remaining CRITICAL analysis
    remaining_critical = df[df["cg_band_new"] == "CRITICAL"]
    print(f"\nRemaining CRITICAL: {len(remaining_critical)}")

    if len(remaining_critical) > 0:
        vendor_needed = remaining_critical[
            remaining_critical["distance_interpolation_method"] == "vendor_needed"
        ]
        print(f"  Vendor distance needed: {len(vendor_needed)}")

        if len(vendor_needed) > 0:
            print("\n  Vendor Request Items:")
            for idx, row in vendor_needed.head(5).iterrows():
                print(
                    f"    - {row['shipment_ref']}: {row['origin_norm']} → {row['destination_norm']}"
                )

    print("\n" + "=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print("1. Review interpolated results")
    print("2. Create vendor distance request (Step 2)")
    print("3. Generate final comparison report (Step 4)")
    print("=" * 80)

    return df, output_excel


if __name__ == "__main__":
    main()
