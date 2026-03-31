"""Unified evidence weighting model.

Produces a single ``combined_weight`` (0.0–1.0) for any piece of
scouting evidence — observations, buck events, or mixed clusters —
by composing four orthogonal dimensions:

1. **Source quality** — intrinsic trustworthiness of the evidence type.
2. **Recency** — exponential-style decay favouring current-season data.
3. **Maturity** — boost for confirmed mature / target buck sign.
4. **Pattern bonus** — additive reward for repeated, daylight, or
   multi-evidence co-occurrence at the same location.

Usage
-----
>>> from backend.models.evidence_weights import compute_evidence_weight
>>> w = compute_evidence_weight(
...     source_quality=0.85,
...     age_days=10,
...     maturity_multiplier=1.2,
...     pattern_flags={"repeated": True, "daylight": True},
... )
>>> 0.0 <= w <= 1.0
True
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional, Sequence

from backend.scouting_models import ObservationType


# ── Source-quality baselines ─────────────────────────────────────────────
# These represent the intrinsic trustworthiness of an evidence source on
# a 0-1 scale *before* recency or maturity adjustments.

SOURCE_QUALITY: Dict[str, float] = {
    # Camera / direct detections
    "camera_target_buck": 1.00,
    "camera_mature_buck": 0.90,
    "camera_generic_buck": 0.70,
    "camera_doe_spike": 0.50,
    "camera_no_deer": 0.20,
    # Field sign
    "fresh_rub": 0.85,
    "fresh_scrape": 0.80,
    "fresh_bed_with_hair": 0.80,
    "rub_line": 0.75,
    "bedding_area": 0.70,
    "feeding_sign": 0.60,
    "deer_tracks": 0.55,
    "deer_sighting": 0.65,
    "generic_trail": 0.50,
    "scat": 0.40,
    # GPX / imported markers
    "dated_waypoint": 0.45,
    "undated_waypoint": 0.30,
    "other_sign": 0.35,
}

# Map ObservationType → default source-quality key
_OBS_TYPE_QUALITY_KEY: Dict[ObservationType, str] = {
    ObservationType.FRESH_SCRAPE: "fresh_scrape",
    ObservationType.RUB_LINE: "rub_line",
    ObservationType.BEDDING_AREA: "bedding_area",
    ObservationType.TRAIL_CAMERA: "camera_generic_buck",
    ObservationType.DEER_TRACKS: "deer_tracks",
    ObservationType.FEEDING_SIGN: "feeding_sign",
    ObservationType.SCAT_DROPPINGS: "scat",
    ObservationType.DEER_SIGHTING: "deer_sighting",
    ObservationType.OTHER_SIGN: "other_sign",
}


def source_quality_for_observation(
    obs_type: ObservationType,
    *,
    has_mature_buck: bool = False,
    is_target_buck: bool = False,
    is_dated: bool = True,
) -> float:
    """Return the source-quality value for a scouting observation."""
    if obs_type == ObservationType.TRAIL_CAMERA:
        if is_target_buck:
            return SOURCE_QUALITY["camera_target_buck"]
        if has_mature_buck:
            return SOURCE_QUALITY["camera_mature_buck"]
        return SOURCE_QUALITY["camera_generic_buck"]
    key = _OBS_TYPE_QUALITY_KEY.get(obs_type, "other_sign")
    base = SOURCE_QUALITY[key]
    if not is_dated:
        base = min(base, SOURCE_QUALITY["undated_waypoint"])
    return base


# ── Recency decay ────────────────────────────────────────────────────────

_RECENCY_BREAKPOINTS = [
    # (max_age_days, weight)
    (14, 1.00),
    (45, 0.80),
    (90, 0.60),
    (180, 0.45),  # same season but older
    (365, 0.20),  # previous season
    (730, 0.08),  # 2 years
]
_ARCHIVE_WEIGHT = 0.05  # > 2 years


def recency_weight(age_days: float) -> float:
    """Compute recency multiplier (0–1) given observation age in days."""
    if age_days <= 0:
        return 1.0
    for max_days, weight in _RECENCY_BREAKPOINTS:
        if age_days <= max_days:
            return weight
    return _ARCHIVE_WEIGHT


def age_days_from_timestamp(ts: datetime, *, now: Optional[datetime] = None) -> float:
    """Return age in fractional days for a UTC-aware timestamp."""
    if now is None:
        now = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    delta = now - ts
    return max(0.0, delta.total_seconds() / 86400)


# ── Maturity multiplier ──────────────────────────────────────────────────
# These defaults intentionally duplicate the values in BuckEvent.maturity_weight
# so that callers without a BuckEvent instance can still get correct weights.

_MATURITY_DEFAULTS = {
    "target_buck_repeated": 1.50,
    "mature_confirmed": 1.20,
    "generic_buck": 0.80,
    "doe_spike": 0.50,
    "unknown": 0.60,
}


def maturity_multiplier(
    *,
    is_mature: bool = False,
    is_target: bool = False,
    is_repeated: bool = False,
) -> float:
    """Return a maturity multiplier (typically 0.5–1.5)."""
    if is_target and is_repeated:
        return _MATURITY_DEFAULTS["target_buck_repeated"]
    if is_mature:
        return _MATURITY_DEFAULTS["mature_confirmed"]
    return _MATURITY_DEFAULTS["generic_buck"]


# ── Pattern bonus ────────────────────────────────────────────────────────

_PATTERN_BONUSES = {
    "repeated": 0.20,
    "daylight": 0.15,
    "multi_evidence": 0.15,
    "cross_season": 0.10,
}


def pattern_bonus(flags: Optional[Dict[str, bool]] = None) -> float:
    """Sum additive pattern bonuses.  Capped at 0.50."""
    if not flags:
        return 0.0
    total = sum(
        _PATTERN_BONUSES.get(k, 0.0) for k, v in flags.items() if v
    )
    return min(total, 0.50)


# ── Combined weight ──────────────────────────────────────────────────────

def compute_evidence_weight(
    source_quality: float,
    age_days: float,
    maturity_multiplier_val: float = 1.0,
    pattern_flags: Optional[Dict[str, bool]] = None,
) -> float:
    """Compute a normalised combined evidence weight in [0, 1].

    Formula: ``min(1.0, source_quality × recency × maturity + bonus)``
    """
    rec = recency_weight(age_days)
    bonus = pattern_bonus(pattern_flags)
    raw = source_quality * rec * maturity_multiplier_val + bonus
    return round(min(1.0, max(0.0, raw)), 4)
