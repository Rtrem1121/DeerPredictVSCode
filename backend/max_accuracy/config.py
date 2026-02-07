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

    # Terrain feature weights (tuned for rut behavior)
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "slope_pref": 0.22,
            "elev_pref": 0.12,
            "bench": 0.14,
            "saddle": 0.14,
            "corridor": 0.10,
            "roughness": 0.08,
            "curvature": 0.05,
            "shelter": 0.05,
            "aspect": 0.10,  # south-facing / leeward preference
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
    enable_tiling: bool = True
    tile_size_px: int = 2048
