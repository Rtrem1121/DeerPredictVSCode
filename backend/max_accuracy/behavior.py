from __future__ import annotations

from typing import Dict


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_behavior(candidate: Dict, *, season: str) -> float:
    """Score rut/early-season behavior for a candidate point."""

    bench = float(candidate.get("bench_score", 0.0))
    saddle = float(candidate.get("saddle_score", 0.0))
    corridor = float(candidate.get("corridor_score", 0.0))
    shelter = float(candidate.get("shelter_score", 0.0))

    canopy = float(candidate.get("gee_canopy", 0.0))
    ndvi = float(candidate.get("gee_ndvi", 0.0))

    canopy_bonus = clamp01((canopy - 60.0) / 40.0)
    ndvi_bonus = clamp01((ndvi - 0.35) / 0.35)

    if season in {"rut", "pre_rut", "post_rut"}:
        score = (
            bench * 0.25
            + saddle * 0.30
            + corridor * 0.20
            + shelter * 0.15
            + canopy_bonus * 0.06
            + ndvi_bonus * 0.04
        )
    else:
        score = (
            bench * 0.20
            + saddle * 0.15
            + corridor * 0.15
            + shelter * 0.10
            + canopy_bonus * 0.20
            + ndvi_bonus * 0.20
        )

    return float(score)
