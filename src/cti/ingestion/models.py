from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass
class RawEvent:
    event_id: str
    source: str
    source_url: str
    fetched_at: datetime
    raw_text: str
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    content_hash: Optional[str] = None

    def ensure_hash(self) -> str:
        # WHY: stable hashes enable de-duplication across noisy OSINT sources.
        if self.content_hash:
            return self.content_hash
        hasher = hashlib.sha256()
        payload = f"{self.source}|{self.source_url}|{self.raw_text}".encode("utf-8")
        hasher.update(payload)
        self.content_hash = hasher.hexdigest()
        return self.content_hash


def new_event_id() -> str:
    return str(uuid.uuid4())
