#!/usr/bin/env python3
"""
Invoice Audit System - CLI Wrapper
통합 Configuration + Contract 로직으로 전체 인보이스 검증

Version: 2.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from shipment_audit_engine import ShipmentAuditEngine


def run_full_validation():
    """통합 시스템으로 전체 검증 실행"""

    print("\n" + "=" * 80)
    print("Full Invoice Validation - Configuration Enhanced")
    print("=" * 80)

    # 시작 시간 측정
    start_time = time.time()

    # Audit System 초기화
    print("\n[STEP 1] Initializing Shipment Audit Engine with Configuration...")
    audit_system = ShipmentAuditEngine()

    # 설정 확인
    config_summary = audit_system.config_manager.get_config_summary()
    print(f"\n[CONFIG] Configuration Manager:")
    print(f"  Lanes loaded: {config_summary['lanes_loaded']}")
    print(f"  Cost Guard bands: {config_summary['cost_guard_bands']}")
    print(f"  Contract rates: {config_summary['contract_rates']}")
    print(f"  Portal fees: {config_summary['portal_fees']}")

    # Excel 파일 확인
    print(f"\n[STEP 2] Checking Excel file...")
    print(f"  File: {audit_system.excel_file.name}")
    print(f"  Exists: {audit_system.excel_file.exists()}")
    if audit_system.excel_file.exists():
        file_size = audit_system.excel_file.stat().st_size / 1024 / 1024
        print(f"  Size: {file_size:.2f} MB")

    # 전체 검증 실행
    print(f"\n[STEP 3] Running full validation...")
    try:
        results = audit_system.run_full_enhanced_audit()

        # 처리 시간
        elapsed_time = time.time() - start_time

        # 결과 요약
        print(f"\n[RESULTS]")
        print(f"  Total items processed: {results['summary']['total_items']}")
        print(f"  Total sheets: {results['summary']['total_sheets']}")
        print(f"  Processing time: {elapsed_time:.2f} seconds")

        # Contract 검증 분석
        contract_items = [
            item
            for item in results["detailed_results"]
            if item.get("charge_group") == "Contract"
        ]
        contract_with_ref = len(
            [item for item in contract_items if item.get("ref_rate_usd") is not None]
        )
        contract_coverage = (
            (contract_with_ref / len(contract_items) * 100)
            if len(contract_items) > 0
            else 0
        )

        print(f"\n[CONTRACT VALIDATION]")
        print(f"  Total Contract items: {len(contract_items)}")
        print(f"  Items with ref_rate: {contract_with_ref}")
        print(f"  Coverage: {contract_coverage:.1f}%")

        # 상태 분포
        status_counts = {}
        for item in results["detailed_results"]:
            status = item.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

        print(f"\n[STATUS DISTRIBUTION]")
        for status, count in sorted(status_counts.items()):
            percentage = (
                (count / results["summary"]["total_items"] * 100)
                if results["summary"]["total_items"] > 0
                else 0
            )
            print(f"  {status}: {count} ({percentage:.1f}%)")

        # Charge Group 분포
        charge_groups = {}
        for item in results["detailed_results"]:
            group = item.get("charge_group", "UNKNOWN")
            charge_groups[group] = charge_groups.get(group, 0) + 1

        print(f"\n[CHARGE GROUP DISTRIBUTION]")
        for group, count in sorted(charge_groups.items()):
            percentage = (
                (count / results["summary"]["total_items"] * 100)
                if results["summary"]["total_items"] > 0
                else 0
            )
            print(f"  {group}: {count} ({percentage:.1f}%)")

        # 성능 메트릭
        items_per_second = (
            results["summary"]["total_items"] / elapsed_time if elapsed_time > 0 else 0
        )
        print(f"\n[PERFORMANCE]")
        print(f"  Items/second: {items_per_second:.1f}")
        print(
            f"  Avg time/item: {elapsed_time / results['summary']['total_items'] * 1000:.2f} ms"
        )

        # 결과 파일 위치
        print(f"\n[OUTPUT FILES]")
        print(f"  Results directory: {audit_system.out_dir}")

        print("\n" + "=" * 80)
        print("[SUCCESS] Full validation completed!")
        print("=" * 80)

        return results

    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    run_full_validation()
