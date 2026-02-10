from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Campaign:
    campaign_id: str
    name: str
    start_time: datetime
    end_time: datetime
    event_ids: List[str] = field(default_factory=list)
    iocs: List[str] = field(default_factory=list)
    mitre_tactics: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class CorrelationResult:
    event_id: str
    campaign_id: Optional[str]
    shared_iocs: List[str]
    temporal_cluster: Optional[str]
    mitre_tactics: List[str]
    confidence: float
