from __future__ import annotations

from typing import Any, Dict, Iterable, List
import logging

from cti.analysis.models import AnalysisResult
from cti.correlation.models import CorrelationResult
from cti.scoring.models import ScoreResult


class ScoringManager:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

        scoring_cfg = config.get("scoring", {})
        self.severity_thresholds = scoring_cfg.get(
            "severity_thresholds",
            {"low": 0.3, "medium": 0.6, "high": 0.8},
        )
        self.weights = scoring_cfg.get(
            "weights",
            {
                "incident_conf": 0.35,
                "sector_conf": 0.15,
                "correlation_conf": 0.30,
                "ioc_count": 0.10,
                "mitre_tactics": 0.10,
            },
        )

    def score(
        self,
        analyses: Iterable[AnalysisResult],
        correlations: Iterable[CorrelationResult],
        iocs_by_event: Dict[str, int],
    ) -> List[ScoreResult]:
        analysis_map = {analysis.event_id: analysis for analysis in analyses}
        correlation_map = {corr.event_id: corr for corr in correlations}

        results: List[ScoreResult] = []
        for event_id, analysis in analysis_map.items():
            corr = correlation_map.get(event_id)
            ioc_count = iocs_by_event.get(event_id, 0)

            ioc_score = min(1.0, ioc_count / 10.0)
            mitre_score = min(1.0, len(corr.mitre_tactics) / 5.0) if corr else 0.0
            corr_conf = corr.confidence if corr else 0.0

            severity = (
                self.weights.get("incident_conf", 0.35) * analysis.incident_confidence
                + self.weights.get("sector_conf", 0.15) * analysis.sector_confidence
                + self.weights.get("correlation_conf", 0.30) * corr_conf
                + self.weights.get("ioc_count", 0.10) * ioc_score
                + self.weights.get("mitre_tactics", 0.10) * mitre_score
            )
            severity = max(0.0, min(1.0, severity))

            label = self._severity_label(severity)
            confidence = max(analysis.incident_confidence, corr_conf)

            results.append(
                ScoreResult(
                    event_id=event_id,
                    severity=severity,
                    severity_label=label,
                    confidence=confidence,
                    rationale={
                        "incident_conf": analysis.incident_confidence,
                        "sector_conf": analysis.sector_confidence,
                        "correlation_conf": corr_conf,
                        "ioc_score": ioc_score,
                        "mitre_score": mitre_score,
                    },
                )
            )

        self.logger.info("Scoring complete events=%d", len(results))
        return results

    def _severity_label(self, severity: float) -> str:
        high = float(self.severity_thresholds.get("high", 0.8))
        medium = float(self.severity_thresholds.get("medium", 0.6))
        low = float(self.severity_thresholds.get("low", 0.3))
        if severity >= high:
            return "high"
        if severity >= medium:
            return "medium"
        if severity >= low:
            return "low"
        return "informational"
