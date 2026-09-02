from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from typing import Any

import httpx

_RETRYABLE = {429, 500, 502, 503, 504}


class Transport:
    """Small synchronous HTTP transport with bounded retries and rate buckets."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout: float = 60.0,
        retries: int = 3,
        intervals: Mapping[str, float] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "gallica-sdk/0.1.0.dev0 (+https://github.com/maribakulj/gallica-sdk)",
                "Accept": "*/*",
            },
        )
        self._retries = retries
        self._intervals = dict(
            intervals
            or {
                "default": 0.0,
                "text": 12.5,
                "pdf": 15.5,
                "iiif_hd": 12.5,
            }
        )
        self._last_call: dict[str, float] = {}
        self._sleep = sleeper

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _throttle(self, bucket: str) -> None:
        interval = self._intervals.get(bucket, self._intervals.get("default", 0.0))
        last = self._last_call.get(bucket)
        if last is not None and interval > 0:
            remaining = interval - (time.monotonic() - last)
            if remaining > 0:
                self._sleep(remaining)
        self._last_call[bucket] = time.monotonic()

    @staticmethod
    def _retry_after(response: httpx.Response, attempt: int) -> float:
        raw = response.headers.get("Retry-After")
        if raw is not None:
            try:
                return max(0.0, float(raw))
            except ValueError:
                pass
        return min(2.0**attempt, 8.0)

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        bucket: str = "default",
    ) -> httpx.Response:
        last_response: httpx.Response | None = None
        for attempt in range(self._retries + 1):
            self._throttle(bucket)
            response = self._client.get(url, params=params)
            last_response = response
            if response.status_code not in _RETRYABLE:
                response.raise_for_status()
                return response
            if attempt < self._retries:
                self._sleep(self._retry_after(response, attempt))
        assert last_response is not None
        last_response.raise_for_status()
        raise RuntimeError("unreachable")
