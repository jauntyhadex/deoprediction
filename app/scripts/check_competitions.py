from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def main() -> None:

    print()
    print(
        "DEOPREDICTION COMPETITION API TEST"
    )
    print("=" * 60)

    list_response = client.get(
        "/competitions",
        params={
            "limit": 10,
        },
    )

    assert (
        list_response.status_code
        == 200
    ), list_response.text

    list_data = list_response.json()

    competitions = list_data.get(
        "competitions",
        [],
    )

    assert competitions

    first_competition = (
        competitions[0]
    )

    required_fields = {
        "id",
        "external_id",
        "code",
        "name",
        "country",
        "type",
        "season",
        "sport",
        "reliability",
    }

    assert required_fields.issubset(
        first_competition
    )

    print(
        "COMPETITION LIST PASSED"
    )

    search_response = client.get(
        "/competitions",
        params={
            "search": (
                first_competition[
                    "name"
                ]
            ),
            "limit": 10,
        },
    )

    assert (
        search_response.status_code
        == 200
    ), search_response.text

    assert (
        search_response.json()[
            "competitions"
        ]
    )

    print(
        "COMPETITION SEARCH PASSED"
    )

    detail_response = client.get(
        (
            "/competitions/"
            f"{first_competition['id']}"
        )
    )

    assert (
        detail_response.status_code
        == 200
    ), detail_response.text

    assert (
        detail_response.json()[
            "competition"
        ]["id"]
        == first_competition["id"]
    )

    print(
        "COMPETITION DETAIL PASSED"
    )

    invalid_response = client.get(
        "/competitions",
        params={
            "reliability_status": (
                "INVALID"
            ),
        },
    )

    assert (
        invalid_response.status_code
        == 400
    ), invalid_response.text

    print(
        "COMPETITION STATUS VALIDATION PASSED"
    )

    public_response = client.get(
        "/competitions",
    )

    assert (
        public_response.status_code
        == 200
    ), public_response.text

    print(
        "PUBLIC COMPETITION ACCESS PASSED"
    )

    print("=" * 60)
    print(
        "COMPETITION API TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
