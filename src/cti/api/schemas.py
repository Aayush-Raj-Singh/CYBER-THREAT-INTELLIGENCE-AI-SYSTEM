from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class SummaryStats(BaseModel):
    total_events: int
    severity_counts: Dict[str, int]
    incident_counts: Dict[str, int]
    sector_counts: Dict[str, int]
    campaign_count: int
    ioc_count: int


class EventSummary(BaseModel):
    event_id: str
    incident_type: str
    sector: str
    severity: float
    severity_label: str
    confidence: float
    fetched_at: datetime
    source: str
    source_url: str
    mitre_tactics: List[str]
    campaign_id: Optional[str]


class EventDetail(BaseModel):
    event_id: str
    incident_type: str
    incident_confidence: float
    sector: str
    sector_confidence: float
    severity: float
    severity_label: str
    confidence: float
    fetched_at: datetime
    source: str
    source_url: str
    clean_text: str
    mitre_tactics: List[str]
    campaign_id: Optional[str]
    shared_iocs: List[str]
    iocs: List[str]


class CampaignItem(BaseModel):
    campaign_id: str
    name: str
    start_time: datetime
    end_time: datetime
    event_ids: List[str]
    iocs: List[str]
    mitre_tactics: List[str]
    confidence: float


class IocItem(BaseModel):
    ioc_type: str
    value: str
    normalized_value: str
    confidence: float
    source_event_id: str
    context: Optional[str]


class ReportResponse(BaseModel):
    raw_json: str
