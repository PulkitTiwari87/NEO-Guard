"""Analytics schemas. Every value is computed from stored data; empty data yields zeros/nulls."""
from __future__ import annotations

from pydantic import BaseModel

from app.schemas.neo import Approach, NeoSummary


class NumericSummary(BaseModel):
    count: int
    min: float
    max: float
    mean: float
    median: float


class YearCount(BaseModel):
    year: int
    count: int


class AnalyticsSummary(BaseModel):
    diameter_km: NumericSummary | None
    absolute_magnitude_h: NumericSummary | None
    relative_velocity_km_s: NumericSummary | None
    miss_distance_au: NumericSummary | None


class UpcomingApproach(BaseModel):
    """A real, stored close approach with its NEO's identity attached."""

    neo: NeoSummary
    approach: Approach


class AnalyticsResponse(BaseModel):
    total_neos: int
    hazardous_count: int
    non_hazardous_count: int
    unknown_hazard_count: int  # PHA flag unavailable (no Earth MOID)
    total_approaches: int
    orbit_class_counts: dict[str, int]
    approaches_by_year: list[YearCount]
    summary: AnalyticsSummary
    # Soonest stored approaches at/after "now" (TDB treated as UTC; offset is under two
    # minutes and immaterial at this granularity). Empty on a database with no future rows.
    upcoming_close_approaches: list[UpcomingApproach]
