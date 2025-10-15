#!/usr/bin/env python3
"""
Contract Validation 테스트 (TDD - Red Phase)
Enhanced 시스템의 Contract 항목 검증 기능 테스트
"""

import pytest
import sys
from pathlib import Path

# 상위 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
sys.path.insert(0, str(Path(__file__).parent))

from shpt_sept_2025_enhanced_audit import SHPTSept2025EnhancedAuditSystem
from rate_loader import UnifiedRateLoader


class TestContractValidation:
    """Contract 항목 검증 테스트"""

    @pytest.fixture
    def audit_system(self):
        """Audit system fixture"""
        system = SHPTSept2025EnhancedAuditSystem()
        # Rate loader 주입
        rate_dir = Path(__file__).parent.parent.parent / "Rate"
        system.rate_loader = UnifiedRateLoader(rate_dir)
        system.rate_loader.load_all_rates()
        return system

    def test_should_classify_contract_item(self, audit_system):
        """Contract 항목을 올바르게 분류해야 함"""
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

    def test_should_find_ref_rate_for_standard_contract_item(self, audit_system):
        """표준 Contract 항목의 ref_rate를 찾아야 함"""
        # MASTER DO FEE
        item = {
            "s_no": 1,
            "sheet_name": "TEST-001",
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
        assert result["cg_band"] == "PASS"

    def test_should_calculate_delta_for_overcharged_contract(self, audit_system):
        """과다 청구된 Contract 항목의 Delta를 계산해야 함"""
        # MASTER DO FEE를 $160으로 과다 청구
        item = {
            "s_no": 1,
            "sheet_name": "TEST-001",
            "description": "MASTER DO FEE",
            "rate_source": "CONTRACT",
            "unit_rate": 160.00,  # 과다 청구 ($150 → $160)
            "quantity": 1,
            "total_usd": 160.00,
            "formula_text": "",
        }

        result = audit_system.validate_enhanced_item(item, [])

        assert result["ref_rate_usd"] == 150.00
        assert result["delta_pct"] == pytest.approx(6.67, abs=0.1)  # (160-150)/150*100
        assert result["cg_band"] == "HIGH"  # >5%
        assert result["status"] == "FAIL" or result["status"] == "REVIEW_NEEDED"

    def test_should_find_ref_rate_for_transportation_contract(self, audit_system):
        """Transportation Contract 항목의 ref_rate를 찾아야 함"""
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

        # Lane Map에서 찾아야 함
        assert result["ref_rate_usd"] is not None
        assert result["ref_rate_usd"] == 252.00
        assert result["delta_pct"] == 0.0
        assert result["cg_band"] == "PASS"

    def test_should_handle_customs_clearance_contract(self, audit_system):
        """Customs Clearance Contract 항목 처리"""
        item = {
            "s_no": 1,
            "sheet_name": "TEST-001",
            "description": "CUSTOMS CLEARANCE FEE",
            "rate_source": "CONTRACT",
            "unit_rate": 150.00,
            "quantity": 1,
            "total_usd": 150.00,
            "formula_text": "",
        }

        result = audit_system.validate_enhanced_item(item, [])

        assert result["ref_rate_usd"] == 150.00
        assert result["delta_pct"] == 0.0

    def test_should_return_none_for_unknown_contract_item(self, audit_system):
        """알 수 없는 Contract 항목은 ref_rate None 반환"""
        item = {
            "s_no": 1,
            "sheet_name": "TEST-001",
            "description": "PORT CONTAINER REPAIR",  # 특수 항목
            "rate_source": "CONTRACT",
            "unit_rate": 500.00,
            "quantity": 1,
            "total_usd": 500.00,
            "formula_text": "",
        }

        result = audit_system.validate_enhanced_item(item, [])

        # ref_rate를 찾지 못하면 None
        assert result["ref_rate_usd"] is None
        assert result["delta_pct"] == 0.0  # ref 없으면 delta 계산 안 함


if __name__ == "__main__":
    # pytest 실행
    pytest.main([__file__, "-v", "--tb=short"])
