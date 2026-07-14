from datetime import UTC, datetime


def to_utc_iso(
    value: datetime | None,
) -> str | None:

    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(
            tzinfo=UTC
        )
    else:
        value = value.astimezone(
            UTC
        )

    return value.isoformat().replace(
        "+00:00",
        "Z",
    )
