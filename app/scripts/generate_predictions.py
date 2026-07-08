from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.prediction.match_predictor import MatchPredictor
from app.services.prediction_service import PredictionService


def main():
    db = SessionLocal()
    service = PredictionService(db)

    try:
        fixtures = db.query(Fixture).all()
        total_fixtures = len(fixtures)

        print(
            f"Generating predictions for "
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
            )

            existing = service.get_by_fixture(
                fixture.id
            )

            confidence = max(
                prediction["home_win"],
                prediction["draw"],
                prediction["away_win"],
            )

            if existing:
                existing.home_win_probability = (
                    prediction["home_win"]
                )

                existing.draw_probability = (
                    prediction["draw"]
                )

                existing.away_win_probability = (
                    prediction["away_win"]
                )

                existing.predicted_home_score = round(
                    prediction["home_xg"]
                )

                existing.predicted_away_score = round(
                    prediction["away_xg"]
                )

                existing.confidence = confidence

            else:
                service.create(
                    fixture_id=fixture.id,
                    home_win_probability=(
                        prediction["home_win"]
                    ),
                    draw_probability=(
                        prediction["draw"]
                    ),
                    away_win_probability=(
                        prediction["away_win"]
                    ),
                    predicted_home_score=round(
                        prediction["home_xg"]
                    ),
                    predicted_away_score=round(
                        prediction["away_xg"]
                    ),
                    confidence=confidence,
                )

            if index % 100 == 0:
                db.commit()

                print(
                    f"{index}/"
                    f"{total_fixtures} completed"
                )

        db.commit()

        print("Finished!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()