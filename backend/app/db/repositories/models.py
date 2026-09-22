"""Model registry queries."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Model

# Auto-selection prefers vetted models. "deprecated" is never chosen automatically.
STATUS_RANK = {"production": 3, "validated": 2, "experimental": 1}


def list_models(db: Session) -> list[Model]:
    return list(db.scalars(select(Model).order_by(Model.created_at.desc(), Model.version)))


def get_by_version(db: Session, version: str) -> Model | None:
    return db.scalar(select(Model).where(Model.version == version))


def _validation_pr_auc(model: Model) -> float:
    value = ((model.metrics or {}).get("validation") or {}).get("pr_auc")
    return float(value) if value is not None else -1.0


def default_model(db: Session, pinned_version: str | None = None) -> Model | None:
    """Pinned version if configured, else best status, ties broken by validation PR-AUC."""
    if pinned_version:
        return get_by_version(db, pinned_version)
    candidates = [m for m in list_models(db) if m.status in STATUS_RANK]
    if not candidates:
        return None
    return max(candidates, key=lambda m: (STATUS_RANK[m.status], _validation_pr_auc(m)))
