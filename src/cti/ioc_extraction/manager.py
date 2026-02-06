from __future__ import annotations

from typing import Any, Dict, Iterable, List
import logging

from cti.ioc_extraction.extractor import extract_iocs, normalize_ioc
from cti.ioc_extraction.models import IOC
from cti.preprocessing.models import NormalizedEvent


class IOCExtractionManager:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        extraction_cfg = config.get("ioc_extraction", {})
        self.min_confidence = float(extraction_cfg.get("min_confidence", 0.75))

    def extract(self, events: Iterable[NormalizedEvent]) -> List[IOC]:
        iocs: List[IOC] = []
        for event in events:
            hits = extract_iocs(event.clean_text)
            for ioc_type, values in hits.items():
                for value in values:
                    normalized = normalize_ioc(ioc_type, value)
                    iocs.append(
                        IOC(
                            ioc_type=ioc_type,
                            value=value,
                            normalized_value=normalized,
                            confidence=self.min_confidence,
                            source_event_id=event.event_id,
                            context=self._context_snippet(event.clean_text, value),
                        )
                    )
        return iocs

    def _context_snippet(self, text: str, value: str, window: int = 40) -> str:
        idx = text.find(value)
        if idx == -1:
            return ""
        start = max(idx - window, 0)
        end = min(idx + len(value) + window, len(text))
        return text[start:end].strip()
