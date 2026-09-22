"""NEO and close-approach queries."""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import BadRequest
from app.db.models import CloseApproach, NeoObject

MAX_PER_PAGE = 100
SORT_FIELDS = {
    "id", "designation", "name", "absolute_magnitude_h", "diameter_km", "semi_major_axis_au",
    "eccentricity", "inclination_deg", "earth_moid_au", "first_obs_year",
}


def parse_sort(sort: str) -> tuple[str, bool]:
    """``"-field"`` sorts descending. Only whitelisted fields are accepted."""
    descending = sort.startswith("-")
    field = sort.lstrip("-+")
    if field not in SORT_FIELDS:
        raise BadRequest(f"Unsupported sort field '{field}'. Allowed: {sorted(SORT_FIELDS)}")
    return field, descending


def list_neos(
    db: Session,
    *,
    page: int,
    per_page: int,
    is_hazardous: bool | None,
    search: str | None,
    sort: str,
) -> tuple[list[NeoObject], int]:
    field, descending = parse_sort(sort)
    stmt = select(NeoObject)
    if is_hazardous is not None:
        stmt = stmt.where(NeoObject.is_potentially_hazardous.is_(is_hazardous))
    if search and search.strip():
        term = search.strip()
        stmt = stmt.where(or_(
            NeoObject.designation.icontains(term, autoescape=True),
            NeoObject.full_name.icontains(term, autoescape=True),
            NeoObject.name.icontains(term, autoescape=True),
        ))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    column = getattr(NeoObject, field)
    order = column.desc().nulls_last() if descending else column.asc().nulls_last()
    rows = db.scalars(
        stmt.order_by(order, NeoObject.id).offset((page - 1) * per_page).limit(per_page)
    ).all()
    return list(rows), total


def get_neo(db: Session, neo_id: int) -> NeoObject | None:
    return db.get(NeoObject, neo_id)


def list_approaches(db: Session, neo_id: int) -> list[CloseApproach]:
    return list(db.scalars(
        select(CloseApproach)
        .where(CloseApproach.neo_id == neo_id)
        .order_by(CloseApproach.approach_time_tdb)
    ))
