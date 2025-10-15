#!/usr/bin/env python3
"""
Contract 검증 개선 확인 스크립트
기존 CSV 결과에서 Contract 항목을 읽어와서 새 로직으로 ref_rate를 채우고 개선 효과를 측정
"""

import pandas as pd
import sys
from pathlib import Path

# Import UnifiedRateLoader
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from rate_loader import UnifiedRateLoader
from shpt_sept_2025_enhanced_audit import SHPTSept2025EnhancedAuditSystem


def test_contract_improvement():
    """Contract 검증 개선 테스트"""

    # 기존 CSV 결과 로드
    csv_file = (
        Path(__file__).parent.parent
        / "Results"
        / "Sept_2025"
        / "CSV"
        / "shpt_sept_2025_enhanced_result_20251012_123727.csv"
    )

    if not csv_file.exists():
        print(f"[ERROR] CSV file not found: {csv_file}")
        return

    df = pd.read_csv(csv_file)

    # Contract 항목만 필터링
    contract_items = df[df["charge_group"] == "Contract"].copy()

    print("=" * 80)
    print("Contract Validation Improvement Test")
    print("=" * 80)
    print()
    print(f"Total Contract Items: {len(contract_items)}")
    print()

    # Rate Loader 초기화
    rate_dir = Path(__file__).parent.parent.parent / "Rate"
    rate_loader = UnifiedRateLoader(rate_dir)
    rate_loader.load_all_rates()

    # Audit System 초기화 (helper methods 사용)
    audit_system = SHPTSept2025EnhancedAuditSystem()

    # 각 Contract 항목에 대해 ref_rate 조회 시뮬레이션
    found_count = 0
    not_found_count = 0

    ref_rates_found = []

    for idx, row in contract_items.iterrows():
        item = {
            "description": row["description"],
            "rate_source": row["rate_source"],
            "unit_rate": row["unit_rate"],
        }

        # ref_rate 조회
        ref_rate = audit_system._find_contract_ref_rate(item)

        if ref_rate is not None:
            found_count += 1

            # Delta 계산
            delta_pct = rate_loader.calculate_delta_percent(row["unit_rate"], ref_rate)
            cg_band = rate_loader.get_cost_guard_band(delta_pct)

            ref_rates_found.append(
                {
                    "s_no": row["s_no"],
                    "description": row["description"],
                    "draft_rate": row["unit_rate"],
                    "ref_rate": ref_rate,
                    "delta_pct": delta_pct,
                    "cg_band": cg_band,
                }
            )
        else:
            not_found_count += 1

    # 결과 출력
    print("=" * 80)
    print("Results")
    print("=" * 80)
    print(f"ref_rate Found: {found_count} ({found_count/len(contract_items)*100:.1f}%)")
    print(
        f"ref_rate Not Found: {not_found_count} ({not_found_count/len(contract_items)*100:.1f}%)"
    )
    print()

    # 개선 비교
    print("=" * 80)
    print("Before vs After")
    print("=" * 80)
    print(f"Before: ref_rate filled = 0/64 (0.0%)")
    print(f"After:  ref_rate filled = {found_count}/64 ({found_count/64*100:.1f}%)")
    print(f"Improvement: +{found_count} items (+{found_count/64*100:.1f}%)")
    print()

    # COST-GUARD 밴드 분포
    if ref_rates_found:
        print("=" * 80)
        print("COST-GUARD Band Distribution")
        print("=" * 80)

        band_counts = {}
        for item in ref_rates_found:
            band = item["cg_band"]
            band_counts[band] = band_counts.get(band, 0) + 1

        for band in ["PASS", "WARN", "HIGH", "CRITICAL"]:
            count = band_counts.get(band, 0)
            pct = count / len(ref_rates_found) * 100 if ref_rates_found else 0
            print(f"{band}: {count} ({pct:.1f}%)")
        print()

    # 샘플 항목 출력
    if ref_rates_found:
        print("=" * 80)
        print("Sample Contract Items (First 10)")
        print("=" * 80)

        for item in ref_rates_found[:10]:
            print(f"\nS/No {item['s_no']}: {item['description'][:60]}")
            print(f"  Draft: ${item['draft_rate']:.2f}")
            print(f"  Ref:   ${item['ref_rate']:.2f}")
            print(f"  Delta: {item['delta_pct']:.2f}%")
            print(f"  Band:  {item['cg_band']}")

    # 성공 판정
    print()
    print("=" * 80)
    if found_count >= 55:  # 85.9% 목표
        print("[PASS] Contract validation improvement achieved!")
        print(
            f"Target: >=55 items (85.9%), Actual: {found_count} ({found_count/64*100:.1f}%)"
        )
        return True
    else:
        print("[WARN] Contract validation improvement below target")
        print(
            f"Target: >=55 items (85.9%), Actual: {found_count} ({found_count/64*100:.1f}%)"
        )
        return False


if __name__ == "__main__":
    success = test_contract_improvement()
    sys.exit(0 if success else 1)
