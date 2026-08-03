import random
from datetime import datetime, timezone, timedelta
from sqlalchemy import or_
from app.models.team import Team
from app.models.prediction_market import PredictionMarket
from app.models.prediction import Prediction
from app.models.fixture import Fixture
from app.models.competition import Competition
from sqlalchemy.orm import aliased
from datetime import timezone
from datetime import UTC, datetime

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
from app.utils.datetime_utils import (
    to_utc_iso,
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


def validate_date_range(
    date_from: datetime | None,
    date_to: datetime | None,
) -> tuple[
    datetime | None,
    datetime | None,
]:

    def normalize(
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

    normalized_from = normalize(
        date_from
    )

    normalized_to = normalize(
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
                "date_to must be greater "
                "than or equal to date_from."
            ),
        )

    return (
        normalized_from,
        normalized_to,
    )


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
    date_from: datetime | None = Query(
        default=None,
        description=(
            "Inclusive kickoff lower bound. "
            "Timezone-aware ISO timestamps "
            "are converted to UTC."
        ),
    ),
    date_to: datetime | None = Query(
        default=None,
        description=(
            "Inclusive kickoff upper bound. "
            "Timezone-aware ISO timestamps "
            "are converted to UTC."
        ),
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

    (
        normalized_date_from,
        normalized_date_to,
    ) = validate_date_range(
        date_from=date_from,
        date_to=date_to,
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
        date_from=normalized_date_from,
        date_to=normalized_date_to,
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
            "date_from": to_utc_iso(
                normalized_date_from
            ),
            "date_to": to_utc_iso(
                normalized_date_to
            ),
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
    date_from: datetime | None = Query(
        default=None,
        description=(
            "Inclusive kickoff lower bound. "
            "Timezone-aware ISO timestamps "
            "are converted to UTC."
        ),
    ),
    date_to: datetime | None = Query(
        default=None,
        description=(
            "Inclusive kickoff upper bound. "
            "Timezone-aware ISO timestamps "
            "are converted to UTC."
        ),
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
    line: float | None = Query(
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

    (
        normalized_date_from,
        normalized_date_to,
    ) = validate_date_range(
        date_from=date_from,
        date_to=date_to,
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
        date_from=normalized_date_from,
        date_to=normalized_date_to,
        competition_id=competition_id,
        competition_status=(
            normalized_status
        ),
        market_type=market_type,
        selection=selection,
        line=line,
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
            "date_from": to_utc_iso(
                normalized_date_from
            ),
            "date_to": to_utc_iso(
                normalized_date_to
            ),
            "competition_id": competition_id,
            "competition_status": (
                normalized_status
            ),
            "market_type": market_type,
            "selection": selection,
            "line": line,
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




def fixture_kickoff_iso(kickoff_time):
    if kickoff_time is None:
        return None

    if kickoff_time.tzinfo is None:
        return kickoff_time.isoformat() + "Z"

    return kickoff_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fixture_result_label(prediction):
    values = {
        "HOME": getattr(prediction, "home_win_probability", 0) or 0,
        "DRAW": getattr(prediction, "draw_probability", 0) or 0,
        "AWAY": getattr(prediction, "away_win_probability", 0) or 0,
    }

    return max(values, key=values.get)


def get_fixture_experimental_markets(db, fixture_id: int, limit: int) -> list[dict]:
    home_team = aliased(Team)
    away_team = aliased(Team)

    rows = (
        db.query(
            PredictionMarket,
            Fixture,
            Prediction,
            Competition,
            home_team,
            away_team,
        )
        .join(Fixture, PredictionMarket.fixture_id == Fixture.id)
        .join(Prediction, Prediction.fixture_id == Fixture.id)
        .join(Competition, Fixture.competition_id == Competition.id)
        .join(home_team, Fixture.home_team_id == home_team.id)
        .join(away_team, Fixture.away_team_id == away_team.id)
        .filter(Fixture.id == fixture_id)
        .order_by(
            PredictionMarket.confidence.desc(),
            PredictionMarket.probability.desc(),
            PredictionMarket.fair_odds.asc(),
        )
        .limit(limit)
        .all()
    )

    markets = []

    for market, fixture, prediction, competition, home, away in rows:
        confidence = round(float(market.confidence or 0), 2)
        probability = round(float(market.probability or 0), 2)
        fair_odds = round(float(market.fair_odds or 0), 2)

        markets.append(
            {
                "market_id": market.id,
                "fixture_id": fixture.id,
                "competition_id": competition.id,
                "competition_name": competition.name,
                "competition_status": "EXPERIMENTAL",
                "competition_status_message": (
                    "Experimental market probabilities. No official quality-gated "
                    "pick passed yet for this fixture."
                ),
                "home_team": home.name,
                "away_team": away.name,
                "kickoff_time": fixture_kickoff_iso(fixture.kickoff_time),
                "status": fixture.status,
                "market_type": market.market_type,
                "selection": market.selection,
                "line": market.line,
                "probability": probability,
                "fair_odds": fair_odds,
                "confidence": confidence,
                "market_confidence": confidence,
                "fixture_result": fixture_result_label(prediction),
                "quality_gate": "EXPERIMENTAL",
                "data_quality": "LIMITED",
                "score": confidence,
                "grade": "EXP",
            }
        )

    return markets



def parse_experimental_date(value: str | None, end_of_day: bool = False):
    if not value:
        return None

    try:
        if "T" not in value:
            suffix = "T23:59:59" if end_of_day else "T00:00:00"
            value = value + suffix

        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)

        return parsed
    except ValueError:
        return None


@router.get("/markets/experimental")
def get_experimental_prediction_markets(
    limit: int = Query(default=200, ge=1, le=500),
    upcoming_only: bool = True,
    date_from: str | None = None,
    date_to: str | None = None,
    market_type: str | None = None,
    selection: str | None = None,
    line: float | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    home_team = aliased(Team)
    away_team = aliased(Team)

    query = (
        db.query(
            PredictionMarket,
            Fixture,
            Prediction,
            Competition,
            home_team,
            away_team,
        )
        .join(Fixture, PredictionMarket.fixture_id == Fixture.id)
        .join(Prediction, Prediction.fixture_id == Fixture.id)
        .join(Competition, Fixture.competition_id == Competition.id)
        .join(home_team, Fixture.home_team_id == home_team.id)
        .join(away_team, Fixture.away_team_id == away_team.id)
        .filter(
            or_(
                Competition.code.like("APIF-%"),
                Competition.code.like("TSD-%"),
            )
        )
    )

    if upcoming_only:
        query = query.filter(
            Fixture.kickoff_time >= datetime.now(timezone.utc).replace(tzinfo=None)
        )

    parsed_from = parse_experimental_date(date_from)
    parsed_to = parse_experimental_date(date_to, end_of_day=True)

    if parsed_from:
        query = query.filter(Fixture.kickoff_time >= parsed_from)

    if parsed_to:
        query = query.filter(Fixture.kickoff_time <= parsed_to)

    if market_type:
        query = query.filter(PredictionMarket.market_type == market_type)

    if selection:
        query = query.filter(PredictionMarket.selection == selection)

    if line is not None:
        query = query.filter(PredictionMarket.line == line)

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Competition.code.ilike(like),
                Competition.name.ilike(like),
                Competition.country.ilike(like),
                home_team.name.ilike(like),
                away_team.name.ilike(like),
                PredictionMarket.market_type.ilike(like),
                PredictionMarket.selection.ilike(like),
            )
        )

    rows = (
        query.order_by(
            Fixture.kickoff_time.asc(),
            PredictionMarket.confidence.desc(),
            PredictionMarket.probability.desc(),
        )
        .limit(limit)
        .all()
    )

    markets = []

    for market, fixture, prediction, competition, home, away in rows:
        confidence = round(float(market.confidence or 0), 2)
        probability = round(float(market.probability or 0), 2)
        fair_odds = round(float(market.fair_odds or 0), 2)

        markets.append(
            {
                "market_id": market.id,
                "fixture_id": fixture.id,
                "competition_id": competition.id,
                "competition_name": competition.name,
                "competition_status": "EXPERIMENTAL",
                "competition_status_message": (
                    "Experimental underground market probability. "
                    "Not an official quality-gated pick."
                ),
                "home_team": home.name,
                "away_team": away.name,
                "kickoff_time": fixture_kickoff_iso(fixture.kickoff_time),
                "status": fixture.status,
                "market_type": market.market_type,
                "selection": market.selection,
                "line": market.line,
                "probability": probability,
                "fair_odds": fair_odds,
                "confidence": confidence,
                "market_confidence": confidence,
                "fixture_result": fixture_result_label(prediction),
                "quality_gate": "EXPERIMENTAL",
                "data_quality": "LIMITED",
                "score": confidence,
                "grade": "EXP",
            }
        )

    return {
        "count": len(markets),
        "markets": markets,
    }



def accumulator_leg_key(leg: dict) -> tuple:
    return (
        leg.get("fixture_id"),
        leg.get("market_type"),
        leg.get("selection"),
        leg.get("line"),
    )


def accumulator_fixture_key(leg: dict):
    return leg.get("fixture_id")


def accumulator_decimal(value, fallback=1.0) -> float:
    try:
        parsed = float(value)
        if parsed <= 0:
            return fallback
        return parsed
    except (TypeError, ValueError):
        return fallback


@router.get("/accumulators/bulk")
def get_bulk_accumulators(
    count: int = Query(default=100, ge=1, le=5000),
    legs: int = Query(default=5, ge=2, le=20),
    pool_limit: int = Query(default=500, ge=20, le=2000),
    minimum_probability: float = Query(default=50.0, ge=0.0, le=100.0),
    minimum_fair_odds: float = Query(default=1.2, ge=1.0, le=100.0),
    max_same_competition: int = Query(default=4, ge=1, le=20),
    db: Session = Depends(get_db),
):
    service = PredictionMarketService(db)

    pool = service.get_top_markets(
        limit=pool_limit,
        upcoming_only=True,
        days_ahead=None,
        minimum_fair_odds=minimum_fair_odds,
        maximum_fair_odds=100.0,
        minimum_probability=minimum_probability,
        minimum_market_confidence=0.0,
        one_per_fixture=False,
    )

    pool = [
        market for market in pool
        if str(market.get("grade", "")).upper() in {"A+", "A", "B"}
    ]

    if len(pool) < legs:
        return {
            "count": 0,
            "requested": count,
            "legs_per_accumulator": legs,
            "pool_size": len(pool),
            "accumulators": [],
            "message": "Not enough official markets to build accumulators with these filters.",
        }

    ranked_pool = sorted(
        pool,
        key=lambda item: (
            accumulator_decimal(item.get("probability"), 0),
            accumulator_decimal(item.get("market_confidence") or item.get("confidence"), 0),
            accumulator_decimal(item.get("fair_odds"), 1),
        ),
        reverse=True,
    )

    accumulators = []
    seen_slips = set()
    attempts = 0
    max_attempts = count * 120

    while len(accumulators) < count and attempts < max_attempts:
        attempts += 1

        if attempts % 3 == 0:
            sample_pool = ranked_pool[: min(len(ranked_pool), max(pool_limit // 2, legs * 3))]
        else:
            sample_pool = ranked_pool

        selected = []
        used_fixtures = set()
        competition_counts = {}

        for market in random.sample(sample_pool, k=len(sample_pool)):
            fixture_id = accumulator_fixture_key(market)

            if fixture_id in used_fixtures:
                continue

            competition_name = market.get("competition_name") or "Unknown"
            current_competition_count = competition_counts.get(competition_name, 0)

            if current_competition_count >= max_same_competition:
                continue

            selected.append(market)
            used_fixtures.add(fixture_id)
            competition_counts[competition_name] = current_competition_count + 1

            if len(selected) == legs:
                break

        if len(selected) != legs:
            continue

        slip_key = tuple(sorted(accumulator_leg_key(leg) for leg in selected))

        if slip_key in seen_slips:
            continue

        seen_slips.add(slip_key)

        total_odds = 1.0
        combined_probability = 1.0
        average_confidence = 0.0

        for leg in selected:
            total_odds *= accumulator_decimal(leg.get("fair_odds"), 1.0)
            combined_probability *= accumulator_decimal(leg.get("probability"), 0.0) / 100.0
            average_confidence += accumulator_decimal(
                leg.get("market_confidence") or leg.get("confidence"),
                0.0,
            )

        average_confidence = average_confidence / len(selected)

        accumulators.append(
            {
                "rank": len(accumulators) + 1,
                "legs_count": len(selected),
                "total_fair_odds": round(total_odds, 2),
                "combined_probability": round(combined_probability * 100.0, 4),
                "average_confidence": round(average_confidence, 2),
                "grade": "A" if average_confidence >= 70 else "B",
                "legs": selected,
            }
        )

    return {
        "count": len(accumulators),
        "requested": count,
        "legs_per_accumulator": legs,
        "pool_size": len(pool),
        "accumulators": accumulators,
        "message": "Official accumulator slips generated.",
    }



def parse_public_market_date(value: str | None, end_of_day: bool = False):
    if not value or value in {"all", "any"}:
        return None

    try:
        if "T" not in value:
            suffix = "T23:59:59" if end_of_day else "T00:00:00"
            value = value + suffix

        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)

        return parsed
    except ValueError:
        return None


def public_market_grade(probability: float, confidence: float) -> str:
    if probability >= 65 and confidence >= 60:
        return "A"

    return "B"


@router.get("/markets/public")
def get_public_football_markets(
    limit: int = Query(default=500, ge=1, le=2000),
    upcoming_only: bool = True,
    date: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    days_ahead: int | None = Query(default=None, ge=1, le=365),
    market_type: str | None = None,
    selection: str | None = None,
    line: float | None = None,
    search: str | None = None,
    minimum_probability: float = Query(default=0.0, ge=0.0, le=100.0),
    minimum_fair_odds: float = Query(default=1.01, ge=1.0, le=100.0),
    maximum_fair_odds: float = Query(default=100.0, ge=1.0, le=1000.0),
    db: Session = Depends(get_db),
):
    home_team = aliased(Team)
    away_team = aliased(Team)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    query = (
        db.query(PredictionMarket, Fixture, Competition, home_team, away_team)
        .join(Fixture, PredictionMarket.fixture_id == Fixture.id)
        .join(Competition, Fixture.competition_id == Competition.id)
        .join(home_team, Fixture.home_team_id == home_team.id)
        .join(away_team, Fixture.away_team_id == away_team.id)
        .filter(Competition.sport == "FOOTBALL")
        .filter(Competition.code.notlike("APIF-%"))
        .filter(Competition.code.notlike("TSD-%"))
        .filter(PredictionMarket.probability >= minimum_probability)
        .filter(PredictionMarket.fair_odds >= minimum_fair_odds)
        .filter(PredictionMarket.fair_odds <= maximum_fair_odds)
    )

    if upcoming_only:
        query = query.filter(Fixture.kickoff_time >= now)

    parsed_date_from = parse_public_market_date(date_from)
    parsed_date_to = parse_public_market_date(date_to, end_of_day=True)

    if date:
        parsed_date_from = parse_public_market_date(date)
        parsed_date_to = parse_public_market_date(date, end_of_day=True)

    if parsed_date_from:
        query = query.filter(Fixture.kickoff_time >= parsed_date_from)

    if parsed_date_to:
        query = query.filter(Fixture.kickoff_time <= parsed_date_to)

    if days_ahead:
        query = query.filter(Fixture.kickoff_time <= now + timedelta(days=days_ahead))

    if market_type:
        query = query.filter(PredictionMarket.market_type == market_type)

    if selection:
        query = query.filter(PredictionMarket.selection == selection)

    if line is not None:
        query = query.filter(PredictionMarket.line == line)

    if search:
        like = f"%{search}%"
        query = query.filter(
            (Competition.name.ilike(like))
            | (Competition.code.ilike(like))
            | (home_team.name.ilike(like))
            | (away_team.name.ilike(like))
            | (PredictionMarket.market_type.ilike(like))
            | (PredictionMarket.selection.ilike(like))
        )

    rows = (
        query.order_by(
            Fixture.kickoff_time.asc(),
            PredictionMarket.confidence.desc(),
            PredictionMarket.probability.desc(),
        )
        .limit(limit)
        .all()
    )

    markets = []

    for market, fixture, competition, home, away in rows:
        probability = round(float(market.probability or 0), 2)
        confidence = round(float(market.confidence or 0), 2)
        fair_odds = round(float(market.fair_odds or 0), 2)

        markets.append(
            {
                "market_id": market.id,
                "fixture_id": fixture.id,
                "competition_id": competition.id,
                "competition_name": competition.name,
                "competition_status": "PUBLIC",
                "competition_status_message": "",
                "home_team": home.name,
                "away_team": away.name,
                "kickoff_time": fixture_kickoff_iso(fixture.kickoff_time),
                "status": fixture.status,
                "market_type": market.market_type,
                "selection": market.selection,
                "line": market.line,
                "probability": probability,
                "fair_odds": fair_odds,
                "confidence": confidence,
                "market_confidence": confidence,
                "fixture_result": None,
                "quality_gate": "MARKET_BOARD",
                "data_quality": "PUBLIC_MARKET",
                "score": round((probability + confidence) / 2, 2),
                "grade": public_market_grade(probability, confidence),
            }
        )

    return {
        "count": len(markets),
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
    market_limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
):

    pick_service = PredictionPickService(db)
    market_service = PredictionMarketService(db)

    picks = pick_service.get_fixture_picks(
        fixture_id=fixture_id,
        limit=limit,
    )

    markets = market_service.get_top_markets(
        fixture_id=fixture_id,
        limit=market_limit,
        upcoming_only=False,
        days_ahead=None,
        minimum_fair_odds=1.0,
        maximum_fair_odds=100.0,
        minimum_probability=0.0,
        minimum_market_confidence=0.0,
        one_per_fixture=False,
    )

    if not markets:
        markets = get_fixture_experimental_markets(
            db=db,
            fixture_id=fixture_id,
            limit=market_limit,
        )

    if not picks and not markets:
        raise HTTPException(
            status_code=404,
            detail="Prediction picks or markets not found.",
        )

    return {
        "fixture_id": fixture_id,
        "count": len(picks),
        "market_count": len(markets),
        "picks": picks,
        "markets": markets,
    }