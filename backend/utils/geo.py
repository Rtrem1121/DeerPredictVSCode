"""Shared geographic utility functions.

Single source of truth for haversine, bearing, angular difference,
cardinal directions, and point-in-polygon calculations used across
the prediction pipeline and max-accuracy modules.
"""

from __future__ import annotations

import math
from typing import List, Tuple


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in meters between two lat/lon points."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_between(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return bearing in degrees (0-360) from point 1 to point 2."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    y = math.sin(dlam) * math.cos(phi2)
    x = (
        math.cos(phi1) * math.sin(phi2)
        - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    )
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def angular_diff(a: float, b: float) -> float:
    """Smallest absolute angular difference between two bearings (0-180)."""
    diff = abs(a - b) % 360
    return diff if diff <= 180 else 360 - diff


def bearing_to_cardinal(bearing: float) -> str:
    """Convert bearing degrees to 8-point cardinal direction."""
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((bearing + 22.5) % 360 / 45)
    return dirs[idx]


def point_in_polygon(
    lat: float,
    lon: float,
    polygon: List[Tuple[float, float]],
) -> bool:
    """Ray-casting point-in-polygon test for (lat, lon) coords."""
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        yi, xi = polygon[i]
        yj, xj = polygon[j]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside
