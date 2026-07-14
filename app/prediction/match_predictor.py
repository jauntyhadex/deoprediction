from app.prediction.expected_goals import (
    ExpectedGoalsCalculator,
)
from app.prediction.probability import (
    ProbabilityPredictor,
)


class MatchPredictor:

    @staticmethod
    def predict(
        db,
        home_team_id: int,
        away_team_id: int,
        data_cache: dict | None = None,
    ):

        home_xg, away_xg = (
            ExpectedGoalsCalculator.calculate(
                db,
                home_team_id,
                away_team_id,
                data_cache=data_cache,
            )
        )

        probabilities = (
            ProbabilityPredictor
            .match_probabilities(
                home_xg,
                away_xg,
            )
        )

        btts = (
            ProbabilityPredictor
            .btts_probability(
                home_xg,
                away_xg,
            )
        )

        over25 = (
            ProbabilityPredictor.over_under(
                home_xg,
                away_xg,
            )
        )

        return {
            "home_xg": home_xg,
            "away_xg": away_xg,
            "home_win": probabilities["home"],
            "draw": probabilities["draw"],
            "away_win": probabilities["away"],
            "btts": btts,
            "over25": over25["over"],
            "under25": over25["under"],
        }
