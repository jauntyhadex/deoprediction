from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.fixture import Fixture
from app.models.team import Team
from app.services.fixture_service import FixtureService
from app.utils.datetime_utils import to_utc_iso
from app.utils.fixture_status_utils import (
    VALID_FIXTURE_STATUSES,
)


router = APIRouter(
    prefix="/fixtures",
    tags=["Fixtures"],
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def normalize_datetime(
    value: datetime | None,
) -> datetime | None:

    if value is None:
        return None

    if value.tzinfo is None:
        return value

    return value.astimezone(
        UTC
    ).replace(
        tzinfo=None
    )


def validate_date_range(
    date_from: datetime | None,
    date_to: datetime | None,
) -> tuple[
    datetime | None,
    datetime | None,
]:

    normalized_from = normalize_datetime(
        date_from
    )

    normalized_to = normalize_datetime(
        date_to
    )

    if (
        normalized_from is not None
        and normalized_to is not None
        and normalized_to
        < normalized_from
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "date_to must be greater than "
                "or equal to date_from."
            ),
        )

    return normalized_from, normalized_to


def validate_status(
    status: str | None,
) -> str | None:

    if status is None:
        return None

    normalized_status = (
        status.strip().upper()
    )

    if (
        normalized_status
        not in VALID_FIXTURE_STATUSES
    ):

        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Invalid fixture status."
                ),
                "valid_values": sorted(
                    VALID_FIXTURE_STATUSES
                ),
            },
        )

    return normalized_status


def serialize_team(
    team: Team,
) -> dict:

    return {
        "id": team.id,
        "external_id": team.external_id,
        "name": team.name,
        "short_name": team.short_name,
        "tla": team.tla,
        "country": team.country,
        "logo": team.logo,
    }


def serialize_fixture(
    fixture: Fixture,
    competition: Competition,
    home_team: Team,
    away_team: Team,
) -> dict:

    return {
        "id": fixture.id,
        "api_fixture_id": (
            fixture.api_fixture_id
        ),
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
        "home_team": serialize_team(
            home_team
        ),
        "away_team": serialize_team(
            away_team
        ),
        "season": fixture.season,
        "venue": fixture.venue,
        "status": fixture.status,
        "kickoff_time": to_utc_iso(
            fixture.kickoff_time
        ),
        "score": {
            "home": fixture.home_score,
            "away": fixture.away_score,
        },
        "created_at": to_utc_iso(
            fixture.created_at
        ),
        "updated_at": to_utc_iso(
            fixture.updated_at
        ),
    }


@router.get("")
def get_fixtures(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    upcoming_only: bool = Query(
        default=True,
    ),
    days_ahead: int | None = Query(
        default=30,
        ge=1,
        le=730,
    ),
    date_from: datetime | None = Query(
        default=None,
    ),
    date_to: datetime | None = Query(
        default=None,
    ),
    competition_id: int | None = Query(
        default=None,
        ge=1,
    ),
    team_id: int | None = Query(
        default=None,
        ge=1,
    ),
    status: str | None = Query(
        default=None,
    ),
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    db: Session = Depends(get_db),
):

    (
        normalized_date_from,
        normalized_date_to,
    ) = validate_date_range(
        date_from,
        date_to,
    )

    normalized_status = validate_status(
        status
    )

    total, rows = (
        FixtureService(db).list_catalog(
            limit=limit,
            offset=offset,
            upcoming_only=upcoming_only,
            days_ahead=days_ahead,
            date_from=normalized_date_from,
            date_to=normalized_date_to,
            competition_id=competition_id,
            team_id=team_id,
            status=normalized_status,
            search=search,
        )
    )

    return {
        "count": len(rows),
        "total": total,
        "filters": {
            "limit": limit,
            "offset": offset,
            "upcoming_only": upcoming_only,
            "days_ahead": days_ahead,
            "date_from": to_utc_iso(
                normalized_date_from
            ),
            "date_to": to_utc_iso(
                normalized_date_to
            ),
            "competition_id": competition_id,
            "team_id": team_id,
            "status": normalized_status,
            "search": search,
        },
        "fixtures": [
            serialize_fixture(
                fixture,
                competition,
                home_team,
                away_team,
            )
            for (
                fixture,
                competition,
                home_team,
                away_team,
            ) in rows
        ],
    }


@router.get("/{fixture_id}")
def get_fixture(
    fixture_id: int,
    db: Session = Depends(get_db),
):

    row = FixtureService(db).get_by_id(
        fixture_id
    )

    if row is None:

        raise HTTPException(
            status_code=404,
            detail="Fixture not found.",
        )

    (
        fixture,
        competition,
        home_team,
        away_team,
    ) = row

    return {
        "fixture": serialize_fixture(
            fixture,
            competition,
            home_team,
            away_team,
        )
    }
