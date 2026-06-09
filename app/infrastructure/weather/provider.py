from typing import Any

import httpx

from app.domain.interfaces import IWeatherProvider


class OpenMeteoProvider(IWeatherProvider):
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    async def get_weather(self, lat: float, lon: float, timestamp: int) -> dict[str, Any]:
        """
        Fetches historical weather data from Open-Meteo's free Archive API.
        No API key required.
        """
        from datetime import UTC, datetime
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
