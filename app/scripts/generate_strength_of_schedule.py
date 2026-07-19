from app.database import model_loader
from collections import defaultdict

from app.models.team import Team
from app.database.connection import SessionLocal
from app.models.elo_rating import EloRating
from app.models.fixture import Fixture
from app.services.strength_of_schedule_service import (
    StrengthOfScheduleService,
)


def safe_console_text(
    value: object,
) -> str:

    return (
        str(value)
        .encode(
            "ascii",
            errors="replace",
        )
        .decode("ascii")
    )



def main():

    db = SessionLocal()

    service = StrengthOfScheduleService(db)

    elo = {
        rating.team_id: rating.elo_rating
        for rating in db.query(EloRating).all()
    }

    opponents = defaultdict(list)

    fixtures = (
        db.query(Fixture)
        .filter(Fixture.status == "FINISHED")
        .all()
    )

    print(f"Processing {len(fixtures)} fixtures...")

    for match in fixtures:

        opponents[match.home_team_id].append(
            elo.get(match.away_team_id, 1500)
        )

        opponents[match.away_team_id].append(
            elo.get(match.home_team_id, 1500)
        )

    from app.models.team import Team

    teams = db.query(Team).all()

    for team in teams:

        ratings = opponents.get(team.id, [])

        sos = (
            sum(ratings) / len(ratings)
            if ratings
            else 1500
        )

        service.create_or_update(
            team_id=team.id,
            sos_rating=round(sos, 2),
        )

    db.close()

    print("Finished!")


if __name__ == "__main__":
    main()