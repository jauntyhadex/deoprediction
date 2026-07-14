from datetime import UTC, datetime
import time

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.fixture import Fixture
from app.utils.fixture_status_utils import (
    normalize_fixture_status,
)
from app.models.team import Team
from app.providers.football.fixture_provider import FixtureProvider


REQUEST_DELAY_SECONDS = 7
ERROR_DELAY_SECONDS = 10


def parse_datetime(
    value: str | None,
) -> datetime | None:

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


def main() -> None:

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

        teams = (
            db.query(Team)
            .filter(
                Team.external_id.is_not(None)
            )
            .all()
        )

        teams_by_external_id = {
            team.external_id: team
            for team in teams
        }

        existing_fixtures = (
            db.query(Fixture)
            .filter(
                Fixture.api_fixture_id.is_not(None)
            )
            .all()
        )

        fixtures_by_api_id = {
            fixture.api_fixture_id: fixture
            for fixture in existing_fixtures
        }

        print(
            "Preloaded teams: "
            f"{len(teams_by_external_id)}"
        )

        print(
            "Preloaded fixtures: "
            f"{len(fixtures_by_api_id)}"
        )

        total_competitions = len(
            competitions
        )

        for competition_index, competition in enumerate(
            competitions,
            start=1,
        ):

            print()
            print(
                f"[{competition_index}/"
                f"{total_competitions}] "
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

                refresh_time = datetime.now(UTC).replace(tzinfo=None)

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

                        continue

                    home_team = (
                        teams_by_external_id.get(
                            home_external_id
                        )
                    )

                    away_team = (
                        teams_by_external_id.get(
                            away_external_id
                        )
                    )

                    if (
                        home_team is None
                        or away_team is None
                    ):

                        fixtures_skipped += 1
                        competition_skipped += 1

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
                        "status": normalize_fixture_status(
                            match.get(
                                "status"
                            )
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
                        fixtures_by_api_id.get(
                            api_fixture_id
                        )
                    )

                    if existing_fixture is None:

                        fixture = Fixture(
                            api_fixture_id=(
                                api_fixture_id
                            ),
                            updated_at=refresh_time,
                            **fixture_values,
                        )

                        db.add(fixture)

                        fixtures_by_api_id[
                            api_fixture_id
                        ] = fixture

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

                        existing_fixture.updated_at = (
                            refresh_time
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

                if (
                    competition_index
                    < total_competitions
                ):
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
