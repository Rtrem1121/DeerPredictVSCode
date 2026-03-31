"""Stand reasoning — generates human-readable 'why this stand' narratives.

Combines terrain features, bedding proximity, corridor presence, and wind
information into a concise justification string for each stand recommendation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.utils.geo import bearing_to_cardinal


def _pct(value: float) -> str:
    return f"{value:.0%}"


def _dist_str(meters: float) -> str:
    if meters < 100:
        return f"{meters:.0f}m"
    return f"{meters:.0f}m"


def generate_stand_narrative(
    stand: Dict[str, Any],
    *,
    rank: int = 1,
    bedding_zones: Optional[List[Dict[str, Any]]] = None,
    corridor_data: Optional[Dict[str, Any]] = None,
    season: str = "rut",
) -> str:
    """Build a 2-4 sentence 'why this stand' explanation.

    Designed for display in the frontend stand detail panel.
    """
    parts: List[str] = []

    # ── Terrain feature lead ──
    features = []
    bench = float(stand.get("bench_score", 0))
    saddle = float(stand.get("saddle_score", 0))
    corridor = float(stand.get("corridor_score", 0))
    ridgeline = float(stand.get("ridgeline_score", 0))
    drainage = float(stand.get("drainage_score", 0))
    shelter = float(stand.get("shelter_score", 0))

    if bench >= 0.65:
        features.append("sidehill bench")
    if saddle >= 0.65:
        features.append("saddle funnel")
    if corridor >= 0.60:
        features.append("travel corridor")
    if ridgeline >= 0.40:
        features.append("ridgeline")
    if drainage >= 0.40:
        features.append("drainage draw")
    if shelter >= 0.55 and not features:
        features.append("sheltered terrain")

    if features:
        feat_str = ", ".join(features[:-1]) + (" and " if len(features) > 1 else "") + features[-1] if len(features) > 1 else features[0]
        parts.append(f"Stand #{rank} sits on a {feat_str}.")

    # ── Bedding proximity ──
    nearest = stand.get("nearest_bedding")
    if isinstance(nearest, dict):
        dist_m = nearest.get("distance_m")
        bearing_deg = nearest.get("bearing_deg")
        quality = nearest.get("bedding_quality")
        if isinstance(dist_m, (int, float)):
            direction = ""
            if isinstance(bearing_deg, (int, float)):
                direction = f" to the {bearing_to_cardinal(float(bearing_deg))}"
            qual_note = ""
            if isinstance(quality, (int, float)) and float(quality) >= 0.7:
                qual_note = " high-quality"
            if 60 <= dist_m <= 180:
                parts.append(f"A{qual_note} bedding zone is {_dist_str(dist_m)}{direction} — ideal intercept distance.")
            elif dist_m < 60:
                parts.append(f"Bedding is very close ({_dist_str(dist_m)}{direction}) — approach carefully.")
            else:
                parts.append(f"Nearest bedding is {_dist_str(dist_m)}{direction}.")

    # ── Corridor context ──
    corridor_prox = stand.get("corridor_proximity_score")
    if isinstance(corridor_prox, (int, float)) and float(corridor_prox) > 0.3:
        parts.append("Located on a modeled movement corridor — deer travel predicted through this area.")
    elif saddle >= 0.65 and corridor >= 0.5:
        parts.append("Terrain funneling should concentrate deer movement past this point.")

    # ── Wind recommendation ──
    huntable = stand.get("huntable_winds", [])
    avoid = stand.get("avoid_winds", [])
    if huntable:
        wind_str = ", ".join(huntable[:4])
        parts.append(f"Best winds: {wind_str}.")

    # ── Season tip ──
    season_tips = {
        "pre_rut": "During pre-rut, bucks make short cruising loops from bedding — morning and evening ambush.",
        "seeking": "Bucks are ranging widely now — all-day sits near funnels pay off.",
        "peak_rut": "Peak rut — hunt all day. Bucks will cross this terrain chasing does.",
        "rut": "Rut activity favors saddle and corridor positions where bucks intercept does.",
        "post_rut": "Post-rut bucks prioritize food and security cover; expect shorter movement windows.",
        "late_season": "Late season — focus on thermals. Deer conserve energy; hunt food-to-bed transitions.",
        "early_season": "Early season patterns are predictable bed-to-feed transitions at dawn and dusk.",
    }
    tip = season_tips.get(season)
    if tip and len(parts) < 4:
        parts.append(tip)

    return " ".join(parts) if parts else f"Stand #{rank} ranked by terrain and bedding analysis."


def enrich_stands_with_corridor_proximity(
    stands: List[Dict[str, Any]],
    corridor_data: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Add ``corridor_proximity_score`` to each stand based on corridor polylines.

    A stand near a modeled corridor path gets a higher score (0-1).
    """
    if not corridor_data or not isinstance(corridor_data, dict):
        for s in stands:
            s["corridor_proximity_score"] = None
        return stands

    # Collect all corridor path points as flat list of (lat, lon)
    polylines = corridor_data.get("polylines", [])
    corridor_points: List[tuple] = []
    for pl in polylines:
        for pt in pl:
            if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                corridor_points.append((float(pt[0]), float(pt[1])))

    if not corridor_points:
        for s in stands:
            s["corridor_proximity_score"] = None
        return stands

    from backend.utils.geo import haversine

    for s in stands:
        s_lat = s.get("lat")
        s_lon = s.get("lon")
        if s_lat is None or s_lon is None:
            s["corridor_proximity_score"] = None
            continue

        # Find minimum distance to any corridor point
        min_dist = float("inf")
        for clat, clon in corridor_points:
            d = haversine(float(s_lat), float(s_lon), clat, clon)
            if d < min_dist:
                min_dist = d

        # Score: 1.0 at 0m, 0.0 at 200m+, linear decay
        if min_dist <= 200:
            s["corridor_proximity_score"] = round(1.0 - min_dist / 200.0, 3)
        else:
            s["corridor_proximity_score"] = 0.0

    return stands
