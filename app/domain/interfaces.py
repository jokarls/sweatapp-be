from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.models import Activity, StravaToken, User


class IActivityRepository(ABC):
    @abstractmethod
    async def get_by_id(self, activity_id: UUID) -> Activity | None:
        pass

    @abstractmethod
    async def get_by_strava_id(self, strava_id: int) -> Activity | None:
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID, limit: int = 20) -> list[Activity]:
        pass

    @abstractmethod
    async def save(self, activity: Activity) -> None:
        pass


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        pass

    @abstractmethod
    async def get_by_strava_athlete_id(self, strava_id: int) -> User | None:
        pass

    @abstractmethod
    async def save(self, user: User) -> None:
        pass


class ITokenRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> StravaToken | None:
        pass

    @abstractmethod
    async def save(self, token: StravaToken) -> None:
        pass


class IWeatherProvider(ABC):
    @abstractmethod
    async def get_weather(self, lat: float, lon: float, timestamp: int) -> dict[str, Any]:
        pass


class IStravaClient(ABC):
    @abstractmethod
    async def get_activity_details(self, activity_id: int, access_token: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def refresh_token(
        self, client_id: str, client_secret: str, refresh_token: str
    ) -> dict[str, Any]:
        pass
