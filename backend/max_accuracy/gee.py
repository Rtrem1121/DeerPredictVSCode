from __future__ import annotations

from typing import Dict

from backend.vegetation_analyzer import get_vegetation_analyzer


def get_gee_summary(lat: float, lon: float, radius_km: float = 0.25) -> Dict[str, float]:
    """Fetch a lightweight canopy/NDVI summary for a candidate point."""

    analyzer = get_vegetation_analyzer()
    try:
        data = analyzer.analyze_hunting_area(lat, lon, radius_km=radius_km, season="rut")
    except Exception:
        return {"gee_canopy": 0.0, "gee_ndvi": 0.0}

    canopy = 0.0
    ndvi = 0.0

    canopy_data = data.get("canopy_coverage_analysis") if isinstance(data, dict) else None
    if isinstance(canopy_data, dict):
        canopy = float(canopy_data.get("canopy_coverage", 0.0) or 0.0) * 100.0

    ndvi_data = data.get("ndvi_analysis") if isinstance(data, dict) else None
    if isinstance(ndvi_data, dict):
        ndvi = float(ndvi_data.get("mean_ndvi", 0.0) or 0.0)

    return {"gee_canopy": canopy, "gee_ndvi": ndvi}
