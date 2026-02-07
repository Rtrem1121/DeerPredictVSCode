"""LiDAR/DEM terrain scoring for hotspot property analysis."""

from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional, Tuple


def pick_best_dem_file(lidar_files: Dict[str, str]) -> Optional[str]:
    """Select the best DEM file from available LiDAR files (prefers true DEM over hillshade)."""
    if not lidar_files:
        return None
    for name, path in lidar_files.items():
        if "DEM" in str(name).upper():
            return path
    return next(iter(lidar_files.values()), None)


def lidar_shortlist_points(
    corners: List[Tuple[float, float]],
    points: List[Tuple[float, float]],
    *,
    sample_radius_m: int,
    top_k: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Score many points using local LiDAR/DEM and return the top *top_k*.

    Returns ``(scored_list, meta_dict)``.  If LiDAR is unavailable the scored
    list will be empty and *meta* will contain the reason.
    """

    from backend.services.lidar_processor import DEMFileManager, RASTERIO_AVAILABLE  # type: ignore

    if not RASTERIO_AVAILABLE:
        return [], {"lidar_available": False, "reason": "rasterio_not_available"}

    dem_manager = DEMFileManager()
    lidar_files = dem_manager.get_files()
    dem_path = pick_best_dem_file(lidar_files)
    if not dem_path:
        return [], {"lidar_available": False, "reason": "no_lidar_files"}

    try:
        import numpy as np  # type: ignore
        import rasterio  # type: ignore
        from rasterio.windows import from_bounds  # type: ignore
        from rasterio.warp import transform  # type: ignore

        lats = [c[0] for c in corners]
        lons = [c[1] for c in corners]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        with rasterio.open(dem_path) as src:
            xs, ys = transform("EPSG:4326", src.crs, [min_lon, max_lon], [min_lat, max_lat])
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            pad = float(sample_radius_m) * 2.0
            min_x -= pad
            max_x += pad
            min_y -= pad
            max_y += pad

            window = from_bounds(min_x, min_y, max_x, max_y, transform=src.transform)
            elevation = src.read(1, window=window, masked=True)

            max_cells = int(os.getenv("HOTSPOT_LIDAR_MAX_WINDOW_CELLS", "50000000"))
            if int(elevation.shape[0]) * int(elevation.shape[1]) > max_cells:
                raise RuntimeError(f"DEM window too large: {elevation.shape}")

            elev = elevation.astype("float32").filled(np.nan)
            valid = np.isfinite(elev)
            if not bool(valid.any()):
                raise RuntimeError("No valid DEM values in window")

            xres = float(abs(src.res[0]))
            yres = float(abs(src.res[1]))
            gy, gx = np.gradient(elev, yres, xres)
            slope_rad = np.arctan(np.sqrt(gx * gx + gy * gy))
            slope_deg = np.degrees(slope_rad)

            dgy_dy, dgy_dx = np.gradient(gy, yres, xres)
            dgx_dy, dgx_dx = np.gradient(gx, yres, xres)
            curvature = dgy_dy + dgx_dx

            elev_min = float(np.nanmin(elev))
            elev_max = float(np.nanmax(elev))
            elev_range = max(1e-6, elev_max - elev_min)

            w_transform = src.window_transform(window)

            def _sample_at(lat: float, lon: float) -> Optional[Tuple[int, int, float, float]]:
                xs2, ys2 = transform("EPSG:4326", src.crs, [lon], [lat])
                x, y = xs2[0], ys2[0]
                row, col = rasterio.transform.rowcol(w_transform, x, y)
                if row < 0 or col < 0 or row >= elev.shape[0] or col >= elev.shape[1]:
                    return None
                e = float(elev[row, col])
                s = float(slope_deg[row, col])
                if not (math.isfinite(e) and math.isfinite(s)):
                    return None
                return row, col, e, s

            def _clamp01(value: float) -> float:
                return max(0.0, min(1.0, value))

            cell_m = max(1e-6, max(xres, yres))
            local_radius_px = max(1, min(6, int((float(sample_radius_m) / cell_m) * 0.15)))
            large_radius_px = max(local_radius_px + 2, min(18, int((float(sample_radius_m) / cell_m) * 0.6)))

            # ---- Phase 1: fast base scoring ----
            base_scored: List[Dict[str, Any]] = []
            for (lat, lon) in points:
                sampled = _sample_at(lat, lon)
                if not sampled:
                    continue
                row, col, e, s = sampled

                slope_pref = max(0.0, 1.0 - (abs(s - 10.0) / 10.0))
                elev_norm = (e - elev_min) / elev_range
                elev_pref = max(0.0, 1.0 - (abs(elev_norm - 0.6) / 0.6))
                base_score = slope_pref * 60.0 + elev_pref * 40.0

                base_scored.append(
                    {
                        "lat": float(lat),
                        "lon": float(lon),
                        "row": int(row),
                        "col": int(col),
                        "elevation_m": float(e),
                        "slope_deg": float(s),
                        "slope_pref": float(slope_pref),
                        "elev_pref": float(elev_pref),
                        "base_score": float(base_score),
                    }
                )

            base_scored.sort(
                key=lambda r: (
                    -float(r.get("base_score", 0.0)),
                    float(r.get("lat", 0.0)),
                    float(r.get("lon", 0.0)),
                )
            )

            candidate_pool = max(200, max(1, top_k) * 20)
            candidates = base_scored[: min(candidate_pool, len(base_scored))]

            # ---- Phase 2: detailed terrain scoring ----
            scored: List[Dict[str, Any]] = []
            for c in candidates:
                row = int(c["row"])
                col = int(c["col"])
                e = float(c["elevation_m"])
                s = float(c["slope_deg"])
                slope_pref = float(c["slope_pref"])
                elev_pref = float(c["elev_pref"])

                r0 = max(0, row - local_radius_px)
                r1 = min(elev.shape[0], row + local_radius_px + 1)
                c0 = max(0, col - local_radius_px)
                c1 = min(elev.shape[1], col + local_radius_px + 1)

                local_elev = elev[r0:r1, c0:c1]
                local_slope = slope_deg[r0:r1, c0:c1]
                local_curv = curvature[r0:r1, c0:c1]

                local_mean = float(np.nanmean(local_elev)) if np.isfinite(local_elev).any() else e
                local_min = float(np.nanmin(local_elev)) if np.isfinite(local_elev).any() else e
                local_max = float(np.nanmax(local_elev)) if np.isfinite(local_elev).any() else e
                local_relief = max(1e-6, local_max - local_min)

                local_slope_mean = float(np.nanmean(local_slope)) if np.isfinite(local_slope).any() else s
                local_slope_std = float(np.nanstd(local_slope)) if np.isfinite(local_slope).any() else 0.0
                local_roughness = float(np.nanstd(local_elev)) if np.isfinite(local_elev).any() else 0.0
                local_curv_mean = float(np.nanmean(np.abs(local_curv))) if np.isfinite(local_curv).any() else 0.0

                tpi = float(e - local_mean)
                tpi_norm = float(tpi / local_relief)

                lr0 = max(0, row - large_radius_px)
                lr1 = min(elev.shape[0], row + large_radius_px + 1)
                lc0 = max(0, col - large_radius_px)
                lc1 = min(elev.shape[1], col + large_radius_px + 1)
                large_elev = elev[lr0:lr1, lc0:lc1]
                large_mean = float(np.nanmean(large_elev)) if np.isfinite(large_elev).any() else local_mean
                large_min = float(np.nanmin(large_elev)) if np.isfinite(large_elev).any() else local_min
                large_max = float(np.nanmax(large_elev)) if np.isfinite(large_elev).any() else local_max
                large_relief = max(1e-6, large_max - large_min)
                tpi_large = float(e - large_mean)
                tpi_large_norm = float(tpi_large / large_relief)

                bench_score = _clamp01(1.0 - (local_slope_mean / 12.0)) * _clamp01(1.0 - (abs(tpi_norm) * 2.0))
                saddle_score = _clamp01(local_relief / 12.0) * _clamp01(1.0 - (abs(tpi_norm) * 2.0)) * _clamp01(local_slope_std / 5.0)
                corridor_score = _clamp01(1.0 - (abs(local_slope_mean - 8.0) / 8.0)) * _clamp01(local_relief / 10.0)
                roughness_score = _clamp01(local_roughness / 6.0)
                curvature_score = _clamp01(local_curv_mean / 0.08)
                shelter_score = _clamp01((-tpi_norm) * 1.5) * _clamp01(local_relief / 15.0) * _clamp01(1.0 - (abs(local_slope_mean - 10.0) / 12.0))
                tpi_large_score = _clamp01(1.0 - (abs(tpi_large_norm) * 2.0))

                score = (
                    slope_pref * 30.0
                    + elev_pref * 20.0
                    + bench_score * 12.0
                    + saddle_score * 8.0
                    + corridor_score * 8.0
                    + roughness_score * 8.0
                    + curvature_score * 4.0
                    + shelter_score * 6.0
                    + tpi_large_score * 4.0
                )
                scored.append(
                    {
                        "lat": float(c["lat"]),
                        "lon": float(c["lon"]),
                        "lidar_score": float(score),
                        "elevation_m": float(e),
                        "slope_deg": float(s),
                        "tpi": float(tpi),
                        "tpi_large": float(tpi_large),
                        "local_relief_m": float(local_relief),
                        "large_relief_m": float(large_relief),
                        "local_slope_mean": float(local_slope_mean),
                        "local_roughness": float(local_roughness),
                        "local_curvature": float(local_curv_mean),
                        "bench_score": float(bench_score),
                        "saddle_score": float(saddle_score),
                        "corridor_score": float(corridor_score),
                        "roughness_score": float(roughness_score),
                        "curvature_score": float(curvature_score),
                        "shelter_score": float(shelter_score),
                        "tpi_large_score": float(tpi_large_score),
                    }
                )

            scored.sort(
                key=lambda r: (
                    -float(r.get("lidar_score", 0.0)),
                    float(r.get("lat", 0.0)),
                    float(r.get("lon", 0.0)),
                )
            )
            top = scored[: max(1, top_k)]

            meta = {
                "lidar_available": True,
                "dem_path": dem_path,
                "scored_points": len(scored),
                "window_shape": [int(elev.shape[0]), int(elev.shape[1])],
                "window_resolution_m": [xres, yres],
            }
            return top, meta

    except Exception as e:
        return [], {"lidar_available": False, "reason": f"lidar_window_failed: {e}"}
