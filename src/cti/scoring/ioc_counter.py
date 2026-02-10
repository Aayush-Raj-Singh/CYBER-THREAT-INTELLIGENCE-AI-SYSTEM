from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterator
import json
from pathlib import Path


def count_iocs_by_event(path: str) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    file_path = Path(path)
    if not file_path.exists():
        return {}

    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            event_id = payload.get("source_event_id")
            if event_id:
                counts[event_id] += 1
    return dict(counts)
