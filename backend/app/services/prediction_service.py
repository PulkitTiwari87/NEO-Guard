"""Prediction orchestration: pick a registered model, load it once, predict, optionally persist."""
from __future__ import annotations

import logging
import threading
from functools import lru_cache
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFound, ServiceUnavailable
from app.db.models import Model, Prediction
from app.db.repositories import models as model_repo
from app.db.repositories import neos as neo_repo
from app.schemas.prediction import PredictRequest, PredictResponse
from ml.inference.predict import LoadedModel, load_model, predict

log = logging.getLogger(__name__)


class PredictionService:
    def __init__(self, model_dir: Path, pinned_version: str | None = None) -> None:
        self._model_dir = model_dir.resolve()
        self._pinned = pinned_version
        self._loaded: dict[str, LoadedModel] = {}
        self._lock = threading.Lock()

    def resolve_model(self, db: Session, requested: str | None) -> Model:
        if requested:
            row = model_repo.get_by_version(db, requested)
            if row is None:
                raise NotFound(f"Model version '{requested}' not found")
            return row
        row = model_repo.default_model(db, self._pinned)
        if row is None:
            raise ServiceUnavailable("No trained model is available")
        return row

    def _load(self, row: Model) -> LoadedModel:
        with self._lock:
            cached = self._loaded.get(row.version)
            if cached:
                return cached
            path = (self._model_dir / row.artifact_path).resolve()
            if not path.is_relative_to(self._model_dir):  # registry rows must stay inside MODEL_DIR
                log.error("artifact path escapes MODEL_DIR for %s", row.version)
                raise ServiceUnavailable("Model artifact unavailable")
            try:
                loaded = load_model(path)
            except Exception:  # missing files, incompatible feature schema, unpickling errors
                log.exception("failed to load model %s", row.version)
                raise ServiceUnavailable("Model artifact unavailable") from None
            self._loaded[row.version] = loaded
            return loaded

    def predict(self, db: Session, request: PredictRequest, explain: bool = True) -> PredictResponse:
        row = self.resolve_model(db, request.model_version)
        if request.neo_id is not None and neo_repo.get_neo(db, request.neo_id) is None:
            raise NotFound("NEO not found")
        features = request.features.model_dump()
        try:
            result = predict(self._load(row), features, explain=explain)
        except ServiceUnavailable:
            raise
        except Exception:
            log.exception("prediction failed for %s", row.version)
            raise ServiceUnavailable("Prediction failed") from None
        response = PredictResponse.from_result(result, row.status)
        if request.neo_id is not None:
            db.add(Prediction(
                neo_id=request.neo_id, model_version=row.version, prediction=response.prediction,
                probability=response.probability, features=features,
                explanation=response.explanation.model_dump() if response.explanation else None,
            ))
            db.commit()
        return response


@lru_cache
def get_prediction_service() -> PredictionService:
    settings = get_settings()
    return PredictionService(settings.model_dir, settings.active_model_version)
