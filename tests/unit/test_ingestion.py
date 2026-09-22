"""JPL client (retry/backoff/validation) and write-once raw storage. Uses SYNTHETIC / TEST DATA."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from ml.ingestion import raw_store
from ml.ingestion.jpl_client import FetchResult, JPLAPIError, JPLClient, cad_params, sbdb_params
from tests.helpers import fetch_result, synthetic_sbdb_payload

PAYLOAD = synthetic_sbdb_payload(n=5)


def make_client(handler, **kwargs):
    sleeps: list[float] = []
    client = JPLClient(transport=httpx.MockTransport(handler), sleep=sleeps.append,
                       min_interval_s=0, **kwargs)
    return client, sleeps


def test_fetch_preserves_exact_response_bytes():
    client, _ = make_client(lambda request: httpx.Response(200, json=PAYLOAD))
    result = client.fetch_sbdb_neos()
    assert result.status == 200 and result.payload["count"] == 5
    assert json.loads(result.content) == PAYLOAD


def test_sbdb_request_uses_the_verified_query_parameters():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, json=PAYLOAD)

    make_client(handler)[0].fetch_sbdb_neos()
    assert seen["sb-kind"] == "a" and seen["sb-group"] == "neo" and seen["full-prec"] == "true"
    assert {"pha", "moid", "H", "e", "a", "q"} <= set(seen["fields"].split(","))
    assert cad_params("2000-01-01", "2100-01-01", 0.05)["nea"] == "true"


def test_retries_transient_errors_with_exponential_backoff():
    statuses = iter([503, 503, 200])
    client, sleeps = make_client(lambda request: httpx.Response(next(statuses), json=PAYLOAD))
    assert client.fetch_sbdb_neos().status == 200
    assert sleeps == [2.0, 4.0]


def test_retry_after_header_is_honoured():
    responses = iter([httpx.Response(429, headers={"Retry-After": "7"}), httpx.Response(200, json=PAYLOAD)])
    client, sleeps = make_client(lambda request: next(responses))
    client.fetch_sbdb_neos()
    assert sleeps == [7.0]


def test_gives_up_after_bounded_retries():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(503)

    client, _ = make_client(handler, max_retries=2)
    with pytest.raises(JPLAPIError, match="unavailable after 3 attempts"):
        client.fetch_sbdb_neos()
    assert len(calls) == 3


def test_client_errors_are_not_retried():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(400, json={"code": "400", "message": "bad field"})

    with pytest.raises(JPLAPIError, match="HTTP 400: bad field"):
        make_client(handler)[0].fetch_sbdb_neos()
    assert len(calls) == 1


def test_transport_errors_are_retried():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            raise httpx.ConnectTimeout("boom")
        return httpx.Response(200, json=PAYLOAD)

    assert make_client(handler)[0].fetch_sbdb_neos().status == 200
    assert len(calls) == 2


@pytest.mark.parametrize("body, message", [
    (b"<html>not json</html>", "invalid JSON"),
    (json.dumps({"signature": {}, "fields": [], "data": []}).encode(), "missing 'count'"),
    (json.dumps({"signature": {}, "fields": ["a"], "data": [[1]], "count": 9}).encode(), "Truncated"),
    (json.dumps([1, 2]).encode(), "not a JSON object"),
])
def test_malformed_responses_are_rejected(body, message):
    client, _ = make_client(lambda request: httpx.Response(200, content=body))
    with pytest.raises(JPLAPIError, match=message):
        client.fetch_sbdb_neos()


def test_snapshot_is_verbatim_with_provenance(tmp_path):
    result = fetch_result(PAYLOAD, "https://example.invalid/api?x=1")
    snap = raw_store.save_snapshot("jpl_sbdb", result, sbdb_params(), tmp_path)
    assert snap.data_path.read_bytes() == result.content
    meta = json.loads(snap.meta_path.read_text())
    assert meta["sha256"] == hashlib.sha256(result.content).hexdigest()
    assert meta["record_count"] == 5 and meta["params"] == sbdb_params()
    assert meta["endpoint"] == "https://example.invalid/api"  # query string not stored in the endpoint
    assert raw_store.load_snapshot(snap.meta_path).payload() == PAYLOAD


def test_raw_snapshots_are_write_once(tmp_path):
    result = fetch_result(PAYLOAD)
    raw_store.save_snapshot("jpl_sbdb", result, sbdb_params(), tmp_path)
    with pytest.raises(FileExistsError):
        raw_store.save_snapshot("jpl_sbdb", result, sbdb_params(), tmp_path)


def test_recent_snapshot_is_reused_only_for_identical_params(tmp_path):
    raw_store.save_snapshot("jpl_sbdb", fetch_result(PAYLOAD), sbdb_params(), tmp_path)
    hour = timedelta(hours=1)
    assert raw_store.find_recent("jpl_sbdb", sbdb_params(), hour, tmp_path) is not None
    assert raw_store.find_recent("jpl_sbdb", {**sbdb_params(), "limit": "1"}, hour, tmp_path) is None
    assert raw_store.find_recent("jpl_sbdb", sbdb_params(), timedelta(0), tmp_path) is None
    assert raw_store.find_recent("jpl_cad", sbdb_params(), hour, tmp_path) is None


def test_latest_snapshot_is_the_newest(tmp_path):
    older = datetime(2026, 1, 1, tzinfo=UTC)
    for retrieved_at in (older, older + timedelta(days=3), older + timedelta(days=1)):
        base = fetch_result(PAYLOAD)
        result = FetchResult(base.url, base.status, base.content, base.payload, retrieved_at)
        raw_store.save_snapshot("jpl_sbdb", result, sbdb_params(), tmp_path)
    latest = raw_store.latest_snapshot("jpl_sbdb", tmp_path)
    assert latest.meta["retrieved_at"].startswith("2026-01-04")
    assert raw_store.latest_snapshot("jpl_cad", tmp_path) is None
