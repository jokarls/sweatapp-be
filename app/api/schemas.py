from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActivityStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"

class ActivityDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    strava_id: int
    status: ActivityStatus
    activity_type: str | None
    start_date: datetime | None
    duration_seconds: int
    avg_heartrate: float | None = None
    relative_effort: int | None = None
    is_indoor: bool
    ignore_for_profile: bool
    
    # Weather API Data
    temp_celsius_api: float | None = None
    humidity_api: int | None = None
    
    # User Data
    weight_before_user: float | None = None
    weight_after_user: float | None = None
    fluid_intake_ml_user: int | None = None
    bathroom_visits_user: int
    clothing_index_user: int | None = None
    temp_celsius_user: float | None = None
    humidity_user: int | None = None
    
    # Calculated
    total_sweat_loss_ml: int | None = None
    sweat_rate_ml_per_hour: float | None = None

class ActivityUpdateDTO(BaseModel):
    is_indoor: bool | None = None
    ignore_for_profile: bool | None = None
    weight_before_user: float | None = None
    weight_after_user: float | None = None
    fluid_intake_ml_user: int | None = None
    bathroom_visits_user: int | None = None
    clothing_index_user: int | None = None
    temp_celsius_user: float | None = None
    humidity_user: int | None = None

class UserDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    strava_athlete_id: int
    last_known_weight: float | None
    weight_unit: str
    fluid_unit: str

class SweatZoneDTO(BaseModel):
    temp_range: str
    avg_sweat_rate: float
    activity_count: int

class SweatStatsDTO(BaseModel):
    zones: list[SweatZoneDTO]
