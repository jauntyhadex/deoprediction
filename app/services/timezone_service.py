from datetime import UTC, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo, available_timezones

from app.config.settings import settings


class TimezoneService:

    DEFAULT_TIMEZONE = settings.default_timezone

    EXCLUDED_PREFIXES = (
        "Etc/",
        "posix/",
        "right/",
        "SystemV/",
    )

    EXCLUDED_NAMES = {
        "Factory",
        "localtime",
    }

    @classmethod
    @lru_cache(maxsize=1)
    def supported_timezones(
        cls,
    ) -> tuple[str, ...]:

        zones = {
            timezone_name
            for timezone_name
            in available_timezones()
            if (
                timezone_name
                not in cls.EXCLUDED_NAMES
                and not timezone_name.startswith(
                    cls.EXCLUDED_PREFIXES
                )
            )
        }

        zones.add(
            cls.DEFAULT_TIMEZONE
        )

        return tuple(
            sorted(zones)
        )

    @classmethod
    def validate(
        cls,
        timezone_name: str | None,
    ) -> str:

        normalized_name = (
            timezone_name
            or cls.DEFAULT_TIMEZONE
        ).strip()

        if (
            normalized_name
            not in cls.supported_timezones()
        ):
            raise ValueError(
                "Unsupported timezone: "
                f"{normalized_name}"
            )

        return normalized_name

    @classmethod
    def search(
        cls,
        search_text: str | None = None,
        limit: int = 100,
    ) -> list[str]:

        timezones = (
            cls.supported_timezones()
        )

        if search_text:

            normalized_search = (
                search_text
                .strip()
                .lower()
            )

            timezones = tuple(
                timezone_name
                for timezone_name in timezones
                if normalized_search
                in timezone_name.lower()
            )

        return list(
            timezones[:limit]
        )

    @classmethod
    def convert_from_utc(
        cls,
        value: datetime,
        timezone_name: str | None = None,
    ) -> dict:

        validated_timezone = (
            cls.validate(
                timezone_name
            )
        )

        if value.tzinfo is None:

            utc_value = value.replace(
                tzinfo=UTC
            )

        else:

            utc_value = value.astimezone(
                UTC
            )

        local_value = (
            utc_value.astimezone(
                ZoneInfo(
                    validated_timezone
                )
            )
        )

        return {
            "timezone": (
                validated_timezone
            ),
            "utc_time": (
                utc_value
                .isoformat()
                .replace(
                    "+00:00",
                    "Z",
                )
            ),
            "local_time": (
                local_value.isoformat()
            ),
        }
