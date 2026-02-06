from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class IOC:
    ioc_type: str
    value: str
    normalized_value: str
    confidence: float
    source_event_id: str
    context: Optional[str] = None
