from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import httpx
import pytest

from gallica.transport import Transport


def test_retries_retryable_status_and_respects_numeric_retry_after() -> None:
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "2.5"}, request=request)
        return httpx.Response(200, text="ok", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Transport(client=client, retries=1, intervals={}, sleeper=sleeps.append)
    response = transport.get("https://example.test/")

    assert response.text == "ok"
    assert attempts == 2
    assert sleeps == [2.5]


def test_retry_after_accepts_http_date() -> None:
    retry_at = datetime.now(UTC) + timedelta(seconds=30)
    request = httpx.Request("GET", "https://example.test/")
    response = httpx.Response(
        429,
        headers={"Retry-After": format_datetime(retry_at, usegmt=True)},
        request=request,
    )

    delay = Transport._retry_after(response, 0)
    assert 0 < delay <= 30


def test_retry_after_invalid_header_falls_back_to_bounded_exponential_backoff() -> None:
    request = httpx.Request("GET", "https://example.test/")
    response = httpx.Response(
        429,
        headers={"Retry-After": "definitely-not-a-date"},
        request=request,
    )

    assert Transport._retry_after(response, 0) == 1.0
    assert Transport._retry_after(response, 2) == 4.0
    assert Transport._retry_after(response, 20) == 8.0


def test_retry_after_past_http_date_never_sleeps_negative_duration() -> None:
    retry_at = datetime.now(UTC) - timedelta(seconds=30)
    request = httpx.Request("GET", "https://example.test/")
    response = httpx.Response(
        429,
        headers={"Retry-After": format_datetime(retry_at, usegmt=True)},
        request=request,
    )

    assert Transport._retry_after(response, 0) == 0.0


def test_retries_transient_transport_errors() -> None:
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise httpx.ReadTimeout("temporary timeout", request=request)
        return httpx.Response(200, text="recovered", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Transport(client=client, retries=2, intervals={}, sleeper=sleeps.append)

    assert transport.get("https://example.test/").text == "recovered"
    assert attempts == 3
    assert sleeps == [1.0, 2.0]


def test_transport_error_is_raised_after_retry_budget() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("offline", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Transport(client=client, retries=1, intervals={}, sleeper=lambda _: None)

    with pytest.raises(httpx.ConnectError):
        transport.get("https://example.test/")
    assert attempts == 2


def test_retryable_http_status_is_raised_after_retry_budget() -> None:
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Transport(client=client, retries=2, intervals={}, sleeper=sleeps.append)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        transport.get("https://example.test/")
    assert exc_info.value.response.status_code == 503
    assert attempts == 3
    assert sleeps == [1.0, 2.0]


def test_non_retryable_http_error_is_raised_immediately() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(404, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Transport(client=client, retries=5, intervals={}, sleeper=lambda _: None)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        transport.get("https://example.test/")
    assert exc_info.value.response.status_code == 404
    assert attempts == 1


def test_empty_intervals_mapping_disables_default_throttling() -> None:
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="ok", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Transport(client=client, intervals={}, sleeper=sleeps.append)
    transport.get("https://example.test/", bucket="text")
    transport.get("https://example.test/", bucket="text")

    assert sleeps == []


def test_rate_bucket_sleeps_only_for_remaining_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    ticks = iter([100.0, 102.0, 102.0, 105.0])
    monkeypatch.setattr("gallica.transport.time.monotonic", lambda: next(ticks))
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="ok", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Transport(client=client, intervals={"text": 10.0}, sleeper=sleeps.append)
    transport.get("https://example.test/", bucket="text")
    transport.get("https://example.test/", bucket="text")

    assert sleeps == [8.0]


def test_transport_constructor_rejects_invalid_settings() -> None:
    with pytest.raises(ValueError, match="timeout"):
        Transport(timeout=0)
    with pytest.raises(ValueError, match="retries"):
        Transport(retries=-1)
    with pytest.raises(ValueError, match="intervals"):
        Transport(intervals={"text": -1})
