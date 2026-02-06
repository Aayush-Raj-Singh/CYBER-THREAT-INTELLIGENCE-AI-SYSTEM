from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from cti.preprocessing.models import NormalizedEvent


def write_normalized_events(events: Iterable[NormalizedEvent], output_path: str) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            payload = {
                "event_id": event.event_id,
                "source": event.source,
                "source_url": event.source_url,
                "fetched_at": event.fetched_at.isoformat(),
                "language": event.language,
                "language_confidence": event.language_confidence,
                "clean_text": event.clean_text,
                "tokens": event.tokens,
                "raw_metadata": event.raw_metadata,
                "content_hash": event.content_hash,
            }
            handle.write(json.dumps(payload, ensure_ascii=True))
            handle.write("\n")
            count += 1
    return count
