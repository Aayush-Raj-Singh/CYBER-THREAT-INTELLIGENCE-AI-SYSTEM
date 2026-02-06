from __future__ import annotations

from typing import Any, Dict, Iterable, List
import logging

from cti.ingestion.models import RawEvent
from cti.preprocessing.cleaner import clean_text, tokenize
from cti.preprocessing.language import detect_language
from cti.preprocessing.models import NormalizedEvent
from cti.preprocessing.reader import read_raw_events


class PreprocessingManager:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

        preprocessing_cfg = config.get("preprocessing", {})
        self.min_text_length = int(preprocessing_cfg.get("min_text_length", 20))
        self.noise_patterns = preprocessing_cfg.get("noise_patterns", [])
        self.allowed_languages = preprocessing_cfg.get("allowed_languages", [])
        self.min_token_length = int(preprocessing_cfg.get("min_token_length", 2))

    def read_input(self, input_path: str) -> Iterable[RawEvent]:
        return read_raw_events(input_path)

    def normalize(self, events: Iterable[RawEvent]) -> List[NormalizedEvent]:
        normalized: List[NormalizedEvent] = []
        for event in events:
            text = clean_text(event.raw_text, self.noise_patterns)
            if len(text) < self.min_text_length:
                continue

            language, confidence = detect_language(text)
            if self.allowed_languages and language not in self.allowed_languages:
                continue

            tokens = tokenize(text, min_token_length=self.min_token_length)

            normalized.append(
                NormalizedEvent(
                    event_id=event.event_id,
                    source=event.source,
                    source_url=event.source_url,
                    fetched_at=event.fetched_at,
                    language=language,
                    language_confidence=confidence,
                    clean_text=text,
                    tokens=tokens,
                    raw_metadata=event.raw_metadata,
                    content_hash=event.content_hash,
                )
            )
        return normalized
