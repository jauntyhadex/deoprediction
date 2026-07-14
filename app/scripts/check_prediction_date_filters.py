from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def check_valid_date_filter(
    path: str,
) -> None:

    response = client.get(
        path,
        params={
            "limit": 3,
            "upcoming_only": False,
            "date_from": (
                "2020-01-01T00:00:00Z"
            ),
            "date_to": (
                "2030-01-01T00:00:00Z"
            ),
        },
    )

    assert (
        response.status_code == 200
    ), response.text

    filters = response.json()[
        "filters"
    ]

    assert (
        filters["date_from"]
        == "2020-01-01T00:00:00Z"
    )

    assert (
        filters["date_to"]
        == "2030-01-01T00:00:00Z"
    )

    print(
        f"DATE FILTER PASSED: {path}"
    )


def check_timezone_conversion() -> None:

    response = client.get(
        "/prediction-picks/top",
        params={
            "limit": 1,
            "upcoming_only": False,
            "date_from": (
                "2026-07-14T16:00:00+01:00"
            ),
            "date_to": (
                "2027-07-14T16:00:00+01:00"
            ),
        },
    )

    assert (
        response.status_code == 200
    ), response.text

    filters = response.json()[
        "filters"
    ]

    assert (
        filters["date_from"]
        == "2026-07-14T15:00:00Z"
    )

    assert (
        filters["date_to"]
        == "2027-07-14T15:00:00Z"
    )

    print(
        "TIMEZONE DATE CONVERSION PASSED"
    )


def check_invalid_range(
    path: str,
) -> None:

    response = client.get(
        path,
        params={
            "date_from": (
                "2030-01-01T00:00:00Z"
            ),
            "date_to": (
                "2020-01-01T00:00:00Z"
            ),
        },
    )

    assert (
        response.status_code == 400
    ), response.text

    print(
        f"INVALID RANGE PASSED: {path}"
    )


def main() -> None:

    print()
    print(
        "DEOPREDICTION DATE FILTER TEST"
    )
    print("=" * 60)

    paths = (
        "/prediction-picks/top",
        "/prediction-picks/markets/top",
    )

    for path in paths:
        check_valid_date_filter(path)
        check_invalid_range(path)

    check_timezone_conversion()

    print("=" * 60)
    print(
        "PREDICTION DATE FILTER TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
