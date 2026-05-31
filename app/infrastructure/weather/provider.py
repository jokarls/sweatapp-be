from typing import Any, cast

import httpx

from app.domain.interfaces import IWeatherProvider


class OpenWeatherMapProvider(IWeatherProvider):
    BASE_URL = "https://api.openweathermap.org/data/3.0/onecall/timemachine"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_weather(self, lat: float, lon: float, timestamp: int) -> dict[str, Any]:
        """
        Fetches historical weather data for a specific location and time.
        Requires OpenWeatherMap One Call 3.0 subscription.
        """
        if not self.api_key:
            return {"temp": None, "humidity": None, "error": "No API key"}

        async with httpx.AsyncClient() as client:
            params: dict[str, str | float | int] = {
                "lat": lat,
                "lon": lon,
                "dt": timestamp,
                "appid": self.api_key,
                "units": "metric",
            }
            response = await client.get(self.BASE_URL, params=params)

            # If 3.0 is not available, fallback to something or log
            if response.status_code == 401:
                return {"temp": None, "humidity": None, "error": "Unauthorized / API Key issue"}

            response.raise_for_status()
            data = cast(dict[str, Any], response.json())

            # One Call 3.0 Time Machine returns 'data': [ { 'temp': ..., 'humidity': ... } ]
            results = data.get("data", [])
            if not results:
                return {"temp": None, "humidity": None, "error": "No data found for timestamp"}

            weather = results[0]
            return {
                "temp": weather.get("temp"),
                "humidity": weather.get("humidity"),
                "provider": "openweathermap",
            }
