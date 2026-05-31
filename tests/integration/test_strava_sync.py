from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domain.models import StravaToken, User
from app.domain.services.activity_sync import ActivitySyncService
from app.domain.services.strava_auth import StravaAuthService
from app.infrastructure.db.repository import PostgresActivityRepository
from app.infrastructure.db.token_repository import PostgresTokenRepository
from app.infrastructure.db.user_repository import PostgresUserRepository


@pytest.mark.asyncio
async def test_full_activity_sync_flow(db_pool):
    # 1. Setup Repositories
    activity_repo = PostgresActivityRepository(db_pool)
    user_repo = PostgresUserRepository(db_pool)
    token_repo = PostgresTokenRepository(db_pool)

    # 2. Setup User & Token in DB
    user_id = uuid4()
    strava_athlete_id = 999
    user = User(id=user_id, strava_athlete_id=strava_athlete_id, email="test@example.com")
    await user_repo.save(user)

    token = StravaToken(
        user_id=user_id,
        access_token="valid_access",
        refresh_token="valid_refresh",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    await token_repo.save(token)

    # 3. Setup Mocks
    strava_client = MagicMock()
    strava_data = {
        "id": 12345,
        "type": "Run",
        "start_date": "2026-05-31T12:00:00Z",
        "elapsed_time": 3600,
        "average_heartrate": 150.0,
        "suffer_score": 50,
        "start_latlng": [59.3293, 18.0686],
    }
    strava_client.get_activity_details = AsyncMock(return_value=strava_data)

    weather_provider = MagicMock()
    weather_provider.get_weather = AsyncMock(return_value={"temp": 20.5, "humidity": 45})

    strava_auth = StravaAuthService(token_repo, strava_client)

    # 4. Run Service
    sync_service = ActivitySyncService(
        activity_repo, user_repo, strava_auth, strava_client, weather_provider
    )

    await sync_service.sync_activity(12345, strava_athlete_id)

    # 5. Verify Results in DB
    saved_activity = await activity_repo.get_by_strava_id(12345)

    assert saved_activity is not None
    assert saved_activity.user_id == user_id
    assert saved_activity.activity_type == "Run"
    assert saved_activity.temp_celsius_api == 20.5
    assert saved_activity.humidity_api == 45
    assert saved_activity.avg_heartrate == 150.0
