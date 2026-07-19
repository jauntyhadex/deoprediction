from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.elo_rating import EloRating


INITIAL_ELO = 1500
K = 20


def expected_score(rating_a, rating_b):
    return 1 / (1 + (10 ** ((rating_b - rating_a) / 400)))


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

    ratings = {}

    fixtures = (
        db.query(Fixture)
        .filter(Fixture.status == "FINISHED")
        .order_by(Fixture.kickoff_time)
        .all()
    )

    print(f"Processing {len(fixtures)} fixtures...")

    for match in fixtures:

        if match.home_score is None or match.away_score is None:
            continue

        home = match.home_team_id
        away = match.away_team_id

        ratings.setdefault(home, INITIAL_ELO)
        ratings.setdefault(away, INITIAL_ELO)

        home_rating = ratings[home]
        away_rating = ratings[away]

        expected_home = expected_score(home_rating, away_rating)
        expected_away = expected_score(away_rating, home_rating)

        if match.home_score > match.away_score:
            actual_home = 1
            actual_away = 0

        elif match.home_score < match.away_score:
            actual_home = 0
            actual_away = 1

        else:
            actual_home = 0.5
            actual_away = 0.5

        ratings[home] = home_rating + K * (actual_home - expected_home)
        ratings[away] = away_rating + K * (actual_away - expected_away)

    db.query(EloRating).delete()

    db.commit()

    
    from app.models.team import Team

    teams = db.query(Team).all()

    for team in teams:

        rating = ratings.get(team.id, INITIAL_ELO)

        db.add(
            EloRating(
                team_id=team.id,
                elo_rating=round(rating, 2),
            )
        )   

    
    db.commit()

    db.close()

    print("Finished!")


if __name__ == "__main__":
    main()