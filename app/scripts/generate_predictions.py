from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.prediction.predictor import MatchPredictor
from app.services.prediction_service import PredictionService


def main():
    db = SessionLocal()

    predictor = MatchPredictor()
    service = PredictionService(db)

    fixtures = db.query(Fixture).all()

    print(f"Found {len(fixtures)} fixtures")

    for fixture in fixtures:

        existing = service.get_by_fixture(fixture.id)

        if existing:
            continue

        prediction = predictor.predict(
            fixture.home_team,
            fixture.away_team,
        )

        service.create(
            fixture_id=fixture.id,
            home_win_probability=prediction["home_win_probability"],
            draw_probability=prediction["draw_probability"],
            away_win_probability=prediction["away_win_probability"],
            predicted_home_score=prediction["predicted_home_score"],
            predicted_away_score=prediction["predicted_away_score"],
            confidence=prediction["confidence"],
        )

    print("Finished generating predictions.")

    db.close()


if __name__ == "__main__":
    main()