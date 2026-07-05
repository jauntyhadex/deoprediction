import math


class PoissonPredictor:

    @staticmethod
    def poisson_probability(expected_goals: float, goals: int):

        return (
            math.exp(-expected_goals)
            * (expected_goals ** goals)
            / math.factorial(goals)
        )

    @staticmethod
    def goal_distribution(
        expected_goals: float,
        max_goals: int = 10,
    ):

        return [
            PoissonPredictor.poisson_probability(
                expected_goals,
                goals,
            )
            for goals in range(max_goals + 1)
        ]

    @staticmethod
    def score_matrix(
        home_expected: float,
        away_expected: float,
        max_goals: int = 10,
    ):

        home = PoissonPredictor.goal_distribution(
            home_expected,
            max_goals,
        )

        away = PoissonPredictor.goal_distribution(
            away_expected,
            max_goals,
        )

        matrix = []

        for i in range(max_goals + 1):

            row = []

            for j in range(max_goals + 1):

                row.append(home[i] * away[j])

            matrix.append(row)

        return matrix