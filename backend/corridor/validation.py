"""Corridor validation — backtest modeled corridors against real observations.

Provides metrics for measuring how well predicted corridors explain field
evidence:
- Event-to-corridor distance (how far are real sightings from corridors?)
- Hit rate (% of events within N meters of a corridor)
- Corridor confidence calibration (do high-density cells really predict more?)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from backend.utils.geo import haversine


@dataclass
class ValidationResult:
    """Summary of corridor vs. observations comparison."""

    total_events: int
    events_within_50m: int
    events_within_100m: int
    events_within_200m: int
    hit_rate_50m: float
    hit_rate_100m: float
    hit_rate_200m: float
    mean_distance_m: float
    median_distance_m: float
    per_event: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_events": self.total_events,
            "events_within_50m": self.events_within_50m,
            "events_within_100m": self.events_within_100m,
            "events_within_200m": self.events_within_200m,
            "hit_rate_50m": round(self.hit_rate_50m, 3),
            "hit_rate_100m": round(self.hit_rate_100m, 3),
            "hit_rate_200m": round(self.hit_rate_200m, 3),
            "mean_distance_m": round(self.mean_distance_m, 1),
            "median_distance_m": round(self.median_distance_m, 1),
            "per_event": self.per_event,
        }


def validate_corridors(
    corridor_data: Dict[str, Any],
    events: List[Dict[str, Any]],
) -> ValidationResult:
    """Compare real observation/buck events against modeled corridor polylines.

    Parameters
    ----------
    corridor_data : dict from ``CorridorResult.to_dict()`` — must contain
        ``polylines`` (list of lat/lon point lists).
    events : list of dicts each with ``lat``, ``lon``, and optionally
        ``name`` / ``timestamp``.

    Returns
    -------
    ``ValidationResult`` with per-event distances and aggregate hit rates.
    """
    polylines = corridor_data.get("polylines", [])
    corridor_points: List[Tuple[float, float]] = []
    for pl in polylines:
        for pt in pl:
            if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                corridor_points.append((float(pt[0]), float(pt[1])))

    per_event: List[Dict[str, Any]] = []
    distances: List[float] = []

    for ev in events:
        ev_lat = ev.get("lat")
        ev_lon = ev.get("lon")
        if ev_lat is None or ev_lon is None:
            continue

        if not corridor_points:
            per_event.append({
                "lat": ev_lat, "lon": ev_lon,
                "name": ev.get("name", ""),
                "min_distance_m": None,
                "within_50m": False,
                "within_100m": False,
                "within_200m": False,
            })
            continue

        min_dist = min(
            haversine(float(ev_lat), float(ev_lon), clat, clon)
            for clat, clon in corridor_points
        )
        distances.append(min_dist)
        per_event.append({
            "lat": float(ev_lat),
            "lon": float(ev_lon),
            "name": ev.get("name", ""),
            "min_distance_m": round(min_dist, 1),
            "within_50m": min_dist <= 50,
            "within_100m": min_dist <= 100,
            "within_200m": min_dist <= 200,
        })

    n = max(1, len(distances))
    sorted_d = sorted(distances) if distances else [0]
    median = sorted_d[len(sorted_d) // 2] if sorted_d else 0

    return ValidationResult(
        total_events=len(distances),
        events_within_50m=sum(1 for d in distances if d <= 50),
        events_within_100m=sum(1 for d in distances if d <= 100),
        events_within_200m=sum(1 for d in distances if d <= 200),
        hit_rate_50m=sum(1 for d in distances if d <= 50) / n,
        hit_rate_100m=sum(1 for d in distances if d <= 100) / n,
        hit_rate_200m=sum(1 for d in distances if d <= 200) / n,
        mean_distance_m=sum(distances) / n if distances else 0,
        median_distance_m=median,
        per_event=per_event,
    )
