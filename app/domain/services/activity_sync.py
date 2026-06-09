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
        if existing_activity:
            logger.info(f"Activity {strava_activity_id} already exists. Skipping sync.")
            return

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
            logger.info("Strava activity details do not contain average_temp (likely recorded without a thermometer sensor).")

        humidity = None

        # Fallback/enrichment via Weather Provider for humidity and missing temperature
        if temp is None or humidity is None:
            start_latlng = strava_data.get("start_latlng")
            if start_latlng and len(start_latlng) == 2:
                try:
                    # Strava provides start_date as ISO string
                    start_date = datetime.fromisoformat(
                        strava_data["start_date"].replace("Z", "+00:00")
                    )
                    logger.info(f"Attempting weather fallback/enrichment for lat={start_latlng[0]}, lon={start_latlng[1]} at {start_date}")
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
                except Exception as e:
                    logger.error(f"Failed to fetch weather fallback: {e}")
            else:
                logger.warning("Cannot fetch fallback weather/humidity because activity start location (start_latlng) is missing or invalid.")

        logger.info(f"Final activity sync values: temp_celsius_api={temp}, humidity_api={humidity}")

        # 5. Create Activity entity
        activity = Activity(
            user_id=user.id,
            strava_id=strava_activity_id,
            activity_type=strava_data.get("type", "Unknown"),
            start_date=datetime.fromisoformat(strava_data["start_date"].replace("Z", "+00:00")),
            duration_seconds=strava_data.get("elapsed_time", 0),
            avg_heartrate=strava_data.get("average_heartrate"),
            relative_effort=strava_data.get("suffer_score"),
            temp_celsius_api=temp,
            humidity_api=humidity,
            status=ActivityStatus.PENDING,
        )

        # 6. Save to DB
        await self.activity_repo.save(activity)
        logger.info(f"Successfully synced activity {strava_activity_id} for user {user.id}")

        # 7. TODO: Send Push Notification
