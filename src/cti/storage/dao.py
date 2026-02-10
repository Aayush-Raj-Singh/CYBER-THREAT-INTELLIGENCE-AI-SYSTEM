from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

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
    rows = [
        {
            "event_id": event.event_id,
            "source": event.source,
            "source_url": event.source_url,
            "fetched_at": event.fetched_at,
            "raw_text": event.raw_text,
            "raw_metadata": event.raw_metadata,
            "content_hash": event.content_hash,
        }
        for event in events
    ]
    _bulk_insert_ignore(session, RawEventModel, rows, ["event_id"])


def upsert_normalized_events(session: Session, events: Iterable[NormalizedEvent]) -> None:
    rows = [
        {
            "event_id": event.event_id,
            "source": event.source,
            "source_url": event.source_url,
            "fetched_at": event.fetched_at,
            "language": event.language,
            "language_confidence": event.language_confidence,
            "clean_text": event.clean_text,
            "tokens": event.tokens,
            "raw_metadata": event.raw_metadata,
            "content_hash": event.content_hash,
        }
        for event in events
    ]
    _bulk_insert_ignore(session, NormalizedEventModel, rows, ["event_id"])


def insert_iocs(session: Session, iocs: Iterable[IOC]) -> None:
    deduped = {}
    for ioc in iocs:
        key = (ioc.source_event_id, ioc.ioc_type, ioc.normalized_value)
        if key not in deduped:
            deduped[key] = ioc

    rows = [
        {
            "ioc_type": ioc.ioc_type,
            "value": ioc.value,
            "normalized_value": ioc.normalized_value,
            "confidence": ioc.confidence,
            "source_event_id": ioc.source_event_id,
            "context": ioc.context,
        }
        for ioc in deduped.values()
    ]
    _bulk_insert_ignore(
        session,
        IOCModel,
        rows,
        ["source_event_id", "ioc_type", "normalized_value"],
    )


def upsert_analysis(session: Session, results: Iterable[AnalysisResult]) -> None:
    rows = [
        {
            "event_id": result.event_id,
            "incident_type": result.incident_type,
            "incident_confidence": result.incident_confidence,
            "sector": result.sector,
            "sector_confidence": result.sector_confidence,
            "cluster_id": result.cluster_id,
            "cluster_confidence": result.cluster_confidence,
            "explanations": result.explanations,
        }
        for result in results
    ]
    _bulk_insert_ignore(session, AnalysisModel, rows, ["event_id"])


def upsert_correlation(session: Session, results: Iterable[CorrelationResult]) -> None:
    rows = [
        {
            "event_id": result.event_id,
            "campaign_id": result.campaign_id,
            "shared_iocs": result.shared_iocs,
            "temporal_cluster": result.temporal_cluster,
            "mitre_tactics": result.mitre_tactics,
            "confidence": result.confidence,
        }
        for result in results
    ]
    _bulk_insert_ignore(session, CorrelationModel, rows, ["event_id"])


def upsert_campaigns(session: Session, campaigns: Iterable[Campaign]) -> None:
    rows = [
        {
            "campaign_id": campaign.campaign_id,
            "name": campaign.name,
            "start_time": campaign.start_time,
            "end_time": campaign.end_time,
            "event_ids": campaign.event_ids,
            "iocs": campaign.iocs,
            "mitre_tactics": campaign.mitre_tactics,
            "confidence": campaign.confidence,
        }
        for campaign in campaigns
    ]
    _bulk_insert_ignore(session, CampaignModel, rows, ["campaign_id"])


def upsert_scores(session: Session, scores: Iterable[ScoreResult]) -> None:
    rows = [
        {
            "event_id": score.event_id,
            "severity": score.severity,
            "severity_label": score.severity_label,
            "confidence": score.confidence,
            "rationale": score.rationale,
        }
        for score in scores
    ]
    _bulk_insert_ignore(session, ScoreModel, rows, ["event_id"])


def _bulk_insert_ignore(
    session: Session,
    model,
    rows: Iterable[dict],
    conflict_cols: Iterable[str],
) -> None:
    rows_list = list(rows)
    if not rows_list:
        return

    dialect = session.bind.dialect.name if session.bind is not None else ""
    if dialect == "sqlite":
        stmt = sqlite_insert(model).values(rows_list).on_conflict_do_nothing(
            index_elements=list(conflict_cols)
        )
        session.execute(stmt)
        return

    if dialect == "postgresql":
        stmt = pg_insert(model).values(rows_list).on_conflict_do_nothing(
            index_elements=list(conflict_cols)
        )
        session.execute(stmt)
        return

    # Fallback: safe per-row check for unsupported dialects.
    for row in rows_list:
        query = session.query(model)
        for col in conflict_cols:
            query = query.filter(getattr(model, col) == row[col])
        if query.first():
            continue
        session.add(model(**row))
