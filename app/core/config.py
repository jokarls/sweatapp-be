from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/sweatcheck"

    # Strava
    STRAVA_CLIENT_ID: str = ""
    STRAVA_CLIENT_SECRET: str = ""
    STRAVA_WEBHOOK_VERIFY_TOKEN: str = "default_verify_token"
    STRAVA_REDIRECT_URI: str = "http://localhost:8000/api/v1/strava/callback"

    # OpenWeatherMap
    OPENWEATHERMAP_API_KEY: str = ""

settings = Settings()
