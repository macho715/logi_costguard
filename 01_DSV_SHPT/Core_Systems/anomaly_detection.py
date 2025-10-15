"""이상 탐지 서비스 / Anomaly detection service."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from statistics import median
from typing import Any, Dict, Iterable, List

try:
    from sklearn.ensemble import IsolationForest  # type: ignore

    SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    IsolationForest = None  # type: ignore
    SKLEARN_AVAILABLE = False

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnomalyScore:
    """이상 탐지 결과 값 객체 / Value object for anomaly detection output."""

    enabled: bool
    score: float
    risk_level: str
    flagged: bool
    model: str
    details: Dict[str, Any]


class AnomalyDetectionService:
    """이상 탐지 서비스 래퍼 / Wrapper around anomaly detection models."""

    def __init__(self, config: Dict[str, Any]):
        """이상 탐지기 초기화 / Initialize anomaly detector from config."""

        self.config = config
        self.enabled = bool(config.get("enabled", False))
        self.model_type = str(config.get("model", {}).get("type", "robust_zscore")).lower()
        self.model_params = config.get("model", {}).get("params", {})
        self.risk_thresholds = {
            "low": float(config.get("risk_thresholds", {}).get("low", 1.0)),
            "medium": float(config.get("risk_thresholds", {}).get("medium", 2.0)),
            "high": float(config.get("risk_thresholds", {}).get("high", 3.0)),
        }
        self.reference_stats = config.get("reference_statistics", {})
        self._model = None

        if not self.enabled:
            LOGGER.info("Anomaly detection disabled via configuration")
            return

        if self.model_type == "isolation_forest":
            self._initialize_isolation_forest()
        elif self.model_type == "robust_zscore":
            self._initialize_robust_zscore()
        else:
            LOGGER.warning("Unknown anomaly model type '%s'. Disabling.", self.model_type)
            self.enabled = False

    def _initialize_isolation_forest(self) -> None:
        """IsolationForest 모델 초기화 / Initialize IsolationForest model."""

        if not SKLEARN_AVAILABLE:
            LOGGER.error("sklearn not available, disabling IsolationForest anomaly detection")
            self.enabled = False
            return

        params = {"random_state": 42}
        params.update(self.model_params)
        self._model = IsolationForest(**params)

        baseline = self.config.get("baseline_samples") or []
        if baseline:
            feature_matrix = [self._extract_numeric_features(sample) for sample in baseline]
            self._model.fit(feature_matrix)
        else:
            LOGGER.warning("IsolationForest baseline samples missing; detector will flag nothing")

    def _initialize_robust_zscore(self) -> None:
        """Robust Z-score 설정 준비 / Prepare robust z-score configuration."""

        if not self.reference_stats:
            default_spread = float(self.model_params.get("default_spread", 0.1))
            self.reference_stats = {
                "unit_rate": {"median": None, "mad": default_spread},
                "quantity": {"median": None, "mad": default_spread},
            }

    def score_item(self, item_dict: Dict[str, Any]) -> AnomalyScore:
        """단일 항목 이상 점수 계산 / Score a single item for anomaly."""

        if not self.enabled:
            return AnomalyScore(False, 0.0, "DISABLED", False, self.model_type, {})

        if self.model_type == "isolation_forest" and self._model is not None:
            return self._score_item_isolation_forest(item_dict)

        return self._score_item_robust_zscore(item_dict)

    def score_batch(self, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        """배치 이상 점수 요약 / Summarise anomaly scores for a batch."""

        results: List[AnomalyScore] = [self.score_item(item) for item in items]
        total = len(results)
        flagged = sum(1 for r in results if r.flagged)
        risk_counts: Dict[str, int] = {}
        scores: List[float] = []

        for result in results:
            risk_counts[result.risk_level] = risk_counts.get(result.risk_level, 0) + 1
            scores.append(result.score)

        avg_score = round(sum(scores) / total, 2) if total else 0.0

        return {
            "enabled": self.enabled,
            "model": self.model_type,
            "total_scored": total,
            "flagged_items": flagged,
            "average_score": avg_score,
            "risk_counts": risk_counts,
            "results": [result.__dict__ for result in results],
        }

    def _score_item_isolation_forest(self, item_dict: Dict[str, Any]) -> AnomalyScore:
        """IsolationForest 이상 점수 산출 / Score using IsolationForest."""

        assert self._model is not None  # for type checkers
        features = self._extract_numeric_features(item_dict)
        if not features:
            return AnomalyScore(True, 0.0, "NO_DATA", False, self.model_type, {})

        try:
            prediction = self._model.predict([features])[0]
            score = float(-self._model.decision_function([features])[0])
        except Exception as exc:  # pragma: no cover - sklearn runtime failure
            LOGGER.error("IsolationForest scoring failed: %s", exc)
            return AnomalyScore(True, 0.0, "ERROR", False, self.model_type, {"error": str(exc)})

        flagged = prediction == -1
        risk_level = self._risk_from_score(score)
        return AnomalyScore(True, round(score, 2), risk_level, flagged, self.model_type, {})

    def _score_item_robust_zscore(self, item_dict: Dict[str, Any]) -> AnomalyScore:
        """Robust Z-score 이상 점수 산출 / Score using robust z-score."""

        unit_rate = float(item_dict.get("unit_rate", 0.0))
        reference = float(item_dict.get("lane_rate") or item_dict.get("ref_rate") or 0.0)
        spread = self._resolve_spread("unit_rate", reference)

        if reference == 0.0 and unit_rate != 0.0:
            reference = unit_rate

        diff = abs(unit_rate - reference)
        score = diff / spread if spread else 0.0
        score = round(score, 2)
        risk_level = self._risk_from_score(score)
        flagged = score >= self.risk_thresholds["low"]

        details = {
            "reference": round(reference, 2),
            "difference": round(diff, 2),
            "spread": round(spread, 2),
        }

        return AnomalyScore(True, score, risk_level, flagged, self.model_type, details)

    def _risk_from_score(self, score: float) -> str:
        """점수 기반 위험 등급 변환 / Map score to risk level."""

        if score >= self.risk_thresholds["high"]:
            return "HIGH"
        if score >= self.risk_thresholds["medium"]:
            return "MEDIUM"
        if score >= self.risk_thresholds["low"]:
            return "LOW"
        return "NONE"

    def _resolve_spread(self, feature: str, reference: float) -> float:
        """분산 대체값 계산 / Resolve spread for robust z-score."""

        stats = self.reference_stats.get(feature, {})
        mad = float(stats.get("mad") or 0.0)
        if mad <= 0.0:
            mad = max(abs(reference) * float(self.model_params.get("default_spread", 0.1)), 1.0)

        return mad

    @staticmethod
    def _extract_numeric_features(item_dict: Dict[str, Any]) -> List[float]:
        """수치 피처 추출 / Extract numeric features for modelling."""

        numeric_fields = [
            key
            for key, value in item_dict.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        ]

        if not numeric_fields:
            return []

        return [float(item_dict[field]) for field in numeric_fields]

    @staticmethod
    def build_lane_reference_stats(lane_items: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Lane 기준 통계 생성 / Build reference stats from lane items."""

        rates = [float(item.get("unit_rate", 0.0)) for item in lane_items if item.get("unit_rate")]
        if not rates:
            return {}

        med = median(rates)
        deviations = [abs(rate - med) for rate in rates]
        mad = median(deviations) if deviations else 0.0
        return {"unit_rate": {"median": med, "mad": mad or 1.0}}
