from typing import Any
from uuid import UUID

from asyncpg import Pool

from app.domain.interfaces import IUserRepository
from app.domain.models import User


class PostgresUserRepository(IUserRepository):
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_by_id(self, user_id: UUID) -> User | None:
        query = 'SELECT * FROM "user" WHERE id = $1'
        row = await self.pool.fetchrow(query, user_id)
        return self._map_row_to_user(row) if row else None

    async def get_by_strava_athlete_id(self, strava_id: int) -> User | None:
        query = 'SELECT * FROM "user" WHERE strava_athlete_id = $1'
        row = await self.pool.fetchrow(query, strava_id)
        return self._map_row_to_user(row) if row else None

    async def save(self, user: User) -> None:
        query = """
            INSERT INTO "user" (
                id, strava_athlete_id, last_known_weight, weight_unit, fluid_unit, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE SET
                last_known_weight = EXCLUDED.last_known_weight,
                weight_unit = EXCLUDED.weight_unit,
                fluid_unit = EXCLUDED.fluid_unit
        """
        await self.pool.execute(
            query,
            user.id,
            user.strava_athlete_id,
            user.last_known_weight,
            user.weight_unit,
            user.fluid_unit,
            user.created_at,
        )

    def _map_row_to_user(self, row: Any) -> User:
        return User(
            id=row["id"],
            strava_athlete_id=row["strava_athlete_id"],
            last_known_weight=row["last_known_weight"],
            weight_unit=row["weight_unit"],
            fluid_unit=row["fluid_unit"],
            created_at=row["created_at"],
        )
