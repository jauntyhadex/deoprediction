from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def main() -> None:

    print()
    print(
        "DEOPREDICTION TEAM API TEST"
    )
    print("=" * 60)

    list_response = client.get(
        "/teams",
        params={
            "limit": 10,
        },
    )

    assert (
        list_response.status_code == 200
    ), list_response.text

    list_data = list_response.json()

    teams = list_data.get(
        "teams",
        [],
    )

    assert teams

    first_team = teams[0]

    required_fields = {
        "id",
        "external_id",
        "name",
        "short_name",
        "country",
        "competition",
        "created_at",
    }

    assert required_fields.issubset(
        first_team
    )

    assert first_team[
        "created_at"
    ].endswith("Z")

    print("TEAM LIST PASSED")

    detail_response = client.get(
        f"/teams/{first_team['id']}"
    )

    assert (
        detail_response.status_code == 200
    ), detail_response.text

    assert (
        detail_response.json()[
            "team"
        ]["id"]
        == first_team["id"]
    )

    print("TEAM DETAIL PASSED")

    search_response = client.get(
        "/teams",
        params={
            "search": first_team["name"],
            "limit": 10,
        },
    )

    assert (
        search_response.status_code == 200
    ), search_response.text

    assert search_response.json()[
        "teams"
    ]

    print("TEAM SEARCH PASSED")

    competition_response = client.get(
        "/teams",
        params={
            "competition_id": (
                first_team[
                    "competition"
                ]["id"]
            ),
            "limit": 10,
        },
    )

    assert (
        competition_response.status_code
        == 200
    ), competition_response.text

    competition_teams = (
        competition_response.json()[
            "teams"
        ]
    )

    assert competition_teams

    assert all(
        team["competition"]["id"]
        == first_team[
            "competition"
        ]["id"]
        for team in competition_teams
    )

    print(
        "TEAM COMPETITION FILTER PASSED"
    )

    country_response = client.get(
        "/teams",
        params={
            "country": (
                first_team["country"]
            ),
            "limit": 10,
        },
    )

    assert (
        country_response.status_code
        == 200
    ), country_response.text

    assert country_response.json()[
        "teams"
    ]

    print("TEAM COUNTRY FILTER PASSED")

    missing_response = client.get(
        "/teams/999999999"
    )

    assert (
        missing_response.status_code
        == 404
    ), missing_response.text

    print(
        "TEAM NOT-FOUND VALIDATION PASSED"
    )

    public_response = client.get(
        "/teams",
        params={
            "limit": 1,
        },
    )

    assert (
        public_response.status_code
        == 200
    ), public_response.text

    print(
        "PUBLIC TEAM ACCESS PASSED"
    )

    print("=" * 60)
    print(
        "TEAM API TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
