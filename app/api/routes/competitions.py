from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.services.competition_reliability_service import (
    CompetitionReliabilityService,
)
from app.services.competition_service import (
    CompetitionService,
)


router = APIRouter(
    prefix="/competitions",
    tags=["Competitions"],
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def validate_reliability_status(
    reliability_status: str | None,
) -> str | None:

    if reliability_status is None:
        return None

    normalized_status = (
        reliability_status
        .strip()
        .upper()
    )

    valid_statuses = (
        CompetitionReliabilityService
        .VALID_STATUSES
    )

    if (
        normalized_status
        not in valid_statuses
    ):

        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Invalid reliability_status."
                ),
                "valid_values": (
                    valid_statuses
                ),
            },
        )

    return normalized_status


def serialize_competition(
    competition: Competition,
    reliability_report: dict | None,
) -> dict:

    sport = competition.sport

    sport_value = getattr(
        sport,
        "value",
        str(sport),
    )

    return {
        "id": competition.id,
        "external_id": (
            competition.external_id
        ),
        "code": competition.code,
        "name": competition.name,
        "country": competition.country,
        "type": competition.type,
        "emblem": competition.emblem,
        "season": competition.season,
        "sport": sport_value,
        "reliability": (
            reliability_report
        ),
    }


@router.get("")
def get_competitions(
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    country: str | None = Query(
        default=None,
        max_length=100,
    ),
    reliability_status: str | None = Query(
        default=None,
        description=(
            "RELIABLE, PROMISING, LIMITED, "
            "WEAK, or UNVALIDATED"
        ),
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
):

    normalized_status = (
        validate_reliability_status(
            reliability_status
        )
    )

    competitions = (
        CompetitionService(db)
        .list_catalog(
            search=search,
            country=country,
        )
    )

    reliability_reports = (
        CompetitionReliabilityService(db)
        .get_reports_by_competition_id()
    )

    if normalized_status:

        competitions = [
            competition
            for competition in competitions
            if (
                reliability_reports.get(
                    competition.id,
                    {},
                ).get("status")
                == normalized_status
            )
        ]

    total = len(competitions)

    competitions = competitions[
        :limit
    ]

    return {
        "count": len(competitions),
        "total": total,
        "filters": {
            "search": search,
            "country": country,
            "reliability_status": (
                normalized_status
            ),
            "limit": limit,
        },
        "competitions": [
            serialize_competition(
                competition=competition,
                reliability_report=(
                    reliability_reports.get(
                        competition.id
                    )
                ),
            )
            for competition in competitions
        ],
    }


@router.get("/{competition_id}")
def get_competition(
    competition_id: int,
    db: Session = Depends(get_db),
):

    competition = (
        CompetitionService(db)
        .get_by_id(
            competition_id
        )
    )

    if competition is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Competition not found."
            ),
        )

    reliability_report = (
        CompetitionReliabilityService(db)
        .get_reports_by_competition_id()
        .get(competition.id)
    )

    return {
        "competition": (
            serialize_competition(
                competition=competition,
                reliability_report=(
                    reliability_report
                ),
            )
        )
    }
