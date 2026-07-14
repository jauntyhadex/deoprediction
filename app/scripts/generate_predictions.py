from datetime import datetime

from sqlalchemy import insert

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.prediction import Prediction
from app.prediction.expected_goals import (
    ExpectedGoalsCalculator,
)
from app.prediction.match_predictor import (
    MatchPredictor,
)


INSERT_BATCH_SIZE = 5_000


def main() -> None:

    db = SessionLocal()

    try:

        fixtures = (
            db.query(Fixture)
            .order_by(
                Fixture.id.asc()
            )
            .all()
        )

        total_fixtures = len(fixtures)

        data_cache = (
            ExpectedGoalsCalculator
            .build_cache(db)
        )

        prediction_rows = []
        created_at = datetime.utcnow()

        print(
            "Generating predictions for "
            f"{total_fixtures} fixtures..."
        )

        for index, fixture in enumerate(
            fixtures,
            start=1,
        ):

            prediction = MatchPredictor.predict(
                db,
                fixture.home_team_id,
                fixture.away_team_id,
                data_cache=data_cache,
            )

            confidence = max(
                prediction["home_win"],
                prediction["draw"],
                prediction["away_win"],
            )

            prediction_rows.append(
                {
                    "fixture_id": fixture.id,
                    "home_win_probability": (
                        prediction["home_win"]
                    ),
                    "draw_probability": (
                        prediction["draw"]
                    ),
                    "away_win_probability": (
                        prediction["away_win"]
                    ),
                    "predicted_home_score": round(
                        prediction["home_xg"]
                    ),
                    "predicted_away_score": round(
                        prediction["away_xg"]
                    ),
                    "confidence": confidence,
                    "created_at": created_at,
                }
            )

            if index % 500 == 0:
                print(
                    f"{index}/"
                    f"{total_fixtures} completed"
                )

        db.query(Prediction).delete(
            synchronize_session=False
        )

        for start_index in range(
            0,
            len(prediction_rows),
            INSERT_BATCH_SIZE,
        ):

            db.execute(
                insert(Prediction),
                prediction_rows[
                    start_index:
                    start_index
                    + INSERT_BATCH_SIZE
                ],
            )

        db.commit()

        database_count = (
            db.query(Prediction)
            .count()
        )

        print(
            f"Predictions created: "
            f"{len(prediction_rows)}"
        )

        print(
            f"Database predictions: "
            f"{database_count}"
        )

        print("Finished!")

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()
