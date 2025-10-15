#!/usr/bin/env python3
"""
INLAND TRUCKING/TRANSPORTATION 검증 현황 분석
"""

import pandas as pd
from pathlib import Path

csv_path = Path(__file__).parent / "out" / "masterdata_validated_20251014_212635.csv"
df = pd.read_csv(csv_path)

trans = df[
    df["DESCRIPTION"].str.contains("TRANSPORTATION|TRUCKING", na=False, case=False)
]

print("=" * 100)
print("TRANSPORTATION/TRUCKING 항목 검증 현황")
print("=" * 100)

print(f"\nTotal TRANSPORTATION/TRUCKING: {len(trans)}건")

status_counts = trans["Validation_Status"].value_counts()
print("\nValidation Status 분포:")
for status, count in status_counts.items():
    print(f"  {status}: {count}건 ({count/len(trans)*100:.1f}%)")

print("\nRef Rate 현황:")
has_ref = trans["Ref_Rate_USD"].notna().sum()
no_ref = trans["Ref_Rate_USD"].isna().sum()
print(f"  Ref Rate 있음: {has_ref}건 ({has_ref/len(trans)*100:.1f}%)")
print(f"  Ref Rate 없음: {no_ref}건 ({no_ref/len(trans)*100:.1f}%)")

print("\n" + "=" * 100)
print("샘플 항목 (처음 10건)")
print("=" * 100)
sample_cols = [
    "No",
    "Order Ref. Number",
    "DESCRIPTION",
    "RATE",
    "Ref_Rate_USD",
    "Validation_Status",
]
print(trans[sample_cols].head(10).to_string(index=False))

print("\n" + "=" * 100)
print("경로 패턴 분석")
print("=" * 100)

print("\nDESCRIPTION 샘플 (FROM/TO 포함):")
trans_with_route = trans[
    trans["DESCRIPTION"].str.contains("FROM|TO", na=False, case=False)
]
for idx, row in trans_with_route.head(5).iterrows():
    print(f"\n  No {int(row['No'])}: {row['DESCRIPTION'][:80]}")
    print(f"    RATE: {row['RATE']} | Ref_Rate: {row.get('Ref_Rate_USD', 'N/A')}")
    print(f"    Notes: {row['Validation_Notes'][:100]}")

print("\n" + "=" * 100)
print("문제 분석")
print("=" * 100)

print("\n[발견]:")
print(
    f"  - TRANSPORTATION 항목 중 {no_ref}건({no_ref/len(trans)*100:.1f}%)이 Ref Rate 없음"
)
print("  - Lane Map에 등록되지 않은 경로로 추정")
print("  - 경로 파싱 실패 가능성")

print("\n[해결 필요]:")
print("  1. Lane Map 확장 (config_shpt_lanes.json)")
print("  2. 경로 파싱 로직 개선 (_parse_transportation_route)")
print("  3. Inland Trucking JSON 파일 통합")
