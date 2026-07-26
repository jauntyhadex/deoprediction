# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from app.database.connection import SessionLocal
from app.enums import Sport
from app.models.competition import Competition
from app.models.fixture import Fixture
from app.models.team import Team


BASE_URL = "https://v3.football.api-sports.io"
FIXTURE_CACHE_PATH = Path("data/api_football_fixture_import_cache.json")

COMPETITION_OFFSET = 900_000_000
TEAM_OFFSET = 900_000_000
FIXTURE_OFFSET = 9_000_000_000

HISTORICAL_SEASONS = [2024, 2023, 2022]

FIRST_BATCH_TARGETS = [
    ("Norway", 103),
    ("Norway", 104),

    ("Australia", 192),
    ("Australia", 195),
    ("Australia", 482),
    ("Australia", 188),

    ("Russia", 235),
    ("Russia", 236),

    ("Peru", 281),
    ("Peru", 282),

    ("Paraguay", 250),
    ("Paraguay", 252),
    ("Paraguay", 251),

    ("Scotland", 179),
    ("Scotland", 180),
    ("Scotland", 183),
    ("Scotland", 184),

    ("Sweden", 113),
    ("Sweden", 114),
    ("Sweden", 564),
    ("Sweden", 563),
]


def read_env() -> dict[str, str]:
    env_path = Path(".env")
    env = {}

    if not env_path.exists():
        return env

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")

    return env


def read_cache() -> dict:
    if not FIXTURE_CACHE_PATH.exists():
        return {}

    try:
        return json.loads(FIXTURE_CACHE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_cache(cache: dict) -> None:
    FIXTURE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_CACHE_PATH.write_text(
        json.dumps(cache, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def api_get(path: str, params: dict[str, str], api_key: str) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}{path}?{query}"

    request = urllib.request.Request(
        url,
        headers={"x-apisports-key": api_key},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def mapped_competition_external_id(league_id: int) -> int:
    return COMPETITION_OFFSET + int(league_id)


def mapped_team_external_id(team_id: int) -> int:
    return TEAM_OFFSET + int(team_id)


def mapped_fixture_id(fixture_id: int) -> int:
    return FIXTURE_OFFSET + int(fixture_id)


def parse_kickoff_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC).replace(tzinfo=None)

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(UTC).replace(tzinfo=None)

    return parsed


def map_status(status: dict) -> str:
    code = str(status.get("short") or status.get("long") or "").upper()

    if code in {"NS"}:
        return "SCHEDULED"

    if code in {"TBD"}:
        return "TIMED"

    if code in {"PST", "PSTD"}:
        return "POSTPONED"

    if code in {"CANC", "CANCELLED", "ABD", "ABANDONED"}:
        return "CANCELLED"

    if code in {"SUSP", "INT"}:
        return "SUSPENDED"

    if code in {"FT", "AET", "PEN"}:
        return "FINISHED"

    if code in {"AWD", "WO"}:
        return "AWARDED"

    if code in {"HT", "BT", "P"}:
        return "PAUSED"

    if code in {"1H", "2H", "ET", "LIVE"}:
        return "IN_PLAY"

    return "SCHEDULED"


def safe_tla(name: str) -> str:
    letters = "".join(character for character in name.upper() if character.isalnum())

    if not letters:
        return "TBD"

    return letters[:3]


def upsert_competition(db, league_data: dict, country_name: str, season: int) -> Competition:
    league = league_data.get("league") or {}
    league_id = int(league.get("id"))
    external_id = mapped_competition_external_id(league_id)
    code = f"APIF-{league_id}"

    competition = (
        db.query(Competition)
        .filter(Competition.external_id == external_id, Competition.code == code)
        .first()
    )

    if competition is None:
        competition = Competition(
            external_id=external_id,
            code=code,
            name=league.get("name") or code,
            country=country_name,
            type=league.get("type") or "League",
            emblem=league.get("logo"),
            season=str(season),
            sport=Sport.FOOTBALL,
        )
        db.add(competition)
        db.flush()
    else:
        competition.name = league.get("name") or competition.name
        competition.country = country_name
        competition.type = league.get("type") or competition.type
        competition.emblem = league.get("logo") or competition.emblem
        competition.season = str(season)
        competition.sport = Sport.FOOTBALL

    return competition


def upsert_team(db, team_data: dict, competition: Competition, country_name: str) -> Team:
    team_id = int(team_data.get("id"))
    external_id = mapped_team_external_id(team_id)
    name = team_data.get("name") or f"Team {team_id}"

    team = (
        db.query(Team)
        .filter(
            Team.external_id == external_id,
            Team.competition_id == competition.id,
        )
        .first()
    )

    if team is None:
        team = Team(
            external_id=external_id,
            name=name,
            short_name=name[:50],
            tla=safe_tla(name),
            country=country_name,
            founded=None,
            venue=None,
            website=None,
            club_colors=None,
            logo=team_data.get("logo"),
            competition_id=competition.id,
        )
        db.add(team)
        db.flush()
    else:
        team.name = name
        team.short_name = name[:50]
        team.tla = team.tla or safe_tla(name)
        team.logo = team_data.get("logo") or team.logo
        team.country = country_name

    return team


def upsert_fixture(db, item: dict, competition: Competition, home_team: Team, away_team: Team, season: int) -> str:
    fixture_data = item.get("fixture") or {}
    fixture_id = int(fixture_data.get("id"))
    mapped_id = mapped_fixture_id(fixture_id)

    venue_data = fixture_data.get("venue") or {}
    status_data = fixture_data.get("status") or {}
    goals = item.get("goals") or {}

    fixture = (
        db.query(Fixture)
        .filter(Fixture.api_fixture_id == mapped_id)
        .first()
    )

    values = {
        "competition_id": competition.id,
        "home_team_id": home_team.id,
        "away_team_id": away_team.id,
        "season": str(season),
        "venue": venue_data.get("name"),
        "status": map_status(status_data),
        "kickoff_time": parse_kickoff_time(fixture_data.get("date")),
        "home_score": goals.get("home"),
        "away_score": goals.get("away"),
    }

    if fixture is None:
        fixture = Fixture(api_fixture_id=mapped_id, **values)
        db.add(fixture)
        return "inserted"

    for key, value in values.items():
        setattr(fixture, key, value)

    return "updated"


def import_league(db, country_name: str, league_id: int, season: int, data: dict) -> dict:
    response = data.get("response") or []

    if not response:
        return {
            "fixtures": 0,
            "inserted": 0,
            "updated": 0,
            "teams": 0,
            "competition": f"APIF-{league_id}",
        }

    first = response[0]
    league_data = {"league": first.get("league") or {"id": league_id}}
    competition = upsert_competition(db, league_data, country_name, season)

    inserted = 0
    updated = 0
    touched_team_ids = set()

    for item in response:
        teams = item.get("teams") or {}
        home_data = teams.get("home") or {}
        away_data = teams.get("away") or {}

        if not home_data.get("id") or not away_data.get("id"):
            continue

        home_team = upsert_team(db, home_data, competition, country_name)
        away_team = upsert_team(db, away_data, competition, country_name)

        touched_team_ids.add(home_team.id)
        touched_team_ids.add(away_team.id)

        action = upsert_fixture(db, item, competition, home_team, away_team, season)

        if action == "inserted":
            inserted += 1
        else:
            updated += 1

    db.commit()

    return {
        "fixtures": inserted + updated,
        "inserted": inserted,
        "updated": updated,
        "teams": len(touched_team_ids),
        "competition": competition.name,
    }


def main() -> None:
    env = read_env()
    api_key = env.get("API_FOOTBALL_API_KEY") or env.get("APISPORTS_API_KEY")

    if not api_key:
        print("API_FOOTBALL_API_KEY not found in .env")
        return

    fresh_limit = int(env.get("API_FOOTBALL_IMPORT_LIMIT", os.getenv("API_FOOTBALL_IMPORT_LIMIT", "3")))
    cache = read_cache()
    fresh_requests = 0

    print("API-FOOTBALL UNDERGROUND LEAGUE IMPORT")
    print("Safe mode: cached league fixtures cost 0 requests.")
    print(f"Safe mode: max fresh historical fixture requests this run = {fresh_limit}")
    print("Safe mode: waits 7 seconds between fresh requests.")
    print("")

    db = SessionLocal()

    try:
        for country_name, league_id in FIRST_BATCH_TARGETS:
            for season in HISTORICAL_SEASONS:
                cache_key = f"{league_id}:{season}"

                if cache_key in cache:
                    data = cache[cache_key]
                    source = "cached"
                else:
                    if fresh_requests >= fresh_limit:
                        print("")
                        print(f"Stopped safely after {fresh_requests} fresh fixture requests.")
                        print("Run again later/tomorrow to continue importing the next leagues.")
                        return

                    try:
                        data = api_get(
                            "/fixtures",
                            {"league": str(league_id), "season": str(season)},
                            api_key,
                        )
                    except urllib.error.HTTPError as error:
                        print("")
                        print(f"Stopped because provider returned HTTP {error.code}: {error.reason}")
                        print("Do not keep retrying now. Wait for quota/rate-limit reset.")
                        write_cache(cache)
                        return

                    cache[cache_key] = data
                    write_cache(cache)
                    fresh_requests += 1
                    source = "fresh"
                    time.sleep(7)

                errors = data.get("errors") or {}

                if errors:
                    print(f"{country_name} | {league_id} | {season} | {source} | skipped | errors={errors}")
                    continue

                result = import_league(db, country_name, league_id, season, data)

                print(
                    f"{country_name} | {league_id} | {season} | {result['competition']} | {source} | "
                    f"fixtures={result['fixtures']} | inserted={result['inserted']} | "
                    f"updated={result['updated']} | teams={result['teams']}"
                )

    finally:
        db.close()

    print("")
    print(f"Done. Fresh fixture requests used this run: {fresh_requests}")
    print(f"Cache saved to: {FIXTURE_CACHE_PATH}")


if __name__ == "__main__":
    main()
