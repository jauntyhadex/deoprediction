from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def main() -> None:

    print()
    print(
        "DEOPREDICTION FIXTURE API TEST"
    )
    print("=" * 60)

    list_response = client.get(
        "/fixtures",
        params={
            "limit": 5,
            "upcoming_only": False,
        },
    )

    assert (
        list_response.status_code == 200
    ), list_response.text

    list_data = list_response.json()

    fixtures = list_data.get(
        "fixtures",
        [],
    )

    assert fixtures

    first_fixture = fixtures[0]

    assert {
        "id",
        "competition",
        "home_team",
        "away_team",
        "status",
        "kickoff_time",
        "score",
    }.issubset(first_fixture)

    assert first_fixture[
        "kickoff_time"
    ].endswith("Z")

    print("FIXTURE LIST PASSED")

    detail_response = client.get(
        f"/fixtures/{first_fixture['id']}"
    )

    assert (
        detail_response.status_code == 200
    ), detail_response.text

    assert (
        detail_response.json()[
            "fixture"
        ]["id"]
        == first_fixture["id"]
    )

    print("FIXTURE DETAIL PASSED")

    search_response = client.get(
        "/fixtures",
        params={
            "limit": 5,
            "upcoming_only": False,
            "search": (
                first_fixture[
                    "home_team"
                ]["name"]
            ),
        },
    )

    assert (
        search_response.status_code == 200
    ), search_response.text

    assert search_response.json()[
        "fixtures"
    ]

    print("FIXTURE SEARCH PASSED")

    status_response = client.get(
        "/fixtures",
        params={
            "limit": 5,
            "upcoming_only": False,
            "status": (
                first_fixture["status"]
            ),
        },
    )

    assert (
        status_response.status_code == 200
    ), status_response.text

    print("FIXTURE STATUS FILTER PASSED")

    timezone_response = client.get(
        "/fixtures",
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
        timezone_response.status_code == 200
    ), timezone_response.text

    filters = timezone_response.json()[
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
        "FIXTURE TIMEZONE FILTER PASSED"
    )

    invalid_status_response = client.get(
        "/fixtures",
        params={
            "status": "INVALID",
        },
    )

    assert (
        invalid_status_response.status_code
        == 400
    ), invalid_status_response.text

    print(
        "FIXTURE STATUS VALIDATION PASSED"
    )

    invalid_range_response = client.get(
        "/fixtures",
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
        invalid_range_response.status_code
        == 400
    ), invalid_range_response.text

    print(
        "FIXTURE DATE VALIDATION PASSED"
    )

    print("=" * 60)
    print(
        "FIXTURE API TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
