"""
Unified terrain scoring for mature buck stand placement.

Single source of truth for slope preference, elevation preference,
ridgeline/drainage detection, and feature scoring. Used by both the
max-accuracy pipeline and the hotspot/standard pipeline.
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Slope preference
# ---------------------------------------------------------------------------

def slope_preference(slope_deg: float) -> float:
    """
    Score slope suitability for mature buck terrain (bedding, travel, stands).

    Research basis:
    - 5–22° is the productive range for whitetail bedding and travel.
    - Sidehill benches at 8–15° are prime bedding.
    - 15–22° sidehill terrain is still excellent for travel corridors.
    - Below 5° is flat (fields, bottomland — exposed).
    - Above 30° is too steep for comfortable bedding.

    Returns 0.0–1.0 with a plateau across 5–22° (score=1.0),
    smooth ramp-up from 0–5° and ramp-down from 22–35°.
    """
    if slope_deg < 0:
        return 0.0
    if slope_deg < 5.0:
        # Ramp up: 0° → 0.2, 5° → 1.0
        return 0.2 + 0.8 * (slope_deg / 5.0)
    if slope_deg <= 22.0:
        # Plateau: prime terrain
        return 1.0
    if slope_deg <= 35.0:
        # Ramp down: 22° → 1.0, 35° → 0.0
        return max(0.0, 1.0 - (slope_deg - 22.0) / 13.0)
    return 0.0


# ---------------------------------------------------------------------------
# Elevation / ridge proximity preference
# ---------------------------------------------------------------------------

def ridge_proximity_preference(
    elevation: float,
    elev_min: float,
    elev_max: float,
) -> float:
    """
    Score elevation by proximity to ridgetops (upper third of local terrain).

    Research basis:
    - Mature bucks bed on the upper 1/3 of slopes, typically 70–90% of
      the local elevation range, where they can see/smell downhill.
    - Valley floors (bottom 30%) are avoided for bedding (too exposed,
      scent pools).
    - Ridgetops themselves (top 5%) can be exposed to wind; just below
      the ridgetop is ideal.

    Returns 0.0–1.0 with peak at 75th–85th percentile of local elevation.
    """
    denom = max(1e-6, elev_max - elev_min)
    elev_norm = (elevation - elev_min) / denom

    if elev_norm < 0.3:
        # Valley floor — poor for bedding, moderate for travel
        return max(0.1, elev_norm / 0.3 * 0.4)
    if elev_norm < 0.6:
        # Mid-slope — decent travel terrain
        return 0.4 + (elev_norm - 0.3) / 0.3 * 0.5
    if elev_norm <= 0.92:
        # Upper slope — prime bedding zone (peak at ~0.80)
        # Peaks at 0.80, scores 0.9 at edges (0.60, 0.92)
        center = 0.80
        dist = abs(elev_norm - center)
        return max(0.9, 1.0 - dist / 0.20)
    # Ridgetop — slightly exposed, still good but not peak
    return max(0.7, 1.0 - (elev_norm - 0.92) / 0.08 * 0.3)


# ---------------------------------------------------------------------------
# Ridgeline detection from DEM grids
# ---------------------------------------------------------------------------

def detect_ridgelines(
    tpi_large: np.ndarray,
    slope_deg: np.ndarray,
    relief: np.ndarray,
) -> np.ndarray:
    """
    Identify ridgeline pixels from TPI + slope + relief.

    A ridgeline point has:
    - High large-scale TPI (above its neighborhood)
    - Moderate slope (ridgetops are relatively flat compared to sides)
    - Meaningful relief (not a flat plain)

    Returns a 0.0–1.0 ridgeline score array.
    """
    relief_safe = np.maximum(relief, 1e-6)

    # TPI normalized by relief — high = above surroundings
    tpi_norm = tpi_large / relief_safe
    ridge_tpi = np.clip(tpi_norm / 0.5, 0.0, 1.0)  # peaks at tpi_norm >= 0.5

    # Ridgetops tend to be flatter than sides (< 15°)
    ridge_slope = np.clip(1.0 - slope_deg / 20.0, 0.0, 1.0)

    # Need real terrain, not flat ground
    ridge_relief = np.clip(relief / 8.0, 0.0, 1.0)

    return ridge_tpi * ridge_slope * ridge_relief


# ---------------------------------------------------------------------------
# Drainage / draw detection from DEM grids
# ---------------------------------------------------------------------------

def detect_drainages(
    tpi_small: np.ndarray,
    tpi_large: np.ndarray,
    curvature: np.ndarray,
    relief: np.ndarray,
) -> np.ndarray:
    """
    Identify drainage / draw corridors from TPI + curvature.

    A drainage point has:
    - Negative TPI (below its neighborhood — a valley/draw)
    - Positive plan curvature (converging flow)
    - Meaningful relief (not a flat plain)

    Returns a 0.0–1.0 drainage score array.
    """
    relief_safe = np.maximum(relief, 1e-6)

    # Negative TPI = below neighbors = valley/draw
    tpi_small_norm = -tpi_small / relief_safe
    tpi_large_norm = -tpi_large / relief_safe
    draw_tpi = np.clip(
        0.6 * np.clip(tpi_small_norm / 0.3, 0.0, 1.0) +
        0.4 * np.clip(tpi_large_norm / 0.3, 0.0, 1.0),
        0.0, 1.0,
    )

    # Converging curvature (positive = concave up = water collects)
    curv_score = np.clip(curvature / 0.05, 0.0, 1.0)

    # Relief minimum
    relief_score = np.clip(relief / 5.0, 0.0, 1.0)

    return draw_tpi * (0.6 + 0.4 * curv_score) * relief_score


# ---------------------------------------------------------------------------
# Season-aware canopy/NDVI scoring
# ---------------------------------------------------------------------------

def season_canopy_score(
    canopy_pct: float,
    ndvi: float,
    month: int,
) -> float:
    """
    Score canopy/NDVI contribution with season gating.

    After leaf-off (mid-October in Vermont), deciduous canopy and NDVI
    measure dead leaves/bare branches — noise, not signal. Only conifer
    stands retain meaningful canopy in winter.

    Rules:
    - May–September: full weight (leaves on)
    - October: half weight (transitional)
    - November–April: near-zero weight (leaf-off)
      BUT high canopy (>80%) likely indicates conifers → retain partial credit.

    Returns 0.0–1.0.
    """
    canopy_bonus = max(0.0, min(1.0, (canopy_pct - 60.0) / 40.0))
    ndvi_bonus = max(0.0, min(1.0, (ndvi - 0.35) / 0.35))
    raw = canopy_bonus * 0.6 + ndvi_bonus * 0.4

    if 5 <= month <= 9:
        # Full leaf-on
        return raw
    if month == 10:
        # Transitional — half weight
        return raw * 0.5
    # November–April: leaf-off
    # High canopy (>80%) likely = conifers, give partial credit
    if canopy_pct > 80.0:
        return raw * 0.3  # conifer bonus
    return raw * 0.05  # basically ignore


# ---------------------------------------------------------------------------
# Rut phase classification
# ---------------------------------------------------------------------------

def classify_rut_phase(month: int, day: int) -> str:
    """
    Classify the rut phase for Vermont whitetails.

    Based on photoperiod-driven breeding chronology:
    - Pre-rut (Oct 20 – Nov 3): Scrape checking, short cruising loops
    - Seeking (Nov 4 – Nov 9): Bucks ranging widely, checking doe groups
    - Peak rut (Nov 10 – Nov 22): All-day chasing, breeding
    - Post-rut (Nov 23 – Dec 5): Recovery, secondary breeding
    - Late season (Dec 6+): Food-focused, short movements

    Returns one of: "pre_rut", "seeking", "peak_rut", "post_rut", "late_season",
    "early_season".
    """
    if month < 10 or (month == 10 and day < 20):
        return "early_season"
    if month == 10 and day >= 20:
        return "pre_rut"
    if month == 11:
        if day <= 3:
            return "pre_rut"
        if day <= 9:
            return "seeking"
        if day <= 22:
            return "peak_rut"
        return "post_rut"
    if month == 12 and day <= 5:
        return "post_rut"
    if month == 12:
        return "late_season"
    # January–September
    return "early_season"


# ---------------------------------------------------------------------------
# Rut-aware activity level
# ---------------------------------------------------------------------------

def rut_adjusted_activity(
    time_of_day: int,
    rut_phase: str,
) -> str:
    """
    Base activity level adjusted for rut phase.

    Key biological fact: During peak rut and seeking phases, mature bucks
    are on their feet from 9 AM to 3 PM — the famous "10-to-2" midday
    movement window. Standard hunting wisdom (and trail cam data) confirms
    this is when the biggest bucks are killed during rut.

    Returns "high", "moderate", or "low".
    """
    # Dawn/dusk are always high regardless of phase
    if 6 <= time_of_day <= 8 or 16 <= time_of_day <= 19:
        return "high"

    # Midday window (9 AM – 3 PM)
    if 9 <= time_of_day <= 15:
        if rut_phase == "peak_rut":
            return "high"  # All-day movement during peak rut
        if rut_phase == "seeking":
            return "high"  # Cruising bucks midday
        if rut_phase == "pre_rut":
            return "moderate"  # Some midday scrape checking
        if rut_phase == "post_rut":
            return "moderate"  # Secondary rut activity
        # Early/late season: midday is low
        return "low"

    # Late evening / overnight
    if 20 <= time_of_day <= 23 or 0 <= time_of_day <= 5:
        if rut_phase in ("peak_rut", "seeking"):
            return "moderate"  # Extended activity
        return "low" if 0 <= time_of_day <= 4 else "moderate"

    return "moderate"


# ---------------------------------------------------------------------------
# Wind-dependent scent carry distance
# ---------------------------------------------------------------------------

def scent_carry_distance(wind_speed_mph: float) -> float:
    """
    Estimate how far human scent carries downwind in meters.

    Research basis:
    - Calm (0-3 mph): scent pools and drifts erratically, ~150-250m
    - Light (3-8 mph): directional carry, ~250-400m
    - Moderate (8-15 mph): strong directional carry, ~400-550m
    - High (15+ mph): turbulent mixing but long carry, ~500-700m

    Linear model: base 150m + 30m per mph, capped at 700m.
    """
    return min(700.0, 150.0 + wind_speed_mph * 30.0)


# ---------------------------------------------------------------------------
# Scent cone width (wind-speed dependent)
# ---------------------------------------------------------------------------

def scent_cone_half_width(wind_speed_mph: float) -> float:
    """
    Half-angle of the scent cone in degrees.

    In calm air, scent drifts erratically (wide cone).
    In strong wind, scent forms a tight plume (narrow cone).

    Returns half-angle in degrees (full cone = 2x this).
    """
    if wind_speed_mph <= 2:
        return 90.0   # Calm: scent goes everywhere
    if wind_speed_mph <= 5:
        return 75.0   # Light: wide cone
    if wind_speed_mph <= 10:
        return 60.0   # Moderate: standard cone
    if wind_speed_mph <= 15:
        return 45.0   # Strong: tight plume
    return 35.0       # Very strong: very tight plume
