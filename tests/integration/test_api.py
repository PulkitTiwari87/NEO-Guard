"""HTTP API over a database of SYNTHETIC / TEST DATA: success and failure paths for every endpoint."""
from __future__ import annotations

import pytest
from app.db import loader
from app.db.database import get_db
from app.db.models import Model, Prediction
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from ml.config import AU_KM, RAW_FEATURES
from tests.conftest import _make_client


def features_of(client, index=0):
    """Real input for /predict: orbital elements of a stored (synthetic) NEO."""
    neo = client.get("/api/neos", params={"per_page": 1, "page": index + 1}).json()["items"][0]
    orbital = client.get(f"/api/neos/{neo['id']}").json()["orbital_data"]
    return neo["id"], {k: orbital[k] for k in RAW_FEATURES}


# ---- health -----------------------------------------------------------------
def test_health_reports_ok_with_security_headers(client):
    r = client.get("/api/health")
    body = r.json()
    assert r.status_code == 200 and body["status"] == "ok" and body["database"] == "ok"
    assert body["version"] and body["timestamp"]
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"
    assert r.headers["x-request-id"]


def test_health_is_503_when_the_database_is_unreachable(empty_client):
    broken = create_engine("sqlite:////nonexistent-dir-neoguard/x.db")

    def unreachable():
        with Session(broken) as session:
            yield session

    empty_client.app.dependency_overrides[get_db] = unreachable
    r = empty_client.get("/api/health")
    assert r.status_code == 503
    assert r.json()["status"] == "degraded" and r.json()["database"] == "unavailable"
    assert "nonexistent" not in r.text  # no filesystem paths in responses


# ---- neos ---------------------------------------------------------------------
def test_list_defaults_and_pagination(client):
    first = client.get("/api/neos").json()
    assert first["total"] == 3000 and first["page"] == 1 and first["per_page"] == 20
    assert len(first["items"]) == 20
    second = client.get("/api/neos", params={"page": 2}).json()
    assert {i["id"] for i in first["items"]}.isdisjoint(i["id"] for i in second["items"])
    last = client.get("/api/neos", params={"page": 30, "per_page": 100}).json()
    assert len(last["items"]) == 100
    beyond = client.get("/api/neos", params={"page": 999}).json()
    assert beyond["items"] == [] and beyond["total"] == 3000


def test_hazard_filter_matches_analytics_counts(client):
    analytics = client.get("/api/analytics").json()
    yes = client.get("/api/neos", params={"is_hazardous": True, "per_page": 100}).json()
    no = client.get("/api/neos", params={"is_hazardous": False, "per_page": 100}).json()
    assert yes["total"] == analytics["hazardous_count"] > 0
    assert no["total"] == analytics["non_hazardous_count"]
    assert all(i["is_potentially_hazardous"] is True for i in yes["items"])


def test_search_is_case_insensitive_and_treats_wildcards_literally(client):
    assert client.get("/api/neos", params={"search": "TEST-00042"}).json()["total"] == 1
    assert client.get("/api/neos", params={"search": "test-00042"}).json()["total"] == 1
    assert client.get("/api/neos", params={"search": "%"}).json()["total"] == 0
    assert client.get("/api/neos", params={"search": "no-such-object"}).json()["total"] == 0


def test_sorting_and_its_whitelist(client):
    desc = client.get("/api/neos", params={"sort": "-absolute_magnitude_h", "per_page": 50}).json()["items"]
    values = [i["absolute_magnitude_h"] for i in desc]
    assert values == sorted(values, reverse=True)
    asc = client.get("/api/neos", params={"sort": "designation", "per_page": 5}).json()["items"]
    assert [i["designation"] for i in asc] == sorted(i["designation"] for i in asc)
    bad = client.get("/api/neos", params={"sort": "id; DROP TABLE neo_objects"})
    assert bad.status_code == 400 and "Unsupported sort field" in bad.json()["detail"]


@pytest.mark.parametrize("params", [{"per_page": 101}, {"per_page": 0}, {"page": 0}, {"search": "x" * 101}])
def test_invalid_query_parameters_are_422_without_echoing_input(client, params):
    r = client.get("/api/neos", params=params)
    assert r.status_code == 422
    assert all("input" not in error for error in r.json()["detail"])  # submitted values are not echoed


def test_detail_contains_orbital_data_and_time_ordered_approaches(client):
    r = client.get("/api/neos/20000000")
    body = r.json()
    assert r.status_code == 200 and body["designation"] == "TEST-00000"
    assert body["orbital_data"]["eccentricity"] > 0 and body["orbital_data"]["earth_moid_au"] is not None
    dates = [a["date"] for a in body["close_approaches"]]
    assert dates and dates == sorted(dates)
    approach = body["close_approaches"][0]
    assert approach["miss_distance_km"] == pytest.approx(approach["miss_distance_au"] * AU_KM)
    assert approach["time_scale"] == "TDB" and approach["orbiting_body"] == "Earth"


def test_approaches_endpoint(client):
    with_approaches = client.get("/api/neos/20000000/approaches").json()
    assert with_approaches["neo_id"] == 20000000 and with_approaches["approaches"]
    without = client.get("/api/neos/20002999/approaches")
    assert without.status_code == 200 and without.json()["approaches"] == []


@pytest.mark.parametrize("path, status", [
    ("/api/neos/999999999", 404), ("/api/neos/999999999/approaches", 404),
    ("/api/neos/abc", 422), ("/api/neos/0", 422), ("/api/nope", 404),
])
def test_unknown_or_malformed_ids(client, path, status):
    r = client.get(path)
    assert r.status_code == status and "detail" in r.json()


# ---- models -------------------------------------------------------------------
def test_model_list_and_detail_never_expose_filesystem_paths(client, workspace):
    listing = client.get("/api/models")
    models = listing.json()["models"]
    assert listing.status_code == 200 and len(models) == 6
    assert {m["status"] for m in models} == {"experimental"}
    assert all({"validation", "test"} <= set(m["metrics"]) for m in models)
    detail = client.get("/api/models/xgboost-v1")
    body = detail.json()
    assert detail.status_code == 200 and body["input_features"] == RAW_FEATURES
    assert len(body["features"]) == 9 and 0 < body["threshold"] < 1
    for text in (listing.text, detail.text):
        assert "artifact_path" not in text and str(workspace["artifacts_dir"]) not in text
    assert client.get("/api/models/nope-v1").status_code == 404


# ---- analytics ----------------------------------------------------------------
def test_analytics_are_computed_from_stored_data(client):
    a = client.get("/api/analytics").json()
    assert a["total_neos"] == 3000
    assert a["hazardous_count"] + a["non_hazardous_count"] + a["unknown_hazard_count"] == 3000
    assert sum(a["orbit_class_counts"].values()) == 3000
    assert sum(y["count"] for y in a["approaches_by_year"]) == a["total_approaches"] > 0
    assert a["summary"]["diameter_km"] is None  # no synthetic diameters: not invented
    assert a["summary"]["absolute_magnitude_h"]["count"] == 3000
    miss = a["summary"]["miss_distance_au"]
    assert 0 <= miss["min"] <= miss["median"] <= miss["max"] <= 0.05


def test_upcoming_close_approaches_are_real_stored_rows_sorted_ascending(client):
    a = client.get("/api/analytics").json()
    upcoming = a["upcoming_close_approaches"]
    assert 0 < len(upcoming) <= 8  # synthetic fixture spans 2020-2030; some are always "future"
    dates = [u["approach"]["date"] for u in upcoming]
    assert dates == sorted(dates)
    for u in upcoming:
        assert u["neo"]["designation"].startswith("TEST-")  # SYNTHETIC / TEST DATA, not real NEOs
        assert u["approach"]["miss_distance_au"] > 0


def test_analytics_on_an_empty_database_are_zeros_and_nulls(empty_client):
    a = empty_client.get("/api/analytics").json()
    assert a["total_neos"] == 0 and a["total_approaches"] == 0 and a["approaches_by_year"] == []
    assert a["orbit_class_counts"] == {} and all(v is None for v in a["summary"].values())
    assert a["upcoming_close_approaches"] == []
    assert empty_client.get("/api/neos").json() == {"items": [], "total": 0, "page": 1, "per_page": 20}
    assert empty_client.get("/api/models").json() == {"models": []}


# ---- predict ------------------------------------------------------------------
def best_validation_model(client):
    models = client.get("/api/models").json()["models"]
    return max(models, key=lambda m: m["metrics"]["validation"]["pr_auc"])["version"]


def test_predict_uses_the_best_validation_model_and_explains(client):
    _, feats = features_of(client)
    r = client.post("/api/predict", json={"features": feats})
    body = r.json()
    assert r.status_code == 200 and body["model_version"] == best_validation_model(client)
    assert body["model_status"] == "experimental" and body["prediction"] in (0, 1)
    assert 0 <= body["probability"] <= 1
    assert body["label"] == ("potentially_hazardous" if body["prediction"] else "not_potentially_hazardous")
    assert body["explanation"]["method"] == "SHAP" and len(body["explanation"]["contributions"]) == 9
    assert "not JPL's PHA designation" in body["disclaimer"]


def test_predict_options(client):
    _, feats = features_of(client)
    plain = client.post("/api/predict", params={"explain": False},
                        json={"features": feats, "model_version": "logistic_regression-v1"}).json()
    assert plain["model_version"] == "logistic_regression-v1" and plain["explanation"] is None


def test_predict_prefers_a_human_promoted_model(client, session_factory):
    with session_factory() as db:
        loader.set_model_status(db, "logistic_regression-v1", "validated")
    _, feats = features_of(client)
    assert client.post("/api/predict", json={"features": feats}).json()["model_version"] == \
        "logistic_regression-v1"


def test_predictions_are_stored_only_for_known_neos(client, session_factory):
    neo_id, feats = features_of(client)

    def stored():
        with session_factory() as db:
            return db.scalar(select(func.count()).select_from(Prediction))

    client.post("/api/predict", json={"features": feats})
    assert stored() == 0  # anonymous predictions are not persisted
    r = client.post("/api/predict", json={"features": feats, "neo_id": neo_id})
    assert r.status_code == 200 and stored() == 1
    assert client.post("/api/predict", json={"features": feats, "neo_id": 1}).status_code == 404
    assert stored() == 1


@pytest.mark.parametrize("mutation", [
    {"eccentricity": 1.5}, {"eccentricity": -0.1}, {"inclination_deg": 200},
    {"perihelion_distance_au": 0.001},  # inconsistent with a(1-e)
    {"perihelion_distance_au": 5.0},  # outside the NEO training domain
    {"absolute_magnitude_h": 20.0},  # not a model input (would be target leakage)
])
def test_predict_rejects_invalid_or_out_of_domain_input(client, mutation):
    _, feats = features_of(client)
    r = client.post("/api/predict", json={"features": {**feats, **mutation}})
    assert r.status_code == 422
    assert all("input" not in error for error in r.json()["detail"])  # submitted values are not echoed


def test_predict_error_responses(client):
    _, feats = features_of(client)
    assert client.post("/api/predict", json={"features": feats, "model_version": "nope-v9"}).status_code == 404
    assert client.post("/api/predict", json={}).status_code == 422
    assert client.post("/api/predict", content=b"not json",
                       headers={"Content-Type": "application/json"}).status_code == 422


def test_predict_without_any_registered_model_is_503(empty_client):
    feats = {"semi_major_axis_au": 1.2, "eccentricity": 0.5, "inclination_deg": 10.0,
             "perihelion_distance_au": 0.6, "aphelion_distance_au": 1.8,
             "ascending_node_deg": 100.0, "argument_of_perihelion_deg": 50.0}
    r = empty_client.post("/api/predict", json={"features": feats})
    assert r.status_code == 503 and r.json() == {"detail": "No trained model is available"}


def test_missing_or_escaping_artifacts_give_503_without_leaking_paths(client, session_factory, workspace):
    _, feats = features_of(client)
    with session_factory() as db:
        template = db.scalar(select(Model).where(Model.version == "xgboost-v1"))
        for version, path in (("ghost-v1", "ghost/v1"), ("evil-v1", "../../outside")):
            db.add(Model(version=version, name=version, algorithm="xgboost", artifact_path=path,
                         dataset_version="x", feature_version="features-v1", threshold=0.5,
                         created_at=template.created_at, metrics={}))
        db.commit()
    for version in ("ghost-v1", "evil-v1"):
        r = client.post("/api/predict", json={"features": feats, "model_version": version})
        assert r.status_code == 503 and r.json() == {"detail": "Model artifact unavailable"}
        assert "ghost" not in r.text and "outside" not in r.text


# ---- cross-cutting --------------------------------------------------------------
def test_unhandled_errors_return_a_generic_500(client):
    def boom():
        raise RuntimeError("secret-internal-detail /srv/private/path")

    client.app.add_api_route("/boom", boom)
    r = client.get("/boom")
    assert r.status_code == 500 and r.json() == {"detail": "Internal server error"}
    assert "secret" not in r.text and "Traceback" not in r.text


def test_cors_allows_only_configured_origins(client):
    ok = client.options("/api/neos", headers={"Origin": "http://localhost:5173",
                                              "Access-Control-Request-Method": "GET"})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"
    bad = client.options("/api/neos", headers={"Origin": "http://evil.example",
                                               "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in bad.headers


def test_rate_limit_returns_429_but_exempts_health(monkeypatch, session_factory, tmp_path):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "3")
    limited = _make_client(session_factory, tmp_path)
    codes = [limited.get("/api/models").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    blocked = limited.get("/api/models")
    assert blocked.json() == {"detail": "Rate limit exceeded"} and int(blocked.headers["retry-after"]) >= 1
    assert limited.get("/api/health").status_code == 200


def test_openapi_documents_every_endpoint(client):
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) == {
        "/api/health", "/api/neos", "/api/neos/{neo_id}", "/api/neos/{neo_id}/approaches",
        "/api/predict", "/api/models", "/api/models/{version}", "/api/analytics"}
    assert client.get("/docs").status_code == 200 and client.get("/redoc").status_code == 200
