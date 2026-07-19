from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "DeoPrediction"
    app_version: str = "0.1.0"
    environment: str = "development"
    default_timezone: str = "Africa/Lagos"
    cors_allowed_origins: str = "*"

    # Authentication
    auth_secret_key: str
    auth_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Database
    database_url: str
    database_echo: bool = False

    # Football Data API
    football_data_base_url: str
    football_data_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
