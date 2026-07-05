from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.services.head_to_head_service import HeadToHeadService


def main():

    db = SessionLocal()

    service = HeadToHeadService(db)

    fixtures = (
        db.query(Fixture)
        .filter(Fixture.status == "FINISHED")
        .all()
    )

    print(f"Processing {len(fixtures)} fixtures...")

    pairs = {}

    for match in fixtures:

        key = (
            match.home_team_id,
            match.away_team_id,
        )

        if key not in pairs:
            pairs[key] = []

        pairs[key].append(match)

    for (home_team_id, away_team_id), matches in pairs.items():

        matches_played = len(matches)

        home_wins = 0
        draws = 0
        away_wins = 0

        home_goals = 0
        away_goals = 0

        btts = 0
        over25 = 0

        for match in matches:

            if match.home_score is None or match.away_score is None:
                continue

            home_goals += match.home_score
            away_goals += match.away_score

            if match.home_score > match.away_score:
                home_wins += 1

            elif match.home_score < match.away_score:
                away_wins += 1

            else:
                draws += 1

            if match.home_score > 0 and match.away_score > 0:
                btts += 1

            if (match.home_score + match.away_score) > 2:
                over25 += 1

        service.create_or_update(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            matches_played=matches_played,
            home_wins=home_wins,
            draws=draws,
            away_wins=away_wins,
            home_goals=home_goals,
            away_goals=away_goals,
            average_goals=(
                (home_goals + away_goals) / matches_played
                if matches_played else 0
            ),
            btts_rate=(
                btts / matches_played
                if matches_played else 0
            ),
            over25_rate=(
                over25 / matches_played
                if matches_played else 0
            ),
        )

    db.close()

    print("Finished!")
    

if __name__ == "__main__":
    main()