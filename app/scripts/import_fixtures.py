from app.database.connection import SessionLocal
from app.providers.football.fixture_provider import FixtureProvider
from app.services.fixture_service import FixtureService
from app.models.competition import Competition
from app.models.team import Team


def main():
    db = SessionLocal()

    provider = FixtureProvider()
    service = FixtureService(db)

    competitions = db.query(Competition).all()

    import time

for competition in competitions:
    print(f"\nImporting fixtures for {competition.name}...")

    try:
        matches = provider.get_matches(competition.code)
    except Exception as e:
        print(f"Skipping {competition.code} due to API limit: {e}")
        time.sleep(10)  # wait before continuing
        continue

    print(f"Found {len(matches)} matches")

    time.sleep(6) 

if __name__ == "__main__":
    main()