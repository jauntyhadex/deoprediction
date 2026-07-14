from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile
from app.services.timezone_service import (
    TimezoneService,
)


class UserProfileService:

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db

    def get_by_public_id(
        self,
        public_id: str,
    ) -> UserProfile | None:

        return (
            self.db.query(UserProfile)
            .filter(
                UserProfile.public_id
                == public_id
            )
            .first()
        )

    def get_by_email(
        self,
        email: str,
    ) -> UserProfile | None:

        normalized_email = (
            email.strip().lower()
        )

        return (
            self.db.query(UserProfile)
            .filter(
                UserProfile.email
                == normalized_email
            )
            .first()
        )

    def get_by_telegram_user_id(
        self,
        telegram_user_id: int,
    ) -> UserProfile | None:

        return (
            self.db.query(UserProfile)
            .filter(
                UserProfile.telegram_user_id
                == telegram_user_id
            )
            .first()
        )

    def create(
        self,
        email: str | None = None,
        password_hash: str | None = None,
        telegram_user_id: int | None = None,
        display_name: str | None = None,
        timezone_name: str | None = None,
    ) -> UserProfile:

        normalized_email = (
            email.strip().lower()
            if email
            else None
        )

        validated_timezone = (
            TimezoneService.validate(
                timezone_name
            )
        )

        profile = UserProfile(
            email=normalized_email,
            password_hash=password_hash,
            telegram_user_id=(
                telegram_user_id
            ),
            display_name=display_name,
            timezone=validated_timezone,
        )

        self.db.add(profile)
        self.db.flush()

        return profile

    def get_or_create_telegram_user(
        self,
        telegram_user_id: int,
        display_name: str | None = None,
    ) -> UserProfile:

        existing = (
            self.get_by_telegram_user_id(
                telegram_user_id
            )
        )

        if existing is not None:
            return existing

        return self.create(
            telegram_user_id=(
                telegram_user_id
            ),
            display_name=display_name,
        )

    def update_timezone(
        self,
        profile: UserProfile,
        timezone_name: str,
    ) -> UserProfile:

        profile.timezone = (
            TimezoneService.validate(
                timezone_name
            )
        )

        self.db.flush()

        return profile

    def link_telegram_account(
        self,
        profile: UserProfile,
        telegram_user_id: int,
    ) -> UserProfile:

        profile.telegram_user_id = (
            telegram_user_id
        )

        self.db.flush()

        return profile
