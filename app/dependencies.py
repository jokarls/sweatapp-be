from asyncpg import Pool
from fastapi import Request

from app.core.config import settings
from app.domain.services.activity_sync import ActivitySyncService
from app.domain.services.strava_auth import StravaAuthService
from app.infrastructure.db.repository import PostgresActivityRepository
from app.infrastructure.db.token_repository import PostgresTokenRepository
from app.infrastructure.db.user_repository import PostgresUserRepository
from app.infrastructure.strava.client import StravaClient
from app.infrastructure.weather.provider import OpenWeatherMapProvider


def get_pool(request: Request) -> Pool:
    return request.app.state.pool


def get_activity_repo(request: Request) -> PostgresActivityRepository:
    return PostgresActivityRepository(request.app.state.pool)


def get_user_repo(request: Request) -> PostgresUserRepository:
    return PostgresUserRepository(request.app.state.pool)


def get_token_repo(request: Request) -> PostgresTokenRepository:
    return PostgresTokenRepository(request.app.state.pool)


def get_strava_client() -> StravaClient:
    return StravaClient()


def get_weather_provider() -> OpenWeatherMapProvider:
    return OpenWeatherMapProvider(api_key=settings.OPENWEATHERMAP_API_KEY)


def get_strava_auth_service(request: Request) -> StravaAuthService:
    token_repo = get_token_repo(request)
    strava_client = get_strava_client()
    return StravaAuthService(token_repo, strava_client)


def get_activity_sync_service(request: Request) -> ActivitySyncService:
    activity_repo = get_activity_repo(request)
    user_repo = get_user_repo(request)
    strava_auth = get_strava_auth_service(request)
    strava_client = get_strava_client()
    weather_provider = get_weather_provider()

    return ActivitySyncService(
        activity_repo, user_repo, strava_auth, strava_client, weather_provider
    )
