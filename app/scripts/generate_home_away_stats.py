from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.team import Team
from app.services.team_home_away_stats_service import (
    TeamHomeAwayStatsService,
)


def main():

    db = SessionLocal()

    service = TeamHomeAwayStatsService(db)

    teams = db.query(Team).all()

    print(f"Generating home/away stats for {len(teams)} teams...")

    for team in teams:

        home_matches = (
            db.query(Fixture)
            .filter(
                Fixture.home_team_id == team.id,
                Fixture.status == "FINISHED",
            )
            .all()
        )

        away_matches = (
            db.query(Fixture)
            .filter(
                Fixture.away_team_id == team.id,
                Fixture.status == "FINISHED",
            )
            .all()
        )

        home_wins = 0
        home_draws = 0
        home_losses = 0
        home_goals_for = 0
        home_goals_against = 0

        away_wins = 0
        away_draws = 0
        away_losses = 0
        away_goals_for = 0
        away_goals_against = 0

        for match in home_matches:

            if match.home_score is None or match.away_score is None:
                continue

            home_goals_for += match.home_score
            home_goals_against += match.away_score

            if match.home_score > match.away_score:
                home_wins += 1
            elif match.home_score == match.away_score:
                home_draws += 1
            else:
                home_losses += 1

        for match in away_matches:

            if match.home_score is None or match.away_score is None:
                continue

            away_goals_for += match.away_score
            away_goals_against += match.home_score

            if match.away_score > match.home_score:
                away_wins += 1
            elif match.away_score == match.home_score:
                away_draws += 1
            else:
                away_losses += 1

        home_count = len(home_matches)
        away_count = len(away_matches)

        service.create_or_update(
            team_id=team.id,
            home_matches=home_count,
            home_wins=home_wins,
            home_draws=home_draws,
            home_losses=home_losses,
            home_goals_for=home_goals_for,
            home_goals_against=home_goals_against,
            away_matches=away_count,
            away_wins=away_wins,
            away_draws=away_draws,
            away_losses=away_losses,
            away_goals_for=away_goals_for,
            away_goals_against=away_goals_against,
            home_win_rate=(
                home_wins / home_count if home_count else 0
            ),
            away_win_rate=(
                away_wins / away_count if away_count else 0
            ),
        )

        print(team.name)

    db.close()

    print("Finished!")
    

if __name__ == "__main__":
    main()