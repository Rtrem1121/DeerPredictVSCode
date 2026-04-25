from __future__ import annotations

import logging
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from backend.corridor import CorridorEngine, CorridorConfig
from backend.services.lidar_processor import DEMFileManager, RASTERIO_AVAILABLE  # type: ignore
from backend.utils.geo import (
    angular_diff,
    bearing_between,
    bearing_to_cardinal,
    haversine,
)
from backend.utils.terrain_scoring import (
    classify_rut_phase,
    detect_drainages,
    detect_ridgelines,
    ridge_proximity_preference,
    scent_carry_distance,
    scent_cone_half_width,
    season_canopy_score,
    slope_preference,
)

from .behavior import score_behavior
from .config import MaxAccuracyConfig
from .gee import get_gee_summary
from .grid import generate_dense_grid
from .terrain_metrics import compute_metrics, score_bench_saddle
from .wind import build_wind_options, get_wind_data

logger = logging.getLogger(__name__)

# Max GEE concurrent requests (avoid hammering the API)
_GEE_MAX_WORKERS = 8


class MaxAccuracyPipeline:
    def __init__(self, config: MaxAccuracyConfig | None = None) -> None:
        self.config = config or MaxAccuracyConfig()
        self._dem_manager = DEMFileManager()
        self._dem_path_cache: str | None = None

    def _calculate_wind_rotation(
        self,
        stand: Dict[str, Any],
        bedding_zones: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate which wind directions are huntable vs avoidable for this stand.
        
        Logic: If wind blows FROM a direction that would carry your scent TOWARD
        nearby bedding, avoid that wind. If wind carries scent AWAY from bedding, huntable.
        
        Returns dict with 'huntable_winds' and 'avoid_winds' lists.
        """
        WIND_DIRS = [0, 45, 90, 135, 180, 225, 270, 315]  # N, NE, E, SE, S, SW, W, NW
        
        stand_lat = stand.get("lat")
        stand_lon = stand.get("lon")
        if stand_lat is None or stand_lon is None:
            return {"huntable_winds": [], "avoid_winds": []}
        
        # Find all bedding zones within scent-carry distance (wind-dependent)
        # Default to 400m if no wind info available
        wind_speed = stand.get("wind_speed_mph", 8.0)
        max_scent_dist = scent_carry_distance(wind_speed)
        nearby_bedding = []
        for bz in bedding_zones:
            bz_lat, bz_lon = bz.get("lat"), bz.get("lon")
            if bz_lat is None or bz_lon is None:
                continue
            dist = haversine(stand_lat, stand_lon, bz_lat, bz_lon)
            if dist <= max_scent_dist:
                bearing = bearing_between(stand_lat, stand_lon, bz_lat, bz_lon)
                nearby_bedding.append({"lat": bz_lat, "lon": bz_lon, "dist": dist, "bearing": bearing})
        
        if not nearby_bedding:
            # No nearby bedding = all winds huntable
            return {
                "huntable_winds": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                "avoid_winds": [],
            }
        
        huntable = []
        avoid = []
        
        for wind_from_deg in WIND_DIRS:
            # Wind FROM this direction means scent blows TO the opposite direction
            scent_blows_to = (wind_from_deg + 180) % 360
            
            # Scent cone width varies with wind speed (tight in strong wind, wide in calm)
            cone_half = scent_cone_half_width(wind_speed)
            
            # Check if scent blows toward any nearby bedding
            scent_hits_bedding = False
            for bed in nearby_bedding:
                angle_diff_val = angular_diff(scent_blows_to, bed["bearing"])
                if angle_diff_val < cone_half:
                    scent_hits_bedding = True
                    break
            
            cardinal = bearing_to_cardinal(wind_from_deg)
            if scent_hits_bedding:
                avoid.append(cardinal)
            else:
                huntable.append(cardinal)
        
        return {"huntable_winds": huntable, "avoid_winds": avoid}

    def run(
        self,
        corners: List[Tuple[float, float]],
        *,
        date_time: str,
        season: str,
        hunting_pressure: str,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        start_time = time.monotonic()

        # Parse date for rut phase classification and season gating
        try:
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(date_time.replace("Z", "+00:00"))
            run_month = dt.month
            run_day = dt.day
        except Exception:
            run_month, run_day = 11, 10  # default to peak rut

        rut_phase = classify_rut_phase(run_month, run_day)
        # Always use classify_rut_phase result — it returns well-defined keys
        # (early_season, pre_rut, seeking, peak_rut, post_rut, late_season)
        # that match corridor SEASON_PROFILES and behavior weight tables.
        effective_season = rut_phase
        logger.info(
            "MaxAccuracy: date=%s rut_phase=%s effective_season=%s",
            date_time, rut_phase, effective_season,
        )

        def report_progress(stage: str, payload: Optional[Dict[str, Any]] = None) -> None:
            if not progress_callback:
                return
            try:
                progress_callback(stage, payload or {})
            except Exception:
                logger.exception("MaxAccuracy: progress callback failed for stage=%s", stage)

        logger.info(
            "MaxAccuracy: start run corners=%s grid_spacing_m=%s max_candidates=%s",
            len(corners),
            self.config.grid_spacing_m,
            self.config.max_candidates,
        )
        report_progress(
            "started",
            {
                "corners": len(corners),
                "grid_spacing_m": self.config.grid_spacing_m,
                "max_candidates": self.config.max_candidates,
                "enable_gee": self.config.enable_gee,
                "gee_sample_k": self.config.gee_sample_k,
            },
        )
        try:
            if not RASTERIO_AVAILABLE:
                logger.error("MaxAccuracy: rasterio not available")
                report_progress("error", {"error": "rasterio_not_available"})
                return {"error": "rasterio_not_available"}

            dem_path = self._get_dem_path()
            if not dem_path:
                logger.error("MaxAccuracy: no lidar DEM files found")
                report_progress("error", {"error": "no_lidar_files"})
                return {"error": "no_lidar_files"}

            t0 = time.monotonic()
            def _grid_progress(row_idx: int, total_rows: int, points_count: int) -> None:
                report_progress(
                    "grid_progress",
                    {
                        "row": row_idx,
                        "total_rows": total_rows,
                        "points": points_count,
                    },
                )

            points = generate_dense_grid(
                corners,
                self.config.grid_spacing_m,
                progress_callback=_grid_progress,
            )
            logger.info(
                "MaxAccuracy: generated %s grid points in %.2fs",
                len(points),
                time.monotonic() - t0,
            )
            report_progress(
                "grid_generated",
                {
                    "count": len(points),
                    "elapsed_s": round(time.monotonic() - t0, 2),
                },
            )

            t0 = time.monotonic()
            terrain = self._score_terrain(points, dem_path, progress_callback=report_progress)
            logger.info(
                "MaxAccuracy: scored %s terrain candidates in %.2fs",
                len(terrain),
                time.monotonic() - t0,
            )
            report_progress(
                "terrain_scored",
                {
                    "count": len(terrain),
                    "elapsed_s": round(time.monotonic() - t0, 2),
                },
            )

            t0 = time.monotonic()
            enriched = self._enrich_with_gee(terrain)
            if self.config.enable_gee and self.config.gee_sample_k > 0:
                logger.info(
                    "MaxAccuracy: enriched %s candidates with GEE in %.2fs",
                    min(self.config.gee_sample_k, len(enriched)),
                    time.monotonic() - t0,
                )
                report_progress(
                    "gee_enriched",
                    {
                        "count": min(self.config.gee_sample_k, len(enriched)),
                        "elapsed_s": round(time.monotonic() - t0, 2),
                    },
                )

            t0 = time.monotonic()
            scored = self._score_behavior(enriched, effective_season, month=run_month)
            combined = self._combine_scores(scored)
            logger.info(
                "MaxAccuracy: combined score for %s candidates in %.2fs",
                len(combined),
                time.monotonic() - t0,
            )
            report_progress(
                "combined_scored",
                {
                    "count": len(combined),
                    "elapsed_s": round(time.monotonic() - t0, 2),
                },
            )

            # Identify bedding zones from enriched candidates
            t0 = time.monotonic()
            bedding_zones = self._identify_bedding_zones(enriched)
            report_progress(
                "bedding_identified",
                {
                    "count": len(bedding_zones),
                    "elapsed_s": round(time.monotonic() - t0, 2),
                },
            )

            # ── Corridor analysis (M2) ──
            t0 = time.monotonic()
            corridor_data = self._run_corridor_analysis(
                dem_path, corners, bedding_zones, effective_season,
            )
            if corridor_data:
                logger.info(
                    "MaxAccuracy: corridor analysis complete in %.2fs (%d paths)",
                    time.monotonic() - t0,
                    corridor_data.get("num_paths", 0),
                )
                report_progress(
                    "corridors_computed",
                    {
                        "num_paths": corridor_data.get("num_paths", 0),
                        "coverage_pct": corridor_data.get("corridor_coverage_pct", 0),
                        "elapsed_s": round(time.monotonic() - t0, 2),
                    },
                )
            else:
                logger.info("MaxAccuracy: corridor analysis skipped or failed")

            t0 = time.monotonic()
            stand_recommendations = self._select_stands(combined, corners, effective_season, bedding_zones)
            logger.info(
                "MaxAccuracy: selected %s stand recommendations in %.2fs",
                len(stand_recommendations),
                time.monotonic() - t0,
            )
            report_progress(
                "stands_selected",
                {
                    "count": len(stand_recommendations),
                    "elapsed_s": round(time.monotonic() - t0, 2),
                },
            )

            # ── M3: Corridor proximity + stand narratives ──
            try:
                from backend.corridor.stand_reasoning import (
                    enrich_stands_with_corridor_proximity,
                    generate_stand_narrative,
                )
                enrich_stands_with_corridor_proximity(stand_recommendations, corridor_data)
                for idx, rec in enumerate(stand_recommendations):
                    rec["why"] = generate_stand_narrative(
                        rec,
                        rank=idx + 1,
                        bedding_zones=bedding_zones,
                        corridor_data=corridor_data,
                        season=effective_season,
                    )
            except Exception:
                logger.exception("MaxAccuracy: stand reasoning failed (non-fatal)")

            logger.info("MaxAccuracy: run complete in %.2fs", time.monotonic() - start_time)
            report_progress(
                "complete",
                {"elapsed_s": round(time.monotonic() - start_time, 2)},
            )

            return {
                "inputs": {
                    "corners": [{"lat": c[0], "lon": c[1]} for c in corners],
                    "date_time": date_time,
                    "season": season,
                    "rut_phase": rut_phase,
                    "effective_season": effective_season,
                    "hunting_pressure": hunting_pressure,
                    "config": asdict(self.config),
                },
                "terrain_candidates": combined,
                "bedding_zones": [
                    {
                        "lat": b["lat"],
                        "lon": b["lon"],
                        "elevation_m": b.get("elevation_m", 0),
                        "shelter_score": b.get("shelter_score", 0),
                        "canopy": b.get("gee_canopy", 0),
                        "ndvi": b.get("gee_ndvi", 0),
                        "slope_deg": b.get("slope_deg", 0),
                        "aspect_deg": b.get("aspect_deg", 0),
                        "bench_score": b.get("bench_score", 0),
                        "roughness": b.get("roughness", 0),
                        "ridgeline_score": b.get("ridgeline_score", 0),
                        "bedding_quality": b.get("bedding_quality", 0),
                        "criteria_met": b.get("bedding_criteria_met", 0),
                    }
                    for b in bedding_zones
                ],
                "stand_recommendations": stand_recommendations,
                "corridors": corridor_data,
            }
        except Exception as exc:
            logger.exception("MaxAccuracy: run failed")
            report_progress("error", {"error": str(exc)})
            return {"error": str(exc)}

    def _get_dem_path(self) -> str | None:
        if self._dem_path_cache:
            return self._dem_path_cache

        lidar_files = self._dem_manager.get_files()
        for name, path in lidar_files.items():
            if "DEM" in str(name).upper():
                self._dem_path_cache = path
                return self._dem_path_cache

        self._dem_path_cache = next(iter(lidar_files.values()), None) if lidar_files else None
        return self._dem_path_cache

    def _score_terrain(
        self,
        points: List[Tuple[float, float]],
        dem_path: str,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> List[Dict[str, Any]]:
        import rasterio  # type: ignore
        from rasterio.warp import transform  # type: ignore

        if not points:
            return []

        def clamp01(value: float) -> float:
            return max(0.0, min(1.0, value))

        lats = [p[0] for p in points]
        lons = [p[1] for p in points]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        logger.info("MaxAccuracy: scoring terrain using DEM %s", dem_path)
        if progress_callback:
            progress_callback("terrain_scoring_started", {"dem_path": dem_path})
        t_open = time.monotonic()
        logger.info("MaxAccuracy: opening DEM")
        with rasterio.open(dem_path) as src:
            logger.info("MaxAccuracy: DEM opened in %.2fs", time.monotonic() - t_open)
            if progress_callback:
                progress_callback("dem_opened", {"elapsed_s": round(time.monotonic() - t_open, 2)})
            xs, ys = transform("EPSG:4326", src.crs, [min_lon, max_lon], [min_lat, max_lat])
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            window = rasterio.windows.from_bounds(min_x, min_y, max_x, max_y, transform=src.transform)
            window = window.round_offsets().round_lengths()
            height = int(window.height)
            width = int(window.width)
            logger.info(
                "MaxAccuracy: DEM window bounds=(%.2f, %.2f, %.2f, %.2f) size=%sx%s",
                min_x,
                min_y,
                max_x,
                max_y,
                height,
                width,
            )
            full_mb = (height * width * 4) / (1024 * 1024)
            logger.info("MaxAccuracy: DEM window size MB=%.2f", full_mb)
            if progress_callback:
                progress_callback("dem_window", {"shape": [height, width], "size_mb": round(full_mb, 2)})

            cell_m = float(max(abs(src.res[0]), abs(src.res[1])))
            small_px = max(1, int(self.config.tpi_small_m / max(1e-6, cell_m)))
            large_px = max(1, int(self.config.tpi_large_m / max(1e-6, cell_m)))
            pad_px = max(small_px, large_px)

            pt_lons = [p[1] for p in points]
            pt_lats = [p[0] for p in points]
            xs_pts, ys_pts = transform("EPSG:4326", src.crs, pt_lons, pt_lats)
            rows, cols = rasterio.transform.rowcol(
                src.window_transform(window),
                xs_pts,
                ys_pts,
            )

            tile_size = self.config.tile_size_px
            if not self.config.enable_tiling:
                tile_size = max(height, width)
            logger.info(
                "MaxAccuracy: tiling enabled=%s tile_size=%s pad=%s",
                self.config.enable_tiling,
                tile_size,
                pad_px,
            )
            tile_map: Dict[tuple[int, int], List[tuple[float, float, int, int]]] = {}
            for (lat, lon), row, col in zip(points, rows, cols):
                if row < 0 or col < 0 or row >= height or col >= width:
                    continue
                tr = int(row) // tile_size
                tc = int(col) // tile_size
                tile_map.setdefault((tr, tc), []).append((float(lat), float(lon), int(row), int(col)))

            scored: List[Dict[str, Any]] = []
            total_tiles = len(tile_map)
            for tile_idx, ((tr, tc), tile_points) in enumerate(tile_map.items(), start=1):
                row0 = tr * tile_size
                col0 = tc * tile_size
                row1 = min(row0 + tile_size, height)
                col1 = min(col0 + tile_size, width)

                row0_pad = max(row0 - pad_px, 0)
                col0_pad = max(col0 - pad_px, 0)
                row1_pad = min(row1 + pad_px, height)
                col1_pad = min(col1 + pad_px, width)

                tile_window = rasterio.windows.Window(
                    col_off=window.col_off + col0_pad,
                    row_off=window.row_off + row0_pad,
                    width=col1_pad - col0_pad,
                    height=row1_pad - row0_pad,
                )

                try:
                    elev = src.read(1, window=tile_window, masked=True).astype("float32").filled(np.nan)
                except Exception:
                    logger.warning("MaxAccuracy: DEM read failed for tile %s/%s — skipping corrupted tile", tile_idx, total_tiles)
                    continue
                if not np.isfinite(elev).any():
                    continue

                try:
                    metrics = compute_metrics(
                        elev,
                        cell_m,
                        self.config.tpi_small_m,
                        self.config.tpi_large_m,
                    )
                except Exception:
                    logger.exception("MaxAccuracy: terrain metrics failed for tile %s/%s", tile_idx, total_tiles)
                    raise

                elev_min = float(np.nanmin(elev))
                elev_max = float(np.nanmax(elev))

                # Compute ridgeline and drainage grids for this tile
                ridgeline_grid = detect_ridgelines(
                    metrics["tpi_large"], metrics["slope_deg"], metrics["relief_small"]
                )
                drainage_grid = detect_drainages(
                    metrics["tpi_small"], metrics["tpi_large"],
                    metrics["curvature"], metrics["relief_small"]
                )

                # -------------------------------------------------------
                # Vectorized per-point scoring (replaces Python for-loop)
                # -------------------------------------------------------
                tp_arr = np.array(tile_points)  # (N, 4): lat, lon, row, col
                tile_lats_v = tp_arr[:, 0]
                tile_lons_v = tp_arr[:, 1]
                lr_v = tp_arr[:, 2].astype(np.int32) - row0_pad
                lc_v = tp_arr[:, 3].astype(np.int32) - col0_pad

                valid = (
                    (lr_v >= 0) & (lc_v >= 0)
                    & (lr_v < elev.shape[0]) & (lc_v < elev.shape[1])
                )
                if not valid.any():
                    continue
                lr = lr_v[valid]
                lc = lc_v[valid]
                # Renamed tile_pt_* to avoid shadowing the outer pt_lats/pt_lons
                # (the outer names are the full-property lists from rowcol();
                #  these are the per-tile filtered subsets used in scoring below).
                tile_pt_lats = tile_lats_v[valid]
                tile_pt_lons = tile_lons_v[valid]

                # Gather terrain values with fancy indexing (one C call per metric)
                e_arr       = elev[lr, lc].astype(np.float64)
                s_arr       = metrics["slope_deg"][lr, lc].astype(np.float64)
                aspect_arr  = metrics["aspect_deg"][lr, lc].astype(np.float64)
                curv_arr    = metrics["curvature"][lr, lc].astype(np.float64)
                tpi_s_arr   = metrics["tpi_small"][lr, lc].astype(np.float64)
                tpi_l_arr   = metrics["tpi_large"][lr, lc].astype(np.float64)
                relief_arr  = metrics["relief_small"][lr, lc].astype(np.float64)
                rough_arr   = metrics["roughness"][lr, lc].astype(np.float64)
                ridge_arr   = ridgeline_grid[lr, lc].astype(np.float64)
                drain_arr   = drainage_grid[lr, lc].astype(np.float64)

                # Slope preference: plateau 5–22°
                slope_pref = np.where(
                    s_arr < 0.0, 0.0,
                    np.where(s_arr < 5.0, 0.2 + 0.8 * (s_arr / 5.0),
                    np.where(s_arr <= 22.0, 1.0,
                    np.where(s_arr <= 35.0, np.maximum(0.0, 1.0 - (s_arr - 22.0) / 13.0),
                    0.0))))

                # Ridge proximity: upper-third preference
                _elev_denom = max(1e-6, elev_max - elev_min)
                elev_norm = (e_arr - elev_min) / _elev_denom
                elev_pref = np.where(
                    elev_norm < 0.3,
                    np.maximum(0.1, elev_norm / 0.3 * 0.4),
                    np.where(elev_norm < 0.6,
                    0.4 + (elev_norm - 0.3) / 0.3 * 0.5,
                    np.where(elev_norm <= 0.92,
                    np.maximum(0.9, 1.0 - np.abs(elev_norm - 0.80) / 0.20),
                    np.maximum(0.7, 1.0 - (elev_norm - 0.92) / 0.08 * 0.3))))

                # Bench and saddle scores
                relief_safe = np.maximum(relief_arr, 1.0)
                tpi_s_norm  = np.abs(tpi_s_arr) / relief_safe
                bench_v = (
                    np.clip(1.0 - (np.abs(s_arr - 6.0) / 8.0), 0.0, 1.0)
                    * np.clip(1.0 - tpi_s_norm, 0.0, 1.0)
                )
                saddle_v = (
                    np.clip(relief_arr / 8.0, 0.0, 1.0)
                    * np.clip(1.0 - tpi_s_norm, 0.0, 1.0)
                    * np.clip(np.abs(curv_arr) / 0.08, 0.0, 1.0)
                )

                # Corridor, shelter, roughness, curvature
                corridor_v = (
                    np.clip(1.0 - (np.abs(tpi_l_arr) / relief_safe), 0.0, 1.0)
                    * np.clip(relief_arr / 10.0, 0.0, 1.0)
                )
                shelter_v = (
                    np.clip(1.0 - (s_arr / 20.0), 0.0, 1.0)
                    * np.clip((relief_arr - np.abs(tpi_s_arr)) / relief_safe, 0.0, 1.0)
                )
                roughness_v  = np.clip(rough_arr / 6.0, 0.0, 1.0)
                curvature_v  = np.clip(np.abs(curv_arr) / 0.1, 0.0, 1.0)

                # Aspect: prefer SE/south (170°), wider tolerance
                _a_diff   = np.abs(aspect_arr - 170.0) % 360.0
                aspect_v  = np.clip(1.0 - (np.minimum(_a_diff, 360.0 - _a_diff) / 100.0), 0.0, 1.0)

                # Weighted composite score (array dot-product)
                w = self.config.weights
                score_v = (
                    slope_pref   * w["slope_pref"]
                    + elev_pref  * w["elev_pref"]
                    + bench_v    * w["bench"]
                    + saddle_v   * w["saddle"]
                    + corridor_v * w["corridor"]
                    + roughness_v * w["roughness"]
                    + curvature_v * w["curvature"]
                    + shelter_v  * w["shelter"]
                    + aspect_v   * w["aspect"]
                    + ridge_arr  * w.get("ridgeline", 0.04)
                    + drain_arr  * w.get("drainage", 0.04)
                )

                n_valid = int(valid.sum())
                # Convert each metric array to a Python list once so the dict
                # comprehension below does cheap list indexing instead of calling
                # float(numpy_scalar) ~17× per point × N points.
                _lats    = tile_pt_lats.tolist()
                _lons    = tile_pt_lons.tolist()
                _score   = score_v.tolist()
                _elev    = e_arr.tolist()
                _slope   = s_arr.tolist()
                _aspect  = aspect_arr.tolist()
                _tpi_s   = tpi_s_arr.tolist()
                _tpi_l   = tpi_l_arr.tolist()
                _relief  = relief_arr.tolist()
                _curv    = curv_arr.tolist()
                _rough   = rough_arr.tolist()
                _bench   = bench_v.tolist()
                _saddle  = saddle_v.tolist()
                _corr    = corridor_v.tolist()
                _shelter = shelter_v.tolist()
                _asp_sc  = aspect_v.tolist()
                _ridge   = ridge_arr.tolist()
                _drain   = drain_arr.tolist()
                scored.extend(
                    {
                        "lat":            _lats[i],
                        "lon":            _lons[i],
                        "score":          _score[i],
                        "elevation_m":    _elev[i],
                        "slope_deg":      _slope[i],
                        "aspect_deg":     _aspect[i],
                        "tpi_small":      _tpi_s[i],
                        "tpi_large":      _tpi_l[i],
                        "relief_small":   _relief[i],
                        "curvature":      _curv[i],
                        "roughness":      _rough[i],
                        "bench_score":    _bench[i],
                        "saddle_score":   _saddle[i],
                        "corridor_score": _corr[i],
                        "shelter_score":  _shelter[i],
                        "aspect_score":   _asp_sc[i],
                        "ridgeline_score": _ridge[i],
                        "drainage_score":  _drain[i],
                    }
                    for i in range(n_valid)
                )

                if progress_callback and (tile_idx % 10 == 0 or tile_idx == total_tiles):
                    progress_callback(
                        "terrain_tile",
                        {"tile": tile_idx, "tiles": total_tiles, "points": len(scored)},
                    )

        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[: self.config.max_candidates]

    @staticmethod
    def _apply_gee_neutral_defaults(candidate: Dict[str, Any]) -> None:
        """Set neutral GEE values on a candidate that was not enriched.

        50% canopy and 0.5 NDVI are mid-range values that neither reward
        nor penalise the candidate in behavior scoring.
        """
        candidate.setdefault("gee_canopy", 50.0)
        candidate.setdefault("gee_ndvi", 0.5)

    def _enrich_with_gee(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        if not self.config.enable_gee or self.config.gee_sample_k <= 0:
            # Set neutral defaults so behavior scoring doesn't penalize
            for c in candidates:
                self._apply_gee_neutral_defaults(c)
            return candidates

        max_k = min(self.config.gee_sample_k, len(candidates))
        logger.info("MaxAccuracy: starting parallel GEE enrichment for %s candidates (%s workers)", max_k, _GEE_MAX_WORKERS)

        to_enrich = candidates[:max_k]
        results: Dict[int, Dict[str, float]] = {}

        def _fetch(idx: int, lat: float, lon: float) -> Tuple[int, Dict[str, float]]:
            return idx, get_gee_summary(lat, lon)

        failed = 0
        with ThreadPoolExecutor(max_workers=_GEE_MAX_WORKERS) as pool:
            futures = {
                pool.submit(_fetch, i, c["lat"], c["lon"]): i
                for i, c in enumerate(to_enrich)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    _, gee_data = future.result()
                    results[idx] = gee_data
                except Exception:
                    failed += 1
                    logger.warning(
                        "MaxAccuracy: GEE failed for candidate idx=%s", idx
                    )
                done = len(results) + failed
                if done % 50 == 0 or done == max_k:
                    logger.info("MaxAccuracy: GEE enrichment %s/%s done", done, max_k)

        # Apply results; for failures or sentinel values, use neutral defaults
        for idx, candidate in enumerate(to_enrich):
            if idx in results:
                gee = results[idx]
                # Detect sentinel values from get_gee_summary failures
                canopy = gee.get("gee_canopy", -1.0)
                ndvi = gee.get("gee_ndvi", -1.0)
                candidate["gee_canopy"] = canopy if canopy >= 0 else 50.0
                candidate["gee_ndvi"] = ndvi if ndvi >= 0 else 0.5
            else:
                self._apply_gee_neutral_defaults(candidate)

        # Also set neutral defaults for candidates beyond max_k
        for candidate in candidates[max_k:]:
            self._apply_gee_neutral_defaults(candidate)

        if failed:
            logger.warning("MaxAccuracy: GEE enrichment had %s failures out of %s", failed, max_k)

        return candidates

    def _score_behavior(self, candidates: List[Dict[str, Any]], season: str, month: int = 11) -> List[Dict[str, Any]]:
        for candidate in candidates:
            candidate["behavior_score"] = score_behavior(candidate, season=season, month=month)
        return candidates

    def _combine_scores(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        scores = [c["score"] for c in candidates]
        min_score = min(scores)
        max_score = max(scores)
        denom = max(1e-6, max_score - min_score)

        for candidate in candidates:
            terrain_norm = (candidate["score"] - min_score) / denom
            behavior = float(candidate.get("behavior_score", 0.0))
            combined = (1.0 - self.config.behavior_weight) * terrain_norm + self.config.behavior_weight * behavior
            candidate["terrain_norm"] = float(terrain_norm)
            candidate["combined_score"] = float(combined)

        candidates.sort(key=lambda r: r["combined_score"], reverse=True)
        return candidates

    def _select_stands(
        self,
        candidates: List[Dict[str, Any]],
        corners: List[Tuple[float, float]],
        season: str,
        bedding_zones: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        bedding_zones = bedding_zones or []

        lats = [c[0] for c in corners]
        lons = [c[1] for c in corners]
        center_lat = (min(lats) + max(lats)) / 2.0
        center_lon = (min(lons) + max(lons)) / 2.0

        def quadrant(lat: float, lon: float) -> str:
            north = lat >= center_lat
            east = lon >= center_lon
            if north and east:
                return "NE"
            if north and not east:
                return "NW"
            if not north and east:
                return "SE"
            return "SW"

        buckets: Dict[str, List[Dict[str, Any]]] = {"NE": [], "NW": [], "SE": [], "SW": []}
        for candidate in candidates:
            q = quadrant(candidate["lat"], candidate["lon"])
            candidate["quadrant"] = q
            buckets[q].append(candidate)

        for bucket in buckets.values():
            bucket.sort(key=lambda r: r["combined_score"], reverse=True)

        logger.info(
            "MaxAccuracy: quadrant sizes NE=%s NW=%s SE=%s SW=%s",
            len(buckets["NE"]),
            len(buckets["NW"]),
            len(buckets["SE"]),
            len(buckets["SW"]),
        )

        # Exclude bedding zones from stand selection — you can't sit in the bed
        bedding_keys = set()
        for bz in bedding_zones:
            bedding_keys.add((round(bz["lat"], 6), round(bz["lon"], 6)))
        if bedding_keys:
            logger.info("MaxAccuracy: excluding %s bedding zones from stand candidates", len(bedding_keys))

        selected: List[Dict[str, Any]] = []
        selected_keys = set()

        for q in ("NE", "NW", "SE", "SW"):
            for candidate in buckets[q][: self.config.min_per_quadrant * 3]:
                if len([s for s in selected if s.get("quadrant") == q]) >= self.config.min_per_quadrant:
                    break
                key = (round(candidate["lat"], 6), round(candidate["lon"], 6))
                if key in selected_keys or key in bedding_keys:
                    continue
                selected_keys.add(key)
                selected.append(candidate)

        for candidate in candidates:
            if len(selected) >= self.config.top_k_stands:
                break
            key = (round(candidate["lat"], 6), round(candidate["lon"], 6))
            if key in selected_keys or key in bedding_keys:
                continue
            selected_keys.add(key)
            selected.append(candidate)

        wind_direction = None
        wind_speed_mph = 8.0
        _wind_seed_failed = False
        if self.config.enable_wind and selected:
            try:
                # NOTE: wind is sampled from selected[0] *before* the
                # bedding-proximity re-rank below.  On a property-scale
                # polygon the difference is negligible, but be aware the
                # wind data may not belong to the final top-ranked stand.
                wind_data = get_wind_data(selected[0]["lat"], selected[0]["lon"])
                wind_direction = float(wind_data.get("wind_direction", 270.0))
                wind_speed_mph = float(wind_data.get("wind_speed", 8.0))
            except Exception:
                logger.exception("MaxAccuracy: wind option seed failed — defaulting to 270° to avoid per-stand fallback calls")
                wind_direction = 270.0  # safe default; avoids N per-stand API retries
                wind_speed_mph = 8.0
                _wind_seed_failed = True

        for candidate in selected:
            if not self.config.enable_wind:
                candidate["wind_options"] = []
                continue
            candidate["wind_speed_mph"] = wind_speed_mph
            try:
                candidate["wind_options"] = build_wind_options(
                    candidate["lat"],
                    candidate["lon"],
                    season,
                    self.config.wind_offset_m,
                    wind_direction_deg=wind_direction,
                )
            except Exception:
                logger.exception("MaxAccuracy: wind options failed for lat=%s lon=%s", candidate["lat"], candidate["lon"])
                candidate["wind_options"] = []

        # Score bedding proximity for each selected stand
        # Purely distance-based — wind is advisory only, not in the ranking
        if bedding_zones:
            for candidate in selected:
                prox_score, nearest_bed = self._score_bedding_proximity(
                    candidate, bedding_zones
                )
                candidate["bedding_proximity_score"] = round(prox_score, 3)
                candidate["nearest_bedding"] = nearest_bed
            
            # Re-sort by combined score weighted with bedding proximity
            # Use configurable weight (default 0.20) to avoid over-weighting bedding
            bp_weight = getattr(self.config, 'bedding_proximity_weight', 0.20)
            for candidate in selected:
                bp = candidate.get("bedding_proximity_score", 0.5)
                cs = candidate.get("combined_score", 0)
                # Blend: (1-bp_weight) original combined + bp_weight bedding proximity
                candidate["final_score"] = (1 - bp_weight) * cs + bp_weight * bp
            
            selected.sort(key=lambda r: r.get("final_score", 0), reverse=True)
            logger.info(
                "MaxAccuracy: re-ranked %s stands by bedding proximity (found %s bedding zones, weight=%.2f)",
                len(selected),
                len(bedding_zones),
                bp_weight,
            )
        else:
            for candidate in selected:
                candidate["bedding_proximity_score"] = None
                candidate["nearest_bedding"] = None
                candidate["final_score"] = candidate.get("combined_score", 0)

        # Calculate wind rotation (huntable/avoid winds) for each stand
        for candidate in selected:
            wind_rotation = self._calculate_wind_rotation(candidate, bedding_zones)
            candidate["huntable_winds"] = wind_rotation["huntable_winds"]
            candidate["avoid_winds"] = wind_rotation["avoid_winds"]

        return selected

    # ─────────────────────────────────────────────────────────────────────────
    # Bedding Zone Identification & Proximity Scoring
    # ─────────────────────────────────────────────────────────────────────────
    def _identify_bedding_zones(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify candidates that match mature buck bedding characteristics.

        Mature bucks bed on sidehill benches in the upper portion of terrain,
        on moderate slopes with strong shelter and rough terrain texture.
        They want drainage, wind protection, and visibility uphill.
        Valley floors and flat open fields are excluded.

        Criteria (ALL required):
        - Bench score >= 0.65 (prominent sidehill bench)
        - Shelter score >= 0.58 (wind/thermal protection from terrain shape)
        - Slope 7-15° (benches are flat spots — slope is lower on the bed itself)
        - Roughness >= 3.0 (real terrain texture, not flat fields)
        - Elevation >= 40th percentile (upper terrain, not valley bottom)

        Bonus factors (boost quality score, not hard filter):
        - Ridgeline proximity (bedding just below ridge)
        - South/SE aspect (thermal advantage)
        """
        if not candidates:
            return []

        # Compute elevation percentile threshold
        elevations = [float(c.get("elevation_m", 0)) for c in candidates]
        if elevations:
            elevations_sorted = sorted(elevations)
            pct = getattr(self.config, 'bedding_min_elev_percentile', 0.40)
            elev_threshold = elevations_sorted[int(len(elevations_sorted) * pct)]
        else:
            elev_threshold = 0.0

        bedding = []
        for c in candidates:
            shelter = float(c.get("shelter_score", 0))
            slope = float(c.get("slope_deg", 0))
            bench = float(c.get("bench_score", 0))
            aspect_score = float(c.get("aspect_score", 0))
            roughness = float(c.get("roughness", 0))
            elevation = float(c.get("elevation_m", 0))
            ridgeline = float(c.get("ridgeline_score", 0))

            # Hard filters — ALL must pass
            meets_shelter = shelter >= self.config.bedding_min_shelter
            meets_slope = self.config.bedding_slope_min <= slope <= self.config.bedding_slope_max
            meets_bench = bench >= self.config.bedding_min_bench
            meets_roughness = roughness >= self.config.bedding_min_roughness
            meets_elevation = elevation >= elev_threshold

            if not (meets_shelter and meets_slope and meets_bench and meets_roughness and meets_elevation):
                continue

            # Composite bedding quality score (0-1)
            # Higher = more confident this is a mature buck bed
            bench_quality = min(1.0, (bench - 0.60) / 0.15)       # 0.60=0, 0.75=1
            shelter_quality = min(1.0, (shelter - 0.55) / 0.10)    # 0.55=0, 0.65=1
            slope_quality = 1.0 - abs(slope - 13.0) / 5.0          # peak at 13°, ±5°
            slope_quality = max(0.0, min(1.0, slope_quality))
            rough_quality = min(1.0, (roughness - 2.0) / 4.0)     # 2=0, 6=1
            ridgeline_bonus = min(1.0, ridgeline * 1.5)            # near ridge = bonus
            aspect_bonus = aspect_score * 0.5                       # south-facing bonus

            bedding_quality = (
                0.30 * bench_quality
                + 0.25 * shelter_quality
                + 0.20 * slope_quality
                + 0.10 * rough_quality
                + 0.10 * ridgeline_bonus
                + 0.05 * aspect_bonus
            )

            c["is_probable_bedding"] = True
            c["bedding_quality"] = round(bedding_quality, 3)
            c["bedding_criteria_met"] = 5  # all hard filters passed
            c["bedding_criteria"] = {
                "shelter": meets_shelter,
                "slope": meets_slope,
                "bench": meets_bench,
                "roughness": meets_roughness,
                "elevation": meets_elevation,
            }
            bedding.append(c)

        # Sort by quality — best bedding first
        bedding.sort(key=lambda b: b.get("bedding_quality", 0), reverse=True)

        logger.info(
            "MaxAccuracy: identified %s probable bedding zones from %s candidates "
            "(elev threshold=%.0fm, top quality=%.3f)",
            len(bedding),
            len(candidates),
            elev_threshold,
            bedding[0].get("bedding_quality", 0) if bedding else 0,
        )
        return bedding

    # ─────────────────────────────────────────────────────────────────────────
    # Corridor Analysis (M2)
    # ─────────────────────────────────────────────────────────────────────────
    def _run_corridor_analysis(
        self,
        dem_path: str,
        corners: List[Tuple[float, float]],
        bedding_zones: List[Dict[str, Any]],
        season: str,
        corridor_cell_m: float = 10.0,
    ) -> Optional[Dict[str, Any]]:
        """Build movement corridors from the DEM at corridor resolution.

        Reads the DEM at *corridor_cell_m* resolution (downsampled from
        native), computes terrain metrics, builds a cost surface, and
        routes least-cost paths between bedding zone nodes.

        Returns a serialisable dict (from CorridorResult.to_dict()) or
        None on failure.
        """
        try:
            import rasterio  # type: ignore
            from rasterio.warp import transform as rasterio_transform  # type: ignore
        except ImportError:
            logger.warning("CorridorAnalysis: rasterio not available")
            return None

        if len(bedding_zones) < 2:
            logger.info("CorridorAnalysis: <2 bedding zones, skipping corridor analysis")
            return None

        try:
            lats = [c[0] for c in corners]
            lons = [c[1] for c in corners]
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)

            lat_center = (min_lat + max_lat) / 2.0
            m_per_deg_lat = 111_132.0
            m_per_deg_lon = 111_320.0 * math.cos(math.radians(lat_center))

            with rasterio.open(dem_path) as src:
                xs, ys = rasterio_transform("EPSG:4326", src.crs, [min_lon, max_lon], [min_lat, max_lat])
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)

                window = rasterio.windows.from_bounds(
                    min_x, min_y, max_x, max_y, transform=src.transform,
                )
                window = window.round_offsets().round_lengths()

                # Target grid shape at corridor_cell_m resolution
                extent_lat_m = (max_lat - min_lat) * m_per_deg_lat
                extent_lon_m = (max_lon - min_lon) * m_per_deg_lon
                target_rows = max(10, int(extent_lat_m / corridor_cell_m))
                target_cols = max(10, int(extent_lon_m / corridor_cell_m))

                # Read DEM downsampled to target resolution.
                # Use bilinear resampling (not the default nearest-neighbor) so
                # derivative-based metrics (slope, TPI, curvature) do not alias
                # at the corridor scale.
                from rasterio.enums import Resampling as _Resampling
                elev = src.read(
                    1, window=window, masked=True,
                    out_shape=(target_rows, target_cols),
                    resampling=_Resampling.bilinear,
                ).astype("float32").filled(np.nan)

            if not np.isfinite(elev).any():
                logger.warning("CorridorAnalysis: DEM has no valid data in corridor window")
                return None

            # Replace NaN with nearest valid for metric computation
            elev = np.nan_to_num(elev, nan=float(np.nanmean(elev)))

            # Compute terrain metrics at corridor resolution
            metrics = compute_metrics(
                elev, corridor_cell_m,
                self.config.tpi_small_m,
                self.config.tpi_large_m,
            )

            slope_deg_grid = metrics["slope_deg"]
            ridgeline_grid = detect_ridgelines(
                metrics["tpi_large"], metrics["slope_deg"], metrics["relief_small"],
            )
            drainage_grid = detect_drainages(
                metrics["tpi_small"], metrics["tpi_large"],
                metrics["curvature"], metrics["relief_small"],
            )

            # Corridor score (same formula as main pipeline)
            corridor_grid = (
                np.clip(1.0 - np.abs(metrics["tpi_large"]) / np.maximum(metrics["relief_small"], 1.0), 0.0, 1.0)
                * np.clip(metrics["relief_small"] / 10.0, 0.0, 1.0)
            )

            # Build nodes from bedding zones (top 20 by quality)
            sorted_bz = sorted(bedding_zones, key=lambda b: b.get("bedding_quality", 0), reverse=True)
            nodes = [
                {
                    "lat": float(bz["lat"]),
                    "lon": float(bz["lon"]),
                    "kind": "bedding",
                    "name": f"Bed #{i + 1}",
                    "weight": float(bz.get("bedding_quality", 0.5)),
                }
                for i, bz in enumerate(sorted_bz[:20])
            ]

            config = CorridorConfig(cell_m=corridor_cell_m, max_node_pairs=50)
            engine = CorridorEngine(config)
            result = engine.run_from_metrics(
                slope_deg_grid, corridor_grid, ridgeline_grid, drainage_grid,
                origin_lat=min_lat, origin_lon=min_lon,
                nodes=nodes, season=season,
                m_per_deg_lat=m_per_deg_lat, m_per_deg_lon=m_per_deg_lon,
            )

            summary = result.to_dict()
            logger.info(
                "CorridorAnalysis: %d paths, %.1f%% corridor coverage",
                summary["num_paths"],
                summary["corridor_coverage_pct"],
            )
            return summary

        except Exception:
            logger.exception("CorridorAnalysis: failed")
            return None

    def _score_bedding_proximity(
        self,
        stand: Dict[str, Any],
        bedding_zones: List[Dict[str, Any]],
        wind_from_deg: Optional[float] = None,
    ) -> Tuple[float, Optional[Dict[str, Any]]]:
        """
        Score a stand candidate by proximity to predicted bedding zones,
        blended with bedding quality.

        Wind does NOT influence the ranking — advisory only.

        Returns (proximity_score, nearest_bedding_info).
        Optimal distance: 80-150m from bedding (close enough to intercept
        but far enough to avoid bumping deer).

        Blended score = 70% distance + 30% bedding quality.
        This ensures nearby high-quality beds outrank nearby mediocre ones,
        while preventing distant premium beds from overshadowing close viable ones.
        """
        if not bedding_zones:
            return 0.5, None  # Neutral if no bedding identified

        best_score = 0.0
        best_bed = None

        opt_min = self.config.bedding_optimal_distance_min
        opt_max = self.config.bedding_optimal_distance_max

        for bed in bedding_zones:
            dist_m = haversine(stand["lat"], stand["lon"], bed["lat"], bed["lon"])
            bearing_to_bed = bearing_between(stand["lat"], stand["lon"], bed["lat"], bed["lon"])

            # Distance scoring: optimal 80-150m
            if opt_min <= dist_m <= opt_max:
                dist_score = 1.0
            elif dist_m < opt_min:
                # Too close - risk of bumping deer
                dist_score = max(0.3, dist_m / opt_min)
            elif dist_m <= opt_max * 2:
                # 150-300m - still usable but not ideal
                dist_score = max(0.4, 1.0 - (dist_m - opt_max) / opt_max)
            else:
                # Too far
                dist_score = max(0.1, 1.0 - (dist_m - opt_max) / 500.0)

            # Blend: 70% distance + 30% bedding quality
            bed_quality = bed.get("bedding_quality", 0.5)
            blended = 0.70 * dist_score + 0.30 * bed_quality

            if blended > best_score:
                best_score = blended
                best_bed = {
                    "lat": bed["lat"],
                    "lon": bed["lon"],
                    "distance_m": round(dist_m, 1),
                    "bearing_deg": round(bearing_to_bed, 1),
                    "dist_score": round(dist_score, 2),
                    "bedding_quality": round(bed_quality, 3),
                }

        return best_score, best_bed
