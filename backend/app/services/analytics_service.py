"""Aggregate statistics computed from stored data (no fabricated values on an empty database)."""
from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
from sqlalchemy import Column, func, select
from sqlalchemy.orm import Session

from app.db.models import CloseApproach, NeoObject
from app.schemas.analytics import (
    AnalyticsResponse,
    AnalyticsSummary,
    NumericSummary,
    UpcomingApproach,
    YearCount,
)
from app.schemas.neo import Approach, NeoSummary

UPCOMING_APPROACHES_LIMIT = 8


def _summary(db: Session, column: Column) -> NumericSummary | None:
    values = np.asarray(db.scalars(select(column).where(column.is_not(None))).all(), dtype=float)
    if values.size == 0:
        return None
    return NumericSummary(count=int(values.size), min=float(values.min()), max=float(values.max()),
                          mean=float(values.mean()), median=float(np.median(values)))


def _count(db: Session, *conditions) -> int:
    return db.scalar(select(func.count()).select_from(NeoObject).where(*conditions)) or 0


def _upcoming_approaches(db: Session, limit: int = UPCOMING_APPROACHES_LIMIT) -> list[UpcomingApproach]:
    now = datetime.now(UTC).replace(tzinfo=None)  # approach_time_tdb is stored naive (TDB)
    rows = db.execute(
        select(CloseApproach, NeoObject)
        .join(NeoObject, CloseApproach.neo_id == NeoObject.id)
        .where(CloseApproach.approach_time_tdb >= now)
        .order_by(CloseApproach.approach_time_tdb.asc())
        .limit(limit)
    ).all()
    return [
        UpcomingApproach(neo=NeoSummary.model_validate(neo), approach=Approach.from_row(ca))
        for ca, neo in rows
    ]


def compute_analytics(db: Session) -> AnalyticsResponse:
    year = func.extract("year", CloseApproach.approach_time_tdb)
    by_year = db.execute(select(year, func.count()).group_by(year).order_by(year)).all()
    by_class = db.execute(
        select(NeoObject.orbit_class, func.count()).group_by(NeoObject.orbit_class)).all()
    return AnalyticsResponse(
        total_neos=_count(db),
        hazardous_count=_count(db, NeoObject.is_potentially_hazardous.is_(True)),
        non_hazardous_count=_count(db, NeoObject.is_potentially_hazardous.is_(False)),
        unknown_hazard_count=_count(db, NeoObject.is_potentially_hazardous.is_(None)),
        total_approaches=db.scalar(select(func.count()).select_from(CloseApproach)) or 0,
        orbit_class_counts={cls: n for cls, n in by_class},
        approaches_by_year=[YearCount(year=int(y), count=n) for y, n in by_year],
        summary=AnalyticsSummary(
            diameter_km=_summary(db, NeoObject.diameter_km),
            absolute_magnitude_h=_summary(db, NeoObject.absolute_magnitude_h),
            relative_velocity_km_s=_summary(db, CloseApproach.v_rel_km_s),
            miss_distance_au=_summary(db, CloseApproach.distance_au),
        ),
        upcoming_close_approaches=_upcoming_approaches(db),
    )
