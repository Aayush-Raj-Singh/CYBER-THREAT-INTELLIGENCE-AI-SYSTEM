from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class NormalizedEvent:
    event_id: str
    source: str
    source_url: str
    fetched_at: datetime
    language: str
    language_confidence: float
    clean_text: str
    tokens: List[str] = field(default_factory=list)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    content_hash: Optional[str] = None
