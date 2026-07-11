from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)
from app.prediction.result_calibrator import ResultCalibrator


def percentage(
    numerator,
    denominator,
):
    if denominator <= 0:
        return 0

    return round(
        numerator / denominator * 100,
        2,
    )


def main():

    db = SessionLocal()

    try:
        evaluations = (
            db.query(WalkForwardEvaluation)
            .all()
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

        correct = 0

        for evaluation in evaluations:

            predicted_result = (
                ResultCalibrator.calibrate_result(
                    evaluation.home_win_probability,
                    evaluation.draw_probability,
                    evaluation.away_win_probability,
                )
            )

            actual_result = evaluation.actual_result

            actual_counts[actual_result] += 1
            predicted_counts[predicted_result] += 1

            if predicted_result == actual_result:
                correct += 1
                correct_counts[actual_result] += 1

        total = len(evaluations)

        print("CALIBRATOR TEST")
        print("-" * 60)

        print(f"Fixtures: {total}")
        print(
            f"Accuracy: "
            f"{percentage(correct, total)}%"
        )

        print(
            "Recall: "
            f"HOME={percentage(correct_counts['HOME'], actual_counts['HOME'])}% | "
            f"DRAW={percentage(correct_counts['DRAW'], actual_counts['DRAW'])}% | "
            f"AWAY={percentage(correct_counts['AWAY'], actual_counts['AWAY'])}%"
        )

        print(
            "Predictions: "
            f"HOME={predicted_counts['HOME']} | "
            f"DRAW={predicted_counts['DRAW']} | "
            f"AWAY={predicted_counts['AWAY']}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()