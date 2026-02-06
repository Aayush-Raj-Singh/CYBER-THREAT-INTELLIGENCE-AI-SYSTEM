from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from cti.ioc_extraction.models import IOC


def read_iocs(path: str) -> Iterator[IOC]:
    file_path = Path(path)
    if not file_path.exists():
        return iter(())

    def _iter() -> Iterator[IOC]:
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                yield IOC(
                    ioc_type=payload["ioc_type"],
                    value=payload["value"],
                    normalized_value=payload.get("normalized_value", payload["value"]),
                    confidence=float(payload.get("confidence", 0.0)),
                    source_event_id=payload["source_event_id"],
                    context=payload.get("context"),
                )

    return _iter()
