import math

from app.models.prediction_evaluation import (
    PredictionEvaluation,
)


class BacktestReportService:

    CONFIDENCE_BANDS = [
        (0, 40, "0-39"),
        (40, 50, "40-49"),
        (50, 60, "50-59"),
        (60, 70, "60-69"),
        (70, 80, "70-79"),
        (80, 101, "80-100"),
    ]

    def __init__(self, db):
        self.db = db

    @staticmethod
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

    @staticmethod
    def average(values: list[float]) -> float:

        if not values:
            return 0.0

        return round(
            sum(values) / len(values),
            4,
        )

    @staticmethod
    def calculate_log_loss(
        evaluation,
    ) -> float:

        probabilities = {
            "HOME": (
                evaluation.home_win_probability
                / 100
            ),
            "DRAW": (
                evaluation.draw_probability
                / 100
            ),
            "AWAY": (
                evaluation.away_win_probability
                / 100
            ),
        }

        actual_probability = probabilities.get(
            evaluation.actual_result,
            0.0,
        )

        actual_probability = max(
            0.000001,
            min(actual_probability, 0.999999),
        )

        return -math.log(actual_probability)

    def overall_report(
        self,
        evaluations,
    ) -> dict:

        total = len(evaluations)

        correct_results = sum(
            1
            for evaluation in evaluations
            if evaluation.result_correct
        )

        exact_scores = sum(
            1
            for evaluation in evaluations
            if evaluation.score_correct
        )

        brier_scores = [
            float(evaluation.brier_score)
            for evaluation in evaluations
        ]

        goal_errors = [
            float(evaluation.goal_error)
            for evaluation in evaluations
        ]

        log_losses = [
            self.calculate_log_loss(evaluation)
            for evaluation in evaluations
        ]

        return {
            "total_evaluations": total,
            "correct_results": correct_results,
            "result_accuracy": self.percentage(
                correct_results,
                total,
            ),
            "exact_scores": exact_scores,
            "exact_score_accuracy": self.percentage(
                exact_scores,
                total,
            ),
            "average_brier_score": self.average(
                brier_scores
            ),
            "average_log_loss": self.average(
                log_losses
            ),
            "average_goal_error": self.average(
                goal_errors
            ),
        }

    def result_breakdown(
        self,
        evaluations,
    ) -> list[dict]:

        report = []

        for result in [
            "HOME",
            "DRAW",
            "AWAY",
        ]:
            rows = [
                evaluation
                for evaluation in evaluations
                if evaluation.predicted_result
                == result
            ]

            correct = sum(
                1
                for evaluation in rows
                if evaluation.result_correct
            )

            report.append(
                {
                    "predicted_result": result,
                    "predictions": len(rows),
                    "correct": correct,
                    "accuracy": self.percentage(
                        correct,
                        len(rows),
                    ),
                }
            )

        return report

    def actual_result_breakdown(
        self,
        evaluations,
    ) -> list[dict]:

        report = []

        for result in [
            "HOME",
            "DRAW",
            "AWAY",
        ]:
            rows = [
                evaluation
                for evaluation in evaluations
                if evaluation.actual_result
                == result
            ]

            correctly_detected = sum(
                1
                for evaluation in rows
                if (
                    evaluation.predicted_result
                    == result
                )
            )

            report.append(
                {
                    "actual_result": result,
                    "fixtures": len(rows),
                    "correctly_detected": (
                        correctly_detected
                    ),
                    "recall": self.percentage(
                        correctly_detected,
                        len(rows),
                    ),
                }
            )

        return report

    def confidence_breakdown(
        self,
        evaluations,
    ) -> list[dict]:

        report = []

        for minimum, maximum, label in (
            self.CONFIDENCE_BANDS
        ):
            rows = [
                evaluation
                for evaluation in evaluations
                if (
                    minimum
                    <= float(
                        evaluation.confidence
                    )
                    < maximum
                )
            ]

            correct = sum(
                1
                for evaluation in rows
                if evaluation.result_correct
            )

            report.append(
                {
                    "confidence_band": label,
                    "predictions": len(rows),
                    "correct": correct,
                    "accuracy": self.percentage(
                        correct,
                        len(rows),
                    ),
                    "average_brier_score": (
                        self.average(
                            [
                                float(
                                    evaluation
                                    .brier_score
                                )
                                for evaluation in rows
                            ]
                        )
                    ),
                }
            )

        return report

    def generate(self) -> dict:

        evaluations = (
            self.db.query(
                PredictionEvaluation
            )
            .all()
        )

        return {
            "overall": self.overall_report(
                evaluations
            ),
            "predicted_result_breakdown": (
                self.result_breakdown(
                    evaluations
                )
            ),
            "actual_result_breakdown": (
                self.actual_result_breakdown(
                    evaluations
                )
            ),
            "confidence_breakdown": (
                self.confidence_breakdown(
                    evaluations
                )
            ),
        }