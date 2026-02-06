from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class ReportItem:
    event_id: str
    incident_type: str
    sector: str
    severity_label: str
    severity: float
    confidence: float
    mitre_tactics: List[str]
    iocs: List[str]
    summary: str


@dataclass
class ReportBundle:
    generated_at: datetime
    items: List[ReportItem] = field(default_factory=list)
    campaigns: List[Dict[str, object]] = field(default_factory=list)
