from __future__ import annotations

import logging
from typing import Dict

from backend.vegetation_analyzer import get_vegetation_analyzer

logger = logging.getLogger(__name__)

# Sentinel values meaning "GEE returned nothing useful — use neutral defaults"
_NEUTRAL_CANOPY = -1.0
_NEUTRAL_NDVI = -1.0


def get_gee_summary(lat: float, lon: float, radius_km: float = 0.25) -> Dict[str, float]:
    """Fetch a lightweight canopy/NDVI summary for a candidate point.

    Returns ``{"gee_canopy": <pct>, "gee_ndvi": <0-1>}``.
    On failure or empty data, returns sentinel values (-1) so the caller
    can distinguish "GEE unavailable" from "GEE says 0%".
    """

    analyzer = get_vegetation_analyzer()
    try:
        data = analyzer.analyze_hunting_area(lat, lon, radius_km=radius_km, season="rut")
    except Exception:
        logger.debug("GEE exception for (%.5f, %.5f) — returning sentinels", lat, lon)
        return {"gee_canopy": _NEUTRAL_CANOPY, "gee_ndvi": _NEUTRAL_NDVI}

    canopy = _NEUTRAL_CANOPY
    ndvi = _NEUTRAL_NDVI

    canopy_data = data.get("canopy_coverage_analysis") if isinstance(data, dict) else None
    if isinstance(canopy_data, dict):
        raw = canopy_data.get("canopy_coverage")
        if raw is not None:
            canopy = float(raw) * 100.0

    ndvi_data = data.get("ndvi_analysis") if isinstance(data, dict) else None
    if isinstance(ndvi_data, dict):
        raw = ndvi_data.get("mean_ndvi")
        if raw is not None:
            ndvi = float(raw)

    return {"gee_canopy": canopy, "gee_ndvi": ndvi}
