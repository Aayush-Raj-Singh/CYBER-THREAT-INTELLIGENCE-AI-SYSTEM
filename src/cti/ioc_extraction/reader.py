from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterator

from cti.preprocessing.models import NormalizedEvent


def read_normalized_events(path: str) -> Iterator[NormalizedEvent]:
    file_path = Path(path)
    if not file_path.exists():
        return iter(())

    def _iter() -> Iterator[NormalizedEvent]:
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                yield NormalizedEvent(
                    event_id=payload["event_id"],
                    source=payload["source"],
                    source_url=payload["source_url"],
                    fetched_at=datetime.fromisoformat(payload["fetched_at"]),
                    language=payload.get("language", "unknown"),
                    language_confidence=float(payload.get("language_confidence", 0.0)),
                    clean_text=payload["clean_text"],
                    tokens=payload.get("tokens", []),
                    raw_metadata=payload.get("raw_metadata", {}),
                    content_hash=payload.get("content_hash"),
                )

    return _iter()
