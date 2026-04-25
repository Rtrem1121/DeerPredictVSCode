from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np


def _safe_uniform_filter(data: np.ndarray, size: int) -> np.ndarray:
    try:
        from scipy.ndimage import uniform_filter  # type: ignore

        return uniform_filter(data, size=size, mode="nearest")
    except Exception:
        # Fallback: coarse local mean using downsample/upsample
        if size <= 1:
            return data
        k = max(1, size // 4)
        reduced = data[::k, ::k]
        expanded = np.repeat(np.repeat(reduced, k, axis=0), k, axis=1)
        return expanded[: data.shape[0], : data.shape[1]]


def _safe_extrema_filter(data: np.ndarray, size: int, mode: str) -> np.ndarray:
    try:
        from scipy.ndimage import maximum_filter, minimum_filter  # type: ignore

        if mode == "max":
            return maximum_filter(data, size=size, mode="nearest")
        return minimum_filter(data, size=size, mode="nearest")
    except Exception:
        # Fallback: no-op
        return data


def compute_metrics(
    elev: np.ndarray,
    cell_m: float,
    tpi_small_m: int,
    tpi_large_m: int,
) -> Dict[str, np.ndarray]:
    """Compute multi-scale terrain metrics on a DEM grid."""

    # Slope from gradients
    gy, gx = np.gradient(elev, cell_m, cell_m)
    slope_rad = np.arctan(np.sqrt(gx * gx + gy * gy))
    slope_deg = np.degrees(slope_rad)

    # Aspect (compass direction slope faces, 0=N, 90=E, 180=S, 270=W)
    aspect_rad = np.arctan2(-gx, -gy)  # negative because downslope direction
    aspect_deg = (np.degrees(aspect_rad) + 360) % 360

    # Curvature (Laplacian)
    dgy_dy, dgy_dx = np.gradient(gy, cell_m, cell_m)
    dgx_dy, dgx_dx = np.gradient(gx, cell_m, cell_m)
    curvature = dgy_dy + dgx_dx

    # Multi-scale TPI (elev minus local mean)
    small_px = max(1, int(tpi_small_m / max(1e-6, cell_m)))
    large_px = max(1, int(tpi_large_m / max(1e-6, cell_m)))
    mean_small = _safe_uniform_filter(elev, size=small_px)
    mean_large = _safe_uniform_filter(elev, size=large_px)
    tpi_small = elev - mean_small
    tpi_large = elev - mean_large

    # Local relief and roughness (mean_small already computed above for TPI)
    rel_small = _safe_extrema_filter(elev, size=small_px, mode="max") - _safe_extrema_filter(elev, size=small_px, mode="min")
    mean_sq_small = _safe_uniform_filter(elev * elev, size=small_px)
    roughness = np.sqrt(np.maximum(mean_sq_small - mean_small * mean_small, 0.0))

    return {
        "slope_deg": slope_deg,
        "aspect_deg": aspect_deg,
        "curvature": curvature,
        "tpi_small": tpi_small,
        "tpi_large": tpi_large,
        "relief_small": rel_small,
        "roughness": roughness,
    }


def score_bench_saddle(
    slope_deg: float,
    tpi_small: float,
    relief_small: float,
    curvature: float,
) -> Tuple[float, float]:
    """Return (bench_score, saddle_score) for a single point.

    NOTE: The vectorised pipeline inlines equivalent logic for performance.
    This helper is kept for unit-test coverage and point-level debugging.
    Do not add new callers; prefer the vectorised path in pipeline.py.
    """

    def clamp01(value: float) -> float:
        return max(0.0, min(1.0, value))

    # Bench: low slope and near-neutral TPI
    bench = clamp01(1.0 - (abs(slope_deg - 6.0) / 8.0)) * clamp01(1.0 - (abs(tpi_small) / max(1.0, relief_small)))

    # Saddle: neutral TPI + surrounding relief + curvature variability
    saddle = clamp01(relief_small / 8.0) * clamp01(1.0 - (abs(tpi_small) / max(1.0, relief_small))) * clamp01(abs(curvature) / 0.08)

    return bench, saddle
