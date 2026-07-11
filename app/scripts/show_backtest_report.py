from app.database import model_loader
from app.database.connection import SessionLocal
from app.services.backtest_report_service import (
    BacktestReportService,
)


def print_separator():
    print("-" * 60)


def main():

    db = SessionLocal()

    try:
        service = BacktestReportService(db)

        report = service.generate()

        overall = report["overall"]

        print("\nBACKTEST REPORT")
        print_separator()

        print(
            f"Evaluations: "
            f"{overall['total_evaluations']}"
        )

        print(
            f"Correct results: "
            f"{overall['correct_results']}"
        )

        print(
            f"Result accuracy: "
            f"{overall['result_accuracy']}%"
        )

        print(
            f"Exact scores: "
            f"{overall['exact_scores']}"
        )

        print(
            f"Exact-score accuracy: "
            f"{overall['exact_score_accuracy']}%"
        )

        print(
            f"Average Brier score: "
            f"{overall['average_brier_score']}"
        )

        print(
            f"Average log loss: "
            f"{overall['average_log_loss']}"
        )

        print(
            f"Average goal error: "
            f"{overall['average_goal_error']}"
        )

        print("\nPREDICTED RESULT BREAKDOWN")
        print_separator()

        for row in report[
            "predicted_result_breakdown"
        ]:
            print(
                f"{row['predicted_result']}: "
                f"{row['correct']}/"
                f"{row['predictions']} correct "
                f"({row['accuracy']}%)"
            )

        print("\nACTUAL RESULT RECALL")
        print_separator()

        for row in report[
            "actual_result_breakdown"
        ]:
            print(
                f"{row['actual_result']}: "
                f"{row['correctly_detected']}/"
                f"{row['fixtures']} detected "
                f"({row['recall']}%)"
            )

        print("\nCONFIDENCE BREAKDOWN")
        print_separator()

        for row in report[
            "confidence_breakdown"
        ]:
            print(
                f"{row['confidence_band']}: "
                f"{row['correct']}/"
                f"{row['predictions']} correct "
                f"({row['accuracy']}%) | "
                f"Brier: "
                f"{row['average_brier_score']}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()