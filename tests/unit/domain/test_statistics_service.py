from datetime import UTC, datetime
from uuid import uuid4

from app.domain.models import Activity, ActivityStatus
from app.domain.services.statistics import SweatStatisticsService


def test_statistics_service_empty_input() -> None:
    service = SweatStatisticsService()
    stats = service.calculate_statistics([])

    assert stats.summary.overall_avg_sweat_rate_ml_h == 0.0
    assert stats.summary.total_activities_logged == 0
    assert stats.breakdowns["sport"] == []
    assert stats.breakdowns["environment"] == []
    assert stats.breakdowns["clothing"] == []


def test_statistics_service_ignores_incomplete_or_invalid_activities() -> None:
    user_id = uuid4()
    # Incomplete activity
    activity1 = Activity(
        user_id=user_id,
        strava_id=1,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        status=ActivityStatus.PENDING,
    )
    # Valid completed activity
    activity2 = Activity(
        user_id=user_id,
        strava_id=2,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        status=ActivityStatus.COMPLETED,
        weight_before_user=80.0,
        weight_after_user=79.2,
        fluid_intake_ml_user=200,
    )
    activity2.calculate_sweat_loss()

    service = SweatStatisticsService()
    stats = service.calculate_statistics([activity1, activity2])

    assert stats.summary.total_activities_logged == 1
    assert stats.summary.overall_avg_sweat_rate_ml_h == 1000.0


def test_statistics_service_sport_breakdown() -> None:
    user_id = uuid4()
    # Run activity (sweat rate = 1000 ml/h)
    act_run = Activity(
        user_id=user_id,
        strava_id=1,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        status=ActivityStatus.COMPLETED,
        weight_before_user=80.0,
        weight_after_user=79.2,
        fluid_intake_ml_user=200,
    )
    act_run.calculate_sweat_loss()

    # Ride activity (sweat rate = 600 ml/h)
    act_ride1 = Activity(
        user_id=user_id,
        strava_id=2,
        activity_type="Ride",
        start_date=datetime.now(UTC),
        duration_seconds=7200,
        status=ActivityStatus.COMPLETED,
        weight_before_user=80.0,
        weight_after_user=79.0,
        fluid_intake_ml_user=400,
    )
    act_ride1.calculate_sweat_loss()

    # Second Ride activity (sweat rate = 800 ml/h)
    act_ride2 = Activity(
        user_id=user_id,
        strava_id=3,
        activity_type="Ride",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        status=ActivityStatus.COMPLETED,
        weight_before_user=80.0,
        weight_after_user=79.4,
        fluid_intake_ml_user=200,
    )
    act_ride2.calculate_sweat_loss()

    service = SweatStatisticsService()
    stats = service.calculate_statistics([act_run, act_ride1, act_ride2])

    assert stats.summary.total_activities_logged == 3
    # Average of 1000, 700, 800 (wait: act_ride1 total_sweat_loss is:
    # (80.0-79.0)*1000 + 400 - 0 = 1400ml. Rate = 1400 / 2 = 700ml/h)
    # Average = (1000 + 700 + 800) / 3 = 833.33
    assert stats.summary.overall_avg_sweat_rate_ml_h == 833.33

    # Check sport breakdown (sorted by count descending, so Ride (2) first, Run (1) second)
    assert len(stats.breakdowns["sport"]) == 2
    
    ride_stat = stats.breakdowns["sport"][0]
    assert ride_stat.key == "ride"
    assert ride_stat.display_name == "Ride"
    assert ride_stat.avg_sweat_rate_ml_h == 750.0  # Average of 700 and 800
    assert ride_stat.activity_count == 2

    run_stat = stats.breakdowns["sport"][1]
    assert run_stat.key == "run"
    assert run_stat.display_name == "Run"
    assert run_stat.avg_sweat_rate_ml_h == 1000.0
    assert run_stat.activity_count == 1


def test_statistics_service_temperature_breakdown() -> None:
    user_id = uuid4()
    
    # Cold (<10°C) activity using API temp
    act_cold = Activity(
        user_id=user_id,
        strava_id=1,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        status=ActivityStatus.COMPLETED,
        weight_before_user=80.0,
        weight_after_user=79.5,
        fluid_intake_ml_user=0,
        temp_celsius_api=5.0,
    )
    act_cold.calculate_sweat_loss()

    # Moderate (10-20°C) activity using user override temp
    act_mod = Activity(
        user_id=user_id,
        strava_id=2,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        status=ActivityStatus.COMPLETED,
        weight_before_user=80.0,
        weight_after_user=79.2,
        fluid_intake_ml_user=0,
        temp_celsius_api=5.0, # api temp is 5.0, but user override is 15.0
        temp_celsius_user=15.0,
    )
    act_mod.calculate_sweat_loss()

    # Hot (>20°C) activity
    act_hot = Activity(
        user_id=user_id,
        strava_id=3,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        status=ActivityStatus.COMPLETED,
        weight_before_user=80.0,
        weight_after_user=79.0,
        fluid_intake_ml_user=0,
        temp_celsius_api=25.0,
    )
    act_hot.calculate_sweat_loss()

    service = SweatStatisticsService()
    stats = service.calculate_statistics([act_cold, act_mod, act_hot])

    env_breakdown = stats.breakdowns["environment"]
    # Check keys present
    keys = {item.key for item in env_breakdown}
    assert keys == {"cold", "moderate", "hot"}

    cold_stat = next(item for item in env_breakdown if item.key == "cold")
    assert cold_stat.avg_sweat_rate_ml_h == 500.0
    assert cold_stat.activity_count == 1
    assert cold_stat.display_name == "Cold (< 10°C)"

    mod_stat = next(item for item in env_breakdown if item.key == "moderate")
    assert mod_stat.avg_sweat_rate_ml_h == 800.0
    assert mod_stat.activity_count == 1
    assert mod_stat.display_name == "Moderate (10°C - 20°C)"

    hot_stat = next(item for item in env_breakdown if item.key == "hot")
    assert hot_stat.avg_sweat_rate_ml_h == 1000.0
    assert hot_stat.activity_count == 1
    assert hot_stat.display_name == "Hot (> 20°C)"


def test_statistics_service_clothing_breakdown() -> None:
    user_id = uuid4()
    
    act_minimal = Activity(
        user_id=user_id,
        strava_id=1,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        status=ActivityStatus.COMPLETED,
        weight_before_user=80.0,
        weight_after_user=79.1,
        fluid_intake_ml_user=0,
        clothing_index_user=1,
    )
    act_minimal.calculate_sweat_loss()

    act_layers = Activity(
        user_id=user_id,
        strava_id=2,
        activity_type="Run",
        start_date=datetime.now(UTC),
        duration_seconds=3600,
        status=ActivityStatus.COMPLETED,
        weight_before_user=80.0,
        weight_after_user=79.4,
        fluid_intake_ml_user=0,
        clothing_index_user=3,
    )
    act_layers.calculate_sweat_loss()

    service = SweatStatisticsService()
    stats = service.calculate_statistics([act_minimal, act_layers])

    clothing_breakdown = stats.breakdowns["clothing"]
    assert len(clothing_breakdown) == 2

    # Sorted by key ("1", "3")
    assert clothing_breakdown[0].key == "1"
    assert clothing_breakdown[0].display_name == "Minimal"
    assert clothing_breakdown[0].avg_sweat_rate_ml_h == 900.0

    assert clothing_breakdown[1].key == "3"
    assert clothing_breakdown[1].display_name == "Layers"
    assert clothing_breakdown[1].avg_sweat_rate_ml_h == 600.0
