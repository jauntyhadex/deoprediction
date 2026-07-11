from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)
from app.prediction.result_calibrator import (
    ResultCalibrator,
)


TEST_RATIO = 0.20


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


def evaluate(
    rows,
    use_calibrator: bool,
) -> dict:

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

        if use_calibrator:
            predicted_result = (
                ResultCalibrator.calibrate_result(
                    home_probability=float(
                        row.home_win_probability
                    ),
                    draw_probability=float(
                        row.draw_probability
                    ),
                    away_probability=float(
                        row.away_win_probability
                    ),
                )
            )
        else:
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

            predicted_result = max(
                probabilities,
                key=probabilities.get,
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

    macro_recall = round(
        (
            home_recall
            + draw_recall
            + away_recall
        ) / 3,
        2,
    )

    return {
        "fixtures": len(rows),
        "correct": correct,
        "accuracy": percentage(
            correct,
            len(rows),
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


def print_result(
    title: str,
    result: dict,
) -> None:

    print(f"\n{title}")
    print("-" * 60)

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
        f"Home recall: "
        f"{result['home_recall']}%"
    )

    print(
        f"Draw recall: "
        f"{result['draw_recall']}%"
    )

    print(
        f"Away recall: "
        f"{result['away_recall']}%"
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

        test_size = int(
            len(rows) * TEST_RATIO
        )

        test_rows = rows[-test_size:]

        baseline = evaluate(
            rows=test_rows,
            use_calibrator=False,
        )

        calibrated = evaluate(
            rows=test_rows,
            use_calibrator=True,
        )

        print_result(
            "OUT-OF-SAMPLE BASELINE",
            baseline,
        )

        print_result(
            "OUT-OF-SAMPLE CALIBRATED",
            calibrated,
        )

        accuracy_change = round(
            calibrated["accuracy"]
            - baseline["accuracy"],
            2,
        )

        macro_recall_change = round(
            calibrated["macro_recall"]
            - baseline["macro_recall"],
            2,
        )

        print("\nCHANGE")
        print("-" * 60)

        print(
            f"Accuracy change: "
            f"{accuracy_change:+.2f}%"
        )

        print(
            f"Macro-recall change: "
            f"{macro_recall_change:+.2f}%"
        )

        passed = (
            calibrated["accuracy"]
            >= baseline["accuracy"] - 1.0
            and calibrated["macro_recall"]
            > baseline["macro_recall"]
            and calibrated["draw_recall"] > 0
        )

        if passed:
            print(
                "\nVALIDATION PASSED"
            )
        else:
            print(
                "\nVALIDATION FAILED"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()