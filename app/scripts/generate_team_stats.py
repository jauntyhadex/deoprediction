from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.team import Team
from app.services.team_stat_service import TeamStatService


def main():
    db = SessionLocal()

    service = TeamStatService(db)

    teams = db.query(Team).all()

    print(f"Generating statistics for {len(teams)} teams...")

    for team in teams:

        fixtures = (
            db.query(Fixture)
            .filter(
                (Fixture.home_team_id == team.id)
                | (Fixture.away_team_id == team.id)
            )
            .all()
        )

        matches = 0
        wins = 0
        draws = 0
        losses = 0
        goals_for = 0
        goals_against = 0

        for fixture in fixtures:

            if (
                fixture.home_score is None
                or fixture.away_score is None
            ):
                continue

            matches += 1

            if fixture.home_team_id == team.id:

                goals_for += fixture.home_score
                goals_against += fixture.away_score

                if fixture.home_score > fixture.away_score:
                    wins += 1
                elif fixture.home_score == fixture.away_score:
                    draws += 1
                else:
                    losses += 1

            else:

                goals_for += fixture.away_score
                goals_against += fixture.home_score

                if fixture.away_score > fixture.home_score:
                    wins += 1
                elif fixture.away_score == fixture.home_score:
                    draws += 1
                else:
                    losses += 1

        points = wins * 3 + draws
        goal_difference = goals_for - goals_against

        if matches:
            win_rate = wins / matches
            draw_rate = draws / matches
            loss_rate = losses / matches
        else:
            win_rate = 0
            draw_rate = 0
            loss_rate = 0

        service.create_or_update(
            team_id=team.id,
            matches_played=matches,
            wins=wins,
            draws=draws,
            losses=losses,
            goals_for=goals_for,
            goals_against=goals_against,
            goal_difference=goal_difference,
            points=points,
            win_rate=win_rate,
            draw_rate=draw_rate,
            loss_rate=loss_rate,
        )

        print(f"{team.name} OK")

    db.close()

    print("Finished generating team statistics.")


if __name__ == "__main__":
    main()