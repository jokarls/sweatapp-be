from datetime import UTC, datetime
from uuid import uuid4

from app.domain.models import Activity, ActivityStatus


def test_calculate_sweat_loss_no_fluid():
    activity = Activity(
        user_id=uuid4(),
        strava_id=1,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        weight_before_user=70.0,
        weight_after_user=69.0,
        fluid_intake_ml_user=0,
        bathroom_visits_user=0,
    )

    activity.calculate_sweat_loss()

    assert activity.total_sweat_loss_ml == 1000
    assert activity.sweat_rate_ml_per_hour == 1000.0
    assert activity.status == ActivityStatus.COMPLETED


def test_calculate_sweat_loss_with_fluid_and_bathroom():
    activity = Activity(
        user_id=uuid4(),
        strava_id=2,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=1800,  # 30 min
        weight_before_user=70.0,
        weight_after_user=69.5,
        fluid_intake_ml_user=500,
        bathroom_visits_user=1,
    )

    activity.calculate_sweat_loss()

    # (70.0 - 69.5) * 1000 + 500 - (1 * 250) = 500 + 500 - 250 = 750
    assert activity.total_sweat_loss_ml == 750
    # 750ml / 0.5h = 1500ml/h
    assert activity.sweat_rate_ml_per_hour == 1500.0


def test_calculate_sweat_loss_missing_data():
    activity = Activity(
        user_id=uuid4(),
        strava_id=3,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        weight_before_user=70.0,
        weight_after_user=None,  # Missing
    )

    activity.calculate_sweat_loss()

    assert activity.total_sweat_loss_ml is None
    assert activity.status == ActivityStatus.PENDING
