from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.dependencies import get_strava_client
from app.domain.interfaces import IStravaClient
from app.domain.models import Activity
from app.infrastructure.db.repository import PostgresActivityRepository
from app.main import app


class FakeStravaClient(IStravaClient):
    async def exchange_authorization_code(
        self, client_id: str, client_secret: str, code: str
    ) -> dict[str, Any]:
        # Return a fake Strava OAuth response
        return {
            "token_type": "Bearer",
            "access_token": f"access_{code}",
            "refresh_token": f"refresh_{code}",
            "expires_at": 1999999999,  # Far future
            "athlete": {
                "id": 987654,
                "username": "testathlete",
                "firstname": "Test",
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
    # Inject our test Postgres DB pool into the app state
    app.state.pool = db_pool

    # Override the Strava client dependency with our FakeStravaClient
    app.dependency_overrides[get_strava_client] = lambda: FakeStravaClient()

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clear overrides after the test
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unauthorized_endpoints(api_client: AsyncClient) -> None:
    # Attempting to fetch activities without token should return 403
    response = await api_client.get("/api/v1/activities")
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_strava_login_and_secured_endpoint_flow(api_client: AsyncClient, db_pool) -> None:
    # 1. POST /api/v1/auth/strava to Register a new user
    auth_response = await api_client.post(
        "/api/v1/auth/strava",
        json={"code": "auth_code_xyz"},
    )
    assert auth_response.status_code == 200
    data = auth_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["strava_athlete_id"] == 987654

    token = data["access_token"]
    user_id = data["user"]["id"]

    # Verify user was saved in DB
    row = await db_pool.fetchrow('SELECT * FROM "user" WHERE id = $1', user_id)
    assert row is not None
    assert row["strava_athlete_id"] == 987654

    # 2. POST again with same code (Login of existing user)
    login_response = await api_client.post(
        "/api/v1/auth/strava",
        json={"code": "auth_code_xyz"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["user"]["id"] == user_id  # Should reuse same user ID

    # 3. Request GET /api/v1/activities with valid token
    headers = {"Authorization": f"Bearer {token}"}
    activities_response = await api_client.get("/api/v1/activities", headers=headers)
    assert activities_response.status_code == 200
    assert activities_response.json() == []  # No activities yet

    # 4. Insert an activity for this user into the DB and fetch again
    activity_repo = PostgresActivityRepository(db_pool)
    from datetime import UTC, datetime
    activity = Activity(
        user_id=user_id,
        strava_id=1234567,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=1800,
    )
    await activity_repo.save(activity)

    activities_response = await api_client.get("/api/v1/activities", headers=headers)
    assert activities_response.status_code == 200
    activities_list = activities_response.json()
    assert len(activities_list) == 1
    assert activities_list[0]["strava_id"] == 1234567
    assert activities_list[0]["activity_type"] == "Run"


@pytest.mark.asyncio
async def test_access_other_users_activity_denied(api_client: AsyncClient, db_pool) -> None:
    # 1. Register User 1
    auth_resp1 = await api_client.post("/api/v1/auth/strava", json={"code": "user1_code"})
    token1 = auth_resp1.json()["access_token"]

    # 2. Register User 2 (we'll override/mock athlete_id to be different)
    # Since our simple FakeStravaClient has hardcoded id=987654, let's create user 2 manually in DB
    # or just insert an activity belonging to another user.
    from uuid import uuid4
    user2_id = uuid4()
    await db_pool.execute(
        'INSERT INTO "user" (id, strava_athlete_id) VALUES ($1, $2)', user2_id, 888888
    )

    activity_repo = PostgresActivityRepository(db_pool)
    from datetime import UTC, datetime
    user2_activity = Activity(
        user_id=user2_id,
        strava_id=8888889,
        activity_type="Ride",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
    )
    await activity_repo.save(user2_activity)

    # 3. User 1 tries to access User 2's activity -> expect 403 Forbidden
    headers1 = {"Authorization": f"Bearer {token1}"}
    resp = await api_client.get(f"/api/v1/activities/{user2_activity.id}", headers=headers1)
    assert resp.status_code == 403
    assert "permission" in resp.json()["detail"]
