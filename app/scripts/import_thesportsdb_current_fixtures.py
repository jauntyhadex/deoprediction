# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from app.database import model_loader
from app.database.connection import SessionLocal
from app.enums import Sport
from app.models.competition import Competition
from app.models.fixture import Fixture
from app.models.team import Team


AUDIT_CACHE_PATH = Path("data/thesportsdb_current_fixture_audit_cache.json")
IMPORT_CACHE_PATH = Path("data/thesportsdb_current_fixture_import_cache.json")

TSD_COMPETITION_OFFSET = 800_000_000
TSD_TEAM_OFFSET = 800_000_000
TSD_FIXTURE_OFFSET = 8_000_000_000

TARGET_LEAGUES = [
    {
        "country": "Norway",
        "league_id": 4358,
        "league_name": "Norwegian Eliteserien",
        "existing_code": "APIF-103",
    },
    {
        "country": "Norway",
        "league_id": 4457,
        "league_name": "Norwegian 1. Divisjon",
        "existing_code": "APIF-104",
    },
    {
        "country": "USA",
        "league_id": 4684,
        "league_name": "American USL Championship",
        "existing_code": None,
    },
    {
        "country": "Australia",
        "league_id": 5011,
        "league_name": "Australia New South Wales NPL",
        "existing_code": None,
    },
    {
        "country": "Paraguay",
        "league_id": 4900,
        "league_name": "Paraguayan División Intermedia",
        "existing_code": None,
    },
    {
        "country": "Peru",
        "league_id": 4688,
        "league_name": "Peruvian Primera Division",
        "existing_code": None,
    },
    {
        "country": "Peru",
        "league_id": 5073,
        "league_name": "Peruvian Segunda División",
        "existing_code": None,
    },
    {
        "country": "Scotland",
        "league_id": 4395,
        "league_name": "Scottish Championship",
        "existing_code": None,
    },
    {
        "country": "Scotland",
        "league_id": 4669,
        "league_name": "Scottish League 1",
        "existing_code": None,
    },
    {
        "country": "Scotland",
        "league_id": 4670,
        "league_name": "Scottish League 2",
        "existing_code": None,
    },
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


def read_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def api_get(api_key: str, endpoint: str, params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/{endpoint}?{query}"

    request = urllib.request.Request(url)

    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_name(value: str | None) -> str:
    value = value or ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = value.lower()
    value = value.replace("&", "and")

    for token in [".", ",", "-", "_", " fc", " fk", " sk", " bk", " if"]:
        value = value.replace(token, " ")

    return " ".join(value.split())


def parse_int(value) -> int | None:
    if value in [None, ""]:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def parse_kickoff(event: dict) -> datetime | None:
    timestamp = event.get("strTimestamp")

    if timestamp:
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass

    date_value = event.get("dateEvent")
    time_value = event.get("strTime") or "00:00:00"

    if not date_value:
        return None

    try:
        parsed = datetime.fromisoformat(f"{date_value}T{time_value}")
        return parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def get_or_create_competition(db, target: dict) -> Competition:
    existing_code = target.get("existing_code")

    if existing_code:
        competition = (
            db.query(Competition)
            .filter(Competition.code == existing_code)
            .first()
        )

        if competition:
            return competition

    external_id = TSD_COMPETITION_OFFSET + int(target["league_id"])
    code = f"TSD-{target['league_id']}"

    competition = (
        db.query(Competition)
        .filter(Competition.external_id == external_id)
        .first()
    )

    if competition:
        return competition

    competition = Competition(
        external_id=external_id,
        code=code,
        name=target["league_name"],
        country=target["country"],
        type="League",
        season=2026,
        sport=Sport.FOOTBALL,
    )

    db.add(competition)
    db.flush()

    return competition


def get_or_create_team(db, competition: Competition, team_id: int | None, team_name: str) -> Team:
    external_id = TSD_TEAM_OFFSET + team_id if team_id else None

    if external_id:
        team = (
            db.query(Team)
            .filter(
                Team.competition_id == competition.id,
                Team.external_id == external_id,
            )
            .first()
        )

        if team:
            return team

    wanted = normalize_name(team_name)

    teams = (
        db.query(Team)
        .filter(Team.competition_id == competition.id)
        .all()
    )

    for team in teams:
        if normalize_name(team.name) == wanted:
            if external_id and team.external_id is None:
                team.external_id = external_id
            return team

    team = Team(
        external_id=external_id,
        name=team_name,
        short_name=team_name[:30],
        tla=team_name[:3].upper(),
        country=competition.country,
        competition_id=competition.id,
    )

    db.add(team)
    db.flush()

    return team


def import_event(db, target: dict, event: dict) -> tuple[bool, bool]:
    event_id = parse_int(event.get("idEvent"))

    if not event_id:
        return False, False

    home_name = event.get("strHomeTeam")
    away_name = event.get("strAwayTeam")
    kickoff_time = parse_kickoff(event)

    if not home_name or not away_name or not kickoff_time:
        return False, False

    competition = get_or_create_competition(db, target)

    home_team = get_or_create_team(
        db,
        competition,
        parse_int(event.get("idHomeTeam")),
        home_name,
    )

    away_team = get_or_create_team(
        db,
        competition,
        parse_int(event.get("idAwayTeam")),
        away_name,
    )

    api_fixture_id = TSD_FIXTURE_OFFSET + event_id

    fixture = (
        db.query(Fixture)
        .filter(Fixture.api_fixture_id == api_fixture_id)
        .first()
    )

    inserted = fixture is None

    if fixture is None:
        fixture = Fixture(api_fixture_id=api_fixture_id)
        db.add(fixture)

    fixture.competition_id = competition.id
    fixture.home_team_id = home_team.id
    fixture.away_team_id = away_team.id
    fixture.season = kickoff_time.year
    fixture.status = "SCHEDULED"
    fixture.kickoff_time = kickoff_time
    fixture.venue = event.get("strVenue")
    fixture.home_score = None
    fixture.away_score = None

    return inserted, not inserted


def get_events(api_key: str, target: dict, audit_cache: dict, import_cache: dict, fresh_state: dict) -> tuple[dict, str]:
    league_id = str(target["league_id"])

    if league_id in import_cache:
        return import_cache[league_id], "cached-import"

    audit_events = (audit_cache.get("events") or {}).get(league_id)

    if audit_events:
        import_cache[league_id] = audit_events
        write_json(IMPORT_CACHE_PATH, import_cache)
        return audit_events, "cached-audit"

    fresh_limit = fresh_state["fresh_limit"]

    if fresh_state["fresh_requests"] >= fresh_limit:
        return {"events": []}, "skipped-limit"

    data = api_get(api_key, "eventsnextleague.php", {"id": league_id})
    import_cache[league_id] = data
    write_json(IMPORT_CACHE_PATH, import_cache)

    fresh_state["fresh_requests"] += 1
    time.sleep(2)

    return data, "fresh"


def main() -> None:
    env = read_env()
    api_key = env.get("THESPORTSDB_API_KEY") or "123"

    audit_cache = read_json(AUDIT_CACHE_PATH, {"events": {}})
    import_cache = read_json(IMPORT_CACHE_PATH, {})

    fresh_state = {
        "fresh_limit": int(env.get("THESPORTSDB_IMPORT_LIMIT", os.getenv("THESPORTSDB_IMPORT_LIMIT", "8"))),
        "fresh_requests": 0,
    }

    print("THESPORTSDB CURRENT FIXTURE IMPORT")
    print("Safe mode: cached events cost 0 requests.")
    print(f"Safe mode: max fresh requests this run = {fresh_state['fresh_limit']}")
    print("")

    db = SessionLocal()

    try:
        total_inserted = 0
        total_updated = 0
        total_seen = 0

        for target in TARGET_LEAGUES:
            events_data, source = get_events(api_key, target, audit_cache, import_cache, fresh_state)
            events = events_data.get("events") or []

            inserted_count = 0
            updated_count = 0

            for event in events:
                inserted, updated = import_event(db, target, event)

                if inserted:
                    inserted_count += 1

                if updated:
                    updated_count += 1

            db.commit()

            total_seen += len(events)
            total_inserted += inserted_count
            total_updated += updated_count

            print(
                f"{target['country']} | {target['league_id']} | {target['league_name']} | "
                f"{source} | events={len(events)} | inserted={inserted_count} | updated={updated_count}"
            )

        print("")
        print(f"Done. Events seen: {total_seen}")
        print(f"Inserted: {total_inserted}")
        print(f"Updated: {total_updated}")
        print(f"Fresh requests used: {fresh_state['fresh_requests']}")
        print(f"Cache saved to: {IMPORT_CACHE_PATH}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
