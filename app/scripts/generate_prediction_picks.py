from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.prediction_market import PredictionMarket
from app.models.prediction_pick import PredictionPick
from app.prediction.market_ranker import MarketRanker


PICKS_PER_FIXTURE = 5


def main():

    db = SessionLocal()

    try:

        db.query(PredictionPick).delete(
            synchronize_session=False
        )

        db.commit()

        fixtures = db.query(Fixture).all()

        total_fixtures = len(fixtures)

        print(
            f"Generating picks for "
            f"{total_fixtures} fixtures..."
        )

        for index, fixture in enumerate(
            fixtures,
            start=1,
        ):

            markets = (
                db.query(PredictionMarket)
                .filter(
                    PredictionMarket.fixture_id
                    == fixture.id
                )
                .all()
            )

            ranked_markets = MarketRanker.rank(
                markets,
                limit=PICKS_PER_FIXTURE,
            )

            for rank, item in enumerate(
                ranked_markets,
                start=1,
            ):

                pick = PredictionPick(
                    fixture_id=fixture.id,
                    market_id=item["market"].id,
                    rank=rank,
                    score=item["score"],
                    grade=item["grade"],
                )

                db.add(pick)

            if index % 100 == 0:

                db.commit()

                print(
                    f"{index}/"
                    f"{total_fixtures} completed"
                )

        db.commit()

        total_picks = (
            db.query(PredictionPick).count()
        )

        print(
            f"Finished! "
            f"{total_picks} picks created."
        )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()