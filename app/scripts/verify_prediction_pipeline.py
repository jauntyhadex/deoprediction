from sqlalchemy import func, or_

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.prediction import Prediction
from app.models.prediction_market import PredictionMarket
from app.models.prediction_pick import PredictionPick


def main():
    db = SessionLocal()

    try:
        fixture_count = db.query(Fixture).count()
        prediction_count = db.query(Prediction).count()
        market_count = db.query(PredictionMarket).count()
        pick_count = db.query(PredictionPick).count()

        invalid_markets = (
            db.query(PredictionMarket)
            .filter(
                or_(
                    PredictionMarket.probability < 0,
                    PredictionMarket.probability > 100,
                    PredictionMarket.fair_odds < 0,
                    PredictionMarket.confidence < 0,
                    PredictionMarket.confidence > 100,
                )
            )
            .count()
        )

        invalid_picks = (
            db.query(PredictionPick)
            .join(
                PredictionMarket,
                PredictionMarket.id
                == PredictionPick.market_id,
            )
            .filter(
                or_(
                    PredictionMarket.probability > 86.95,
                    PredictionMarket.fair_odds < 1.15,
                    PredictionMarket.fair_odds > 8.00,
                    PredictionMarket.market_type
                    == "CORRECT_SCORE",
                    PredictionPick.score < 0,
                    PredictionPick.score > 100,
                )
            )
            .count()
        )

        duplicate_ranks = (
            db.query(
                PredictionPick.fixture_id,
                PredictionPick.rank,
                func.count(PredictionPick.id),
            )
            .group_by(
                PredictionPick.fixture_id,
                PredictionPick.rank,
            )
            .having(
                func.count(PredictionPick.id) > 1
            )
            .count()
        )

        print(f"Fixtures: {fixture_count}")
        print(f"Predictions: {prediction_count}")
        print(f"Markets: {market_count}")
        print(f"Picks: {pick_count}")
        print(f"Invalid markets: {invalid_markets}")
        print(f"Invalid picks: {invalid_picks}")
        print(f"Duplicate pick ranks: {duplicate_ranks}")

        passed = (
            fixture_count > 0
            and prediction_count == fixture_count
            and market_count > 0
            and pick_count > 0
            and invalid_markets == 0
            and invalid_picks == 0
            and duplicate_ranks == 0
        )

        if passed:
            print("\nVERIFICATION PASSED")
        else:
            print("\nVERIFICATION FAILED")
            raise SystemExit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()