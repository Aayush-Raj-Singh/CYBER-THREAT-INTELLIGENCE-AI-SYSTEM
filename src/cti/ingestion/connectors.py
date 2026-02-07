from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import feedparser
from bs4 import BeautifulSoup

from cti.ingestion.http_client import HttpClient
from cti.ingestion.state import StateStore
from cti.ingestion.models import RawEvent, new_event_id


@dataclass
class SourceConfig:
    name: str
    type: str
    url: Optional[str] = None
    path: Optional[str] = None
    text_prefix: Optional[str] = None
    content_selector: Optional[str] = None
    title_selector: Optional[str] = None
    text_fields: Optional[List[str]] = None
    json_path: Optional[str] = None
    max_items: Optional[int] = None


class SourceConnector:
    def __init__(self, config: SourceConfig, client: HttpClient, state: StateStore) -> None:
        self.config = config
        self.client = client
        self.state = state

    def fetch(self) -> List[RawEvent]:
        raise NotImplementedError

    def _safe_get(self, url: str, headers: Optional[Dict[str, str]] = None):
        # WHY: allow conditional GETs to avoid re-downloading unchanged feeds.
        response = self.client.get(url, headers=headers)
        if response.status_code == 304:
            return None
        return response


class RssFeedConnector(SourceConnector):
    def fetch(self) -> List[RawEvent]:
        if not self.config.url:
            raise ValueError("RSS source requires url")

        headers = _conditional_headers(self.state, self.config.url)
        response = self._safe_get(self.config.url, headers=headers)
        if response is None:
            return []
        feed = feedparser.parse(response.text)
        _update_feed_state(self.state, self.config.url, response)
        events: List[RawEvent] = []

        for entry in feed.entries[: self._max_items()]:
            raw_text = _join_parts(
                entry.get("title"),
                entry.get("summary"),
                _content_from_entry(entry),
            )
            raw_text = _apply_prefix(raw_text, self.config.text_prefix)
            if not raw_text:
                continue
            events.append(
                RawEvent(
                    event_id=new_event_id(),
                    source=self.config.name,
                    source_url=entry.get("link", self.config.url),
                    fetched_at=datetime.utcnow(),
                    raw_text=raw_text,
                    raw_metadata={"published": entry.get("published", "")},
                )
            )
        return events

    def _max_items(self) -> int:
        return int(self.config.max_items or 50)


class HtmlPageConnector(SourceConnector):
    def fetch(self) -> List[RawEvent]:
        if not self.config.url:
            raise ValueError("HTML source requires url")

        headers = _conditional_headers(self.state, self.config.url)
        response = self._safe_get(self.config.url, headers=headers)
        if response is None:
            return []
        soup = BeautifulSoup(response.text, "lxml")
        _update_feed_state(self.state, self.config.url, response)

        title = _extract_text(soup, self.config.title_selector) if self.config.title_selector else ""
        body = _extract_text(soup, self.config.content_selector) if self.config.content_selector else soup.get_text(" ")
        raw_text = _join_parts(title, body)
        raw_text = _apply_prefix(raw_text, self.config.text_prefix)

        if not raw_text:
            return []

        return [
            RawEvent(
                event_id=new_event_id(),
                source=self.config.name,
                source_url=self.config.url,
                fetched_at=datetime.utcnow(),
                raw_text=raw_text,
                raw_metadata={},
            )
        ]


class JsonApiConnector(SourceConnector):
    def fetch(self) -> List[RawEvent]:
        if not self.config.url:
            raise ValueError("JSON API source requires url")

        headers = _conditional_headers(self.state, self.config.url)
        response = self._safe_get(self.config.url, headers=headers)
        if response is None:
            return []
        payload = response.json()
        _update_feed_state(self.state, self.config.url, response)
        items = _extract_json_items(payload, self.config.json_path)

        events: List[RawEvent] = []
        for item in items[: self._max_items()]:
            raw_text = _extract_text_fields(item, self.config.text_fields)
            raw_text = _apply_prefix(raw_text, self.config.text_prefix)
            if not raw_text:
                continue
            events.append(
                RawEvent(
                    event_id=new_event_id(),
                    source=self.config.name,
                    source_url=_extract_url(item) or self.config.url,
                    fetched_at=datetime.utcnow(),
                    raw_text=raw_text,
                    raw_metadata={"item": item},
                )
            )
        return events

    def _max_items(self) -> int:
        return int(self.config.max_items or 50)


class FileConnector(SourceConnector):
    def fetch(self) -> List[RawEvent]:
        if not self.config.path:
            raise ValueError("File source requires path")

        events: List[RawEvent] = []
        # WHY: local exports are the safest path for platforms with strict ToS (e.g., Telegram/social).
        with open(self.config.path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    item = {"text": line}
                raw_text = _extract_text_fields(item, self.config.text_fields) or item.get("text")
                raw_text = _apply_prefix(raw_text, self.config.text_prefix)
                if not raw_text:
                    continue
                events.append(
                    RawEvent(
                        event_id=new_event_id(),
                        source=self.config.name,
                        source_url=item.get("url", self.config.path),
                        fetched_at=datetime.utcnow(),
                        raw_text=raw_text,
                        raw_metadata={"item": item},
                    )
                )
                if self._max_items() and len(events) >= self._max_items():
                    break
        return events

    def _max_items(self) -> int:
        return int(self.config.max_items or 0)


class TextFeedConnector(SourceConnector):
    def fetch(self) -> List[RawEvent]:
        if not self.config.url:
            raise ValueError("Text feed source requires url")

        headers = _conditional_headers(self.state, self.config.url)
        response = self._safe_get(self.config.url, headers=headers)
        if response is None:
            return []
        _update_feed_state(self.state, self.config.url, response)

        events: List[RawEvent] = []
        for line in response.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            raw_text = _apply_prefix(line, self.config.text_prefix)
            if not raw_text:
                continue
            source_url = line if line.startswith(("http://", "https://")) else self.config.url
            events.append(
                RawEvent(
                    event_id=new_event_id(),
                    source=self.config.name,
                    source_url=source_url,
                    fetched_at=datetime.utcnow(),
                    raw_text=raw_text,
                    raw_metadata={"indicator": line},
                )
            )
            if self._max_items() and len(events) >= self._max_items():
                break
        return events

    def _max_items(self) -> int:
        return int(self.config.max_items or 50)


def _join_parts(*parts: Optional[str]) -> str:
    cleaned = [part.strip() for part in parts if part and part.strip()]
    return "\n".join(cleaned)


def _apply_prefix(text: str, prefix: Optional[str]) -> str:
    if not text:
        return ""
    if prefix and prefix.strip():
        return f"{prefix.strip()} {text}"
    return text


def _content_from_entry(entry: Any) -> str:
    contents = entry.get("content")
    if not contents:
        return ""
    if isinstance(contents, list) and contents:
        return contents[0].get("value", "")
    if isinstance(contents, dict):
        return contents.get("value", "")
    return ""


def _extract_text(soup: BeautifulSoup, selector: Optional[str]) -> str:
    if not selector:
        return ""
    nodes = soup.select(selector)
    return " ".join(node.get_text(" ") for node in nodes)


def _extract_json_items(payload: Any, path: Optional[str]) -> List[Dict[str, Any]]:
    if not path:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            return payload.get("items", [])
        return []

    current = payload
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part, {})
        else:
            return []
    if isinstance(current, list):
        return current
    return []


def _extract_text_fields(item: Dict[str, Any], fields: Optional[List[str]]) -> str:
    if not fields:
        for key in ("text", "content", "body", "message", "title"):
            if key in item and isinstance(item[key], str):
                return item[key]
        return ""
    parts = []
    for field in fields:
        value = item.get(field)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    return "\n".join(parts)


def _extract_url(item: Dict[str, Any]) -> Optional[str]:
    for key in ("url", "link", "source_url"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _conditional_headers(state: StateStore, url: str) -> Dict[str, str]:
    etag, last_modified = state.get_feed_state(url)
    headers: Dict[str, str] = {}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    return headers


def _update_feed_state(state: StateStore, url: str, response: Any) -> None:
    etag = response.headers.get("ETag") if response else None
    last_modified = response.headers.get("Last-Modified") if response else None
    state.update_feed_state(url, etag, last_modified)
