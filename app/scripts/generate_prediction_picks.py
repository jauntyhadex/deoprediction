from datetime import UTC, datetime

from sqlalchemy import insert

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
MARKET_STREAM_BATCH_SIZE = 2_000
INSERT_BATCH_SIZE = 5_000
MARKET_PROGRESS_INTERVAL = 100_000


def build_pick_rows(
    fixture_id: int,
    markets: list[PredictionMarket],
    created_at: datetime,
) -> list[dict]:

    ranked_markets = MarketRanker.rank(
        markets,
        limit=PICKS_PER_FIXTURE,
    )

    return [
        {
            "fixture_id": fixture_id,
            "market_id": item["market"].id,
            "rank": rank,
            "score": item["score"],
            "grade": item["grade"],
            "created_at": created_at,
        }
        for rank, item in enumerate(
            ranked_markets,
            start=1,
        )
    ]


def main() -> None:

    db = SessionLocal()

    try:

        db.query(PredictionPick).delete(
            synchronize_session=False
        )

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

        eligible_fixture_ids: set[int] = set()

        skipped_confidence = 0
        skipped_data_quality = 0

        print(
            f"Checking {total_fixtures} "
            f"fixtures..."
        )

        for fixture, prediction in fixture_predictions:

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

            eligible_fixture_ids.add(
                fixture.id
            )

        print(
            "Eligible fixtures: "
            f"{len(eligible_fixture_ids)}"
        )

        print(
            "Streaming prediction markets..."
        )

        market_query = (
            db.query(PredictionMarket)
            .order_by(
                PredictionMarket.fixture_id.asc(),
                PredictionMarket.id.asc(),
            )
            .yield_per(
                MARKET_STREAM_BATCH_SIZE
            )
        )

        created_at = datetime.now(UTC).replace(tzinfo=None)

        pick_rows: list[dict] = []

        current_fixture_id: int | None = None

        current_markets: list[
            PredictionMarket
        ] = []

        processed_markets = 0

        for market in market_query:

            processed_markets += 1

            if (
                processed_markets
                % MARKET_PROGRESS_INTERVAL
                == 0
            ):
                print(
                    f"{processed_markets} "
                    "markets processed"
                )

            if (
                market.fixture_id
                not in eligible_fixture_ids
            ):
                continue

            if current_fixture_id is None:

                current_fixture_id = (
                    market.fixture_id
                )

            elif (
                market.fixture_id
                != current_fixture_id
            ):

                pick_rows.extend(
                    build_pick_rows(
                        fixture_id=(
                            current_fixture_id
                        ),
                        markets=current_markets,
                        created_at=created_at,
                    )
                )

                current_fixture_id = (
                    market.fixture_id
                )

                current_markets = []

            current_markets.append(
                market
            )

        if (
            current_fixture_id is not None
            and current_markets
        ):

            pick_rows.extend(
                build_pick_rows(
                    fixture_id=(
                        current_fixture_id
                    ),
                    markets=current_markets,
                    created_at=created_at,
                )
            )

        print(
            "Inserting prediction picks..."
        )

        for start_index in range(
            0,
            len(pick_rows),
            INSERT_BATCH_SIZE,
        ):

            batch = pick_rows[
                start_index:
                start_index
                + INSERT_BATCH_SIZE
            ]

            db.execute(
                insert(PredictionPick),
                batch,
            )

        db.commit()

        database_pick_count = (
            db.query(PredictionPick)
            .count()
        )

        print()
        print(
            "DATA-QUALITY-GATED PICKS"
        )

        print("-" * 60)

        print(
            "Total fixtures: "
            f"{total_fixtures}"
        )

        print(
            "Eligible fixtures: "
            f"{len(eligible_fixture_ids)}"
        )

        print(
            "Skipped by confidence: "
            f"{skipped_confidence}"
        )

        print(
            "Skipped by data quality: "
            f"{skipped_data_quality}"
        )

        print(
            "Markets processed: "
            f"{processed_markets}"
        )

        print(
            "Picks created: "
            f"{len(pick_rows)}"
        )

        print(
            "Database picks: "
            f"{database_pick_count}"
        )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()
