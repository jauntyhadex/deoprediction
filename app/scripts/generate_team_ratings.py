from app.database.connection import SessionLocal
from app.models.team_stat import TeamStat
from app.services.team_rating_service import TeamRatingService


def main():

    db = SessionLocal()

    service = TeamRatingService(db)

    stats = db.query(TeamStat).all()

    print(f"Generating ratings for {len(stats)} teams...")

    for team in stats:

        attack = (
            team.goals_for / team.matches_played
            if team.matches_played else 0
        )

        defense = (
            1 / (1 + (team.goals_against / team.matches_played))
            if team.matches_played else 0
        )

        overall = (
            attack * 0.6 +
            defense * 0.4
        )

        service.create_or_update(
            team_id=team.team_id,
            attack_rating=round(attack, 2),
            defense_rating=round(defense, 2),
            overall_rating=round(overall, 2),
        )

        print(team.team_id)

    db.close()

    print("Finished!")


if __name__ == "__main__":
    main()