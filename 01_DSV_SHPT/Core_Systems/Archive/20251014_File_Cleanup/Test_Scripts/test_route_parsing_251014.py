#!/usr/bin/env python3
"""
경로 파싱 로직 테스트
"""

import re

test_descriptions = [
    "TRANSPORTATION CHARGES (1 X 20DC / 2 X 40HC) FROM KHALIFA PORT TO DSV MUSSAFAH YARD",
    "TRANSPORTATION CHARGES (1 X 20DC / 2 X 40HC) FROM DSV MUSSAFAH YARD TO KHALIFA PORT (EMPTY RETURN)",
    "TRANSPORTATION CHARGES (1 X 20DC) FROM KHALIFA PORT TO DSV MUSSAFAH YARD",
    "TRANSPORTATION CHARGES (1 FB) FROM AUH AIRPORT TO MOSB",
    "TRANSPORTATION CHARGES (1 X 40HC) FROM KP TO DSV MUSSAFAH YARD",
    "TRANSPORTATION CHARGES (3 TON PU) FROM AUH AIRPORT TO MOSB",
    "TRANSPORTATION CHARGES (1 FB) FROM AUH AIRPORT TO MIRFA + SHUWEIHAT",
]

print("=" * 100)
print("경로 파싱 테스트")
print("=" * 100)

# 현재 로직
print("\n[현재 로직 테스트]")
print("-" * 100)

for desc in test_descriptions:
    desc_upper = desc.upper()
    match = re.search(r"FROM\s+([A-Z\s]+)\s+TO\s+([A-Z\s]+)", desc_upper)

    if match:
        from_port = match.group(1).strip()
        to_dest = match.group(2).strip()
        print(f"\n[OK] {desc[:60]}")
        print(f"  From: '{from_port}'")
        print(f"  To: '{to_dest}'")
    else:
        print(f"\n[FAIL] {desc[:60]}")
        print("  경로 파싱 실패!")

# 개선된 로직
print("\n\n" + "=" * 100)
print("[개선된 로직 테스트]")
print("=" * 100)

port_aliases = {
    "KP": "KHALIFA PORT",
    "KHP": "KHALIFA PORT",
    "AUH AIRPORT": "ABU DHABI AIRPORT",
    "DSV MUSSAFAH": "DSV MUSSAFAH YARD",
    "DSV MUSAFFAH": "DSV MUSSAFAH YARD",
}

for desc in test_descriptions:
    desc_upper = desc.upper()

    # 패턴: FROM ... TO ... (괄호나 문장 끝까지)
    match = re.search(r"FROM\s+(.+?)\s+TO\s+(.+?)(?:\s*\(|$|\s*\+)", desc_upper)

    if match:
        from_port = match.group(1).strip()
        to_dest = match.group(2).strip()

        # 약어 정규화
        for abbr, full_name in port_aliases.items():
            from_port = from_port.replace(abbr, full_name)
            to_dest = to_dest.replace(abbr, full_name)

        print(f"\n[OK] {desc[:60]}")
        print(f"  From: '{from_port}'")
        print(f"  To: '{to_dest}'")
    else:
        print(f"\n[FAIL] {desc[:60]}")
        print("  경로 파싱 실패!")

print("\n" + "=" * 100)
print("[분석 완료]")
print("=" * 100)

print("\n필요한 Lane:")
print("  1. KHALIFA PORT → DSV MUSSAFAH YARD (252 USD)")
print("  2. DSV MUSSAFAH YARD → KHALIFA PORT (252 USD)")
print("  3. ABU DHABI AIRPORT → MOSB (200 USD)")
print("  4. ABU DHABI AIRPORT → MOSB (100 USD - 3 TON PU)")
print("  5. ABU DHABI AIRPORT → MIRFA (810/2 = 405 USD 추정)")
print("  6. ABU DHABI AIRPORT → SHUWEIHAT (810/2 = 405 USD 추정)")
