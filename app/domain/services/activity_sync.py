import logging
from datetime import datetime

from app.domain.interfaces import (
    IActivityRepository,
    IStravaClient,
    IUserRepository,
    IWeatherProvider,
)
from app.domain.models import Activity, ActivityStatus
from app.domain.services.strava_auth import StravaAuthService

logger = logging.getLogger(__name__)


class ActivitySyncService:
    def __init__(
        self,
        activity_repo: IActivityRepository,
        user_repo: IUserRepository,
        strava_auth: StravaAuthService,
        strava_client: IStravaClient,
        weather_provider: IWeatherProvider,
    ):
        self.activity_repo = activity_repo
        self.user_repo = user_repo
        self.strava_auth = strava_auth
        self.strava_client = strava_client
        self.weather_provider = weather_provider

    async def sync_activity(self, strava_activity_id: int, strava_athlete_id: int) -> None:
        # Check if activity already exists in database
        existing_activity = await self.activity_repo.get_by_strava_id(strava_activity_id)

        # 1. Find user
        user = await self.user_repo.get_by_strava_athlete_id(strava_athlete_id)
        if not user:
            logger.warning(f"No user found for Strava athlete {strava_athlete_id}")
            return

        # 2. Get access token
        access_token = await self.strava_auth.get_valid_access_token(user.id)

        # 3. Fetch activity details
        strava_data = await self.strava_client.get_activity_details(
            strava_activity_id, access_token
        )

        # 4. Extract temperature from Strava activity details
        temp = strava_data.get("average_temp")
        if temp is not None:
            logger.info(f"Retrieved average_temp={temp}°C from Strava activity details.")
        else:
            logger.info(
                "Strava activity details do not contain average_temp "
                "(likely recorded without a thermometer sensor)."
            )

        humidity = None
        apparent_temp = None
        weather_code = None

        # Fallback/enrichment via Weather Provider for humidity and missing temperature
        if existing_activity:
            if temp is None:
                temp = existing_activity.temp_celsius_api
            humidity = existing_activity.humidity_api

        if temp is None or humidity is None:
            start_latlng = strava_data.get("start_latlng")
            if start_latlng and len(start_latlng) == 2:
                try:
                    # Strava provides start_date as ISO string
                    start_date = datetime.fromisoformat(
                        strava_data["start_date"].replace("Z", "+00:00")
                    )
                    logger.info(
                        f"Attempting weather fallback/enrichment for lat={start_latlng[0]}, "
                        f"lon={start_latlng[1]} at {start_date}"
                    )
                    weather = await self.weather_provider.get_weather(
                        lat=start_latlng[0], lon=start_latlng[1], timestamp=int(start_date.timestamp())
                    )
                    
                    if "error" in weather:
                        logger.warning(f"Weather provider fallback failed: {weather['error']}")
                    else:
                        if temp is None:
                            temp = weather.get("temp")
                            logger.info(f"Retrieved fallback temperature={temp}°C from weather provider.")
                        humidity = weather.get("humidity")
                        logger.info(f"Retrieved humidity={humidity}% from weather provider.")
                        apparent_temp = weather.get("apparent_temp")
                        weather_code = weather.get("weather_code")
                        logger.info(f"Retrieved apparent_temp={apparent_temp}°C, weather_code={weather_code} from weather provider.")
                except Exception as e:
                    logger.error(f"Failed to fetch weather fallback: {e}")
            else:
                logger.warning(
                    "Cannot fetch fallback weather/humidity because activity start location "
                    "(start_latlng) is missing or invalid."
                )

        logger.info(f"Final activity sync values: temp_celsius_api={temp}, humidity_api={humidity}, apparent_temp={apparent_temp}, weather_code={weather_code}")

        # 5. Create or update Activity entity
        if existing_activity:
            existing_activity.activity_type = strava_data.get("sport_type") or strava_data.get("type", "Unknown")
            existing_activity.duration_seconds = strava_data.get("elapsed_time", 0)
            existing_activity.avg_heartrate = strava_data.get("average_heartrate")
            existing_activity.relative_effort = strava_data.get("suffer_score")
            existing_activity.temp_celsius_api = temp
            existing_activity.humidity_api = humidity

            # Re-calculate sweat loss if inputs are present
            existing_activity.calculate_sweat_loss()
            activity = existing_activity
            logger.info(f"Updating existing activity {strava_activity_id}")
        else:
            activity = Activity(
                user_id=user.id,
                strava_id=strava_activity_id,
                activity_type=strava_data.get("sport_type") or strava_data.get("type", "Unknown"),
                start_date=datetime.fromisoformat(strava_data["start_date"].replace("Z", "+00:00")),
                duration_seconds=strava_data.get("elapsed_time", 0),
                avg_heartrate=strava_data.get("average_heartrate"),
                relative_effort=strava_data.get("suffer_score"),
                temp_celsius_api=temp,
                humidity_api=humidity,
                apparent_temp_celsius_api=apparent_temp,
            weather_code_api=weather_code,
            status=ActivityStatus.PENDING,
        )logger.info(f"Creating new activity {strava_activity_id}")

        # 6. Save to DB
        await self.activity_repo.save(activity)
        logger.info(f"Successfully synced activity {strava_activity_id} for user {user.id}")

        # 7. TODO: Send Push Notification
