from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.models import Activity, ActivityStatus
from app.infrastructure.db.repository import PostgresActivityRepository


@pytest.mark.asyncio
async def test_save_and_get_activity(db_pool):
    repo = PostgresActivityRepository(db_pool)
    user_id = uuid4()

    # Create a user first (needed for FK)
    await db_pool.execute(
        'INSERT INTO "user" (id, strava_athlete_id) VALUES ($1, $2)', user_id, 12345
    )

    activity = Activity(
        user_id=user_id,
        strava_id=98765,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        avg_heartrate=150.0,
    )

    # Save
    await repo.save(activity)

    # Get
    saved = await repo.get_by_id(activity.id)

    assert saved is not None
    assert saved.strava_id == 98765
    assert saved.activity_type == "Run"
    assert saved.avg_heartrate == 150.0
    assert saved.status == ActivityStatus.PENDING


@pytest.mark.asyncio
async def test_calculate_sweat_loss_integration(db_pool):
    repo = PostgresActivityRepository(db_pool)
    user_id = uuid4()
    await db_pool.execute(
        'INSERT INTO "user" (id, strava_athlete_id) VALUES ($1, $2)', user_id, 54321
    )

    activity = Activity(
        user_id=user_id,
        strava_id=11111,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        weight_before_user=80.0,
        weight_after_user=79.0,
        fluid_intake_ml_user=500,
        bathroom_visits_user=0,
    )

    # Logic check
    activity.calculate_sweat_loss()
    assert activity.total_sweat_loss_ml == 1500  # (80-79)*1000 + 500
    assert activity.sweat_rate_ml_per_hour == 1500.0

    # Save
    await repo.save(activity)

    # Verify saved state
    saved = await repo.get_by_id(activity.id)
    assert saved.status == ActivityStatus.COMPLETED
    assert saved.total_sweat_loss_ml == 1500
