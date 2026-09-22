"""NEO explorer endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.db.database import get_db
from app.db.repositories import neos as repo
from app.schemas.common import ErrorResponse
from app.schemas.neo import Approach, ApproachList, NeoDetail, NeoList, NeoSummary

router = APIRouter(prefix="/neos", tags=["neos"])
NeoId = Path(ge=1, le=9223372036854775807, description="JPL SPK-ID")
SORT_HELP = "Field; prefix '-' for descending. One of: " + ", ".join(sorted(repo.SORT_FIELDS))


@router.get("", response_model=NeoList, responses={400: {"model": ErrorResponse}})
def list_neos(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=repo.MAX_PER_PAGE),
    is_hazardous: bool | None = Query(None, description="Filter on JPL's PHA flag"),
    search: str | None = Query(None, max_length=100, description="Substring of designation or name"),
    sort: str = Query("id", description=SORT_HELP),
    db: Session = Depends(get_db),
) -> NeoList:
    rows, total = repo.list_neos(db, page=page, per_page=per_page, is_hazardous=is_hazardous,
                                 search=search, sort=sort)
    return NeoList(items=[NeoSummary.model_validate(r) for r in rows], total=total,
                   page=page, per_page=per_page)


@router.get("/{neo_id}", response_model=NeoDetail, responses={404: {"model": ErrorResponse}})
def get_neo(neo_id: int = NeoId, db: Session = Depends(get_db)) -> NeoDetail:
    neo = repo.get_neo(db, neo_id)
    if neo is None:
        raise NotFound("NEO not found")
    return NeoDetail.build(neo, repo.list_approaches(db, neo_id))


@router.get("/{neo_id}/approaches", response_model=ApproachList,
            responses={404: {"model": ErrorResponse}})
def get_approaches(neo_id: int = NeoId, db: Session = Depends(get_db)) -> ApproachList:
    if repo.get_neo(db, neo_id) is None:
        raise NotFound("NEO not found")
    return ApproachList(neo_id=neo_id,
                        approaches=[Approach.from_row(a) for a in repo.list_approaches(db, neo_id)])
