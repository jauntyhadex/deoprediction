import math
from datetime import datetime, timezone, timedelta
import random
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
                "total_estimated_market_odds": round(total_odds, 2),
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




def accumulator_float(value, fallback=0.0) -> float:
    try:
        parsed = float(value)
        if math.isnan(parsed) or math.isinf(parsed):
            return fallback
        return parsed
    except (TypeError, ValueError):
        return fallback


def accumulator_market_key(market: dict) -> tuple:
    return (
        market.get("fixture_id"),
        market.get("market_type"),
        market.get("selection"),
        market.get("line"),
    )


def accumulator_slip_key(legs: list[dict]) -> tuple:
    return tuple(sorted(accumulator_market_key(leg) for leg in legs))



# ACCUMULATOR_REALISTIC_ODDS_START
def accumulator_clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def accumulator_line_number(line, selection: str = "") -> float | None:
    candidates = [line]

    if selection:
        candidates.extend(str(selection).replace("_", " ").split())

    for candidate in candidates:
        try:
            return abs(float(candidate))
        except (TypeError, ValueError):
            continue

    return None


def accumulator_required_leg_floor(target_odds: float, max_legs: int, minimum_fair_odds: float) -> float:
    target = max(accumulator_float(target_odds, 2.0), 2.0)
    legs = max(int(max_legs or 2), 2)
    mathematical_floor = target ** (1.0 / legs)

    # Small tolerance, but never allow silly 1.15 legs for high targets.
    return round(max(accumulator_float(minimum_fair_odds, 1.05), mathematical_floor * 0.98), 2)


def accumulator_estimated_market_odds(
    market_type: str,
    selection: str,
    line,
    probability: float,
    model_fair_odds: float,
) -> float:
    mt = (market_type or "").upper()
    sel = (selection or "").upper()
    line_number = accumulator_line_number(line, selection)
    base = accumulator_float(model_fair_odds, 0.0)

    if base <= 1.0:
        probability_value = accumulator_float(probability, 0.0)
        base = 100.0 / probability_value if probability_value > 0 else 2.0

    low, high = 1.2, 4.0

    if mt == "MATCH_RESULT":
        low, high = (2.8, 4.6) if sel == "DRAW" else (1.45, 4.5)

    elif mt == "DOUBLE_CHANCE":
        low, high = 1.12, 1.7

    elif mt == "DRAW_NO_BET":
        low, high = 1.25, 3.2

    elif mt == "BTTS":
        low, high = 1.5, 2.4

    elif mt in {"FIRST_HALF_BTTS", "SECOND_HALF_BTTS"}:
        low, high = (1.25, 1.75) if sel == "NO" else (2.8, 6.0)

    elif mt in {"TOTAL_GOALS", "FIRST_HALF_TOTAL_GOALS", "SECOND_HALF_TOTAL_GOALS"}:
        ln = line_number if line_number is not None else 2.5

        if mt == "TOTAL_GOALS":
            if ln <= 0.5:
                low, high = 1.03, 1.25
            elif ln <= 1.5:
                low, high = 1.18, 1.7
            elif ln <= 2.5:
                low, high = 1.55, 2.4
            elif ln <= 3.5:
                low, high = 2.0, 3.6
            else:
                low, high = 3.0, 7.0
        else:
            if ln <= 0.5:
                low, high = 1.3, 2.1
            elif ln <= 1.5:
                low, high = 1.9, 4.0
            else:
                low, high = 3.5, 9.0

    elif mt in {"HOME_TEAM_TOTAL", "AWAY_TEAM_TOTAL"}:
        ln = line_number if line_number is not None else 1.5

        if ln <= 0.5:
            low, high = 1.08, 1.55
        elif ln <= 1.5:
            low, high = 1.55, 3.2
        else:
            low, high = 2.6, 7.0

    elif mt == "ASIAN_HANDICAP":
        ln = line_number if line_number is not None else 0.5

        if ln >= 2.5:
            low, high = 1.08, 1.45
        elif ln >= 1.5:
            low, high = 1.18, 1.85
        elif ln >= 0.5:
            low, high = 1.55, 2.35
        else:
            low, high = 1.65, 2.25

    elif mt in {"FIRST_HALF_RESULT", "SECOND_HALF_RESULT"}:
        low, high = (2.0, 3.4) if sel == "DRAW" else (1.75, 4.8)

    elif mt == "CLEAN_SHEET":
        low, high = 1.75, 4.8

    elif mt == "WIN_TO_NIL":
        low, high = 2.5, 8.0

    elif mt == "CORRECT_SCORE":
        low, high = 6.0, 18.0

    return round(accumulator_clamp(base, low, high), 2)


def accumulator_market_is_practical(
    market_type: str,
    selection: str,
    line,
    estimated_market_odds: float,
    required_leg_floor: float,
    target_odds: float,
) -> bool:
    mt = (market_type or "").upper()
    sel = (selection or "").upper()
    line_number = accumulator_line_number(line, selection)

    if estimated_market_odds < required_leg_floor:
        return False

    if mt == "CORRECT_SCORE":
        return False

    if accumulator_float(target_odds, 0.0) >= 5000 and mt == "DOUBLE_CHANCE":
        return False

    if mt in {"TOTAL_GOALS", "FIRST_HALF_TOTAL_GOALS", "SECOND_HALF_TOTAL_GOALS"}:
        if line_number is not None:
            if sel == "OVER" and line_number <= 0.5:
                return False
            if sel == "UNDER" and line_number >= 4.5:
                return False
            if mt != "TOTAL_GOALS" and sel == "UNDER" and line_number >= 2.5:
                return False

    if mt in {"HOME_TEAM_TOTAL", "AWAY_TEAM_TOTAL"}:
        if line_number is not None:
            if sel == "OVER" and line_number <= 0.5:
                return False
            if sel == "UNDER" and line_number >= 2.5:
                return False

    if mt in {"FIRST_HALF_BTTS", "SECOND_HALF_BTTS"} and sel == "NO":
        if accumulator_float(target_odds, 0.0) >= 5000:
            return False

    if mt == "ASIAN_HANDICAP":
        if line_number is not None and line_number >= 2.5:
            return False

    return True
# ACCUMULATOR_REALISTIC_ODDS_END


def accumulator_public_grade(probability: float, confidence: float) -> str:
    if probability >= 65 and confidence >= 60:
        return "A"
    if probability >= 55 and confidence >= 45:
        return "B"
    return "C"


def accumulator_score_candidate(candidate: dict, desired_odds: float) -> float:
    odds = max(accumulator_float(candidate.get("fair_odds"), 1.01), 1.01)
    probability = accumulator_float(candidate.get("probability"), 0.0)
    confidence = accumulator_float(candidate.get("confidence"), 0.0)

    odds_distance = abs(math.log(odds) - math.log(max(desired_odds, 1.01)))
    quality_bonus = (probability / 100.0) + (confidence / 200.0)

    return odds_distance - quality_bonus



# ACCUMULATOR_PRACTICAL_FILTERS_START
def accumulator_practical_line_number(line, selection: str = ""):
    candidates = [line]

    if selection:
        candidates.extend(str(selection).replace("_", " ").split())

    for candidate in candidates:
        try:
            return abs(float(candidate))
        except (TypeError, ValueError):
            continue

    return None


def accumulator_market_shape(market: dict) -> tuple:
    return (
        str(market.get("market_type") or "").upper(),
        str(market.get("selection") or "").upper(),
        str(market.get("line") or ""),
    )


def accumulator_is_practical_default_market(market: dict, target_odds: float) -> bool:
    market_type = str(market.get("market_type") or "").upper()
    selection = str(market.get("selection") or "").upper()
    line_number = accumulator_practical_line_number(market.get("line"), selection)

    allowed = {
        "MATCH_RESULT",
        "BTTS",
        "TOTAL_GOALS",
        "HOME_TEAM_TOTAL",
        "AWAY_TEAM_TOTAL",
        "DRAW_NO_BET",
        "CLEAN_SHEET",
        "WIN_TO_NIL",
        "ASIAN_HANDICAP",
    }

    if market_type not in allowed:
        return False

    # Do not build public accumulator slips from scoreline lotteries.
    if market_type == "CORRECT_SCORE":
        return False

    # No fake safe filler.
    if market_type == "TOTAL_GOALS":
        if selection == "OVER" and line_number is not None and line_number <= 0.5:
            return False
        if selection == "UNDER" and line_number is not None and line_number >= 4.5:
            return False

    if market_type in {"HOME_TEAM_TOTAL", "AWAY_TEAM_TOTAL"}:
        if selection == "OVER" and line_number is not None and line_number <= 0.5:
            return False
        if selection == "UNDER" and line_number is not None and line_number >= 2.5:
            return False

    # No huge handicap safety cushions.
    if market_type == "ASIAN_HANDICAP":
        if line_number is not None and line_number >= 2.0:
            return False

    # High target accumulators need stronger markets, not low-risk filler.
    if target_odds >= 5000 and market_type in {"DRAW_NO_BET"}:
        return False

    return True


def accumulator_max_same_market_type(target_odds: float) -> int:
    if target_odds >= 5000:
        return 2
    if target_odds >= 500:
        return 2
    return 2
# ACCUMULATOR_PRACTICAL_FILTERS_END


@router.get("/accumulators/target")
def get_target_odds_accumulators(
    count: int = Query(default=100, ge=1, le=5000),
    target_odds: float = Query(default=1000.0, ge=2.0, le=1000000.0),
    min_legs: int = Query(default=4, ge=2, le=50),
    max_legs: int = Query(default=20, ge=2, le=50),
    pool_limit: int = Query(default=3000, ge=50, le=5000),
    days_ahead: int = Query(default=30, ge=1, le=365),
    minimum_probability: float = Query(default=5.0, ge=0.0, le=100.0),
    minimum_fair_odds: float = Query(default=1.2, ge=1.0, le=1000.0),
    maximum_fair_odds: float = Query(default=100.0, ge=1.0, le=1000.0),
    max_same_competition: int = Query(default=6, ge=1, le=50),
    max_overshoot_percent: float = Query(default=20.0, ge=0.0, le=500.0),
    db: Session = Depends(get_db),
):
    if min_legs > max_legs:
        raise HTTPException(
            status_code=400,
            detail="min_legs cannot be greater than max_legs.",
        )

    upper_target = target_odds * (1.0 + (max_overshoot_percent / 100.0))
    required_leg_floor = accumulator_required_leg_floor(target_odds, max_legs, minimum_fair_odds)

    home_team = aliased(Team)
    away_team = aliased(Team)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    end = now + timedelta(days=days_ahead)

    rows = (
        db.query(PredictionMarket, Fixture, Competition, home_team, away_team)
        .join(Fixture, PredictionMarket.fixture_id == Fixture.id)
        .join(Competition, Fixture.competition_id == Competition.id)
        .join(home_team, Fixture.home_team_id == home_team.id)
        .join(away_team, Fixture.away_team_id == away_team.id)
        .filter(Competition.sport == "FOOTBALL")
        .filter(Fixture.kickoff_time >= now)
        .filter(Fixture.kickoff_time <= end)
        .filter(PredictionMarket.probability >= minimum_probability)
        .filter(PredictionMarket.fair_odds >= minimum_fair_odds)
        .filter(PredictionMarket.fair_odds <= maximum_fair_odds)
        .order_by(
            Fixture.kickoff_time.asc(),
            PredictionMarket.probability.desc(),
            PredictionMarket.confidence.desc(),
        )
        .limit(pool_limit)
        .all()
    )

    pool = []

    for market, fixture, competition, home, away in rows:
        probability = round(accumulator_float(market.probability), 2)
        confidence = round(accumulator_float(market.confidence), 2)
        model_fair_odds = round(accumulator_float(market.fair_odds), 2)
        estimated_market_odds = accumulator_estimated_market_odds(
            market.market_type,
            market.selection,
            market.line,
            probability,
            model_fair_odds,
        )

        if not accumulator_market_is_practical(
            market.market_type,
            market.selection,
            market.line,
            estimated_market_odds,
            required_leg_floor,
            target_odds,
        ):
            continue

        pool.append(
            {
                "market_id": market.id,
                "fixture_id": fixture.id,
                "competition_name": competition.name,
                "home_team": home.name,
                "away_team": away.name,
                "kickoff_time": fixture_kickoff_iso(fixture.kickoff_time),
                "market_type": market.market_type,
                "selection": market.selection,
                "line": market.line,
                "probability": probability,
                "model_fair_odds": model_fair_odds,
                "fair_odds": estimated_market_odds,
                "estimated_market_odds": estimated_market_odds,
                "confidence": confidence,
                "market_confidence": confidence,
                "grade": accumulator_public_grade(probability, confidence),
            }
        )

    pool = [market for market in pool if accumulator_is_practical_default_market(market, target_odds)]

    if len(pool) < min_legs:
        return {
            "count": 0,
            "requested": count,
            "target_odds": target_odds,
            "minimum_total_odds": target_odds,
            "maximum_total_odds": round(upper_target, 2),
            "required_leg_floor": round(required_leg_floor, 2),
            "pool_size": len(pool),
            "accumulators": [],
            "message": "Not enough football markets to build accumulators.",
        }

    accumulators = []
    seen = set()
    max_attempts = min(max(count * 200, 10000), 350000)

    for _attempt in range(max_attempts):
        if len(accumulators) >= count:
            break

        selected = []
        used_fixtures = set()
        competition_counts = {}
        market_type_counts = {}
        market_shape_counts = {}
        max_same_market_type = accumulator_max_same_market_type(target_odds)
        total_odds = 1.0

        while len(selected) < max_legs:
            remaining_to_target = target_odds / max(total_odds, 1.0)
            remaining_slots = max(min_legs - len(selected), 1)

            if len(selected) >= min_legs:
                remaining_slots = max(max_legs - len(selected), 1)

            desired_odds = remaining_to_target ** (1.0 / remaining_slots)

            candidates = []

            for market in pool:
                fixture_id = market["fixture_id"]

                if fixture_id in used_fixtures:
                    continue

                competition_name = market["competition_name"]
                if competition_counts.get(competition_name, 0) >= max_same_competition:
                    continue

                market_type = str(market.get("market_type") or "").upper()
                market_shape = accumulator_market_shape(market)

                if market_type_counts.get(market_type, 0) >= max_same_market_type:
                    continue

                if market_shape_counts.get(market_shape, 0) >= 1:
                    continue

                market_odds = accumulator_float(market["fair_odds"], 1.0)
                projected_odds = total_odds * market_odds

                # Before min legs, do not finish early.
                if len(selected) + 1 < min_legs and projected_odds >= target_odds:
                    continue

                # Keep slips near the target. This prevents 1000 becoming 5000+.
                if projected_odds > upper_target:
                    continue

                candidates.append(market)

            if not candidates:
                break

            candidates.sort(key=lambda item: accumulator_score_candidate(item, desired_odds))
            shortlist = candidates[: min(len(candidates), 35)]
            chosen = random.choice(shortlist)

            selected.append(chosen)
            used_fixtures.add(chosen["fixture_id"])
            competition_counts[chosen["competition_name"]] = competition_counts.get(chosen["competition_name"], 0) + 1
            chosen_market_type = str(chosen.get("market_type") or "").upper()
            chosen_market_shape = accumulator_market_shape(chosen)
            market_type_counts[chosen_market_type] = market_type_counts.get(chosen_market_type, 0) + 1
            market_shape_counts[chosen_market_shape] = market_shape_counts.get(chosen_market_shape, 0) + 1
            total_odds *= accumulator_float(chosen["fair_odds"], 1.0)

            if len(selected) >= min_legs and target_odds <= total_odds <= upper_target:
                break

        if len(selected) < min_legs:
            continue

        if not (target_odds <= total_odds <= upper_target):
            continue

        slip_key = accumulator_slip_key(selected)

        if slip_key in seen:
            continue

        seen.add(slip_key)

        combined_probability = 1.0
        average_confidence = 0.0

        for leg in selected:
            combined_probability *= accumulator_float(leg["probability"]) / 100.0
            average_confidence += accumulator_float(leg["confidence"])

        average_confidence = average_confidence / len(selected)

        accumulators.append(
            {
                "rank": len(accumulators) + 1,
                "legs_count": len(selected),
                "target_odds": round(target_odds, 2),
                "minimum_total_odds": round(target_odds, 2),
                "maximum_total_odds": round(upper_target, 2),
                "total_fair_odds": round(total_odds, 2),
                "total_estimated_market_odds": round(total_odds, 2),
                "combined_probability": round(combined_probability * 100.0, 6),
                "average_confidence": round(average_confidence, 2),
                "legs": selected,
            }
        )

    accumulators.sort(
        key=lambda item: (
            abs(item["total_fair_odds"] - target_odds),
            -item["average_confidence"],
            item["legs_count"],
        )
    )

    for index, accumulator in enumerate(accumulators, start=1):
        accumulator["rank"] = index

    return {
        "count": len(accumulators),
        "requested": count,
        "target_odds": round(target_odds, 2),
        "minimum_total_odds": round(target_odds, 2),
        "maximum_total_odds": round(upper_target, 2),
        "required_leg_floor": round(required_leg_floor, 2),
        "pool_size": len(pool),
        "accumulators": accumulators,
        "message": "Target-odds football accumulators generated with realistic accumulator odds filters.",
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