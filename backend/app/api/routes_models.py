"""Model registry endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.db.database import get_db
from app.db.repositories import models as repo
from app.schemas.common import ErrorResponse
from app.schemas.model import ModelDetail, ModelList, ModelSummary

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=ModelList)
def list_models(db: Session = Depends(get_db)) -> ModelList:
    return ModelList(models=[ModelSummary.from_row(m) for m in repo.list_models(db)])


@router.get("/{version}", response_model=ModelDetail, responses={404: {"model": ErrorResponse}})
def get_model(version: str = Path(max_length=64), db: Session = Depends(get_db)) -> ModelDetail:
    model = repo.get_by_version(db, version)
    if model is None:
        raise NotFound("Model not found")
    return ModelDetail.from_row(model)
