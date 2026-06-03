from datetime import UTC, datetime
from uuid import UUID

from app.core.config import settings
from app.domain.interfaces import IStravaClient, ITokenRepository, IUserRepository
from app.domain.models import StravaToken, User


class StravaAuthService:
    def __init__(
        self,
        token_repo: ITokenRepository,
        strava_client: IStravaClient,
        user_repo: IUserRepository | None = None,
    ):
        self.token_repo = token_repo
        self.strava_client = strava_client
        self.user_repo = user_repo

    async def get_valid_access_token(self, user_id: UUID) -> str:
        token = await self.token_repo.get_by_user_id(user_id)
        if not token:
            raise ValueError(f"No Strava token found for user {user_id}")

        if token.is_expired:
            token = await self._refresh_token(token)

        return token.access_token

    async def _refresh_token(self, token: StravaToken) -> StravaToken:
        refresh_response = await self.strava_client.refresh_token(
            client_id=settings.STRAVA_CLIENT_ID,
            client_secret=settings.STRAVA_CLIENT_SECRET,
            refresh_token=token.refresh_token,
        )

        token.access_token = refresh_response["access_token"]
        token.refresh_token = refresh_response["refresh_token"]
        # expires_at is usually provided as 'expires_at' (timestamp)
        token.expires_at = datetime.fromtimestamp(refresh_response["expires_at"], tz=UTC)

        await self.token_repo.save(token)
        return token

    async def login_or_register(self, code: str) -> User:
        if not self.user_repo:
            raise ValueError("user_repo is required to use login_or_register")
        # 1. Exchange auth code for tokens and athlete info
        exchange_response = await self.strava_client.exchange_authorization_code(
            client_id=settings.STRAVA_CLIENT_ID,
            client_secret=settings.STRAVA_CLIENT_SECRET,
            code=code,
        )

        strava_athlete_id = exchange_response["athlete"]["id"]
        access_token = exchange_response["access_token"]
        refresh_token = exchange_response["refresh_token"]
        expires_at = datetime.fromtimestamp(exchange_response["expires_at"], tz=UTC)

        # 2. Check if user already exists
        user = await self.user_repo.get_by_strava_athlete_id(strava_athlete_id)
        if not user:
            # Create a new user (Registration)
            user = User(strava_athlete_id=strava_athlete_id)
            await self.user_repo.save(user)

        # 3. Save or update Strava tokens
        token = await self.token_repo.get_by_user_id(user.id)
        if token:
            token.access_token = access_token
            token.refresh_token = refresh_token
            token.expires_at = expires_at
        else:
            token = StravaToken(
                user_id=user.id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )

        await self.token_repo.save(token)
        return user

