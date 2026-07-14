from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import model_loader
from app.database.connection import SessionLocal
from app.main import app
from app.services.user_profile_service import (
    UserProfileService,
)


client = TestClient(app)


PUBLIC_ENDPOINTS = (
    "/",
    "/health",
    "/system/status",
    "/fixtures?limit=1&upcoming_only=false",
    "/prediction-picks/top?limit=1",
    "/prediction-picks/markets/top?limit=1",
    "/timezones?search=Lagos&limit=5",
    (
        "/timezones/convert"
        "?timestamp=2026-07-14T15%3A00%3A00Z"
        "&timezone=Africa%2FLagos"
    ),
)


def check_public_endpoints() -> None:

    for path in PUBLIC_ENDPOINTS:

        response = client.get(path)

        assert (
            response.status_code == 200
        ), (
            f"Public endpoint failed: "
            f"{path} "
            f"({response.status_code}) "
            f"{response.text}"
        )

        print(
            f"PUBLIC ACCESS PASSED: {path}"
        )


def check_telegram_guest_profile() -> None:

    telegram_user_id = (
        9_000_000_000_000
        + uuid4().int % 1_000_000_000
    )

    db = SessionLocal()

    try:

        service = UserProfileService(db)

        profile = (
            service.get_or_create_telegram_user(
                telegram_user_id=(
                    telegram_user_id
                ),
                display_name="Guest User",
            )
        )

        assert profile.email is None
        assert profile.password_hash is None

        assert (
            profile.timezone
            == "Africa/Lagos"
        )

        service.update_timezone(
            profile,
            "America/New_York",
        )

        assert (
            profile.timezone
            == "America/New_York"
        )

        print(
            "TELEGRAM GUEST PROFILE PASSED"
        )

    finally:

        db.rollback()
        db.close()


def main() -> None:

    print()
    print(
        "DEOPREDICTION PUBLIC ACCESS TEST"
    )
    print("=" * 60)

    check_public_endpoints()
    check_telegram_guest_profile()

    print("=" * 60)
    print(
        "PUBLIC GUEST ACCESS TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
