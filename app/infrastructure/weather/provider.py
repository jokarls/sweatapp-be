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
            params: dict[str, str | float] = {
                "latitude": lat,
                "longitude": lon,
                "start_date": date_str,
                "end_date": date_str,
                "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code",
            }
            response = await client.get(self.BASE_URL, params=params)
            
            if response.status_code != 200:
                return {
                    "temp": None,
                    "humidity": None,
                    "apparent_temp": None,
                    "weather_code": None,
                    "error": f"Open-Meteo returned status {response.status_code}"
                }
            
            data = response.json()
            hourly = data.get("hourly", {})
            temps = hourly.get("temperature_2m", [])
            humidities = hourly.get("relative_humidity_2m", [])
            apparent_temps = hourly.get("apparent_temperature", [])
            weather_codes = hourly.get("weather_code", [])
            
            if 0 <= hour < len(temps) and 0 <= hour < len(humidities):
                apparent_temp = apparent_temps[hour] if hour < len(apparent_temps) else None
                weather_code = int(weather_codes[hour]) if hour < len(weather_codes) and weather_codes[hour] is not None else None
                return {
                    "temp": temps[hour],
                    "humidity": int(humidities[hour]),
                    "apparent_temp": apparent_temp,
                    "weather_code": weather_code,
                    "provider": "open-meteo",
                }
            
            return {
                "temp": None,
                "humidity": None,
                "apparent_temp": None,
                "weather_code": None,
                "error": "No data found for timestamp hour"
            }

