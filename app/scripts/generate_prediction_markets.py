from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.prediction_market import PredictionMarket
from app.prediction.match_predictor import MatchPredictor
from app.services.prediction_market_service import PredictionMarketService

def add_market(
    service,
    fixture_id,
    market_type,
    selection,
    probability,
    confidence,
    line=None,
):

    service.create(
        fixture_id=fixture_id,
        market_type=market_type,
        selection=selection,
        line=line,
        probability=round(probability, 2),
        fair_odds=service.fair_odds(probability),
        confidence=round(confidence, 2),
    )


def main():

    db = SessionLocal()

    service = PredictionMarketService(db)

    db.query(PredictionMarket).delete()
    db.commit()

    fixtures = db.query(Fixture).all()

    print(f"Generating markets for {len(fixtures)} fixtures...")

    for fixture in fixtures:

        prediction = MatchPredictor.predict(
            db,
            fixture.home_team_id,
            fixture.away_team_id,
        )

        home = prediction["home_win"]
        draw = prediction["draw"]
        away = prediction["away_win"]
        btts = prediction["btts"]
        over25 = prediction["over25"]
        under25 = prediction["under25"]

        confidence = max(home, draw, away)

        add_market(
            service,
            fixture.id,
            "MATCH_RESULT",
            "HOME",
            home,
            confidence,
        )

        add_market(
            service,
            fixture.id,
            "MATCH_RESULT",
            "DRAW",
            draw,
            confidence,
        )

        add_market(
            service,
            fixture.id,
            "MATCH_RESULT",
            "AWAY",
            away,
            confidence,
        )

        add_market(
            service,
            fixture.id,
            "BTTS",
            "YES",
            btts,
            btts,
        )

        add_market(
            service,
            fixture.id,
            "BTTS",
            "NO",
            100 - btts,
            100 - btts,
        )

        add_market(
            service,
            fixture.id,
            "TOTAL_GOALS",
            "OVER",
            over25,
            over25,
            line=2.5,
        )

        add_market(
            service,
            fixture.id,
            "TOTAL_GOALS",
            "UNDER",
            under25,
            under25,
            line=2.5,
        )

        add_market(
            service,
            fixture.id,
            "DOUBLE_CHANCE",
            "HOME_OR_DRAW",
            home + draw,
            home + draw,
        )

        add_market(
            service,
            fixture.id,
            "DOUBLE_CHANCE",
            "HOME_OR_AWAY",
            home + away,
            home + away,
        )

        add_market(
            service,
            fixture.id,
            "DOUBLE_CHANCE",
            "DRAW_OR_AWAY",
            draw + away,
            draw + away,
        )

    db.commit()
    db.close()

    print("Finished!")


if __name__ == "__main__":
    main()