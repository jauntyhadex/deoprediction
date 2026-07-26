# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


CACHE_PATH = Path("data/api_football_league_audit_cache.json")

FIRST_BATCH_TARGETS = [
    ("Norway", 103, "Eliteserien"),
    ("Norway", 104, "1. Division"),

    ("Australia", 192, "New South Wales NPL"),
    ("Australia", 195, "Victoria NPL"),
    ("Australia", 482, "Queensland NPL"),
    ("Australia", 188, "A-League"),

    ("Russia", 235, "Premier League"),
    ("Russia", 236, "First League"),

    ("Peru", 281, "Primera Division"),
    ("Peru", 282, "Segunda Division"),

    ("Paraguay", 250, "Division Profesional - Apertura"),
    ("Paraguay", 252, "Division Profesional - Clausura"),
    ("Paraguay", 251, "Division Intermedia"),

    ("Scotland", 179, "Premiership"),
    ("Scotland", 180, "Championship"),
    ("Scotland", 183, "League One"),
    ("Scotland", 184, "League Two"),

    ("Sweden", 113, "Allsvenskan"),
    ("Sweden", 114, "Superettan"),
    ("Sweden", 564, "Ettan - Sodra"),
    ("Sweden", 563, "Ettan - Norra"),
]


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        raise SystemExit(
            "Cache not found. Run: python -m app.scripts.audit_api_football_leagues"
        )

    return json.loads(CACHE_PATH.read_text(encoding="utf-8"))


def find_league(cache: dict, country: str, league_id: int) -> dict | None:
    country_data = cache.get(country) or {}
    leagues = country_data.get("response") or []

    for item in leagues:
        league = item.get("league") or {}

        if league.get("id") == league_id:
            return item

    return None


def main() -> None:
    cache = load_cache()

    print("API-FOOTBALL FIRST UNDERGROUND IMPORT PLAN")
    print("Source: cached audit only. This script uses 0 API requests.")
    print("")

    missing = []
    selected = []

    for country, league_id, expected_name in FIRST_BATCH_TARGETS:
        item = find_league(cache, country, league_id)

        if item is None:
            missing.append((country, league_id, expected_name))
            continue

        league = item.get("league") or {}
        seasons = item.get("seasons") or []
        current_seasons = [season for season in seasons if season.get("current")]
        season = current_seasons[0] if current_seasons else (seasons[-1] if seasons else {})

        selected.append(
            {
                "country": country,
                "league_id": league.get("id"),
                "league_name": league.get("name"),
                "league_type": league.get("type"),
                "season": season.get("year"),
                "start": season.get("start"),
                "end": season.get("end"),
            }
        )

    print(f"Selected leagues: {len(selected)}")
    print("")

    for item in selected:
        print(
            f"{item['country']} | "
            f"{item['league_id']} | "
            f"{item['league_name']} | "
            f"{item['league_type']} | "
            f"{item['season']} | "
            f"{item['start']} to {item['end']}"
        )

    if missing:
        print("")
        print("Missing from cache:")
        for country, league_id, expected_name in missing:
            print(f"{country} | {league_id} | {expected_name}")

    print("")
    print("Next step: build importer for these selected leagues only.")


if __name__ == "__main__":
    main()
