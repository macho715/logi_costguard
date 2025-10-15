#!/usr/bin/env python3
"""
누락된 Contract 항목 분석
ref_rate를 찾지 못한 11개 항목을 분석하여 개선 방안 도출
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from rate_loader import UnifiedRateLoader
from shpt_sept_2025_enhanced_audit import SHPTSept2025EnhancedAuditSystem


def analyze_missing_contracts():
    """누락된 Contract 항목 분석"""

    # CSV 로드
    csv_file = (
        Path(__file__).parent.parent
        / "Results"
        / "Sept_2025"
        / "CSV"
        / "shpt_sept_2025_enhanced_result_20251012_123727.csv"
    )
    df = pd.read_csv(csv_file)

    # Contract 항목
    contract_items = df[df["charge_group"] == "Contract"].copy()

    # Rate Loader 및 Audit System
    rate_dir = Path(__file__).parent.parent.parent / "Rate"
    rate_loader = UnifiedRateLoader(rate_dir)
    rate_loader.load_all_rates()

    audit_system = SHPTSept2025EnhancedAuditSystem()

    # 누락 항목 찾기
    missing_items = []

    for idx, row in contract_items.iterrows():
        item = {
            "description": row["description"],
            "rate_source": row["rate_source"],
            "unit_rate": row["unit_rate"],
        }

        ref_rate = audit_system._find_contract_ref_rate(item)

        if ref_rate is None:
            missing_items.append(
                {
                    "s_no": row["s_no"],
                    "sheet": row["sheet_name"],
                    "description": row["description"],
                    "unit_rate": row["unit_rate"],
                    "quantity": row["quantity"],
                }
            )

    print("=" * 80)
    print(f"Missing Contract Items Analysis ({len(missing_items)} items)")
    print("=" * 80)
    print()

    if not missing_items:
        print("[SUCCESS] All contract items have ref_rate!")
        return

    # Description 패턴 분석
    pattern_counts = {}
    for item in missing_items:
        desc = item["description"]
        # 키워드 추출
        if "TERMINAL HANDLING" in desc.upper():
            pattern = "TERMINAL HANDLING"
        elif "THC" in desc.upper():
            pattern = "THC"
        elif "TRANSPORTATION" in desc.upper():
            pattern = "TRANSPORTATION"
        elif "TRUCKING" in desc.upper():
            pattern = "TRUCKING"
        else:
            pattern = "OTHER"

        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

    print("Pattern Distribution:")
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"  {pattern}: {count} items")
    print()

    # 상세 목록
    print("=" * 80)
    print("Detailed List")
    print("=" * 80)

    for i, item in enumerate(missing_items, 1):
        print(f"\n{i}. S/No {item['s_no']} - {item['sheet']}")
        print(f"   Description: {item['description']}")
        print(f"   Unit Rate: ${item['unit_rate']:.2f}")
        print(f"   Qty: {item['quantity']}")

    # 개선 제안
    print()
    print("=" * 80)
    print("Improvement Suggestions")
    print("=" * 80)

    if "TERMINAL HANDLING" in pattern_counts or "THC" in pattern_counts:
        print("1. Add Terminal Handling keywords:")
        print("   - 'THC' -> 'Terminal Handling Charge'")
        print("   - Extract container type (20DC, 40HC) from description")

    if "TRANSPORTATION" in pattern_counts or "TRUCKING" in pattern_counts:
        print("2. Improve Transportation parsing:")
        print("   - Better regex for route extraction")
        print("   - Handle variations like 'TRUCKING' vs 'TRANSPORTATION'")

    if "OTHER" in pattern_counts:
        print("3. Special items may need manual mapping")


if __name__ == "__main__":
    analyze_missing_contracts()
