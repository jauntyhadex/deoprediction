
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import text

from app.database.connection import SessionLocal


def main() -> None:
    db = SessionLocal()
    now = datetime.now(UTC).replace(tzinfo=None)

    rows = db.execute(
        text("""
            SELECT
                c.id,
                c.code,
                c.name,
                c.country,
                COUNT(DISTINCT f.id) AS total_fixtures,
                SUM(CASE WHEN f.kickoff_time >= :now THEN 1 ELSE 0 END) AS upcoming_fixtures,
                MIN(CASE WHEN f.kickoff_time >= :now THEN f.kickoff_time ELSE NULL END) AS next_kickoff,
                MAX(f.kickoff_time) AS last_kickoff
            FROM competitions c
            LEFT JOIN fixtures f ON f.competition_id = c.id
            GROUP BY c.id, c.code, c.name, c.country
            ORDER BY upcoming_fixtures DESC, c.name
        """),
        {"now": now},
    ).fetchall()

    print("ACTIVE COMPETITION AUDIT")
    print("")

    for row in rows:
        status = "ACTIVE" if row.upcoming_fixtures and row.upcoming_fixtures > 0 else "INACTIVE"
        print(
            f"{status:8} | "
            f"{row.code or '-':6} | "
            f"upcoming={row.upcoming_fixtures or 0:4} | "
            f"total={row.total_fixtures or 0:4} | "
            f"next={row.next_kickoff or '-'} | "
            f"last={row.last_kickoff or '-'} | "
            f"{row.name} | {row.country or '-'}"
        )

    db.close()


if __name__ == "__main__":
    main()
