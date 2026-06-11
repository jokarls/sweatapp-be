from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ActivityStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


@dataclass
class Activity:
    user_id: UUID
    strava_id: int
    activity_type: str
    start_date: datetime
    duration_seconds: int
    id: UUID = field(default_factory=uuid4)
    status: ActivityStatus = ActivityStatus.PENDING

    # Optional metrics from Strava/API
    avg_heartrate: float | None = None
    relative_effort: int | None = None
    temp_celsius_api: float | None = None
    humidity_api: int | None = None
    apparent_temp_celsius_api: float | None = None
    weather_code_api: int | None = None

    # Manual Input
    weight_before_user: float | None = None
    weight_after_user: float | None = None
    fluid_intake_ml_user: int | None = None
    bathroom_visits_user: int = 0
    clothing_index_user: int | None = None

    # Manual Weather Overrides
    temp_celsius_user: float | None = None
    humidity_user: int | None = None

    # Computed Result
    total_sweat_loss_ml: int | None = None
    sweat_rate_ml_per_hour: float | None = None

    # Metadata
    is_indoor: bool = False
    ignore_for_profile: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def calculate_sweat_loss(self) -> None:
        """
        Calculates sweat loss based on weight diff, fluid intake and bathroom visits.
        Formula: (Weight Before - Weight After) + Fluid Intake - (Bathroom Visits * 250ml)
        """
        if self.weight_before_user is None or self.weight_after_user is None:
            return

        weight_diff_kg = self.weight_before_user - self.weight_after_user
        weight_diff_ml = weight_diff_kg * 1000

        # Estimate 250ml per bathroom visit as a starting point
        bathroom_loss_ml = self.bathroom_visits_user * 250

        fluid_intake = self.fluid_intake_ml_user or 0

        self.total_sweat_loss_ml = int(round(weight_diff_ml + fluid_intake - bathroom_loss_ml))

        if self.duration_seconds > 0:
            hours = self.duration_seconds / 3600
            self.sweat_rate_ml_per_hour = round(self.total_sweat_loss_ml / hours, 2)

        self.status = ActivityStatus.COMPLETED


@dataclass
class User:
    strava_athlete_id: int
    id: UUID = field(default_factory=uuid4)
    last_known_weight: float | None = None
    weight_unit: str = "kg"
    fluid_unit: str = "ml"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class StravaToken:
    user_id: UUID
    access_token: str
    refresh_token: str
    expires_at: datetime
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) >= self.expires_at


@dataclass
class BreakdownItem:
    key: str
    display_name: str
    avg_sweat_rate_ml_h: float
    activity_count: int


@dataclass
class SummaryStats:
    overall_avg_sweat_rate_ml_h: float
    total_activities_logged: int


@dataclass
class UserSweatStatistics:
    summary: SummaryStats
    breakdowns: dict[str, list[BreakdownItem]]

