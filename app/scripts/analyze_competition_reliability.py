from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import func

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.fixture import Fixture
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


UPCOMING_STATUSES = [
    "SCHEDULED",
    "TIMED",
]

MINIMUM_EVALUATIONS = 50
MINIMUM_RELIABLE_EVALUATIONS = 100

RELIABLE_MINIMUM_ACCURACY = 55.0
PROMISING_MINIMUM_ACCURACY = 52.0

MAXIMUM_BRIER_SCORE = 0.20


STATUS_ORDER = {
    "RELIABLE": 1,
    "PROMISING": 2,
    "LIMITED": 3,
    "WEAK": 4,
    "UNVALIDATED": 5,
}


def percentage(
    numerator: int,
    denominator: int,
) -> float:
    if denominator <= 0:
        return 0.0

    return round(
        (numerator / denominator) * 100,
        2,
    )


def average(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return round(
        sum(values) / len(values),
        4,
    )


def calculate_metrics(
    rows: list[WalkForwardEvaluation],
) -> dict:

    total = len(rows)

    if total == 0:
        return {
            "evaluations": 0,
            "accuracy": 0.0,
            "brier": 0.0,
            "log_loss": 0.0,
            "goal_error": 0.0,
            "home_recall": 0.0,
            "draw_recall": 0.0,
            "away_recall": 0.0,
            "macro_recall": 0.0,
        }

    correct_results = sum(
        1
        for row in rows
        if row.result_correct
    )

    actual_counts = {
        "HOME": 0,
        "DRAW": 0,
        "AWAY": 0,
    }

    correct_counts = {
        "HOME": 0,
        "DRAW": 0,
        "AWAY": 0,
    }

    for row in rows:

        actual_result = row.actual_result

        if actual_result not in actual_counts:
            continue

        actual_counts[actual_result] += 1

        if row.result_correct:
            correct_counts[actual_result] += 1

    home_recall = percentage(
        correct_counts["HOME"],
        actual_counts["HOME"],
    )

    draw_recall = percentage(
        correct_counts["DRAW"],
        actual_counts["DRAW"],
    )

    away_recall = percentage(
        correct_counts["AWAY"],
        actual_counts["AWAY"],
    )

    macro_recall = round(
        (
            home_recall
            + draw_recall
            + away_recall
        ) / 3,
        2,
    )

    return {
        "evaluations": total,
        "accuracy": percentage(
            correct_results,
            total,
        ),
        "brier": average(
            [
                float(row.brier_score)
                for row in rows
            ]
        ),
        "log_loss": average(
            [
                float(row.log_loss)
                for row in rows
            ]
        ),
        "goal_error": average(
            [
                float(row.goal_error)
                for row in rows
            ]
        ),
        "home_recall": home_recall,
        "draw_recall": draw_recall,
        "away_recall": away_recall,
        "macro_recall": macro_recall,
    }


def determine_status(
    metrics: dict,
) -> str:

    evaluations = metrics["evaluations"]
    accuracy = metrics["accuracy"]
    brier = metrics["brier"]

    if evaluations == 0:
        return "UNVALIDATED"

    if evaluations < MINIMUM_EVALUATIONS:
        return "LIMITED"

    if (
        evaluations
        >= MINIMUM_RELIABLE_EVALUATIONS
        and accuracy
        >= RELIABLE_MINIMUM_ACCURACY
        and brier
        <= MAXIMUM_BRIER_SCORE
    ):
        return "RELIABLE"

    if (
        accuracy
        >= PROMISING_MINIMUM_ACCURACY
        and brier
        <= MAXIMUM_BRIER_SCORE
    ):
        return "PROMISING"

    return "WEAK"


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

        evaluations = (
            db.query(
                WalkForwardEvaluation
            )
            .order_by(
                WalkForwardEvaluation
                .kickoff_time.asc()
            )
            .all()
        )

        grouped_evaluations = defaultdict(
            list
        )

        for evaluation in evaluations:

            grouped_evaluations[
                evaluation.competition_id
            ].append(evaluation)

        upcoming_rows = (
            db.query(
                Fixture.competition_id,
                func.count(Fixture.id),
            )
            .filter(
                Fixture.status.in_(
                    UPCOMING_STATUSES
                ),
                Fixture.kickoff_time
                >= datetime.now(UTC).replace(tzinfo=None),
            )
            .group_by(
                Fixture.competition_id
            )
            .all()
        )

        upcoming_counts = {
            competition_id: count
            for competition_id, count
            in upcoming_rows
        }

        reports = []

        for competition in competitions:

            competition_id = (
                competition.id
            )

            metrics = calculate_metrics(
                grouped_evaluations.get(
                    competition_id,
                    [],
                )
            )

            status = determine_status(
                metrics
            )

            reports.append(
                {
                    "competition_id": (
                        competition_id
                    ),
                    "competition_name": (
                        getattr(
                            competition,
                            "name",
                            (
                                "Competition "
                                f"{competition_id}"
                            ),
                        )
                    ),
                    "status": status,
                    "upcoming_fixtures": (
                        upcoming_counts.get(
                            competition_id,
                            0,
                        )
                    ),
                    **metrics,
                }
            )

        reports.sort(
            key=lambda report: (
                STATUS_ORDER[
                    report["status"]
                ],
                -report["evaluations"],
                -report["accuracy"],
            )
        )

        print(
            "\nCOMPETITION RELIABILITY REPORT"
        )

        print("=" * 90)

        for report in reports:

            print(
                f"\n{report['competition_name']} "
                f"(ID {report['competition_id']})"
            )

            print(
                f"Status: "
                f"{report['status']}"
            )

            print(
                f"Walk-forward evaluations: "
                f"{report['evaluations']}"
            )

            print(
                f"Upcoming fixtures: "
                f"{report['upcoming_fixtures']}"
            )

            if (
                report["evaluations"]
                == 0
            ):
                print(
                    "No historical walk-forward "
                    "evidence is available."
                )

                continue

            print(
                f"Accuracy: "
                f"{report['accuracy']}%"
            )

            print(
                f"Brier: "
                f"{report['brier']}"
            )

            print(
                f"Log loss: "
                f"{report['log_loss']}"
            )

            print(
                f"Goal error: "
                f"{report['goal_error']}"
            )

            print(
                "Recall: "
                f"HOME="
                f"{report['home_recall']}% | "
                f"DRAW="
                f"{report['draw_recall']}% | "
                f"AWAY="
                f"{report['away_recall']}%"
            )

            print(
                f"Macro recall: "
                f"{report['macro_recall']}%"
            )

        status_counts = defaultdict(int)

        for report in reports:
            status_counts[
                report["status"]
            ] += 1

        print(
            "\nSTATUS SUMMARY"
        )

        print("=" * 90)

        for status in [
            "RELIABLE",
            "PROMISING",
            "LIMITED",
            "WEAK",
            "UNVALIDATED",
        ]:
            print(
                f"{status}: "
                f"{status_counts[status]}"
            )

        print(
            "\nSTATUS RULES"
        )

        print("=" * 90)

        print(
            "RELIABLE: at least "
            f"{MINIMUM_RELIABLE_EVALUATIONS} "
            "evaluations, accuracy at least "
            f"{RELIABLE_MINIMUM_ACCURACY}%, "
            "and Brier at most "
            f"{MAXIMUM_BRIER_SCORE}."
        )

        print(
            "PROMISING: at least "
            f"{MINIMUM_EVALUATIONS} "
            "evaluations, accuracy at least "
            f"{PROMISING_MINIMUM_ACCURACY}%, "
            "and Brier at most "
            f"{MAXIMUM_BRIER_SCORE}."
        )

        print(
            "LIMITED: historical evidence "
            f"exists but has fewer than "
            f"{MINIMUM_EVALUATIONS} "
            "evaluations."
        )

        print(
            "WEAK: enough evaluations exist, "
            "but the accuracy or Brier rule "
            "was not passed."
        )

        print(
            "UNVALIDATED: no walk-forward "
            "evaluations exist."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()