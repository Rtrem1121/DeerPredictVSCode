from __future__ import annotations

import math
from typing import Dict, List, Tuple

from backend.wind_analysis import WindAnalyzer


def _offset_point(lat: float, lon: float, bearing_deg: float, distance_m: float) -> Tuple[float, float]:
    """Offset a lat/lon by distance (m) along bearing (deg)."""

    r = 6371000.0
    bearing = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)

    lat2 = math.asin(math.sin(lat1) * math.cos(distance_m / r) + math.cos(lat1) * math.sin(distance_m / r) * math.cos(bearing))
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(distance_m / r) * math.cos(lat1),
        math.cos(distance_m / r) - math.sin(lat1) * math.sin(lat2),
    )

    return math.degrees(lat2), math.degrees(lon2)


def get_wind_data(lat: float, lon: float) -> Dict[str, float]:
    analyzer = WindAnalyzer()
    wind = analyzer.fetch_current_wind_data(lat, lon)
    return {
        "wind_direction": float(getattr(wind, "direction_degrees", 270.0)),
        "wind_speed": float(getattr(wind, "speed_mph", 5.0)),
    }


def best_stand_for_winds(
    lat: float,
    lon: float,
    wind_from_deg: float,
    distance_m: float = 80.0,
) -> Dict[str, float]:
    """Return a stand offset that keeps scent blowing away from the movement line."""

    downwind_bearing = (wind_from_deg + 180.0) % 360.0
    s_lat, s_lon = _offset_point(lat, lon, downwind_bearing, distance_m)
    return {
        "stand_lat": s_lat,
        "stand_lon": s_lon,
        "wind_from_deg": float(wind_from_deg),
        "wind_to_deg": float(downwind_bearing),
        "offset_m": float(distance_m),
    }


def build_wind_options(
    lat: float,
    lon: float,
    season: str,
    distance_m: float = 80.0,
    wind_direction_deg: float | None = None,
) -> List[Dict[str, float]]:
    wind_data = {"wind_direction": wind_direction_deg} if wind_direction_deg is not None else get_wind_data(lat, lon)
    primary = best_stand_for_winds(lat, lon, float(wind_data["wind_direction"]), distance_m)

    if season in {"rut", "pre_rut", "post_rut", "peak_rut", "seeking"}:
        alternates = [225.0, 270.0, 315.0]
    else:
        alternates = [180.0, 225.0, 270.0]

    options = [primary]
    for wd in alternates:
        if abs(wd - primary["wind_from_deg"]) < 5:
            continue
        options.append(best_stand_for_winds(lat, lon, wd, distance_m))

    return options
