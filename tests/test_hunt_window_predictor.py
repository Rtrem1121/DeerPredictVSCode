from datetime import datetime, timedelta

from backend.hunt_window.hunt_window_predictor import HuntWindowPredictor


def _build_weather_payload(start: datetime) -> dict:
    times = [(start + timedelta(hours=i)).isoformat() for i in range(0, 8)]
    temperatures = [55, 52, 49, 46, 43, 42, 42, 41]
    pressures = [29.80, 29.85, 29.92, 30.00, 30.05, 30.06, 30.08, 30.08]
    wind_speeds = [7, 6, 5, 4.5, 4, 3.8, 3.5, 3.2]
    wind_directions = [300, 305, 312, 318, 320, 322, 325, 330]
    return {
        "temperature": temperatures[0],
        "pressure": pressures[0],
        "hourly_forecast": {
            "time": times,
            "temperature_f": temperatures,
            "pressure_inhg": pressures,
            "wind_speed_mph": wind_speeds,
            "wind_direction_deg": wind_directions,
        },
        "pressure_trend": {"trend": "rising", "change_rate": 0.18},
        "wind_trend": {"direction_shift": 35, "speed_trend": "decreasing"},
    }


def test_hunt_window_predictor_identifies_priority_window():
    start_time = datetime(2025, 9, 25, 16, 0)
    weather_data = _build_weather_payload(start_time)

    stand_profiles = [
        {
            "id": "ridge_sanctuary",
            "name": "Ridge Sanctuary Bench",
            "strategy_match": "Travel Corridor Stand",
            "preferred_winds": [{"direction": "NW", "tolerance": 20}],
            "max_gust_mph": 10,
        }
    ]

    predictor = HuntWindowPredictor(stand_profiles=stand_profiles)

    stand_recs = [
        {
            "type": "Travel Corridor Stand",
            "confidence": 80.0,
            "reasoning": "Baseline test stand",
        }
    ]

    thermal_analysis = {"direction": "downslope", "strength_scale": 6.0}

    evaluation = predictor.evaluate(
        weather_data,
        stand_recommendations=stand_recs,
        thermal_analysis=thermal_analysis,
        current_time=start_time,
    )

    assert evaluation.windows, "Expected at least one hunt window"
    window = evaluation.windows[0]
    assert window.stand_id == "ridge_sanctuary"
    assert "cold_front" in window.trigger_summary
    assert stand_recs[0]["confidence"] > 80.0, "Stand confidence should be boosted"
    assert "wind_credibility" in stand_recs[0], "Wind credibility metadata should be attached"
    status = evaluation.stand_status["ridge_sanctuary"]
    assert status.triggers_met, "Stand status should record trigger alignment"
