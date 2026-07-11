from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.prediction import Prediction
from app.models.prediction_market import PredictionMarket
from app.models.prediction_pick import PredictionPick
from app.models.team_home_away_stats import (
    TeamHomeAwayStats,
)
from app.models.team_stat import TeamStat
from app.prediction.data_quality_gate import (
    PredictionDataQualityGate,
)
from app.prediction.market_ranker import MarketRanker
from app.prediction.quality_gate import (
    PredictionQualityGate,
)


PICKS_PER_FIXTURE = 5


def main():

    db = SessionLocal()

    try:

        db.query(PredictionPick).delete(
            synchronize_session=False
        )

        db.commit()

        team_stats = {
            row.team_id: row
            for row in db.query(TeamStat).all()
        }

        venue_stats = {
            row.team_id: row
            for row in db.query(
                TeamHomeAwayStats
            ).all()
        }

        fixture_predictions = (
            db.query(
                Fixture,
                Prediction,
            )
            .join(
                Prediction,
                Prediction.fixture_id
                == Fixture.id,
            )
            .order_by(
                Fixture.id.asc()
            )
            .all()
        )

        total_fixtures = len(
            fixture_predictions
        )

        eligible_fixtures = 0
        skipped_confidence = 0
        skipped_data_quality = 0
        created_picks = 0

        print(
            f"Checking {total_fixtures} "
            f"fixtures..."
        )

        for index, (
            fixture,
            prediction,
        ) in enumerate(
            fixture_predictions,
            start=1,
        ):

            if not PredictionQualityGate.passes(
                prediction
            ):
                skipped_confidence += 1
                continue

            data_is_sufficient = (
                PredictionDataQualityGate.passes(
                    home_team_id=(
                        fixture.home_team_id
                    ),
                    away_team_id=(
                        fixture.away_team_id
                    ),
                    team_stats=team_stats,
                    venue_stats=venue_stats,
                )
            )

            if not data_is_sufficient:
                skipped_data_quality += 1
                continue

            eligible_fixtures += 1

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

                db.add(
                    PredictionPick(
                        fixture_id=fixture.id,
                        market_id=(
                            item["market"].id
                        ),
                        rank=rank,
                        score=item["score"],
                        grade=item["grade"],
                    )
                )

                created_picks += 1

            if index % 100 == 0:

                db.commit()

                print(
                    f"{index}/"
                    f"{total_fixtures} checked"
                )

        db.commit()

        database_pick_count = (
            db.query(PredictionPick)
            .count()
        )

        print("\nDATA-QUALITY-GATED PICKS")
        print("-" * 60)

        print(
            f"Total fixtures: "
            f"{total_fixtures}"
        )

        print(
            f"Eligible fixtures: "
            f"{eligible_fixtures}"
        )

        print(
            f"Skipped by confidence: "
            f"{skipped_confidence}"
        )

        print(
            f"Skipped by data quality: "
            f"{skipped_data_quality}"
        )

        print(
            f"Picks created: "
            f"{created_picks}"
        )

        print(
            f"Database picks: "
            f"{database_pick_count}"
        )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()