#!/usr/bin/env python3
"""
FAIL 항목 상세 분석 스크립트
"""
import pandas as pd
from pathlib import Path

# 최신 검증 결과 파일 로드
csv_file = Path(__file__).parent / "out" / "masterdata_validated_20251015_001208.csv"
df = pd.read_csv(csv_file)

# FAIL 항목 추출
fail_df = df[df["Validation_Status"] == "FAIL"].copy()

print("=" * 80)
print(f"FAIL 항목 분석 ({len(fail_df)}건)")
print("=" * 80)
print()

# 상세 정보 출력
for idx, row in fail_df.iterrows():
    print(f"[FAIL #{idx+1}]")
    print(f"  Order Ref: {row['Order Ref. Number']}")
    print(f"  Description: {row['DESCRIPTION']}")
    print(f"  Rate: {row['RATE']} USD")
    print(f"  Ref Rate: {row.get('Ref_Rate_USD', 'N/A')} USD")
    print(f"  Charge Group: {row.get('Charge_Group', 'N/A')}")
    print(f"  Notes: {row['Validation_Notes']}")
    print()

# 실패 원인 분류
print("=" * 80)
print("실패 원인 분류")
print("=" * 80)

# Notes에서 패턴 추출
fail_reasons = fail_df["Validation_Notes"].value_counts()
for reason, count in fail_reasons.items():
    print(f"  {count}건: {reason[:80]}...")
    print()
