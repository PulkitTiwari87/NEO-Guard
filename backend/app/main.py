"""FastAPI application factory."""
from __future__ import annotations

import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import routes_analytics, routes_health, routes_models, routes_neos, routes_prediction
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.security import RateLimitMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.db import loader
from app.db.database import get_session_factory
from ml import artifacts

log = logging.getLogger(__name__)


def _load_data_and_models() -> None:
    """Idempotent data/model sync, run off the request-serving startup path.

    Alembic's schema migration blocks container startup (fast, required before any query),
    but the data load (42k+ rows) and model sync run here in the background so the process
    binds its port immediately — Render's deploy port-scan times out well before a full load
    finishes.
    """
    try:
        with get_session_factory()() as db:
            loader.load_interim(db)
            loader.sync_models(db, artifacts.list_artifacts())
    except Exception:
        log.exception("background data/model sync failed")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    threading.Thread(target=_load_data_and_models, daemon=True).start()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title="NEO-Guard API",
        version=__version__,
        description=(
            "Near-Earth asteroid data from NASA/JPL (SBDB, CAD) and explainable ML classification "
            "of JPL's PHA flag from orbital elements. Model outputs are statistical estimates."
        ),
        lifespan=lifespan,
    )
    # Last added = outermost: CORS -> request logging -> security headers -> rate limit -> app.
    app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_origin_list, allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"], allow_credentials=False,
    )
    register_exception_handlers(app)

    api = APIRouter(prefix="/api")
    for module in (routes_health, routes_neos, routes_prediction, routes_models, routes_analytics):
        api.include_router(module.router)
    app.include_router(api)
    return app


app = create_app()
