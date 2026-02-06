from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AnalysisResult:
    event_id: str
    incident_type: str
    incident_confidence: float
    sector: str
    sector_confidence: float
    cluster_id: Optional[int]
    cluster_confidence: float
    explanations: Dict[str, List[str]] = field(default_factory=dict)
