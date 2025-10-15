#!/usr/bin/env python3
"""
Transportation 항목 검증 전체 과정 추적
"""

import sys
from pathlib import Path
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")

# Add paths
root = Path(__file__).parent
shared_path = root.parent.parent / "00_Shared"
sys.path.insert(0, str(shared_path))

from config_manager import ConfigurationManager
from validate_masterdata_with_config_251014 import MasterDataValidator

# Test single item
excel_file = root / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm"
validator = MasterDataValidator(str(excel_file))

# Load MasterData
df = pd.read_excel(excel_file, sheet_name="MasterData")

# Get Transportation item
test_row = df[df["No"] == 5].iloc[0]

print("=" * 100)
print("Transportation 항목 검증 전체 과정 추적")
print("=" * 100)

print(f"\nItem No: {test_row['No']}")
print(f"Description: {test_row['DESCRIPTION']}")
print(f"Rate: {test_row['RATE']}")
print(f"Rate Source: {test_row.get('RATE SOURCE', 'N/A')}")

# Classify charge group
charge_group = validator.classify_charge_group(test_row.get("RATE SOURCE"))
print(f"\nCharge Group: {charge_group}")

# Find ref rate
print("\n" + "=" * 100)
print("find_contract_ref_rate 호출")
print("=" * 100)

ref_rate = validator.find_contract_ref_rate(
    test_row["DESCRIPTION"], test_row.get("RATE SOURCE"), test_row
)

print(f"\nReturned Ref Rate: {ref_rate}")
print(f"Type: {type(ref_rate)}")

if ref_rate is not None:
    print(f"✅ Ref Rate 반환됨: {ref_rate} USD")
else:
    print("❌ Ref Rate가 None입니다!")

    # Debug internal process
    print("\n" + "-" * 100)
    print("내부 프로세스 디버깅")
    print("-" * 100)

    desc_upper = str(test_row["DESCRIPTION"]).upper()

    # Check if it triggers transportation logic
    trans_keywords = ["TRANSPORTATION", "TRUCKING", "INLAND", "FROM", "TO"]
    is_trans = any(kw in desc_upper for kw in trans_keywords)
    print(f"Transportation 키워드 매칭: {is_trans}")

    if is_trans:
        # Parse route
        port, dest = validator._parse_transportation_route(test_row["DESCRIPTION"])
        print(f"파싱된 경로: '{port}' → '{dest}'")

        if port and dest:
            # Check lane rate
            lane_rate = validator.config_manager.get_lane_rate(port, dest, "per truck")
            print(f"Lane Rate 조회 결과: {lane_rate}")

print("\n" + "=" * 100)
print("분석 완료")
print("=" * 100)
