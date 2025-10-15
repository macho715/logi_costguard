#!/usr/bin/env python3
"""At Cost 항목 검증 결과 분석"""

import pandas as pd
from pathlib import Path

# 최신 검증 결과 로드
latest_csv = sorted(Path("out").glob("masterdata_validated_*.csv"))[-1]
print(f"\n분석 파일: {latest_csv.name}")
df = pd.read_csv(latest_csv)

print("\n" + "=" * 80)
print("At Cost 항목 검증 결과 분석")
print("=" * 80)

# 전체 Validation Status
print("\n=== Overall Validation Status ===")
print(df["Validation_Status"].value_counts())

# At Cost 항목 필터링
atcost_df = df[df["RATE SOURCE"].str.upper().str.contains("AT COST", na=False)]

print(f"\n=== At Cost Items Analysis ===")
print(f"Total At Cost items: {len(atcost_df)}")

if len(atcost_df) > 0:
    print(f"\nAt Cost Validation Status:")
    print(atcost_df["Validation_Status"].value_counts())

    print(f"\n=== At Cost Items Detail ===")
    cols = [
        "Order Ref. Number",
        "DESCRIPTION",
        "Q'TY",
        "RATE",
        "TOTAL (USD)",
        "PDF_Amount",
        "PDF_Qty",
        "PDF_Unit_Rate",
        "Validation_Status",
        "Validation_Notes",
    ]

    for idx, row in atcost_df.iterrows():
        print(f"\n[{idx+1}] {row['Order Ref. Number']}")
        print(f"  Description: {row['DESCRIPTION']}")
        draft_qty = row["Q'TY"]
        draft_rate = row["RATE"]
        draft_total = row["TOTAL (USD)"]
        print(
            f"  Draft: Q'ty={draft_qty}, Rate=${draft_rate:.2f}, Total=${draft_total:.2f}"
        )

        pdf_amt = row.get("PDF_Amount")
        pdf_qty = row.get("PDF_Qty")
        pdf_rate = row.get("PDF_Unit_Rate")

        if pd.notna(pdf_amt):
            print(
                f"  PDF:   Q'ty={pdf_qty if pd.notna(pdf_qty) else 'N/A'}, Rate=${pdf_rate if pd.notna(pdf_rate) else 'N/A'}, Total=${pdf_amt:.2f}"
            )
            diff = abs(pdf_amt - row["TOTAL (USD)"])
            print(f"  Difference: ${diff:.2f} ({(diff/row['TOTAL (USD)']*100):.1f}%)")
        else:
            print(f"  PDF:   No data extracted")

        print(f"  Status: {row['Validation_Status']}")
        print(f"  Notes: {row['Validation_Notes']}")

print("\n" + "=" * 80)
