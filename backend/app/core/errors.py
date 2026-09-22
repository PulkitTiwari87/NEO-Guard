"""Structured API errors. Clients only ever see ``{"detail": ...}``; details go to the log."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

log = logging.getLogger(__name__)


class ApiError(Exception):
    status_code = 500

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class BadRequest(ApiError):
    status_code = 400


class NotFound(ApiError):
    status_code = 404


class ServiceUnavailable(ApiError):
    status_code = 503


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
        return JSONResponse({"detail": errors}, status_code=422)  # no echo of submitted input

    @app.exception_handler(OperationalError)
    async def _database_down(_: Request, exc: OperationalError) -> JSONResponse:
        log.error("database unavailable", exc_info=exc)
        return JSONResponse({"detail": "Database unavailable"}, status_code=503)

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled error", exc_info=exc)
        return JSONResponse({"detail": "Internal server error"}, status_code=500)
