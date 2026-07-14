from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.user_profile import UserProfile
from app.services.user_profile_service import (
    UserProfileService,
)


class AuthenticationService:

    password_hasher = (
        PasswordHash.recommended()
    )

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db
        self.profile_service = (
            UserProfileService(db)
        )

    def register(
        self,
        email: str,
        password: str,
        display_name: str | None = None,
        timezone_name: str | None = None,
    ) -> UserProfile:

        normalized_email = (
            email.strip().lower()
        )

        if (
            self.profile_service
            .get_by_email(
                normalized_email
            )
            is not None
        ):
            raise ValueError(
                "An account with this email already exists."
            )

        password_hash = (
            self.password_hasher.hash(
                password
            )
        )

        profile = (
            self.profile_service.create(
                email=normalized_email,
                password_hash=password_hash,
                display_name=display_name,
                timezone_name=timezone_name,
            )
        )

        self.db.commit()
        self.db.refresh(profile)

        return profile

    def authenticate(
        self,
        email: str,
        password: str,
    ) -> UserProfile | None:

        profile = (
            self.profile_service
            .get_by_email(email)
        )

        if (
            profile is None
            or profile.password_hash is None
        ):
            return None

        password_is_valid = (
            self.password_hasher.verify(
                password,
                profile.password_hash,
            )
        )

        if not password_is_valid:
            return None

        return profile

    @staticmethod
    def create_access_token(
        profile: UserProfile,
    ) -> str:

        now = datetime.now(UTC)

        expires_at = (
            now
            + timedelta(
                minutes=(
                    settings
                    .access_token_expire_minutes
                )
            )
        )

        payload = {
            "sub": profile.public_id,
            "iat": now,
            "exp": expires_at,
            "type": "access",
        }

        return jwt.encode(
            payload,
            settings.auth_secret_key,
            algorithm=settings.auth_algorithm,
        )

    @staticmethod
    def decode_access_token(
        token: str,
    ) -> dict:

        return jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[
                settings.auth_algorithm
            ],
        )
