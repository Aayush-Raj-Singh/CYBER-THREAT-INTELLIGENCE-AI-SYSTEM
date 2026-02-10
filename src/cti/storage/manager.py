from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import json
import logging

from sqlalchemy.orm import Session

from cti.analysis.reader import read_normalized_events
from cti.correlation.analysis_reader import read_analysis_results
from cti.correlation.ioc_reader import read_iocs
from cti.correlation.models import Campaign
from cti.preprocessing.reader import read_raw_events
from cti.scoring.correlation_reader import read_correlation_results
from cti.scoring.models import ScoreResult
from cti.storage.dao import (
    upsert_analysis,
    upsert_campaigns,
    upsert_correlation,
    upsert_normalized_events,
    upsert_raw_events,
    upsert_scores,
    insert_iocs,
)
from cti.storage.models import create_db_engine, init_db


class StorageManager:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        storage_cfg = config.get("storage", {})
        self.db_url = storage_cfg.get("db_url", "sqlite:///data/cti.db")

    def store(self) -> None:
        engine = create_db_engine(self.db_url)
        init_db(engine)

        with Session(engine) as session:
            self._store_raw_events(session)
            self._store_normalized_events(session)
            self._store_iocs(session)
            self._store_analysis(session)
            self._store_correlation(session)
            self._store_campaigns(session)
            self._store_scores(session)
            session.commit()

        self.logger.info("Storage complete")

    def _store_raw_events(self, session: Session) -> None:
        ingestion_cfg = self.config.get("ingestion", {})
        raw_path = ingestion_cfg.get("output_raw_path", "data/raw_events.jsonl")
        events = list(read_raw_events(raw_path))
        upsert_raw_events(session, events)

    def _store_normalized_events(self, session: Session) -> None:
        preprocessing_cfg = self.config.get("preprocessing", {})
        norm_path = preprocessing_cfg.get("output_normalized_path", "data/normalized_events.jsonl")
        events = list(read_normalized_events(norm_path))
        upsert_normalized_events(session, events)

    def _store_iocs(self, session: Session) -> None:
        ioc_cfg = self.config.get("ioc_extraction", {})
        ioc_path = ioc_cfg.get("output_iocs_path", "data/iocs.jsonl")
        iocs = list(read_iocs(ioc_path))
        insert_iocs(session, iocs)

    def _store_analysis(self, session: Session) -> None:
        analysis_cfg = self.config.get("analysis", {})
        analysis_path = analysis_cfg.get("output_analysis_path", "data/analysis_results.jsonl")
        results = list(read_analysis_results(analysis_path))
        upsert_analysis(session, results)

    def _store_correlation(self, session: Session) -> None:
        correlation_cfg = self.config.get("correlation", {})
        correlation_path = correlation_cfg.get("output_correlation_path", "data/correlation_results.jsonl")
        results = list(read_correlation_results(correlation_path))
        upsert_correlation(session, results)

    def _store_campaigns(self, session: Session) -> None:
        correlation_cfg = self.config.get("correlation", {})
        campaigns_path = correlation_cfg.get("output_campaigns_path", "data/campaigns.jsonl")
        campaigns = self._load_campaigns(campaigns_path)
        upsert_campaigns(session, campaigns)

    def _store_scores(self, session: Session) -> None:
        scoring_cfg = self.config.get("scoring", {})
        scores_path = scoring_cfg.get("output_scores_path", "data/scores.jsonl")
        scores = self._load_scores(scores_path)
        upsert_scores(session, scores)

    def _load_campaigns(self, path_value: str) -> List[Campaign]:
        path = Path(path_value)
        if not path.exists():
            return []
        campaigns: List[Campaign] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                campaigns.append(
                    Campaign(
                        campaign_id=payload["campaign_id"],
                        name=payload.get("name", payload["campaign_id"]),
                        start_time=datetime.fromisoformat(payload["start_time"]),
                        end_time=datetime.fromisoformat(payload["end_time"]),
                        event_ids=payload.get("event_ids", []),
                        iocs=payload.get("iocs", []),
                        mitre_tactics=payload.get("mitre_tactics", []),
                        confidence=float(payload.get("confidence", 0.0)),
                    )
                )
        return campaigns

    def _load_scores(self, path_value: str) -> List[ScoreResult]:
        path = Path(path_value)
        if not path.exists():
            return []
        scores: List[ScoreResult] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                scores.append(
                    ScoreResult(
                        event_id=payload["event_id"],
                        severity=float(payload.get("severity", 0.0)),
                        severity_label=payload.get("severity_label", "informational"),
                        confidence=float(payload.get("confidence", 0.0)),
                        rationale=payload.get("rationale", {}),
                    )
                )
        return scores
