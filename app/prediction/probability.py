from app.prediction.poisson import PoissonPredictor


class ProbabilityPredictor:

    @staticmethod
    def match_probabilities(
        home_expected: float,
        away_expected: float,
    ):

        matrix = PoissonPredictor.score_matrix(
            home_expected,
            away_expected,
        )

        home = 0
        draw = 0
        away = 0

        for i in range(len(matrix)):

            for j in range(len(matrix)):

                if i > j:
                    home += matrix[i][j]

                elif i == j:
                    draw += matrix[i][j]

                else:
                    away += matrix[i][j]

        return {
            "home": round(home * 100, 2),
            "draw": round(draw * 100, 2),
            "away": round(away * 100, 2),
        }

    @staticmethod
    def btts_probability(
        home_expected: float,
        away_expected: float,
    ):

        matrix = PoissonPredictor.score_matrix(
            home_expected,
            away_expected,
        )

        probability = 0

        for i in range(1, len(matrix)):

            for j in range(1, len(matrix)):

                probability += matrix[i][j]

        return round(probability * 100, 2)

    @staticmethod
    def over_under(
        home_expected: float,
        away_expected: float,
        line: float = 2.5,
    ):

        matrix = PoissonPredictor.score_matrix(
            home_expected,
            away_expected,
        )

        over = 0
        under = 0

        for i in range(len(matrix)):

            for j in range(len(matrix)):

                total = i + j

                if total > line:
                    over += matrix[i][j]
                else:
                    under += matrix[i][j]

        return {
            "over": round(over * 100, 2),
            "under": round(under * 100, 2),
        }