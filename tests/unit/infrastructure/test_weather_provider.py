import pytest

from app.infrastructure.weather.provider import OpenWeatherMapProvider


@pytest.mark.asyncio
async def test_get_weather_mock(respx_mock):
    api_key = "fake_key"
    lat, lon, ts = 59.3293, 18.0686, 1717156800

    mock_response = {
        "lat": lat,
        "lon": lon,
        "timezone": "UTC",
        "data": [{"dt": ts, "temp": 22.5, "humidity": 40}],
    }

    respx_mock.get("https://api.openweathermap.org/data/3.0/onecall/timemachine").mock(
        return_value=pytest.importorskip("httpx").Response(200, json=mock_response)
    )

    provider = OpenWeatherMapProvider(api_key)
    result = await provider.get_weather(lat, lon, ts)

    assert result["temp"] == 22.5
    assert result["humidity"] == 40
    assert result["provider"] == "openweathermap"
