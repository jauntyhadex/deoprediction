from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.team import Team
from app.services.team_service import TeamService
from app.utils.datetime_utils import to_utc_iso


router = APIRouter(
    prefix="/teams",
    tags=["Teams"],
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def serialize_team(
    team: Team,
    competition: Competition,
) -> dict:

    return {
        "id": team.id,
        "external_id": team.external_id,
        "name": team.name,
        "short_name": team.short_name,
        "tla": team.tla,
        "country": team.country,
        "founded": team.founded,
        "venue": team.venue,
        "website": team.website,
        "club_colors": team.club_colors,
        "logo": team.logo,
        "competition": {
            "id": competition.id,
            "external_id": (
                competition.external_id
            ),
            "code": competition.code,
            "name": competition.name,
            "country": competition.country,
            "season": competition.season,
            "emblem": competition.emblem,
        },
        "created_at": to_utc_iso(
            team.created_at
        ),
    }


@router.get("")
def get_teams(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    country: str | None = Query(
        default=None,
        max_length=100,
    ),
    competition_id: int | None = Query(
        default=None,
        ge=1,
    ),
    db: Session = Depends(get_db),
):

    total, rows = (
        TeamService(db).list_catalog(
            limit=limit,
            offset=offset,
            search=search,
            country=country,
            competition_id=(
                competition_id
            ),
        )
    )

    return {
        "count": len(rows),
        "total": total,
        "filters": {
            "limit": limit,
            "offset": offset,
            "search": search,
            "country": country,
            "competition_id": (
                competition_id
            ),
        },
        "teams": [
            serialize_team(
                team,
                competition,
            )
            for team, competition in rows
        ],
    }


@router.get("/{team_id}")
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
):

    row = TeamService(db).get_by_id(
        team_id
    )

    if row is None:

        raise HTTPException(
            status_code=404,
            detail="Team not found.",
        )

    team, competition = row

    return {
        "team": serialize_team(
            team,
            competition,
        )
    }
