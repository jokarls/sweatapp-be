import base64
import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.schemas import ActivityDTO, ActivityUpdateDTO
from app.dependencies import get_activity_repo, get_current_user
from app.domain.interfaces import IActivityRepository
from app.domain.models import User

router = APIRouter(prefix="/activities", tags=["Activities"])


def encode_cursor(start_date: datetime, activity_id: UUID) -> str:
    """
    Encodes start_date and activity_id into an opaque Base64 string cursor.
    """
    data = {
        "start_date": start_date.isoformat(),
        "id": str(activity_id)
    }
    json_bytes = json.dumps(data).encode("utf-8")
    return base64.urlsafe_b64encode(json_bytes).decode("utf-8")


def decode_cursor(cursor_str: str) -> tuple[datetime, UUID]:
    """
    Decodes the opaque Base64 string cursor back into (start_date, activity_id).
    Raises ValueError if decoding fails.
    """
    try:
        json_bytes = base64.urlsafe_b64decode(cursor_str.encode("utf-8"))
        data = json.loads(json_bytes.decode("utf-8"))
        return datetime.fromisoformat(data["start_date"]), UUID(data["id"])
    except Exception as e:
        raise ValueError("Invalid pagination cursor format") from e


@router.get("", response_model=list[ActivityDTO])
async def list_activities(
    response: Response,
    limit: int = 20,
    cursor: str | None = None,
    repo: IActivityRepository = Depends(get_activity_repo),
    current_user: User = Depends(get_current_user),
) -> list[ActivityDTO]:
    """
    Lists activities for the currently authenticated user.
    """
    before_start_date = None
    before_id = None

    if cursor:
        try:
            before_start_date, before_id = decode_cursor(cursor)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pagination cursor",
            ) from e

    activities = await repo.list_by_user(
        user_id=current_user.id,
        limit=limit,
        before_start_date=before_start_date,
        before_id=before_id,
    )

    if len(activities) == limit:
        last_item = activities[-1]
        next_cursor = encode_cursor(last_item.start_date, last_item.id)
        response.headers["X-Next-Cursor"] = next_cursor
        response.headers["Access-Control-Expose-Headers"] = "X-Next-Cursor"

    return [ActivityDTO.model_validate(activity) for activity in activities]


@router.get("/{id}", response_model=ActivityDTO)
async def get_activity(
    id: UUID,
    repo: IActivityRepository = Depends(get_activity_repo),
    current_user: User = Depends(get_current_user),
) -> ActivityDTO:
    """
    Retrieves a single activity by ID, ensuring it belongs to the current user.
    """
    activity = await repo.get_by_id(id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    if activity.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this activity",
        )

    return ActivityDTO.model_validate(activity)


@router.patch("/{id}", response_model=ActivityDTO)
async def update_activity(
    id: UUID,
    update_data: ActivityUpdateDTO,
    repo: IActivityRepository = Depends(get_activity_repo),
    current_user: User = Depends(get_current_user),
) -> ActivityDTO:
    """
    Updates an activity, ensuring it belongs to the current user.
    """
    activity = await repo.get_by_id(id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    if activity.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this activity",
        )

    # Update entity fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        if hasattr(activity, field):
            setattr(activity, field, value)

    # Recalculate sweat loss
    activity.calculate_sweat_loss()

    # Save back to repository
    await repo.save(activity)

    return ActivityDTO.model_validate(activity)
