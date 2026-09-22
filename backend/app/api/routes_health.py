"""GET /api/health — reports real dependency status (503 when the database is unreachable)."""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.db.database import get_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])
log = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse,
            responses={503: {"model": HealthResponse, "description": "Database unavailable"}})
def health(db: Session = Depends(get_db)) -> JSONResponse:
    try:
        db.execute(text("SELECT 1"))
        database_ok = True
    except Exception:  # any failure means the service cannot do its job
        log.exception("health check: database unavailable")
        database_ok = False
    body = HealthResponse(
        status="ok" if database_ok else "degraded",
        database="ok" if database_ok else "unavailable",
        version=__version__,
        timestamp=datetime.now(UTC),
    )
    return JSONResponse(body.model_dump(mode="json"), status_code=200 if database_ok else 503)
