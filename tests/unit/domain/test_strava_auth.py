from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domain.models import StravaToken
from app.domain.services.strava_auth import StravaAuthService


@pytest.mark.asyncio
async def test_get_valid_access_token_not_expired():
    token_repo = MagicMock()
    strava_client = MagicMock()

    user_id = uuid4()
    token = StravaToken(
        user_id=user_id,
        access_token="valid_token",
        refresh_token="refresh",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    token_repo.get_by_user_id = AsyncMock(return_value=token)

    service = StravaAuthService(token_repo, strava_client)
    access_token = await service.get_valid_access_token(user_id)

    assert access_token == "valid_token"
    strava_client.refresh_token.assert_not_called()


@pytest.mark.asyncio
async def test_get_valid_access_token_expired():
    token_repo = MagicMock()
    strava_client = MagicMock()

    user_id = uuid4()
    expired_token = StravaToken(
        user_id=user_id,
        access_token="old_token",
        refresh_token="refresh_me",
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    token_repo.get_by_user_id = AsyncMock(return_value=expired_token)

    new_expires_at = int((datetime.now(UTC) + timedelta(hours=6)).timestamp())
    strava_client.refresh_token = AsyncMock(
        return_value={
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_at": new_expires_at,
        }
    )
    token_repo.save = AsyncMock()

    service = StravaAuthService(token_repo, strava_client)
    access_token = await service.get_valid_access_token(user_id)

    assert access_token == "new_token"
    strava_client.refresh_token.assert_called_once()
    token_repo.save.assert_called_once()

    # Check that token object was updated
    updated_token = token_repo.save.call_args[0][0]
    assert updated_token.access_token == "new_token"
    assert updated_token.refresh_token == "new_refresh"
