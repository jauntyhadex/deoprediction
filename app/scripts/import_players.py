from datetime import date
import time

from app.database.connection import SessionLocal
from app.models.team import Team
from app.providers.football.player_provider import PlayerProvider
from app.services.player_service import PlayerService


def parse_date(value):
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def main():
    db = SessionLocal()

    provider = PlayerProvider()
    service = PlayerService(db)

    teams = db.query(Team).all()

    for team in teams:
        print(f"\nImporting players for {team.name}...")

        try:
            players = provider.get_players(team.external_id)

            for player in players:
                existing = service.get_by_external_id(player["id"])

                if existing:
                    print(f"Skipping {player['name']}")
                    continue

                service.create(
                    external_id=player["id"],
                    name=player["name"],
                    jersey_number=player.get("shirtNumber"),
                    position=player.get("position", "Unknown"),
                    nationality=player.get("nationality"),
                    date_of_birth=parse_date(
                        player.get("dateOfBirth")
                    ),
                    team_id=team.id,
                )

                print(f"Imported {player['name']}")

            # Small delay after each successful team
            time.sleep(2)

        except Exception as e:
            print(f"Failed for {team.name}: {e}")

            # Longer delay after rate limit
            time.sleep(10)

            continue

    db.close()


if __name__ == "__main__":
    main()