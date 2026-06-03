from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import StravaLoginRequest, TokenResponse, UserDTO
from app.core.security import create_access_token
from app.dependencies import get_strava_auth_service
from app.domain.services.strava_auth import StravaAuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/strava", response_model=TokenResponse)
async def strava_login(
    payload: StravaLoginRequest,
    auth_service: StravaAuthService = Depends(get_strava_auth_service),
) -> TokenResponse:
    """
    Exchanges a Strava authorization code for tokens, logs in or registers the user,
    and returns a local JWT access token.
    """
    try:
        user = await auth_service.login_or_register(payload.code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strava authentication failed: {str(e)}",
        ) from e

    # Create local JWT signed for SweatCheck backend
    access_token = create_access_token(user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserDTO.model_validate(user),
    )
