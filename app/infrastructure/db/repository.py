from typing import Any
from uuid import UUID

from asyncpg import Pool

from app.domain.interfaces import IActivityRepository
from app.domain.models import Activity, ActivityStatus


class PostgresActivityRepository(IActivityRepository):
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_by_id(self, activity_id: UUID) -> Activity | None:
        query = "SELECT * FROM activity WHERE id = $1"
        row = await self.pool.fetchrow(query, activity_id)
        return self._map_row_to_activity(row) if row else None

    async def get_by_strava_id(self, strava_id: int) -> Activity | None:
        query = "SELECT * FROM activity WHERE strava_id = $1"
        row = await self.pool.fetchrow(query, strava_id)
        return self._map_row_to_activity(row) if row else None

    async def list_by_user(self, user_id: UUID, limit: int = 20) -> list[Activity]:
        query = "SELECT * FROM activity WHERE user_id = $1 ORDER BY start_date DESC LIMIT $2"
        rows = await self.pool.fetch(query, user_id, limit)
        return [self._map_row_to_activity(row) for row in rows]

    async def save(self, activity: Activity) -> None:
        query = """
            INSERT INTO activity (
                id, user_id, strava_id, status, is_indoor, ignore_for_profile,
                activity_type, start_date, duration_seconds, avg_heartrate, relative_effort,
                temp_celsius_api, humidity_api,
                weight_before_user, weight_after_user, fluid_intake_ml_user,
                bathroom_visits_user, clothing_index_user,
                temp_celsius_user, humidity_user,
                total_sweat_loss_ml, sweat_rate_ml_per_hour, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                $21, $22, $23
            )
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                is_indoor = EXCLUDED.is_indoor,
                ignore_for_profile = EXCLUDED.ignore_for_profile,
                weight_before_user = EXCLUDED.weight_before_user,
                weight_after_user = EXCLUDED.weight_after_user,
                fluid_intake_ml_user = EXCLUDED.fluid_intake_ml_user,
                bathroom_visits_user = EXCLUDED.bathroom_visits_user,
                clothing_index_user = EXCLUDED.clothing_index_user,
                temp_celsius_user = EXCLUDED.temp_celsius_user,
                humidity_user = EXCLUDED.humidity_user,
                total_sweat_loss_ml = EXCLUDED.total_sweat_loss_ml,
                sweat_rate_ml_per_hour = EXCLUDED.sweat_rate_ml_per_hour
        """
        await self.pool.execute(
            query,
            activity.id,
            activity.user_id,
            activity.strava_id,
            activity.status.value,
            activity.is_indoor,
            activity.ignore_for_profile,
            activity.activity_type,
            activity.start_date,
            activity.duration_seconds,
            activity.avg_heartrate,
            activity.relative_effort,
            activity.temp_celsius_api,
            activity.humidity_api,
            activity.weight_before_user,
            activity.weight_after_user,
            activity.fluid_intake_ml_user,
            activity.bathroom_visits_user,
            activity.clothing_index_user,
            activity.temp_celsius_user,
            activity.humidity_user,
            activity.total_sweat_loss_ml,
            activity.sweat_rate_ml_per_hour,
            activity.created_at,
        )

    def _map_row_to_activity(self, row: Any) -> Activity:
        return Activity(
            id=row["id"],
            user_id=row["user_id"],
            strava_id=row["strava_id"],
            status=ActivityStatus(row["status"]),
            is_indoor=row["is_indoor"],
            ignore_for_profile=row["ignore_for_profile"],
            activity_type=row["activity_type"],
            start_date=row["start_date"],
            duration_seconds=row["duration_seconds"],
            avg_heartrate=row["avg_heartrate"],
            relative_effort=row["relative_effort"],
            temp_celsius_api=row["temp_celsius_api"],
            humidity_api=row["humidity_api"],
            weight_before_user=row["weight_before_user"],
            weight_after_user=row["weight_after_user"],
            fluid_intake_ml_user=row["fluid_intake_ml_user"],
            bathroom_visits_user=row["bathroom_visits_user"],
            clothing_index_user=row["clothing_index_user"],
            temp_celsius_user=row["temp_celsius_user"],
            humidity_user=row["humidity_user"],
            total_sweat_loss_ml=row["total_sweat_loss_ml"],
            sweat_rate_ml_per_hour=row["sweat_rate_ml_per_hour"],
            created_at=row["created_at"],
        )
