#!/usr/bin/env python3
"""
남은 FAIL 6건 상세 분석 및 요율 파일 매칭
"""

import pandas as pd
import json
from pathlib import Path

# 최신 검증 결과 로드
csv_path = Path(__file__).parent / "out" / "masterdata_validated_20251014_211702.csv"
df = pd.read_csv(csv_path)

# 요율 파일 로드
rate_dir = Path(__file__).parent.parent.parent / "Rate"
config_rates_path = rate_dir / "config_contract_rates.json"
air_rates_path = rate_dir / "air_cargo_rates (1).json"
container_rates_path = rate_dir / "container_cargo_rates (1).json"

with open(config_rates_path, "r", encoding="utf-8") as f:
    config_rates = json.load(f)

with open(air_rates_path, "r", encoding="utf-8") as f:
    air_rates = json.load(f)

with open(container_rates_path, "r", encoding="utf-8") as f:
    container_rates = json.load(f)

print("=" * 100)
print("남은 FAIL 6건 상세 분석 및 해결 방안")
print("=" * 100)

# FAIL 항목 추출
fail_items = df[df["Validation_Status"] == "FAIL"]

print(f"\n[1] 남은 FAIL 항목 상세 ({len(fail_items)}건)")
print("-" * 100)

for _, row in fail_items.iterrows():
    print(f"\n{'='*100}")
    print(f"No: {int(row['No'])}")
    print(f"  Order Ref: {row['Order Ref. Number']}")
    print(f"  DESCRIPTION: {row['DESCRIPTION']}")
    print(f"  RATE: {row['RATE']:.2f} | Ref_Rate: {row.get('Ref_Rate_USD', 'N/A')}")
    if pd.notna(row.get("Python_Delta")):
        print(f"  Delta: {row['Python_Delta']:.2f}%")
    print(
        f"  Charge_Group: {row['Charge_Group']} | CG_Band: {row.get('CG_Band', 'N/A')}"
    )
    print(f"  Notes: {row['Validation_Notes']}")

# 카테고리 분류
print("\n" + "=" * 100)
print("[2] FAIL 항목 카테고리")
print("=" * 100)

print("\nCharge Group 분포:")
fail_charge_group = fail_items["Charge_Group"].value_counts()
for group, count in fail_charge_group.items():
    print(f"  - {group}: {count}건 ({count/len(fail_items)*100:.1f}%)")

print("\nDESCRIPTION 분류:")
fail_desc = fail_items["DESCRIPTION"].value_counts()
for desc, count in fail_desc.items():
    print(f"  - {desc}: {count}건")

# 요율 파일에서 해당 항목 검색
print("\n" + "=" * 100)
print("[3] 요율 파일 매칭 분석")
print("=" * 100)

print("\n[A] Portal Fees 매칭 (config_contract_rates.json)")
print("-" * 100)
portal_fees = config_rates.get("portal_fees_aed", {})
print("Config에 등록된 Portal Fees:")
for fee_name, fee_info in portal_fees.items():
    print(f"  - {fee_name}: {fee_info['rate_usd']} USD ({fee_info['rate_aed']} AED)")

print("\n[B] AIR 요율 매칭 (air_cargo_rates.json)")
print("-" * 100)
print("Abu Dhabi Airport 관련 요율:")
for record in air_rates["records"]:
    if record.get("port") == "Abu Dhabi Airport":
        desc = record.get("description")
        rate_info = record.get("rate", {})
        if rate_info:
            print(f"  - {desc}: {rate_info.get('amount')} {rate_info.get('currency')}")

print("\n[C] DO FEE 매칭 (HE 항목)")
print("-" * 100)
do_fee_fails = fail_items[fail_items["DESCRIPTION"].str.contains("DO FEE", na=False)]
for _, row in do_fee_fails.iterrows():
    order_ref = row["Order Ref. Number"]
    rate = row["RATE"]
    ref_rate = row.get("Ref_Rate_USD")
    print(f"  - {order_ref}: RATE={rate}, Ref={ref_rate}")
    print(f"    분석: Order Ref는 HE인데 청구는 150 USD")
    print(f"    문제: SEPT Mode 정보가 없거나 FCL로 잘못 등록됨")

# 해결 방안 제시
print("\n" + "=" * 100)
print("[4] 해결 방안")
print("=" * 100)

print("\n[Portal Fees - 4건]")
print("  문제: PDF에서 AED 요율을 USD로 오인")
print("  현재: APPOINTMENT/DPC FEE Ref Rate = 2.00~2.59 (잘못된 값)")
print("  정상: APPOINTMENT = 7.35 USD, DPC = 9.53 USD")
print("  해결: Config Portal Fees 우선 적용 로직 추가")

print("\n[DO FEE - 2건]")
print("  문제: HE Order Ref인데 SEPT Mode가 FCL 또는 누락")
print("  해결: SEPT 시트 데이터 검증 또는 Invoice 원본 확인")

# 즉시 적용 가능한 개선
print("\n" + "=" * 100)
print("[5] 즉시 적용 가능한 개선")
print("=" * 100)

print("\n[Priority 1] Portal Fees Configuration 우선 적용")
print(
    """
# find_contract_ref_rate에 추가:
if "APPOINTMENT FEE" in desc_upper or "TRUCK APPOINTMENT" in desc_upper:
    return self.config_manager.get_portal_fee_rate("APPOINTMENT_FEE", "USD")

if "DPC FEE" in desc_upper or "DOCUMENT PROCESSING FEE" in desc_upper:
    return self.config_manager.get_portal_fee_rate("DPC_FEE", "USD")
"""
)

print("\n[Priority 2] HE DO FEE 항목 검증")
print("  - SEPT 시트에서 HE-0466, 0464 항목의 Mode 확인")
print("  - FCL이면 정상 (150 USD 맞음)")
print("  - AIR이면 Invoice 수정 필요 (150 -> 80 USD)")

print("\n" + "=" * 100)
print("[분석 완료]")
print("=" * 100)
