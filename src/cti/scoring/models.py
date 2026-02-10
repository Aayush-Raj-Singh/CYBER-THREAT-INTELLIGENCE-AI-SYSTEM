from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ScoreResult:
    event_id: str
    severity: float
    severity_label: str
    confidence: float
    rationale: Dict[str, float]
