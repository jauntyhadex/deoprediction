
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


BASE_URL = "https://v3.football.api-sports.io"
CACHE_PATH = Path("data/api_football_league_audit_cache.json")
COUNTRIES_CACHE_PATH = Path("data/api_football_country_cache.json")

PRIORITY_COUNTRIES = [
    "Norway",
    "Australia",
    "Russia",
    "Peru",
    "Paraguay",
    "Scotland",
    "South Korea",
    "Sweden",
    "USA",
    "Switzerland",
    "Slovakia",
    "Mexico",
    "Hungary",
    "Germany",
    "Finland",
    "Estonia",
    "Denmark",
    "Czech Republic",
    "Colombia",
    "China",
    "Chile",
    "Brazil",
    "Argentina",
    "Austria",
    "Uruguay",
    "Ecuador",
    "Bolivia",
    "Venezuela",
    "Japan",
    "Poland",
    "Romania",
    "Serbia",
    "Croatia",
    "Bulgaria",
    "Ireland",
    "Wales",
    "Northern Ireland",
]


def read_env() -> dict[str, str]:
    env_path = Path(".env")
    env = {}

    if not env_path.exists():
        return env

    for line in env_path.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")

    return env


def read_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}

    try:
        return json.loads(CACHE_PATH.read_text())
    except json.JSONDecodeError:
        return {}


def write_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True))


def unique_country_list(countries: list[str]) -> list[str]:
    seen = set()
    output = []

    for country in countries:
        name = str(country or "").strip()

        if not name:
            continue

        key = name.lower()

        if key in seen:
            continue

        seen.add(key)
        output.append(name)

    return output


def read_discovered_countries_cache() -> list[str]:
    if not COUNTRIES_CACHE_PATH.exists():
        return []

    try:
        data = json.loads(COUNTRIES_CACHE_PATH.read_text())
    except json.JSONDecodeError:
        return []

    countries = data.get("countries", [])

    if not isinstance(countries, list):
        return []

    return [str(country) for country in countries]


def write_discovered_countries_cache(countries: list[str]) -> None:
    COUNTRIES_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    COUNTRIES_CACHE_PATH.write_text(
        json.dumps({"countries": countries}, indent=2, sort_keys=True)
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


def print_country(country: str, data: dict, cached: bool) -> None:
    leagues = data.get("response", [])
    cache_label = "cached" if cached else "fresh"

    print(f"\n{country.upper()} | current leagues found: {len(leagues)} | {cache_label}")

    for item in leagues:
        league = item.get("league") or {}
        seasons = item.get("seasons") or []
        current_seasons = [season for season in seasons if season.get("current")]
        season = current_seasons[0] if current_seasons else (seasons[-1] if seasons else {})

        print(
            f"  {league.get('id')} | "
            f"{league.get('name')} | "
            f"{league.get('type')} | "
            f"{season.get('year')} | "
            f"{season.get('start')} to {season.get('end')}"
        )


def main() -> None:
    env = read_env()
    api_key = env.get("API_FOOTBALL_API_KEY") or env.get("APISPORTS_API_KEY")

    if not api_key:
        print("API_FOOTBALL_API_KEY not found in .env")
        print("Add a free API-Football key later, then rerun this script.")
        print("No paid provider needed.")
        return

    daily_limit = int(env.get("API_FOOTBALL_AUDIT_LIMIT", os.getenv("API_FOOTBALL_AUDIT_LIMIT", "8")))
    auto_discover = env.get("API_FOOTBALL_AUTO_DISCOVER_COUNTRIES", "true").lower() != "false"
    cache = read_cache()
    requests_used = 0

    print("FREE API-FOOTBALL CURRENT LEAGUE AUDIT")
    print("Safe mode: cached countries cost 0 requests.")
    print(f"Safe mode: max fresh API requests this run = {daily_limit}")
    print("Safe mode: waits 7 seconds between fresh requests.")
    print("")

    discovered_countries = []

    if auto_discover:
        discovered_countries = read_discovered_countries_cache()

        if discovered_countries:
            print(f"Country discovery cache loaded: {len(discovered_countries)} countries")
        elif requests_used < daily_limit:
            try:
                countries_data = api_get("/countries", {}, api_key)
            except urllib.error.HTTPError as error:
                print(f"Country discovery skipped: HTTP {error.code}: {error.reason}")
            else:
                discovered_countries = [
                    item.get("name")
                    for item in countries_data.get("response", [])
                    if item.get("name")
                ]
                discovered_countries = sorted(unique_country_list(discovered_countries))
                write_discovered_countries_cache(discovered_countries)
                requests_used += 1
                print(f"Country discovery saved: {len(discovered_countries)} countries")
                time.sleep(7)

    target_countries = unique_country_list(PRIORITY_COUNTRIES + discovered_countries)

    for country in target_countries:
        if country in cache:
            print_country(country, cache[country], cached=True)
            continue

        if requests_used >= daily_limit:
            print("")
            print(f"Stopped safely after {requests_used} fresh requests.")
            print("Run again tomorrow or increase API_FOOTBALL_AUDIT_LIMIT carefully.")
            break

        try:
            data = api_get(
                "/leagues",
                {"country": country, "current": "true"},
                api_key,
            )
        except urllib.error.HTTPError as error:
            print("")
            print(f"Stopped because provider returned HTTP {error.code}: {error.reason}")
            print("Do not keep retrying now. Wait for quota/rate-limit reset.")
            write_cache(cache)
            return

        cache[country] = data
        write_cache(cache)
        requests_used += 1

        print_country(country, data, cached=False)
        time.sleep(7)

    print("")
    print(f"Done. Fresh requests used this run: {requests_used}")
    print(f"Cache saved to: {CACHE_PATH}")


if __name__ == "__main__":
    main()
