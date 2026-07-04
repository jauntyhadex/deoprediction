import time

from app.database.connection import SessionLocal
from app.models.competition import Competition
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

            # We will save fixtures into the database in the next step.

            time.sleep(6)

        except Exception as e:
            print(f"Skipping {competition.code} due to API limit: {e}")
            time.sleep(10)
            continue

    db.close()


if __name__ == "__main__":
    main()