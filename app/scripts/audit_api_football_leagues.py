
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


BASE_URL = "https://v3.football.api-sports.io"

TARGET_COUNTRIES = [
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


def api_get(path: str, params: dict[str, str], api_key: str) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}{path}?{query}"

    request = urllib.request.Request(
        url,
        headers={"x-apisports-key": api_key},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    env = read_env()
    api_key = env.get("API_FOOTBALL_API_KEY") or env.get("APISPORTS_API_KEY")

    if not api_key:
        print("API_FOOTBALL_API_KEY not found in .env")
        print("Add a free API-Football key later, then rerun this script.")
        print("No paid provider needed.")
        return

    print("FREE API-FOOTBALL CURRENT LEAGUE AUDIT")
    print("Request budget: this uses about 1 request per country.")
    print("")

    total_requests = 0

    for country in TARGET_COUNTRIES:
        data = api_get(
            "/leagues",
            {"country": country, "current": "true"},
            api_key,
        )
        total_requests += 1

        leagues = data.get("response", [])
        print(f"\n{country.upper()} | current leagues found: {len(leagues)}")

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

        time.sleep(1)

    print("")
    print(f"Done. Approx requests used: {total_requests}")


if __name__ == "__main__":
    main()
