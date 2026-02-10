from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    JSON,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class RawEventModel(Base):
    __tablename__ = "raw_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False)
    source = Column(String(128), nullable=False)
    source_url = Column(Text, nullable=False)
    fetched_at = Column(DateTime, nullable=False)
    raw_text = Column(Text, nullable=False)
    raw_metadata = Column(JSON, nullable=True)
    content_hash = Column(String(128), nullable=True)


class NormalizedEventModel(Base):
    __tablename__ = "normalized_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False)
    source = Column(String(128), nullable=False)
    source_url = Column(Text, nullable=False)
    fetched_at = Column(DateTime, nullable=False)
    language = Column(String(16), nullable=False)
    language_confidence = Column(Float, nullable=False)
    clean_text = Column(Text, nullable=False)
    tokens = Column(JSON, nullable=True)
    raw_metadata = Column(JSON, nullable=True)
    content_hash = Column(String(128), nullable=True)


class IOCModel(Base):
    __tablename__ = "iocs"
    __table_args__ = (
        UniqueConstraint("source_event_id", "ioc_type", "normalized_value", name="uq_ioc_event_type_norm"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ioc_type = Column(String(32), nullable=False)
    value = Column(Text, nullable=False)
    normalized_value = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    source_event_id = Column(String(64), nullable=False)
    context = Column(Text, nullable=True)


class AnalysisModel(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False)
    incident_type = Column(String(64), nullable=False)
    incident_confidence = Column(Float, nullable=False)
    sector = Column(String(64), nullable=False)
    sector_confidence = Column(Float, nullable=False)
    cluster_id = Column(Integer, nullable=True)
    cluster_confidence = Column(Float, nullable=False)
    explanations = Column(JSON, nullable=True)


class CorrelationModel(Base):
    __tablename__ = "correlation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False)
    campaign_id = Column(String(64), nullable=True)
    shared_iocs = Column(JSON, nullable=True)
    temporal_cluster = Column(String(64), nullable=True)
    mitre_tactics = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=False)


class CampaignModel(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    event_ids = Column(JSON, nullable=True)
    iocs = Column(JSON, nullable=True)
    mitre_tactics = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=False)


class ScoreModel(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False)
    severity = Column(Float, nullable=False)
    severity_label = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False)
    rationale = Column(JSON, nullable=True)

class FeedStateModel(Base):
    __tablename__ = "feed_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(Text, unique=True, nullable=False)
    etag = Column(String(256), nullable=True)
    last_modified = Column(String(256), nullable=True)
    fetched_at = Column(DateTime, nullable=True)


class IngestedHashModel(Base):
    __tablename__ = "ingested_hashes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_hash = Column(String(128), unique=True, nullable=False)
    event_id = Column(String(64), nullable=False)
    source = Column(String(128), nullable=False)
    source_url = Column(Text, nullable=False)
    first_seen = Column(DateTime, nullable=False)


def create_db_engine(db_url: str):
    return create_engine(db_url, echo=False, future=True)


def init_db(engine) -> None:
    Base.metadata.create_all(engine)
