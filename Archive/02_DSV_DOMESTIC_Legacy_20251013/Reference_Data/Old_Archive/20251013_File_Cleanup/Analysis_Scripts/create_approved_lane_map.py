#!/usr/bin/env python3
"""
ApprovedLaneMap 시트 생성
DOMESTIC_with_distances.xlsx의 items 시트(519건)에서 레인별 median 계산
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from openpyxl import load_workbook

# Normalization functions (domestic_validator_patched.py와 동일)
NORMALIZE_MAP = {
    r"\bDSV\s*MUSSAFAH\s*YARD\b": "DSV Mussafah Yard",
    r"\bDSV\s*M44\b|M44\s*WAREHOUSE": "M44 Warehouse",
    r"\bDSV\s*AL\s*MARKAZ\s*WH\b|AL\s*MARKAZ\s*WAREHOUSE": "Al Markaz Warehouse",
    r"\bPRESTIGE\b.*ICAD.*|PRESTIGE\s*MUSSAFAH": "DSV Mussafah Yard",
    r"\bMOSB\b|AL\s*MASA?OOD\b|AL\s*MASAOOD\b": "Al Masaood (MOSB)",
    r"\bMIRFA\b|MIRFA\s*SITE|MIRFA\s*PMO\s*SAMSUNG": "MIRFA SITE",
    r"\bSHUWEIHAT\b|SHUWEIHAT\s*(SITE|POWER\s*STATION)?": "SHUWEIHAT Site",
    r"\bMINA\s*FREE\s*PORT\b|\bMINA\s*FREEPORT\b|\bMINA\s*ZAYED\b|JDN\s*MINA\s*ZAYED": "Mina Zayed Port",
    r"\bJEBEL\s*ALI\b|MAMMOET\s*JEBEL\s*ALI": "Jebel Ali Port",
    r"\bSAMSUNG\s*MOSB\b": "SAMSUNG MOSB YARD",
    r"\bHAULER\s*DUBAI\b": "HAULER DUBAI",
    r"\bSAS\s*POWER\b": "SAS POWER INDUSTRIES FZE",
}


def normalize_place(x):
    if pd.isna(x):
        return ""
    s = str(x).strip().upper()
    s = re.sub(r"\s+", " ", s)
    for patt, canon in NORMALIZE_MAP.items():
        if re.search(patt, s):
            return canon
    if "MUSSAFAH" in s and "YARD" in s:
        return "DSV Mussafah Yard"
    if "MIRFA" in s:
        return "MIRFA SITE"
    if "SHUWEIHAT" in s:
        return "SHUWEIHAT Site"
    if "MOSB" in s:
        return "Al Masaood (MOSB)"
    if "MINA" in s:
        return "Mina Zayed Port"
    return s.title()


def normalize_vehicle(v):
    if pd.isna(v):
        return np.nan
    s = str(v).strip().upper()
    s = s.replace("FLATBED (HAZMAT)", "FLATBED HAZMAT").replace(
        "FLATBED- CICPA", "FLATBED (CICPA)"
    )
    if s == "FB":
        return "FLATBED"
    if s == "LB":
        return "LOWBED"
    if "FLATBED" in s and "CICPA" in s:
        return "FLATBED (CICPA)"
    if "FLATBED" in s and "HAZ" in s:
        return "FLATBED HAZMAT"
    if "FLATBED" in s:
        return "FLATBED"
    if "LOWBED" in s or s == "LB":
        if "23" in s:
            return "LOWBED (23M)"
        return "LOWBED"
    if "PICKUP" in s or "PU" in s:
        return "7 TON PU" if "7" in s else "3 TON PU"
    return s


def main():
    print("=" * 80)
    print("ApprovedLaneMap Generator")
    print("=" * 80)

    # 파일 경로
    base_dir = Path(__file__).parent
    input_file = base_dir / "DOMESTIC_with_distances.xlsx"

    if not input_file.exists():
        print(f"\n[ERROR] File not found: {input_file}")
        return

    # items 시트 로드
    print(f"\nLoading items sheet from {input_file.name}...")
    df = pd.read_excel(input_file, sheet_name="items")
    print(f"  OK Loaded {len(df)} items")

    # 정규화
    print("\nNormalizing data...")
    df["origin_norm"] = df["place_loading"].apply(normalize_place)
    df["destination_norm"] = df["place_delivery"].apply(normalize_place)
    df["vehicle_norm"] = df["vehicle_type"].apply(normalize_vehicle)
    df["unit"] = "per truck"

    # 수치 변환
    df["rate_usd"] = pd.to_numeric(df["rate_usd"], errors="coerce")
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")

    # 유효 데이터만 필터
    df_valid = df[df["rate_usd"].notna() & df["distance_km"].notna()].copy()
    print(f"  Valid items: {len(df_valid)}/{len(df)}")

    # 레인별 집계
    print("\nAggregating by lane...")
    lane_map = (
        df_valid.groupby(
            ["origin_norm", "destination_norm", "vehicle_norm", "unit"], dropna=False
        )
        .agg(
            {
                "rate_usd": ["median", "mean", "std", "count"],
                "distance_km": ["median", "mean"],
            }
        )
        .reset_index()
    )

    # 컬럼명 평탄화
    lane_map.columns = [
        "origin",
        "destination",
        "vehicle",
        "unit",
        "median_rate_usd",
        "mean_rate_usd",
        "std_rate_usd",
        "samples",
        "median_distance_km",
        "mean_distance_km",
    ]

    # Lane ID 생성
    lane_map["lane_id"] = [f"L{i+1:03d}" for i in range(len(lane_map))]

    # 정렬 (samples 많은 순)
    lane_map = lane_map.sort_values("samples", ascending=False).reset_index(drop=True)

    print(f"  OK Generated {len(lane_map)} unique lanes")

    # 통계 출력
    print("\n" + "=" * 80)
    print("Lane Statistics")
    print("=" * 80)
    print(f"Total Lanes: {len(lane_map)}")
    print(f"Total Samples: {lane_map['samples'].sum()}")
    print(f"Average Samples per Lane: {lane_map['samples'].mean():.1f}")
    print(f"\nSamples Distribution:")
    print(f"  1 sample: {len(lane_map[lane_map['samples'] == 1])}")
    print(f"  2-5 samples: {len(lane_map[lane_map['samples'].between(2, 5)])}")
    print(f"  6+ samples: {len(lane_map[lane_map['samples'] >= 6])}")

    # Vehicle 분포
    print(f"\nVehicle Distribution:")
    print(lane_map["vehicle"].value_counts().head(10))

    # 샘플 레인 출력
    print("\n" + "=" * 80)
    print("Sample Lanes (Top 10 by samples)")
    print("=" * 80)
    for idx, row in lane_map.head(10).iterrows():
        print(f"\n{idx+1}. {row['lane_id']}: {row['origin']} → {row['destination']}")
        print(f"   Vehicle: {row['vehicle']}, Unit: {row['unit']}")
        print(f"   Rate: ${row['median_rate_usd']:.2f} (samples: {row['samples']})")
        print(f"   Distance: {row['median_distance_km']:.1f} km")

    # Excel 파일에 시트 추가
    print("\n" + "=" * 80)
    print("Adding ApprovedLaneMap sheet...")
    print("=" * 80)

    try:
        # openpyxl로 기존 파일 로드
        with pd.ExcelWriter(
            input_file, engine="openpyxl", mode="a", if_sheet_exists="replace"
        ) as writer:
            lane_map.to_excel(writer, sheet_name="ApprovedLaneMap", index=False)

        print(f"\n[OK] ApprovedLaneMap sheet added to {input_file.name}")
        print(f"  Lanes: {len(lane_map)}")
        print(f"  Columns: {list(lane_map.columns)}")

    except Exception as e:
        print(f"\n[ERROR] Failed to add sheet: {e}")
        return

    # 검증
    print("\n" + "=" * 80)
    print("Verification")
    print("=" * 80)

    xls = pd.ExcelFile(input_file)
    print(f"Sheets in file: {xls.sheet_names}")

    if "ApprovedLaneMap" in xls.sheet_names:
        verify_df = pd.read_excel(input_file, sheet_name="ApprovedLaneMap")
        print(f"\n[OK] ApprovedLaneMap verified: {len(verify_df)} lanes")
        print("\n[SUCCESS] ApprovedLaneMap creation complete!")
    else:
        print("\n[ERROR] ApprovedLaneMap not found in file")

    print("=" * 80)


if __name__ == "__main__":
    main()
