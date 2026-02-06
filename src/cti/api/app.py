from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, sessionmaker

from cti.api.schemas import (
    CampaignItem,
    EventDetail,
    EventSummary,
    HealthResponse,
    IocItem,
    ReportResponse,
    SummaryStats,
)
from cti.config.loader import load_config
from cti.storage.models import (
    AnalysisModel,
    CampaignModel,
    CorrelationModel,
    IOCModel,
    NormalizedEventModel,
    ScoreModel,
    create_db_engine,
)


def create_app(config_path: Optional[str] = None) -> FastAPI:
    config: Dict[str, Any] = load_config(config_path)
    db_url = config.get("storage", {}).get("db_url", "sqlite:///data/cti.db")
    engine = create_db_engine(db_url)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    app = FastAPI(title="CTI AI System", version="1.0")

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/api/summary", response_model=SummaryStats)
    def summary() -> SummaryStats:
        with SessionLocal() as session:
            total_events = session.query(ScoreModel).count()
            severity_counts = _count_by_severity(session)
            incident_counts = _count_by_incident(session)
            sector_counts = _count_by_sector(session)
            campaign_count = session.query(CampaignModel).count()
            ioc_count = session.query(IOCModel).count()

        return SummaryStats(
            total_events=total_events,
            severity_counts=severity_counts,
            incident_counts=incident_counts,
            sector_counts=sector_counts,
            campaign_count=campaign_count,
            ioc_count=ioc_count,
        )

    @app.get("/api/events", response_model=List[EventSummary])
    def events(
        severity: Optional[str] = Query(default=None),
        incident: Optional[str] = Query(default=None),
        sector: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> List[EventSummary]:
        with SessionLocal() as session:
            items = _collect_events(session)

        if severity:
            items = [item for item in items if item.severity_label == severity]
        if incident:
            items = [item for item in items if item.incident_type == incident]
        if sector:
            items = [item for item in items if item.sector == sector]

        items = sorted(items, key=lambda item: item.severity, reverse=True)
        return items[offset : offset + limit]

    @app.get("/api/events/{event_id}", response_model=EventDetail)
    def event_detail(event_id: str) -> EventDetail:
        with SessionLocal() as session:
            detail = _collect_event_detail(session, event_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Event not found")
        return detail

    @app.get("/api/campaigns", response_model=List[CampaignItem])
    def campaigns() -> List[CampaignItem]:
        with SessionLocal() as session:
            rows = session.query(CampaignModel).order_by(CampaignModel.confidence.desc()).all()
        return [
            CampaignItem(
                campaign_id=row.campaign_id,
                name=row.name,
                start_time=row.start_time,
                end_time=row.end_time,
                event_ids=row.event_ids or [],
                iocs=row.iocs or [],
                mitre_tactics=row.mitre_tactics or [],
                confidence=row.confidence,
            )
            for row in rows
        ]

    @app.get("/api/iocs", response_model=List[IocItem])
    def iocs(limit: int = Query(default=100, ge=1, le=1000)) -> List[IocItem]:
        with SessionLocal() as session:
            rows = session.query(IOCModel).limit(limit).all()
        return [
            IocItem(
                ioc_type=row.ioc_type,
                value=row.value,
                normalized_value=row.normalized_value,
                confidence=row.confidence,
                source_event_id=row.source_event_id,
                context=row.context,
            )
            for row in rows
        ]

    @app.get("/api/reports/latest", response_model=ReportResponse)
    def latest_report() -> ReportResponse:
        reporting_cfg = config.get("reporting", {})
        report_path = reporting_cfg.get("output_json_path", "reports/report.json")
        path = _resolve_repo_path(report_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        payload = path.read_text(encoding="utf-8")
        return ReportResponse(raw_json=payload)

    react_dist = _resolve_repo_path("web-react/dist")
    if react_dist.exists():
        app.mount("/ui", StaticFiles(directory=str(react_dist), html=True), name="ui")

        @app.get("/")
        def root() -> RedirectResponse:
            return RedirectResponse(url="/ui")

    return app


def _resolve_repo_path(path_value: str) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    path = Path(path_value)
    if path.is_absolute():
        return path
    return repo_root / path


def _collect_events(session: Session) -> List[EventSummary]:
    analysis_map = {row.event_id: row for row in session.query(AnalysisModel).all()}
    correlation_map = {row.event_id: row for row in session.query(CorrelationModel).all()}
    event_map = {row.event_id: row for row in session.query(NormalizedEventModel).all()}

    items: List[EventSummary] = []
    for score in session.query(ScoreModel).all():
        analysis = analysis_map.get(score.event_id)
        event = event_map.get(score.event_id)
        corr = correlation_map.get(score.event_id)
        if not analysis or not event:
            continue

        items.append(
            EventSummary(
                event_id=score.event_id,
                incident_type=analysis.incident_type,
                sector=analysis.sector,
                severity=score.severity,
                severity_label=score.severity_label,
                confidence=score.confidence,
                fetched_at=event.fetched_at,
                source=event.source,
                source_url=event.source_url,
                mitre_tactics=corr.mitre_tactics if corr else [],
                campaign_id=corr.campaign_id if corr else None,
            )
        )
    return items


def _collect_event_detail(session: Session, event_id: str) -> Optional[EventDetail]:
    analysis = session.query(AnalysisModel).filter_by(event_id=event_id).first()
    score = session.query(ScoreModel).filter_by(event_id=event_id).first()
    event = session.query(NormalizedEventModel).filter_by(event_id=event_id).first()
    corr = session.query(CorrelationModel).filter_by(event_id=event_id).first()
    iocs = session.query(IOCModel).filter_by(source_event_id=event_id).all()

    if not analysis or not score or not event:
        return None

    return EventDetail(
        event_id=event_id,
        incident_type=analysis.incident_type,
        incident_confidence=analysis.incident_confidence,
        sector=analysis.sector,
        sector_confidence=analysis.sector_confidence,
        severity=score.severity,
        severity_label=score.severity_label,
        confidence=score.confidence,
        fetched_at=event.fetched_at,
        source=event.source,
        source_url=event.source_url,
        clean_text=event.clean_text,
        mitre_tactics=corr.mitre_tactics if corr else [],
        campaign_id=corr.campaign_id if corr else None,
        shared_iocs=corr.shared_iocs if corr else [],
        iocs=[ioc.normalized_value for ioc in iocs],
    )


def _count_by_severity(session: Session) -> Dict[str, int]:
    counts: Dict[str, int] = {"informational": 0, "low": 0, "medium": 0, "high": 0}
    for row in session.query(ScoreModel).all():
        counts[row.severity_label] = counts.get(row.severity_label, 0) + 1
    return counts


def _count_by_incident(session: Session) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in session.query(AnalysisModel).all():
        counts[row.incident_type] = counts.get(row.incident_type, 0) + 1
    return counts


def _count_by_sector(session: Session) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in session.query(AnalysisModel).all():
        counts[row.sector] = counts.get(row.sector, 0) + 1
    return counts
