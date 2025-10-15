#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

csv_path = Path(__file__).parent / "out" / "masterdata_validated_20251014_212635.csv"
df = pd.read_csv(csv_path)

fail_items = df[df["Validation_Status"] == "FAIL"]

print("=" * 100)
print(f"최종 FAIL {len(fail_items)}건 상세")
print("=" * 100)

for _, row in fail_items.iterrows():
    print(f"\nNo: {int(row['No'])}")
    print(f"  Order Ref: {row['Order Ref. Number']}")
    print(f"  DESCRIPTION: {row['DESCRIPTION']}")
    print(
        f"  RATE: {row['RATE']:.2f} | Ref_Rate: {row.get('Ref_Rate_USD', 'N/A')} | Delta: {row.get('Python_Delta', 0):.1f}%"
    )
    print(f"  Charge_Group: {row['Charge_Group']}")
    print(f"  Notes: {row['Validation_Notes']}")

print("\n" + "=" * 100)
print("전체 통계")
print("=" * 100)

print(f"\nValidation Status 분포:")
status_counts = df["Validation_Status"].value_counts()
for status, count in status_counts.items():
    print(f"  - {status}: {count}건 ({count/len(df)*100:.1f}%)")

print(f"\n개선 효과:")
print(f"  - FAIL: 16건 -> 6건 -> {len(fail_items)}건")
print(f"  - 총 감소: {16-len(fail_items)}건 ({(16-len(fail_items))/16*100:.1f}%)")
print(f"  - PASS: 36건 -> 46건 -> {(df['Validation_Status']=='PASS').sum()}건")
print(
    f"  - 총 증가: {(df['Validation_Status']=='PASS').sum()-36}건 ({((df['Validation_Status']=='PASS').sum()-36)/36*100:.1f}%)"
)
