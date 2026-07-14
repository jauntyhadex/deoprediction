from datetime import datetime


VALID_FIXTURE_STATUSES = frozenset(
    {
        "SCHEDULED",
        "TIMED",
        "IN_PLAY",
        "PAUSED",
        "FINISHED",
        "POSTPONED",
        "SUSPENDED",
        "CANCELLED",
        "AWARDED",
    }
)


def normalize_fixture_status(
    value: object,
    *,
    kickoff_time: datetime | None = None,
    home_score: int | None = None,
    away_score: int | None = None,
) -> str:

    normalized = str(
        value or ""
    ).strip().upper()

    if normalized in VALID_FIXTURE_STATUSES:
        return normalized

    if (
        home_score is not None
        and away_score is not None
    ):
        return "FINISHED"

    return "SCHEDULED"
