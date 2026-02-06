from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterator

from cti.analysis.models import AnalysisResult


def read_analysis_results(path: str) -> Iterator[AnalysisResult]:
    file_path = Path(path)
    if not file_path.exists():
        return iter(())

    def _iter() -> Iterator[AnalysisResult]:
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
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

    return _iter()
