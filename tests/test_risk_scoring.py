import sys
import types
from pathlib import Path

import pytest

if "pandas" not in sys.modules:
    pandas_stub = types.ModuleType("pandas")

    def _unsupported(*_args, **_kwargs):
        raise RuntimeError("pandas stub does not support this operation")

    pandas_stub.read_excel = _unsupported
    pandas_stub.ExcelFile = _unsupported
    pandas_stub.notna = lambda value: value is not None
    pandas_stub.DataFrame = object
    pandas_stub.Series = object
    sys.modules["pandas"] = pandas_stub

ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT_DIR / "01_DSV_SHPT" / "Core_Systems"
SHARED_PATH = ROOT_DIR / "00_Shared"

sys.path.insert(0, str(CORE_PATH))
sys.path.insert(0, str(SHARED_PATH))

from anomaly_detection_service import AnomalyDetectionService
from shipment_audit_engine import ShipmentAuditEngine


def test_risk_score_weight_sensitivity():
    base_service = AnomalyDetectionService(
        weights={
            "delta_weight": 0.4,
            "anomaly_weight": 0.3,
            "cert_weight": 0.2,
            "signature_weight": 0.1,
        },
        trigger_threshold=0.8,
        autofail_threshold=15.0,
    )
    baseline = base_service.compute_risk_score(
        delta_pct=12.0,
        anomaly_indicator=0.5,
        certification_missing=True,
        signature_risk=False,
    )

    heavier_anomaly = AnomalyDetectionService(
        weights={
            "delta_weight": 0.2,
            "anomaly_weight": 0.5,
            "cert_weight": 0.2,
            "signature_weight": 0.1,
        },
        trigger_threshold=0.8,
        autofail_threshold=15.0,
    )
    adjusted = heavier_anomaly.compute_risk_score(
        delta_pct=12.0,
        anomaly_indicator=0.5,
        certification_missing=True,
        signature_risk=False,
    )

    assert adjusted.score != pytest.approx(baseline.score)


def _build_contract_item(rate: float) -> dict:
    return {
        "s_no": "1",
        "sheet_name": "SHEET-1",
        "description": "Contract Service",
        "rate_source": "CONTRACT",
        "unit_rate": rate,
        "quantity": 1.0,
        "total_usd": rate,
        "formula_text": "",
        "remark": "",
    }


def _stub_gate_result(*_args, **_kwargs):
    return {
        "Gate_Status": "PASS",
        "Gate_Fails": "",
        "Gate_Score": 100.0,
        "gates": {},
    }


def test_validate_enhanced_item_risk_threshold_transition():
    engine = ShipmentAuditEngine()
    engine.risk_based_review_config["enabled"] = True

    weights = {
        "delta_weight": 1.0,
        "anomaly_weight": 0.0,
        "cert_weight": 0.0,
        "signature_weight": 0.0,
    }

    engine.anomaly_service = AnomalyDetectionService(
        weights=weights,
        trigger_threshold=0.2,
        autofail_threshold=engine.cost_guard_bands.get("autofail", 15.0),
    )
    engine.risk_based_review_config["score_formula"] = weights
    engine.risk_based_review_config["trigger_threshold"] = 0.2

    engine._find_contract_ref_rate = types.MethodType(
        lambda self, item: 100.0,
        engine,
    )
    engine.run_key_gates = types.MethodType(_stub_gate_result, engine)

    low_result = engine.validate_enhanced_item(_build_contract_item(102.0), [])

    assert low_result["risk_score"] < engine.anomaly_service.trigger_threshold
    assert low_result["status"] == "PASS"
    assert low_result["flag"] == "OK"
    assert low_result["risk_triggered"] is False

    engine.anomaly_service = AnomalyDetectionService(
        weights=weights,
        trigger_threshold=0.1,
        autofail_threshold=engine.cost_guard_bands.get("autofail", 15.0),
    )
    engine.risk_based_review_config["trigger_threshold"] = 0.1

    high_result = engine.validate_enhanced_item(_build_contract_item(102.0), [])

    assert high_result["risk_score"] >= engine.anomaly_service.trigger_threshold
    assert high_result["status"] == "REVIEW_NEEDED"
    assert high_result["flag"] == "RISK"
    assert high_result["risk_triggered"] is True
