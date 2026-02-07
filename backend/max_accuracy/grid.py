from __future__ import annotations

import math
from typing import Callable, List, Optional, Tuple


def _wrap_lon(lon: float) -> float:
    if lon > 180:
        return lon - 360
    if lon < -180:
        return lon + 360
    return lon


def _try_make_polygon(corners: List[Tuple[float, float]]):
    try:
        from shapely.geometry import Polygon  # type: ignore

        ring = [(lon, lat) for lat, lon in corners]
        return Polygon(ring)
    except Exception:
        return None


def _point_in_polygon(lat: float, lon: float, polygon) -> bool:
    if polygon is None:
        return True
    try:
        from shapely.geometry import Point  # type: ignore

        return bool(polygon.contains(Point(lon, lat)) or polygon.touches(Point(lon, lat)))
    except Exception:
        return True


def generate_dense_grid(
    corners: List[Tuple[float, float]],
    spacing_m: int,
    progress_callback: Optional[Callable[[int, int, int], None]] = None,
) -> List[Tuple[float, float]]:
    """Generate a dense grid of points inside polygon using meter spacing."""

    if not corners:
        return []

    lats = [c[0] for c in corners]
    lons = [c[1] for c in corners]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Approximate meters per degree.
    lat_center = (min_lat + max_lat) / 2.0
    meters_per_deg_lat = 111_132.0
    meters_per_deg_lon = 111_320.0 * math.cos(math.radians(lat_center))

    if meters_per_deg_lon <= 0:
        meters_per_deg_lon = 1e-6

    lat_step = spacing_m / meters_per_deg_lat
    lon_step = spacing_m / meters_per_deg_lon

    polygon = _try_make_polygon(corners)

    points: List[Tuple[float, float]] = []
    total_rows = int(((max_lat - min_lat) / lat_step)) + 1 if lat_step > 0 else 0
    row_idx = 0
    lat = min_lat
    while lat <= max_lat:
        lon = min_lon
        while lon <= max_lon:
            lon_w = _wrap_lon(lon)
            if _point_in_polygon(lat, lon_w, polygon):
                points.append((lat, lon_w))
            lon += lon_step
        row_idx += 1
        if progress_callback and row_idx % 25 == 0:
            progress_callback(row_idx, total_rows, len(points))
        lat += lat_step

    return points
