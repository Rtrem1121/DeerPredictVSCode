"""Forecast-driven hunt window predictor with stand wind credibility scoring."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence

logger = logging.getLogger(__name__)

CARDINAL_TO_DEGREES: Dict[str, float] = {
    "N": 0.0,
    "NNE": 22.5,
    "NE": 45.0,
    "ENE": 67.5,
    "E": 90.0,
    "ESE": 112.5,
    "SE": 135.0,
    "SSE": 157.5,
    "S": 180.0,
    "SSW": 202.5,
    "SW": 225.0,
    "WSW": 247.5,
    "W": 270.0,
    "WNW": 292.5,
    "NW": 315.0,
    "NNW": 337.5,
}

DEFAULT_SETTINGS: Dict[str, float] = {
    "cold_front_temp_drop": 10.0,
    "pressure_surge_threshold": 0.15,
    "calm_wind_threshold": 5.0,
    "thermal_temp_change_window": 4.0,
    "direction_tolerance_default": 25.0,
    "priority_boost_base": 8.0,
    "confidence_floor": 0.65,
}


@dataclass
class WindPreference:
    """Preferred wind direction for a stand."""

    direction_label: str
    degrees: float
    tolerance: float

    @classmethod
    def from_dict(cls, raw: Dict[str, Any], default_tolerance: float) -> "WindPreference":
        direction = str(raw.get("direction", "")).strip().upper()
        if not direction:
            raise ValueError("Wind preference missing direction label")
        degrees = _parse_direction_to_degrees(direction)
        tolerance = float(raw.get("tolerance", default_tolerance))
        return cls(direction_label=direction, degrees=degrees, tolerance=tolerance)


@dataclass
class StandWindProfile:
    """Hunter-configured stand profile with trusted winds."""

    id: str
    name: str
    preferred_winds: List[WindPreference]
    max_gust_mph: Optional[float] = None
    strategy_match: Optional[str] = None
    terrain_context: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, raw: Dict[str, Any], default_tolerance: float) -> "StandWindProfile":
        stand_id = str(raw.get("id"))
        name = str(raw.get("name", stand_id)).strip() if stand_id else "Unnamed Stand"
        if not stand_id:
            raise ValueError("Stand profile requires an 'id'")
        raw_preferences = raw.get("preferred_winds", [])
        if not isinstance(raw_preferences, Sequence) or not raw_preferences:
            raise ValueError(f"Stand profile '{stand_id}' must define at least one preferred wind")
        preferences = [
            WindPreference.from_dict(pref, default_tolerance)
            for pref in raw_preferences
            if isinstance(pref, dict)
        ]
        if not preferences:
            raise ValueError(f"Stand profile '{stand_id}' contains no valid wind preferences")
        max_gust = raw.get("max_gust_mph")
        return cls(
            id=stand_id,
            name=name,
            preferred_winds=preferences,
            max_gust_mph=float(max_gust) if max_gust is not None else None,
            strategy_match=raw.get("strategy_match"),
            terrain_context=raw.get("terrain_context"),
            notes=raw.get("notes"),
        )


@dataclass
class ForecastPoint:
    time: datetime
    temperature: float
    pressure: float
    wind_speed: float
    wind_direction: float


@dataclass
class AlignmentCandidate:
    time: datetime
    alignment_score: float
    wind_speed: float
    wind_direction: float
    thermal_stable: bool
    cold_front_ready: bool

    @property
    def triggers_met(self) -> List[str]:
        triggers = []
        if self.cold_front_ready:
            triggers.append("cold_front")
        if self.alignment_score > 0:
            triggers.append("wind_alignment")
        if self.thermal_stable:
            triggers.append("thermal_stability")
        return triggers


@dataclass
class HuntWindow:
    stand_id: str
    stand_name: str
    window_start: datetime
    window_end: datetime
    priority_boost: float
    confidence: float
    trigger_summary: List[str]
    dominant_wind: str
    notes: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "stand_id": self.stand_id,
            "stand_name": self.stand_name,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "priority_boost": round(self.priority_boost, 2),
            "confidence": round(self.confidence, 3),
            "trigger_summary": self.trigger_summary,
            "dominant_wind": self.dominant_wind,
            "notes": self.notes,
        }


@dataclass
class StandWindStatus:
    stand_id: str
    stand_name: str
    match_key: Optional[str]
    is_green_now: bool
    alignment_score_now: float
    preferred_directions: List[str]
    priority_boost: float
    triggers_met: List[str]
    best_alignment_time: Optional[datetime]
    notes: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "stand_id": self.stand_id,
            "stand_name": self.stand_name,
            "match_key": self.match_key,
            "is_green_now": self.is_green_now,
            "alignment_score_now": round(self.alignment_score_now, 3),
            "preferred_directions": self.preferred_directions,
            "priority_boost": round(self.priority_boost, 2),
            "triggers_met": self.triggers_met,
            "best_alignment_time": self.best_alignment_time.isoformat() if self.best_alignment_time else None,
            "notes": self.notes,
        }


@dataclass
class HuntWindowEvaluation:
    windows: List[HuntWindow] = field(default_factory=list)
    stand_status: Dict[str, StandWindStatus] = field(default_factory=dict)

    def windows_as_dict(self) -> List[Dict[str, Any]]:
        return [window.as_dict() for window in self.windows]

    def stand_status_as_dict(self) -> Dict[str, Dict[str, Any]]:
        return {stand_id: status.as_dict() for stand_id, status in self.stand_status.items()}


class HuntWindowPredictor:
    """Evaluate forecast data to surface cold-front driven hunt windows."""

    def __init__(self, stand_profiles: Optional[Iterable[Dict[str, Any]]] = None, settings: Optional[Dict[str, Any]] = None):
        merged_settings = DEFAULT_SETTINGS.copy()
        if settings:
            merged_settings.update({k: float(v) for k, v in settings.items() if isinstance(v, (int, float))})
        self.settings = merged_settings
        default_tol = self.settings["direction_tolerance_default"]
        profiles = list(stand_profiles or [])
        self._profiles: List[StandWindProfile] = []
        for raw in profiles:
            try:
                profile = StandWindProfile.from_dict(raw, default_tol)
                self._profiles.append(profile)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Skipping stand profile due to error: %s", exc)

    @classmethod
    def from_config(cls, config_manager: Any) -> "HuntWindowPredictor":
        return cls(
            stand_profiles=config_manager.get_stand_profiles(),
            settings=config_manager.get_hunt_window_settings(),
        )

    def refresh_from_config(self, config_manager: Any) -> None:
        self.__init__(
            stand_profiles=config_manager.get_stand_profiles(),
            settings=config_manager.get_hunt_window_settings(),
        )

    def evaluate(
        self,
        weather_data: Dict[str, Any],
        stand_recommendations: Optional[List[Dict[str, Any]]] = None,
        thermal_analysis: Optional[Dict[str, Any]] = None,
        current_time: Optional[datetime] = None,
    ) -> HuntWindowEvaluation:
        if not self._profiles:
            return HuntWindowEvaluation()

        now = current_time or datetime.now()
        forecast_points = self._build_forecast_points(weather_data, now)
        if not forecast_points:
            return HuntWindowEvaluation()

        cold_front_info = self._detect_cold_front(weather_data, forecast_points)
        evaluation = HuntWindowEvaluation()

        first_point = forecast_points[0]
        prev_point: Optional[ForecastPoint] = None

        for profile in self._profiles:
            candidates: List[AlignmentCandidate] = []
            for point in forecast_points:
                if point.time > now + timedelta(hours=24):
                    break
                alignment_score = self._calculate_alignment(profile, point.wind_direction)
                if alignment_score <= 0:
                    prev_point = point
                    continue
                if profile.max_gust_mph is not None and point.wind_speed > profile.max_gust_mph:
                    prev_point = point
                    continue
                thermal_stable = self._is_thermal_stable(point, prev_point, thermal_analysis)
                cold_front_ready = cold_front_info["triggered"] and self._is_within_front_window(point.time, cold_front_info)
                candidates.append(
                    AlignmentCandidate(
                        time=point.time,
                        alignment_score=alignment_score,
                        wind_speed=point.wind_speed,
                        wind_direction=point.wind_direction,
                        thermal_stable=thermal_stable,
                        cold_front_ready=cold_front_ready,
                    )
                )
                prev_point = point

            status = self._build_stand_status(profile, candidates, first_point)
            evaluation.stand_status[profile.id] = status

            window = self._build_hunt_window(profile, candidates, cold_front_info)
            if window:
                evaluation.windows.append(window)

        self._apply_priority_to_recommendations(evaluation, stand_recommendations)
        return evaluation

    def _build_forecast_points(self, weather_data: Dict[str, Any], now: datetime) -> List[ForecastPoint]:
        hourly = weather_data.get("hourly_forecast") or {}
        times = hourly.get("time", [])
        temps = hourly.get("temperature_f", [])
        pressures = hourly.get("pressure_inhg", [])
        wind_speeds = hourly.get("wind_speed_mph", [])
        wind_dirs = hourly.get("wind_direction_deg", [])
        length = min(len(times), len(temps), len(pressures), len(wind_speeds), len(wind_dirs))
        points: List[ForecastPoint] = []
        for idx in range(length):
            try:
                timestamp = datetime.fromisoformat(str(times[idx]))
            except ValueError:
                continue
            if timestamp < now - timedelta(hours=1):
                continue
            points.append(
                ForecastPoint(
                    time=timestamp,
                    temperature=float(temps[idx]),
                    pressure=float(pressures[idx]),
                    wind_speed=float(wind_speeds[idx]),
                    wind_direction=float(wind_dirs[idx]),
                )
            )
        return points

    def _detect_cold_front(self, weather_data: Dict[str, Any], forecast_points: Sequence[ForecastPoint]) -> Dict[str, Any]:
        if not forecast_points:
            return {"triggered": False}
        current_temp = float(weather_data.get("temperature", forecast_points[0].temperature))
        current_pressure = float(weather_data.get("pressure", forecast_points[0].pressure))
        horizon = [p for p in forecast_points if p.time <= forecast_points[0].time + timedelta(hours=24)]
        if not horizon:
            return {"triggered": False}
        min_temp_point = min(horizon, key=lambda p: p.temperature)
        max_pressure_point = max(horizon, key=lambda p: p.pressure)
        temp_drop = current_temp - min_temp_point.temperature
        pressure_rise = max_pressure_point.pressure - current_pressure
        triggered = temp_drop >= self.settings["cold_front_temp_drop"] or pressure_rise >= self.settings["pressure_surge_threshold"]
        return {
            "triggered": triggered,
            "temp_drop": temp_drop,
            "pressure_rise": pressure_rise,
            "temp_event_time": min_temp_point.time,
            "pressure_event_time": max_pressure_point.time,
        }

    def _calculate_alignment(self, profile: StandWindProfile, forecast_degrees: float) -> float:
        best_score = 0.0
        for pref in profile.preferred_winds:
            diff = angular_difference(pref.degrees, forecast_degrees)
            if diff <= pref.tolerance:
                score = 1.0 - (diff / max(pref.tolerance, 1.0))
                if score > best_score:
                    best_score = score
        return best_score

    def _is_thermal_stable(
        self,
        point: ForecastPoint,
        prev_point: Optional[ForecastPoint],
        thermal_analysis: Optional[Dict[str, Any]],
    ) -> bool:
        if point.wind_speed > self.settings["calm_wind_threshold"]:
            return False
        if prev_point:
            temp_delta = abs(point.temperature - prev_point.temperature)
            if temp_delta > self.settings["thermal_temp_change_window"]:
                return False
        hour = point.time.hour
        thermal_hours = (5 <= hour <= 9) or (17 <= hour <= 21)
        if not thermal_hours:
            return False
        if not thermal_analysis:
            return True
        direction = thermal_analysis.get("direction")
        strength = float(thermal_analysis.get("strength_scale", 0))
        if direction in {"upslope", "downslope"} and strength >= 4.0:
            return True
        return strength >= 2.5

    def _is_within_front_window(self, candidate_time: datetime, cold_front_info: Dict[str, Any]) -> bool:
        if not cold_front_info.get("triggered"):
            return False
        event_times = [
            cold_front_info.get("temp_event_time"),
            cold_front_info.get("pressure_event_time"),
        ]
        event_times = [t for t in event_times if isinstance(t, datetime)]
        if not event_times:
            return True
        earliest = min(event_times)
        window_start = earliest - timedelta(hours=6)
        window_end = earliest + timedelta(hours=12)
        return window_start <= candidate_time <= window_end

    def _build_hunt_window(
        self,
        profile: StandWindProfile,
        candidates: Sequence[AlignmentCandidate],
        cold_front_info: Dict[str, Any],
    ) -> Optional[HuntWindow]:
        viable = [c for c in candidates if c.cold_front_ready and c.thermal_stable and c.alignment_score > 0]
        if not viable:
            return None
        best = max(viable, key=lambda c: (c.alignment_score, -c.wind_speed))
        boost = self.settings["priority_boost_base"] * best.alignment_score
        confidence = min(0.95, max(self.settings["confidence_floor"], 0.55 + 0.3 * best.alignment_score))
        wind_label = degrees_to_cardinal(best.wind_direction)
        notes = f"{wind_label} wind at {best.wind_speed:.1f} mph; thermals stable"
        triggers = ["cold_front", "wind_alignment", "thermal_stability"]
        window_end = best.time + timedelta(hours=2)
        return HuntWindow(
            stand_id=profile.id,
            stand_name=profile.name,
            window_start=best.time,
            window_end=window_end,
            priority_boost=boost,
            confidence=confidence,
            trigger_summary=triggers,
            dominant_wind=wind_label,
            notes=notes,
        )

    def _build_stand_status(
        self,
        profile: StandWindProfile,
        candidates: Sequence[AlignmentCandidate],
        first_point: ForecastPoint,
    ) -> StandWindStatus:
        alignment_now = self._calculate_alignment(profile, first_point.wind_direction)
        is_green_now = alignment_now > 0 and (profile.max_gust_mph is None or first_point.wind_speed <= profile.max_gust_mph)
        best_candidate = max(candidates, key=lambda c: c.alignment_score, default=None)
        boost = 0.0
        triggers: List[str] = []
        best_time = None
        if best_candidate and best_candidate.alignment_score > 0:
            boost = self.settings["priority_boost_base"] * best_candidate.alignment_score
            triggers = best_candidate.triggers_met
            best_time = best_candidate.time
        return StandWindStatus(
            stand_id=profile.id,
            stand_name=profile.name,
            match_key=profile.strategy_match,
            is_green_now=is_green_now,
            alignment_score_now=alignment_now,
            preferred_directions=[pref.direction_label for pref in profile.preferred_winds],
            priority_boost=boost,
            triggers_met=triggers,
            best_alignment_time=best_time,
            notes=profile.notes,
        )

    def _apply_priority_to_recommendations(
        self,
        evaluation: HuntWindowEvaluation,
        stand_recommendations: Optional[List[Dict[str, Any]]],
    ) -> None:
        if not stand_recommendations:
            return
        status_by_match: Dict[str, StandWindStatus] = {
            status.match_key: status
            for status in evaluation.stand_status.values()
            if status.match_key
        }
        status_by_id = evaluation.stand_status
        for stand in stand_recommendations:
            match_key = stand.get("type")
            stand_id = stand.get("stand_id") or stand.get("id")
            status = None
            if match_key and match_key in status_by_match:
                status = status_by_match[match_key]
            elif stand_id and stand_id in status_by_id:
                status = status_by_id[stand_id]
            if not status:
                continue
            stand.setdefault("wind_credibility", {})
            stand["wind_credibility"].update(status.as_dict())
            if status.priority_boost > 0:
                base_confidence = float(stand.get("confidence", 0))
                stand["confidence"] = min(99.0, base_confidence + status.priority_boost)
                tags = stand.setdefault("context_tags", [])
                if "hunt_window_priority" not in tags:
                    tags.append("hunt_window_priority")


def _parse_direction_to_degrees(direction: str) -> float:
    if direction in CARDINAL_TO_DEGREES:
        return CARDINAL_TO_DEGREES[direction]
    try:
        return float(direction)
    except ValueError as exc:
        raise ValueError(f"Unsupported wind direction '{direction}'") from exc


def angular_difference(deg_a: float, deg_b: float) -> float:
    diff = abs(deg_a - deg_b) % 360
    return diff if diff <= 180 else 360 - diff


def degrees_to_cardinal(degrees: float) -> str:
    degrees = degrees % 360
    best_label = "N"
    smallest_diff = math.inf
    for label, target in CARDINAL_TO_DEGREES.items():
        diff = angular_difference(target, degrees)
        if diff < smallest_diff:
            smallest_diff = diff
            best_label = label
    return best_label
