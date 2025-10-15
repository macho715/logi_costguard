#!/usr/bin/env python3
"""
TRANSPORTATION Lane lookup 디버깅
"""

import sys
from pathlib import Path

# Add paths
root = Path(__file__).parent
shared_path = root.parent.parent / "00_Shared"
sys.path.insert(0, str(shared_path))

from config_manager import ConfigurationManager
import pandas as pd

# Initialize config manager
rate_dir = root.parent.parent / "Rate"
config_manager = ConfigurationManager(str(rate_dir))

# Test transportation descriptions
test_items = [
    "TRANSPORTATION CHARGES (1 X 20DC / 2 X 40HC) FROM KHALIFA PORT TO DSV MUSSAFAH YARD",
    "TRANSPORTATION CHARGES (1 X 20DC / 2 X 40HC) FROM DSV MUSSAFAH YARD TO KHALIFA PORT (EMPTY RETURN)",
    "TRANSPORTATION CHARGES (1 FB) FROM AUH AIRPORT TO MOSB",
    "TRANSPORTATION CHARGES (1 X 40HC) FROM KP TO DSV MUSSAFAH YARD",
    "TRANSPORTATION CHARGES (3 TON PU) FROM AUH AIRPORT TO MOSB",
]

print("=" * 100)
print("TRANSPORTATION Lane Lookup 디버깅")
print("=" * 100)

# Check loaded lanes
lane_map = config_manager.get_lane_map()
sea_lanes = lane_map.get("sea_transport", {})
air_lanes = lane_map.get("air_transport", {})

print(f"\nLoaded Sea Transport lanes: {len(sea_lanes)}")
print("Sea Transport Lanes:")
for lane_key, lane_info in sea_lanes.items():
    print(
        f"  {lane_key}: {lane_info['port']} → {lane_info['destination']} ({lane_info['rate']} USD)"
    )

print(f"\nLoaded Air Transport lanes: {len(air_lanes)}")
print("Air Transport Lanes:")
for lane_key, lane_info in air_lanes.items():
    print(
        f"  {lane_key}: {lane_info['port']} → {lane_info['destination']} ({lane_info['rate']} USD)"
    )

print("\n" + "=" * 100)
print("경로 파싱 및 Lane Lookup 테스트")
print("=" * 100)

# Simplified parsing function
import re


def parse_route(description):
    desc_upper = str(description).upper()
    match = re.search(r"FROM\s+(.+?)\s+TO\s+(.+?)(?:\s*\(|$|\s*\+)", desc_upper)
    if match:
        from_port = match.group(1).strip()
        to_dest = match.group(2).strip()
        return (from_port, to_dest)
    return (None, None)


def normalize_location(location, config_manager):
    """위치명 정규화"""
    normalization = config_manager.get_normalization_aliases()

    location_clean = str(location).strip().upper()

    # Check ports
    for standard, aliases_list in normalization.get("ports", {}).items():
        if isinstance(aliases_list, list):
            if (
                location_clean in [str(a).upper() for a in aliases_list]
                or location_clean == str(standard).upper()
            ):
                return standard
        elif location_clean == str(standard).upper():
            return standard

    # Check destinations
    for standard, aliases_list in normalization.get("destinations", {}).items():
        if isinstance(aliases_list, list):
            if (
                location_clean in [str(a).upper() for a in aliases_list]
                or location_clean == str(standard).upper()
            ):
                return standard
        elif location_clean == str(standard).upper():
            return standard

    return location_clean


for desc in test_items:
    print(f"\n[Test] {desc[:80]}")

    # Parse route
    port, dest = parse_route(desc)
    print(f"  Parsed: {port} → {dest}")

    if port and dest:
        # Normalize
        norm_port = normalize_location(port, config_manager)
        norm_dest = normalize_location(dest, config_manager)
        print(f"  Normalized: {norm_port} → {norm_dest}")

        # Try to get lane rate
        lane_rate = config_manager.get_lane_rate(norm_port, norm_dest, "per truck")
        print(
            f"  Lane Rate: {lane_rate} USD" if lane_rate else "  Lane Rate: NOT FOUND"
        )

        # Debug: Show exact match attempts
        print(f"  Debug - Looking for: port='{norm_port}', dest='{norm_dest}'")

print("\n" + "=" * 100)
print("Normalization Aliases 확인")
print("=" * 100)

norm_aliases = config_manager.get_normalization_aliases()
print("\nPorts:")
for key, value in norm_aliases.get("ports", {}).items():
    print(f"  {key} = {value}")

print("\nDestinations:")
for key, value in norm_aliases.get("destinations", {}).items():
    print(f"  {key} = {value}")
