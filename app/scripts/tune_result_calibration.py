import math
from dataclasses import dataclass

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


TRAIN_RATIO = 0.60
VALIDATION_RATIO = 0.20

MAX_VALIDATION_ACCURACY_LOSS = 2.0
MAX_VALIDATION_LOG_LOSS_INCREASE = 0.05

MIN_HOME_RECALL = 50.0
MIN_DRAW_RECALL = 10.0
MIN_AWAY_RECALL = 15.0


@dataclass
class CalibrationResult:
    home_multiplier: float
    draw_multiplier: float
    away_multiplier: float
    temperature: float

    fixtures: int
    correct: int
    accuracy: float

    home_recall: float
    draw_recall: float
    away_recall: float

    macro_recall: float
    minimum_recall: float
    balanced_score: float

    average_brier_score: float
    average_log_loss: float

    predicted_home: int
    predicted_draw: int
    predicted_away: int


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


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(
        minimum,
        min(float(value), maximum),
    )


def calibrate_probabilities(
    home_probability: float,
    draw_probability: float,
    away_probability: float,
    home_multiplier: float,
    draw_multiplier: float,
    away_multiplier: float,
    temperature: float,
) -> dict:

    home = clamp(
        home_probability / 100,
        0.000001,
        0.999999,
    )

    draw = clamp(
        draw_probability / 100,
        0.000001,
        0.999999,
    )

    away = clamp(
        away_probability / 100,
        0.000001,
        0.999999,
    )

    exponent = 1 / temperature

    home_score = (
        home ** exponent
    ) * home_multiplier

    draw_score = (
        draw ** exponent
    ) * draw_multiplier

    away_score = (
        away ** exponent
    ) * away_multiplier

    total = (
        home_score
        + draw_score
        + away_score
    )

    if total <= 0:
        return {
            "HOME": 33.33,
            "DRAW": 33.34,
            "AWAY": 33.33,
        }

    return {
        "HOME": round(
            (home_score / total) * 100,
            4,
        ),
        "DRAW": round(
            (draw_score / total) * 100,
            4,
        ),
        "AWAY": round(
            (away_score / total) * 100,
            4,
        ),
    }


def calculate_brier_score(
    probabilities: dict,
    actual_result: str,
) -> float:

    targets = {
        "HOME": 0.0,
        "DRAW": 0.0,
        "AWAY": 0.0,
    }

    targets[actual_result] = 1.0

    score = sum(
        (
            probabilities[result] / 100
            - targets[result]
        ) ** 2
        for result in targets
    ) / 3

    return score


def calculate_log_loss(
    probabilities: dict,
    actual_result: str,
) -> float:

    actual_probability = clamp(
        probabilities[actual_result] / 100,
        0.000001,
        0.999999,
    )

    return -math.log(
        actual_probability
    )


def evaluate(
    rows,
    home_multiplier: float,
    draw_multiplier: float,
    away_multiplier: float,
    temperature: float,
) -> CalibrationResult:

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

    correct = 0
    brier_scores = []
    log_losses = []

    for row in rows:

        probabilities = calibrate_probabilities(
            home_probability=float(
                row.home_win_probability
            ),
            draw_probability=float(
                row.draw_probability
            ),
            away_probability=float(
                row.away_win_probability
            ),
            home_multiplier=home_multiplier,
            draw_multiplier=draw_multiplier,
            away_multiplier=away_multiplier,
            temperature=temperature,
        )

        predicted_result = max(
            probabilities,
            key=probabilities.get,
        )

        actual_result = (
            row.actual_result
        )

        actual_counts[
            actual_result
        ] += 1

        predicted_counts[
            predicted_result
        ] += 1

        if predicted_result == actual_result:
            correct += 1

            correct_counts[
                actual_result
            ] += 1

        brier_scores.append(
            calculate_brier_score(
                probabilities,
                actual_result,
            )
        )

        log_losses.append(
            calculate_log_loss(
                probabilities,
                actual_result,
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

    accuracy = percentage(
        correct,
        len(rows),
    )

    macro_recall = round(
        (
            home_recall
            + draw_recall
            + away_recall
        ) / 3,
        2,
    )

    minimum_recall = min(
        home_recall,
        draw_recall,
        away_recall,
    )

    balanced_score = round(
        accuracy * 0.45
        + macro_recall * 0.40
        + minimum_recall * 0.15,
        4,
    )

    return CalibrationResult(
        home_multiplier=home_multiplier,
        draw_multiplier=draw_multiplier,
        away_multiplier=away_multiplier,
        temperature=temperature,
        fixtures=len(rows),
        correct=correct,
        accuracy=accuracy,
        home_recall=home_recall,
        draw_recall=draw_recall,
        away_recall=away_recall,
        macro_recall=macro_recall,
        minimum_recall=minimum_recall,
        balanced_score=balanced_score,
        average_brier_score=average(
            brier_scores
        ),
        average_log_loss=average(
            log_losses
        ),
        predicted_home=(
            predicted_counts["HOME"]
        ),
        predicted_draw=(
            predicted_counts["DRAW"]
        ),
        predicted_away=(
            predicted_counts["AWAY"]
        ),
    )


def generate_training_candidates(
    training_rows,
) -> list[CalibrationResult]:

    candidates = []

    home_multipliers = [
        0.70,
        0.75,
        0.80,
        0.85,
        0.90,
        0.95,
        1.00,
    ]

    draw_multipliers = [
        1.00,
        1.10,
        1.20,
        1.30,
        1.40,
        1.50,
        1.60,
        1.70,
        1.80,
    ]

    away_multipliers = [
        1.00,
        1.10,
        1.20,
        1.30,
        1.40,
        1.50,
        1.60,
        1.70,
        1.80,
    ]

    temperatures = [
        0.80,
        0.90,
        1.00,
        1.10,
        1.20,
        1.30,
    ]

    for home_multiplier in home_multipliers:

        for draw_multiplier in draw_multipliers:

            for away_multiplier in away_multipliers:

                for temperature in temperatures:

                    result = evaluate(
                        rows=training_rows,
                        home_multiplier=(
                            home_multiplier
                        ),
                        draw_multiplier=(
                            draw_multiplier
                        ),
                        away_multiplier=(
                            away_multiplier
                        ),
                        temperature=temperature,
                    )

                    if (
                        result.home_recall >= 50
                        and result.draw_recall >= 10
                        and result.away_recall >= 15
                    ):
                        candidates.append(
                            result
                        )

    if not candidates:
        raise RuntimeError(
            "No training calibration passed."
        )

    candidates.sort(
        key=lambda result: (
            result.balanced_score,
            result.macro_recall,
            result.accuracy,
            -result.average_log_loss,
        ),
        reverse=True,
    )

    return candidates[:300]


def select_validation_candidate(
    training_candidates,
    validation_rows,
) -> tuple[
    CalibrationResult,
    CalibrationResult,
]:

    baseline = evaluate(
        rows=validation_rows,
        home_multiplier=1.0,
        draw_multiplier=1.0,
        away_multiplier=1.0,
        temperature=1.0,
    )

    qualified = []
    fallback = []

    for candidate in training_candidates:

        result = evaluate(
            rows=validation_rows,
            home_multiplier=(
                candidate.home_multiplier
            ),
            draw_multiplier=(
                candidate.draw_multiplier
            ),
            away_multiplier=(
                candidate.away_multiplier
            ),
            temperature=(
                candidate.temperature
            ),
        )

        fallback.append(result)

        accuracy_is_valid = (
            result.accuracy
            >= baseline.accuracy
            - MAX_VALIDATION_ACCURACY_LOSS
        )

        log_loss_is_valid = (
            result.average_log_loss
            <= baseline.average_log_loss
            + MAX_VALIDATION_LOG_LOSS_INCREASE
        )

        recall_is_valid = (
            result.home_recall
            >= MIN_HOME_RECALL
            and result.draw_recall
            >= MIN_DRAW_RECALL
            and result.away_recall
            >= MIN_AWAY_RECALL
        )

        if (
            accuracy_is_valid
            and log_loss_is_valid
            and recall_is_valid
        ):
            qualified.append(result)

    choices = (
        qualified
        if qualified
        else fallback
    )

    choices.sort(
        key=lambda result: (
            result.balanced_score,
            result.macro_recall,
            result.accuracy,
            -result.average_log_loss,
        ),
        reverse=True,
    )

    return (
        baseline,
        choices[0],
    )


def print_result(
    title: str,
    result: CalibrationResult,
) -> None:

    print(f"\n{title}")
    print("-" * 60)

    print(
        f"Fixtures: {result.fixtures}"
    )

    print(
        f"Correct: {result.correct}"
    )

    print(
        f"Accuracy: {result.accuracy}%"
    )

    print(
        f"Home recall: "
        f"{result.home_recall}%"
    )

    print(
        f"Draw recall: "
        f"{result.draw_recall}%"
    )

    print(
        f"Away recall: "
        f"{result.away_recall}%"
    )

    print(
        f"Macro recall: "
        f"{result.macro_recall}%"
    )

    print(
        f"Minimum recall: "
        f"{result.minimum_recall}%"
    )

    print(
        f"Balanced score: "
        f"{result.balanced_score}"
    )

    print(
        f"Average Brier score: "
        f"{result.average_brier_score}"
    )

    print(
        f"Average log loss: "
        f"{result.average_log_loss}"
    )

    print(
        "Predictions: "
        f"HOME={result.predicted_home}, "
        f"DRAW={result.predicted_draw}, "
        f"AWAY={result.predicted_away}"
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
                WalkForwardEvaluation.id.asc(),
            )
            .all()
        )

        if len(rows) < 100:
            raise RuntimeError(
                "Not enough evaluations."
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

        training_rows = rows[
            :training_end
        ]

        validation_rows = rows[
            training_end:validation_end
        ]

        testing_rows = rows[
            validation_end:
        ]

        candidates = (
            generate_training_candidates(
                training_rows
            )
        )

        (
            validation_baseline,
            selected,
        ) = select_validation_candidate(
            candidates,
            validation_rows,
        )

        test_baseline = evaluate(
            rows=testing_rows,
            home_multiplier=1.0,
            draw_multiplier=1.0,
            away_multiplier=1.0,
            temperature=1.0,
        )

        test_calibrated = evaluate(
            rows=testing_rows,
            home_multiplier=(
                selected.home_multiplier
            ),
            draw_multiplier=(
                selected.draw_multiplier
            ),
            away_multiplier=(
                selected.away_multiplier
            ),
            temperature=(
                selected.temperature
            ),
        )

        print("\nSELECTED RESULT CALIBRATION")
        print("-" * 60)

        print(
            f"Home multiplier: "
            f"{selected.home_multiplier}"
        )

        print(
            f"Draw multiplier: "
            f"{selected.draw_multiplier}"
        )

        print(
            f"Away multiplier: "
            f"{selected.away_multiplier}"
        )

        print(
            f"Temperature: "
            f"{selected.temperature}"
        )

        print_result(
            "VALIDATION BASELINE",
            validation_baseline,
        )

        print_result(
            "VALIDATION CALIBRATED",
            selected,
        )

        print_result(
            "TEST BASELINE",
            test_baseline,
        )

        print_result(
            "TEST CALIBRATED",
            test_calibrated,
        )

        print("\nTEST CHANGE")
        print("-" * 60)

        print(
            "Accuracy change: "
            f"{(
                test_calibrated.accuracy
                - test_baseline.accuracy
            ):+.2f}%"
        )

        print(
            "Macro-recall change: "
            f"{(
                test_calibrated.macro_recall
                - test_baseline.macro_recall
            ):+.2f}%"
        )

        print(
            "Brier-score change: "
            f"{(
                test_calibrated.average_brier_score
                - test_baseline.average_brier_score
            ):+.4f}"
        )

        print(
            "Log-loss change: "
            f"{(
                test_calibrated.average_log_loss
                - test_baseline.average_log_loss
            ):+.4f}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()