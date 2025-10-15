#!/usr/bin/env python3
"""
Configuration Manager for HVDC Invoice Audit System
외부 JSON 설정 파일 로드 및 관리

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ConfigurationManager:
    """통합 설정 관리자"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        초기화

        Args:
            config_dir: 설정 파일 디렉토리 (기본: Rate 폴더)
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent / "Rate"
        else:
            self.config_dir = Path(config_dir)

        # 설정 데이터 캐시
        self.lane_config = {}
        self.cost_guard_config = {}
        self.contract_rates_config = {}
        self.validation_rules_config = {}
        self.anomaly_config = {}

        # 로드 상태
        self.is_loaded = False

    def load_all_configs(self):
        """모든 설정 파일 로드"""
        logger.info(f"Loading configurations from: {self.config_dir}")

        self.lane_config = self._load_json_config("config_shpt_lanes.json")
        self.cost_guard_config = self._load_json_config("config_cost_guard_bands.json")
        self.contract_rates_config = self._load_json_config(
            "config_contract_rates.json"
        )
        self.validation_rules_config = self._load_json_config(
            "config_validation_rules.json"
        )
        self.anomaly_config = self.lane_config.get("anomaly_detection", {})

        self.is_loaded = True
        logger.info("All configurations loaded successfully")

    def _load_json_config(self, filename: str) -> Dict[str, Any]:
        """JSON 설정 파일 로드"""
        file_path = self.config_dir / filename

        if not file_path.exists():
            logger.warning(f"Config file not found: {filename}")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"Loaded: {filename}")
            return config
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return {}

    def get_lane_map(self) -> Dict[str, Dict[str, Any]]:
        """Lane Map 조회 (해상 + 항공 통합)"""
        if not self.is_loaded:
            self.load_all_configs()

        lane_map = {}

        # 해상 운송
        if "sea_transport" in self.lane_config:
            lane_map.update(self.lane_config["sea_transport"])

        # 항공 운송
        if "air_transport" in self.lane_config:
            lane_map.update(self.lane_config["air_transport"])

        return lane_map

    def get_normalization_aliases(self) -> Dict[str, Dict[str, str]]:
        """정규화 별칭 조회"""
        if not self.is_loaded:
            self.load_all_configs()

        return self.lane_config.get(
            "normalization_aliases", {"ports": {}, "destinations": {}}
        )

    def get_cost_guard_bands(self) -> Dict[str, float]:
        """
        COST-GUARD 밴드 설정 조회 (간소화된 형식)

        Returns:
            dict: {"pass": 3.0, "warn": 5.0, "high": 10.0, "autofail": 15.0}
        """
        if not self.is_loaded:
            self.load_all_configs()

        # 새 형식 (pass/warn/high/autofail) 우선 반환
        simple_bands = self.cost_guard_config.get("cost_guard_bands", {})
        if simple_bands and "pass" in simple_bands:
            return simple_bands

        # Fallback: 상세 형식에서 추출
        detailed_bands = self.cost_guard_config.get("cost_guard_bands_detailed", {})
        if detailed_bands:
            return {
                "pass": detailed_bands.get("PASS", {}).get("max_delta", 3.0),
                "warn": detailed_bands.get("WARN", {}).get("max_delta", 5.0),
                "high": detailed_bands.get("HIGH", {}).get("max_delta", 10.0),
                "autofail": detailed_bands.get("CRITICAL", {}).get("max_delta", 15.0),
            }

        # Default values
        return {"pass": 3.0, "warn": 5.0, "high": 10.0, "autofail": 15.0}

    def get_special_tolerance(self, charge_type: str) -> Optional[float]:
        """특별 허용 오차 조회"""
        if not self.is_loaded:
            self.load_all_configs()

        special_tolerances = self.cost_guard_config.get("special_tolerances", {})

        if charge_type in special_tolerances:
            return special_tolerances[charge_type].get("max_delta")

        # 기본 허용 오차
        validation_rules = self.validation_rules_config.get("tolerance_rules", {})
        return validation_rules.get("default", {}).get("percent", 3.0)

    def get_contract_rate(self, charge_name: str) -> Optional[float]:
        """계약 요율 조회"""
        if not self.is_loaded:
            self.load_all_configs()

        fixed_fees = self.contract_rates_config.get("fixed_fees", {})

        # 정규화된 키 생성
        normalized_key = charge_name.upper().replace(" ", "_")

        for key, fee_info in fixed_fees.items():
            if key == normalized_key or charge_name.upper() in key:
                return fee_info.get("rate")

        return None

    def get_do_fee(self, transport_mode: str) -> Optional[float]:
        """DO FEE 조회 (AIR/CONTAINER 구분)"""
        if not self.is_loaded:
            self.load_all_configs()

        mode_upper = str(transport_mode).upper()
        fixed_fees = self.contract_rates_config.get("fixed_fees", {})

        if "AIR" in mode_upper or "HE" in mode_upper:
            fee_config = fixed_fees.get("DO_FEE_AIR", {})
            return fee_config.get("rate")
        else:  # CONTAINER or Default
            fee_config = fixed_fees.get("DO_FEE_CONTAINER", {})
            return fee_config.get("rate")

    def get_customs_clearance_fee(self) -> float:
        """CUSTOMS CLEARANCE FEE 조회"""
        if not self.is_loaded:
            self.load_all_configs()

        fixed_fees = self.contract_rates_config.get("fixed_fees", {})
        fee_config = fixed_fees.get("CUSTOMS_CLEARANCE_FEE", {})
        return fee_config.get("rate", 150.00)

    def get_fixed_fee_by_keywords(self, description: str) -> Optional[Dict]:
        """키워드 기반 고정 요율 조회"""
        if not self.is_loaded:
            self.load_all_configs()

        desc_upper = str(description).upper()
        fixed_fees = self.contract_rates_config.get("fixed_fees", {})

        for fee_name, fee_config in fixed_fees.items():
            keywords = fee_config.get("keywords", [])
            if keywords and any(str(kw).upper() in desc_upper for kw in keywords):
                return {
                    "name": fee_name,
                    "rate": fee_config.get("rate"),
                    "category": fee_config.get("category"),
                    "transport_mode": fee_config.get("transport_mode"),
                }

        return None

    def get_portal_fee_rate(
        self, fee_name: str, currency: str = "USD"
    ) -> Optional[float]:
        """Portal Fee 요율 조회"""
        if not self.is_loaded:
            self.load_all_configs()

        portal_fees = self.contract_rates_config.get("portal_fees_aed", {})

        # 정규화된 키 생성
        normalized_key = fee_name.upper().replace(" ", "_")

        for key, fee_info in portal_fees.items():
            if normalized_key in key or fee_name.upper() in key:
                if currency == "USD":
                    return fee_info.get("rate_usd")
                elif currency == "AED":
                    return fee_info.get("rate_aed")

        return None

    def get_fx_rate(
        self, from_currency: str = "USD", to_currency: str = "AED"
    ) -> float:
        """환율 조회"""
        if not self.is_loaded:
            self.load_all_configs()

        fx_rates = self.cost_guard_config.get("fx_rates", {})

        if from_currency == "USD" and to_currency == "AED":
            return fx_rates.get("USD_AED", 3.6725)
        elif from_currency == "AED" and to_currency == "USD":
            return 1.0 / fx_rates.get("USD_AED", 3.6725)

        return 1.0

    def get_lane_rate(
        self, port: str, destination: str, unit: str = "per truck"
    ) -> Optional[float]:
        """Lane 요율 조회"""
        if not self.is_loaded:
            self.load_all_configs()

        lane_map = self.get_lane_map()

        # 직접 매칭
        lane_key = f"{port}_{destination}".replace(" ", "_").upper()

        if lane_key in lane_map:
            return lane_map[lane_key].get("rate")

        # 정규화 후 재시도
        aliases = self.get_normalization_aliases()

        normalized_port = port
        for alias, canonical in aliases.get("ports", {}).items():
            if alias.upper() in port.upper():
                normalized_port = canonical
                break

        normalized_dest = destination
        for alias, canonical in aliases.get("destinations", {}).items():
            if alias.upper() in destination.upper():
                normalized_dest = canonical
                break

        lane_key = f"{normalized_port}_{normalized_dest}".replace(" ", "_").upper()

        if lane_key in lane_map:
            return lane_map[lane_key].get("rate")

        # Lane Map 순회하며 매칭
        for lane_id, lane_info in lane_map.items():
            if (
                lane_info.get("port", "").upper() in port.upper()
                or port.upper() in lane_info.get("port", "").upper()
            ) and (
                lane_info.get("destination", "").upper() in destination.upper()
                or destination.upper() in lane_info.get("destination", "").upper()
            ):
                if lane_info.get("unit") == unit:
                    return lane_info.get("rate")

        return None

    def get_lane_metadata(
        self, port: str, destination: str, unit: str = "per truck"
    ) -> Optional[Dict[str, Any]]:
        """Lane 메타데이터 조회 / Retrieve lane metadata."""

        if not self.is_loaded:
            self.load_all_configs()

        lane_map = self.get_lane_map()
        lane_key = f"{port}_{destination}".replace(" ", "_").upper()

        if lane_key in lane_map:
            metadata = dict(lane_map[lane_key])
            metadata["lane_key"] = lane_key
            return metadata

        aliases = self.get_normalization_aliases()
        normalized_port = port
        for alias, canonical in aliases.get("ports", {}).items():
            if alias.upper() in port.upper():
                normalized_port = canonical
                break

        normalized_dest = destination
        for alias, canonical in aliases.get("destinations", {}).items():
            if alias.upper() in destination.upper():
                normalized_dest = canonical
                break

        lane_key = f"{normalized_port}_{normalized_dest}".replace(" ", "_").upper()
        if lane_key in lane_map:
            metadata = dict(lane_map[lane_key])
            metadata["lane_key"] = lane_key
            return metadata

        for lane_name, lane_info in lane_map.items():
            port_name = lane_info.get("port", "")
            dest_name = lane_info.get("destination", "")
            if (
                port_name.upper() in port.upper() or port.upper() in port_name.upper()
            ) and (
                dest_name.upper() in destination.upper()
                or destination.upper() in dest_name.upper()
            ):
                if lane_info.get("unit") == unit:
                    metadata = dict(lane_info)
                    metadata["lane_key"] = lane_name
                    return metadata

        return None

    def get_anomaly_detection_config(
        self, lane_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """이상 탐지 설정 조회 / Retrieve anomaly detection configuration."""

        if not self.is_loaded:
            self.load_all_configs()

        config = dict(self.anomaly_config)
        overrides = config.get("lane_overrides", {})

        if lane_id and lane_id in overrides:
            lane_override = overrides[lane_id]
            merged = dict(config)
            merged.update({k: v for k, v in lane_override.items() if k != "risk_thresholds"})
            if "risk_thresholds" in lane_override:
                merged.setdefault("risk_thresholds", {})
                base_thresholds = dict(config.get("risk_thresholds", {}))
                base_thresholds.update(lane_override["risk_thresholds"])
                merged["risk_thresholds"] = base_thresholds
            config = merged

        return config

    def get_inland_transportation_rate(
        self, origin: str, destination: str
    ) -> Optional[float]:
        """
        Inland Transportation 요율 조회

        Args:
            origin: 출발지 (예: "AIRPORT", "AUH AIRPORT")
            destination: 목적지 (예: "MOSB", "MIRFA+SHUWEIHAT")

        Returns:
            rate_usd (float) or None
        """
        if not self.is_loaded:
            self.load_all_configs()

        inland_transport = self.contract_rates_config.get("inland_transportation", {})

        # Normalize inputs
        origin_norm = origin.upper().strip()
        dest_norm = destination.upper().strip().replace(" ", "")

        # Exact match first
        for route_key, route_info in inland_transport.items():
            route_origin = route_info.get("origin", "").upper().replace(" ", "")
            route_dest = route_info.get("destination", "").upper().replace(" ", "")

            if origin_norm in route_origin and dest_norm in route_dest:
                logger.info(
                    f"[TRANSPORT] Found rate for {origin} → {destination}: ${route_info['rate_usd']}"
                )
                return route_info.get("rate_usd")

        # Keyword matching
        for route_key, route_info in inland_transport.items():
            keywords = [kw.upper() for kw in route_info.get("keywords", [])]
            desc = route_info.get("description", "").upper()

            # Check if all major keywords are present
            if any(
                kw in origin_norm
                for kw in keywords
                if "AIRPORT" in kw or "FB" not in kw
            ):
                if any(
                    kw in dest_norm
                    for kw in keywords
                    if kw not in ["AIRPORT", "1", "FB", "FLATBED"]
                ):
                    logger.info(
                        f"[TRANSPORT] Keyword match for {origin} → {destination}: ${route_info['rate_usd']}"
                    )
                    return route_info.get("rate_usd")

        logger.warning(f"[TRANSPORT] No rate found for {origin} → {destination}")
        return None

    def reload_configs(self):
        """설정 파일 재로드"""
        logger.info("Reloading all configurations...")
        self.is_loaded = False
        self.load_all_configs()

    def get_validation_rule(self, rule_name: str) -> Any:
        """검증 규칙 조회"""
        if not self.is_loaded:
            self.load_all_configs()

        return self.validation_rules_config.get(rule_name)

    def get_gate_rule(self, gate_name: str) -> Optional[Dict[str, Any]]:
        """Gate 검증 규칙 조회"""
        if not self.is_loaded:
            self.load_all_configs()

        gate_rules = self.validation_rules_config.get("gate_validation_rules", {})
        return gate_rules.get(gate_name)

    def get_risk_based_review_config(self) -> Dict[str, Any]:
        """Risk-based review 설정 조회"""
        if not self.is_loaded:
            self.load_all_configs()

        default_config = {
            "enabled": False,
            "trigger_threshold": 0.8,
            "score_formula": {
                "delta_weight": 0.4,
                "anomaly_weight": 0.3,
                "cert_weight": 0.2,
                "signature_weight": 0.1,
            },
        }

        config = self.validation_rules_config.get("risk_based_review", {})
        merged = default_config.copy()

        merged["enabled"] = bool(config.get("enabled", merged["enabled"]))
        merged["trigger_threshold"] = float(
            config.get("trigger_threshold", merged["trigger_threshold"])
        )

        score_formula = default_config["score_formula"].copy()
        score_formula.update(config.get("score_formula", {}))
        merged["score_formula"] = score_formula

        return merged

    def get_config_summary(self) -> Dict[str, Any]:
        """설정 요약 정보"""
        if not self.is_loaded:
            self.load_all_configs()

        lane_map = self.get_lane_map()

        return {
            "lanes_loaded": len(lane_map),
            "cost_guard_bands": len(self.get_cost_guard_bands()),
            "contract_rates": len(self.contract_rates_config.get("fixed_fees", {})),
            "portal_fees": len(self.contract_rates_config.get("portal_fees_aed", {})),
            "anomaly_detection_enabled": bool(self.anomaly_config.get("enabled", False)),
            "config_files_loaded": sum(
                [
                    bool(self.lane_config),
                    bool(self.cost_guard_config),
                    bool(self.contract_rates_config),
                    bool(self.validation_rules_config),
                ]
            ),
            "config_directory": str(self.config_dir),
        }


# Singleton instance
_config_manager_instance = None


def get_config_manager(config_dir: Optional[Path] = None) -> ConfigurationManager:
    """ConfigurationManager 싱글톤 인스턴스 반환"""
    global _config_manager_instance

    if _config_manager_instance is None:
        _config_manager_instance = ConfigurationManager(config_dir)
        _config_manager_instance.load_all_configs()

    return _config_manager_instance


# 테스트 실행
if __name__ == "__main__":
    manager = ConfigurationManager()
    manager.load_all_configs()

    print("\n" + "=" * 80)
    print("Configuration Manager 테스트")
    print("=" * 80)

    summary = manager.get_config_summary()
    print(f"\n설정 파일 로드: {summary['config_files_loaded']}/4")
    print(f"Lane 수: {summary['lanes_loaded']}개")
    print(f"COST-GUARD 밴드: {summary['cost_guard_bands']}개")
    print(f"Contract 요율: {summary['contract_rates']}개")
    print(f"Portal Fee: {summary['portal_fees']}개")

    # 샘플 조회
    print(f"\nLane Map 조회 테스트:")
    rate = manager.get_lane_rate("Khalifa Port", "Storage Yard")
    print(f"  Khalifa Port → Storage Yard: ${rate}")

    print(f"\nContract 요율 조회:")
    master_do = manager.get_contract_rate("MASTER DO FEE")
    print(f"  Master DO Fee: ${master_do}")

    print(f"\nPortal Fee 조회:")
    appointment = manager.get_portal_fee_rate("APPOINTMENT FEE")
    print(f"  Appointment Fee (USD): ${appointment}")

    print(f"\n환율 조회:")
    fx = manager.get_fx_rate("USD", "AED")
    print(f"  1 USD = {fx} AED")
