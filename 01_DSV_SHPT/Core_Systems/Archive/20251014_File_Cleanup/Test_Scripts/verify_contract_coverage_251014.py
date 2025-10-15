#!/usr/bin/env python3
"""
Contract Validation Coverage Verification
통합 후 Contract 검증 커버리지 확인 도구

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import pandas as pd
import sys
from pathlib import Path

# Import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from shpt_sept_2025_enhanced_audit import SHPTSept2025EnhancedAuditSystem


def verify_contract_coverage():
    """Contract 검증 커버리지 검증"""

    # 최신 CSV 결과 로드
    results_dir = Path(__file__).parent.parent / "Results" / "Sept_2025" / "CSV"
    csv_files = list(results_dir.glob("shpt_sept_2025_enhanced_result_*.csv"))

    if not csv_files:
        print("[ERROR] No CSV result files found")
        return

    latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"[INFO] Analyzing: {latest_csv.name}")

    df = pd.read_csv(latest_csv)

    # Contract 항목만 필터링
    contract_items = df[df["charge_group"] == "Contract"].copy()

    print("\n" + "=" * 80)
    print("Contract Validation Coverage Verification")
    print("=" * 80)

    # 기존 커버리지
    items_with_ref = len(contract_items[contract_items["ref_rate_usd"].notna()])
    items_without_ref = len(contract_items[contract_items["ref_rate_usd"].isna()])
    coverage_before = (
        (items_with_ref / len(contract_items) * 100) if len(contract_items) > 0 else 0
    )

    print(f"\n[BEFORE INTEGRATION]")
    print(f"Total Contract items: {len(contract_items)}")
    print(f"Items with ref_rate: {items_with_ref} ({coverage_before:.1f}%)")
    print(f"Items without ref_rate: {items_without_ref}")

    # 통합 후 재검증
    print(f"\n[AFTER INTEGRATION - Re-validation]")
    audit_system = SHPTSept2025EnhancedAuditSystem()

    found_count = 0
    not_found_count = 0
    found_items = []
    not_found_items = []

    for idx, row in contract_items.iterrows():
        item = {
            "description": row["description"],
            "rate_source": row["rate_source"],
            "unit_rate": row["unit_rate"],
        }

        ref_rate = audit_system._find_contract_ref_rate(item)

        if ref_rate is not None:
            found_count += 1
            found_items.append(
                {
                    "s_no": row["s_no"],
                    "description": row["description"],
                    "unit_rate": row["unit_rate"],
                    "ref_rate": ref_rate,
                    "delta": round((row["unit_rate"] - ref_rate) / ref_rate * 100, 2),
                }
            )
        else:
            not_found_count += 1
            not_found_items.append(
                {
                    "s_no": row["s_no"],
                    "description": row["description"],
                    "unit_rate": row["unit_rate"],
                }
            )

    coverage_after = (
        (found_count / len(contract_items) * 100) if len(contract_items) > 0 else 0
    )

    print(f"Total Contract items: {len(contract_items)}")
    print(f"Items with ref_rate: {found_count} ({coverage_after:.1f}%)")
    print(f"Items without ref_rate: {not_found_count}")

    # 개선 효과
    improvement = coverage_after - coverage_before
    print(f"\n[IMPROVEMENT]")
    print(f"Coverage improvement: +{improvement:.1f}%")
    print(f"Additional items validated: {found_count - items_with_ref}")

    # 상세 결과
    if found_count > 0:
        print(f"\n[VALIDATED ITEMS - Sample 10]")
        for item in found_items[:10]:
            print(f"  S/No {item['s_no']}: {item['description'][:50]}")
            print(
                f"    Rate: ${item['unit_rate']} | Ref: ${item['ref_rate']} | Delta: {item['delta']}%"
            )

    if not_found_count > 0:
        print(f"\n[NOT FOUND ITEMS - First 5]")
        for item in not_found_items[:5]:
            print(f"  S/No {item['s_no']}: {item['description']}")

    # 성과 평가
    print(f"\n" + "=" * 80)
    if coverage_after >= 90:
        print("[SUCCESS] Target coverage 90%+ achieved!")
    elif coverage_after >= 80:
        print("[GOOD] Coverage >80%, approaching target")
    elif improvement > 20:
        print("[PROGRESS] Significant improvement achieved")
    else:
        print("[NEEDS WORK] Additional improvements needed")

    print("=" * 80)

    return {
        "before": coverage_before,
        "after": coverage_after,
        "improvement": improvement,
        "found": found_count,
        "total": len(contract_items),
    }


if __name__ == "__main__":
    verify_contract_coverage()
