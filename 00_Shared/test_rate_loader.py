#!/usr/bin/env python3
"""
UnifiedRateLoader 테스트 (TDD - Red Phase)
HVDC Project - Rate Data Integration
"""

import pytest
from pathlib import Path
import sys

# 상대 경로에서 rate_loader import
sys.path.insert(0, str(Path(__file__).parent))

from rate_loader import UnifiedRateLoader


class TestUnifiedRateLoader:
    """UnifiedRateLoader 기본 기능 테스트"""

    @pytest.fixture
    def rate_loader(self):
        """Rate loader fixture"""
        rate_dir = Path(__file__).parent.parent / "Rate"
        return UnifiedRateLoader(rate_dir)

    # ========== Basic Loading Tests ==========

    def test_should_load_all_json_files(self, rate_loader):
        """모든 JSON 파일을 로드해야 함"""
        result = rate_loader.load_all_rates()

        assert result is not None
        assert "air_cargo" in result
        assert "bulk_cargo" in result
        assert "container_cargo" in result

        # 최소 레코드 수 확인
        total_records = (
            len(result["air_cargo"])
            + len(result["bulk_cargo"])
            + len(result["container_cargo"])
        )
        assert total_records >= 190  # 196개 예상 (일부 invalid 제외)

    def test_should_find_standard_item_by_description(self, rate_loader):
        """Description으로 표준 항목 요율을 찾아야 함"""
        # DO Fee - Abu Dhabi Airport
        rate = rate_loader.get_standard_rate("DO Fee", "Abu Dhabi Airport")
        assert rate == 80.00

        # DO Fee - Dubai Airport (다른 공항)
        rate = rate_loader.get_standard_rate("DO Fee", "Dubai Airport")
        assert rate == 150.00

        # Custom Clearance - Khalifa Port
        rate = rate_loader.get_standard_rate("Custom Clearance", "Khalifa Port")
        assert rate == 150.00

        # Port Handling Charge는 cargo type에 따라 다름
        # 조회 결과가 존재하는지만 확인
        rate = rate_loader.get_standard_rate("Port Handling Charge", "Khalifa Port")
        assert rate is not None
        assert rate > 0

    def test_should_find_lane_by_port_and_destination(self, rate_loader):
        """Port와 Destination으로 Inland Trucking 요율을 찾아야 함"""
        # Khalifa Port → Storage Yard
        rate = rate_loader.get_lane_rate("Khalifa Port", "Storage Yard", "per truck")
        assert rate == 252.00

        # Jebel Ali Port → MIRFA SITE (Container, per truck)
        rate = rate_loader.get_lane_rate("Jebel Ali Port", "MIRFA SITE", "per truck")
        assert rate == 770.00  # 20FT or 40FT

    def test_should_return_none_for_missing_rate(self, rate_loader):
        """존재하지 않는 요율은 None을 반환해야 함"""
        rate = rate_loader.get_standard_rate("NONEXISTENT ITEM", "Some Port")
        assert rate is None

        rate = rate_loader.get_lane_rate("NONEXISTENT PORT", "SOME DEST", "per truck")
        assert rate is None

    def test_should_apply_tolerance_correctly(self, rate_loader):
        """Tolerance를 올바르게 적용해야 함"""
        # Tolerance 3% 확인
        tolerance = rate_loader.get_tolerance()
        assert tolerance == 0.03

        # Tolerance 범위 계산
        ref_rate = 100.00
        min_rate, max_rate = rate_loader.get_tolerance_range(ref_rate)
        assert min_rate == 97.00  # 100 * (1 - 0.03)
        assert max_rate == 103.00  # 100 * (1 + 0.03)

    # ========== Delta Calculation Tests ==========

    def test_should_calculate_delta_percent_positive(self, rate_loader):
        """양의 Delta % 계산"""
        delta = rate_loader.calculate_delta_percent(105.00, 100.00)
        assert delta == 5.00  # (105 - 100) / 100 * 100

    def test_should_calculate_delta_percent_negative(self, rate_loader):
        """음의 Delta % 계산"""
        delta = rate_loader.calculate_delta_percent(95.00, 100.00)
        assert delta == -5.00  # (95 - 100) / 100 * 100

    def test_should_calculate_delta_percent_zero(self, rate_loader):
        """Delta % 0 계산"""
        delta = rate_loader.calculate_delta_percent(100.00, 100.00)
        assert delta == 0.00

    def test_should_handle_zero_reference_rate(self, rate_loader):
        """참조 요율이 0일 때 처리"""
        delta = rate_loader.calculate_delta_percent(100.00, 0.00)
        assert delta == 0.00 or delta is None  # 0으로 나누기 방지

    # ========== COST-GUARD Band Tests ==========

    def test_should_return_pass_band_for_small_delta(self, rate_loader):
        """작은 Delta는 PASS 밴드"""
        band = rate_loader.get_cost_guard_band(1.5)
        assert band == "PASS"

        band = rate_loader.get_cost_guard_band(-1.5)
        assert band == "PASS"

    def test_should_return_warn_band_for_medium_delta(self, rate_loader):
        """중간 Delta는 WARN 밴드"""
        band = rate_loader.get_cost_guard_band(3.5)
        assert band == "WARN"

        band = rate_loader.get_cost_guard_band(-4.0)
        assert band == "WARN"

    def test_should_return_high_band_for_large_delta(self, rate_loader):
        """큰 Delta는 HIGH 밴드"""
        band = rate_loader.get_cost_guard_band(7.5)
        assert band == "HIGH"

    def test_should_return_critical_band_for_huge_delta(self, rate_loader):
        """매우 큰 Delta는 CRITICAL 밴드"""
        band = rate_loader.get_cost_guard_band(15.0)
        assert band == "CRITICAL"

    # ========== Normalization Tests ==========

    def test_should_normalize_port_names(self, rate_loader):
        """Port 이름 정규화"""
        # Khalifa Port 변형들
        assert rate_loader.normalize_port("Khalifa Port") == "Khalifa Port"
        assert rate_loader.normalize_port("khalifa port") == "Khalifa Port"
        assert rate_loader.normalize_port("KP") == "Khalifa Port"

    def test_should_normalize_destination_names(self, rate_loader):
        """Destination 이름 정규화"""
        # MIRFA 변형들
        assert rate_loader.normalize_destination("MIRFA SITE") == "MIRFA SITE"
        assert rate_loader.normalize_destination("Mirfa") == "MIRFA SITE"
        assert rate_loader.normalize_destination("MIRFA PMO SAMSUNG") == "MIRFA SITE"

    def test_should_normalize_unit_names(self, rate_loader):
        """Unit 이름 정규화"""
        assert rate_loader.normalize_unit("per truck") == "per truck"
        assert rate_loader.normalize_unit("per RT") == "per RT"
        assert rate_loader.normalize_unit("per B/L") == "per B/L"


if __name__ == "__main__":
    # pytest 실행
    pytest.main([__file__, "-v", "--tb=short"])
