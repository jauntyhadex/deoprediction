import sys
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def check_endpoint(
    name: str,
    path: str,
) -> dict[str, Any]:

    response = client.get(path)

    if response.status_code != 200:

        print(
            f"FAILED: {name}"
        )

        print(
            f"Path: {path}"
        )

        print(
            f"Status code: "
            f"{response.status_code}"
        )

        print(
            f"Response: "
            f"{response.text}"
        )

        raise SystemExit(1)

    data = response.json()

    print(
        f"PASSED: {name} "
        f"({response.status_code})"
    )

    return data


def main() -> None:

    print()
    print(
        "DEOPREDICTION API SMOKE TEST"
    )

    print("=" * 60)

    root_data = check_endpoint(
        name="Root endpoint",
        path="/",
    )

    if (
        root_data.get("message")
        != "DeoPrediction API is running"
    ):

        print(
            "FAILED: Unexpected root response"
        )

        raise SystemExit(1)

    health_data = check_endpoint(
        name="Health endpoint",
        path="/health",
    )

    if (
        health_data.get("status")
        != "healthy"
    ):

        print(
            "FAILED: API health is not healthy"
        )

        raise SystemExit(1)

    status_data = check_endpoint(
        name="System status endpoint",
        path="/system/status",
    )

    if (
        status_data.get("database")
        != "connected"
    ):

        print(
            "FAILED: Database is not connected"
        )

        raise SystemExit(1)

    utc_timestamp_fields = (
        "latest_fixture_updated_at",
        "latest_fixture_kickoff_time",
    )

    for field_name in utc_timestamp_fields:

        timestamp = status_data.get(
            field_name
        )

        if (
            timestamp is not None
            and not timestamp.endswith("Z")
        ):

            print(
                "FAILED: Timestamp is not "
                f"explicit UTC: {field_name}"
            )

            raise SystemExit(1)

    counts = status_data.get(
        "counts",
        {},
    )

    required_counts = (
        "fixtures",
        "predictions",
        "markets",
        "picks",
    )

    for count_name in required_counts:

        count_value = counts.get(
            count_name
        )

        if (
            not isinstance(
                count_value,
                int,
            )
            or count_value < 0
        ):

            print(
                "FAILED: Invalid system count "
                f"for {count_name}"
            )

            raise SystemExit(1)

    picks_data = check_endpoint(
        name="Top prediction picks",
        path=(
            "/prediction-picks/top"
            "?limit=3"
        ),
    )

    markets_data = check_endpoint(
        name="Top prediction markets",
        path=(
            "/prediction-picks/markets/top"
            "?limit=3"
        ),
    )


    timezone_data = check_endpoint(
        name="Timezone list endpoint",
        path=(
            "/timezones"
            "?search=Lagos"
            "&limit=10"
        ),
    )

    if (
        "Africa/Lagos"
        not in timezone_data.get(
            "timezones",
            [],
        )
    ):

        print(
            "FAILED: Africa/Lagos "
            "timezone was not returned"
        )

        raise SystemExit(1)

    conversion_data = check_endpoint(
        name="Timezone conversion endpoint",
        path=(
            "/timezones/convert"
            "?timestamp="
            "2026-07-14T15%3A00%3A00Z"
            "&timezone=Africa%2FLagos"
        ),
    )

    if (
        conversion_data.get("timezone")
        != "Africa/Lagos"
        or not conversion_data.get(
            "local_time",
            "",
        ).endswith("+01:00")
    ):

        print(
            "FAILED: Lagos timezone "
            "conversion is incorrect"
        )

        raise SystemExit(1)

    print()
    print(
        "DATABASE COUNTS"
    )

    print("-" * 60)

    for count_name in required_counts:

        print(
            f"{count_name.capitalize()}: "
            f"{counts[count_name]}"
        )

    print()
    print(
        "API RESULTS"
    )

    print("-" * 60)

    print(
        "Top picks returned: "
        f"{picks_data.get('count', 0)}"
    )

    print(
        "Top markets returned: "
        f"{markets_data.get('count', 0)}"
    )

    print()
    print("=" * 60)
    print(
        "API SMOKE TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":

    try:
        main()

    except Exception as error:

        print()
        print(
            "API SMOKE TEST FAILED"
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        sys.exit(1)