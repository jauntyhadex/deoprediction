from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class RegisterRequest(BaseModel):

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    display_name: str | None = Field(
        default=None,
        max_length=150,
    )

    timezone: str | None = Field(
        default=None,
        max_length=64,
    )


class LoginRequest(BaseModel):

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class TimezoneUpdateRequest(BaseModel):

    timezone: str = Field(
        min_length=1,
        max_length=64,
    )
