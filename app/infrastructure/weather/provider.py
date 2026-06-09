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
            data = cast("dict[str, Any]", response.json())

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


class OpenMeteoProvider(IWeatherProvider):
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    async def get_weather(self, lat: float, lon: float, timestamp: int) -> dict[str, Any]:
        """
        Fetches historical weather data from Open-Meteo's free Archive API.
        No API key required.
        """
        from datetime import datetime, UTC
        dt = datetime.fromtimestamp(timestamp, tz=UTC)
        date_str = dt.date().isoformat()  # "YYYY-MM-DD"
        hour = dt.hour

        async with httpx.AsyncClient() as client:
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": date_str,
                "end_date": date_str,
                "hourly": "temperature_2m,relative_humidity_2m",
            }
            response = await client.get(self.BASE_URL, params=params)
            
            if response.status_code != 200:
                return {"temp": None, "humidity": None, "error": f"Open-Meteo returned status {response.status_code}"}
            
            data = response.json()
            hourly = data.get("hourly", {})
            temps = hourly.get("temperature_2m", [])
            humidities = hourly.get("relative_humidity_2m", [])
            
            if 0 <= hour < len(temps) and 0 <= hour < len(humidities):
                return {
                    "temp": temps[hour],
                    "humidity": int(humidities[hour]),
                    "provider": "open-meteo",
                }
            
            return {"temp": None, "humidity": None, "error": "No data found for timestamp hour"}
