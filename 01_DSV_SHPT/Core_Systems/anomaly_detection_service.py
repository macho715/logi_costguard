"""Anomaly detection risk blending service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class RiskAssessment:
    """위험 점수 평가/Combined risk score assessment."""

    score: float
    components: Dict[str, float]
    triggered: bool


class AnomalyDetectionService:
    """위험 기반 리뷰 계산기/Risk based review calculator."""

    _DEFAULT_WEIGHTS = {
        "delta_weight": 0.4,
        "anomaly_weight": 0.3,
        "cert_weight": 0.2,
        "signature_weight": 0.1,
    }

    def __init__(
        self,
        weights: Dict[str, float] | None,
        trigger_threshold: float,
        autofail_threshold: float,
    ) -> None:
        """가중치와 임계값 설정/Configure weights and trigger threshold."""

        self.weights = self._normalise_weights(weights)
        self.trigger_threshold = float(trigger_threshold)
        self.autofail_threshold = max(float(autofail_threshold), 0.01)

    def _normalise_weights(self, weights: Dict[str, float] | None) -> Dict[str, float]:
        """가중치를 정규화/Normalise incoming weights."""

        merged = self._DEFAULT_WEIGHTS.copy()
        if weights:
            for key, value in weights.items():
                if key in merged and value is not None:
                    merged[key] = float(value)

        total = sum(merged.values())
        if total <= 0:
            return merged

        return {key: value / total for key, value in merged.items()}

    def compute_risk_score(
        self,
        *,
        delta_pct: float | None,
        anomaly_indicator: float = 0.0,
        certification_missing: bool = False,
        signature_risk: bool = False,
    ) -> RiskAssessment:
        """위험 점수 계산/Compute blended risk score."""

        delta_norm = 0.0
        if delta_pct is not None:
            delta_norm = min(
                1.0,
                max(0.0, abs(float(delta_pct)) / self.autofail_threshold),
            )

        anomaly_norm = max(0.0, min(1.0, float(anomaly_indicator)))
        cert_norm = 1.0 if certification_missing else 0.0
        signature_norm = 1.0 if signature_risk else 0.0

        components = {
            "delta": round(delta_norm, 2),
            "anomaly": round(anomaly_norm, 2),
            "certification": round(cert_norm, 2),
            "signature": round(signature_norm, 2),
        }

        raw_score = (
            components["delta"] * self.weights.get("delta_weight", 0.0)
            + components["anomaly"] * self.weights.get("anomaly_weight", 0.0)
            + components["certification"] * self.weights.get("cert_weight", 0.0)
            + components["signature"] * self.weights.get("signature_weight", 0.0)
        )

        score = round(raw_score, 2)
        triggered = score >= self.trigger_threshold

        return RiskAssessment(score=score, components=components, triggered=triggered)
