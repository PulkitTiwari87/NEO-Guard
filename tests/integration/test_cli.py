"""Every documented CLI entry point, end to end, on SYNTHETIC / TEST DATA in temp directories.

JPL is replaced by a mock HTTP transport and ``ml.config`` paths point at a sandbox, so this never
touches the network, ``data/`` or ``ml/artifacts/``.
"""
from __future__ import annotations

import httpx
import pytest
from app import cli as db_cli
from app.core.config import get_settings
from app.db.database import get_engine, get_session_factory
from app.db.models import Base, CloseApproach, Experiment, Model, NeoObject
from sqlalchemy import func, select

from ml import config
from ml.evaluation.__main__ import main as evaluation_main
from ml.explainability.__main__ import main as explainability_main
from ml.ingestion import __main__ as ingestion_cli
from ml.ingestion.jpl_client import JPLClient
from ml.preprocessing.__main__ import main as preprocessing_main
from ml.training.__main__ import main as training_main
from ml.validation.__main__ import main as validation_main
from tests.helpers import synthetic_cad_payload, synthetic_sbdb_payload

SBDB = synthetic_sbdb_payload(n=1500)
CAD = synthetic_cad_payload(SBDB, n_objects=100)


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    for name in ("raw", "interim", "processed", "artifacts"):
        (tmp_path / name).mkdir()
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(config, "INTERIM_DIR", tmp_path / "interim")
    monkeypatch.setattr(config, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(config, "ARTIFACTS_DIR", tmp_path / "artifacts")
    log = tmp_path / "EXPERIMENTS.md"
    log.write_text("# Experiments Log (SYNTHETIC / TEST DATA)\n", encoding="utf-8")
    monkeypatch.setattr(config, "EXPERIMENTS_DOC", log)
    return tmp_path


def fake_jpl(monkeypatch, status: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        if status != 200:
            return httpx.Response(status)
        return httpx.Response(200, json=SBDB if "sbdb_query" in request.url.path else CAD)

    monkeypatch.setattr(ingestion_cli, "JPLClient", lambda: JPLClient(
        transport=httpx.MockTransport(handler), sleep=lambda s: None, min_interval_s=0, max_retries=1))


def raw_files(sandbox):
    return sorted((sandbox / "raw").rglob("*.json"))


def test_ingestion_fetches_then_reuses_the_cache(sandbox, monkeypatch, capsys):
    fake_jpl(monkeypatch)
    assert ingestion_cli.main([]) == 0
    first = raw_files(sandbox)
    assert len(first) == 4  # 2 snapshots + 2 metadata files
    assert "[fetched] jpl_sbdb: 1500 records" in capsys.readouterr().out
    assert ingestion_cli.main([]) == 0
    assert raw_files(sandbox) == first  # cache hit: no new raw files
    assert "[cache]" in capsys.readouterr().out


def test_ingestion_fails_loudly_when_jpl_is_unavailable(sandbox, monkeypatch, capsys):
    fake_jpl(monkeypatch, status=503)
    assert ingestion_cli.main(["--source", "sbdb"]) == 1
    assert "INGESTION FAILED" in capsys.readouterr().err
    assert raw_files(sandbox) == []  # nothing is fabricated or half-written


def test_pipeline_stages_report_missing_inputs_instead_of_crashing(sandbox, capsys):
    stages = (validation_main, preprocessing_main, lambda: training_main([]), lambda: evaluation_main([]))
    assert [stage() for stage in stages] == [1, 1, 1, 1]
    assert capsys.readouterr().err.count("FAILED") == 4


def test_full_pipeline_and_database_clis(sandbox, monkeypatch, capsys):
    fake_jpl(monkeypatch)
    assert ingestion_cli.main([]) == 0
    assert validation_main() == 0
    assert preprocessing_main() == 0
    assert training_main(["--algorithms", "logistic_regression", "--class-weight", "none"]) == 0
    assert evaluation_main([]) == 0
    assert explainability_main([]) == 0
    out = capsys.readouterr().out
    assert "logistic_regression-v1" in out and "PHA rule audit" in out

    version = sandbox / "artifacts" / "logistic_regression" / "v1"
    assert {p.name for p in version.iterdir()} >= {
        "model.joblib", "metadata.json", "evaluation.json", "shap_global.json"}
    assert "### EXP-" in config.EXPERIMENTS_DOC.read_text(encoding="utf-8")

    # database CLI on a throwaway SQLite file
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{sandbox / 'cli.db'}")
    get_settings.cache_clear()
    get_engine.cache_clear()
    try:
        Base.metadata.create_all(get_engine())
        assert db_cli.main(["load-data"]) == 0
        assert db_cli.main(["sync-models"]) == 0
        assert db_cli.main(["set-status", "logistic_regression-v1", "validated"]) == 0
        assert db_cli.main(["set-status", "ghost-v1", "validated"]) == 1
        with get_session_factory()() as db:
            assert db.scalar(select(func.count()).select_from(NeoObject)) == 1500
            assert db.scalar(select(func.count()).select_from(CloseApproach)) > 0
            assert db.scalar(select(func.count()).select_from(Experiment)) == 1
            status = db.scalar(select(Model.status).where(Model.version == "logistic_regression-v1"))
            assert status == "validated"
    finally:
        get_engine().dispose()
        get_settings.cache_clear()
        get_engine.cache_clear()
