import math

from app.prediction.poisson import PoissonPredictor


class ProbabilityPredictor:

    @staticmethod
    def _to_percent(value: float) -> float:
        value = max(0.0, min(float(value), 1.0))
        return round(value * 100, 2)

    @staticmethod
    def _clamp_percent(value: float) -> float:
        return round(
            max(0.0, min(float(value), 100.0)),
            2,
        )

    @staticmethod
    def match_probabilities(
        home_expected: float,
        away_expected: float,
    ) -> dict:
        matrix = PoissonPredictor.score_matrix(
            home_expected,
            away_expected,
        )

        home = 0.0
        draw = 0.0
        away = 0.0

        for home_goals, row in enumerate(matrix):
            for away_goals, probability in enumerate(row):

                if home_goals > away_goals:
                    home += probability

                elif home_goals == away_goals:
                    draw += probability

                else:
                    away += probability

        total = home + draw + away

        if total <= 0:
            return {
                "home": 33.33,
                "draw": 33.34,
                "away": 33.33,
            }

        home /= total
        draw /= total
        away /= total

        return {
            "home": ProbabilityPredictor._to_percent(home),
            "draw": ProbabilityPredictor._to_percent(draw),
            "away": ProbabilityPredictor._to_percent(away),
        }

    @staticmethod
    def btts_probability(
        home_expected: float,
        away_expected: float,
    ) -> float:
        probability = (
            1
            - math.exp(-home_expected)
            - math.exp(-away_expected)
            + math.exp(
                -(home_expected + away_expected)
            )
        )

        return ProbabilityPredictor._to_percent(
            probability
        )

    @staticmethod
    def over_under(
        home_expected: float,
        away_expected: float,
        line: float = 2.5,
    ) -> dict:
        matrix = PoissonPredictor.score_matrix(
            home_expected,
            away_expected,
        )

        over = 0.0
        under = 0.0

        for home_goals, row in enumerate(matrix):
            for away_goals, probability in enumerate(row):

                total_goals = home_goals + away_goals

                if total_goals > line:
                    over += probability
                else:
                    under += probability

        total = over + under

        if total <= 0:
            return {
                "over": 50.0,
                "under": 50.0,
            }

        over /= total
        under /= total

        return {
            "over": ProbabilityPredictor._to_percent(over),
            "under": ProbabilityPredictor._to_percent(
                under
            ),
        }

    @staticmethod
    def double_chance(
        home_expected: float,
        away_expected: float,
    ) -> dict:
        probabilities = (
            ProbabilityPredictor.match_probabilities(
                home_expected,
                away_expected,
            )
        )

        home = probabilities["home"]
        draw = probabilities["draw"]
        away = probabilities["away"]

        return {
            "home_or_draw": (
                ProbabilityPredictor._clamp_percent(
                    100 - away
                )
            ),
            "home_or_away": (
                ProbabilityPredictor._clamp_percent(
                    100 - draw
                )
            ),
            "draw_or_away": (
                ProbabilityPredictor._clamp_percent(
                    100 - home
                )
            ),
        }

    @staticmethod
    def draw_no_bet(
        home_expected: float,
        away_expected: float,
    ) -> dict:
        probabilities = (
            ProbabilityPredictor.match_probabilities(
                home_expected,
                away_expected,
            )
        )

        home = probabilities["home"]
        away = probabilities["away"]

        total = home + away

        if total <= 0:
            return {
                "home": 50.0,
                "away": 50.0,
            }

        return {
            "home": (
                ProbabilityPredictor._clamp_percent(
                    (home / total) * 100
                )
            ),
            "away": (
                ProbabilityPredictor._clamp_percent(
                    (away / total) * 100
                )
            ),
        }

    @staticmethod
    def team_total(
        expected_goals: float,
        line: float,
    ) -> dict:
        maximum_under_goals = int(
            math.floor(line)
        )

        under = sum(
            PoissonPredictor.poisson_probability(
                expected_goals,
                goals,
            )
            for goals in range(
                maximum_under_goals + 1
            )
        )

        over = 1 - under

        return {
            "over": ProbabilityPredictor._to_percent(over),
            "under": ProbabilityPredictor._to_percent(
                under
            ),
        }

    @staticmethod
    def clean_sheet(
        home_expected: float,
        away_expected: float,
    ) -> dict:
        return {
            "home": ProbabilityPredictor._to_percent(
                math.exp(-away_expected)
            ),
            "away": ProbabilityPredictor._to_percent(
                math.exp(-home_expected)
            ),
        }

    @staticmethod
    def win_to_nil(
        home_expected: float,
        away_expected: float,
    ) -> dict:
        home_probability = (
            1 - math.exp(-home_expected)
        ) * math.exp(-away_expected)

        away_probability = (
            1 - math.exp(-away_expected)
        ) * math.exp(-home_expected)

        return {
            "home": ProbabilityPredictor._to_percent(
                home_probability
            ),
            "away": ProbabilityPredictor._to_percent(
                away_probability
            ),
        }

    @staticmethod
    def asian_handicap(
        home_expected: float,
        away_expected: float,
        home_line: float,
    ) -> dict:
        matrix = PoissonPredictor.score_matrix(
            home_expected,
            away_expected,
        )

        home_probability = 0.0
        away_probability = 0.0

        for home_goals, row in enumerate(matrix):
            for away_goals, probability in enumerate(row):

                adjusted_home_goals = (
                    home_goals + home_line
                )

                if adjusted_home_goals > away_goals:
                    home_probability += probability
                else:
                    away_probability += probability

        total = (
            home_probability
            + away_probability
        )

        if total <= 0:
            return {
                "home": 50.0,
                "away": 50.0,
            }

        home_probability /= total
        away_probability /= total

        return {
            "home": ProbabilityPredictor._to_percent(
                home_probability
            ),
            "away": ProbabilityPredictor._to_percent(
                away_probability
            ),
        }

    @staticmethod
    def correct_scores(
        home_expected: float,
        away_expected: float,
        top_n: int = 5,
    ) -> list[dict]:
        matrix = PoissonPredictor.score_matrix(
            home_expected,
            away_expected,
        )

        scores = []

        for home_goals, row in enumerate(matrix):
            for away_goals, probability in enumerate(row):

                scores.append(
                    {
                        "score": (
                            f"{home_goals}-"
                            f"{away_goals}"
                        ),
                        "probability": (
                            ProbabilityPredictor
                            ._to_percent(
                                probability
                            )
                        ),
                    }
                )

        scores.sort(
            key=lambda item: item["probability"],
            reverse=True,
        )

        return scores[:top_n]

    @staticmethod
    def period_expected_goals(
        home_expected: float,
        away_expected: float,
        period: str,
    ) -> tuple[float, float]:

        if period == "FIRST_HALF":
            multiplier = 0.45

        elif period == "SECOND_HALF":
            multiplier = 0.55

        else:
            raise ValueError(
                "Period must be FIRST_HALF "
                "or SECOND_HALF"
            )

        return (
            round(
                home_expected * multiplier,
                4,
            ),
            round(
                away_expected * multiplier,
                4,
            ),
        )

    @staticmethod
    def period_probabilities(
        home_expected: float,
        away_expected: float,
        period: str,
    ) -> dict:
        period_home_xg, period_away_xg = (
            ProbabilityPredictor
            .period_expected_goals(
                home_expected,
                away_expected,
                period,
            )
        )

        result = (
            ProbabilityPredictor
            .match_probabilities(
                period_home_xg,
                period_away_xg,
            )
        )

        btts_yes = (
            ProbabilityPredictor
            .btts_probability(
                period_home_xg,
                period_away_xg,
            )
        )

        return {
            "home_xg": period_home_xg,
            "away_xg": period_away_xg,
            "home": result["home"],
            "draw": result["draw"],
            "away": result["away"],
            "btts_yes": btts_yes,
            "btts_no": (
                ProbabilityPredictor._clamp_percent(
                    100 - btts_yes
                )
            ),
        }