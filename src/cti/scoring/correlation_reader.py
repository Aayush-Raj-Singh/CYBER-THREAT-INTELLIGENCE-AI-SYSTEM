from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from cti.correlation.models import CorrelationResult


def read_correlation_results(path: str) -> Iterator[CorrelationResult]:
    file_path = Path(path)
    if not file_path.exists():
        return iter(())

    def _iter() -> Iterator[CorrelationResult]:
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                yield CorrelationResult(
                    event_id=payload["event_id"],
                    campaign_id=payload.get("campaign_id"),
                    shared_iocs=payload.get("shared_iocs", []),
                    temporal_cluster=payload.get("temporal_cluster"),
                    mitre_tactics=payload.get("mitre_tactics", []),
                    confidence=float(payload.get("confidence", 0.0)),
                )

    return _iter()
