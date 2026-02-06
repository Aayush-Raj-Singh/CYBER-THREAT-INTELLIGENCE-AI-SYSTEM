from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from cti.analysis.models import AnalysisResult
from cti.correlation.models import Campaign, CorrelationResult
from cti.ioc_extraction.models import IOC
from cti.ingestion.models import RawEvent
from cti.preprocessing.models import NormalizedEvent
from cti.scoring.models import ScoreResult
from cti.storage.models import (
    AnalysisModel,
    CampaignModel,
    CorrelationModel,
    IOCModel,
    NormalizedEventModel,
    RawEventModel,
    ScoreModel,
)


def load_jsonl(path: str) -> Iterable[dict]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def upsert_raw_events(session: Session, events: Iterable[RawEvent]) -> None:
    for event in events:
        existing = session.query(RawEventModel).filter_by(event_id=event.event_id).first()
        if existing:
            continue
        session.add(
            RawEventModel(
                event_id=event.event_id,
                source=event.source,
                source_url=event.source_url,
                fetched_at=event.fetched_at,
                raw_text=event.raw_text,
                raw_metadata=event.raw_metadata,
                content_hash=event.content_hash,
            )
        )


def upsert_normalized_events(session: Session, events: Iterable[NormalizedEvent]) -> None:
    for event in events:
        existing = session.query(NormalizedEventModel).filter_by(event_id=event.event_id).first()
        if existing:
            continue
        session.add(
            NormalizedEventModel(
                event_id=event.event_id,
                source=event.source,
                source_url=event.source_url,
                fetched_at=event.fetched_at,
                language=event.language,
                language_confidence=event.language_confidence,
                clean_text=event.clean_text,
                tokens=event.tokens,
                raw_metadata=event.raw_metadata,
                content_hash=event.content_hash,
            )
        )


def insert_iocs(session: Session, iocs: Iterable[IOC]) -> None:
    for ioc in iocs:
        session.add(
            IOCModel(
                ioc_type=ioc.ioc_type,
                value=ioc.value,
                normalized_value=ioc.normalized_value,
                confidence=ioc.confidence,
                source_event_id=ioc.source_event_id,
                context=ioc.context,
            )
        )


def upsert_analysis(session: Session, results: Iterable[AnalysisResult]) -> None:
    for result in results:
        existing = session.query(AnalysisModel).filter_by(event_id=result.event_id).first()
        if existing:
            continue
        session.add(
            AnalysisModel(
                event_id=result.event_id,
                incident_type=result.incident_type,
                incident_confidence=result.incident_confidence,
                sector=result.sector,
                sector_confidence=result.sector_confidence,
                cluster_id=result.cluster_id,
                cluster_confidence=result.cluster_confidence,
                explanations=result.explanations,
            )
        )


def upsert_correlation(session: Session, results: Iterable[CorrelationResult]) -> None:
    for result in results:
        existing = session.query(CorrelationModel).filter_by(event_id=result.event_id).first()
        if existing:
            continue
        session.add(
            CorrelationModel(
                event_id=result.event_id,
                campaign_id=result.campaign_id,
                shared_iocs=result.shared_iocs,
                temporal_cluster=result.temporal_cluster,
                mitre_tactics=result.mitre_tactics,
                confidence=result.confidence,
            )
        )


def upsert_campaigns(session: Session, campaigns: Iterable[Campaign]) -> None:
    for campaign in campaigns:
        existing = session.query(CampaignModel).filter_by(campaign_id=campaign.campaign_id).first()
        if existing:
            continue
        session.add(
            CampaignModel(
                campaign_id=campaign.campaign_id,
                name=campaign.name,
                start_time=campaign.start_time,
                end_time=campaign.end_time,
                event_ids=campaign.event_ids,
                iocs=campaign.iocs,
                mitre_tactics=campaign.mitre_tactics,
                confidence=campaign.confidence,
            )
        )


def upsert_scores(session: Session, scores: Iterable[ScoreResult]) -> None:
    for score in scores:
        existing = session.query(ScoreModel).filter_by(event_id=score.event_id).first()
        if existing:
            continue
        session.add(
            ScoreModel(
                event_id=score.event_id,
                severity=score.severity,
                severity_label=score.severity_label,
                confidence=score.confidence,
                rationale=score.rationale,
            )
        )
