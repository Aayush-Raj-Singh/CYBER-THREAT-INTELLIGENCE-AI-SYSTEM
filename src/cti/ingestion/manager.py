from __future__ import annotations

from typing import Any, Dict, List
import logging
import os

from cti.ingestion.connectors import (
    FileConnector,
    HtmlPageConnector,
    JsonApiConnector,
    RssFeedConnector,
    TextFeedConnector,
    SourceConfig,
)
from cti.ingestion.http_client import HttpClient, RateLimiter
from cti.ingestion.models import RawEvent
from cti.ingestion.state import StateStore


class IngestionManager:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

        ingestion_cfg = config.get("ingestion", {})
        self.sources_cfg = ingestion_cfg.get("sources", {})
        storage_cfg = config.get("storage", {})
        db_url = storage_cfg.get("db_url", "sqlite:///data/cti.db")

        rate_limit = int(ingestion_cfg.get("rate_limit_per_minute", 30))
        user_agent = ingestion_cfg.get("user_agent", "CTI-OSINT-Collector/1.0")
        timeout_seconds = int(ingestion_cfg.get("timeout_seconds", 15))
        retries = int(ingestion_cfg.get("retries", 2))
        backoff_seconds = float(ingestion_cfg.get("backoff_seconds", 1.0))

        self.client = HttpClient(
            user_agent=user_agent,
            timeout_seconds=timeout_seconds,
            retries=retries,
            backoff_seconds=backoff_seconds,
            rate_limiter=RateLimiter(rate_limit),
        )
        self.state = StateStore(db_url=db_url, logger=logger)

    def collect(self) -> List[RawEvent]:
        connectors = self._build_connectors()
        events: List[RawEvent] = []
        seen_hashes = set()

        for connector in connectors:
            try:
                fetched = connector.fetch()
                for event in fetched:
                    content_hash = event.ensure_hash()
                    if content_hash in seen_hashes or self.state.has_hash(content_hash):
                        continue
                    seen_hashes.add(content_hash)
                    self.state.mark_hash(
                        content_hash=content_hash,
                        event_id=event.event_id,
                        source=event.source,
                        source_url=event.source_url,
                    )
                    events.append(event)
                self.logger.info(
                    "Ingestion source=%s count=%d",
                    connector.config.name,
                    len(fetched),
                )
            except Exception as exc:  # noqa: BLE001 - ingestion must tolerate partial failures
                self.logger.error("Ingestion error source=%s error=%s", connector.config.name, exc)

        return events

    def _build_connectors(self) -> List[Any]:
        connectors: List[Any] = []

        def add_sources(source_list: List[Dict[str, Any]]) -> None:
            for src in source_list:
                if not src.get("enabled", True):
                    continue
                url = _expand_env(src.get("url"))
                path = _expand_env(src.get("path"))
                source_config = SourceConfig(
                    name=src.get("name", "unknown"),
                    type=src.get("type", "rss"),
                    url=url,
                    path=path,
                    text_prefix=src.get("text_prefix"),
                    content_selector=src.get("content_selector"),
                    title_selector=src.get("title_selector"),
                    text_fields=src.get("text_fields"),
                    json_path=src.get("json_path"),
                    max_items=src.get("max_items"),
                )
                connectors.append(self._connector_from_config(source_config))

        add_sources(self.sources_cfg.get("paste_sites", []))
        add_sources(self.sources_cfg.get("forums", []))
        add_sources(self.sources_cfg.get("telegram_channels", []))
        add_sources(self.sources_cfg.get("advisories", []))
        add_sources(self.sources_cfg.get("blogs", []))
        add_sources(self.sources_cfg.get("threat_feeds", []))

        return connectors

    def _connector_from_config(self, config: SourceConfig) -> Any:
        # WHY: explicit connector mapping avoids hidden scraping behavior.
        source_type = config.type.lower()
        if source_type == "rss":
            return RssFeedConnector(config, self.client, self.state)
        if source_type == "html":
            return HtmlPageConnector(config, self.client, self.state)
        if source_type == "json_api":
            return JsonApiConnector(config, self.client, self.state)
        if source_type == "file":
            return FileConnector(config, self.client, self.state)
        if source_type == "text_feed":
            return TextFeedConnector(config, self.client, self.state)
        raise ValueError(f"Unsupported source type: {config.type}")


def _expand_env(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return os.path.expandvars(value)
