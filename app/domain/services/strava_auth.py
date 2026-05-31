from datetime import UTC, datetime
from uuid import UUID

from app.core.config import settings
from app.domain.interfaces import IStravaClient, ITokenRepository
from app.domain.models import StravaToken


class StravaAuthService:
    def __init__(self, token_repo: ITokenRepository, strava_client: IStravaClient):
        self.token_repo = token_repo
        self.strava_client = strava_client

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
