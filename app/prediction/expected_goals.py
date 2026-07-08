from app.models.elo_rating import EloRating
from app.models.strength_of_schedule import StrengthOfSchedule
from app.models.team_form import TeamForm
from app.models.team_home_away_stats import TeamHomeAwayStats
from app.models.team_power_rating import TeamPowerRating


class ExpectedGoalsCalculator:

    DEFAULT_HOME_GOALS = 1.45
    DEFAULT_AWAY_GOALS = 1.15

    MIN_EXPECTED_GOALS = 0.25
    MAX_EXPECTED_GOALS = 3.50

    @staticmethod
    def clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:
        return max(
            minimum,
            min(float(value), maximum),
        )

    @staticmethod
    def safe_rate(
        goals,
        matches,
        default: float,
    ) -> float:

        if matches is None or matches <= 0:
            return default

        if goals is None:
            return default

        rate = float(goals) / float(matches)

        return ExpectedGoalsCalculator.clamp(
            rate,
            0.10,
            4.00,
        )

    @staticmethod
    def relative_difference(
        first_value: float,
        second_value: float,
    ) -> float:

        denominator = max(
            abs(first_value) + abs(second_value),
            1.0,
        )

        difference = (
            first_value - second_value
        ) / denominator

        return ExpectedGoalsCalculator.clamp(
            difference,
            -1.0,
            1.0,
        )

    @staticmethod
    def calculate(
        db,
        home_team_id: int,
        away_team_id: int,
    ) -> tuple[float, float]:

        home_stats = (
            db.query(TeamHomeAwayStats)
            .filter(
                TeamHomeAwayStats.team_id
                == home_team_id
            )
            .first()
        )

        away_stats = (
            db.query(TeamHomeAwayStats)
            .filter(
                TeamHomeAwayStats.team_id
                == away_team_id
            )
            .first()
        )

        home_elo = (
            db.query(EloRating)
            .filter(
                EloRating.team_id == home_team_id
            )
            .first()
        )

        away_elo = (
            db.query(EloRating)
            .filter(
                EloRating.team_id == away_team_id
            )
            .first()
        )

        home_form = (
            db.query(TeamForm)
            .filter(
                TeamForm.team_id == home_team_id
            )
            .first()
        )

        away_form = (
            db.query(TeamForm)
            .filter(
                TeamForm.team_id == away_team_id
            )
            .first()
        )

        home_power = (
            db.query(TeamPowerRating)
            .filter(
                TeamPowerRating.team_id
                == home_team_id
            )
            .first()
        )

        away_power = (
            db.query(TeamPowerRating)
            .filter(
                TeamPowerRating.team_id
                == away_team_id
            )
            .first()
        )

        home_sos = (
            db.query(StrengthOfSchedule)
            .filter(
                StrengthOfSchedule.team_id
                == home_team_id
            )
            .first()
        )

        away_sos = (
            db.query(StrengthOfSchedule)
            .filter(
                StrengthOfSchedule.team_id
                == away_team_id
            )
            .first()
        )

        home_scoring_rate = (
            ExpectedGoalsCalculator.safe_rate(
                getattr(
                    home_stats,
                    "home_goals_for",
                    None,
                ),
                getattr(
                    home_stats,
                    "home_matches",
                    None,
                ),
                ExpectedGoalsCalculator.DEFAULT_HOME_GOALS,
            )
        )

        away_conceding_rate = (
            ExpectedGoalsCalculator.safe_rate(
                getattr(
                    away_stats,
                    "away_goals_against",
                    None,
                ),
                getattr(
                    away_stats,
                    "away_matches",
                    None,
                ),
                ExpectedGoalsCalculator.DEFAULT_HOME_GOALS,
            )
        )

        away_scoring_rate = (
            ExpectedGoalsCalculator.safe_rate(
                getattr(
                    away_stats,
                    "away_goals_for",
                    None,
                ),
                getattr(
                    away_stats,
                    "away_matches",
                    None,
                ),
                ExpectedGoalsCalculator.DEFAULT_AWAY_GOALS,
            )
        )

        home_conceding_rate = (
            ExpectedGoalsCalculator.safe_rate(
                getattr(
                    home_stats,
                    "home_goals_against",
                    None,
                ),
                getattr(
                    home_stats,
                    "home_matches",
                    None,
                ),
                ExpectedGoalsCalculator.DEFAULT_AWAY_GOALS,
            )
        )

        home_expected = (
            home_scoring_rate * 0.55
            + away_conceding_rate * 0.45
        )

        away_expected = (
            away_scoring_rate * 0.55
            + home_conceding_rate * 0.45
        )

        # Home advantage

        home_expected *= 1.08

        # Elo adjustment

        home_elo_value = float(
            getattr(home_elo, "elo_rating", 1500)
        )

        away_elo_value = float(
            getattr(away_elo, "elo_rating", 1500)
        )

        elo_difference = (
            home_elo_value - away_elo_value
        )

        home_elo_multiplier = (
            ExpectedGoalsCalculator.clamp(
                1 + elo_difference / 2000,
                0.85,
                1.15,
            )
        )

        away_elo_multiplier = (
            ExpectedGoalsCalculator.clamp(
                1 - elo_difference / 2000,
                0.85,
                1.15,
            )
        )

        home_expected *= home_elo_multiplier
        away_expected *= away_elo_multiplier

        # Recent form adjustment

        home_form_points = float(
            getattr(
                home_form,
                "last_ten_points",
                15,
            )
        )

        away_form_points = float(
            getattr(
                away_form,
                "last_ten_points",
                15,
            )
        )

        form_difference = (
            home_form_points - away_form_points
        ) / 30

        form_difference = (
            ExpectedGoalsCalculator.clamp(
                form_difference,
                -1.0,
                1.0,
            )
        )

        home_expected *= (
            1 + form_difference * 0.10
        )

        away_expected *= (
            1 - form_difference * 0.10
        )

        # Power-rating adjustment

        home_power_value = float(
            getattr(
                home_power,
                "overall_power",
                50,
            )
        )

        away_power_value = float(
            getattr(
                away_power,
                "overall_power",
                50,
            )
        )

        power_difference = (
            ExpectedGoalsCalculator.relative_difference(
                home_power_value,
                away_power_value,
            )
        )

        home_expected *= (
            1 + power_difference * 0.08
        )

        away_expected *= (
            1 - power_difference * 0.08
        )

        # Strength-of-schedule adjustment

        home_sos_value = float(
            getattr(
                home_sos,
                "sos_rating",
                1500,
            )
        )

        away_sos_value = float(
            getattr(
                away_sos,
                "sos_rating",
                1500,
            )
        )

        sos_difference = (
            ExpectedGoalsCalculator.relative_difference(
                home_sos_value,
                away_sos_value,
            )
        )

        home_expected *= (
            1 + sos_difference * 0.04
        )

        away_expected *= (
            1 - sos_difference * 0.04
        )

        home_expected = (
            ExpectedGoalsCalculator.clamp(
                home_expected,
                ExpectedGoalsCalculator.MIN_EXPECTED_GOALS,
                ExpectedGoalsCalculator.MAX_EXPECTED_GOALS,
            )
        )

        away_expected = (
            ExpectedGoalsCalculator.clamp(
                away_expected,
                ExpectedGoalsCalculator.MIN_EXPECTED_GOALS,
                ExpectedGoalsCalculator.MAX_EXPECTED_GOALS,
            )
        )

        return (
            round(home_expected, 2),
            round(away_expected, 2),
        )