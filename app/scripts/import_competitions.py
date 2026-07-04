from app.database.connection import SessionLocal
from app.providers.football.competition_provider import CompetitionProvider
from app.services.competition_service import CompetitionService


def main():
    db = SessionLocal()

    try:
        provider = CompetitionProvider()
        service = CompetitionService(db)

        competitions = provider.fetch_competitions()

        print(f"Found {len(competitions)} competitions.\n")

        for competition in competitions:
            saved = service.create(competition)
            print(f"✓ {saved.name}")

    finally:
        db.close()


if __name__ == "__main__":
    main()