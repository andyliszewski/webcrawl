"""Shared fixtures for webcrawl_mcp tests."""

from __future__ import annotations

import httpx
import pytest

from webcrawl_mcp import scraper
from webcrawl_mcp.cache import cache
from webcrawl_mcp.rate_limiter import rate_limiter


class FakeResponse:
    """Stand-in for httpx.Response — exposes only what scraper.fetch_url touches."""

    def __init__(
        self,
        status_code: int,
        text: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "http://test.local/")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError(
                f"{self.status_code}", request=request, response=response
            )


class FakeAsyncClient:
    """Pops queued FakeResponses on each .get() call."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        # Share the queue so multiple clients (one per fetch_url call) drain
        # it in order rather than each seeing an independent copy.
        self._responses = responses
        self.calls: list[str] = []

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *exc) -> bool:  # noqa: ANN001 - test code
        return False

    async def get(self, url: str, **kwargs) -> FakeResponse:  # noqa: ANN003
        self.calls.append(url)
        if not self._responses:
            raise RuntimeError("FakeAsyncClient: no more queued responses")
        return self._responses.pop(0)


@pytest.fixture
def queue_responses(monkeypatch):
    """Queue HTTP responses for scraper.fetch_url to consume in order."""

    queued: list[FakeResponse] = []

    def factory(*args, **kwargs):  # noqa: ANN002 ANN003
        return FakeAsyncClient(queued)

    monkeypatch.setattr(scraper.httpx, "AsyncClient", factory)
    return queued


@pytest.fixture
def fake_sleep(monkeypatch):
    """Replace the sleep used by scraper with a recording no-op.

    Patches scraper._async_sleep specifically (not the global asyncio.sleep)
    so other coroutines in the test process aren't affected.
    """

    durations: list[float] = []

    async def _sleep(seconds: float) -> None:
        durations.append(seconds)

    monkeypatch.setattr(scraper, "_async_sleep", _sleep)
    return durations


@pytest.fixture
def fake_firecrawl(monkeypatch):
    """Configure firecrawl behavior and capture invocations.

    Returns a control object with:
      - configured: bool flag toggling firecrawl_configured()
      - response:   str | None returned by scrape_with_firecrawl
      - calls:      list of URLs the fake was invoked with
    """

    class Control:
        configured: bool = False
        response: str | None = None
        calls: list[str] = []

    ctrl = Control()
    ctrl.calls = []

    monkeypatch.setattr(scraper, "firecrawl_configured", lambda: ctrl.configured)

    async def _scrape(url: str, timeout: int = 60) -> str | None:
        ctrl.calls.append(url)
        return ctrl.response

    monkeypatch.setattr(scraper, "scrape_with_firecrawl", _scrape)
    return ctrl


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    """Clear cache, rate limiter state, and skip rate-limit waits between tests."""

    cache.clear()
    rate_limiter._last_request.clear()
    rate_limiter._retry_after.clear()

    async def _noop_wait(url: str) -> None:
        return None

    monkeypatch.setattr(rate_limiter, "wait_if_needed", _noop_wait)
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def _reset_flags(monkeypatch):
    """Ensure each test starts with default env flags unless it overrides."""

    monkeypatch.delenv("FALLBACK_ON_TRANSPORT_ERROR", raising=False)
    monkeypatch.delenv("POLITE_MODE", raising=False)
    yield


@pytest.fixture
def stub_extract(monkeypatch):
    """Replace _extract with a deterministic stub returning a known markdown string.

    Tests can override the return value by calling stub_extract(value).
    Default returns content longer than MIN_CONTENT_LENGTH so the quality
    fallback path is not triggered.
    """

    state = {"value": "extracted body " * 30}

    def setter(value: str) -> None:
        state["value"] = value

    def _extract(html: str, url: str) -> str:
        return state["value"]

    monkeypatch.setattr(scraper, "_extract", _extract)
    return setter
