from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import ActivityDTO, ActivityUpdateDTO
from app.dependencies import get_activity_repo
from app.domain.interfaces import IActivityRepository

router = APIRouter(prefix="/activities", tags=["Activities"])

@router.get("", response_model=list[ActivityDTO])
async def list_activities(
    limit: int = 20,
    repo: IActivityRepository = Depends(get_activity_repo),
) -> list[ActivityDTO]:
    # For now, we don't have a user context, so we'd need a user_id
    # In a real app, this would come from the auth token
    return []

@router.get("/{id}", response_model=ActivityDTO)
async def get_activity(
    id: UUID,
    repo: IActivityRepository = Depends(get_activity_repo),
) -> ActivityDTO:
    activity = await repo.get_by_id(id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return ActivityDTO.model_validate(activity)

@router.patch("/{id}", response_model=ActivityDTO)
async def update_activity(
    id: UUID,
    update_data: ActivityUpdateDTO,
    repo: IActivityRepository = Depends(get_activity_repo),
) -> ActivityDTO:
    activity = await repo.get_by_id(id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Update entity fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        if hasattr(activity, field):
            setattr(activity, field, value)

    # Recalculate sweat loss
    activity.calculate_sweat_loss()

    # Save back to repository
    await repo.save(activity)

    return ActivityDTO.model_validate(activity)
