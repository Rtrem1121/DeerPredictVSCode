"""Polygon sampling and grid-generation utilities for property hotspot analysis."""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple


def _wrap_lon(lon: float) -> float:
    return ((lon + 180.0) % 360.0) - 180.0


def points_center(points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Return the centroid (lat, lon) of a set of points.  Falls back to Vermont default."""
    if not points:
        return 44.0, -72.5
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def try_make_polygon(corners: List[Tuple[float, float]]):
    """Build a shapely Polygon from (lat, lon) corners.  Returns None if shapely is unavailable."""
    try:
        from shapely.geometry import Polygon  # type: ignore

        if len(corners) < 3:
            return None
        ring = [(lon, lat) for lat, lon in corners]
        return Polygon(ring)
    except Exception:
        return None


def point_in_polygon(lat: float, lon: float, polygon) -> bool:
    """Return True when *lat/lon* lies inside *polygon* (or polygon is None)."""
    if polygon is None:
        return True
    try:
        from shapely.geometry import Point  # type: ignore

        return bool(polygon.contains(Point(lon, lat)) or polygon.touches(Point(lon, lat)))
    except Exception:
        return True


def sample_points_in_polygon(
    corners: List[Tuple[float, float]],
    n: int,
    seed: Optional[int] = None,
) -> List[Tuple[float, float]]:
    """Random-sample *n* points that lie inside the polygon defined by *corners*."""
    if not corners:
        return []

    rng = random.Random(seed)
    lats = [c[0] for c in corners]
    lons = [c[1] for c in corners]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    polygon = try_make_polygon(corners)

    points: List[Tuple[float, float]] = []
    center = points_center(corners)
    points.append(center)

    max_tries = max(2000, n * 200)
    tries = 0
    while len(points) < n and tries < max_tries:
        tries += 1
        lat = rng.uniform(min_lat, max_lat)
        lon = rng.uniform(min_lon, max_lon)
        lon = _wrap_lon(lon)
        if point_in_polygon(lat, lon, polygon):
            points.append((lat, lon))

    return points[:n]


def stable_seed_from_corners(corners: List[Tuple[float, float]]) -> int:
    """Deterministic seed derived from property boundary for reproducible sampling."""
    if not corners:
        return 0
    try:
        import hashlib

        normalized = [(round(lat, 6), round(lon, 6)) for lat, lon in corners]
        payload = "|".join(f"{lat:.6f},{lon:.6f}" for lat, lon in normalized)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)
    except Exception:
        return 0


def generate_grid_points_in_polygon(
    corners: List[Tuple[float, float]],
    target_n: int,
) -> List[Tuple[float, float]]:
    """Generate a dense deterministic grid inside the polygon, returning up to *target_n* points."""
    if not corners:
        return []

    lats = [c[0] for c in corners]
    lons = [c[1] for c in corners]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    polygon = try_make_polygon(corners)

    oversample = 2.0
    grid_size = max(8, int(math.sqrt(max(1, target_n) * oversample)))

    try:
        import numpy as np  # type: ignore

        lat_vals = np.linspace(min_lat, max_lat, grid_size, dtype=float)
        lon_vals = np.linspace(min_lon, max_lon, grid_size, dtype=float)
        inside: List[Tuple[float, float]] = []
        for lat in lat_vals:
            for lon in lon_vals:
                lon_w = _wrap_lon(float(lon))
                lat_f = float(lat)
                if point_in_polygon(lat_f, lon_w, polygon):
                    inside.append((lat_f, lon_w))
    except Exception:
        inside = []
        for i in range(grid_size):
            lat = min_lat + (max_lat - min_lat) * (i / max(1, grid_size - 1))
            for j in range(grid_size):
                lon = min_lon + (max_lon - min_lon) * (j / max(1, grid_size - 1))
                lon = _wrap_lon(lon)
                if point_in_polygon(lat, lon, polygon):
                    inside.append((lat, lon))

    if not inside:
        return []

    center = points_center(corners)
    if center not in inside and point_in_polygon(center[0], center[1], polygon):
        inside.insert(0, center)

    if len(inside) <= target_n:
        return inside
    step = max(1, len(inside) // max(1, target_n))
    sampled = inside[::step][:target_n]
    return sampled
