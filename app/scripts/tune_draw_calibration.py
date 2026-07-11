from dataclasses import dataclass

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


TRAIN_RATIO = 0.60
VALIDATION_RATIO = 0.20

MIN_TRAIN_HOME_RECALL = 55.0
MIN_TRAIN_DRAW_RECALL = 15.0
MIN_TRAIN_AWAY_RECALL = 20.0

MIN_VALIDATION_HOME_RECALL = 50.0
MIN_VALIDATION_DRAW_RECALL = 10.0
MIN_VALIDATION_AWAY_RECALL = 15.0


@dataclass
class CalibrationResult:
    draw_threshold: float
    leader_margin: float
    side_gap: float

    fixtures: int
    correct: int
    accuracy: float

    home_recall: float
    draw_recall: float
    away_recall: float
    macro_recall: float
    minimum_recall: float
    balanced_score: float

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


def baseline_result(
    home_probability: float,
    draw_probability: float,
    away_probability: float,
) -> str:
    probabilities = {
        "HOME": home_probability,
        "DRAW": draw_probability,
        "AWAY": away_probability,
    }

    return max(
        probabilities,
        key=probabilities.get,
    )


def calibrated_result(
    home_probability: float,
    draw_probability: float,
    away_probability: float,
    draw_threshold: float,
    leader_margin: float,
    side_gap: float,
) -> str:
    strongest_side = max(
        home_probability,
        away_probability,
    )

    home_away_gap = abs(
        home_probability - away_probability
    )

    draw_near_leader = (
        strongest_side - draw_probability
        <= leader_margin
    )

    sides_are_close = (
        home_away_gap <= side_gap
    )

    if (
        draw_probability >= draw_threshold
        and draw_near_leader
        and sides_are_close
    ):
        return "DRAW"

    if home_probability >= away_probability:
        return "HOME"

    return "AWAY"


def evaluate(
    rows,
    draw_threshold: float = 0.0,
    leader_margin: float = 0.0,
    side_gap: float = 0.0,
    use_calibration: bool = True,
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

    for row in rows:
        home_probability = float(
            row.home_win_probability
        )

        draw_probability = float(
            row.draw_probability
        )

        away_probability = float(
            row.away_win_probability
        )

        if use_calibration:
            predicted_result = calibrated_result(
                home_probability=home_probability,
                draw_probability=draw_probability,
                away_probability=away_probability,
                draw_threshold=draw_threshold,
                leader_margin=leader_margin,
                side_gap=side_gap,
            )
        else:
            predicted_result = baseline_result(
                home_probability=home_probability,
                draw_probability=draw_probability,
                away_probability=away_probability,
            )

        actual_result = row.actual_result

        actual_counts[actual_result] += 1
        predicted_counts[predicted_result] += 1

        if predicted_result == actual_result:
            correct += 1
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
        accuracy * 0.40
        + macro_recall * 0.45
        + minimum_recall * 0.15,
        4,
    )

    return CalibrationResult(
        draw_threshold=draw_threshold,
        leader_margin=leader_margin,
        side_gap=side_gap,
        fixtures=len(rows),
        correct=correct,
        accuracy=accuracy,
        home_recall=home_recall,
        draw_recall=draw_recall,
        away_recall=away_recall,
        macro_recall=macro_recall,
        minimum_recall=minimum_recall,
        balanced_score=balanced_score,
        predicted_home=predicted_counts["HOME"],
        predicted_draw=predicted_counts["DRAW"],
        predicted_away=predicted_counts["AWAY"],
    )


def passes_training_rules(
    result: CalibrationResult,
) -> bool:
    return (
        result.home_recall
        >= MIN_TRAIN_HOME_RECALL
        and result.draw_recall
        >= MIN_TRAIN_DRAW_RECALL
        and result.away_recall
        >= MIN_TRAIN_AWAY_RECALL
    )


def passes_validation_rules(
    result: CalibrationResult,
) -> bool:
    return (
        result.home_recall
        >= MIN_VALIDATION_HOME_RECALL
        and result.draw_recall
        >= MIN_VALIDATION_DRAW_RECALL
        and result.away_recall
        >= MIN_VALIDATION_AWAY_RECALL
    )


def generate_candidates(
    training_rows,
) -> list[CalibrationResult]:
    candidates = []

    draw_thresholds = [
        float(value)
        for value in range(20, 36)
    ]

    leader_margins = [
        float(value)
        for value in range(4, 21)
    ]

    side_gaps = [
        float(value)
        for value in range(6, 31, 2)
    ]

    for draw_threshold in draw_thresholds:
        for leader_margin in leader_margins:
            for side_gap in side_gaps:
                result = evaluate(
                    rows=training_rows,
                    draw_threshold=draw_threshold,
                    leader_margin=leader_margin,
                    side_gap=side_gap,
                    use_calibration=True,
                )

                if passes_training_rules(result):
                    candidates.append(result)

    if not candidates:
        raise RuntimeError(
            "No calibration passed the training rules."
        )

    candidates.sort(
        key=lambda result: (
            result.balanced_score,
            result.macro_recall,
            result.accuracy,
            result.minimum_recall,
        ),
        reverse=True,
    )

    return candidates[:200]


def select_best_candidate(
    training_candidates,
    validation_rows,
) -> CalibrationResult:
    validation_candidates = []

    for candidate in training_candidates:
        result = evaluate(
            rows=validation_rows,
            draw_threshold=(
                candidate.draw_threshold
            ),
            leader_margin=(
                candidate.leader_margin
            ),
            side_gap=candidate.side_gap,
            use_calibration=True,
        )

        if passes_validation_rules(result):
            validation_candidates.append(result)

    if not validation_candidates:
        for candidate in training_candidates:
            validation_candidates.append(
                evaluate(
                    rows=validation_rows,
                    draw_threshold=(
                        candidate.draw_threshold
                    ),
                    leader_margin=(
                        candidate.leader_margin
                    ),
                    side_gap=candidate.side_gap,
                    use_calibration=True,
                )
            )

    validation_candidates.sort(
        key=lambda result: (
            result.balanced_score,
            result.macro_recall,
            result.accuracy,
            result.minimum_recall,
        ),
        reverse=True,
    )

    return validation_candidates[0]


def print_result(
    title: str,
    result: CalibrationResult,
) -> None:
    print(f"\n{title}")
    print("-" * 60)

    print(f"Fixtures: {result.fixtures}")
    print(f"Correct: {result.correct}")
    print(f"Accuracy: {result.accuracy}%")

    print(f"Home recall: {result.home_recall}%")
    print(f"Draw recall: {result.draw_recall}%")
    print(f"Away recall: {result.away_recall}%")

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
        "Predictions: "
        f"HOME={result.predicted_home}, "
        f"DRAW={result.predicted_draw}, "
        f"AWAY={result.predicted_away}"
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

        train_end = int(
            len(rows) * TRAIN_RATIO
        )

        validation_end = int(
            len(rows)
            * (
                TRAIN_RATIO
                + VALIDATION_RATIO
            )
        )

        training_rows = rows[:train_end]

        validation_rows = rows[
            train_end:validation_end
        ]

        testing_rows = rows[
            validation_end:
        ]

        training_candidates = (
            generate_candidates(
                training_rows
            )
        )

        selected = select_best_candidate(
            training_candidates,
            validation_rows,
        )

        test_baseline = evaluate(
            rows=testing_rows,
            use_calibration=False,
        )

        test_calibrated = evaluate(
            rows=testing_rows,
            draw_threshold=(
                selected.draw_threshold
            ),
            leader_margin=(
                selected.leader_margin
            ),
            side_gap=selected.side_gap,
            use_calibration=True,
        )

        print("\nSELECTED DRAW CALIBRATION")
        print("-" * 60)

        print(
            f"Draw threshold: "
            f"{selected.draw_threshold}"
        )

        print(
            f"Leader margin: "
            f"{selected.leader_margin}"
        )

        print(
            f"Home-away gap: "
            f"{selected.side_gap}"
        )

        print_result(
            "VALIDATION RESULTS",
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

        accuracy_change = round(
            test_calibrated.accuracy
            - test_baseline.accuracy,
            2,
        )

        macro_recall_change = round(
            test_calibrated.macro_recall
            - test_baseline.macro_recall,
            2,
        )

        print("\nTEST CHANGE")
        print("-" * 60)

        print(
            f"Accuracy change: "
            f"{accuracy_change:+.2f}%"
        )

        print(
            f"Macro-recall change: "
            f"{macro_recall_change:+.2f}%"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()