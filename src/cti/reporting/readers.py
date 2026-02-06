from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from cti.analysis.models import AnalysisResult
from cti.correlation.models import CorrelationResult
from cti.ioc_extraction.models import IOC
from cti.scoring.models import ScoreResult


def _read_jsonl(path: str) -> Iterator[dict]:
    file_path = Path(path)
    if not file_path.exists():
        return iter(())

    def _iter() -> Iterator[dict]:
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)

    return _iter()


def read_analysis(path: str) -> Iterator[AnalysisResult]:
    for payload in _read_jsonl(path):
        yield AnalysisResult(
            event_id=payload["event_id"],
            incident_type=payload.get("incident_type", "unknown"),
            incident_confidence=float(payload.get("incident_confidence", 0.0)),
            sector=payload.get("sector", "unknown"),
            sector_confidence=float(payload.get("sector_confidence", 0.0)),
            cluster_id=payload.get("cluster_id"),
            cluster_confidence=float(payload.get("cluster_confidence", 0.0)),
            explanations=payload.get("explanations", {}),
        )


def read_correlation(path: str) -> Iterator[CorrelationResult]:
    for payload in _read_jsonl(path):
        yield CorrelationResult(
            event_id=payload["event_id"],
            campaign_id=payload.get("campaign_id"),
            shared_iocs=payload.get("shared_iocs", []),
            temporal_cluster=payload.get("temporal_cluster"),
            mitre_tactics=payload.get("mitre_tactics", []),
            confidence=float(payload.get("confidence", 0.0)),
        )


def read_scores(path: str) -> Iterator[ScoreResult]:
    for payload in _read_jsonl(path):
        yield ScoreResult(
            event_id=payload["event_id"],
            severity=float(payload.get("severity", 0.0)),
            severity_label=payload.get("severity_label", "informational"),
            confidence=float(payload.get("confidence", 0.0)),
            rationale=payload.get("rationale", {}),
        )


def read_iocs(path: str) -> Iterator[IOC]:
    for payload in _read_jsonl(path):
        yield IOC(
            ioc_type=payload["ioc_type"],
            value=payload["value"],
            normalized_value=payload.get("normalized_value", payload["value"]),
            confidence=float(payload.get("confidence", 0.0)),
            source_event_id=payload["source_event_id"],
            context=payload.get("context"),
        )


def read_campaigns(path: str) -> Iterator[dict]:
    for payload in _read_jsonl(path):
        yield payload
