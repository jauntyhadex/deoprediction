from collections import Counter, defaultdict
from datetime import datetime

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.fixture import Fixture
from app.models.prediction import Prediction
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


UPCOMING_STATUSES = {
    "SCHEDULED",
    "TIMED",
}

FINISHED_STATUSES = {
    "FINISHED",
}


def percentage(
    numerator: int,
    denominator: int,
) -> float:
    if denominator <= 0:
        return 0.0

    return round(
        numerator / denominator * 100,
        2,
    )


def format_datetime(
    value,
) -> str:
    if value is None:
        return "None"

    return value.strftime(
        "%Y-%m-%d %H:%M"
    )


def main():

    db = SessionLocal()

    try:

        competitions = (
            db.query(Competition)
            .order_by(
                Competition.id.asc()
            )
            .all()
        )

        fixtures = (
            db.query(Fixture)
            .order_by(
                Fixture.competition_id.asc(),
                Fixture.kickoff_time.asc(),
            )
            .all()
        )

        prediction_fixture_ids = {
            row.fixture_id
            for row in (
                db.query(
                    Prediction.fixture_id
                )
                .all()
            )
        }

        evaluation_fixture_ids = {
            row.fixture_id
            for row in (
                db.query(
                    WalkForwardEvaluation.fixture_id
                )
                .all()
            )
        }

        fixtures_by_competition = defaultdict(
            list
        )

        for fixture in fixtures:
            fixtures_by_competition[
                fixture.competition_id
            ].append(fixture)

        print(
            "\nHISTORICAL COVERAGE REPORT"
        )

        print("=" * 90)

        total_fixtures = 0
        total_finished = 0
        total_upcoming = 0
        total_finished_predictions = 0
        total_evaluations = 0

        competitions_without_history = []

        for competition in competitions:

            competition_fixtures = (
                fixtures_by_competition.get(
                    competition.id,
                    [],
                )
            )

            status_counts = Counter(
                fixture.status
                for fixture
                in competition_fixtures
            )

            finished_fixtures = [
                fixture
                for fixture
                in competition_fixtures
                if fixture.status
                in FINISHED_STATUSES
            ]

            upcoming_fixtures = [
                fixture
                for fixture
                in competition_fixtures
                if (
                    fixture.status
                    in UPCOMING_STATUSES
                    and fixture.kickoff_time
                    >= datetime.utcnow()
                )
            ]

            finished_with_prediction = [
                fixture
                for fixture
                in finished_fixtures
                if fixture.id
                in prediction_fixture_ids
            ]

            evaluated_finished = [
                fixture
                for fixture
                in finished_fixtures
                if fixture.id
                in evaluation_fixture_ids
            ]

            finished_dates = [
                fixture.kickoff_time
                for fixture
                in finished_fixtures
                if fixture.kickoff_time
                is not None
            ]

            upcoming_dates = [
                fixture.kickoff_time
                for fixture
                in upcoming_fixtures
                if fixture.kickoff_time
                is not None
            ]

            earliest_finished = (
                min(finished_dates)
                if finished_dates
                else None
            )

            latest_finished = (
                max(finished_dates)
                if finished_dates
                else None
            )

            earliest_upcoming = (
                min(upcoming_dates)
                if upcoming_dates
                else None
            )

            latest_upcoming = (
                max(upcoming_dates)
                if upcoming_dates
                else None
            )

            competition_name = getattr(
                competition,
                "name",
                (
                    "Competition "
                    f"{competition.id}"
                ),
            )

            print(
                f"\n{competition_name} "
                f"(ID {competition.id})"
            )

            print("-" * 90)

            print(
                f"Total fixtures: "
                f"{len(competition_fixtures)}"
            )

            print(
                f"Finished fixtures: "
                f"{len(finished_fixtures)}"
            )

            print(
                f"Upcoming fixtures: "
                f"{len(upcoming_fixtures)}"
            )

            print(
                f"Finished fixtures with predictions: "
                f"{len(finished_with_prediction)}"
            )

            print(
                f"Walk-forward evaluations: "
                f"{len(evaluated_finished)}"
            )

            print(
                "Evaluation coverage: "
                f"{percentage(
                    len(evaluated_finished),
                    len(finished_fixtures),
                )}%"
            )

            print(
                "Finished date range: "
                f"{format_datetime(
                    earliest_finished
                )} -> "
                f"{format_datetime(
                    latest_finished
                )}"
            )

            print(
                "Upcoming date range: "
                f"{format_datetime(
                    earliest_upcoming
                )} -> "
                f"{format_datetime(
                    latest_upcoming
                )}"
            )

            print(
                "Statuses: "
                + (
                    ", ".join(
                        (
                            f"{status}="
                            f"{count}"
                        )
                        for status, count
                        in sorted(
                            status_counts.items()
                        )
                    )
                    or "None"
                )
            )

            if (
                len(finished_fixtures)
                == 0
            ):
                competitions_without_history.append(
                    (
                        competition.id,
                        competition_name,
                        len(upcoming_fixtures),
                    )
                )

            total_fixtures += len(
                competition_fixtures
            )

            total_finished += len(
                finished_fixtures
            )

            total_upcoming += len(
                upcoming_fixtures
            )

            total_finished_predictions += len(
                finished_with_prediction
            )

            total_evaluations += len(
                evaluated_finished
            )

        print(
            "\nDATABASE TOTALS"
        )

        print("=" * 90)

        print(
            f"Fixtures: "
            f"{total_fixtures}"
        )

        print(
            f"Finished fixtures: "
            f"{total_finished}"
        )

        print(
            f"Upcoming fixtures: "
            f"{total_upcoming}"
        )

        print(
            "Finished fixtures with predictions: "
            f"{total_finished_predictions}"
        )

        print(
            f"Walk-forward evaluations: "
            f"{total_evaluations}"
        )

        print(
            "Overall evaluation coverage: "
            f"{percentage(
                total_evaluations,
                total_finished,
            )}%"
        )

        print(
            "\nCOMPETITIONS WITHOUT FINISHED HISTORY"
        )

        print("=" * 90)

        if not competitions_without_history:
            print(
                "Every competition has "
                "finished fixture history."
            )

        for (
            competition_id,
            competition_name,
            upcoming_count,
        ) in competitions_without_history:

            print(
                f"{competition_name} "
                f"(ID {competition_id}) | "
                f"Upcoming fixtures: "
                f"{upcoming_count}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()