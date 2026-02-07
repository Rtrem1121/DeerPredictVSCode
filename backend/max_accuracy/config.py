from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class MaxAccuracyConfig:
    """Configuration for the max-accuracy pipeline."""

    grid_spacing_m: int = 20  # dense coverage (~20m)
    max_candidates: int = 5000  # keep a large candidate pool
    top_k_stands: int = 30
    gee_sample_k: int = 200
    wind_offset_m: float = 80.0
    behavior_weight: float = 0.4
    enable_gee: bool = True
    enable_wind: bool = True
    season: str = "rut"
    hunting_pressure: str = "medium"

    # Terrain feature weights (rebalanced for mature buck biology)
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "slope_pref": 0.18,   # 5-22° plateau scoring
            "elev_pref": 0.12,    # ridge proximity (upper third)
            "bench": 0.14,        # sidehill benches — prime bedding
            "saddle": 0.14,       # terrain funnels — proven travel
            "corridor": 0.08,     # general travel corridor
            "roughness": 0.06,    # terrain texture (not flat field)
            "curvature": 0.04,    # terrain shape
            "shelter": 0.08,      # wind/thermal protection
            "aspect": 0.08,       # south/SE facing thermal advantage
            "ridgeline": 0.04,    # ridge spine travel
            "drainage": 0.04,     # drainage funnel travel
        }
    )

    # Bedding zone identification thresholds (tuned based on field data)
    bedding_min_shelter: float = 0.55  # terrain shelter score
    bedding_min_roughness: float = 2.0 # filter out flat fields - need terrain texture
    bedding_slope_min: float = 8.0     # need drainage
    bedding_slope_max: float = 22.0    # not too steep
    bedding_min_bench: float = 0.45    # benches are key
    bedding_min_aspect_score: float = 0.4  # south-facing thermal advantage

    # Bedding proximity scoring
    bedding_optimal_distance_min: float = 80.0  # meters
    bedding_optimal_distance_max: float = 150.0  # meters
    bedding_proximity_weight: float = 0.20  # reduced from 0.30 - don't over-weight

    # Multi-scale terrain windows (in meters)
    tpi_small_m: int = 60
    tpi_large_m: int = 200

    # Diversity constraints
    min_per_quadrant: int = 6

    # Tiling for large-area DEM processing
    # Smaller tiles (512px ≈ 350m) improve resilience to corrupted DEM blocks
    # — a single bad TIFF tile only kills one small pipeline tile instead of
    # a 2048px quadrant covering the entire property.
    enable_tiling: bool = True
    tile_size_px: int = 512
