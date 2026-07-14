from datetime import datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from app.services.timezone_service import (
    TimezoneService,
)


router = APIRouter(
    prefix="/timezones",
    tags=["Timezones"],
)


@router.get("")
def get_timezones(
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
):

    timezones = TimezoneService.search(
        search_text=search,
        limit=limit,
    )

    return {
        "default_timezone": (
            TimezoneService
            .DEFAULT_TIMEZONE
        ),
        "count": len(timezones),
        "timezones": timezones,
    }


@router.get("/convert")
def convert_timezone(
    timestamp: datetime = Query(),
    timezone_name: str | None = Query(
        default=None,
        alias="timezone",
    ),
):

    try:

        return (
            TimezoneService
            .convert_from_utc(
                value=timestamp,
                timezone_name=(
                    timezone_name
                ),
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail={
                "message": str(error),
                "default_timezone": (
                    TimezoneService
                    .DEFAULT_TIMEZONE
                ),
            },
        ) from error
