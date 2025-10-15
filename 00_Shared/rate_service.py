#!/usr/bin/env python3
"""
Rate Service
운송 요율 탐색 통합 서비스 (중복 로직 제거)

Version: 1.0.0
Created: 2025-10-15
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import re
import pandas as pd
from typing import Optional, Dict, Tuple
from pathlib import Path


class RateService:
    """운송 요율 통합 서비스"""

    def __init__(self, config_manager, normalizer=None):
        """
        초기화

        Args:
            config_manager: ConfigurationManager instance
            normalizer: CategoryNormalizer instance (optional)
        """
        self.config_manager = config_manager
        self.normalizer = normalizer
        self.lane_map = config_manager.get_lane_map()

    def find_contract_ref_rate(
        self,
        description: str,
        row: Optional[pd.Series] = None,
        transport_mode: Optional[str] = None,
    ) -> Optional[float]:
        """
        계약 참조 요율 통합 탐색

        Priority:
            1. Config 고정요율 (DO FEE, CUSTOMS CLEARANCE, Portal Fees)
            2. 표준 키워드 매칭 (config_contract_rates.json - fixed_fees)
            3. Inland Transportation (FROM..TO 파싱 → config/lane_map)
            4. LaneMap 조회

        Args:
            description: Item description
            row: DataFrame row (optional, for additional context)
            transport_mode: Transport mode (AIR/SEA/DOMESTIC)

        Returns:
            float: Reference rate or None
        """
        if not description or pd.isna(description):
            return None

        desc_upper = str(description).upper()

        # Priority 1: 고빈도 고정 요율
        fixed_rate = self._get_fixed_fee_rate(desc_upper, transport_mode)
        if fixed_rate is not None:
            return fixed_rate

        # Priority 2: 키워드 기반 고정 요율 조회
        keyword_fee = self.config_manager.get_fixed_fee_by_keywords(description)
        if keyword_fee:
            # Transport mode 검증
            if keyword_fee.get("transport_mode"):
                if (
                    transport_mode
                    and keyword_fee["transport_mode"].upper() == transport_mode.upper()
                ):
                    return keyword_fee["rate"]
            else:
                return keyword_fee["rate"]

        # Priority 3: Inland Transportation (FROM..TO)
        if any(
            kw in desc_upper
            for kw in ["TRANSPORTATION", "TRUCKING", "INLAND", "FROM", "TO"]
        ):
            inland_rate = self._find_inland_transportation_rate(description)
            if inland_rate is not None:
                return inland_rate

        # Priority 4: General contract rate
        contract_rate = self.config_manager.get_contract_rate(description)
        if contract_rate is not None:
            return contract_rate

        return None

    def _get_fixed_fee_rate(
        self, desc_upper: str, transport_mode: Optional[str]
    ) -> Optional[float]:
        """
        고정 Fee 요율 조회 (DO FEE, CUSTOMS CLEARANCE, Portal Fees)

        Args:
            desc_upper: Uppercased description
            transport_mode: Transport mode (AIR/SEA/DOMESTIC)

        Returns:
            float: Fixed fee or None
        """
        # DO FEE
        if any(kw in desc_upper for kw in ["MASTER DO FEE", "DO FEE"]):
            return self.config_manager.get_do_fee(transport_mode or "SEA")

        # CUSTOMS CLEARANCE
        if any(
            kw in desc_upper
            for kw in ["CUSTOMS CLEARANCE", "CUSTOM CLEARANCE", "CLEARANCE FEE"]
        ):
            return self.config_manager.get_customs_clearance_fee()

        # Portal Fees
        if "APPOINTMENT FEE" in desc_upper or "TRUCK APPOINTMENT" in desc_upper:
            return self.config_manager.get_portal_fee_rate("APPOINTMENT_FEE", "USD")

        if "DPC FEE" in desc_upper:
            return self.config_manager.get_portal_fee_rate("DPC_FEE", "USD")

        if "DOCUMENT PROCESSING FEE" in desc_upper or "DOCS PROCESSING" in desc_upper:
            return self.config_manager.get_portal_fee_rate(
                "DOCUMENT_PROCESSING_FEE", "USD"
            )

        return None

    def _find_inland_transportation_rate(self, description: str) -> Optional[float]:
        """
        Inland Transportation 요율 탐색

        Args:
            description: Item description

        Returns:
            float: Transportation rate or None
        """
        # Parse FROM..TO
        port, destination = self._parse_transportation_route(description)
        if not port or not destination:
            return None

        # Priority 1: Inland transportation config
        inland_rate = self.config_manager.get_inland_transportation_rate(
            port, destination
        )
        if inland_rate is not None:
            return inland_rate

        # Priority 2: Lane map
        lane_rate = self.config_manager.get_lane_rate(port, destination, "per truck")
        if lane_rate is not None:
            return lane_rate

        return None

    def _parse_transportation_route(
        self, description: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Transportation route 파싱 (FROM origin TO destination)

        Args:
            description: Item description

        Returns:
            tuple: (port/origin, destination) or (None, None)

        Examples:
            "TRANSPORTATION FROM KHALIFA PORT TO DSV YARD" -> ("KHALIFA PORT", "DSV YARD")
            "TRUCKING CHARGES - AUH AIRPORT → MOSB" -> ("AUH AIRPORT", "MOSB")
        """
        if not description:
            return None, None

        desc_upper = str(description).upper()

        # Pattern 1: FROM ... TO ...
        from_to_pattern = r"FROM\s+(.+?)\s+TO\s+(.+?)(?:\s|$|\(|\))"
        match = re.search(from_to_pattern, desc_upper)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            return self._normalize_location(origin), self._normalize_location(
                destination
            )

        # Pattern 2: 화살표 (→, ↔, ->)
        arrow_pattern = r"(.+?)\s*(?:→|↔|->|TO)\s*(.+?)(?:\s|$|\(|\))"
        match = re.search(arrow_pattern, desc_upper)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            # FROM 키워드 제거
            origin = re.sub(
                r"^(FROM|TRANSPORTATION|TRUCKING|CHARGES?|FEE)\s+", "", origin
            ).strip()
            return self._normalize_location(origin), self._normalize_location(
                destination
            )

        return None, None

    def _normalize_location(self, location: str) -> str:
        """
        Location 표준화

        Args:
            location: Location name

        Returns:
            str: Normalized location

        Examples:
            "AUH AIRPORT" -> "Abu Dhabi Airport"
            "DSV YARD" -> "DSV Mussafah Yard"
        """
        if not location:
            return location

        # 표준 별칭 매핑
        aliases = {
            "AUH AIRPORT": "Abu Dhabi Airport",
            "ABU DHABI AIRPORT": "Abu Dhabi Airport",
            "DXB AIRPORT": "Dubai Airport",
            "DUBAI AIRPORT": "Dubai Airport",
            "KHALIFA PORT": "Khalifa Port",
            "KP": "Khalifa Port",
            "DSV YARD": "DSV Mussafah Yard",
            "DSV MUSSAFAH": "DSV Mussafah Yard",
            "MUSSAFAH YARD": "DSV Mussafah Yard",
            "MOSB": "MOSB",
            "MIRFA": "MIRFA",
            "SHUWEIHAT": "SHUWEIHAT",
            "STORAGE": "DSV Mussafah Yard",
        }

        location_upper = location.upper().strip()

        # 직접 매칭
        if location_upper in aliases:
            return aliases[location_upper]

        # 부분 매칭
        for key, value in aliases.items():
            if key in location_upper:
                return value

        return location

    def get_lane_rate(
        self, origin: str, destination: str, unit: str = "per truck"
    ) -> Optional[float]:
        """
        Lane map에서 요율 조회 (간편 래퍼)

        Args:
            origin: Origin location
            destination: Destination location
            unit: Rate unit

        Returns:
            float: Lane rate or None
        """
        return self.config_manager.get_lane_rate(origin, destination, unit)
