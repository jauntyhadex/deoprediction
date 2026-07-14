from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import model_loader
from app.database.connection import SessionLocal
from app.main import app
from app.models.user_profile import UserProfile


client = TestClient(app)


def main() -> None:

    email = (
        f"auth-test-{uuid4().hex}"
        "@example.com"
    )

    password = (
        "SecureTestPassword123!"
    )

    try:

        register_response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "display_name": "Auth Test",
            },
        )

        assert (
            register_response.status_code
            == 201
        ), register_response.text

        register_data = (
            register_response.json()
        )

        assert (
            register_data["user"][
                "timezone"
            ]
            == "Africa/Lagos"
        )

        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert (
            login_response.status_code
            == 200
        ), login_response.text

        token = login_response.json()[
            "access_token"
        ]

        headers = {
            "Authorization": (
                f"Bearer {token}"
            )
        }

        me_response = client.get(
            "/auth/me",
            headers=headers,
        )

        assert (
            me_response.status_code
            == 200
        ), me_response.text

        timezone_response = client.patch(
            "/auth/timezone",
            headers=headers,
            json={
                "timezone": (
                    "America/New_York"
                )
            },
        )

        assert (
            timezone_response.status_code
            == 200
        ), timezone_response.text

        assert (
            timezone_response.json()[
                "user"
            ]["timezone"]
            == "America/New_York"
        )

        print(
            "AUTHENTICATION TEST PASSED"
        )

    finally:

        db = SessionLocal()

        try:

            db.query(UserProfile).filter(
                UserProfile.email == email
            ).delete(
                synchronize_session=False
            )

            db.commit()

        finally:

            db.close()


if __name__ == "__main__":
    main()
