from fastapi import APIRouter
from sqlalchemy import func

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.prediction import Prediction
from app.models.prediction_market import PredictionMarket
from app.models.prediction_pick import PredictionPick
from app.utils.datetime_utils import to_utc_iso


router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get("/status")
def system_status():

    db = SessionLocal()

    try:

        fixture_count = (
            db.query(Fixture)
            .count()
        )

        prediction_count = (
            db.query(Prediction)
            .count()
        )

        market_count = (
            db.query(PredictionMarket)
            .count()
        )

        pick_count = (
            db.query(PredictionPick)
            .count()
        )

        latest_fixture_updated_at = (
            db.query(
                func.max(
                    Fixture.updated_at
                )
            )
            .scalar()
        )

        latest_fixture_kickoff_time = (
            db.query(
                func.max(
                    Fixture.kickoff_time
                )
            )
            .scalar()
        )

        return {
            "status": "healthy",
            "database": "connected",
            "counts": {
                "fixtures": fixture_count,
                "predictions": prediction_count,
                "markets": market_count,
                "picks": pick_count,
            },
            "latest_fixture_updated_at": to_utc_iso(
                latest_fixture_updated_at
            ),
            "latest_fixture_kickoff_time": to_utc_iso(
                latest_fixture_kickoff_time
            ),
        }

    finally:

        db.close()

