"""이상 탐지 테스트 / Tests for anomaly detection integration."""

from __future__ import annotations

from typing import Dict, List

import pytest

import sys
from pathlib import Path

pytest.importorskip("pandas")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "00_Shared"))
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "01_DSV_SHPT" / "Core_Systems"))

from anomaly_detection import AnomalyDetectionService
from shipment_audit_engine import ShipmentAuditEngine


@pytest.fixture(name="audit_engine")
def fixture_audit_engine() -> ShipmentAuditEngine:
    """감사 엔진 픽스처 / Provide a configured audit engine."""

    engine = ShipmentAuditEngine()
    base_config = engine.config_manager.get_anomaly_detection_config()
    engine.anomaly_base_config = base_config
    engine.anomaly_detectors = {None: engine._create_anomaly_detector(base_config)}
    engine.anomaly_disabled_lanes = set()
    return engine


def build_transport_item(
    s_no: int,
    unit_rate: float,
    description: str,
    quantity: float = 1.0,
) -> Dict[str, object]:
    """운송 항목 생성 / Build transport invoice item."""

    return {
        "s_no": s_no,
        "sheet_name": "SCT0100",
        "description": description,
        "rate_source": "CONTRACT",
        "unit_rate": unit_rate,
        "quantity": quantity,
        "total_usd": round(unit_rate * quantity, 2),
        "formula_text": "",
        "remark": "",
    }


def test_anomaly_service_flags_high_risk() -> None:
    """Robust Z-score 모델의 고위험 감지 확인 / Ensure high risk flagged."""

    config = {
        "enabled": True,
        "model": {"type": "robust_zscore", "params": {"default_spread": 0.05}},
        "risk_thresholds": {"low": 1.0, "medium": 2.0, "high": 3.0},
    }
    service = AnomalyDetectionService(config)
    features = {"unit_rate": 400.0, "lane_rate": 200.0}

    result = service.score_item(features)

    assert result.flagged is True
    assert result.risk_level in {"HIGH", "MEDIUM"}
    assert result.score >= 4.0


def test_validate_enhanced_item_normal_pass(audit_engine: ShipmentAuditEngine) -> None:
    """정상 운송 항목은 PASS 유지 / Typical lane stays PASS."""

    item = build_transport_item(
        1,
        252.0,
        "TRANSPORTATION FROM KHALIFA PORT TO STORAGE YARD",
    )
    validation = audit_engine.validate_enhanced_item(item, [])

    anomaly = validation.get("anomaly_detection", {})
    assert anomaly.get("flagged") is False
    assert validation["status"] == "PASS"
    assert "Anomaly detection" not in "|".join(validation["issues"])


def test_validate_enhanced_item_anomaly_flag(audit_engine: ShipmentAuditEngine) -> None:
    """이상 요율은 FAIL 처리 / Abnormal rate escalates to FAIL."""

    item = build_transport_item(
        2,
        520.0,
        "TRANSPORTATION FROM KHALIFA PORT TO STORAGE YARD",
    )
    validation = audit_engine.validate_enhanced_item(item, [])

    anomaly = validation.get("anomaly_detection", {})
    assert anomaly.get("flagged") is True
    assert anomaly.get("risk_level") == "HIGH"
    assert validation["status"] == "FAIL"
    assert any("Anomaly detection" in issue for issue in validation["issues"])


def test_lane_toggle_disables_detection(audit_engine: ShipmentAuditEngine) -> None:
    """Lane 비활성화시 이상 탐지 비활성 / Lane override disables detector."""

    item = build_transport_item(
        3,
        100.0,
        "TRANSPORTATION FROM ABU DHABI AIRPORT TO DSV MUSSAFAH YARD",
    )
    validation = audit_engine.validate_enhanced_item(item, [])

    anomaly = validation.get("anomaly_detection", {})
    assert anomaly.get("enabled", True) is False
    assert anomaly.get("details", {}).get("reason") == "lane_disabled"
    assert validation["status"] == "PASS"


def test_anomaly_summary_batch(audit_engine: ShipmentAuditEngine) -> None:
    """배치 요약 산출 검증 / Validate batch summary aggregation."""

    items: List[Dict[str, object]] = [
        build_transport_item(10, 252.0, "TRANSPORTATION FROM KHALIFA PORT TO STORAGE YARD"),
        build_transport_item(11, 520.0, "TRANSPORTATION FROM KHALIFA PORT TO STORAGE YARD"),
    ]
    results = [audit_engine.validate_enhanced_item(item, []) for item in items]

    summary = audit_engine._summarize_anomalies(results)

    assert summary["total_scored"] >= 2
    assert summary["flagged_items"] >= 1
    assert summary["average_score"] >= 0.0
