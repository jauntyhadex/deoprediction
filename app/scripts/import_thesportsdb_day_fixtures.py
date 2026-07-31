# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from app.database import model_loader
from app.database.connection import SessionLocal
from app.scripts.import_thesportsdb_current_fixtures import (
    TARGET_LEAGUES,
    api_get,
    import_event,
    normalize_name,
    read_env,
    read_json,
    write_json,
)


CACHE_PATH = Path("data/thesportsdb_day_fixture_import_cache.json")


def resolve_target(event: dict) -> dict | None:
    event_league_id = str(event.get("idLeague") or "")

    for target in TARGET_LEAGUES:
        if str(target["league_id"]) == event_league_id:
            return target

    event_league_name = normalize_name(event.get("strLeague"))

    for target in TARGET_LEAGUES:
        target_name = normalize_name(target["league_name"])

        if event_league_name == target_name:
            return target

        if event_league_name and (
            event_league_name in target_name or target_name in event_league_name
        ):
            return target

    return None


def main() -> None:
    env = read_env()
    api_key = env.get("THESPORTSDB_API_KEY") or "123"

    target_date = sys.argv[1] if len(sys.argv) > 1 else str(date.today() + timedelta(days=1))

    cache = read_json(CACHE_PATH, {})
    cache_key = f"soccer:{target_date}"

    print("THESPORTSDB DAY FIXTURE IMPORT")
    print(f"Date: {target_date}")
    print("Safe mode: cached day calls cost 0 requests.")
    print("")

    if cache_key in cache:
        data = cache[cache_key]
        source = "cached"
    else:
        data = api_get(
            api_key,
            "eventsday.php",
            {
                "d": target_date,
                "s": "Soccer",
            },
        )
        cache[cache_key] = data
        write_json(CACHE_PATH, cache)
        source = "fresh"
        time.sleep(2)

    events = data.get("events") or []

    db = SessionLocal()

    try:
        matched = 0
        inserted_count = 0
        updated_count = 0
        skipped = 0

        print(f"Provider events found: {len(events)} | {source}")
        print("")

        for event in events:
            target = resolve_target(event)

            if not target:
                skipped += 1
                continue

            inserted, updated = import_event(db, target, event)

            matched += 1

            if inserted:
                inserted_count += 1

            if updated:
                updated_count += 1

            print(
                f"{event.get('dateEvent')} {event.get('strTime') or ''} | "
                f"{target['country']} | {target['league_name']} | "
                f"{event.get('strHomeTeam')} vs {event.get('strAwayTeam')} | "
                f"inserted={inserted} | updated={updated}"
            )

        db.commit()

        print("")
        print(f"Matched target events: {matched}")
        print(f"Inserted: {inserted_count}")
        print(f"Updated: {updated_count}")
        print(f"Skipped non-target events: {skipped}")
        print(f"Cache saved to: {CACHE_PATH}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
