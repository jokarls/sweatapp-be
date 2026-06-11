from typing import Any, cast

import httpx

from app.domain.interfaces import IStravaClient


class StravaClient(IStravaClient):
    BASE_URL = "https://www.strava.com/api/v3"

    async def get_activity_details(self, activity_id: int, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/activities/{activity_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

    async def refresh_token(self, client_id: str, client_secret: str, refresh_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise ValueError(
                    f"Strava token refresh failed. Status: {response.status_code}, Body: {response.text}"
                ) from e
            return cast("dict[str, Any]", response.json())

    async def exchange_authorization_code(self, client_id: str, client_secret: str, code: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise ValueError(
                    f"Strava token exchange failed. Status: {response.status_code}, Body: {response.text}"
                ) from e
            return cast("dict[str, Any]", response.json())
