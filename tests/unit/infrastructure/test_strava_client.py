import pytest

from app.infrastructure.strava.client import StravaClient


@pytest.mark.asyncio
async def test_get_activity_details_mock(respx_mock):
    # Setup mock
    activity_id = 123456789
    access_token = "fake_token"
    mock_data = {
        "id": activity_id,
        "name": "Lunch Run",
        "type": "Run",
        "start_date": "2026-05-31T12:00:00Z",
        "elapsed_time": 3600,
        "average_heartrate": 155.5
    }
    
    respx_mock.get(f"https://www.strava.com/api/v3/activities/{activity_id}").mock(
        return_value=pytest.importorskip("httpx").Response(200, json=mock_data)
    )
    
    client = StravaClient()
    result = await client.get_activity_details(activity_id, access_token)
    
    assert result["id"] == activity_id
    assert result["average_heartrate"] == 155.5
