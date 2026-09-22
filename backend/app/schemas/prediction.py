"""Prediction request/response schemas.

Inputs are the orbital elements the models were trained on. Ranges follow the training
population (near-Earth asteroids, bound orbits, perihelion < 1.3 au): anything outside would
be extrapolation, so it is rejected instead of silently predicted.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ml.validation.schema import REL_TOL

DISCLAIMER = (
    "Orbital-geometry-based classification score from seven orbital elements only. It is not "
    "JPL's PHA designation (which also requires absolute magnitude H and Earth MOID), not an "
    "impact-risk assessment, and not demonstrated to be a calibrated probability — treat "
    "'probability' as an uncalibrated model score (docs/EXPERIMENTS.md, calibration diagnostic)."
)


class PredictFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semi_major_axis_au: float = Field(gt=0, description="Semi-major axis a [au]")
    eccentricity: float = Field(ge=0, lt=1, description="Eccentricity e (bound orbit)")
    inclination_deg: float = Field(ge=0, le=180, description="Inclination i [deg]")
    perihelion_distance_au: float = Field(gt=0, le=1.3, description="q = a(1-e) [au]; NEO: q < 1.3")
    aphelion_distance_au: float = Field(gt=0, description="Q = a(1+e) [au]")
    ascending_node_deg: float = Field(ge=0, le=360, description="Longitude of ascending node [deg]")
    argument_of_perihelion_deg: float = Field(ge=0, le=360, description="Argument of perihelion [deg]")

    @model_validator(mode="after")
    def _consistent_orbit(self) -> PredictFeatures:
        a, e = self.semi_major_axis_au, self.eccentricity
        if abs(self.perihelion_distance_au - a * (1 - e)) > REL_TOL * self.perihelion_distance_au:
            raise ValueError("perihelion_distance_au must equal semi_major_axis_au*(1-eccentricity)")
        if abs(self.aphelion_distance_au - a * (1 + e)) > REL_TOL * self.aphelion_distance_au:
            raise ValueError("aphelion_distance_au must equal semi_major_axis_au*(1+eccentricity)")
        return self


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    features: PredictFeatures
    model_version: str | None = Field(default=None, max_length=64,
                                      description="Default: best available model")
    neo_id: int | None = Field(default=None, ge=1, le=9223372036854775807,
                               description="If given, the prediction is stored for this NEO")


class Contribution(BaseModel):
    feature: str
    value: float
    shap_value: float


class Explanation(BaseModel):
    method: Literal["SHAP"]
    output_space: Literal["log_odds", "probability"]
    base_value: float
    contributions: list[Contribution]  # sorted by |shap_value|, descending


class PredictResponse(BaseModel):
    prediction: Literal[0, 1]
    label: Literal["potentially_hazardous", "not_potentially_hazardous"]
    probability: float
    threshold: float
    model_version: str
    model_status: str
    explanation: Explanation | None
    disclaimer: str = DISCLAIMER

    @classmethod
    def from_result(cls, result: dict[str, Any], model_status: str) -> PredictResponse:
        return cls(
            prediction=result["prediction"],
            label="potentially_hazardous" if result["prediction"] else "not_potentially_hazardous",
            probability=result["probability"], threshold=result["threshold"],
            model_version=result["model_version"], model_status=model_status,
            explanation=result["explanation"],
        )
