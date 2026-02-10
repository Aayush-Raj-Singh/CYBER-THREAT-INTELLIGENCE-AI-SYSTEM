from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from cti.scoring.models import ScoreResult


def write_scores(scores: Iterable[ScoreResult], output_path: str) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for score in scores:
            payload = {
                "event_id": score.event_id,
                "severity": score.severity,
                "severity_label": score.severity_label,
                "confidence": score.confidence,
                "rationale": score.rationale,
            }
            handle.write(json.dumps(payload, ensure_ascii=True))
            handle.write("\n")
            count += 1
    return count
