from collections import defaultdict

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


MINIMUM_COMPETITION_FIXTURES = 15

HISTORY_THRESHOLDS = [
    3,
    5,
    7,
    10,
]


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
    rows,
) -> dict:
    total = len(rows)

    correct_results = sum(
        1
        for row in rows
        if row.result_correct
    )

    exact_scores = sum(
        1
        for row in rows
        if row.score_correct
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

    predicted_counts = {
        "HOME": 0,
        "DRAW": 0,
        "AWAY": 0,
    }

    for row in rows:
        actual_counts[
            row.actual_result
        ] += 1

        predicted_counts[
            row.predicted_result
        ] += 1

        if row.result_correct:
            correct_counts[
                row.actual_result
            ] += 1

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
        "fixtures": total,
        "accuracy": percentage(
            correct_results,
            total,
        ),
        "exact_score_accuracy": percentage(
            exact_scores,
            total,
        ),
        "average_brier": average(
            [
                float(row.brier_score)
                for row in rows
            ]
        ),
        "average_log_loss": average(
            [
                float(row.log_loss)
                for row in rows
            ]
        ),
        "average_goal_error": average(
            [
                float(row.goal_error)
                for row in rows
            ]
        ),
        "home_recall": home_recall,
        "draw_recall": draw_recall,
        "away_recall": away_recall,
        "macro_recall": macro_recall,
        "predicted_home": (
            predicted_counts["HOME"]
        ),
        "predicted_draw": (
            predicted_counts["DRAW"]
        ),
        "predicted_away": (
            predicted_counts["AWAY"]
        ),
    }


def print_metrics(
    title: str,
    metrics: dict,
) -> None:
    print(f"\n{title}")
    print("-" * 70)

    print(
        f"Fixtures: "
        f"{metrics['fixtures']}"
    )

    print(
        f"Accuracy: "
        f"{metrics['accuracy']}%"
    )

    print(
        f"Exact score: "
        f"{metrics['exact_score_accuracy']}%"
    )

    print(
        f"Brier: "
        f"{metrics['average_brier']}"
    )

    print(
        f"Log loss: "
        f"{metrics['average_log_loss']}"
    )

    print(
        f"Goal error: "
        f"{metrics['average_goal_error']}"
    )

    print(
        "Recall: "
        f"HOME={metrics['home_recall']}% | "
        f"DRAW={metrics['draw_recall']}% | "
        f"AWAY={metrics['away_recall']}%"
    )

    print(
        f"Macro recall: "
        f"{metrics['macro_recall']}%"
    )

    print(
        "Predictions: "
        f"HOME={metrics['predicted_home']} | "
        f"DRAW={metrics['predicted_draw']} | "
        f"AWAY={metrics['predicted_away']}"
    )


def main():
    db = SessionLocal()

    try:
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

        competitions = (
            db.query(Competition)
            .all()
        )

        competition_names = {
            competition.id: getattr(
                competition,
                "name",
                f"Competition {competition.id}",
            )
            for competition in competitions
        }

        print_metrics(
            "OVERALL WALK-FORWARD QUALITY",
            calculate_metrics(
                evaluations
            ),
        )

        print(
            "\nQUALITY BY MINIMUM TEAM HISTORY"
        )
        print("=" * 70)

        for threshold in HISTORY_THRESHOLDS:
            rows = [
                row
                for row in evaluations
                if (
                    row.home_history_matches
                    >= threshold
                    and row.away_history_matches
                    >= threshold
                )
            ]

            print_metrics(
                (
                    f"MINIMUM {threshold} "
                    f"PREVIOUS MATCHES"
                ),
                calculate_metrics(rows),
            )

        grouped = defaultdict(list)

        for evaluation in evaluations:
            grouped[
                evaluation.competition_id
            ].append(evaluation)

        competition_reports = []

        for competition_id, rows in grouped.items():
            if (
                len(rows)
                < MINIMUM_COMPETITION_FIXTURES
            ):
                continue

            metrics = calculate_metrics(
                rows
            )

            metrics["competition_id"] = (
                competition_id
            )

            metrics["competition_name"] = (
                competition_names.get(
                    competition_id,
                    (
                        f"Competition "
                        f"{competition_id}"
                    ),
                )
            )

            competition_reports.append(
                metrics
            )

        competition_reports.sort(
            key=lambda report: (
                report["accuracy"],
                report["fixtures"],
            ),
            reverse=True,
        )

        print(
            "\nQUALITY BY COMPETITION"
        )
        print("=" * 70)

        for report in competition_reports:
            print(
                f"\n{report['competition_name']} "
                f"(ID {report['competition_id']})"
            )

            print(
                f"Fixtures: "
                f"{report['fixtures']} | "
                f"Accuracy: "
                f"{report['accuracy']}% | "
                f"Brier: "
                f"{report['average_brier']} | "
                f"Goal error: "
                f"{report['average_goal_error']}"
            )

            print(
                "Recall: "
                f"HOME={report['home_recall']}% | "
                f"DRAW={report['draw_recall']}% | "
                f"AWAY={report['away_recall']}%"
            )

        reliable_competitions = [
            report
            for report in competition_reports
            if (
                report["accuracy"] >= 55
                and report["average_brier"]
                <= 0.20
                and report["fixtures"]
                >= MINIMUM_COMPETITION_FIXTURES
            )
        ]

        print(
            "\nRELIABLE COMPETITIONS"
        )
        print("=" * 70)

        if not reliable_competitions:
            print(
                "No competition currently "
                "passes the reliability rules."
            )

        for report in reliable_competitions:
            print(
                f"{report['competition_name']} | "
                f"Fixtures: "
                f"{report['fixtures']} | "
                f"Accuracy: "
                f"{report['accuracy']}% | "
                f"Brier: "
                f"{report['average_brier']}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()