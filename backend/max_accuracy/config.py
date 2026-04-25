from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class MaxAccuracyConfig:
    """Configuration for the max-accuracy pipeline."""

    grid_spacing_m: int = 20  # dense coverage (~20m)
    max_candidates: int = 5000  # keep a large candidate pool
    top_k_stands: int = 30
    gee_sample_k: int = 100
    wind_offset_m: float = 60.0
    behavior_weight: float = 0.50  # behavior IS terrain features (saddle/bench/corridor/ridgeline)
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

    # Bedding zone identification thresholds (strict — mature buck only)
    bedding_min_shelter: float = 0.58  # strong terrain shelter
    bedding_min_roughness: float = 3.0 # needs real terrain texture, not fields
    bedding_slope_min: float = 7.0     # benches are flat spots — slope is lower on the bed itself
    bedding_slope_max: float = 15.0    # too steep = not comfortable
    bedding_min_bench: float = 0.65    # prominent sidehill bench character
    bedding_min_aspect_score: float = 0.4  # south-facing thermal advantage
    bedding_min_elev_percentile: float = 0.40  # bed in upper 60% of terrain (not valley floor)

    # Bedding proximity scoring
    bedding_optimal_distance_min: float = 80.0  # meters
    bedding_optimal_distance_max: float = 150.0  # meters
    bedding_proximity_weight: float = 0.20  # reduced from 0.30 - don't over-weight

    # Multi-scale terrain windows (in meters)
    tpi_small_m: int = 60
    tpi_large_m: int = 200

    # Diversity constraints
    min_per_quadrant: int = 1

    # Tiling for large-area DEM processing
    # Smaller tiles (512px ≈ 350m) improve resilience to corrupted DEM blocks
    # — a single bad TIFF tile only kills one small pipeline tile instead of
    # a 2048px quadrant covering the entire property.
    enable_tiling: bool = True
    tile_size_px: int = 512
