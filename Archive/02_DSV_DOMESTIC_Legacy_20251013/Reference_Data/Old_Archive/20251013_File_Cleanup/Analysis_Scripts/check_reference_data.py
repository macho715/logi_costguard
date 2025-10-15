#!/usr/bin/env python3
"""참조 데이터 확인"""

import pandas as pd
from pathlib import Path

ref_file = Path(__file__).parent / "DOMESTIC_with_distances.xlsx"

print("=" * 80)
print("DOMESTIC Reference Data Check")
print("=" * 80)

if not ref_file.exists():
    print(f"\n[ERROR] File not found: {ref_file}")
    print("Using embedded fallback references (8 lanes)")
else:
    print(f"\n[OK] File found: {ref_file.name}")
    print(
        f"Size: {ref_file.stat().st_size:,} bytes ({ref_file.stat().st_size/1024:.1f} KB)"
    )

    try:
        xls = pd.ExcelFile(ref_file)
        print(f"\nSheets: {xls.sheet_names}")

        if "ApprovedLaneMap" in xls.sheet_names:
            df = pd.read_excel(ref_file, sheet_name="ApprovedLaneMap")
            print(f"\n[ApprovedLaneMap]")
            print(f"  Total Lanes: {len(df)}")
            print(f"  Columns: {list(df.columns)}")

            # 샘플 데이터
            print(f"\n  Sample Lanes (First 5):")
            for idx, row in df.head(5).iterrows():
                print(
                    f"    {idx+1}. {row.get('origin', 'N/A')} → {row.get('destination', 'N/A')}"
                )
                print(
                    f"       Vehicle: {row.get('vehicle', 'N/A')}, Rate: ${row.get('median_rate_usd', 0):.2f}"
                )
        else:
            print("\n[WARN] ApprovedLaneMap sheet not found")

    except Exception as e:
        print(f"\n[ERROR] Failed to read file: {e}")

print("\n" + "=" * 80)
