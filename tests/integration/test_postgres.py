"""PostgreSQL-specific behaviour: Alembic migration from scratch, JSONB, upserts, analytics.

Skipped unless TEST_DATABASE_URL points at a DEDICATED, disposable PostgreSQL database
(the test drops every table in it). It never uses DATABASE_URL, so it cannot touch dev data.
Example: TEST_DATABASE_URL=postgresql://user:pw@127.0.0.1:55432/neoguard_test pytest -m postgres
"""
from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import REPO_ROOT, get_settings
from app.db import loader
from app.db.models import CloseApproach, NeoObject
from app.services.analytics_service import compute_analytics
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.orm import Session

from ml import artifacts

pytestmark = pytest.mark.postgres
TABLES = {"data_sources", "neo_objects", "close_approaches", "predictions", "models", "experiments"}


@pytest.fixture
def pg(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set")
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    cfg = Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    command.downgrade(cfg, "base")  # clean slate (dedicated test database only)
    yield cfg
    command.downgrade(cfg, "base")
    get_settings.cache_clear()


def test_migration_builds_the_schema_and_is_reversible(pg):
    command.upgrade(pg, "head")
    engine = create_engine(get_settings().sqlalchemy_url)
    assert TABLES <= set(inspect(engine).get_table_names())
    with engine.connect() as conn:
        types = {row[0]: row[1] for row in conn.execute(text(
            "select column_name, data_type from information_schema.columns where table_name='models'"))}
    assert types["metrics"] == "jsonb" and types["created_at"] == "timestamp with time zone"
    command.downgrade(pg, "base")
    assert not TABLES & set(inspect(engine).get_table_names())
    engine.dispose()


def test_loader_and_analytics_on_postgres(pg, workspace):
    command.upgrade(pg, "head")
    engine = create_engine(get_settings().sqlalchemy_url)
    n_cad = workspace["report"]["close_approaches"]["valid"]
    with Session(engine) as db:
        first = loader.load_interim(db, workspace["interim_dir"])
        second = loader.load_interim(db, workspace["interim_dir"])
        assert first["neo_objects"]["inserted"] == 3000 and second["neo_objects"]["updated"] == 3000
        assert db.scalar(select(func.count()).select_from(NeoObject)) == 3000
        assert db.scalar(select(func.count()).select_from(CloseApproach)) == n_cad
        items = artifacts.list_artifacts(workspace["artifacts_dir"])
        assert loader.sync_models(db, items) == {"added": 6, "updated": 0}
        assert loader.sync_models(db, items) == {"added": 0, "updated": 6}
        analytics = compute_analytics(db)
        assert analytics.total_neos == 3000 and analytics.total_approaches == n_cad
        assert sum(y.count for y in analytics.approaches_by_year) == n_cad
        metrics = db.execute(text("select metrics->'validation'->>'pr_auc' from models limit 1")).scalar()
        assert float(metrics) >= 0  # JSONB path queries work
    engine.dispose()
