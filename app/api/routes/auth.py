from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.connection import SessionLocal
from app.models.user_profile import UserProfile
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TimezoneUpdateRequest,
)
from app.services.authentication_service import (
    AuthenticationService,
)
from app.services.user_profile_service import (
    UserProfileService,
)
from app.utils.datetime_utils import (
    to_utc_iso,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


bearer_scheme = HTTPBearer(
    auto_error=False,
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def serialize_profile(
    profile: UserProfile,
) -> dict:

    return {
        "public_id": profile.public_id,
        "email": profile.email,
        "telegram_linked": (
            profile.telegram_user_id
            is not None
        ),
        "display_name": (
            profile.display_name
        ),
        "timezone": profile.timezone,
        "created_at": to_utc_iso(
            profile.created_at
        ),
        "updated_at": to_utc_iso(
            profile.updated_at
        ),
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials
    | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> UserProfile:

    if credentials is None:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Authentication required.",
        )

    try:

        payload = (
            AuthenticationService
            .decode_access_token(
                credentials.credentials
            )
        )

        public_id = payload.get(
            "sub"
        )

        if not public_id:
            raise InvalidTokenError()

    except InvalidTokenError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid or expired token.",
        ) from error

    profile = (
        UserProfileService(db)
        .get_by_public_id(
            public_id
        )
    )

    if profile is None:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="User account not found.",
        )

    return profile


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):

    service = AuthenticationService(db)

    try:

        profile = service.register(
            email=str(request.email),
            password=request.password,
            display_name=(
                request.display_name
            ),
            timezone_name=(
                request.timezone
            ),
        )

    except ValueError as error:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    token = service.create_access_token(
        profile
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_seconds": (
            settings
            .access_token_expire_minutes
            * 60
        ),
        "user": serialize_profile(
            profile
        ),
    }


@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):

    service = AuthenticationService(db)

    profile = service.authenticate(
        email=str(request.email),
        password=request.password,
    )

    if profile is None:

        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid email or password."
            ),
        )

    token = service.create_access_token(
        profile
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_seconds": (
            settings
            .access_token_expire_minutes
            * 60
        ),
        "user": serialize_profile(
            profile
        ),
    }


@router.get("/me")
def get_me(
    profile: UserProfile = Depends(
        get_current_user
    ),
):

    return {
        "user": serialize_profile(
            profile
        )
    }


@router.patch("/timezone")
def update_timezone(
    request: TimezoneUpdateRequest,
    profile: UserProfile = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    service = UserProfileService(db)

    try:

        service.update_timezone(
            profile,
            request.timezone,
        )

        db.commit()
        db.refresh(profile)

    except ValueError as error:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "user": serialize_profile(
            profile
        )
    }
