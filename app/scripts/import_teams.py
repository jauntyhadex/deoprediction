import time

from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.providers.football.team_provider import TeamProvider
from app.services.team_service import TeamService


def main():
    db = SessionLocal()

    provider = TeamProvider()
    service = TeamService(db)

    competitions = db.query(Competition).all()

    for competition in competitions:
        print(f"\nImporting teams for {competition.name}...")

    
        try:
            teams = provider.get_teams(competition.code)

        except Exception as e:
            print(f"Failed to fetch teams for {competition.code}: {e}")
            continue

        for team in teams:

            existing = service.get_by_external_id(team["id"])

            if existing:
                print(f"Skipping {team['name']}")
                continue

            service.create(
                external_id=team["id"],
                name=team["name"],
                short_name=team.get("shortName", team.get("name")),
                tla=team.get("tla"),
                country=team["area"]["name"] if team.get("area") else None,
                founded=team.get("founded"),
                venue=team.get("venue"),
                website=team.get("website"),
                club_colors=team.get("clubColors"),
                logo=team.get("crest"),
                competition_id=competition.id,
            )

            print(f"Imported {team['name']}")

        # IMPORTANT: avoid 429 rate limit
        time.sleep(5)

    db.close()


if __name__ == "__main__":
    main()