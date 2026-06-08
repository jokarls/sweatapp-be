from fastapi import APIRouter, Depends

from app.api.schemas import UserSweatStatisticsDTO
from app.dependencies import get_activity_repo, get_current_user
from app.domain.interfaces import IActivityRepository
from app.domain.models import User
from app.domain.services.statistics import SweatStatisticsService

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("", response_model=UserSweatStatisticsDTO)
async def get_user_statistics(
    repo: IActivityRepository = Depends(get_activity_repo),
    current_user: User = Depends(get_current_user),
) -> UserSweatStatisticsDTO:
    """
    Computes and retrieves personalized hydration and fluid loss metrics for the user.
    """
    activities = await repo.get_completed_by_user(current_user.id)
    stats_service = SweatStatisticsService()
    stats = stats_service.calculate_statistics(activities)
    return UserSweatStatisticsDTO.model_validate(stats)
