from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def main() -> None:

    print()
    print(
        "DEOPREDICTION DISCOVERY API TEST"
    )
    print("=" * 60)

    response = client.get(
        "/discovery/home",
        params={
            "timezone": "Africa/Lagos",
            "days_ahead": 30,
            "fixture_limit": 3,
            "pick_limit": 3,
            "market_limit": 3,
        },
    )

    assert (
        response.status_code == 200
    ), response.text

    data = response.json()

    assert (
        data["timezone"]
        == "Africa/Lagos"
    )

    assert data["counts"]["fixtures"] > 0
    assert data["counts"]["predictions"] > 0
    assert data["counts"]["markets"] > 0
    assert data["counts"]["picks"] > 0

    assert "upcoming_fixtures" in data
    assert "top_picks" in data
    assert "top_markets" in data
    assert "market_catalog" in data

    assert (
        data["timestamps"]["storage"]
        == "UTC"
    )

    print(
        "DISCOVERY HOME PASSED"
    )

    invalid_response = client.get(
        "/discovery/home",
        params={
            "timezone": "Invalid/Zone",
        },
    )

    assert (
        invalid_response.status_code
        == 400
    ), invalid_response.text

    print(
        "DISCOVERY TIMEZONE VALIDATION PASSED"
    )

    public_response = client.get(
        "/discovery/home"
    )

    assert (
        public_response.status_code
        == 200
    ), public_response.text

    print(
        "PUBLIC DISCOVERY ACCESS PASSED"
    )

    print("=" * 60)
    print(
        "DISCOVERY API TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
