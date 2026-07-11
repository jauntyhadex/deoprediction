from dataclasses import dataclass

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


TRAIN_RATIO = 0.60
VALIDATION_RATIO = 0.20

MINIMUM_VALIDATION_FIXTURES = 20
MINIMUM_VALIDATION_COVERAGE = 15.0
MINIMUM_ACCURACY_IMPROVEMENT = 2.0

CONFIDENCE_THRESHOLDS = [
    35.0,
    40.0,
    45.0,
    50.0,
    55.0,
    60.0,
    65.0,
    70.0,
]

MARGIN_THRESHOLDS = [
    0.0,
    5.0,
    10.0,
    15.0,
    20.0,
    25.0,
]


@dataclass
class GateResult:
    minimum_confidence: float
    minimum_margin: float

    total_available: int
    selected: int
    correct: int

    coverage: float
    accuracy: float

    home_predictions: int
    draw_predictions: int
    away_predictions: int

    home_accuracy: float
    draw_accuracy: float
    away_accuracy: float

    average_brier: float
    average_log_loss: float

    quality_score: float


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


def prediction_details(
    row,
) -> tuple[str, float, float]:

    probabilities = {
        "HOME": float(
            row.home_win_probability
        ),
        "DRAW": float(
            row.draw_probability
        ),
        "AWAY": float(
            row.away_win_probability
        ),
    }

    ordered = sorted(
        probabilities.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    predicted_result = ordered[0][0]
    confidence = ordered[0][1]

    margin = (
        ordered[0][1]
        - ordered[1][1]
    )

    return (
        predicted_result,
        confidence,
        margin,
    )


def evaluate_gate(
    rows,
    minimum_confidence: float,
    minimum_margin: float,
) -> GateResult:

    selected_rows = []

    for row in rows:

        (
            predicted_result,
            confidence,
            margin,
        ) = prediction_details(row)

        if confidence < minimum_confidence:
            continue

        if margin < minimum_margin:
            continue

        selected_rows.append(
            (
                row,
                predicted_result,
            )
        )

    correct = 0

    prediction_counts = {
        "HOME": 0,
        "DRAW": 0,
        "AWAY": 0,
    }

    correct_counts = {
        "HOME": 0,
        "DRAW": 0,
        "AWAY": 0,
    }

    for row, predicted_result in selected_rows:

        prediction_counts[
            predicted_result
        ] += 1

        if predicted_result == row.actual_result:

            correct += 1

            correct_counts[
                predicted_result
            ] += 1

    selected = len(selected_rows)

    coverage = percentage(
        selected,
        len(rows),
    )

    accuracy = percentage(
        correct,
        selected,
    )

    home_accuracy = percentage(
        correct_counts["HOME"],
        prediction_counts["HOME"],
    )

    draw_accuracy = percentage(
        correct_counts["DRAW"],
        prediction_counts["DRAW"],
    )

    away_accuracy = percentage(
        correct_counts["AWAY"],
        prediction_counts["AWAY"],
    )

    average_brier = average(
        [
            float(row.brier_score)
            for row, _ in selected_rows
        ]
    )

    average_log_loss = average(
        [
            float(row.log_loss)
            for row, _ in selected_rows
        ]
    )

    quality_score = round(
        accuracy * 0.80
        + coverage * 0.20,
        4,
    )

    return GateResult(
        minimum_confidence=minimum_confidence,
        minimum_margin=minimum_margin,
        total_available=len(rows),
        selected=selected,
        correct=correct,
        coverage=coverage,
        accuracy=accuracy,
        home_predictions=prediction_counts["HOME"],
        draw_predictions=prediction_counts["DRAW"],
        away_predictions=prediction_counts["AWAY"],
        home_accuracy=home_accuracy,
        draw_accuracy=draw_accuracy,
        away_accuracy=away_accuracy,
        average_brier=average_brier,
        average_log_loss=average_log_loss,
        quality_score=quality_score,
    )


def find_best_gate(
    validation_rows,
) -> tuple[GateResult, GateResult]:

    baseline = evaluate_gate(
        rows=validation_rows,
        minimum_confidence=0.0,
        minimum_margin=0.0,
    )

    candidates = []

    for confidence in CONFIDENCE_THRESHOLDS:

        for margin in MARGIN_THRESHOLDS:

            result = evaluate_gate(
                rows=validation_rows,
                minimum_confidence=confidence,
                minimum_margin=margin,
            )

            if (
                result.selected
                < MINIMUM_VALIDATION_FIXTURES
            ):
                continue

            if (
                result.coverage
                < MINIMUM_VALIDATION_COVERAGE
            ):
                continue

            candidates.append(result)

    if not candidates:
        raise RuntimeError(
            "No quality gate had enough fixtures."
        )

    improved = [
        candidate
        for candidate in candidates
        if (
            candidate.accuracy
            >= baseline.accuracy
            + MINIMUM_ACCURACY_IMPROVEMENT
        )
    ]

    choices = (
        improved
        if improved
        else candidates
    )

    choices.sort(
        key=lambda result: (
            result.quality_score,
            result.accuracy,
            result.coverage,
            -result.average_brier,
        ),
        reverse=True,
    )

    return (
        baseline,
        choices[0],
    )


def print_result(
    title: str,
    result: GateResult,
) -> None:

    print(f"\n{title}")
    print("-" * 60)

    print(
        f"Minimum confidence: "
        f"{result.minimum_confidence}"
    )

    print(
        f"Minimum margin: "
        f"{result.minimum_margin}"
    )

    print(
        f"Available fixtures: "
        f"{result.total_available}"
    )

    print(
        f"Selected fixtures: "
        f"{result.selected}"
    )

    print(
        f"Coverage: "
        f"{result.coverage}%"
    )

    print(
        f"Correct: "
        f"{result.correct}"
    )

    print(
        f"Accuracy: "
        f"{result.accuracy}%"
    )

    print(
        f"Average Brier: "
        f"{result.average_brier}"
    )

    print(
        f"Average log loss: "
        f"{result.average_log_loss}"
    )

    print(
        "Predictions: "
        f"HOME={result.home_predictions} | "
        f"DRAW={result.draw_predictions} | "
        f"AWAY={result.away_predictions}"
    )

    print(
        "Accuracy by selection: "
        f"HOME={result.home_accuracy}% | "
        f"DRAW={result.draw_accuracy}% | "
        f"AWAY={result.away_accuracy}%"
    )


def main():

    db = SessionLocal()

    try:

        rows = (
            db.query(WalkForwardEvaluation)
            .order_by(
                WalkForwardEvaluation
                .kickoff_time.asc(),
                WalkForwardEvaluation.id.asc(),
            )
            .all()
        )

        if len(rows) < 100:
            raise RuntimeError(
                "Not enough walk-forward evaluations."
            )

        training_end = int(
            len(rows) * TRAIN_RATIO
        )

        validation_end = int(
            len(rows)
            * (
                TRAIN_RATIO
                + VALIDATION_RATIO
            )
        )

        validation_rows = rows[
            training_end:validation_end
        ]

        testing_rows = rows[
            validation_end:
        ]

        (
            validation_baseline,
            selected_gate,
        ) = find_best_gate(
            validation_rows
        )

        test_baseline = evaluate_gate(
            rows=testing_rows,
            minimum_confidence=0.0,
            minimum_margin=0.0,
        )

        test_selected = evaluate_gate(
            rows=testing_rows,
            minimum_confidence=(
                selected_gate.minimum_confidence
            ),
            minimum_margin=(
                selected_gate.minimum_margin
            ),
        )

        print_result(
            "VALIDATION BASELINE",
            validation_baseline,
        )

        print_result(
            "SELECTED VALIDATION GATE",
            selected_gate,
        )

        print_result(
            "TEST BASELINE",
            test_baseline,
        )

        print_result(
            "OUT-OF-SAMPLE QUALITY GATE",
            test_selected,
        )

        print("\nTEST CHANGE")
        print("-" * 60)

        print(
            "Accuracy change: "
            f"{(
                test_selected.accuracy
                - test_baseline.accuracy
            ):+.2f}%"
        )

        print(
            "Coverage: "
            f"{test_selected.coverage}%"
        )

        print(
            "Brier-score change: "
            f"{(
                test_selected.average_brier
                - test_baseline.average_brier
            ):+.4f}"
        )

        passed = (
            test_selected.selected >= 20
            and test_selected.accuracy
            > test_baseline.accuracy
            and test_selected.average_brier
            < test_baseline.average_brier
        )

        if passed:
            print(
                "\nQUALITY GATE PASSED"
            )
        else:
            print(
                "\nQUALITY GATE FAILED"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()