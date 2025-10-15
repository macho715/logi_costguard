#!/usr/bin/env python3
"""
고정 요율 통합 후 개선 지표 분석
"""

import pandas as pd
from pathlib import Path

# 최신 검증 결과 로드
csv_path = Path(__file__).parent / "out" / "masterdata_validated_20251014_205430.csv"
df = pd.read_csv(csv_path)

print("=" * 80)
print("고정 요율 통합 개선 지표 분석")
print("=" * 80)

# 1. DO FEE 분석
print("\n[1] MASTER DO FEE 분석 (25건 예상)")
print("-" * 80)
do_fee = df[df["DESCRIPTION"].str.contains("MASTER DO FEE", na=False, case=False)]
print(f"Total DO FEE 항목: {len(do_fee)}")
print(
    f"Ref Rate 찾음: {do_fee['Ref_Rate_USD'].notna().sum()} ({do_fee['Ref_Rate_USD'].notna().sum()/len(do_fee)*100:.1f}%)"
)
print(f"  - Ref Rate 80 (AIR): {(do_fee['Ref_Rate_USD'] == 80.0).sum()}건")
print(f"  - Ref Rate 150 (CONTAINER): {(do_fee['Ref_Rate_USD'] == 150.0).sum()}건")
print(f"Ref Rate 못 찾음: {do_fee['Ref_Rate_USD'].isna().sum()}건")

# Transport mode 분석
print("\n[DO FEE Order Ref 패턴]")
for idx, row in do_fee.head(10).iterrows():
    order_ref = row["Order Ref. Number"]
    ref_rate = row["Ref_Rate_USD"]
    mode = "AIR" if "HE" in str(order_ref) else "CONTAINER"
    status = (
        "OK"
        if (mode == "AIR" and ref_rate == 80)
        or (mode == "CONTAINER" and ref_rate == 150)
        else "MISMATCH"
    )
    print(f"  {order_ref}: {mode} -> Ref Rate {ref_rate} [{status}]")

# 2. CUSTOMS CLEARANCE 분석
print("\n[2] CUSTOMS CLEARANCE FEE 분석 (24건 예상)")
print("-" * 80)
customs = df[
    df["DESCRIPTION"].str.contains(
        "CUSTOMS CLEARANCE|CUSTOM CLEARANCE", na=False, case=False, regex=True
    )
]
print(f"Total CUSTOMS 항목: {len(customs)}")
print(
    f"Ref Rate 찾음: {customs['Ref_Rate_USD'].notna().sum()} ({customs['Ref_Rate_USD'].notna().sum()/len(customs)*100:.1f}%)"
)
print(f"  - Ref Rate 150: {(customs['Ref_Rate_USD'] == 150.0).sum()}건")
print(f"  - Ref Rate 350 (구버전): {(customs['Ref_Rate_USD'] == 350.0).sum()}건")
print(f"Ref Rate 못 찾음: {customs['Ref_Rate_USD'].isna().sum()}건")

# 3. Contract 전체 검증
print("\n[3] Contract 검증 전체 현황")
print("-" * 80)
contract = df[df["Charge_Group"] == "Contract"]
print(f"Total Contract 항목: {len(contract)}")
print(
    f"Ref Rate 있음: {contract['Ref_Rate_USD'].notna().sum()} ({contract['Ref_Rate_USD'].notna().sum()/len(contract)*100:.1f}%)"
)
print(f"Ref Rate 없음: {contract['Ref_Rate_USD'].isna().sum()} (이전: 17/21 = 81.0%)")

# 개선율 계산
prev_no_rate = 17
current_no_rate = contract["Ref_Rate_USD"].isna().sum()
improvement = (
    ((prev_no_rate - current_no_rate) / prev_no_rate * 100) if prev_no_rate > 0 else 0
)
print(f"\n[개선율]")
print(f"  이전 'No ref rate': 17/21 (81.0%)")
print(
    f"  현재 'No ref rate': {current_no_rate}/64 ({current_no_rate/len(contract)*100:.1f}%)"
)
print(f"  개선: {prev_no_rate - current_no_rate}건 감소 ({improvement:.1f}% 개선)")

# 4. Ref Rate 소스 분석
print("\n[4] Ref Rate 소스 분석")
print("-" * 80)
notes_with_config = df[
    df["Validation_Notes"].str.contains("Config", na=False, case=False)
]
notes_with_pdf = df[df["Validation_Notes"].str.contains("PDF", na=False, case=False)]
print(f"Config 소스: {len(notes_with_config)}건")
print(f"PDF 소스: {len(notes_with_pdf)}건")

# 5. Validation Status 분포
print("\n[5] Validation Status 분포")
print("-" * 80)
status_counts = df["Validation_Status"].value_counts()
for status, count in status_counts.items():
    print(f"  {status}: {count}건 ({count/len(df)*100:.1f}%)")

# 6. COST-GUARD 분포
print("\n[6] COST-GUARD 분포 (Contract)")
print("-" * 80)
contract_with_band = contract[contract["CG_Band"].notna()]
cg_counts = contract_with_band["CG_Band"].value_counts()
for band, count in cg_counts.items():
    print(f"  {band}: {count}건 ({count/len(contract_with_band)*100:.1f}%)")

# 7. 샘플 항목 상세
print("\n[7] DO FEE 샘플 (처음 5건)")
print("-" * 80)
do_fee_sample = do_fee[
    [
        "Order Ref. Number",
        "DESCRIPTION",
        "RATE",
        "Ref_Rate_USD",
        "Python_Delta",
        "Validation_Notes",
    ]
].head(5)
print(do_fee_sample.to_string(index=False))

print("\n[8] CUSTOMS 샘플 (처음 5건)")
print("-" * 80)
customs_sample = customs[
    [
        "Order Ref. Number",
        "DESCRIPTION",
        "RATE",
        "Ref_Rate_USD",
        "Python_Delta",
        "Validation_Notes",
    ]
].head(5)
print(customs_sample.to_string(index=False))

print("\n" + "=" * 80)
print("[분석 완료]")
print("=" * 80)
