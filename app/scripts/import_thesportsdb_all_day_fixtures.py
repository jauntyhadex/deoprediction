# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from app.database import model_loader
from app.database.connection import SessionLocal
from app.scripts.import_thesportsdb_current_fixtures import (
    api_get,
    import_event,
    read_env,
    read_json,
    write_json,
)


CACHE_PATH = Path("data/thesportsdb_all_day_fixture_import_cache.json")


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def date_range(start: date, end: date):
    current = start

    while current <= end:
        yield current
        current = current + timedelta(days=1)


def parse_int(value):
    if value in [None, ""]:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def dynamic_target(event: dict) -> dict | None:
    league_id = parse_int(event.get("idLeague"))
    league_name = event.get("strLeague")

    if not league_id or not league_name:
        return None

    country = (
        event.get("strCountry")
        or event.get("strVenueCountry")
        or "Unknown"
    )

    return {
        "country": country,
        "league_id": league_id,
        "league_name": league_name,
        "existing_code": None,
    }


def import_all_days(start: date, end: date) -> dict:
    env = read_env()
    api_key = env.get("THESPORTSDB_API_KEY") or "123"

    cache = read_json(CACHE_PATH, {})

    db = SessionLocal()

    try:
        total_events = 0
        total_imported = 0
        total_inserted = 0
        total_updated = 0
        total_skipped = 0
        fresh_requests = 0

        print("THESPORTSDB ALL FOOTBALL DAY IMPORT")
        print(f"Date range: {start} to {end}")
        print("Mode: import every Soccer event returned by provider.")
        print("")

        for current_day in date_range(start, end):
            day_text = str(current_day)
            cache_key = f"soccer:{day_text}"

            if cache_key in cache:
                data = cache[cache_key]
                source = "cached"
            else:
                data = api_get(
                    api_key,
                    "eventsday.php",
                    {
                        "d": day_text,
                        "s": "Soccer",
                    },
                )
                cache[cache_key] = data
                write_json(CACHE_PATH, cache)
                source = "fresh"
                fresh_requests += 1
                time.sleep(2)

            events = data.get("events") or []

            print("")
            print(f"{day_text} | provider events={len(events)} | {source}")

            day_imported = 0
            day_inserted = 0
            day_updated = 0
            day_skipped = 0

            for event in events:
                target = dynamic_target(event)

                if not target:
                    day_skipped += 1
                    continue

                inserted, updated = import_event(db, target, event)

                if inserted or updated:
                    day_imported += 1

                if inserted:
                    day_inserted += 1

                if updated:
                    day_updated += 1

            db.commit()

            total_events += len(events)
            total_imported += day_imported
            total_inserted += day_inserted
            total_updated += day_updated
            total_skipped += day_skipped

            print(
                f"  imported={day_imported} | "
                f"inserted={day_inserted} | updated={day_updated} | skipped={day_skipped}"
            )

        print("")
        print("DONE")
        print(f"Provider events: {total_events}")
        print(f"Imported: {total_imported}")
        print(f"Inserted: {total_inserted}")
        print(f"Updated: {total_updated}")
        print(f"Skipped: {total_skipped}")
        print(f"Fresh requests used: {fresh_requests}")
        print(f"Cache saved to: {CACHE_PATH}")

        return {
            "provider_events": total_events,
            "imported": total_imported,
            "inserted": total_inserted,
            "updated": total_updated,
            "skipped": total_skipped,
            "fresh_requests": fresh_requests,
        }

    finally:
        db.close()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:")
        print("python -m app.scripts.import_thesportsdb_all_day_fixtures 2026-08-03 2026-08-06")
        raise SystemExit(1)

    start = parse_date(sys.argv[1])
    end = parse_date(sys.argv[2]) if len(sys.argv) >= 3 else start

    import_all_days(start, end)


if __name__ == "__main__":
    main()
