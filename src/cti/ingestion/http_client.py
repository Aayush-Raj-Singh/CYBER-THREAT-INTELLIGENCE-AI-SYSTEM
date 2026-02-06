from __future__ import annotations

import time
from typing import Dict, Optional

import requests


class RateLimiter:
    def __init__(self, requests_per_minute: int) -> None:
        if requests_per_minute <= 0:
            self.min_interval = 0.0
        else:
            self.min_interval = 60.0 / float(requests_per_minute)
        self._last_request_ts: Optional[float] = None

    def wait(self) -> None:
        if self.min_interval <= 0:
            return
        now = time.monotonic()
        if self._last_request_ts is None:
            self._last_request_ts = now
            return
        elapsed = now - self._last_request_ts
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request_ts = time.monotonic()


class HttpClient:
    def __init__(
        self,
        user_agent: str,
        timeout_seconds: int,
        retries: int,
        backoff_seconds: float,
        rate_limiter: RateLimiter,
    ) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": user_agent})
        self._timeout = timeout_seconds
        self._retries = retries
        self._backoff_seconds = backoff_seconds
        self._rate_limiter = rate_limiter

    def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        last_exc: Optional[Exception] = None
        for attempt in range(self._retries + 1):
            self._rate_limiter.wait()
            try:
                response = self._session.get(url, params=params, headers=headers, timeout=self._timeout)
                response.raise_for_status()
                return response
            except Exception as exc:  # noqa: BLE001 - controlled retry for OSINT endpoints
                last_exc = exc
                if attempt < self._retries:
                    time.sleep(self._backoff_seconds * (attempt + 1))
        if last_exc:
            raise last_exc
        raise RuntimeError("HTTP client failed without exception")
