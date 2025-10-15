#!/usr/bin/env python3
"""
Contract Validation Integration Tests (TDD)
SHPT Contract 검증 로직 통합 테스트 - Kent Beck TDD 원칙

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import pytest
import sys
from pathlib import Path

# 상위 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
sys.path.insert(0, str(Path(__file__).parent))

from shpt_sept_2025_enhanced_audit import SHPTSept2025EnhancedAuditSystem
from config_manager import ConfigurationManager


class TestContractIntegration:
    """Contract 검증 통합 테스트 (TDD Red-Green-Refactor)"""

    @pytest.fixture
    def audit_system(self):
        """Audit system fixture"""
        return SHPTSept2025EnhancedAuditSystem()

    # RED PHASE: Configuration Manager 로드 테스트
    def test_should_load_configuration_manager(self, audit_system):
        """ConfigurationManager가 로드되어야 함"""
        assert audit_system.config_manager is not None
        assert audit_system.config_manager.is_loaded is True

    def test_should_load_lane_map_from_config(self, audit_system):
        """Lane Map이 설정 파일에서 로드되어야 함"""
        assert audit_system.lane_map is not None
        assert len(audit_system.lane_map) > 0
        # 최소 5개 기본 Lane (SHPT 시스템 기준)
        assert len(audit_system.lane_map) >= 5

    def test_should_load_normalization_map_from_config(self, audit_system):
        """Normalization Map이 설정 파일에서 로드되어야 함"""
        assert audit_system.normalization_map is not None
        assert "ports" in audit_system.normalization_map
        assert "destinations" in audit_system.normalization_map

    def test_should_load_cost_guard_bands_from_config(self, audit_system):
        """COST-GUARD 밴드가 설정 파일에서 로드되어야 함"""
        assert audit_system.cost_guard_bands is not None
        assert "PASS" in audit_system.cost_guard_bands
        assert "WARN" in audit_system.cost_guard_bands
        assert "HIGH" in audit_system.cost_guard_bands
        assert "CRITICAL" in audit_system.cost_guard_bands

    # GREEN PHASE: Contract 검증 로직 통합 테스트
    def test_should_find_ref_rate_for_khalifa_to_storage_yard(self, audit_system):
        """Khalifa Port → Storage Yard Lane 요율을 찾아야 함"""
        item = {
            "s_no": 1,
            "sheet_name": "TEST-001",
            "description": "TRANSPORTATION FROM KHALIFA PORT TO STORAGE YARD",
            "rate_source": "CONTRACT",
            "unit_rate": 252.00,
            "quantity": 3,
            "total_usd": 756.00,
            "formula_text": "",
        }

        result = audit_system.validate_enhanced_item(item, [])

        assert result["charge_group"] == "Contract"
        assert result["ref_rate_usd"] is not None
        assert result["ref_rate_usd"] == 252.00
        assert result["delta_pct"] == 0.0
        assert result["cg_band"] == "PASS"

    def test_should_find_ref_rate_for_mirfa_transportation(self, audit_system):
        """DSV Yard → MIRFA 운송 요율을 찾아야 함"""
        item = {
            "s_no": 2,
            "sheet_name": "TEST-002",
            "description": "TRANSPORTATION FROM DSV YARD TO MIRFA SITE",
            "rate_source": "CONTRACT",
            "unit_rate": 420.00,
            "quantity": 2,
            "total_usd": 840.00,
            "formula_text": "",
        }

        result = audit_system.validate_enhanced_item(item, [])

        assert result["ref_rate_usd"] is not None
        assert result["ref_rate_usd"] == 420.00
        assert result["delta_pct"] == 0.0

    def test_should_find_ref_rate_for_shuweihat_transportation(self, audit_system):
        """DSV Yard → SHUWEIHAT 운송 요율을 찾아야 함"""
        item = {
            "s_no": 3,
            "sheet_name": "TEST-003",
            "description": "TRANSPORTATION FROM STORAGE YARD TO SHUWEIHAT SITE",
            "rate_source": "CONTRACT",
            "unit_rate": 600.00,
            "quantity": 1,
            "total_usd": 600.00,
            "formula_text": "",
        }

        result = audit_system.validate_enhanced_item(item, [])

        assert result["ref_rate_usd"] is not None
        assert result["ref_rate_usd"] == 600.00

    def test_should_find_ref_rate_for_master_do_fee(self, audit_system):
        """MASTER DO FEE 고정 요율을 찾아야 함"""
        item = {
            "s_no": 4,
            "sheet_name": "TEST-004",
            "description": "MASTER DO FEE",
            "rate_source": "CONTRACT",
            "unit_rate": 150.00,
            "quantity": 1,
            "total_usd": 150.00,
            "formula_text": "",
        }

        result = audit_system.validate_enhanced_item(item, [])

        assert result["ref_rate_usd"] is not None
        assert result["ref_rate_usd"] == 150.00
        assert result["delta_pct"] == 0.0

    def test_should_calculate_delta_for_overcharged_transportation(self, audit_system):
        """과다 청구된 Transportation의 Delta를 계산해야 함"""
        item = {
            "s_no": 5,
            "sheet_name": "TEST-005",
            "description": "TRANSPORTATION FROM KHALIFA PORT TO STORAGE YARD",
            "rate_source": "CONTRACT",
            "unit_rate": 300.00,  # 과다 청구 ($252 → $300)
            "quantity": 1,
            "total_usd": 300.00,
            "formula_text": "",
        }

        result = audit_system.validate_enhanced_item(item, [])

        assert result["ref_rate_usd"] == 252.00
        delta_pct = result["delta_pct"]
        assert delta_pct is not None
        # (300 - 252) / 252 * 100 = 19.05%
        assert 19.0 <= delta_pct <= 19.1
        assert result["cg_band"] == "CRITICAL"  # >10%
        assert result["status"] == "FAIL"

    def test_should_detect_undercharged_transportation(self, audit_system):
        """과소 청구된 Transportation을 감지해야 함"""
        item = {
            "s_no": 6,
            "sheet_name": "TEST-006",
            "description": "TRANSPORTATION FROM DSV YARD TO MIRFA",
            "rate_source": "CONTRACT",
            "unit_rate": 350.00,  # 과소 청구 ($420 → $350)
            "quantity": 1,
            "total_usd": 350.00,
            "formula_text": "",
        }

        result = audit_system.validate_enhanced_item(item, [])

        assert result["ref_rate_usd"] == 420.00
        delta_pct = result["delta_pct"]
        # (350 - 420) / 420 * 100 = -16.67%
        assert delta_pct < 0
        assert abs(delta_pct) > 10
        assert result["cg_band"] == "CRITICAL"

    # REFACTOR PHASE: 고급 시나리오 테스트
    def test_should_use_normalization_for_port_aliases(self, audit_system):
        """Port 별칭이 정규화되어 조회되어야 함"""
        item = {
            "s_no": 7,
            "sheet_name": "TEST-007",
            "description": "TRANSPORTATION FROM KP TO STORAGE YARD",  # KP = Khalifa Port
            "rate_source": "CONTRACT",
            "unit_rate": 252.00,
            "quantity": 1,
            "total_usd": 252.00,
            "formula_text": "",
        }

        result = audit_system.validate_enhanced_item(item, [])

        # KP가 Khalifa Port로 정규화되어 요율이 조회되어야 함
        assert result["ref_rate_usd"] == 252.00

    def test_should_use_normalization_for_destination_aliases(self, audit_system):
        """Destination 별칭이 정규화되어 조회되어야 함"""
        item = {
            "s_no": 8,
            "sheet_name": "TEST-008",
            "description": "TRANSPORTATION FROM STORAGE YARD TO SHU",  # SHU = SHUWEIHAT
            "rate_source": "CONTRACT",
            "unit_rate": 600.00,
            "quantity": 1,
            "total_usd": 600.00,
            "formula_text": "",
        }

        result = audit_system.validate_enhanced_item(item, [])

        # SHU가 SHUWEIHAT Site로 정규화되어 요율이 조회되어야 함
        assert result["ref_rate_usd"] == 600.00

    def test_should_apply_correct_cost_guard_band(self, audit_system):
        """올바른 COST-GUARD 밴드를 적용해야 함"""
        test_cases = [
            {"delta": 1.5, "expected_band": "PASS"},  # ≤2%
            {"delta": 3.5, "expected_band": "WARN"},  # 2-5%
            {"delta": 7.0, "expected_band": "HIGH"},  # 5-10%
            {"delta": 15.0, "expected_band": "CRITICAL"},  # >10%
        ]

        for test_case in test_cases:
            # Delta를 생성하기 위한 요율 계산
            ref_rate = 252.00
            unit_rate = ref_rate * (1 + test_case["delta"] / 100)

            item = {
                "s_no": 9,
                "sheet_name": "TEST-009",
                "description": "TRANSPORTATION FROM KHALIFA PORT TO STORAGE YARD",
                "rate_source": "CONTRACT",
                "unit_rate": round(unit_rate, 2),
                "quantity": 1,
                "total_usd": round(unit_rate, 2),
                "formula_text": "",
            }

            result = audit_system.validate_enhanced_item(item, [])

            assert (
                result["cg_band"] == test_case["expected_band"]
            ), f"Delta {test_case['delta']}% should be {test_case['expected_band']}, got {result['cg_band']}"


# Integration Test
def test_integration_with_real_data():
    """실제 9월 2025 데이터로 통합 테스트"""
    audit_system = SHPTSept2025EnhancedAuditSystem()

    # 설정 로드 확인
    config_summary = audit_system.config_manager.get_config_summary()
    print(f"\nConfiguration Summary:")
    print(f"  Lanes loaded: {config_summary['lanes_loaded']}")
    print(f"  Cost Guard bands: {config_summary['cost_guard_bands']}")
    print(f"  Contract rates: {config_summary['contract_rates']}")

    # 샘플 Contract 항목 검증
    sample_items = [
        {
            "s_no": 1,
            "sheet_name": "SCT-0126",
            "description": "TRANSPORTATION FROM KHALIFA PORT TO STORAGE YARD",
            "rate_source": "CONTRACT",
            "unit_rate": 252.00,
            "quantity": 3,
            "total_usd": 756.00,
            "formula_text": "",
        },
        {
            "s_no": 2,
            "sheet_name": "SCT-0127",
            "description": "MASTER DO FEE",
            "rate_source": "CONTRACT",
            "unit_rate": 150.00,
            "quantity": 1,
            "total_usd": 150.00,
            "formula_text": "",
        },
    ]

    validated_count = 0
    for item in sample_items:
        result = audit_system.validate_enhanced_item(item, [])
        if result.get("ref_rate_usd") is not None:
            validated_count += 1
            print(f"\n[OK] Item {item['s_no']}: {item['description']}")
            print(f"   Ref Rate: ${result['ref_rate_usd']}")
            print(f"   Delta: {result.get('delta_pct', 0)}%")
            print(f"   Status: {result['status']}")

    print(f"\n통합 테스트 결과: {validated_count}/{len(sample_items)} 항목 검증 성공")
    assert validated_count == len(sample_items), "모든 샘플 항목이 검증되어야 함"


if __name__ == "__main__":
    # pytest 실행 또는 간단한 통합 테스트
    print("\n" + "=" * 80)
    print("Contract Integration Test (TDD)")
    print("=" * 80)

    test_integration_with_real_data()

    print("\n" + "=" * 80)
    print("✅ 통합 테스트 완료")
    print("=" * 80)
    print("\npytest로 전체 테스트 실행:")
    print("  pytest test_contract_integration_tdd.py -v")
