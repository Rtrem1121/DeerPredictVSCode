"""Evidence cluster framework.

Groups spatially-proximate scouting observations and buck events into
first-class modelling units.  A cluster carries an aggregated weight,
seasonal confidence profile, and evidence-type summary — making it a
stronger input to the corridor engine than isolated waypoints.

Auto-clustering uses DBSCAN (eps=300 m, min_samples=2).  The 300 m
default reflects real property scale where rubs, crossings, and camera
detections along the same corridor can be 200–300 m apart.
Manual overrides let the user name, anchor, and curate clusters.
"""

from __future__ import annotations

import math
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.models.buck_event import BuckEvent
from backend.models.evidence_weights import (
    age_days_from_timestamp,
    compute_evidence_weight,
    maturity_multiplier,
    pattern_bonus,
    source_quality_for_observation,
)
from backend.scouting_models import ObservationType, ScoutingObservation

logger = logging.getLogger(__name__)

# ── Geometry helpers ─────────────────────────────────────────────────────

_EARTH_RADIUS_M = 6_371_000


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in metres between two WGS-84 points."""
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


# ── Season helpers ───────────────────────────────────────────────────────

_SEASON_RANGES: List[Tuple[str, int, int]] = [
    # (season_name, start_month_day, end_month_day) encoded as MMDD ints
    ("early_season", 901, 1015),
    ("pre_rut", 1016, 1031),
    ("rut", 1101, 1130),
    ("post_rut", 1201, 1220),
    ("late_season", 1221, 131),  # wraps into January
]


def _season_for_date(dt: datetime) -> str:
    mmdd = dt.month * 100 + dt.day
    for name, start, end in _SEASON_RANGES:
        if start <= end:
            if start <= mmdd <= end:
                return name
        else:
            # Wrapping range (late_season: Dec 21 → Jan 31)
            if mmdd >= start or mmdd <= end:
                return name
    return "off_season"


# ── Cluster model ────────────────────────────────────────────────────────


class EvidenceCluster(BaseModel):
    """A cluster of spatially-related evidence."""

    cluster_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(default="")
    anchor_lat: float = Field(...)
    anchor_lon: float = Field(...)
    radius_m: float = Field(default=0.0)
    observation_ids: List[str] = Field(default_factory=list)
    buck_event_ids: List[str] = Field(default_factory=list)
    combined_weight: float = Field(default=0.0)
    seasonal_confidence: Dict[str, float] = Field(default_factory=dict)
    evidence_types: List[str] = Field(default_factory=list)
    notes: str = Field(default="")

    # ── serialisation ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "EvidenceCluster":
        return cls(**data)


# ── Point wrapper (internal) ─────────────────────────────────────────────

class _EvidencePoint:
    """Thin wrapper unifying observations and buck events for clustering."""
    __slots__ = ("lat", "lon", "timestamp", "obs_type", "ev_id", "kind",
                 "is_mature", "is_target", "is_repeated", "is_daylight",
                 "is_dated", "confidence")

    def __init__(
        self,
        lat: float,
        lon: float,
        timestamp: datetime,
        obs_type: ObservationType,
        ev_id: str,
        kind: str,  # "observation" | "buck_event"
        *,
        is_mature: bool = False,
        is_target: bool = False,
        is_repeated: bool = False,
        is_daylight: bool = False,
        is_dated: bool = True,
        confidence: int = 6,
    ):
        self.lat = lat
        self.lon = lon
        self.timestamp = timestamp
        self.obs_type = obs_type
        self.ev_id = ev_id
        self.kind = kind
        self.is_mature = is_mature
        self.is_target = is_target
        self.is_repeated = is_repeated
        self.is_daylight = is_daylight
        self.is_dated = is_dated
        self.confidence = confidence


def _point_from_observation(obs: ScoutingObservation) -> _EvidencePoint:
    has_mature = False
    is_target = False
    if obs.observation_type == ObservationType.TRAIL_CAMERA and obs.camera_details:
        has_mature = obs.camera_details.mature_buck_seen
    return _EvidencePoint(
        lat=obs.lat,
        lon=obs.lon,
        timestamp=obs.timestamp,
        obs_type=obs.observation_type,
        ev_id=obs.id or "",
        kind="observation",
        is_mature=has_mature,
        is_target=is_target,
        is_dated=True,
        confidence=obs.confidence,
    )


def _point_from_buck_event(ev: BuckEvent) -> _EvidencePoint:
    return _EvidencePoint(
        lat=ev.lat,
        lon=ev.lon,
        timestamp=ev.timestamp,
        obs_type=ObservationType.TRAIL_CAMERA,
        ev_id=ev.event_id,
        kind="buck_event",
        is_mature=ev.is_mature,
        is_target=ev.target_buck,
        is_repeated=ev.repeat_location,
        is_daylight=ev.daylight or False,
        is_dated=True,
        confidence=ev.confidence,
    )


# ── DBSCAN clustering ───────────────────────────────────────────────────

def _dbscan_cluster(
    points: Sequence[_EvidencePoint],
    eps_m: float = 75.0,
    min_samples: int = 2,
) -> List[List[int]]:
    """Simple DBSCAN on lat/lon points using haversine distance.

    Returns a list of clusters, each cluster being a list of point indices.
    Noise points (not in any cluster) are omitted.
    """
    n = len(points)
    labels = [-1] * n
    cluster_id = 0

    def _neighbors(idx: int) -> List[int]:
        p = points[idx]
        return [
            j for j in range(n)
            if j != idx and _haversine_m(p.lat, p.lon, points[j].lat, points[j].lon) <= eps_m
        ]

    visited = [False] * n
    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True
        nbrs = _neighbors(i)
        if len(nbrs) < min_samples - 1:
            continue
        # Expand cluster
        labels[i] = cluster_id
        seed_set = list(nbrs)
        j = 0
        while j < len(seed_set):
            q = seed_set[j]
            if not visited[q]:
                visited[q] = True
                q_nbrs = _neighbors(q)
                if len(q_nbrs) >= min_samples - 1:
                    seed_set.extend(q_nbrs)
            if labels[q] == -1:
                labels[q] = cluster_id
            j += 1
        cluster_id += 1

    # Group indices by label
    clusters: Dict[int, List[int]] = {}
    for idx, lbl in enumerate(labels):
        if lbl >= 0:
            clusters.setdefault(lbl, []).append(idx)
    return list(clusters.values())


# ── Cluster builder ──────────────────────────────────────────────────────

def build_clusters(
    observations: Sequence[ScoutingObservation],
    buck_events: Sequence[BuckEvent],
    *,
    eps_m: float = 300.0,
    min_samples: int = 2,
    now: Optional[datetime] = None,
) -> List[EvidenceCluster]:
    """Auto-cluster observations + buck events and return scored clusters."""
    if now is None:
        now = datetime.now(timezone.utc)

    # Convert everything to _EvidencePoint
    points: List[_EvidencePoint] = []
    for obs in observations:
        points.append(_point_from_observation(obs))
    for ev in buck_events:
        points.append(_point_from_buck_event(ev))

    if len(points) < min_samples:
        return []

    raw_clusters = _dbscan_cluster(points, eps_m=eps_m, min_samples=min_samples)
    result: List[EvidenceCluster] = []

    for member_indices in raw_clusters:
        members = [points[i] for i in member_indices]
        cluster = _score_cluster(members, now=now)
        result.append(cluster)

    # Sort by combined weight descending
    result.sort(key=lambda c: c.combined_weight, reverse=True)
    return result


def _score_cluster(
    members: List[_EvidencePoint],
    *,
    now: datetime,
) -> EvidenceCluster:
    """Compute anchor, radius, weight, and seasonal profile for a cluster."""
    # Centroid
    avg_lat = sum(p.lat for p in members) / len(members)
    avg_lon = sum(p.lon for p in members) / len(members)

    # Radius
    radius = max(
        (_haversine_m(avg_lat, avg_lon, p.lat, p.lon) for p in members),
        default=0.0,
    )

    # Per-member weights
    obs_ids: List[str] = []
    event_ids: List[str] = []
    ev_types: set = set()
    member_weights: List[float] = []
    season_buckets: Dict[str, List[float]] = {}
    has_repeated = any(p.is_repeated for p in members)
    has_daylight = any(p.is_daylight for p in members)
    multi_type = len({p.obs_type for p in members}) > 1

    for p in members:
        if p.kind == "observation":
            obs_ids.append(p.ev_id)
        else:
            event_ids.append(p.ev_id)

        ev_types.add(p.obs_type.value)
        age = age_days_from_timestamp(p.timestamp, now=now)
        sq = source_quality_for_observation(
            p.obs_type,
            has_mature_buck=p.is_mature,
            is_target_buck=p.is_target,
            is_dated=p.is_dated,
        )
        mm = maturity_multiplier(
            is_mature=p.is_mature,
            is_target=p.is_target,
            is_repeated=p.is_repeated,
        )
        pf = {
            "repeated": has_repeated,
            "daylight": has_daylight,
            "multi_evidence": multi_type,
        }
        w = compute_evidence_weight(sq, age, mm, pf)
        member_weights.append(w)

        season = _season_for_date(p.timestamp)
        season_buckets.setdefault(season, []).append(w)

    # Cluster combined weight: sum with sqrt-diminishing returns above 3 members
    sorted_w = sorted(member_weights, reverse=True)
    combined = 0.0
    for i, w in enumerate(sorted_w):
        if i < 3:
            combined += w
        else:
            combined += w / math.sqrt(i - 1)
    # Normalise to 0–1 (cluster weight can exceed 1.0 for very strong clusters)
    combined = round(min(combined, 1.0 * len(sorted_w)), 4)

    # Seasonal confidence: average weight per season bucket
    seasonal = {}
    for season, weights in season_buckets.items():
        seasonal[season] = round(sum(weights) / len(weights), 4)

    return EvidenceCluster(
        anchor_lat=round(avg_lat, 6),
        anchor_lon=round(avg_lon, 6),
        radius_m=round(radius, 1),
        observation_ids=obs_ids,
        buck_event_ids=event_ids,
        combined_weight=round(combined, 4),
        seasonal_confidence=seasonal,
        evidence_types=sorted(ev_types),
    )
