from uuid import UUID

from asyncpg import Pool
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.domain.interfaces import IWeatherProvider
from app.domain.models import User
from app.domain.services.activity_sync import ActivitySyncService
from app.domain.services.strava_auth import StravaAuthService
from app.infrastructure.db.repository import PostgresActivityRepository
from app.infrastructure.db.token_repository import PostgresTokenRepository
from app.infrastructure.db.user_repository import PostgresUserRepository
from app.infrastructure.strava.client import StravaClient
from app.infrastructure.weather.provider import OpenMeteoProvider

oauth2_scheme = HTTPBearer()


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


def get_weather_provider() -> IWeatherProvider:
    return OpenMeteoProvider()


def get_strava_auth_service(
    token_repo: PostgresTokenRepository = Depends(get_token_repo),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
    strava_client: StravaClient = Depends(get_strava_client),
) -> StravaAuthService:
    return StravaAuthService(token_repo, strava_client, user_repo)


def get_activity_sync_service(
    activity_repo: PostgresActivityRepository = Depends(get_activity_repo),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
    strava_auth: StravaAuthService = Depends(get_strava_auth_service),
    strava_client: StravaClient = Depends(get_strava_client),
    weather_provider: IWeatherProvider = Depends(get_weather_provider),
) -> ActivitySyncService:
    return ActivitySyncService(activity_repo, user_repo, strava_auth, strava_client, weather_provider)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identification",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identification format",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
