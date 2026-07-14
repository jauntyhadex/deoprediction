from collections import defaultdict
from datetime import datetime

from sqlalchemy import insert

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.head_to_head import HeadToHead


def main() -> None:

    db = SessionLocal()

    try:

        fixtures = (
            db.query(Fixture)
            .filter(
                Fixture.status == "FINISHED",
                Fixture.home_score.is_not(None),
                Fixture.away_score.is_not(None),
            )
            .order_by(
                Fixture.kickoff_time.asc()
            )
            .all()
        )

        print(
            f"Processing {len(fixtures)} fixtures..."
        )

        pair_stats = defaultdict(
            lambda: {
                "matches_played": 0,
                "home_wins": 0,
                "draws": 0,
                "away_wins": 0,
                "home_goals": 0,
                "away_goals": 0,
                "btts": 0,
                "over25": 0,
            }
        )

        for fixture in fixtures:

            key = (
                fixture.home_team_id,
                fixture.away_team_id,
            )

            stats = pair_stats[key]

            home_score = int(
                fixture.home_score
            )

            away_score = int(
                fixture.away_score
            )

            stats["matches_played"] += 1
            stats["home_goals"] += home_score
            stats["away_goals"] += away_score

            if home_score > away_score:
                stats["home_wins"] += 1
            elif home_score < away_score:
                stats["away_wins"] += 1
            else:
                stats["draws"] += 1

            if (
                home_score > 0
                and away_score > 0
            ):
                stats["btts"] += 1

            if (
                home_score + away_score
                > 2
            ):
                stats["over25"] += 1

        created_at = datetime.utcnow()
        rows = []

        for (
            home_team_id,
            away_team_id,
        ), stats in pair_stats.items():

            matches_played = stats[
                "matches_played"
            ]

            rows.append(
                {
                    "home_team_id": (
                        home_team_id
                    ),
                    "away_team_id": (
                        away_team_id
                    ),
                    "matches_played": (
                        matches_played
                    ),
                    "home_wins": (
                        stats["home_wins"]
                    ),
                    "draws": (
                        stats["draws"]
                    ),
                    "away_wins": (
                        stats["away_wins"]
                    ),
                    "home_goals": (
                        stats["home_goals"]
                    ),
                    "away_goals": (
                        stats["away_goals"]
                    ),
                    "average_goals": (
                        (
                            stats["home_goals"]
                            + stats["away_goals"]
                        )
                        / matches_played
                    ),
                    "btts_rate": (
                        stats["btts"]
                        / matches_played
                    ),
                    "over25_rate": (
                        stats["over25"]
                        / matches_played
                    ),
                    "created_at": created_at,
                }
            )

        db.query(HeadToHead).delete(
            synchronize_session=False
        )

        if rows:
            db.execute(
                insert(HeadToHead),
                rows,
            )

        db.commit()

        database_count = (
            db.query(HeadToHead)
            .count()
        )

        print(
            f"Pairs created: {len(rows)}"
        )

        print(
            f"Database pairs: {database_count}"
        )

        print("Finished!")

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()
