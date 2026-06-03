from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import ActivityDTO, ActivityUpdateDTO
from app.dependencies import get_activity_repo, get_current_user
from app.domain.interfaces import IActivityRepository
from app.domain.models import User

router = APIRouter(prefix="/activities", tags=["Activities"])


@router.get("", response_model=list[ActivityDTO])
async def list_activities(
    limit: int = 20,
    repo: IActivityRepository = Depends(get_activity_repo),
    current_user: User = Depends(get_current_user),
) -> list[ActivityDTO]:
    """
    Lists activities for the currently authenticated user.
    """
    activities = await repo.list_by_user(user_id=current_user.id, limit=limit)
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
