from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.utils.fixture_status_utils import (
    VALID_FIXTURE_STATUSES,
    normalize_fixture_status,
)


def main() -> None:

    db = SessionLocal()

    try:

        fixtures = (
            db.query(Fixture)
            .filter(
                Fixture.status.notin_(
                    VALID_FIXTURE_STATUSES
                )
            )
            .all()
        )

        repaired = 0

        for fixture in fixtures:

            old_status = fixture.status

            fixture.status = (
                normalize_fixture_status(
                    old_status,
                    kickoff_time=(
                        fixture.kickoff_time
                    ),
                    home_score=(
                        fixture.home_score
                    ),
                    away_score=(
                        fixture.away_score
                    ),
                )
            )

            repaired += 1

        db.commit()

        print(
            "Malformed statuses repaired:",
            repaired,
        )

        print(
            "FIXTURE STATUS REPAIR PASSED"
        )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()
