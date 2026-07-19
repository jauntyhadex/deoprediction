from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def main() -> None:

    print()
    print(
        "DEOPREDICTION CORS TEST"
    )
    print("=" * 60)

    origin = "http://localhost:3000"

    preflight_response = client.options(
        "/discovery/home",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": (
                "Authorization, Content-Type"
            ),
        },
    )

    assert (
        preflight_response.status_code
        == 200
    ), preflight_response.text

    allow_origin = (
        preflight_response.headers.get(
            "access-control-allow-origin"
        )
    )

    assert allow_origin in (
        "*",
        origin,
    ), dict(preflight_response.headers)

    print(
        "CORS PREFLIGHT PASSED"
    )

    get_response = client.get(
        "/discovery/home",
        headers={
            "Origin": origin,
        },
    )

    assert (
        get_response.status_code == 200
    ), get_response.text

    allow_origin = (
        get_response.headers.get(
            "access-control-allow-origin"
        )
    )

    assert allow_origin in (
        "*",
        origin,
    ), dict(get_response.headers)

    print(
        "CORS GET PASSED"
    )

    print("=" * 60)
    print(
        "CORS TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
