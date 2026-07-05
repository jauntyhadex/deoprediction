from app.models.elo_rating import EloRating
from app.models.strength_of_schedule import StrengthOfSchedule
from app.models.team_form import TeamForm
from app.models.team_home_away_stats import TeamHomeAwayStats
from app.models.team_power_rating import TeamPowerRating


class ExpectedGoalsCalculator:

    @staticmethod
    def calculate(
        db,
        home_team_id: int,
        away_team_id: int,
    ):

        home_power = (
            db.query(TeamPowerRating)
            .filter(TeamPowerRating.team_id == home_team_id)
            .first()
        )

        away_power = (
            db.query(TeamPowerRating)
            .filter(TeamPowerRating.team_id == away_team_id)
            .first()
        )

        home_elo = (
            db.query(EloRating)
            .filter(EloRating.team_id == home_team_id)
            .first()
        )

        away_elo = (
            db.query(EloRating)
            .filter(EloRating.team_id == away_team_id)
            .first()
        )

        home_form = (
            db.query(TeamForm)
            .filter(TeamForm.team_id == home_team_id)
            .first()
        )

        away_form = (
            db.query(TeamForm)
            .filter(TeamForm.team_id == away_team_id)
            .first()
        )

        home_stats = (
            db.query(TeamHomeAwayStats)
            .filter(TeamHomeAwayStats.team_id == home_team_id)
            .first()
        )

        away_stats = (
            db.query(TeamHomeAwayStats)
            .filter(TeamHomeAwayStats.team_id == away_team_id)
            .first()
        )

        home_sos = (
            db.query(StrengthOfSchedule)
            .filter(StrengthOfSchedule.team_id == home_team_id)
            .first()
        )

        away_sos = (
            db.query(StrengthOfSchedule)
            .filter(StrengthOfSchedule.team_id == away_team_id)
            .first()
        )

        home_attack = home_power.attack_power
        away_attack = away_power.attack_power

        home_defense = home_power.defense_power
        away_defense = away_power.defense_power

        home_goal_rate = (
            home_stats.home_goals_for /
            max(home_stats.home_matches, 1)
        )

        away_goal_rate = (
            away_stats.away_goals_for /
            max(away_stats.away_matches, 1)
        )

        home_expected = (
            home_goal_rate * 0.40 +
            home_attack * 0.25 +
            (home_elo.elo_rating / 1500) * 0.15 +
            (home_form.last_ten_points / 30) * 0.10 +
            (home_sos.sos_rating / 1500) * 0.10
        )

        away_expected = (
            away_goal_rate * 0.40 +
            away_attack * 0.25 +
            (away_elo.elo_rating / 1500) * 0.15 +
            (away_form.last_ten_points / 30) * 0.10 +
            (away_sos.sos_rating / 1500) * 0.10
        )

        home_expected *= (2 - away_defense)
        away_expected *= (2 - home_defense)

        return (
            round(home_expected, 2),
            round(away_expected, 2),
        )