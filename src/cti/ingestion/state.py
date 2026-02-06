from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple
import logging

from sqlalchemy.orm import Session, sessionmaker

from cti.storage.models import FeedStateModel, IngestedHashModel, create_db_engine, init_db


class StateStore:
    def __init__(self, db_url: str, logger: logging.Logger) -> None:
        self.db_url = db_url
        self.logger = logger
        self.engine = create_db_engine(db_url)
        init_db(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)

    def get_feed_state(self, source_url: str) -> Tuple[Optional[str], Optional[str]]:
        with self.SessionLocal() as session:
            row = session.query(FeedStateModel).filter_by(source_url=source_url).first()
            if not row:
                return None, None
            return row.etag, row.last_modified

    def update_feed_state(self, source_url: str, etag: Optional[str], last_modified: Optional[str]) -> None:
        with self.SessionLocal() as session:
            row = session.query(FeedStateModel).filter_by(source_url=source_url).first()
            if row:
                if etag:
                    row.etag = etag
                if last_modified:
                    row.last_modified = last_modified
                row.fetched_at = datetime.utcnow()
            else:
                session.add(
                    FeedStateModel(
                        source_url=source_url,
                        etag=etag,
                        last_modified=last_modified,
                        fetched_at=datetime.utcnow(),
                    )
                )
            session.commit()

    def has_hash(self, content_hash: str) -> bool:
        with self.SessionLocal() as session:
            return session.query(IngestedHashModel).filter_by(content_hash=content_hash).first() is not None

    def mark_hash(self, content_hash: str, event_id: str, source: str, source_url: str) -> None:
        with self.SessionLocal() as session:
            exists = session.query(IngestedHashModel).filter_by(content_hash=content_hash).first()
            if exists:
                return
            session.add(
                IngestedHashModel(
                    content_hash=content_hash,
                    event_id=event_id,
                    source=source,
                    source_url=source_url,
                    first_seen=datetime.utcnow(),
                )
            )
            session.commit()
