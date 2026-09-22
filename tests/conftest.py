"""Shared fixtures. All data here is SYNTHETIC / TEST DATA (see tests/helpers.py).

Environment is forced BEFORE the app is imported so tests can never touch the developer's
database or a real .env: they run on in-memory SQLite (PostgreSQL only when TEST_DATABASE_URL
is set, in tests/integration/test_postgres.py).
"""
from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["MODEL_ENV"] = "test"
os.environ["RATE_LIMIT_PER_MINUTE"] = "0"
os.environ.pop("ACTIVE_MODEL_VERSION", None)

import pytest  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db import loader  # noqa: E402
from app.db.database import get_db  # noqa: E402
from app.db.models import Base  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.prediction_service import PredictionService, get_prediction_service  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from ml import artifacts  # noqa: E402
from tests import helpers  # noqa: E402


@pytest.fixture(scope="session")
def workspace(tmp_path_factory):
    """Synthetic raw -> interim -> processed -> trained/evaluated/explained artifacts (built once)."""
    return helpers.build_workspace(tmp_path_factory.mktemp("neoguard_synthetic"))


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


def _make_client(session_factory, model_dir) -> TestClient:
    get_settings.cache_clear()
    app = create_app()

    def _db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_prediction_service] = lambda: PredictionService(model_dir)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client(session_factory, workspace):
    """API client over a database loaded with the synthetic data and registered models."""
    with session_factory() as db:
        loader.load_interim(db, workspace["interim_dir"])
        loader.sync_models(db, artifacts.list_artifacts(workspace["artifacts_dir"]))
    return _make_client(session_factory, workspace["artifacts_dir"])


@pytest.fixture
def empty_client(session_factory, tmp_path):
    """API client over an empty database (no NEOs, no models)."""
    return _make_client(session_factory, tmp_path)
