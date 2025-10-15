#!/usr/bin/env python3
"""
Unified Rate Loader
HVDC Project - 통합 요율 데이터 로더
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class UnifiedRateLoader:
    """통합 요율 데이터 로더"""

    # COST-GUARD 밴드 정의 (SHPT 기준)
    COST_GUARD_BANDS = [
        (2.00, "PASS"),
        (5.00, "WARN"),
        (10.00, "HIGH"),
        (float("inf"), "CRITICAL"),
    ]

    # 기본 Tolerance (3%)
    DEFAULT_TOLERANCE = 0.03

    def __init__(self, rate_json_dir: Path):
        """
        초기화

        Args:
            rate_json_dir: Rate JSON 파일이 있는 디렉토리
        """
        self.rate_json_dir = Path(rate_json_dir)
        self.all_rates = {}
        self.standard_items_index = {}
        self.lane_index = {}

        # Port/Destination 정규화 맵
        self.port_normalization = {
            "khalifa port": "Khalifa Port",
            "kp": "Khalifa Port",
            "jebel ali port": "Jebel Ali Port",
            "jap": "Jebel Ali Port",
            "abu dhabi airport": "Abu Dhabi Airport",
            "auh": "Abu Dhabi Airport",
            "dubai airport": "Dubai Airport",
            "dxb": "Dubai Airport",
            "mina zayed port": "Mina Zayed Port",
            "musaffah port": "Musaffah Port",
        }

        self.destination_normalization = {
            "mirfa": "MIRFA SITE",
            "mirfa site": "MIRFA SITE",
            "mirfa pmo samsung": "MIRFA SITE",
            "shuweihat": "SHUWEIHAT Site",
            "shuweihat site": "SHUWEIHAT Site",
            "storage yard": "Storage Yard",
            "dsv yard": "Storage Yard",
            "dsv mussafah yard": "Storage Yard",
            "dsv musaffah yard": "Storage Yard",
        }

    def load_all_rates(self) -> Dict[str, List[Dict]]:
        """
        모든 Rate JSON 파일 로드

        Returns:
            {
                "air_cargo": [...],
                "bulk_cargo": [...],
                "container_cargo": [...]
            }
        """
        result = {"air_cargo": [], "bulk_cargo": [], "container_cargo": []}

        # Air cargo rates
        air_file = self.rate_json_dir / "air_cargo_rates (1).json"
        if air_file.exists():
            with open(air_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                result["air_cargo"] = data.get("records", [])

        # Bulk cargo rates
        bulk_file = self.rate_json_dir / "bulk_cargo_rates (1).json"
        if bulk_file.exists():
            with open(bulk_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                result["bulk_cargo"] = data.get("records", [])

        # Container cargo rates
        container_file = self.rate_json_dir / "container_cargo_rates (1).json"
        if container_file.exists():
            with open(container_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                result["container_cargo"] = data.get("records", [])

        self.all_rates = result

        # 인덱스 구축
        self._build_standard_items_index()
        self._build_lane_index()

        return result

    def _build_standard_items_index(self):
        """Standard Items 인덱스 구축 (DO Fee, Custom Clearance 등)"""
        self.standard_items_index = {}

        for category, records in self.all_rates.items():
            for record in records:
                description = record.get("description", "").strip()
                port = record.get("port", "").strip()

                # Rate 추출
                rate_value = self._extract_rate_value(record)
                if rate_value is None:
                    continue

                # Description + Port를 키로 사용
                key = f"{description}|{port}"

                # 중복 시 첫 번째 것만 사용
                if key not in self.standard_items_index:
                    self.standard_items_index[key] = rate_value

    def _build_lane_index(self):
        """Lane 인덱스 구축 (Inland Trucking)"""
        self.lane_index = {}

        for category, records in self.all_rates.items():
            for record in records:
                description = record.get("description", "").strip()

                # Inland Trucking만 Lane으로 취급
                if "Inland Trucking" not in description:
                    continue

                port = record.get("port", "").strip()
                destination = record.get("destination")
                unit = record.get("unit", "").strip()

                if not destination:
                    continue

                destination = destination.strip()

                # Rate 추출
                rate_value = self._extract_rate_value(record)
                if rate_value is None:
                    continue

                # Port + Destination + Unit를 키로 사용
                key = f"{port}|{destination}|{unit}"

                # 중복 시 첫 번째 것만 사용 (또는 리스트로 관리 가능)
                if key not in self.lane_index:
                    self.lane_index[key] = rate_value

    def _extract_rate_value(self, record: Dict) -> Optional[float]:
        """레코드에서 rate 값 추출"""
        # rate dict 구조
        if "rate" in record and isinstance(record["rate"], dict):
            return record["rate"].get("amount")

        # rates(usd) 문자열 (At cost 등은 None)
        if "rates(usd)" in record:
            rate_str = record["rates(usd)"]
            if isinstance(rate_str, (int, float)):
                return float(rate_str)

        return None

    def get_standard_rate(self, description: str, port: str) -> Optional[float]:
        """
        표준 항목 요율 조회

        Args:
            description: 항목 설명 (예: "DO Fee", "Custom Clearance")
            port: 포트 이름

        Returns:
            요율 (USD) 또는 None
        """
        if not self.standard_items_index:
            self.load_all_rates()

        # 정규화
        port_norm = self.normalize_port(port)

        # 정확한 매칭 시도
        key = f"{description}|{port_norm}"
        if key in self.standard_items_index:
            return self.standard_items_index[key]

        # 부분 매칭 시도 (description만)
        for indexed_key, rate in self.standard_items_index.items():
            indexed_desc, indexed_port = indexed_key.split("|", 1)
            if (
                description.lower() in indexed_desc.lower()
                and port_norm == indexed_port
            ):
                return rate

        return None

    def get_lane_rate(self, port: str, destination: str, unit: str) -> Optional[float]:
        """
        Lane 요율 조회 (Inland Trucking)

        Args:
            port: 출발 포트
            destination: 목적지
            unit: 단위 (per truck, per RT 등)

        Returns:
            요율 (USD) 또는 None
        """
        if not self.lane_index:
            self.load_all_rates()

        # 정규화
        port_norm = self.normalize_port(port)
        dest_norm = self.normalize_destination(destination)
        unit_norm = self.normalize_unit(unit)

        # 정확한 매칭
        key = f"{port_norm}|{dest_norm}|{unit_norm}"
        if key in self.lane_index:
            return self.lane_index[key]

        # 유사 매칭 (unit 없이)
        for indexed_key, rate in self.lane_index.items():
            indexed_port, indexed_dest, indexed_unit = indexed_key.split("|", 2)
            if port_norm == indexed_port and dest_norm == indexed_dest:
                # Unit이 호환되면 반환
                if self._is_unit_compatible(unit_norm, indexed_unit):
                    return rate

        return None

    def _is_unit_compatible(self, unit1: str, unit2: str) -> bool:
        """Unit 호환성 체크"""
        # 동일하면 OK
        if unit1 == unit2:
            return True

        # per truck과 per RT는 일부 상황에서 호환 가능
        truck_units = ["per truck", "per rt"]
        if unit1.lower() in truck_units and unit2.lower() in truck_units:
            return False  # 엄격하게 구분

        return False

    def calculate_delta_percent(self, draft_rate: float, ref_rate: float) -> float:
        """
        Delta % 계산

        Args:
            draft_rate: Draft invoice 요율
            ref_rate: 참조 요율

        Returns:
            Delta % (소수점 2자리)
        """
        if ref_rate == 0:
            return 0.00  # 0으로 나누기 방지

        delta = ((draft_rate - ref_rate) / ref_rate) * 100
        return round(delta, 2)

    def get_cost_guard_band(self, delta_pct: float) -> str:
        """
        COST-GUARD 밴드 결정

        Args:
            delta_pct: Delta % (절대값 사용)

        Returns:
            "PASS" | "WARN" | "HIGH" | "CRITICAL"
        """
        abs_delta = abs(delta_pct)

        for threshold, band in self.COST_GUARD_BANDS:
            if abs_delta <= threshold:
                return band

        return "CRITICAL"

    def get_tolerance(self) -> float:
        """Tolerance 값 반환 (3%)"""
        return self.DEFAULT_TOLERANCE

    def get_tolerance_range(self, ref_rate: float) -> Tuple[float, float]:
        """
        Tolerance 범위 계산

        Args:
            ref_rate: 참조 요율

        Returns:
            (min_rate, max_rate) 튜플
        """
        tolerance = self.DEFAULT_TOLERANCE
        min_rate = round(ref_rate * (1 - tolerance), 2)
        max_rate = round(ref_rate * (1 + tolerance), 2)
        return (min_rate, max_rate)

    def normalize_port(self, port: str) -> str:
        """Port 이름 정규화"""
        if not port:
            return ""

        port_lower = port.strip().lower()
        return self.port_normalization.get(port_lower, port.strip())

    def normalize_destination(self, destination: str) -> str:
        """Destination 이름 정규화"""
        if not destination:
            return ""

        dest_lower = destination.strip().lower()
        return self.destination_normalization.get(dest_lower, destination.strip())

    def normalize_unit(self, unit: str) -> str:
        """Unit 이름 정규화"""
        if not unit:
            return ""

        # 소문자로 변환 후 매핑
        unit_map = {
            "per truck": "per truck",
            "per rt": "per RT",
            "per r/t": "per RT",
            "per b/l": "per B/L",
            "per bl": "per B/L",
            "per kg": "per KG",
            "per contiainer": "per container",
            "per container": "per container",
        }

        unit_lower = unit.strip().lower()
        return unit_map.get(unit_lower, unit.strip())

    def get_all_standard_items(self) -> Dict[str, float]:
        """모든 Standard Items 반환 (디버깅/조회용)"""
        if not self.standard_items_index:
            self.load_all_rates()
        return self.standard_items_index.copy()

    def get_all_lanes(self) -> Dict[str, float]:
        """모든 Lanes 반환 (디버깅/조회용)"""
        if not self.lane_index:
            self.load_all_rates()
        return self.lane_index.copy()


# CLI 실행용
if __name__ == "__main__":
    import sys

    # Rate 디렉토리 경로
    script_dir = Path(__file__).parent
    rate_dir = script_dir.parent / "Rate"

    if not rate_dir.exists():
        print(f"[ERROR] Rate directory not found: {rate_dir}")
        sys.exit(1)

    # Loader 생성 및 테스트
    loader = UnifiedRateLoader(rate_dir)
    rates = loader.load_all_rates()

    print("=" * 80)
    print("Unified Rate Loader - Quick Test")
    print("=" * 80)
    print()

    print(f"Air Cargo Records: {len(rates['air_cargo'])}")
    print(f"Bulk Cargo Records: {len(rates['bulk_cargo'])}")
    print(f"Container Cargo Records: {len(rates['container_cargo'])}")
    print(f"Total Records: {sum(len(v) for v in rates.values())}")
    print()

    print(f"Standard Items Indexed: {len(loader.standard_items_index)}")
    print(f"Lanes Indexed: {len(loader.lane_index)}")
    print()

    # 샘플 조회
    print("=" * 80)
    print("Sample Lookups")
    print("=" * 80)
    print()

    # Standard Item 조회
    rate = loader.get_standard_rate("DO Fee", "Abu Dhabi Airport")
    print(f"DO Fee @ Abu Dhabi Airport: ${rate}")

    rate = loader.get_standard_rate("Custom Clearance", "Khalifa Port")
    print(f"Custom Clearance @ Khalifa Port: ${rate}")

    # Lane 조회
    rate = loader.get_lane_rate("Khalifa Port", "Storage Yard", "per truck")
    print(f"Khalifa Port → Storage Yard (per truck): ${rate}")

    rate = loader.get_lane_rate("Jebel Ali Port", "MIRFA SITE", "per truck")
    print(f"Jebel Ali Port → MIRFA SITE (per truck): ${rate}")
    print()

    # Delta 계산 테스트
    print("=" * 80)
    print("Delta Calculation Test")
    print("=" * 80)
    delta = loader.calculate_delta_percent(260.00, 252.00)
    band = loader.get_cost_guard_band(delta)
    print(f"Draft: $260.00, Ref: $252.00 → Delta: {delta}%, Band: {band}")
    print()
