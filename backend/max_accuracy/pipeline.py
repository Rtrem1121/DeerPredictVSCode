from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

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
from .wind import build_wind_options

logger = logging.getLogger(__name__)

# Max GEE concurrent requests (avoid hammering the API)
_GEE_MAX_WORKERS = 8


class MaxAccuracyPipeline:
    def __init__(self, config: MaxAccuracyConfig | None = None) -> None:
        self.config = config or MaxAccuracyConfig()

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
            run_hour = dt.hour
        except Exception:
            run_month, run_day, run_hour = 11, 10, 7  # default to peak rut morning

        rut_phase = classify_rut_phase(run_month, run_day)
        # Override season with more precise rut phase when applicable
        effective_season = rut_phase if rut_phase != "early_season" else season
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
                        "shelter_score": b.get("shelter_score", 0),
                        "canopy": b.get("gee_canopy", 0),
                        "slope_deg": b.get("slope_deg", 0),
                        "aspect_deg": b.get("aspect_deg", 0),
                        "bench_score": b.get("bench_score", 0),
                        "criteria_met": b.get("bedding_criteria_met", 0),
                    }
                    for b in bedding_zones
                ],
                "stand_recommendations": stand_recommendations,
            }
        except Exception as exc:
            logger.exception("MaxAccuracy: run failed")
            report_progress("error", {"error": str(exc)})
            return {"error": str(exc)}

    def _get_dem_path(self) -> str | None:
        dem_manager = DEMFileManager()
        lidar_files = dem_manager.get_files()
        for name, path in lidar_files.items():
            if "DEM" in str(name).upper():
                return path
        return next(iter(lidar_files.values()), None) if lidar_files else None

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

                elev = src.read(1, window=tile_window, masked=True).astype("float32").filled(np.nan)
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
                elev_denom = max(1e-6, elev_max - elev_min)

                # Compute ridgeline and drainage grids for this tile
                ridgeline_grid = detect_ridgelines(
                    metrics["tpi_large"], metrics["slope_deg"], metrics["relief_small"]
                )
                drainage_grid = detect_drainages(
                    metrics["tpi_small"], metrics["tpi_large"],
                    metrics["curvature"], metrics["relief_small"]
                )

                for lat, lon, row, col in tile_points:
                    local_row = row - row0_pad
                    local_col = col - col0_pad
                    if local_row < 0 or local_col < 0 or local_row >= elev.shape[0] or local_col >= elev.shape[1]:
                        continue
                    e = float(elev[local_row, local_col])
                    s = float(metrics["slope_deg"][local_row, local_col])
                    aspect = float(metrics["aspect_deg"][local_row, local_col])
                    curv = float(metrics["curvature"][local_row, local_col])
                    tpi_small = float(metrics["tpi_small"][local_row, local_col])
                    tpi_large = float(metrics["tpi_large"][local_row, local_col])
                    relief_small = float(metrics["relief_small"][local_row, local_col])
                    roughness = float(metrics["roughness"][local_row, local_col])

                    bench_score, saddle_score = score_bench_saddle(s, tpi_small, relief_small, curv)

                    # Unified slope scoring: plateau across 5-22° instead of narrow 10° peak
                    slope_pref = slope_preference(s)
                    # Ridge proximity: upper-third preference instead of arbitrary 60th percentile
                    elev_pref = ridge_proximity_preference(e, elev_min, elev_max)

                    corridor_score = clamp01(1.0 - (abs(tpi_large) / max(1.0, relief_small))) * clamp01(relief_small / 10.0)
                    shelter_score = clamp01(1.0 - (s / 20.0)) * clamp01((relief_small - abs(tpi_small)) / max(1.0, relief_small))
                    roughness_score = clamp01(roughness / 6.0)
                    curvature_score = clamp01(abs(curv) / 0.1)

                    # Aspect score: prefer south-facing (135-225°) for thermal advantage
                    # SE aspects (135-165°) get morning solar warming — also preferred
                    aspect_diff = angular_diff(aspect, 170.0)  # shifted slightly SE of due south
                    aspect_score = clamp01(1.0 - (aspect_diff / 100.0))  # wider tolerance

                    # Ridgeline and drainage from pre-computed grids
                    ridgeline_s = float(ridgeline_grid[local_row, local_col])
                    drainage_s = float(drainage_grid[local_row, local_col])

                    score = (
                        slope_pref * self.config.weights["slope_pref"]
                        + elev_pref * self.config.weights["elev_pref"]
                        + bench_score * self.config.weights["bench"]
                        + saddle_score * self.config.weights["saddle"]
                        + corridor_score * self.config.weights["corridor"]
                        + roughness_score * self.config.weights["roughness"]
                        + curvature_score * self.config.weights["curvature"]
                        + shelter_score * self.config.weights["shelter"]
                        + aspect_score * self.config.weights["aspect"]
                        + ridgeline_s * self.config.weights.get("ridgeline", 0.04)
                        + drainage_s * self.config.weights.get("drainage", 0.04)
                    )

                    scored.append(
                        {
                            "lat": float(lat),
                            "lon": float(lon),
                            "score": float(score),
                            "elevation_m": float(e),
                            "slope_deg": float(s),
                            "aspect_deg": float(aspect),
                            "tpi_small": float(tpi_small),
                            "tpi_large": float(tpi_large),
                            "relief_small": float(relief_small),
                            "curvature": float(curv),
                            "roughness": float(roughness),
                            "bench_score": float(bench_score),
                            "saddle_score": float(saddle_score),
                            "corridor_score": float(corridor_score),
                            "shelter_score": float(shelter_score),
                            "aspect_score": float(aspect_score),
                            "ridgeline_score": float(ridgeline_grid[local_row, local_col]),
                            "drainage_score": float(drainage_grid[local_row, local_col]),
                        }
                    )

                if progress_callback and tile_idx % 10 == 0:
                    progress_callback(
                        "terrain_tile",
                        {"tile": tile_idx, "tiles": total_tiles, "points": len(scored)},
                    )

        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[: self.config.max_candidates]

    def _enrich_with_gee(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        if not self.config.enable_gee or self.config.gee_sample_k <= 0:
            # Set neutral defaults so behavior scoring doesn't penalize
            for c in candidates:
                c.setdefault("gee_canopy", 50.0)  # neutral, not zero
                c.setdefault("gee_ndvi", 0.5)
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

            done = len(results)
            if done % 50 == 0 or done == max_k:
                logger.info("MaxAccuracy: GEE enrichment %s/%s done", done, max_k)

        # Apply results; for failures, use neutral defaults (not zero)
        for idx, candidate in enumerate(to_enrich):
            if idx in results:
                candidate.update(results[idx])
            else:
                candidate.setdefault("gee_canopy", 50.0)
                candidate.setdefault("gee_ndvi", 0.5)

        # Also set neutral defaults for candidates beyond max_k
        for candidate in candidates[max_k:]:
            candidate.setdefault("gee_canopy", 50.0)
            candidate.setdefault("gee_ndvi", 0.5)

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

        selected: List[Dict[str, Any]] = []
        selected_keys = set()

        for q in ("NE", "NW", "SE", "SW"):
            for candidate in buckets[q][: self.config.min_per_quadrant]:
                key = (candidate["lat"], candidate["lon"])
                if key in selected_keys:
                    continue
                selected_keys.add(key)
                selected.append(candidate)

        for candidate in candidates:
            if len(selected) >= self.config.top_k_stands:
                break
            key = (candidate["lat"], candidate["lon"])
            if key in selected_keys:
                continue
            selected_keys.add(key)
            selected.append(candidate)

        wind_direction = None
        if self.config.enable_wind and selected:
            try:
                wind_direction = build_wind_options(
                    selected[0]["lat"],
                    selected[0]["lon"],
                    season,
                    self.config.wind_offset_m,
                )[0]["wind_from_deg"]
            except Exception:
                logger.exception("MaxAccuracy: wind option seed failed")
                wind_direction = None

        for candidate in selected:
            if not self.config.enable_wind:
                candidate["wind_options"] = []
                continue
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
        if bedding_zones and wind_direction is not None:
            for candidate in selected:
                prox_score, nearest_bed = self._score_bedding_proximity(
                    candidate, bedding_zones, wind_direction
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
        
        Criteria:
        - High shelter score (wind/thermal protection)
        - High canopy cover (security from above)
        - Moderate slope (drainage, comfort, visibility uphill)
        - Bench character (flat spots on hillsides)
        - South-facing aspect bonus (thermal advantage)
        - Roughness minimum (filter out flat open fields)
        
        Note: Canopy (GEE/NDVI) removed - it measures leaves not tree structure,
        useless after October in Vermont. Roughness filters out open fields instead.
        """
        bedding = []
        for c in candidates:
            shelter = float(c.get("shelter_score", 0))
            slope = float(c.get("slope_deg", 0))
            bench = float(c.get("bench_score", 0))
            aspect_score = float(c.get("aspect_score", 0))
            roughness = float(c.get("roughness", 0))

            # Terrain-only bedding filter
            meets_shelter = shelter >= self.config.bedding_min_shelter
            meets_slope = self.config.bedding_slope_min <= slope <= self.config.bedding_slope_max
            meets_bench = bench >= self.config.bedding_min_bench
            meets_aspect = aspect_score >= getattr(self.config, 'bedding_min_aspect_score', 0.4)
            meets_roughness = roughness >= getattr(self.config, 'bedding_min_roughness', 2.0)

            # Require: slope in range + bench terrain + shelter + roughness (not a field)
            # At least 3 of 4 main criteria met
            core_terrain = meets_slope and meets_bench
            criteria_met = sum([meets_shelter, meets_slope, meets_bench, meets_aspect])
            
            # Must have core terrain + shelter + roughness, and at least 3 of 4 criteria
            if core_terrain and meets_shelter and meets_roughness and criteria_met >= 3:
                c["is_probable_bedding"] = True
                c["bedding_criteria_met"] = criteria_met
                c["bedding_criteria"] = {
                    "shelter": meets_shelter,
                    "slope": meets_slope,
                    "bench": meets_bench,
                    "aspect": meets_aspect,
                    "roughness": meets_roughness,
                }
                bedding.append(c)

        logger.info(
            "MaxAccuracy: identified %s probable bedding zones from %s candidates",
            len(bedding),
            len(candidates),
        )
        return bedding

    def _score_bedding_proximity(
        self,
        stand: Dict[str, Any],
        bedding_zones: List[Dict[str, Any]],
        wind_from_deg: float,
    ) -> Tuple[float, Optional[Dict[str, Any]]]:
        """
        Score a stand candidate by its relationship to nearby bedding zones.
        
        Returns (proximity_score, nearest_bedding_info).
        Optimal setup: 80-150m from bedding, downwind so scent blows away from deer.
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

            # Wind scoring: stand should be DOWNWIND of bedding
            # Best: wind blows FROM bedding TOWARD stand (scent carries away from deer)
            wind_to_deg = (wind_from_deg + 180.0) % 360.0
            angle_diff_val = angular_diff(bearing_to_bed, wind_to_deg)

            if angle_diff_val < 30:
                # Excellent - directly downwind
                wind_score = 1.0
            elif angle_diff_val < 60:
                # Good - mostly downwind
                wind_score = 0.8
            elif angle_diff_val < 90:
                # Marginal - crosswind
                wind_score = 0.5
            else:
                # Poor - upwind of bedding (scent blows toward deer)
                wind_score = 0.2

            combined = dist_score * 0.55 + wind_score * 0.45
            if combined > best_score:
                best_score = combined
                best_bed = {
                    "lat": bed["lat"],
                    "lon": bed["lon"],
                    "distance_m": round(dist_m, 1),
                    "bearing_deg": round(bearing_to_bed, 1),
                    "dist_score": round(dist_score, 2),
                    "wind_score": round(wind_score, 2),
                }

        return best_score, best_bed
