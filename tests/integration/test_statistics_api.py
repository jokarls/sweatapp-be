from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_strava_client
from app.domain.interfaces import IStravaClient
from app.domain.models import Activity
from app.infrastructure.db.repository import PostgresActivityRepository
from app.main import app


class FakeStravaClient(IStravaClient):
    async def exchange_authorization_code(
        self, client_id: str, client_secret: str, code: str
    ) -> dict[str, Any]:
        return {
            "token_type": "Bearer",
            "access_token": f"access_{code}",
            "refresh_token": f"refresh_{code}",
            "expires_at": 1999999999,
            "athlete": {
                "id": 112233,
                "username": "statsathlete",
                "firstname": "Stats",
                "lastname": "Athlete",
            },
        }

    async def get_activity_details(self, activity_id: int, access_token: str) -> dict[str, Any]:
        return {}

    async def refresh_token(
        self, client_id: str, client_secret: str, refresh_token: str
    ) -> dict[str, Any]:
        return {}


@pytest_asyncio.fixture
async def api_client(db_pool):
    app.state.pool = db_pool
    app.dependency_overrides[get_strava_client] = lambda: FakeStravaClient()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_statistics_unauthorized(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/statistics")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_statistics_flow(api_client: AsyncClient, db_pool) -> None:
    # 1. Login user to get auth token and user_id
    auth_response = await api_client.post(
        "/api/v1/auth/strava",
        json={"code": "stats_code"},
    )
    assert auth_response.status_code == 200
    data = auth_response.json()
    token = data["access_token"]
    user_id = data["user"]["id"]

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Assert stats are empty initially
    stats_response = await api_client.get("/api/v1/statistics", headers=headers)
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    assert stats_data["summary"]["overall_avg_sweat_rate_ml_h"] == 0.0
    assert stats_data["summary"]["total_activities_logged"] == 0
    assert stats_data["breakdowns"]["sport"] == []
    assert stats_data["breakdowns"]["environment"] == []
    assert stats_data["breakdowns"]["clothing"] == []

    # 3. Add completed activities to DB
    activity_repo = PostgresActivityRepository(db_pool)

    # Activity 1: Run, temp 8 (Cold), clothing 2 (Standard)
    # 1 hour, weight diff 1.0kg, intake 0ml -> 1000ml / 1h = 1000 ml/h
    act1 = Activity(
        user_id=user_id,
        strava_id=50001,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        weight_before_user=80.0,
        weight_after_user=79.0,
        fluid_intake_ml_user=0,
        clothing_index_user=2,
        temp_celsius_api=8.0,
    )
    act1.calculate_sweat_loss()
    await activity_repo.save(act1)

    # Activity 2: Run, temp 15 (Moderate), clothing 1 (Minimal)
    # 1.5 hours, weight diff 1.2kg, intake 300ml -> (1200 + 300) = 1500ml / 1.5h = 1000 ml/h
    act2 = Activity(
        user_id=user_id,
        strava_id=50002,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=5400,
        weight_before_user=80.0,
        weight_after_user=78.8,
        fluid_intake_ml_user=300,
        clothing_index_user=1,
        temp_celsius_api=15.0,
    )
    act2.calculate_sweat_loss()
    await activity_repo.save(act2)

    # Activity 3: Ride, temp 25 (Hot), clothing 1 (Minimal)
    # 2 hours, weight diff 1.5kg, intake 500ml -> (1500 + 500) = 2000ml / 2h = 1000 ml/h
    act3 = Activity(
        user_id=user_id,
        strava_id=50003,
        activity_type="Ride",
        start_date=datetime.now(UTC),
        duration_seconds=7200,
        weight_before_user=80.0,
        weight_after_user=78.5,
        fluid_intake_ml_user=500,
        clothing_index_user=1,
        temp_celsius_api=25.0,
    )
    act3.calculate_sweat_loss()
    await activity_repo.save(act3)

    # 4. Fetch statistics again and verify calculations
    stats_response = await api_client.get("/api/v1/statistics", headers=headers)
    assert stats_response.status_code == 200
    stats_data = stats_response.json()

    # Overall summary
    assert stats_data["summary"]["total_activities_logged"] == 3
    assert stats_data["summary"]["overall_avg_sweat_rate_ml_h"] == 1000.0

    # Sport breakdown (Sorted by count descending, so Run (2) first, Ride (1) second)
    sport_breakdown = stats_data["breakdowns"]["sport"]
    assert len(sport_breakdown) == 2
    assert sport_breakdown[0]["key"] == "run"
    assert sport_breakdown[0]["display_name"] == "Run"
    assert sport_breakdown[0]["avg_sweat_rate_ml_h"] == 1000.0
    assert sport_breakdown[0]["activity_count"] == 2

    assert sport_breakdown[1]["key"] == "ride"
    assert sport_breakdown[1]["display_name"] == "Ride"
    assert sport_breakdown[1]["avg_sweat_rate_ml_h"] == 1000.0
    assert sport_breakdown[1]["activity_count"] == 1

    # Environment breakdown (Cold, Moderate, Hot each have 1 activity with 1000 ml/h rate)
    env_breakdown = stats_data["breakdowns"]["environment"]
    assert len(env_breakdown) == 3
    cold_item = next(i for i in env_breakdown if i["key"] == "cold")
    assert cold_item["display_name"] == "Cold (< 10°C)"
    assert cold_item["avg_sweat_rate_ml_h"] == 1000.0
    assert cold_item["activity_count"] == 1

    mod_item = next(i for i in env_breakdown if i["key"] == "moderate")
    assert mod_item["display_name"] == "Moderate (10°C - 20°C)"
    assert mod_item["avg_sweat_rate_ml_h"] == 1000.0
    assert mod_item["activity_count"] == 1

    hot_item = next(i for i in env_breakdown if i["key"] == "hot")
    assert hot_item["display_name"] == "Hot (> 20°C)"
    assert hot_item["avg_sweat_rate_ml_h"] == 1000.0
    assert hot_item["activity_count"] == 1

    # Clothing breakdown (Index 1: 2 activities, Index 2: 1 activity)
    clothing_breakdown = stats_data["breakdowns"]["clothing"]
    assert len(clothing_breakdown) == 2
    assert clothing_breakdown[0]["key"] == "1"
    assert clothing_breakdown[0]["display_name"] == "Minimal"
    assert clothing_breakdown[0]["avg_sweat_rate_ml_h"] == 1000.0
    assert clothing_breakdown[0]["activity_count"] == 2

    assert clothing_breakdown[1]["key"] == "2"
    assert clothing_breakdown[1]["display_name"] == "Standard"
    assert clothing_breakdown[1]["avg_sweat_rate_ml_h"] == 1000.0
    assert clothing_breakdown[1]["activity_count"] == 1
