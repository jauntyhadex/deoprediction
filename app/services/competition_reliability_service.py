from collections import defaultdict

from app.models.competition import Competition
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


class CompetitionReliabilityService:

    MINIMUM_EVALUATIONS = 50
    MINIMUM_RELIABLE_EVALUATIONS = 100

    RELIABLE_MINIMUM_ACCURACY = 55.0
    PROMISING_MINIMUM_ACCURACY = 52.0

    MAXIMUM_BRIER_SCORE = 0.20

    VALID_STATUSES = [
        "RELIABLE",
        "PROMISING",
        "LIMITED",
        "WEAK",
        "UNVALIDATED",
    ]

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _percentage(
        numerator: int,
        denominator: int,
    ) -> float:

        if denominator <= 0:
            return 0.0

        return round(
            numerator / denominator * 100,
            2,
        )

    @staticmethod
    def _average(
        values: list[float],
    ) -> float | None:

        if not values:
            return None

        return round(
            sum(values) / len(values),
            4,
        )

    def _calculate_metrics(
        self,
        rows: list[WalkForwardEvaluation],
    ) -> dict:

        total = len(rows)

        if total == 0:
            return {
                "evaluations": 0,
                "accuracy": None,
                "brier": None,
                "log_loss": None,
                "goal_error": None,
                "home_recall": None,
                "draw_recall": None,
                "away_recall": None,
                "macro_recall": None,
            }

        correct_results = sum(
            1
            for row in rows
            if row.result_correct
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

        for row in rows:

            actual_result = row.actual_result

            if actual_result not in actual_counts:
                continue

            actual_counts[actual_result] += 1

            if row.result_correct:
                correct_counts[
                    actual_result
                ] += 1

        home_recall = self._percentage(
            correct_counts["HOME"],
            actual_counts["HOME"],
        )

        draw_recall = self._percentage(
            correct_counts["DRAW"],
            actual_counts["DRAW"],
        )

        away_recall = self._percentage(
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
            "evaluations": total,
            "accuracy": self._percentage(
                correct_results,
                total,
            ),
            "brier": self._average(
                [
                    float(row.brier_score)
                    for row in rows
                ]
            ),
            "log_loss": self._average(
                [
                    float(row.log_loss)
                    for row in rows
                ]
            ),
            "goal_error": self._average(
                [
                    float(row.goal_error)
                    for row in rows
                ]
            ),
            "home_recall": home_recall,
            "draw_recall": draw_recall,
            "away_recall": away_recall,
            "macro_recall": macro_recall,
        }

    def _determine_status(
        self,
        metrics: dict,
    ) -> str:

        evaluations = metrics["evaluations"]

        if evaluations == 0:
            return "UNVALIDATED"

        if (
            evaluations
            < self.MINIMUM_EVALUATIONS
        ):
            return "LIMITED"

        accuracy = float(
            metrics["accuracy"] or 0
        )

        brier = float(
            metrics["brier"] or 999
        )

        if (
            evaluations
            >= self.MINIMUM_RELIABLE_EVALUATIONS
            and accuracy
            >= self.RELIABLE_MINIMUM_ACCURACY
            and brier
            <= self.MAXIMUM_BRIER_SCORE
        ):
            return "RELIABLE"

        if (
            accuracy
            >= self.PROMISING_MINIMUM_ACCURACY
            and brier
            <= self.MAXIMUM_BRIER_SCORE
        ):
            return "PROMISING"

        return "WEAK"

    @staticmethod
    def _status_message(
        status: str,
    ) -> str:

        messages = {
            "RELIABLE": (
                "The competition passed the "
                "current reliability rules."
            ),
            "PROMISING": (
                "The competition has encouraging "
                "results but has not passed the "
                "reliable threshold."
            ),
            "LIMITED": (
                "The competition has too few "
                "walk-forward evaluations."
            ),
            "WEAK": (
                "The competition has historical "
                "evidence but did not pass the "
                "quality rules."
            ),
            "UNVALIDATED": (
                "No walk-forward validation "
                "evidence is currently available."
            ),
        }

        return messages.get(
            status,
            "Competition status is unknown.",
        )

    def get_reports_by_competition_id(
        self,
    ) -> dict[int, dict]:

        competitions = (
            self.db.query(Competition)
            .order_by(
                Competition.id.asc()
            )
            .all()
        )

        evaluations = (
            self.db.query(
                WalkForwardEvaluation
            )
            .all()
        )

        grouped = defaultdict(list)

        for evaluation in evaluations:
            grouped[
                evaluation.competition_id
            ].append(evaluation)

        reports = {}

        for competition in competitions:

            metrics = self._calculate_metrics(
                grouped.get(
                    competition.id,
                    [],
                )
            )

            status = self._determine_status(
                metrics
            )

            reports[competition.id] = {
                "competition_id": (
                    competition.id
                ),
                "competition_name": getattr(
                    competition,
                    "name",
                    (
                        "Competition "
                        f"{competition.id}"
                    ),
                ),
                "status": status,
                "status_message": (
                    self._status_message(
                        status
                    )
                ),
                **metrics,
            }

        return reports

    def get_competition_ids_for_status(
        self,
        status: str,
    ) -> list[int]:

        normalized_status = status.upper()

        if (
            normalized_status
            not in self.VALID_STATUSES
        ):
            return []

        reports = (
            self.get_reports_by_competition_id()
        )

        return [
            competition_id
            for competition_id, report
            in reports.items()
            if (
                report["status"]
                == normalized_status
            )
        ]