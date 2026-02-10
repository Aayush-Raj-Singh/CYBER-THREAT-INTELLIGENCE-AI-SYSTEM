from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from cti.analysis.models import AnalysisResult


def write_analysis_results(results: Iterable[AnalysisResult], output_path: str) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for result in results:
            payload = {
                "event_id": result.event_id,
                "incident_type": result.incident_type,
                "incident_confidence": result.incident_confidence,
                "sector": result.sector,
                "sector_confidence": result.sector_confidence,
                "cluster_id": result.cluster_id,
                "cluster_confidence": result.cluster_confidence,
                "explanations": result.explanations,
            }
            handle.write(json.dumps(payload, ensure_ascii=True))
            handle.write("\n")
            count += 1
    return count
