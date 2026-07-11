from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.services.competition_reliability_service import (
    CompetitionReliabilityService,
)
from app.services.prediction_market_service import (
    PredictionMarketService,
)
from app.services.prediction_pick_service import (
    PredictionPickService,
)


router = APIRouter(
    prefix="/prediction-picks",
    tags=["Prediction Picks"],
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def validate_competition_status(
    competition_status: str | None,
) -> str | None:

    if competition_status is None:
        return None

    normalized_status = (
        competition_status.upper()
    )

    if (
        normalized_status
        not in (
            CompetitionReliabilityService
            .VALID_STATUSES
        )
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Invalid competition_status."
                ),
                "valid_values": (
                    CompetitionReliabilityService
                    .VALID_STATUSES
                ),
            },
        )

    return normalized_status


@router.get("/top")
def get_top_prediction_picks(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    minimum_grade: str | None = Query(
        default=None,
    ),
    upcoming_only: bool = Query(
        default=True,
    ),
    days_ahead: int | None = Query(
        default=30,
        ge=1,
        le=730,
    ),
    competition_id: int | None = Query(
        default=None,
        ge=1,
    ),
    competition_status: str | None = Query(
        default=None,
        description=(
            "RELIABLE, PROMISING, LIMITED, "
            "WEAK, or UNVALIDATED"
        ),
    ),
    market_type: str | None = Query(
        default=None,
    ),
    minimum_fair_odds: float = Query(
        default=1.15,
        ge=1.0,
        le=100.0,
    ),
    maximum_fair_odds: float = Query(
        default=8.0,
        ge=1.0,
        le=100.0,
    ),
    minimum_probability: float = Query(
        default=0.0,
        ge=0.0,
        le=100.0,
    ),
    one_per_fixture: bool = Query(
        default=True,
    ),
    db: Session = Depends(get_db),
):

    if maximum_fair_odds < minimum_fair_odds:

        raise HTTPException(
            status_code=400,
            detail=(
                "maximum_fair_odds must be "
                "greater than or equal to "
                "minimum_fair_odds."
            ),
        )

    normalized_status = (
        validate_competition_status(
            competition_status
        )
    )

    service = PredictionPickService(db)

    picks = service.get_top_picks(
        limit=limit,
        minimum_grade=minimum_grade,
        upcoming_only=upcoming_only,
        days_ahead=days_ahead,
        competition_id=competition_id,
        competition_status=(
            normalized_status
        ),
        market_type=market_type,
        minimum_fair_odds=minimum_fair_odds,
        maximum_fair_odds=maximum_fair_odds,
        minimum_probability=minimum_probability,
        one_per_fixture=one_per_fixture,
    )

    return {
        "count": len(picks),
        "filters": {
            "upcoming_only": upcoming_only,
            "days_ahead": days_ahead,
            "competition_id": competition_id,
            "competition_status": (
                normalized_status
            ),
            "market_type": market_type,
            "minimum_grade": minimum_grade,
            "minimum_fair_odds": (
                minimum_fair_odds
            ),
            "maximum_fair_odds": (
                maximum_fair_odds
            ),
            "minimum_probability": (
                minimum_probability
            ),
            "one_per_fixture": (
                one_per_fixture
            ),
        },
        "picks": picks,
    }


@router.get("/markets/top")
def get_top_prediction_markets(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    upcoming_only: bool = Query(
        default=True,
    ),
    days_ahead: int | None = Query(
        default=30,
        ge=1,
        le=730,
    ),
    competition_id: int | None = Query(
        default=None,
        ge=1,
    ),
    competition_status: str | None = Query(
        default=None,
        description=(
            "RELIABLE, PROMISING, LIMITED, "
            "WEAK, or UNVALIDATED"
        ),
    ),
    market_type: str | None = Query(
        default=None,
    ),
    selection: str | None = Query(
        default=None,
    ),
    minimum_fair_odds: float = Query(
        default=1.15,
        ge=1.0,
        le=100.0,
    ),
    maximum_fair_odds: float = Query(
        default=8.0,
        ge=1.0,
        le=100.0,
    ),
    minimum_probability: float = Query(
        default=0.0,
        ge=0.0,
        le=100.0,
    ),
    minimum_market_confidence: float = Query(
        default=0.0,
        ge=0.0,
        le=100.0,
    ),
    one_per_fixture: bool = Query(
        default=True,
    ),
    db: Session = Depends(get_db),
):

    if maximum_fair_odds < minimum_fair_odds:

        raise HTTPException(
            status_code=400,
            detail=(
                "maximum_fair_odds must be "
                "greater than or equal to "
                "minimum_fair_odds."
            ),
        )

    normalized_status = (
        validate_competition_status(
            competition_status
        )
    )

    service = PredictionMarketService(db)

    markets = service.get_top_markets(
        limit=limit,
        upcoming_only=upcoming_only,
        days_ahead=days_ahead,
        competition_id=competition_id,
        competition_status=(
            normalized_status
        ),
        market_type=market_type,
        selection=selection,
        minimum_fair_odds=minimum_fair_odds,
        maximum_fair_odds=maximum_fair_odds,
        minimum_probability=minimum_probability,
        minimum_market_confidence=(
            minimum_market_confidence
        ),
        one_per_fixture=one_per_fixture,
    )

    return {
        "count": len(markets),
        "filters": {
            "upcoming_only": upcoming_only,
            "days_ahead": days_ahead,
            "competition_id": competition_id,
            "competition_status": (
                normalized_status
            ),
            "market_type": market_type,
            "selection": selection,
            "minimum_fair_odds": (
                minimum_fair_odds
            ),
            "maximum_fair_odds": (
                maximum_fair_odds
            ),
            "minimum_probability": (
                minimum_probability
            ),
            "minimum_market_confidence": (
                minimum_market_confidence
            ),
            "one_per_fixture": (
                one_per_fixture
            ),
        },
        "markets": markets,
    }


@router.get("/fixture/{fixture_id}")
def get_fixture_prediction_picks(
    fixture_id: int,
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
    ),
    db: Session = Depends(get_db),
):

    service = PredictionPickService(db)

    picks = service.get_fixture_picks(
        fixture_id=fixture_id,
        limit=limit,
    )

    if not picks:

        raise HTTPException(
            status_code=404,
            detail="Prediction picks not found.",
        )

    return {
        "fixture_id": fixture_id,
        "count": len(picks),
        "picks": picks,
    }