from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.api.routes.fixtures import (
    serialize_fixture,
)
from app.config.settings import settings
from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.fixture import Fixture
from app.models.prediction import Prediction
from app.models.prediction_market import PredictionMarket
from app.models.prediction_pick import PredictionPick
from app.models.team import Team
from app.services.fixture_service import FixtureService
from app.services.market_catalog_service import (
    MarketCatalogService,
)
from app.services.prediction_market_service import (
    PredictionMarketService,
)
from app.services.prediction_pick_service import (
    PredictionPickService,
)
from app.services.timezone_service import (
    TimezoneService,
)


router = APIRouter(
    prefix="/discovery",
    tags=["Discovery"],
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def get_counts(
    db: Session,
) -> dict:

    return {
        "competitions": (
            db.query(Competition).count()
        ),
        "teams": (
            db.query(Team).count()
        ),
        "fixtures": (
            db.query(Fixture).count()
        ),
        "predictions": (
            db.query(Prediction).count()
        ),
        "markets": (
            db.query(PredictionMarket).count()
        ),
        "picks": (
            db.query(PredictionPick).count()
        ),
    }


@router.get("/home")
def get_discovery_home(
    timezone: str | None = Query(
        default=None,
        max_length=64,
    ),
    days_ahead: int = Query(
        default=30,
        ge=1,
        le=365,
    ),
    fixture_limit: int = Query(
        default=5,
        ge=1,
        le=50,
    ),
    pick_limit: int = Query(
        default=5,
        ge=1,
        le=50,
    ),
    market_limit: int = Query(
        default=5,
        ge=1,
        le=50,
    ),
    db: Session = Depends(get_db),
):

    try:

        display_timezone = (
            TimezoneService.validate(
                timezone
                or settings.default_timezone
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    fixture_total, fixture_rows = (
        FixtureService(db).list_catalog(
            limit=fixture_limit,
            offset=0,
            upcoming_only=True,
            days_ahead=days_ahead,
        )
    )

    top_picks = (
        PredictionPickService(db)
        .get_top_picks(
            limit=pick_limit,
            upcoming_only=True,
            days_ahead=days_ahead,
            one_per_fixture=True,
        )
    )

    top_markets = (
        PredictionMarketService(db)
        .get_top_markets(
            limit=market_limit,
            upcoming_only=True,
            days_ahead=days_ahead,
            one_per_fixture=True,
        )
    )

    market_types = (
        MarketCatalogService(db)
        .get_market_types()
    )

    return {
        "timezone": display_timezone,
        "default_timezone": (
            settings.default_timezone
        ),
        "timestamps": {
            "storage": "UTC",
            "api_format": "ISO-8601 Z",
            "client_display": (
                "Convert UTC timestamps to "
                "the user timezone."
            ),
        },
        "filters": {
            "days_ahead": days_ahead,
            "fixture_limit": fixture_limit,
            "pick_limit": pick_limit,
            "market_limit": market_limit,
        },
        "counts": get_counts(db),
        "upcoming_fixtures": {
            "count": len(fixture_rows),
            "total": fixture_total,
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
                ) in fixture_rows
            ],
        },
        "top_picks": {
            "count": len(top_picks),
            "picks": top_picks,
        },
        "top_markets": {
            "count": len(top_markets),
            "markets": top_markets,
        },
        "market_catalog": {
            "count": len(market_types),
            "market_types": [
                {
                    "market_type": item[
                        "market_type"
                    ],
                    "display_name": item[
                        "display_name"
                    ],
                }
                for item in market_types
            ],
        },
    }
