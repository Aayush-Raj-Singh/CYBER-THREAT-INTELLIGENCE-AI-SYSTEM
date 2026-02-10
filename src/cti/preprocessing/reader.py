from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterator

from cti.ingestion.models import RawEvent


def read_raw_events(path: str) -> Iterator[RawEvent]:
    file_path = Path(path)
    if not file_path.exists():
        return iter(())

    def _iter() -> Iterator[RawEvent]:
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                yield RawEvent(
                    event_id=payload["event_id"],
                    source=payload["source"],
                    source_url=payload["source_url"],
                    fetched_at=datetime.fromisoformat(payload["fetched_at"]),
                    raw_text=payload["raw_text"],
                    raw_metadata=payload.get("raw_metadata", {}),
                    content_hash=payload.get("content_hash"),
                )

    return _iter()
