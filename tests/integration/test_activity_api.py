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


@pytest.mark.asyncio
async def test_cursor_pagination_repository(db_pool):
    repo = PostgresActivityRepository(db_pool)
    user_id = uuid4()
    await db_pool.execute(
        'INSERT INTO "user" (id, strava_athlete_id) VALUES ($1, $2)', user_id, 99999
    )

    # Create 3 activities at distinct start dates
    # start_date: a1 (newest), a2 (middle), a3 (oldest)
    a1 = Activity(
        user_id=user_id,
        strava_id=101,
        activity_type="Run",
        start_date=datetime(2026, 6, 8, 10, 0, 0, tzinfo=UTC),
        duration_seconds=1800,
    )
    a2 = Activity(
        user_id=user_id,
        strava_id=102,
        activity_type="Cycle",
        start_date=datetime(2026, 6, 8, 9, 0, 0, tzinfo=UTC),
        duration_seconds=3600,
    )
    a3 = Activity(
        user_id=user_id,
        strava_id=103,
        activity_type="Swim",
        start_date=datetime(2026, 6, 8, 8, 0, 0, tzinfo=UTC),
        duration_seconds=1200,
    )

    await repo.save(a1)
    await repo.save(a2)
    await repo.save(a3)

    # 1. Fetch initial page limit=2 (should return a1, a2)
    page1 = await repo.list_by_user(user_id=user_id, limit=2)
    assert len(page1) == 2
    assert page1[0].id == a1.id
    assert page1[1].id == a2.id

    # 2. Get cursor parameters using the last item in page 1 (a2)
    last_item = page1[-1]

    # 3. Fetch second page using cursor of a2 (should return a3)
    page2 = await repo.list_by_user(
        user_id=user_id,
        limit=2,
        before_start_date=last_item.start_date,
        before_id=last_item.id
    )
    assert len(page2) == 1
    assert page2[0].id == a3.id
