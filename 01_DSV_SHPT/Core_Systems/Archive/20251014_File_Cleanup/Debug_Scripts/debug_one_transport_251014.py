#!/usr/bin/env python3
"""
단일 TRANSPORTATION 항목 디버깅
"""

import sys
from pathlib import Path
import pandas as pd

# Add paths
root = Path(__file__).parent
shared_path = root.parent.parent / "00_Shared"
sys.path.insert(0, str(shared_path))

from config_manager import ConfigurationManager

# Initialize
rate_dir = root.parent.parent / "Rate"
config_manager = ConfigurationManager(str(rate_dir))

# Test item
test_row = pd.Series(
    {
        "No": 5,
        "DESCRIPTION": "TRANSPORTATION CHARGES (1 X 20DC / 2 X 40HC) FROM KHALIFA PORT TO DSV MUSSAFAH YARD",
        "RATE": 252.0,
        "CHARGE GROUP": "Contract",
        "Order Ref. Number": "HVDC-ADOPT-SCT-0126",
    }
)

print("=" * 100)
print("단일 TRANSPORTATION 항목 디버깅")
print("=" * 100)

description = test_row["DESCRIPTION"]
desc_upper = description.upper()

print(f"\nItem No: {test_row['No']}")
print(f"Description: {description}")
print(f"Rate: {test_row['RATE']}")
print(f"Charge Group: {test_row['CHARGE GROUP']}")

# Step 1: Check if it's a transportation item
print("\n" + "-" * 100)
print("Step 1: Transportation 키워드 체크")
print("-" * 100)

trans_keywords = ["TRANSPORTATION", "TRUCKING", "INLAND", "FROM", "TO"]
is_trans = any(kw in desc_upper for kw in trans_keywords)
print(f"Is Transportation: {is_trans}")
print(f"Matched keywords: {[kw for kw in trans_keywords if kw in desc_upper]}")

# Step 2: Parse route
print("\n" + "-" * 100)
print("Step 2: 경로 파싱")
print("-" * 100)

import re

match = re.search(r"FROM\s+(.+?)\s+TO\s+(.+?)(?:\s*\(|$|\s*\+)", desc_upper)
if match:
    raw_port = match.group(1).strip()
    raw_dest = match.group(2).strip()
    print(f"Raw port: '{raw_port}'")
    print(f"Raw dest: '{raw_dest}'")

    # Step 3: Normalize
    print("\n" + "-" * 100)
    print("Step 3: 정규화")
    print("-" * 100)

    normalization = config_manager.get_normalization_aliases()

    def normalize(location):
        location_upper = str(location).strip().upper()

        # Check ports
        ports = normalization.get("ports", {})
        for alias, standard in ports.items():
            if str(alias).upper() == location_upper:
                return standard

        # Check destinations
        destinations = normalization.get("destinations", {})
        for alias, standard in destinations.items():
            if str(alias).upper() == location_upper:
                return standard

        return location.strip()

    norm_port = normalize(raw_port)
    norm_dest = normalize(raw_dest)

    print(f"Normalized port: '{norm_port}'")
    print(f"Normalized dest: '{norm_dest}'")

    # Step 4: Lane lookup
    print("\n" + "-" * 100)
    print("Step 4: Lane Rate 조회")
    print("-" * 100)

    lane_rate = config_manager.get_lane_rate(norm_port, norm_dest, "per truck")
    print(f"Lane Rate Result: {lane_rate}")

    # Step 5: Debug lane map
    print("\n" + "-" * 100)
    print("Step 5: Lane Map 확인")
    print("-" * 100)

    lane_map = config_manager.get_lane_map()
    sea_lanes = lane_map.get("sea_transport", {})
    air_lanes = lane_map.get("air_transport", {})

    print(f"\nSea Transport Lanes ({len(sea_lanes)}):")
    for lane_key, lane_info in list(sea_lanes.items())[:5]:
        print(
            f"  {lane_key}: {lane_info.get('port')} → {lane_info.get('destination')} ({lane_info.get('rate')} USD)"
        )

    print(f"\nAir Transport Lanes ({len(air_lanes)}):")
    for lane_key, lane_info in list(air_lanes.items())[:5]:
        print(
            f"  {lane_key}: {lane_info.get('port')} → {lane_info.get('destination')} ({lane_info.get('rate')} USD)"
        )

    # Step 6: Manual check
    print("\n" + "-" * 100)
    print("Step 6: 수동 Lane 검색")
    print("-" * 100)

    print(f"\nSearching for: port='{norm_port}', dest='{norm_dest}'")

    for transport_type, lanes in [
        ("sea_transport", sea_lanes),
        ("air_transport", air_lanes),
    ]:
        for lane_key, lane_info in lanes.items():
            lane_port = str(lane_info.get("port", "")).strip()
            lane_dest = str(lane_info.get("destination", "")).strip()

            if lane_port == norm_port and lane_dest == norm_dest:
                print(f"\n[FOUND] {transport_type}/{lane_key}")
                print(f"  Port Match: '{lane_port}' == '{norm_port}'")
                print(f"  Dest Match: '{lane_dest}' == '{norm_dest}'")
                print(f"  Rate: {lane_info.get('rate')} USD")
                break
else:
    print("경로 파싱 실패!")

print("\n" + "=" * 100)
print("디버깅 완료")
print("=" * 100)
