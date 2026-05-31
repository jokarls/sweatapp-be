from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response, status

from app.core.config import settings
from app.dependencies import get_activity_sync_service
from app.domain.services.activity_sync import ActivitySyncService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/strava")
async def validate_webhook(
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge"),
) -> dict[str, str] | Response:
    """
    Strava webhook validation.
    """
    if mode == "subscribe" and token == settings.STRAVA_WEBHOOK_VERIFY_TOKEN:
        return {"hub.challenge": challenge}

    return Response(status_code=status.HTTP_403_FORBIDDEN)


@router.post("/strava")
async def handle_webhook_event(
    request: Request,
    background_tasks: BackgroundTasks,
    sync_service: ActivitySyncService = Depends(get_activity_sync_service),
) -> Response:
    """
    Receives Strava events.
    """
    data = await request.json()

    # Check if it's an activity creation
    if data.get("object_type") == "activity" and data.get("aspect_type") == "create":
        activity_id = data.get("object_id")
        athlete_id = data.get("owner_id")

        # Trigger background task to process this activity
        background_tasks.add_task(sync_service.sync_activity, activity_id, athlete_id)

    return Response(status_code=status.HTTP_200_OK)


@router.post("/test-sync/{athlete_id}/{activity_id}")
async def manual_sync(
    athlete_id: int,
    activity_id: int,
    background_tasks: BackgroundTasks,
    sync_service: ActivitySyncService = Depends(get_activity_sync_service),
) -> dict[str, str]:
    """
    Manually trigger a sync for testing.
    """
    background_tasks.add_task(sync_service.sync_activity, activity_id, athlete_id)
    return {"message": f"Sync started for activity {activity_id}"}
