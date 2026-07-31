# -*- coding: utf-8 -*-
from __future__ import annotations

import difflib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


CACHE_PATH = Path("data/thesportsdb_current_fixture_audit_cache.json")

TARGET_LEAGUES = [
    ("Norway", "Eliteserien"),
    ("Norway", "1. Division"),

    ("Australia", "A-League"),
    ("Australia", "New South Wales NPL"),
    ("Australia", "Victoria NPL"),
    ("Australia", "Queensland NPL"),

    ("Russia", "Premier League"),
    ("Russia", "First League"),

    ("Peru", "Primera Division"),
    ("Peru", "Segunda Division"),

    ("Paraguay", "Division Profesional"),
    ("Paraguay", "Division Intermedia"),

    ("Scotland", "Premiership"),
    ("Scotland", "Championship"),
    ("Scotland", "League One"),
    ("Scotland", "League Two"),

    ("Sweden", "Allsvenskan"),
    ("Sweden", "Superettan"),
    ("Sweden", "Ettan"),
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
    if not CACHE_PATH.exists():
        return {"leagues": {}, "events": {}}

    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"leagues": {}, "events": {}}

    data.setdefault("leagues", {})
    data.setdefault("events", {})
    return data


def write_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")


def api_get(api_key: str, endpoint: str, params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/{endpoint}?{query}"

    request = urllib.request.Request(url)

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def score_match(expected: str, actual: str) -> float:
    expected_clean = expected.lower().replace("-", " ").replace(".", " ").strip()
    actual_clean = actual.lower().replace("-", " ").replace(".", " ").strip()

    if expected_clean in actual_clean or actual_clean in expected_clean:
        return 1.0

    return difflib.SequenceMatcher(None, expected_clean, actual_clean).ratio()


def find_best_league(expected_name: str, leagues: list[dict]) -> tuple[dict | None, float]:
    best = None
    best_score = 0.0

    for league in leagues:
        name = league.get("strLeague") or ""
        score = score_match(expected_name, name)

        if score > best_score:
            best = league
            best_score = score

    return best, best_score


def main() -> None:
    env = read_env()
    api_key = env.get("THESPORTSDB_API_KEY") or "123"
    fresh_limit = int(env.get("THESPORTSDB_AUDIT_LIMIT", os.getenv("THESPORTSDB_AUDIT_LIMIT", "12")))

    cache = read_cache()
    fresh_requests = 0

    print("THESPORTSDB CURRENT UNDERGROUND FIXTURE AUDIT")
    print("Safe mode: cached calls cost 0 requests.")
    print(f"Safe mode: max fresh requests this run = {fresh_limit}")
    print("")

    countries = sorted({country for country, _ in TARGET_LEAGUES})

    for country in countries:
        cache_key = country.lower()

        if cache_key in cache["leagues"]:
            leagues_data = cache["leagues"][cache_key]
            source = "cached"
        else:
            if fresh_requests >= fresh_limit:
                print(f"Stopped safely after {fresh_requests} fresh requests.")
                write_cache(cache)
                return

            try:
                leagues_data = api_get(
                    api_key,
                    "search_all_leagues.php",
                    {"c": country, "s": "Soccer"},
                )
            except Exception as error:
                print(f"League search failed for {country}: {type(error).__name__}: {error}")
                continue

            cache["leagues"][cache_key] = leagues_data
            write_cache(cache)
            fresh_requests += 1
            source = "fresh"
            time.sleep(2)

        leagues = leagues_data.get("countries") or []
        print(f"\n{country.upper()} | leagues found={len(leagues)} | {source}")

        for league in leagues[:10]:
            print(f"  CANDIDATE | {league.get('idLeague')} | {league.get('strLeague')}")

        for league in leagues[:10]:
            print(f"  CANDIDATE | {league.get('idLeague')} | {league.get('strLeague')}")

        targets = [name for target_country, name in TARGET_LEAGUES if target_country == country]

        for expected_name in targets:
            best, match_score = find_best_league(expected_name, leagues)

            if not best or match_score < 0.55:
                print(f"  MISS | {expected_name}")
                continue

            league_id = best.get("idLeague")
            league_name = best.get("strLeague")

            events_cache_key = str(league_id)

            if events_cache_key in cache["events"]:
                events_data = cache["events"][events_cache_key]
                events_source = "cached"
            else:
                if fresh_requests >= fresh_limit:
                    print(f"  MATCH | {expected_name} -> {league_name} ({league_id}) | events not checked, request limit reached")
                    continue

                try:
                    events_data = api_get(
                        api_key,
                        "eventsnextleague.php",
                        {"id": str(league_id)},
                    )
                except Exception as error:
                    print(
                        f"  MATCH | {expected_name} -> {league_name} ({league_id}) "
                        f"| events failed: {type(error).__name__}: {error}"
                    )
                    continue

                cache["events"][events_cache_key] = events_data
                write_cache(cache)
                fresh_requests += 1
                events_source = "fresh"
                time.sleep(2)

            events = events_data.get("events") or []

            print(
                f"  MATCH | {expected_name} -> {league_name} ({league_id}) "
                f"| score={match_score:.2f} | next_events={len(events)} | {events_source}"
            )

            for event in events[:3]:
                print(
                    f"    {event.get('dateEvent')} {event.get('strTime') or ''} | "
                    f"{event.get('strHomeTeam')} vs {event.get('strAwayTeam')}"
                )

    print("")
    print(f"Done. Fresh requests used this run: {fresh_requests}")
    print(f"Cache saved to: {CACHE_PATH}")


if __name__ == "__main__":
    main()
