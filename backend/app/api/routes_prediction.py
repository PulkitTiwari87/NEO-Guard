"""POST /api/predict."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.prediction import PredictRequest, PredictResponse
from app.services.prediction_service import PredictionService, get_prediction_service

router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=PredictResponse,
             responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
def predict(
    request: PredictRequest,
    explain: bool = Query(True, description="Include the SHAP explanation"),
    db: Session = Depends(get_db),
    service: PredictionService = Depends(get_prediction_service),
) -> PredictResponse:
    return service.predict(db, request, explain=explain)
