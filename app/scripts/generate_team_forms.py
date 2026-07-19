from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.team import Team
from app.services.team_form_service import TeamFormService


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

    service = TeamFormService(db)

    teams = db.query(Team).all()

    print(f"Generating form for {len(teams)} teams...")

    for team in teams:

        fixtures = (
            db.query(Fixture)
            .filter(
                (Fixture.home_team_id == team.id)
                | (Fixture.away_team_id == team.id)
            )
            .order_by(Fixture.kickoff_time.desc())
            .all()
        )

        results = []

        win_streak = 0
        unbeaten_streak = 0
            
        for fixture in fixtures:

            if fixture.status not in [
              "FINISHED",
              "AWARDED",
            ]:
                continue

            if fixture.home_score is None or fixture.away_score is None:
                continue

            if fixture.home_team_id == team.id:

                gf = fixture.home_score
                ga = fixture.away_score

            else:

                gf = fixture.away_score
                ga = fixture.home_score

            if gf > ga:
                result = "W"
            elif gf == ga:
                result = "D"
            else:
                result = "L"

            results.append(result)

        last_five = "".join(results[:5])

        last_ten = results[:10]

        last_ten_points = (
            last_ten.count("W") * 3
            + last_ten.count("D")
        )

        for result in results:

            if result == "W":
                win_streak += 1
            else:
                break

        for result in results:

            if result != "L":
                unbeaten_streak += 1
            else:
                break

        service.create_or_update(
            team_id=team.id,
            last_five=last_five,
            last_ten_points=last_ten_points,
            current_win_streak=win_streak,
            current_unbeaten_streak=unbeaten_streak,
        )

        print(safe_console_text(team.name), last_five)

    db.close()

    print("Finished.")
    

if __name__ == "__main__":
    main()