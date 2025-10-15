#!/usr/bin/env python3
"""
INLAND TRUCKING 관련 Rate 찾기
"""

import json
from pathlib import Path

# Rate 파일들 로드
rate_dir = Path(__file__).parent.parent.parent / "Rate"

# 1. inland_trucking_reference_rates_clean (2).json
inland_file = rate_dir / "inland_trucking_reference_rates_clean (2).json"
inland_data = json.load(open(inland_file, "r", encoding="utf-8"))

# 2. container_cargo_rates (1).json
container_file = rate_dir / "container_cargo_rates (1).json"
container_data = json.load(open(container_file, "r", encoding="utf-8"))

print("=" * 100)
print("TRANSPORTATION 관련 Rate 검색")
print("=" * 100)

# Khalifa Port to Storage Yard (DSV Mussafah는 Storage Yard로 분류될 가능성)
print("\n[1] Khalifa Port → Storage Yard:")
khalifa_storage = [
    r
    for r in inland_data["records"]
    if "Khalifa Port" in r.get("port", "")
    and "Storage" in r.get("destination", "")
]
for r in khalifa_storage[:3]:
    print(
        f"  {r['category']} - {r['unit']}: {r['rate']['amount']} USD (destination: {r['destination']})"
    )

# Container Khalifa Port rates
print("\n[2] Container - Khalifa Port:")
container_khalifa = [
    r
    for r in container_data["records"]
    if "Khalifa Port" in r.get("port", "")
    and "Storage" in str(r.get("destination", ""))
]
for r in container_khalifa[:3]:
    print(
        f"  {r['description']} - {r['unit']}: {r['rate']['amount']} USD (destination: {r['destination']})"
    )

# Abu Dhabi Airport rates
print("\n[3] Air - Abu Dhabi Airport:")
air_abu_dhabi = [
    r
    for r in inland_data["records"]
    if "Abu Dhabi Airport" in r.get("port", "") or "AUH" in r.get("port", "")
]
print(f"  Found {len(air_abu_dhabi)} records")
for r in air_abu_dhabi[:5]:
    print(
        f"  {r['destination']} - {r['unit']}: {r['rate']['amount']} USD ({r.get('charge_description', '')})"
    )

# Mina Zayed or MOSB rates
print("\n[4] Storage Yard / MOSB destinations:")
storage_rates = [
    r
    for r in inland_data["records"]
    if "Storage" in r.get("destination", "") and "Abu Dhabi" in r.get("port", "")
]
for r in storage_rates[:3]:
    print(
        f"  {r['port']} → {r['destination']}: {r['rate']['amount']} USD ({r['unit']})"
    )

print("\n" + "=" * 100)
print("[분석 결론]")
print("=" * 100)

print("\nKhalifa Port → Storage Yard (DSV Mussafah):")
print("  - Container 252 USD (from inland_trucking)")
print("  - 실제 Invoice: 252 USD")
print("  - 매칭!")

print("\nAbu Dhabi Airport:")
print("  - MIRFA SITE: 150 USD (Upto 3ton)")
print("  - SHUWEIHAT Site: 210 USD (Upto 3ton)")
print("  - Storage Yard: 100 USD (Upto 3ton)")
print("  - 실제 Invoice MOSB: 200 USD, 100 USD")

print("\n필요한 Lane:")
print("  1. Khalifa Port → DSV Mussafah Yard: 252 USD")
print("  2. DSV Mussafah Yard → Khalifa Port: 252 USD")
print("  3. Abu Dhabi Airport → MOSB (Storage Yard): 100-200 USD")
print("  4. Abu Dhabi Airport → MIRFA: 150 USD")
print("  5. Abu Dhabi Airport → SHUWEIHAT: 210 USD")

