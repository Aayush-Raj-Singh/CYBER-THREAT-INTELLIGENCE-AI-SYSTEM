from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from cti.ioc_extraction.models import IOC


def write_iocs(iocs: Iterable[IOC], output_path: str) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for ioc in iocs:
            payload = {
                "ioc_type": ioc.ioc_type,
                "value": ioc.value,
                "normalized_value": ioc.normalized_value,
                "confidence": ioc.confidence,
                "source_event_id": ioc.source_event_id,
                "context": ioc.context,
            }
            handle.write(json.dumps(payload, ensure_ascii=True))
            handle.write("\n")
            count += 1
    return count
