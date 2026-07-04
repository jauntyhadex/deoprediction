from datetime import datetime
import time

from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.team import Team
from app.providers.football.fixture_provider import FixtureProvider
from app.services.fixture_service import FixtureService


def main():
    db = SessionLocal()

    provider = FixtureProvider()
    service = FixtureService(db)

    competitions = db.query(Competition).all()

    for competition in competitions:
        print(f"\nImporting fixtures for {competition.name}...")

        try:
            matches = provider.get_matches(competition.code)

            print(f"Found {len(matches)} matches")

            for match in matches:

                existing = service.get_by_external_id(match["id"])

                if existing:
                    continue

                home_team = (
                    db.query(Team)
                    .filter(
                        Team.external_id ==
                        match["homeTeam"]["id"]
                    )
                    .first()
                )

                away_team = (
                    db.query(Team)
                    .filter(
                        Team.external_id ==
                        match["awayTeam"]["id"]
                    )
                    .first()
                )
                
                if not home_team or not away_team:
                    print(
                        f"Skipping match {match['id']} - "
                        f"home={match['homeTeam']['name']} "
                        f"away={match['awayTeam']['name']}"
                    )
                    continue
                
                service.create(
                    api_fixture_id=match["id"],
                    competition_id=competition.id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    season=str(match["season"]["id"]),
                    venue=None,
                    status=match["status"],
                    kickoff_time=datetime.fromisoformat(
                        match["utcDate"].replace("Z", "+00:00")
                    ),
                    home_score=match["score"]["fullTime"]["home"],
                    away_score=match["score"]["fullTime"]["away"],
                )

            print("Finished.")

            time.sleep(5)

        except Exception as e:
            print(f"Failed for {competition.code}: {e}")
            time.sleep(10)

    db.close()


if __name__ == "__main__":
    main()