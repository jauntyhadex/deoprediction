from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.utils.fixture_status_utils import (
    VALID_FIXTURE_STATUSES,
)


def main() -> None:

    db = SessionLocal()

    try:

        status_counts = (
            db.query(
                Fixture.status,
            )
            .order_by(
                Fixture.status.asc()
            )
            .all()
        )

        invalid_statuses = sorted(
            {
                status
                for status, in status_counts
                if (
                    status
                    not in VALID_FIXTURE_STATUSES
                )
            }
        )

        if invalid_statuses:

            print(
                "INVALID FIXTURE STATUSES:"
            )

            for status in invalid_statuses:
                print(status)

            raise SystemExit(1)

        print(
            "Valid fixture statuses:"
        )

        distinct_statuses = sorted(
            {
                status
                for status, in status_counts
            }
        )

        for status in distinct_statuses:
            print(status)

        print(
            "FIXTURE STATUS AUDIT PASSED"
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()
