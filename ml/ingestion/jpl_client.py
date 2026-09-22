"""HTTP client for the JPL SSD/CNEOS APIs (SBDB Query API and Close-Approach Data API).

Both APIs are public and need no API key. The client provides timeouts, bounded retries with
exponential backoff (honouring ``Retry-After``), a minimum interval between requests, and
structural validation of the JSON envelope. It never fabricates a response: on failure it
raises :class:`JPLAPIError`.
"""
from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from ml import config

log = logging.getLogger(__name__)

USER_AGENT = "NEO-Guard/0.1 (student research project; python-httpx)"
RETRY_STATUSES = {429, 500, 502, 503, 504}


class JPLAPIError(RuntimeError):
    """The JPL API could not provide a valid response."""


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: int
    content: bytes  # exact response bytes, stored verbatim as the raw snapshot
    payload: dict[str, Any]
    retrieved_at: datetime


class JPLClient:
    def __init__(
        self,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: httpx.Timeout | None = None,
        max_retries: int = 4,
        backoff_s: float = 2.0,
        min_interval_s: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = httpx.Client(
            transport=transport,
            timeout=timeout or httpx.Timeout(connect=10.0, read=180.0, write=10.0, pool=10.0),
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        self._max_retries = max_retries
        self._backoff_s = backoff_s
        self._min_interval_s = min_interval_s
        self._sleep = sleep
        self._last_request = 0.0

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> JPLClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- public API ----------------------------------------------------------
    def fetch_sbdb_neos(self) -> FetchResult:
        """All near-Earth asteroids from the SBDB Query API, at full numeric precision."""
        return self._get(config.SBDB_URL, sbdb_params())

    def fetch_close_approaches(
        self, date_min: str, date_max: str, dist_max_au: float
    ) -> FetchResult:
        """Earth close approaches of near-Earth asteroids from the CAD API."""
        return self._get(config.CAD_URL, cad_params(date_min, date_max, dist_max_au))

    # -- internals -----------------------------------------------------------
    def _get(self, url: str, params: dict[str, str]) -> FetchResult:
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            self._throttle()
            delay = self._delay(attempt)
            try:
                response = self._client.get(url, params=params)
            except httpx.TransportError as exc:  # timeouts, connection errors
                last_error = exc
                log.warning("JPL request failed (attempt %d): %s", attempt + 1, type(exc).__name__)
            else:
                if response.status_code == 200:
                    return self._parse(response)
                if response.status_code not in RETRY_STATUSES:
                    raise JPLAPIError(
                        f"JPL API returned HTTP {response.status_code}: {_message(response)}"
                    )
                last_error = JPLAPIError(f"HTTP {response.status_code}")
                log.warning("JPL API HTTP %d (attempt %d)", response.status_code, attempt + 1)
                retry_after = _retry_after(response)
                if retry_after is not None:
                    delay = retry_after
            if attempt < self._max_retries:
                self._sleep(delay)
        raise JPLAPIError(f"JPL API unavailable after {self._max_retries + 1} attempts: {last_error}")

    def _delay(self, attempt: int) -> float:
        return self._backoff_s * (2**attempt)

    def _throttle(self) -> None:
        wait = self._min_interval_s - (time.monotonic() - self._last_request)
        if wait > 0:
            self._sleep(wait)
        self._last_request = time.monotonic()

    @staticmethod
    def _parse(response: httpx.Response) -> FetchResult:
        try:
            payload = json.loads(response.content)
        except json.JSONDecodeError as exc:
            raise JPLAPIError("JPL API returned invalid JSON") from exc
        _validate_envelope(payload)
        return FetchResult(
            url=str(response.request.url),
            status=response.status_code,
            content=response.content,
            payload=payload,
            retrieved_at=datetime.now(UTC),
        )


def sbdb_params() -> dict[str, str]:
    return {
        "fields": ",".join(config.SBDB_FIELDS),
        "sb-kind": "a",  # asteroids (PHA is defined for asteroids only)
        "sb-group": "neo",  # near-Earth objects (q < 1.3 au)
        "full-prec": "true",
    }


def cad_params(date_min: str, date_max: str, dist_max_au: float) -> dict[str, str]:
    return {
        "date-min": date_min,
        "date-max": date_max,
        "dist-max": str(dist_max_au),
        "body": config.CAD_BODY,
        "nea": "true",  # near-Earth asteroids: same population as sbdb_params()
        "sort": "date",
    }


def _validate_envelope(payload: Any) -> None:
    """Check the documented response envelope: signature, fields, data, count."""
    if not isinstance(payload, dict):
        raise JPLAPIError("Unexpected JPL response: not a JSON object")
    for key in ("signature", "fields", "data", "count"):
        if key not in payload:
            raise JPLAPIError(f"Unexpected JPL response: missing '{key}'")
    if not isinstance(payload["fields"], list) or not isinstance(payload["data"], list):
        raise JPLAPIError("Unexpected JPL response: 'fields'/'data' must be lists")
    if int(payload["count"]) != len(payload["data"]):
        raise JPLAPIError(
            f"Truncated JPL response: count={payload['count']} but {len(payload['data'])} rows"
        )


def _retry_after(response: httpx.Response) -> float | None:
    value = response.headers.get("Retry-After")
    try:
        return min(float(value), 300.0) if value is not None else None
    except ValueError:
        return None


def _message(response: httpx.Response) -> str:
    try:
        return str(response.json().get("message", ""))[:200]
    except (ValueError, AttributeError):
        return response.text[:200]
