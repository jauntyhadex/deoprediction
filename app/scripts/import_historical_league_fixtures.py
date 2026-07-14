import time
from datetime import datetime, timezone

import httpx

from app.clients.football_api_client import (
    FootballAPIClient,
)
from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.fixture import Fixture
from app.utils.fixture_status_utils import (
    normalize_fixture_status,
)
from app.models.team import Team


HISTORICAL_SEASON = 2025

REQUEST_DELAY_SECONDS = 7

TARGET_COMPETITION_CODES = [
    "ELC",
    "PL",
    "FL1",
    "BL1",
    "SA",
    "DED",
    "PD",
]


def limited_text(
    value,
    maximum_length: int,
    fallback: str | None = None,
) -> str | None:

    if value is None:
        value = fallback

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        text = fallback

    if text is None:
        return None

    return str(text)[:maximum_length]


def parse_utc_datetime(
    value: str | None,
) -> datetime | None:

    if not value:
        return None

    parsed = datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )

    if parsed.tzinfo is not None:

        parsed = parsed.astimezone(
            timezone.utc
        )

        parsed = parsed.replace(
            tzinfo=None
        )

    return parsed


def get_full_time_scores(
    match_data: dict,
) -> tuple[int | None, int | None]:

    score_data = (
        match_data.get("score")
        or {}
    )

    full_time = (
        score_data.get("fullTime")
        or {}
    )

    home_score = full_time.get(
        "home"
    )

    away_score = full_time.get(
        "away"
    )

    return (
        home_score,
        away_score,
    )


def get_season_value(
    match_data: dict,
    requested_season: int,
) -> str:

    season_data = (
        match_data.get("season")
        or {}
    )

    season_id = season_data.get(
        "id"
    )

    if season_id is not None:
        return str(season_id)

    start_date = season_data.get(
        "startDate"
    )

    if start_date:
        return str(start_date)[:4]

    return str(requested_season)


def find_or_create_team(
    db,
    team_data: dict,
    competition: Competition,
) -> tuple[Team | None, bool]:

    external_id = team_data.get(
        "id"
    )

    if external_id is None:
        return None, False

    team = (
        db.query(Team)
        .filter(
            Team.external_id
            == external_id
        )
        .order_by(
            Team.id.asc()
        )
        .first()
    )

    if team is not None:

        if (
            not team.logo
            and team_data.get("crest")
        ):
            team.logo = limited_text(
                team_data.get("crest"),
                255,
            )

        if (
            not team.tla
            and team_data.get("tla")
        ):
            team.tla = limited_text(
                team_data.get("tla"),
                10,
            )

        return team, False

    name = limited_text(
        team_data.get("name"),
        100,
        fallback=(
            f"Team {external_id}"
        ),
    )

    short_name = limited_text(
        team_data.get("shortName"),
        50,
        fallback=name,
    )

    team = Team(
        external_id=external_id,
        name=name,
        short_name=short_name,
        tla=limited_text(
            team_data.get("tla"),
            10,
        ),
        country=limited_text(
            competition.country,
            100,
            fallback="Unknown",
        ),
        founded=None,
        venue=None,
        website=None,
        club_colors=None,
        logo=limited_text(
            team_data.get("crest"),
            255,
        ),
        competition_id=competition.id,
    )

    db.add(team)
    db.flush()

    return team, True


def import_match(
    db,
    competition: Competition,
    match_data: dict,
    requested_season: int,
) -> dict:

    result = {
        "fixture_created": 0,
        "fixture_updated": 0,
        "team_created": 0,
        "skipped": 0,
    }

    api_fixture_id = match_data.get(
        "id"
    )

    kickoff_time = parse_utc_datetime(
        match_data.get("utcDate")
    )

    home_team_data = (
        match_data.get("homeTeam")
        or {}
    )

    away_team_data = (
        match_data.get("awayTeam")
        or {}
    )

    if (
        api_fixture_id is None
        or kickoff_time is None
        or home_team_data.get("id")
        is None
        or away_team_data.get("id")
        is None
    ):
        result["skipped"] += 1
        return result

    (
        home_team,
        home_created,
    ) = find_or_create_team(
        db=db,
        team_data=home_team_data,
        competition=competition,
    )

    (
        away_team,
        away_created,
    ) = find_or_create_team(
        db=db,
        team_data=away_team_data,
        competition=competition,
    )

    if home_created:
        result["team_created"] += 1

    if away_created:
        result["team_created"] += 1

    if (
        home_team is None
        or away_team is None
    ):
        result["skipped"] += 1
        return result

    (
        home_score,
        away_score,
    ) = get_full_time_scores(
        match_data
    )

    season_value = get_season_value(
        match_data=match_data,
        requested_season=requested_season,
    )

    status = normalize_fixture_status(
        match_data.get("status"),
        kickoff_time=kickoff_time,
        home_score=home_score,
        away_score=away_score,
    )

    venue = limited_text(
        match_data.get("venue"),
        150,
    )

    fixture = (
        db.query(Fixture)
        .filter(
            Fixture.api_fixture_id
            == api_fixture_id
        )
        .order_by(
            Fixture.id.asc()
        )
        .first()
    )

    if fixture is None:

        fixture = Fixture(
            api_fixture_id=(
                api_fixture_id
            ),
            competition_id=(
                competition.id
            ),
            home_team_id=(
                home_team.id
            ),
            away_team_id=(
                away_team.id
            ),
            season=season_value,
            venue=venue,
            status=status,
            kickoff_time=kickoff_time,
            home_score=home_score,
            away_score=away_score,
        )

        db.add(fixture)

        result[
            "fixture_created"
        ] += 1

        return result

    fixture.competition_id = (
        competition.id
    )

    fixture.home_team_id = (
        home_team.id
    )

    fixture.away_team_id = (
        away_team.id
    )

    fixture.season = season_value
    fixture.venue = venue
    fixture.status = status

    fixture.kickoff_time = (
        kickoff_time
    )

    fixture.home_score = home_score
    fixture.away_score = away_score

    result[
        "fixture_updated"
    ] += 1

    return result


def import_competition(
    db,
    client: FootballAPIClient,
    competition: Competition,
    season: int,
) -> dict:

    totals = {
        "received": 0,
        "fixture_created": 0,
        "fixture_updated": 0,
        "team_created": 0,
        "skipped": 0,
    }

    print()
    print(
        f"Downloading "
        f"{competition.name} "
        f"({competition.code}), "
        f"season {season}..."
    )

    data = client.get_matches(
        competition_code=(
            competition.code
        ),
        season=season,
    )

    matches = (
        data.get("matches")
        or []
    )

    totals["received"] = len(
        matches
    )

    for match_data in matches:

        match_result = import_match(
            db=db,
            competition=competition,
            match_data=match_data,
            requested_season=season,
        )

        for key in [
            "fixture_created",
            "fixture_updated",
            "team_created",
            "skipped",
        ]:
            totals[key] += (
                match_result[key]
            )

    db.commit()

    print(
        f"Received: "
        f"{totals['received']}"
    )

    print(
        f"Fixtures created: "
        f"{totals['fixture_created']}"
    )

    print(
        f"Fixtures updated: "
        f"{totals['fixture_updated']}"
    )

    print(
        f"Teams created: "
        f"{totals['team_created']}"
    )

    print(
        f"Matches skipped: "
        f"{totals['skipped']}"
    )

    return totals


def main():

    db = SessionLocal()
    client = FootballAPIClient()

    grand_totals = {
        "competitions_completed": 0,
        "competitions_failed": 0,
        "received": 0,
        "fixture_created": 0,
        "fixture_updated": 0,
        "team_created": 0,
        "skipped": 0,
    }

    try:

        competitions = (
            db.query(Competition)
            .filter(
                Competition.code.in_(
                    TARGET_COMPETITION_CODES
                )
            )
            .order_by(
                Competition.id.asc()
            )
            .all()
        )

        competition_by_code = {
            competition.code: competition
            for competition
            in competitions
        }

        missing_codes = [
            code
            for code
            in TARGET_COMPETITION_CODES
            if code
            not in competition_by_code
        ]

        if missing_codes:

            print(
                "Missing competition codes: "
                + ", ".join(
                    missing_codes
                )
            )

        for index, code in enumerate(
            TARGET_COMPETITION_CODES,
            start=1,
        ):

            competition = (
                competition_by_code.get(
                    code
                )
            )

            if competition is None:
                continue

            try:

                totals = import_competition(
                    db=db,
                    client=client,
                    competition=competition,
                    season=(
                        HISTORICAL_SEASON
                    ),
                )

                grand_totals[
                    "competitions_completed"
                ] += 1

                for key in [
                    "received",
                    "fixture_created",
                    "fixture_updated",
                    "team_created",
                    "skipped",
                ]:
                    grand_totals[key] += (
                        totals[key]
                    )

            except httpx.HTTPStatusError as error:

                db.rollback()

                grand_totals[
                    "competitions_failed"
                ] += 1

                status_code = (
                    error.response.status_code
                )

                response_text = (
                    error.response.text
                )

                print()
                print(
                    f"FAILED: "
                    f"{competition.name}"
                )

                print(
                    f"HTTP status: "
                    f"{status_code}"
                )

                print(
                    "Response: "
                    f"{response_text[:500]}"
                )

            except Exception as error:

                db.rollback()

                grand_totals[
                    "competitions_failed"
                ] += 1

                print()
                print(
                    f"FAILED: "
                    f"{competition.name}"
                )

                print(
                    f"{type(error).__name__}: "
                    f"{error}"
                )

            if (
                index
                < len(
                    TARGET_COMPETITION_CODES
                )
            ):

                print(
                    f"Waiting "
                    f"{REQUEST_DELAY_SECONDS} "
                    "seconds..."
                )

                time.sleep(
                    REQUEST_DELAY_SECONDS
                )

        print()
        print(
            "HISTORICAL IMPORT COMPLETE"
        )

        print("=" * 70)

        print(
            "Competitions completed: "
            f"{grand_totals[
                'competitions_completed'
            ]}"
        )

        print(
            "Competitions failed: "
            f"{grand_totals[
                'competitions_failed'
            ]}"
        )

        print(
            "Matches received: "
            f"{grand_totals['received']}"
        )

        print(
            "Fixtures created: "
            f"{grand_totals[
                'fixture_created'
            ]}"
        )

        print(
            "Fixtures updated: "
            f"{grand_totals[
                'fixture_updated'
            ]}"
        )

        print(
            "Teams created: "
            f"{grand_totals[
                'team_created'
            ]}"
        )

        print(
            "Matches skipped: "
            f"{grand_totals['skipped']}"
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()