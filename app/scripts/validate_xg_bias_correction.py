import math
from dataclasses import dataclass

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


TRAIN_RATIO = 0.60
VALIDATION_RATIO = 0.20

MAXIMUM_GOALS = 10
MINIMUM_XG = 0.20
MAXIMUM_XG = 4.50

HOME_XG_CORRECTIONS = [
    0.00,
    0.025,
    0.050,
    0.075,
    0.100,
    0.125,
    0.150,
    0.175,
    0.200,
    0.225,
    0.250,
]

AWAY_XG_CORRECTIONS = [
    0.00,
    0.025,
    0.050,
    0.075,
    0.100,
    0.125,
    0.150,
    0.175,
    0.200,
]

MINIMUM_VALIDATION_BRIER_IMPROVEMENT = 0.0005
MINIMUM_VALIDATION_LOG_LOSS_IMPROVEMENT = 0.0010

MAXIMUM_VALIDATION_ACCURACY_DROP = 1.00


@dataclass
class XGBiasCorrection:

    home_subtraction: float
    away_addition: float


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
        6,
    )


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:

    return max(
        minimum,
        min(
            value,
            maximum,
        ),
    )


def poisson_probability(
    goals: int,
    expected_goals: float,
) -> float:

    return (
        math.exp(
            -expected_goals
        )
        * (
            expected_goals ** goals
        )
        / math.factorial(goals)
    )


def calculate_probabilities(
    home_xg: float,
    away_xg: float,
) -> dict:

    home_win_probability = 0.0
    draw_probability = 0.0
    away_win_probability = 0.0

    best_score_probability = -1.0
    predicted_home_score = 0
    predicted_away_score = 0

    home_goal_probabilities = [
        poisson_probability(
            goals=goals,
            expected_goals=home_xg,
        )
        for goals in range(
            MAXIMUM_GOALS + 1
        )
    ]

    away_goal_probabilities = [
        poisson_probability(
            goals=goals,
            expected_goals=away_xg,
        )
        for goals in range(
            MAXIMUM_GOALS + 1
        )
    ]

    total_probability = 0.0

    for home_goals in range(
        MAXIMUM_GOALS + 1
    ):

        for away_goals in range(
            MAXIMUM_GOALS + 1
        ):

            score_probability = (
                home_goal_probabilities[
                    home_goals
                ]
                * away_goal_probabilities[
                    away_goals
                ]
            )

            total_probability += (
                score_probability
            )

            if home_goals > away_goals:

                home_win_probability += (
                    score_probability
                )

            elif home_goals == away_goals:

                draw_probability += (
                    score_probability
                )

            else:

                away_win_probability += (
                    score_probability
                )

            if (
                score_probability
                > best_score_probability
            ):

                best_score_probability = (
                    score_probability
                )

                predicted_home_score = (
                    home_goals
                )

                predicted_away_score = (
                    away_goals
                )

    if total_probability <= 0:

        return {
            "HOME": 1 / 3,
            "DRAW": 1 / 3,
            "AWAY": 1 / 3,
            "predicted_home_score": 0,
            "predicted_away_score": 0,
        }

    return {
        "HOME": (
            home_win_probability
            / total_probability
        ),
        "DRAW": (
            draw_probability
            / total_probability
        ),
        "AWAY": (
            away_win_probability
            / total_probability
        ),
        "predicted_home_score": (
            predicted_home_score
        ),
        "predicted_away_score": (
            predicted_away_score
        ),
    }


def corrected_xg(
    row,
    correction: XGBiasCorrection | None,
) -> tuple[float, float]:

    home_xg = float(
        row.home_xg or 0
    )

    away_xg = float(
        row.away_xg or 0
    )

    if correction is not None:

        home_xg -= (
            correction.home_subtraction
        )

        away_xg += (
            correction.away_addition
        )

    home_xg = clamp(
        value=home_xg,
        minimum=MINIMUM_XG,
        maximum=MAXIMUM_XG,
    )

    away_xg = clamp(
        value=away_xg,
        minimum=MINIMUM_XG,
        maximum=MAXIMUM_XG,
    )

    return (
        home_xg,
        away_xg,
    )


def actual_result_vector(
    actual_result: str,
) -> dict:

    return {
        "HOME": (
            1.0
            if actual_result == "HOME"
            else 0.0
        ),
        "DRAW": (
            1.0
            if actual_result == "DRAW"
            else 0.0
        ),
        "AWAY": (
            1.0
            if actual_result == "AWAY"
            else 0.0
        ),
    }


def calculate_brier_score(
    probabilities: dict,
    actual_result: str,
) -> float:

    actual = actual_result_vector(
        actual_result
    )

    squared_errors = [
        (
            probabilities[result]
            - actual[result]
        ) ** 2
        for result in [
            "HOME",
            "DRAW",
            "AWAY",
        ]
    ]

    return sum(
        squared_errors
    ) / 3


def calculate_log_loss(
    probabilities: dict,
    actual_result: str,
) -> float:

    probability = clamp(
        value=probabilities[
            actual_result
        ],
        minimum=0.000001,
        maximum=0.999999,
    )

    return -math.log(
        probability
    )


def evaluate(
    rows,
    correction: XGBiasCorrection | None,
) -> dict:

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

    total_correct = 0
    exact_scores = 0

    brier_scores = []
    log_losses = []
    goal_errors = []

    predicted_home_goals = []
    predicted_away_goals = []

    actual_home_goals = []
    actual_away_goals = []

    for row in rows:

        actual_result = (
            row.actual_result
        )

        if (
            actual_result
            not in actual_counts
        ):
            continue

        home_xg, away_xg = corrected_xg(
            row=row,
            correction=correction,
        )

        probabilities = (
            calculate_probabilities(
                home_xg=home_xg,
                away_xg=away_xg,
            )
        )

        predicted_result = max(
            [
                "HOME",
                "DRAW",
                "AWAY",
            ],
            key=lambda result: (
                probabilities[result]
            ),
        )

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

            total_correct += 1

            correct_counts[
                actual_result
            ] += 1

        predicted_home_score = int(
            probabilities[
                "predicted_home_score"
            ]
        )

        predicted_away_score = int(
            probabilities[
                "predicted_away_score"
            ]
        )

        actual_home_score = int(
            row.actual_home_score or 0
        )

        actual_away_score = int(
            row.actual_away_score or 0
        )

        if (
            predicted_home_score
            == actual_home_score
            and predicted_away_score
            == actual_away_score
        ):

            exact_scores += 1

        brier_scores.append(
            calculate_brier_score(
                probabilities=probabilities,
                actual_result=actual_result,
            )
        )

        log_losses.append(
            calculate_log_loss(
                probabilities=probabilities,
                actual_result=actual_result,
            )
        )

        goal_errors.append(
            (
                abs(
                    home_xg
                    - actual_home_score
                )
                + abs(
                    away_xg
                    - actual_away_score
                )
            )
            / 2
        )

        predicted_home_goals.append(
            home_xg
        )

        predicted_away_goals.append(
            away_xg
        )

        actual_home_goals.append(
            float(
                actual_home_score
            )
        )

        actual_away_goals.append(
            float(
                actual_away_score
            )
        )

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
        )
        / 3,
        2,
    )

    predicted_home_average = average(
        predicted_home_goals
    )

    predicted_away_average = average(
        predicted_away_goals
    )

    actual_home_average = average(
        actual_home_goals
    )

    actual_away_average = average(
        actual_away_goals
    )

    return {
        "fixtures": len(rows),
        "correct": total_correct,
        "accuracy": percentage(
            total_correct,
            len(rows),
        ),
        "exact_score_accuracy": percentage(
            exact_scores,
            len(rows),
        ),
        "brier": average(
            brier_scores
        ),
        "log_loss": average(
            log_losses
        ),
        "goal_error": average(
            goal_errors
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
        "predicted_home_goals": (
            predicted_home_average
        ),
        "actual_home_goals": (
            actual_home_average
        ),
        "home_goal_bias": round(
            predicted_home_average
            - actual_home_average,
            6,
        ),
        "predicted_away_goals": (
            predicted_away_average
        ),
        "actual_away_goals": (
            actual_away_average
        ),
        "away_goal_bias": round(
            predicted_away_average
            - actual_away_average,
            6,
        ),
        "goal_gap_bias": round(
            (
                predicted_home_average
                - predicted_away_average
            )
            - (
                actual_home_average
                - actual_away_average
            ),
            6,
        ),
    }


def generate_corrections(
) -> list[XGBiasCorrection]:

    corrections = []

    for home_subtraction in (
        HOME_XG_CORRECTIONS
    ):

        for away_addition in (
            AWAY_XG_CORRECTIONS
        ):

            if (
                home_subtraction == 0
                and away_addition == 0
            ):
                continue

            corrections.append(
                XGBiasCorrection(
                    home_subtraction=(
                        home_subtraction
                    ),
                    away_addition=(
                        away_addition
                    ),
                )
            )

    return corrections


def select_correction(
    validation_rows,
) -> tuple[
    XGBiasCorrection | None,
    dict,
    dict | None,
]:

    baseline = evaluate(
        rows=validation_rows,
        correction=None,
    )

    candidates = []

    for correction in (
        generate_corrections()
    ):

        result = evaluate(
            rows=validation_rows,
            correction=correction,
        )

        accuracy_change = (
            result["accuracy"]
            - baseline["accuracy"]
        )

        brier_improvement = (
            baseline["brier"]
            - result["brier"]
        )

        log_loss_improvement = (
            baseline["log_loss"]
            - result["log_loss"]
        )

        if (
            accuracy_change
            < -MAXIMUM_VALIDATION_ACCURACY_DROP
        ):
            continue

        if (
            brier_improvement
            < (
                MINIMUM_VALIDATION_BRIER_IMPROVEMENT
            )
        ):
            continue

        if (
            log_loss_improvement
            < (
                MINIMUM_VALIDATION_LOG_LOSS_IMPROVEMENT
            )
        ):
            continue

        candidates.append(
            (
                correction,
                result,
            )
        )

    if not candidates:

        return (
            None,
            baseline,
            None,
        )

    candidates.sort(
        key=lambda item: (
            -item[1]["brier"],
            -item[1]["log_loss"],
            item[1]["accuracy"],
            item[1]["macro_recall"],
            -abs(
                item[1]["goal_gap_bias"]
            ),
        ),
        reverse=True,
    )

    selected_correction = (
        candidates[0][0]
    )

    selected_result = (
        candidates[0][1]
    )

    return (
        selected_correction,
        baseline,
        selected_result,
    )


def print_correction(
    correction: XGBiasCorrection,
) -> None:

    print(
        "Home xG subtraction: "
        f"{correction.home_subtraction}"
    )

    print(
        "Away xG addition: "
        f"{correction.away_addition}"
    )


def print_result(
    title: str,
    result: dict,
) -> None:

    print()
    print(title)
    print("-" * 75)

    print(
        f"Fixtures: "
        f"{result['fixtures']}"
    )

    print(
        f"Correct: "
        f"{result['correct']}"
    )

    print(
        f"Accuracy: "
        f"{result['accuracy']}%"
    )

    print(
        f"Exact-score accuracy: "
        f"{result['exact_score_accuracy']}%"
    )

    print(
        f"Brier: "
        f"{result['brier']}"
    )

    print(
        f"Log loss: "
        f"{result['log_loss']}"
    )

    print(
        f"Goal error: "
        f"{result['goal_error']}"
    )

    print(
        "Recall: "
        f"HOME={result['home_recall']}% | "
        f"DRAW={result['draw_recall']}% | "
        f"AWAY={result['away_recall']}%"
    )

    print(
        f"Macro recall: "
        f"{result['macro_recall']}%"
    )

    print(
        "Predictions: "
        f"HOME={result['predicted_home']} | "
        f"DRAW={result['predicted_draw']} | "
        f"AWAY={result['predicted_away']}"
    )

    print(
        "Home goals: "
        f"predicted="
        f"{result['predicted_home_goals']} | "
        f"actual="
        f"{result['actual_home_goals']} | "
        f"bias="
        f"{result['home_goal_bias']:+.6f}"
    )

    print(
        "Away goals: "
        f"predicted="
        f"{result['predicted_away_goals']} | "
        f"actual="
        f"{result['actual_away_goals']} | "
        f"bias="
        f"{result['away_goal_bias']:+.6f}"
    )

    print(
        "Home-minus-away goal-gap bias: "
        f"{result['goal_gap_bias']:+.6f}"
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

        if len(rows) < 300:

            raise RuntimeError(
                "Not enough walk-forward "
                "evaluations."
            )

        training_end = int(
            len(rows)
            * TRAIN_RATIO
        )

        validation_end = int(
            len(rows)
            * (
                TRAIN_RATIO
                + VALIDATION_RATIO
            )
        )

        training_rows = rows[
            :training_end
        ]

        validation_rows = rows[
            training_end:validation_end
        ]

        test_rows = rows[
            validation_end:
        ]

        print(
            "\nXG BIAS CORRECTION VALIDATION"
        )

        print("=" * 75)

        print(
            f"Total evaluations: "
            f"{len(rows)}"
        )

        print(
            f"Training rows: "
            f"{len(training_rows)}"
        )

        print(
            f"Validation rows: "
            f"{len(validation_rows)}"
        )

        print(
            f"Test rows: "
            f"{len(test_rows)}"
        )

        (
            selected_correction,
            validation_baseline,
            validation_selected,
        ) = select_correction(
            validation_rows
        )

        print_result(
            title="VALIDATION BASELINE",
            result=validation_baseline,
        )

        if selected_correction is None:

            print()
            print(
                "NO XG CORRECTION PASSED "
                "VALIDATION"
            )

            print()
            print(
                "XG BIAS CORRECTION "
                "VALIDATION FAILED"
            )

            return

        print()
        print(
            "SELECTED XG CORRECTION"
        )

        print("-" * 75)

        print_correction(
            selected_correction
        )

        print_result(
            title=(
                "SELECTED VALIDATION RESULT"
            ),
            result=validation_selected,
        )

        test_baseline = evaluate(
            rows=test_rows,
            correction=None,
        )

        test_selected = evaluate(
            rows=test_rows,
            correction=(
                selected_correction
            ),
        )

        print_result(
            title="OUT-OF-SAMPLE BASELINE",
            result=test_baseline,
        )

        print_result(
            title=(
                "OUT-OF-SAMPLE "
                "CORRECTED XG"
            ),
            result=test_selected,
        )

        accuracy_change = round(
            test_selected["accuracy"]
            - test_baseline["accuracy"],
            2,
        )

        brier_change = round(
            test_selected["brier"]
            - test_baseline["brier"],
            6,
        )

        log_loss_change = round(
            test_selected["log_loss"]
            - test_baseline["log_loss"],
            6,
        )

        macro_recall_change = round(
            test_selected["macro_recall"]
            - test_baseline["macro_recall"],
            2,
        )

        goal_gap_bias_change = round(
            abs(
                test_selected[
                    "goal_gap_bias"
                ]
            )
            - abs(
                test_baseline[
                    "goal_gap_bias"
                ]
            ),
            6,
        )

        print()
        print(
            "OUT-OF-SAMPLE CHANGE"
        )

        print("-" * 75)

        print(
            f"Accuracy change: "
            f"{accuracy_change:+.2f}%"
        )

        print(
            f"Brier change: "
            f"{brier_change:+.6f}"
        )

        print(
            f"Log-loss change: "
            f"{log_loss_change:+.6f}"
        )

        print(
            f"Macro-recall change: "
            f"{macro_recall_change:+.2f}%"
        )

        print(
            "Absolute goal-gap-bias change: "
            f"{goal_gap_bias_change:+.6f}"
        )

        passed = (
            brier_change < 0
            and log_loss_change < 0
            and accuracy_change >= -1.0
            and goal_gap_bias_change < 0
        )

        if passed:

            print()
            print(
                "XG BIAS CORRECTION "
                "VALIDATION PASSED"
            )

        else:

            print()
            print(
                "XG BIAS CORRECTION "
                "VALIDATION FAILED"
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()