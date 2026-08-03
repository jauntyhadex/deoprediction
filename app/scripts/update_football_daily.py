# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from app.scripts.import_thesportsdb_all_day_fixtures import import_all_days


def run_command(command: list[str]) -> None:
    print("")
    print("RUN:", " ".join(command))
    result = subprocess.run(command)

    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--start-offset", type=int, default=-1)
    parser.add_argument("--skip-rebuild", action="store_true")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).date()
    start = today + timedelta(days=args.start_offset)
    end = today + timedelta(days=args.days)

    print("DEOPREDICTION FOOTBALL DAILY UPDATE")
    print(f"UTC today: {today}")
    print(f"Import window: {start} to {end}")
    print("")

    import_all_days(start, end)

    if not args.skip_rebuild:
        run_command([sys.executable, "-m", "app.scripts.rebuild_prediction_pipeline"])

    print("")
    print("FOOTBALL DAILY UPDATE COMPLETE")


if __name__ == "__main__":
    main()
