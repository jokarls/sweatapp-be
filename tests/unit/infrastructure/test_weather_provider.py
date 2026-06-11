import pytest


@pytest.mark.asyncio
async def test_get_weather_open_meteo_mock(respx_mock):
    lat, lon, ts = 59.3293, 18.0686, 1717156800  # 2024-05-31 12:00:00 UTC

    temps = [0.0] * 24
    temps[12] = 22.5
    humidities = [0] * 24
    humidities[12] = 40
    apparent_temps = [0.0] * 24
    apparent_temps[12] = 24.1
    weather_codes = [0] * 24
    weather_codes[12] = 3  # Overcast

    mock_response = {
        "latitude": lat,
        "longitude": lon,
        "hourly": {
            "time": [f"2024-05-31T{h:02d}:00" for h in range(24)],
            "temperature_2m": temps,
            "relative_humidity_2m": humidities,
            "apparent_temperature": apparent_temps,
            "weather_code": weather_codes,
        }
    }

    respx_mock.get("https://archive-api.open-meteo.com/v1/archive").mock(
        return_value=pytest.importorskip("httpx").Response(200, json=mock_response)
    )

    from app.infrastructure.weather.provider import OpenMeteoProvider
    provider = OpenMeteoProvider()
    result = await provider.get_weather(lat, lon, ts)

    assert result["temp"] == 22.5
    assert result["humidity"] == 40
    assert result["apparent_temp"] == 24.1
    assert result["weather_code"] == 3
    assert result["provider"] == "open-meteo"
