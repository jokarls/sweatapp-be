from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/sweatcheck"

    # Strava
    STRAVA_CLIENT_ID: str = ""
    STRAVA_CLIENT_SECRET: str = ""
    STRAVA_WEBHOOK_VERIFY_TOKEN: str = "default_verify_token"

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-fallback-secret-for-testing-only"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    @model_validator(mode="after")
    def validate_required_config(self) -> Self:
        required_fields = {
            "DATABASE_URL": self.DATABASE_URL,
            "STRAVA_CLIENT_ID": self.STRAVA_CLIENT_ID,
            "STRAVA_CLIENT_SECRET": self.STRAVA_CLIENT_SECRET,
            "STRAVA_WEBHOOK_VERIFY_TOKEN": self.STRAVA_WEBHOOK_VERIFY_TOKEN,
            "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
        }

        missing_fields = [field for field, val in required_fields.items() if not val or not str(val).strip()]
        if missing_fields:
            raise ValueError(
                f"Missing required configuration values at startup: {', '.join(missing_fields)}. "
                "Please configure them as non-empty strings in your environment or .env file."
            )
        return self


settings = Settings()
