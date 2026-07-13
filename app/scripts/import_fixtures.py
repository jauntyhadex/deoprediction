from datetime import datetime
import time

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.fixture import Fixture
from app.models.team import Team
from app.providers.football.fixture_provider import FixtureProvider


REQUEST_DELAY_SECONDS = 7
ERROR_DELAY_SECONDS = 10


def parse_datetime(value: str | None):

    if not value:
        return None

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def get_full_time_scores(
    match: dict,
) -> tuple[int | None, int | None]:

    score = (
        match.get("score")
        or {}
    )

    full_time = (
        score.get("fullTime")
        or {}
    )

    return (
        full_time.get("home"),
        full_time.get("away"),
    )


def main():

    db = SessionLocal()

    provider = FixtureProvider()

    competitions_completed = 0
    competitions_failed = 0

    fixtures_created = 0
    fixtures_updated = 0
    fixtures_skipped = 0

    try:

        competitions = (
            db.query(Competition)
            .order_by(
                Competition.id.asc()
            )
            .all()
        )

        for competition in competitions:

            print()
            print(
                "Importing fixtures for "
                f"{competition.name}..."
            )

            try:

                matches = provider.get_matches(
                    competition.code
                )

                print(
                    f"Found {len(matches)} matches"
                )

                competition_created = 0
                competition_updated = 0
                competition_skipped = 0

                for match in matches:

                    api_fixture_id = match.get(
                        "id"
                    )

                    home_team_data = (
                        match.get("homeTeam")
                        or {}
                    )

                    away_team_data = (
                        match.get("awayTeam")
                        or {}
                    )

                    home_external_id = (
                        home_team_data.get("id")
                    )

                    away_external_id = (
                        away_team_data.get("id")
                    )

                    if (
                        api_fixture_id is None
                        or home_external_id is None
                        or away_external_id is None
                    ):

                        fixtures_skipped += 1
                        competition_skipped += 1

                        print(
                            "Skipping incomplete match "
                            f"record: {api_fixture_id}"
                        )

                        continue

                    home_team = (
                        db.query(Team)
                        .filter(
                            Team.external_id
                            == home_external_id
                        )
                        .first()
                    )

                    away_team = (
                        db.query(Team)
                        .filter(
                            Team.external_id
                            == away_external_id
                        )
                        .first()
                    )

                    if (
                        home_team is None
                        or away_team is None
                    ):

                        fixtures_skipped += 1
                        competition_skipped += 1

                        print(
                            f"Skipping match "
                            f"{api_fixture_id} - "
                            f"home="
                            f"{home_team_data.get('name')} "
                            f"away="
                            f"{away_team_data.get('name')}"
                        )

                        continue

                    (
                        home_score,
                        away_score,
                    ) = get_full_time_scores(
                        match
                    )

                    season_data = (
                        match.get("season")
                        or {}
                    )

                    fixture_values = {
                        "competition_id": (
                            competition.id
                        ),
                        "home_team_id": (
                            home_team.id
                        ),
                        "away_team_id": (
                            away_team.id
                        ),
                        "season": str(
                            season_data.get(
                                "id",
                                "",
                            )
                        ),
                        "venue": None,
                        "status": match.get(
                            "status"
                        ),
                        "kickoff_time": (
                            parse_datetime(
                                match.get(
                                    "utcDate"
                                )
                            )
                        ),
                        "home_score": (
                            home_score
                        ),
                        "away_score": (
                            away_score
                        ),
                    }

                    existing_fixture = (
                        db.query(Fixture)
                        .filter(
                            Fixture.api_fixture_id
                            == api_fixture_id
                        )
                        .first()
                    )

                    if existing_fixture is None:

                        fixture = Fixture(
                            api_fixture_id=(
                                api_fixture_id
                            ),
                            **fixture_values,
                        )

                        db.add(fixture)

                        fixtures_created += 1
                        competition_created += 1

                    else:

                        for (
                            field_name,
                            field_value,
                        ) in fixture_values.items():

                            setattr(
                                existing_fixture,
                                field_name,
                                field_value,
                            )

                        fixtures_updated += 1
                        competition_updated += 1

                db.commit()

                competitions_completed += 1

                print(
                    "Created: "
                    f"{competition_created}"
                )

                print(
                    "Updated: "
                    f"{competition_updated}"
                )

                print(
                    "Skipped: "
                    f"{competition_skipped}"
                )

                print("Finished.")

                time.sleep(
                    REQUEST_DELAY_SECONDS
                )

            except Exception as error:

                db.rollback()

                competitions_failed += 1

                print(
                    f"Failed for "
                    f"{competition.code}: "
                    f"{error}"
                )

                time.sleep(
                    ERROR_DELAY_SECONDS
                )

        print()
        print(
            "FIXTURE IMPORT SUMMARY"
        )

        print("-" * 60)

        print(
            "Competitions completed: "
            f"{competitions_completed}"
        )

        print(
            "Competitions failed: "
            f"{competitions_failed}"
        )

        print(
            "Fixtures created: "
            f"{fixtures_created}"
        )

        print(
            "Fixtures updated: "
            f"{fixtures_updated}"
        )

        print(
            "Fixtures skipped: "
            f"{fixtures_skipped}"
        )

        if competitions_failed > 0:

            raise SystemExit(1)

    finally:

        db.close()


if __name__ == "__main__":
    main()
