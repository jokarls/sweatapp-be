from typing import Any
from uuid import UUID

from asyncpg import Pool

from app.domain.interfaces import ITokenRepository
from app.domain.models import StravaToken


class PostgresTokenRepository(ITokenRepository):
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_by_user_id(self, user_id: UUID) -> StravaToken | None:
        query = "SELECT * FROM strava_token WHERE user_id = $1"
        row = await self.pool.fetchrow(query, user_id)
        return self._map_row_to_token(row) if row else None

    async def save(self, token: StravaToken) -> None:
        query = """
            INSERT INTO strava_token (
                id, user_id, access_token, refresh_token, expires_at, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                expires_at = EXCLUDED.expires_at
        """
        await self.pool.execute(
            query,
            token.id,
            token.user_id,
            token.access_token,
            token.refresh_token,
            token.expires_at,
            token.created_at,
        )

    def _map_row_to_token(self, row: Any) -> StravaToken:
        return StravaToken(
            id=row["id"],
            user_id=row["user_id"],
            access_token=row["access_token"],
            refresh_token=row["refresh_token"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
        )
