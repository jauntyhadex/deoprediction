from app.database.connection import SessionLocal
from app.models.elo_rating import EloRating
from app.models.strength_of_schedule import StrengthOfSchedule
from app.models.team import Team
from app.models.team_stat import TeamStat
from app.services.team_power_rating_service import (
    TeamPowerRatingService,
)


def main():

    db = SessionLocal()

    service = TeamPowerRatingService(db)

    teams = db.query(Team).all()

    for team in teams:

        stat = (
            db.query(TeamStat)
            .filter(TeamStat.team_id == team.id)
            .first()
        )

        elo = (
            db.query(EloRating)
            .filter(EloRating.team_id == team.id)
            .first()
        )

        sos = (
            db.query(StrengthOfSchedule)
            .filter(StrengthOfSchedule.team_id == team.id)
            .first()
        )

        if not stat or not elo or not sos:
            continue

        attack = (
            stat.goals_for / max(stat.matches_played, 1)
        ) * (elo.elo_rating / 1500)

        defense = (
            stat.goals_against / max(stat.matches_played, 1)
        ) / (elo.elo_rating / 1500)

        overall = (
            attack * 0.40
            + (2 - defense) * 0.30
            + (elo.elo_rating / 1000) * 0.20
            + (sos.sos_rating / 2000) * 0.10
        )

        service.create_or_update(
            team_id=team.id,
            attack_power=round(attack, 3),
            defense_power=round(defense, 3),
            overall_power=round(overall, 3),
        )

    db.close()

    print("Finished!")
    

if __name__ == "__main__":
    main()