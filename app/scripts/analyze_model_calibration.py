from collections import defaultdict

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


PROBABILITY_BANDS = [
    (0.0, 10.0),
    (10.0, 20.0),
    (20.0, 30.0),
    (30.0, 40.0),
    (40.0, 50.0),
    (50.0, 60.0),
    (60.0, 70.0),
    (70.0, 80.0),
    (80.0, 90.0),
    (90.0, 100.01),
]


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


def average(
    values: list[float],
) -> float:

    if not values:
        return 0.0

    return round(
        sum(values) / len(values),
        4,
    )


def mean_absolute_error(
    predicted_values: list[float],
    actual_values: list[float],
) -> float:

    if not predicted_values:
        return 0.0

    errors = [
        abs(predicted - actual)
        for predicted, actual
        in zip(
            predicted_values,
            actual_values,
        )
    ]

    return average(errors)


def get_probability(
    row,
    result: str,
) -> float:

    if result == "HOME":
        return float(
            row.home_win_probability
            or 0
        )

    if result == "DRAW":
        return float(
            row.draw_probability
            or 0
        )

    return float(
        row.away_win_probability
        or 0
    )


def get_predicted_result(
    row,
) -> str:

    probabilities = {
        "HOME": get_probability(
            row,
            "HOME",
        ),
        "DRAW": get_probability(
            row,
            "DRAW",
        ),
        "AWAY": get_probability(
            row,
            "AWAY",
        ),
    }

    return max(
        probabilities,
        key=probabilities.get,
    )


def print_overall_goal_calibration(
    rows,
) -> None:

    predicted_home = [
        float(row.home_xg or 0)
        for row in rows
    ]

    predicted_away = [
        float(row.away_xg or 0)
        for row in rows
    ]

    actual_home = [
        float(row.actual_home_score or 0)
        for row in rows
    ]

    actual_away = [
        float(row.actual_away_score or 0)
        for row in rows
    ]

    predicted_total = [
        home + away
        for home, away
        in zip(
            predicted_home,
            predicted_away,
        )
    ]

    actual_total = [
        home + away
        for home, away
        in zip(
            actual_home,
            actual_away,
        )
    ]

    predicted_home_average = average(
        predicted_home
    )

    predicted_away_average = average(
        predicted_away
    )

    actual_home_average = average(
        actual_home
    )

    actual_away_average = average(
        actual_away
    )

    print(
        "\nOVERALL EXPECTED-GOALS CALIBRATION"
    )

    print("=" * 90)

    print(
        f"Evaluations: "
        f"{len(rows)}"
    )

    print(
        "Home goals | "
        f"Predicted={predicted_home_average} | "
        f"Actual={actual_home_average} | "
        f"Bias={round(
            predicted_home_average
            - actual_home_average,
            4,
        ):+.4f} | "
        f"MAE={mean_absolute_error(
            predicted_home,
            actual_home,
        )}"
    )

    print(
        "Away goals | "
        f"Predicted={predicted_away_average} | "
        f"Actual={actual_away_average} | "
        f"Bias={round(
            predicted_away_average
            - actual_away_average,
            4,
        ):+.4f} | "
        f"MAE={mean_absolute_error(
            predicted_away,
            actual_away,
        )}"
    )

    predicted_total_average = average(
        predicted_total
    )

    actual_total_average = average(
        actual_total
    )

    print(
        "Total goals | "
        f"Predicted={predicted_total_average} | "
        f"Actual={actual_total_average} | "
        f"Bias={round(
            predicted_total_average
            - actual_total_average,
            4,
        ):+.4f} | "
        f"MAE={mean_absolute_error(
            predicted_total,
            actual_total,
        )}"
    )

    predicted_goal_gap = average(
        [
            home - away
            for home, away
            in zip(
                predicted_home,
                predicted_away,
            )
        ]
    )

    actual_goal_gap = average(
        [
            home - away
            for home, away
            in zip(
                actual_home,
                actual_away,
            )
        ]
    )

    print(
        "Home-minus-away goal gap | "
        f"Predicted={predicted_goal_gap} | "
        f"Actual={actual_goal_gap} | "
        f"Bias={round(
            predicted_goal_gap
            - actual_goal_gap,
            4,
        ):+.4f}"
    )


def print_result_distribution(
    rows,
) -> None:

    actual_counts = {
        "HOME": 0,
        "DRAW": 0,
        "AWAY": 0,
    }

    predicted_counts = {
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

        actual_result = (
            row.actual_result
        )

        predicted_result = (
            get_predicted_result(row)
        )

        if actual_result in actual_counts:
            actual_counts[
                actual_result
            ] += 1

        predicted_counts[
            predicted_result
        ] += 1

        if (
            predicted_result
            == actual_result
        ):
            correct_counts[
                actual_result
            ] += 1

    print(
        "\nRESULT DISTRIBUTION"
    )

    print("=" * 90)

    print(
        "Result | Actual count | Actual rate | "
        "Predicted count | Predicted rate | Recall"
    )

    print("-" * 90)

    for result in [
        "HOME",
        "DRAW",
        "AWAY",
    ]:

        print(
            f"{result:6} | "
            f"{actual_counts[result]:12} | "
            f"{percentage(
                actual_counts[result],
                len(rows),
            ):10.2f}% | "
            f"{predicted_counts[result]:15} | "
            f"{percentage(
                predicted_counts[result],
                len(rows),
            ):13.2f}% | "
            f"{percentage(
                correct_counts[result],
                actual_counts[result],
            ):6.2f}%"
        )


def print_probability_calibration(
    rows,
    result: str,
) -> None:

    print()
    print(
        f"{result} PROBABILITY CALIBRATION"
    )

    print("=" * 90)

    print(
        "Probability band | Fixtures | "
        "Average prediction | Observed rate | "
        "Calibration gap"
    )

    print("-" * 90)

    for lower, upper in (
        PROBABILITY_BANDS
    ):

        selected = [
            row
            for row in rows
            if (
                get_probability(
                    row,
                    result,
                )
                >= lower
                and get_probability(
                    row,
                    result,
                )
                < upper
            )
        ]

        if not selected:
            continue

        average_prediction = average(
            [
                get_probability(
                    row,
                    result,
                )
                for row in selected
            ]
        )

        observed_count = sum(
            1
            for row in selected
            if row.actual_result
            == result
        )

        observed_rate = percentage(
            observed_count,
            len(selected),
        )

        calibration_gap = round(
            average_prediction
            - observed_rate,
            2,
        )

        upper_label = (
            "100"
            if upper > 100
            else str(int(upper))
        )

        print(
            f"{int(lower):02d}-"
            f"{upper_label:>3}% | "
            f"{len(selected):8} | "
            f"{average_prediction:18.2f}% | "
            f"{observed_rate:13.2f}% | "
            f"{calibration_gap:+15.2f}%"
        )


def print_competition_calibration(
    rows,
    competition_names: dict[int, str],
) -> None:

    grouped = defaultdict(list)

    for row in rows:
        grouped[
            row.competition_id
        ].append(row)

    print(
        "\nCALIBRATION BY COMPETITION"
    )

    print("=" * 125)

    print(
        "Competition | Fixtures | "
        "Home xG bias | Away xG bias | "
        "Total xG bias | Actual draw rate | "
        "Average draw probability | Accuracy"
    )

    print("-" * 125)

    reports = []

    for (
        competition_id,
        competition_rows,
    ) in grouped.items():

        predicted_home = average(
            [
                float(row.home_xg or 0)
                for row in competition_rows
            ]
        )

        predicted_away = average(
            [
                float(row.away_xg or 0)
                for row in competition_rows
            ]
        )

        actual_home = average(
            [
                float(
                    row.actual_home_score
                    or 0
                )
                for row in competition_rows
            ]
        )

        actual_away = average(
            [
                float(
                    row.actual_away_score
                    or 0
                )
                for row in competition_rows
            ]
        )

        correct = sum(
            1
            for row in competition_rows
            if (
                get_predicted_result(row)
                == row.actual_result
            )
        )

        actual_draws = sum(
            1
            for row in competition_rows
            if row.actual_result == "DRAW"
        )

        reports.append(
            {
                "name": (
                    competition_names.get(
                        competition_id,
                        (
                            "Competition "
                            f"{competition_id}"
                        ),
                    )
                ),
                "fixtures": len(
                    competition_rows
                ),
                "home_bias": round(
                    predicted_home
                    - actual_home,
                    4,
                ),
                "away_bias": round(
                    predicted_away
                    - actual_away,
                    4,
                ),
                "total_bias": round(
                    (
                        predicted_home
                        + predicted_away
                    )
                    - (
                        actual_home
                        + actual_away
                    ),
                    4,
                ),
                "draw_rate": percentage(
                    actual_draws,
                    len(
                        competition_rows
                    ),
                ),
                "draw_probability": average(
                    [
                        float(
                            row.draw_probability
                            or 0
                        )
                        for row
                        in competition_rows
                    ]
                ),
                "accuracy": percentage(
                    correct,
                    len(
                        competition_rows
                    ),
                ),
            }
        )

    reports.sort(
        key=lambda report: (
            report["fixtures"],
            report["accuracy"],
        ),
        reverse=True,
    )

    for report in reports:

        print(
            f"{report['name'][:30]:30} | "
            f"{report['fixtures']:8} | "
            f"{report['home_bias']:+12.4f} | "
            f"{report['away_bias']:+12.4f} | "
            f"{report['total_bias']:+13.4f} | "
            f"{report['draw_rate']:16.2f}% | "
            f"{report['draw_probability']:24.2f}% | "
            f"{report['accuracy']:8.2f}%"
        )


def main():

    db = SessionLocal()

    try:

        rows = (
            db.query(
                WalkForwardEvaluation
            )
            .order_by(
                WalkForwardEvaluation
                .kickoff_time.asc(),
                WalkForwardEvaluation
                .id.asc(),
            )
            .all()
        )

        competitions = (
            db.query(Competition)
            .all()
        )

        competition_names = {
            competition.id: (
                competition.name
            )
            for competition in competitions
        }

        if not rows:

            raise RuntimeError(
                "No walk-forward evaluations "
                "were found."
            )

        print_overall_goal_calibration(
            rows
        )

        print_result_distribution(
            rows
        )

        for result in [
            "HOME",
            "DRAW",
            "AWAY",
        ]:

            print_probability_calibration(
                rows=rows,
                result=result,
            )

        print_competition_calibration(
            rows=rows,
            competition_names=(
                competition_names
            ),
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()