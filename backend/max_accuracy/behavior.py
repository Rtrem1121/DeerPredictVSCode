from __future__ import annotations

from typing import Dict

from backend.utils.terrain_scoring import season_canopy_score


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_behavior(candidate: Dict, *, season: str, month: int = 11) -> float:
    """Score rut/early-season behavior for a candidate point.
    
    The month parameter gates canopy/NDVI scoring — after leaf-off (Nov+)
    these signals are noise for deciduous forest.
    """

    bench = float(candidate.get("bench_score", 0.0))
    saddle = float(candidate.get("saddle_score", 0.0))
    corridor = float(candidate.get("corridor_score", 0.0))
    shelter = float(candidate.get("shelter_score", 0.0))

    canopy = float(candidate.get("gee_canopy", 0.0))
    ndvi = float(candidate.get("gee_ndvi", 0.0))

    # Ridgeline/drainage scores (from unified terrain scoring)
    ridgeline = float(candidate.get("ridgeline_score", 0.0))
    drainage = float(candidate.get("drainage_score", 0.0))

    # Season-gated canopy/NDVI (near-zero weight after leaf-off)
    veg_score = season_canopy_score(canopy, ndvi, month)

    if season in {"rut", "pre_rut", "peak_rut", "seeking"}:
        score = (
            bench * 0.18
            + saddle * 0.22
            + corridor * 0.15
            + shelter * 0.15
            + ridgeline * 0.10   # ridge travel corridors
            + drainage * 0.08    # drainage funnels
            + veg_score * 0.06   # season-gated canopy
            + clamp01(saddle * corridor * 4.0) * 0.06  # pinch point bonus
        )
    elif season == "post_rut":
        score = (
            bench * 0.20
            + saddle * 0.15
            + corridor * 0.15
            + shelter * 0.20
            + ridgeline * 0.08
            + drainage * 0.08
            + veg_score * 0.08
            + clamp01(saddle * corridor * 4.0) * 0.06
        )
    else:
        # Early / late season — shelter and cover matter more
        score = (
            bench * 0.15
            + saddle * 0.10
            + corridor * 0.10
            + shelter * 0.20
            + ridgeline * 0.08
            + drainage * 0.08
            + veg_score * 0.18   # canopy matters when leaves are on
            + clamp01(saddle * corridor * 4.0) * 0.06
            + clamp01(bench * shelter * 4.0) * 0.05  # bedding quality bonus
        )

    return float(clamp01(score))
