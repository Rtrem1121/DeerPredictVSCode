"""Movement cost surface generation from terrain metrics.

Converts terrain feature grids (slope, TPI, corridor score, etc.) into a
single per-cell movement resistance value.  Lower cost = deer travel more
easily through that cell.  The cost function is parameterised by season so
that rut-phase bucks get lower slope sensitivity (they'll cross anything)
while post-rut / late-season bucks conserve energy.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np

# ── Seasonal cost profiles ──────────────────────────────────────────────
# Each key scales a biological factor in the cost function.
#   slope_sensitivity — multiplier on the quadratic slope term
#   cover_weight      — how much canopy cover reduces cost (0 = irrelevant)
#   drainage_bonus    — discount for travel along drainages
#   ridge_penalty     — extra cost for exposed ridgeline travel
#   corridor_bonus    — discount for natural terrain funnels (saddles/draws)

SEASON_PROFILES: Dict[str, Dict[str, float]] = {
    "early_season": {
        "slope_sensitivity": 1.0,
        "cover_weight": 0.30,
        "drainage_bonus": 0.30,
        "ridge_penalty": 0.20,
        "corridor_bonus": 0.30,
    },
    "pre_rut": {
        "slope_sensitivity": 0.80,
        "cover_weight": 0.20,
        "drainage_bonus": 0.20,
        "ridge_penalty": 0.10,
        "corridor_bonus": 0.40,
    },
    "seeking": {  # alias for peak pre-rut cruising
        "slope_sensitivity": 0.70,
        "cover_weight": 0.15,
        "drainage_bonus": 0.15,
        "ridge_penalty": 0.08,
        "corridor_bonus": 0.45,
    },
    "rut": {
        "slope_sensitivity": 0.60,
        "cover_weight": 0.10,
        "drainage_bonus": 0.15,
        "ridge_penalty": 0.05,
        "corridor_bonus": 0.50,
    },
    "peak_rut": {
        "slope_sensitivity": 0.55,
        "cover_weight": 0.08,
        "drainage_bonus": 0.10,
        "ridge_penalty": 0.03,
        "corridor_bonus": 0.55,
    },
    "post_rut": {
        "slope_sensitivity": 1.20,
        "cover_weight": 0.40,
        "drainage_bonus": 0.30,
        "ridge_penalty": 0.30,
        "corridor_bonus": 0.25,
    },
    "late_season": {
        "slope_sensitivity": 1.30,
        "cover_weight": 0.50,
        "drainage_bonus": 0.25,
        "ridge_penalty": 0.35,
        "corridor_bonus": 0.20,
    },
}


def compute_movement_cost(
    slope_deg: np.ndarray,
    corridor_score: np.ndarray,
    ridgeline_score: np.ndarray,
    drainage_score: np.ndarray,
    *,
    canopy_pct: Optional[np.ndarray] = None,
    season: str = "rut",
) -> np.ndarray:
    """Generate a movement cost surface from terrain metric grids.

    Parameters
    ----------
    slope_deg : 2-D float array — slope in degrees.
    corridor_score : 2-D float array 0-1 — natural terrain funnel suitability.
    ridgeline_score : 2-D float array 0-1 — ridgeline exposure.
    drainage_score : 2-D float array 0-1 — drainage / draw presence.
    canopy_pct : optional 2-D float array 0-100 — canopy cover from GEE.
    season : season key selecting cost profile.

    Returns
    -------
    2-D float array, same shape as *slope_deg*.
    Values start at 1.0 (easiest) and increase with resistance.
    Cells with slope > 45° are set to ``np.inf`` (impassable).
    """
    profile = SEASON_PROFILES.get(season, SEASON_PROFILES["rut"])

    # ── Base slope cost (biomechanical) ──
    # Quadratic rise: 0° → 1.0, 10° → ~2.6, 20° → ~7.3, 30° → ~15, 45° → ~33
    sensitivity = profile["slope_sensitivity"]
    slope_cost = 1.0 + (slope_deg * sensitivity / 8.0) ** 2
    slope_cost = np.where(slope_deg > 45.0, np.inf, slope_cost)

    # ── Corridor discount (saddles, draws, natural funnels) ──
    corridor_factor = 1.0 - np.clip(corridor_score, 0.0, 1.0) * profile["corridor_bonus"]

    # ── Drainage discount ──
    drainage_factor = 1.0 - np.clip(drainage_score, 0.0, 1.0) * profile["drainage_bonus"]

    # ── Ridgeline penalty (exposed) ──
    ridge_factor = 1.0 + np.clip(ridgeline_score, 0.0, 1.0) * profile["ridge_penalty"]

    # ── Cover bonus ──
    if canopy_pct is not None:
        # Optimal travel cover ~60-70 %; open fields and impenetrable brush hurt.
        canopy_norm = np.clip(canopy_pct / 100.0, 0.0, 1.0)
        cover_quality = 1.0 - 4.0 * (canopy_norm - 0.65) ** 2
        cover_quality = np.clip(cover_quality, 0.0, 1.0)
        cover_factor = 1.0 - cover_quality * profile["cover_weight"]
    else:
        cover_factor = 1.0

    # ── Combine ──
    cost = slope_cost * corridor_factor * drainage_factor * ridge_factor * cover_factor
    return np.maximum(cost, 1.0)
