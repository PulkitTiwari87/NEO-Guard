"""Model registry schemas. The artifact path is intentionally not exposed."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.db.models import Model
from ml import config


class ModelSummary(BaseModel):
    version: str
    name: str
    algorithm: str
    status: str
    created_at: datetime  # training time
    dataset_version: str
    feature_version: str
    metrics: dict[str, Any]  # {"validation": {...}, "test": {...}}

    @classmethod
    def from_row(cls, row: Model) -> ModelSummary:
        return cls(
            version=row.version, name=row.name, algorithm=row.algorithm, status=row.status,
            created_at=row.created_at, dataset_version=row.dataset_version,
            feature_version=row.feature_version, metrics=row.metrics or {},
        )


class ModelList(BaseModel):
    models: list[ModelSummary]


class ModelDetail(ModelSummary):
    threshold: float
    features: list[str]  # engineered model inputs
    input_features: list[str] | None  # raw fields accepted by POST /api/predict
    parameters: dict[str, Any]
    split: dict[str, Any]

    @classmethod
    def from_row(cls, row: Model) -> ModelDetail:
        return cls(
            **ModelSummary.from_row(row).model_dump(),
            threshold=row.threshold, features=row.features or [],
            input_features=config.RAW_FEATURES if row.feature_version == config.FEATURE_VERSION else None,
            parameters=row.parameters or {}, split=row.split or {},
        )
