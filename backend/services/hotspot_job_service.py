from __future__ import annotations

import asyncio
import json
import math
import os
import random
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from zoneinfo import ZoneInfo

from backend.utils.geo import haversine


try:
    import folium  # type: ignore
except Exception:  # pragma: no cover
    folium = None


def _meters_to_radians(meters: float) -> float:
    return meters / 6371000.0


def _wrap_lon(lon: float) -> float:
    return ((lon + 180.0) % 360.0) - 180.0


_COMPASS_16 = [
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
]


def _degrees_to_compass(degrees: Any) -> Optional[str]:
    try:
        if degrees is None:
            return None
        d = float(degrees) % 360.0
        return _COMPASS_16[int((d + 11.25) / 22.5) % 16]
    except Exception:
        return None


def _parse_dt_to_eastern(date_time: str) -> datetime:
    dt = datetime.fromisoformat(date_time.replace("Z", "+00:00"))
    eastern = ZoneInfo("America/New_York")
    return dt.astimezone(eastern) if dt.tzinfo else dt.replace(tzinfo=eastern)


def _points_center(points: List[Tuple[float, float]]) -> Tuple[float, float]:
    if not points:
        return 44.0, -72.5
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def _try_make_polygon(corners: List[Tuple[float, float]]):
    try:
        from shapely.geometry import Polygon  # type: ignore

        if len(corners) < 3:
            return None
        # shapely expects (x,y) = (lon,lat)
        ring = [(lon, lat) for lat, lon in corners]
        return Polygon(ring)
    except Exception:
        return None


def _point_in_polygon(lat: float, lon: float, polygon) -> bool:
    if polygon is None:
        return True
    try:
        from shapely.geometry import Point  # type: ignore

        return bool(polygon.contains(Point(lon, lat)) or polygon.touches(Point(lon, lat)))
    except Exception:
        return True


def _sample_points_in_polygon(
    corners: List[Tuple[float, float]],
    n: int,
    seed: Optional[int] = None,
) -> List[Tuple[float, float]]:
    if not corners:
        return []

    rng = random.Random(seed)
    lats = [c[0] for c in corners]
    lons = [c[1] for c in corners]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    polygon = _try_make_polygon(corners)

    points: List[Tuple[float, float]] = []
    center = _points_center(corners)
    points.append(center)

    max_tries = max(2000, n * 200)
    tries = 0
    while len(points) < n and tries < max_tries:
        tries += 1
        lat = rng.uniform(min_lat, max_lat)
        lon = rng.uniform(min_lon, max_lon)
        lon = _wrap_lon(lon)
        if _point_in_polygon(lat, lon, polygon):
            points.append((lat, lon))

    # If polygon containment fails, we still return what we have.
    return points[:n]


def _stable_seed_from_corners(corners: List[Tuple[float, float]]) -> int:
    if not corners:
        return 0
    try:
        import hashlib

        normalized = [(round(lat, 6), round(lon, 6)) for lat, lon in corners]
        payload = "|".join(f"{lat:.6f},{lon:.6f}" for lat, lon in normalized)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)
    except Exception:
        return 0


def _generate_grid_points_in_polygon(
    corners: List[Tuple[float, float]],
    target_n: int,
) -> List[Tuple[float, float]]:
    """Generate a dense grid across the property bbox and keep points inside polygon.

    This mirrors the analyzer-style "generate ~100k points" flow but stays deterministic
    and keeps containment checks inside the polygon when available.
    """

    if not corners:
        return []

    lats = [c[0] for c in corners]
    lons = [c[1] for c in corners]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    polygon = _try_make_polygon(corners)

    # Oversample the grid so that after polygon filtering we land near target_n.
    # For convex-ish polygons in their bbox, ~50% yield is common.
    oversample = 2.0
    grid_size = max(8, int(math.sqrt(max(1, target_n) * oversample)))

    try:
        import numpy as np  # type: ignore

        lat_vals = np.linspace(min_lat, max_lat, grid_size, dtype=float)
        lon_vals = np.linspace(min_lon, max_lon, grid_size, dtype=float)
        inside: List[Tuple[float, float]] = []
        for lat in lat_vals:
            for lon in lon_vals:
                lon_w = _wrap_lon(float(lon))
                lat_f = float(lat)
                if _point_in_polygon(lat_f, lon_w, polygon):
                    inside.append((lat_f, lon_w))
    except Exception:
        # Fallback: deterministic pseudo-grid without numpy
        inside = []
        for i in range(grid_size):
            lat = min_lat + (max_lat - min_lat) * (i / max(1, grid_size - 1))
            for j in range(grid_size):
                lon = min_lon + (max_lon - min_lon) * (j / max(1, grid_size - 1))
                lon = _wrap_lon(lon)
                if _point_in_polygon(lat, lon, polygon):
                    inside.append((lat, lon))

    if not inside:
        return []

    # Always include the property center as a stable anchor.
    center = _points_center(corners)
    if center not in inside and _point_in_polygon(center[0], center[1], polygon):
        inside.insert(0, center)

    # Downsample evenly to target_n (keeps spatial coverage).
    if len(inside) <= target_n:
        return inside
    step = max(1, len(inside) // max(1, target_n))
    sampled = inside[::step][:target_n]
    return sampled


def _pick_best_dem_file(lidar_files: Dict[str, str]) -> Optional[str]:
    if not lidar_files:
        return None
    # Prefer true DEM over hillshade.
    for name, path in lidar_files.items():
        if "DEM" in str(name).upper():
            return path
    return next(iter(lidar_files.values()), None)


def _lidar_shortlist_points(
    corners: List[Tuple[float, float]],
    points: List[Tuple[float, float]],
    *,
    sample_radius_m: int,
    top_k: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Score many points quickly using local LiDAR/DEM and return top K.

    Implementation notes:
    - Uses a DEM window covering the property bbox (fast) when feasible.
    - Falls back to per-point extraction if window read fails.
    """

    from backend.services.lidar_processor import DEMFileManager, RASTERIO_AVAILABLE  # type: ignore

    if not RASTERIO_AVAILABLE:
        return [], {"lidar_available": False, "reason": "rasterio_not_available"}

    dem_manager = DEMFileManager()
    lidar_files = dem_manager.get_files()
    dem_path = _pick_best_dem_file(lidar_files)
    if not dem_path:
        return [], {"lidar_available": False, "reason": "no_lidar_files"}

    try:
        import numpy as np  # type: ignore
        import rasterio  # type: ignore
        from rasterio.windows import from_bounds  # type: ignore
        from rasterio.warp import transform  # type: ignore

        # Property bounds with a small padding so slope neighborhood doesn't clip.
        lats = [c[0] for c in corners]
        lons = [c[1] for c in corners]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        with rasterio.open(dem_path) as src:
            # Transform bbox to raster CRS
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

            # Guardrail: if the window is too massive, fall back to per-point reads.
            max_cells = int(os.getenv("HOTSPOT_LIDAR_MAX_WINDOW_CELLS", "50000000"))
            if int(elevation.shape[0]) * int(elevation.shape[1]) > max_cells:
                raise RuntimeError(f"DEM window too large: {elevation.shape}")

            # Convert masked array -> float with NaNs
            elev = elevation.astype("float32").filled(np.nan)
            valid = np.isfinite(elev)
            if not bool(valid.any()):
                raise RuntimeError("No valid DEM values in window")

            # Precompute slope (Horn-like approximation via gradient magnitude)
            xres = float(abs(src.res[0]))
            yres = float(abs(src.res[1]))
            gy, gx = np.gradient(elev, yres, xres)
            slope_rad = np.arctan(np.sqrt(gx * gx + gy * gy))
            slope_deg = np.degrees(slope_rad)

            # Curvature (Laplacian) for micro-terrain texture
            dgy_dy, dgy_dx = np.gradient(gy, yres, xres)
            dgx_dy, dgx_dx = np.gradient(gx, yres, xres)
            curvature = dgy_dy + dgx_dx

            elev_min = float(np.nanmin(elev))
            elev_max = float(np.nanmax(elev))
            elev_range = max(1e-6, elev_max - elev_min)

            # Affine transform for the window: src.window_transform
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

            base_scored: List[Dict[str, Any]] = []
            for (lat, lon) in points:
                sampled = _sample_at(lat, lon)
                if not sampled:
                    continue
                row, col, e, s = sampled

                # Fast terrain heuristic for pre-ranking.
                slope_pref = max(0.0, 1.0 - (abs(s - 10.0) / 10.0))  # peak at 10°, 0 at 0/20
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

                # Bench: low slope, near-neutral TPI
                bench_score = _clamp01(1.0 - (local_slope_mean / 12.0)) * _clamp01(1.0 - (abs(tpi_norm) * 2.0))

                # Saddle-ish: neutral TPI with surrounding relief + varied slopes
                saddle_score = _clamp01(local_relief / 12.0) * _clamp01(1.0 - (abs(tpi_norm) * 2.0)) * _clamp01(local_slope_std / 5.0)

                # Corridor: moderate slope + some relief (travelable edges)
                corridor_score = _clamp01(1.0 - (abs(local_slope_mean - 8.0) / 8.0)) * _clamp01(local_relief / 10.0)

                # Roughness + curvature: micro-terrain texture often used by mature bucks
                roughness_score = _clamp01(local_roughness / 6.0)
                curvature_score = _clamp01(local_curv_mean / 0.08)

                # Shelter (leeward proxy): slightly below local mean with relief + moderate slope
                shelter_score = _clamp01((-tpi_norm) * 1.5) * _clamp01(local_relief / 15.0) * _clamp01(1.0 - (abs(local_slope_mean - 10.0) / 12.0))

                # Large-scale position: avoid exposed ridges/valleys at broader scale
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


def _extract_stand_points(prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
    stands: List[Dict[str, Any]] = []

    # Capture a small amount of contextual metadata so the "Best Stand Site" popup
    # can explain the recommendation (wind, situation) without storing the full
    # prediction payload.
    wind_thermal = prediction.get("wind_thermal_analysis") if isinstance(prediction, dict) else None
    if not isinstance(wind_thermal, dict):
        wind_thermal = None

    wind_summary = prediction.get("wind_summary") if isinstance(prediction, dict) else None
    if not isinstance(wind_summary, dict):
        wind_summary = None
    wind_overall = wind_summary.get("overall_wind_conditions") if isinstance(wind_summary, dict) else None
    if not isinstance(wind_overall, dict):
        wind_overall = None

    context_summary = prediction.get("context_summary") if isinstance(prediction, dict) else None
    if not isinstance(context_summary, dict):
        context_summary = None

    optimized = prediction.get("optimized_points") if isinstance(prediction, dict) else None
    if isinstance(optimized, dict):
        stand_sites = optimized.get("stand_sites")
        if isinstance(stand_sites, list):
            for s in stand_sites:
                if not isinstance(s, dict):
                    continue
                lat = s.get("lat")
                lon = s.get("lon")
                if lat is None or lon is None:
                    continue
                stands.append(
                    {
                        "lat": float(lat),
                        "lon": float(lon),
                        "score": float(s.get("score", 0.0) or 0.0),
                        "strategy": s.get("strategy") or s.get("description") or "stand_site",
                        "source": "optimized_points.stand_sites",
                        "description": s.get("description"),
                        "confidence": s.get("confidence"),
                        "wind_thermal": wind_thermal,
                        "wind_overall": wind_overall,
                        "context_summary": context_summary,
                        "raw": s,
                    }
                )

    mba = prediction.get("mature_buck_analysis") if isinstance(prediction, dict) else None
    if isinstance(mba, dict):
        stand_recs = mba.get("stand_recommendations")
        if isinstance(stand_recs, list):
            for s in stand_recs:
                if not isinstance(s, dict):
                    continue
                lat = s.get("lat")
                lon = s.get("lon")
                if lat is None or lon is None:
                    continue
                stands.append(
                    {
                        "lat": float(lat),
                        "lon": float(lon),
                        "score": float(s.get("score", 0.0) or 0.0),
                        "strategy": s.get("strategy") or s.get("type") or "stand_recommendation",
                        "source": "mature_buck_analysis.stand_recommendations",
                        "description": s.get("description") or s.get("reason"),
                        "confidence": s.get("confidence"),
                        "wind_thermal": wind_thermal,
                        "wind_overall": wind_overall,
                        "context_summary": context_summary,
                        "raw": s,
                    }
                )

    return stands


def _stand_summary_for_report(stand: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "lat": float(stand.get("lat")) if stand.get("lat") is not None else None,
        "lon": float(stand.get("lon")) if stand.get("lon") is not None else None,
        "score": float(stand.get("score", 0.0) or 0.0),
        "strategy": stand.get("strategy"),
        "source": stand.get("source"),
        "description": stand.get("description"),
        "confidence": stand.get("confidence"),
        "wind_thermal": stand.get("wind_thermal"),
        "wind_overall": stand.get("wind_overall"),
        "context_summary": stand.get("context_summary"),
    }


def _best_site_score_0_200(*, support: int, avg_stand_score_0_10: float) -> float:
    """Composite score intended for UX (approx 0..200).

    The stand generator's native score is typically ~0..10.
    Users previously saw a larger-scale score (~165), so we expose a stable,
    explainable composite score that incorporates both:
    - cluster support (repeatability across samples)
    - mean stand score within that cluster
    """

    s = 15.0 + (5.0 * float(max(0, support))) + (10.0 * float(max(0.0, min(10.0, avg_stand_score_0_10))))
    return float(max(0.0, min(200.0, s)))


def _cluster_haversine(points: List[Dict[str, Any]], epsilon_m: float, min_samples: int) -> List[Dict[str, Any]]:
    if not points:
        return []

    try:
        import numpy as np  # type: ignore
        from sklearn.cluster import DBSCAN  # type: ignore

        coords = np.radians(np.array([[p["lat"], p["lon"]] for p in points], dtype=float))
        clustering = DBSCAN(eps=_meters_to_radians(epsilon_m), min_samples=min_samples, metric="haversine")
        labels = clustering.fit_predict(coords)

        clusters: Dict[int, List[int]] = {}
        for idx, label in enumerate(labels):
            if int(label) == -1:
                continue
            clusters.setdefault(int(label), []).append(idx)

        out: List[Dict[str, Any]] = []
        for label, idxs in clusters.items():
            cluster_points = [points[i] for i in idxs]
            centroid_lat = sum(p["lat"] for p in cluster_points) / len(cluster_points)
            centroid_lon = sum(p["lon"] for p in cluster_points) / len(cluster_points)

            # medoid = point with min sum distance
            best_i = 0
            best_sum = float("inf")
            for i, p in enumerate(cluster_points):
                s = 0.0
                for q in cluster_points:
                    s += haversine(p["lat"], p["lon"], q["lat"], q["lon"])
                if s < best_sum:
                    best_sum = s
                    best_i = i

            medoid = cluster_points[best_i]
            best_point = max(cluster_points, key=lambda s: float(s.get("score", 0.0)))
            avg_score = sum(p.get("score", 0.0) for p in cluster_points) / len(cluster_points)
            out.append(
                {
                    "cluster_id": label,
                    "size": len(cluster_points),
                    "centroid": {"lat": centroid_lat, "lon": centroid_lon},
                    "medoid": {"lat": medoid["lat"], "lon": medoid["lon"]},
                    "avg_score": avg_score,
                    "best_score": float(best_point.get("score", 0.0) or 0.0),
                    "medoid_point": _stand_summary_for_report(medoid),
                    "best_point": _stand_summary_for_report(best_point),
                    "strategies": sorted({str(p.get("strategy") or "") for p in cluster_points if p.get("strategy")}),
                    "points": [
                        {
                            "lat": p["lat"],
                            "lon": p["lon"],
                            "score": p.get("score", 0.0),
                            "strategy": p.get("strategy"),
                            "source": p.get("source"),
                        }
                        for p in cluster_points
                    ],
                }
            )

        out.sort(key=lambda c: (c["size"], c["avg_score"]), reverse=True)
        return out

    except Exception:
        # Fallback: no clustering available
        return []


def _build_map_html(
    corners: List[Tuple[float, float]],
    stand_points: List[Dict[str, Any]],
    clusters: List[Dict[str, Any]],
    baseline: Optional[Dict[str, Any]],
) -> str:
    if folium is None:
        return "<html><body><h3>folium not available</h3></body></html>"

    center_lat, center_lon = _points_center(corners or [(p["lat"], p["lon"]) for p in stand_points])
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15)

    if corners and len(corners) >= 3:
        folium.Polygon(locations=[[lat, lon] for lat, lon in corners], color="#2563eb", weight=3, fill=False).add_to(m)

    for p in stand_points[:500]:
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=4,
            color="#64748b",
            fill=True,
            fill_opacity=0.6,
            tooltip=f"{p.get('strategy','stand')} @ ({float(p['lat']):.6f}, {float(p['lon']):.6f})",
            popup=(
                f"<b>Stand:</b> {p.get('strategy','stand')}<br/>"
                f"<b>Score:</b> {float(p.get('score',0.0) or 0.0):.1f}<br/>"
                f"<b>Lat/Lon:</b> {float(p['lat']):.6f}, {float(p['lon']):.6f}"
            ),
        ).add_to(m)

    for c in clusters[:10]:
        centroid = c.get("centroid") or {}
        c_lat = float(centroid.get("lat"))
        c_lon = float(centroid.get("lon"))
        med = c.get("medoid") or {}
        m_lat = float(med.get("lat")) if med.get("lat") is not None else None
        m_lon = float(med.get("lon")) if med.get("lon") is not None else None
        popup_lines = [
            f"<b>Cluster:</b> {c.get('cluster_id')}",
            f"<b>Size:</b> {c.get('size')}",
            f"<b>Avg score:</b> {float(c.get('avg_score',0.0) or 0.0):.1f}",
            f"<b>Centroid:</b> {c_lat:.6f}, {c_lon:.6f}",
        ]
        if m_lat is not None and m_lon is not None:
            popup_lines.append(f"<b>Medoid:</b> {m_lat:.6f}, {m_lon:.6f}")
        folium.CircleMarker(
            location=[c_lat, c_lon],
            radius=8,
            color="#f97316",
            fill=True,
            fill_opacity=0.8,
            tooltip=f"Cluster {c.get('cluster_id')} @ ({c_lat:.6f}, {c_lon:.6f})",
            popup="<br/>".join(popup_lines),
        ).add_to(m)

    if baseline:
        popup_lines: List[str] = []
        popup_lines.append(f"<b>Lat/Lon:</b> {float(baseline['lat']):.6f}, {float(baseline['lon']):.6f}")
        score_200 = baseline.get("best_site_score_0_200")
        if isinstance(score_200, (int, float)):
            popup_lines.append(f"<b>Composite score:</b> {float(score_200):.0f}/200")
        stand_score = baseline.get("stand_score_0_10")
        if isinstance(stand_score, (int, float)):
            popup_lines.append(f"<b>Stand score:</b> {float(stand_score):.1f}/10")
        popup_lines.append(f"<b>Cluster support:</b> {int(baseline.get('supporting_predictions', 0))}")
        avg_cluster = baseline.get("cluster_avg_score_0_10")
        if isinstance(avg_cluster, (int, float)):
            popup_lines.append(f"<b>Cluster avg:</b> {float(avg_cluster):.1f}/10")

        desc = baseline.get("description")
        if isinstance(desc, str) and desc.strip():
            popup_lines.append(f"<b>Why here:</b> {desc}")

        wind = baseline.get("wind_thermal")
        if isinstance(wind, dict):
            wd = wind.get("wind_direction")
            ws = wind.get("wind_speed")
            prot = wind.get("wind_protection")
            therm = wind.get("thermal_advantage")
            optimal = wind.get("optimal_wind_alignment")
            scent_dir = wind.get("scent_cone_direction")
            approach = wind.get("optimal_approach_bearing")
            if wd is not None and ws is not None:
                wd_compass = _degrees_to_compass(wd)
                wd_label = f"{wd_compass} ({float(wd):.0f}°)" if wd_compass else f"{float(wd):.0f}°"
                popup_lines.append(f"<b>Wind (at run time):</b> {wd_label} @ {float(ws):.1f} mph")
            if prot is not None:
                popup_lines.append(f"<b>Wind protection:</b> {prot}")
            if therm is not None:
                popup_lines.append(f"<b>Thermal advantage:</b> {therm}")
            if isinstance(optimal, bool):
                popup_lines.append(f"<b>Optimal wind alignment:</b> {'Yes' if optimal else 'No'}")
            if scent_dir is not None:
                scent_compass = _degrees_to_compass(scent_dir)
                scent_label = f"{scent_compass} ({float(scent_dir):.0f}°)" if scent_compass else f"{float(scent_dir):.0f}°"
                popup_lines.append(f"<b>Scent cone travels toward:</b> {scent_label}")
            if approach is not None:
                app_compass = _degrees_to_compass(approach)
                app_label = f"{app_compass} ({float(approach):.0f}°)" if app_compass else f"{float(approach):.0f}°"
                popup_lines.append(f"<b>Suggested approach bearing:</b> {app_label}")

        overall = baseline.get("wind_overall")
        if isinstance(overall, dict):
            prevailing = overall.get("prevailing_wind")
            effective = overall.get("effective_wind")
            rating = overall.get("hunting_rating")
            # These strings often already include compass (e.g., "NW at 3.8 mph").
            if isinstance(prevailing, str) and prevailing.strip():
                popup_lines.append(f"<b>Prevailing wind:</b> {prevailing}")
            if isinstance(effective, str) and effective.strip():
                popup_lines.append(f"<b>Effective wind (terrain/thermals):</b> {effective}")
            if rating is not None:
                popup_lines.append(f"<b>Wind hunting rating:</b> {rating}")

        ctx = baseline.get("context_summary")
        if isinstance(ctx, dict):
            situation = ctx.get("situation")
            guidance = ctx.get("primary_guidance")
            if isinstance(situation, str) and situation.strip():
                popup_lines.append(f"<b>Situation:</b> {situation}")
            if isinstance(guidance, str) and guidance.strip():
                popup_lines.append(f"<b>Guidance:</b> {guidance}")

        folium.Marker(
            location=[baseline["lat"], baseline["lon"]],
            tooltip=(
                f"Best Stand Site @ ({float(baseline['lat']):.6f}, {float(baseline['lon']):.6f})"
                + (f" | {float(score_200):.0f}/200" if isinstance(score_200, (int, float)) else "")
            ),
            popup="<br/>".join(popup_lines) or "Best Stand Site",
            icon=folium.Icon(color="red", icon="star"),
        ).add_to(m)

    return m.get_root().render()


@dataclass
class HotspotJob:
    job_id: str
    status: str
    created_at: str
    updated_at: str
    total: int
    completed: int
    message: str
    error: Optional[str] = None
    report_path: Optional[str] = None
    map_path: Optional[str] = None


class HotspotJobService:
    def __init__(self) -> None:
        self._jobs: Dict[str, HotspotJob] = {}
        self._lock = threading.Lock()

    def _job_state_path(self, job_id: str) -> Path:
        jobs_dir = Path(os.getenv("HOTSPOT_JOBS_DIR", "/app/data/hotspot_jobs"))
        return jobs_dir / job_id / "job_state.json"

    def _persist_job_state(self, job: HotspotJob) -> None:
        try:
            state_path = self._job_state_path(job.job_id)
            state_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "job_id": job.job_id,
                "status": job.status,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "total": job.total,
                "completed": job.completed,
                "message": job.message,
                "error": job.error,
                "report_path": job.report_path,
                "map_path": job.map_path,
            }
            state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            return

    def _recover_job_from_disk(self, job_id: str) -> Optional[HotspotJob]:
        jobs_dir = Path(os.getenv("HOTSPOT_JOBS_DIR", "/app/data/hotspot_jobs"))
        job_dir = jobs_dir / job_id
        if not job_dir.exists():
            return None

        state_path = job_dir / "job_state.json"
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
                status = state.get("status") or "unknown"
                report_path = state.get("report_path")
                map_path = state.get("map_path")
                if status != "completed" and not report_path:
                    status = "interrupted"
                return HotspotJob(
                    job_id=job_id,
                    status=status,
                    created_at=state.get("created_at") or datetime.utcnow().isoformat() + "Z",
                    updated_at=state.get("updated_at") or datetime.utcnow().isoformat() + "Z",
                    total=int(state.get("total") or 0),
                    completed=int(state.get("completed") or 0),
                    message=state.get("message") or "Recovered from disk",
                    error=state.get("error"),
                    report_path=report_path,
                    map_path=map_path,
                )
            except Exception:
                pass

        report_path = job_dir / "hotspot_report.json"
        map_path = job_dir / "hotspot_map.html"
        if not report_path.exists() and not map_path.exists():
            return None

        now = datetime.utcnow().isoformat() + "Z"
        status = "completed" if report_path.exists() else "unknown"
        job = HotspotJob(
            job_id=job_id,
            status=status,
            created_at=now,
            updated_at=now,
            total=0,
            completed=0,
            message="Recovered from disk",
            report_path=str(report_path) if report_path.exists() else None,
            map_path=str(map_path) if map_path.exists() else None,
        )
        return job

    def create_job(self, total: int, message: str) -> HotspotJob:
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        job = HotspotJob(
            job_id=job_id,
            status="queued",
            created_at=now,
            updated_at=now,
            total=total,
            completed=0,
            message=message,
        )
        with self._lock:
            self._jobs[job_id] = job
        self._persist_job_state(job)
        return job

    def get_job(self, job_id: str) -> Optional[HotspotJob]:
        with self._lock:
            job = self._jobs.get(job_id)
        if job:
            return job

        recovered = self._recover_job_from_disk(job_id)
        if recovered:
            with self._lock:
                self._jobs[job_id] = recovered
            return recovered
        return None

    def update_job(self, job_id: str, **kwargs) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for k, v in kwargs.items():
                if hasattr(job, k):
                    setattr(job, k, v)
            job.updated_at = datetime.utcnow().isoformat() + "Z"
        self._persist_job_state(job)

    async def run_job(
        self,
        job_id: str,
        *,
        corners: List[Tuple[float, float]],
        mode: str,
        num_sample_points: int,
        lidar_grid_points: int,
        lidar_top_k: int,
        lidar_sample_radius_m: int,
        epsilon_meters: float,
        min_samples: int,
        date_time: str,
        season: str,
        hunting_pressure: str,
    ) -> None:
        from backend.services.prediction_service import get_prediction_service

        jobs_dir = Path(os.getenv("HOTSPOT_JOBS_DIR", "/app/data/hotspot_jobs"))
        jobs_dir.mkdir(parents=True, exist_ok=True)
        job_dir = jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        self.update_job(job_id, status="running", message="Preparing hotspot run")

        effective_epsilon = epsilon_meters
        if season in ["rut", "pre_rut", "post_rut"]:
            effective_epsilon = max(float(epsilon_meters), 150.0)

        service = get_prediction_service()
        target_dt = _parse_dt_to_eastern(date_time)

        lidar_shortlist: List[Dict[str, Any]] = []
        lidar_meta: Dict[str, Any] = {}

        if mode == "lidar_first":
            self.update_job(job_id, message=f"Generating grid (~{lidar_grid_points} points)")
            grid_points = _generate_grid_points_in_polygon(corners, lidar_grid_points)

            self.update_job(job_id, message=f"Scoring {len(grid_points)} points with LiDAR (local DEM)")
            lidar_shortlist, lidar_meta = _lidar_shortlist_points(
                corners,
                grid_points,
                sample_radius_m=lidar_sample_radius_m,
                top_k=lidar_top_k,
            )

            if not lidar_shortlist:
                # Fallback: if LiDAR scoring fails, degrade to sample_predict mode.
                self.update_job(job_id, message="LiDAR shortlist unavailable; falling back to random sample predictions")
                mode = "sample_predict"
            else:
                total = len(lidar_shortlist)
                self.update_job(job_id, total=total, completed=0, message=f"Running full predictions for top {total} LiDAR candidates")
        else:
            self.update_job(job_id, message="Sampling points inside property")
            seed = _stable_seed_from_corners(corners)
            sample_points = _sample_points_in_polygon(corners, num_sample_points, seed=seed)
            total = len(sample_points)
            self.update_job(job_id, total=total, completed=0, message="Running predictions")

        all_stands: List[Dict[str, Any]] = []
        per_point_best: List[Dict[str, Any]] = []

        # Decide which query points to run full predictions on.
        if mode == "lidar_first" and lidar_shortlist:
            query_points = [(r["lat"], r["lon"]) for r in lidar_shortlist]
        else:
            seed = _stable_seed_from_corners(corners)
            query_points = _sample_points_in_polygon(corners, num_sample_points, seed=seed)

        total = len(query_points)
        max_concurrency = int(os.getenv("HOTSPOT_PREDICTION_CONCURRENCY", "3"))
        max_concurrency = max(1, min(10, max_concurrency))
        self.update_job(job_id, message=f"Running predictions ({total} points, concurrency={max_concurrency})", completed=0, total=total)

        sem = asyncio.Semaphore(max_concurrency)

        async def _predict_one(idx: int, lat: float, lon: float) -> Tuple[int, float, float, Any]:
            async with sem:
                self.update_job(job_id, message=f"Predicting {idx}/{total}")
                return (
                    idx,
                    lat,
                    lon,
                    await asyncio.wait_for(
                        service.predict(
                            lat=lat,
                            lon=lon,
                            time_of_day=target_dt.hour,
                            season=season,
                            hunting_pressure=hunting_pressure,
                            target_datetime=target_dt,
                        ),
                        timeout=180,
                    ),
                )

        tasks = [asyncio.create_task(_predict_one(i, lat, lon)) for i, (lat, lon) in enumerate(query_points, 1)]

        done_count = 0
        for fut in asyncio.as_completed(tasks):
            try:
                idx, lat, lon, prediction = await fut
                stands = _extract_stand_points(prediction)
                all_stands.extend(stands)

                if stands:
                    best = max(stands, key=lambda s: float(s.get("score", 0.0)))
                    per_point_best.append(
                        {
                            "query_lat": lat,
                            "query_lon": lon,
                            "best_lat": best["lat"],
                            "best_lon": best["lon"],
                            "best_score": best.get("score", 0.0),
                            "best_strategy": best.get("strategy"),
                        }
                    )
            except Exception as e:
                # We do not know which index failed here reliably; record the error generally.
                all_stands.append(
                    {
                        "lat": None,
                        "lon": None,
                        "score": 0.0,
                        "strategy": "prediction_error",
                        "source": "error",
                        "error": str(e),
                    }
                )
            finally:
                done_count += 1
                self.update_job(job_id, completed=done_count, message=f"Predictions: {done_count}/{total}")

        self.update_job(job_id, message="Clustering stand points")
        clusters = _cluster_haversine(all_stands, effective_epsilon, min_samples)

        baseline: Optional[Dict[str, Any]] = None
        best_stand_site: Optional[Dict[str, Any]] = None
        if clusters:
            top = clusters[0]
            medoid_point = top.get("medoid_point") if isinstance(top, dict) else None
            if not isinstance(medoid_point, dict):
                medoid_point = {"lat": float(top["medoid"]["lat"]), "lon": float(top["medoid"]["lon"])}
            support = int(top.get("size", 0) or 0)
            avg_score = float(top.get("avg_score", 0.0) or 0.0)
            best_stand_site = {
                "lat": float(medoid_point.get("lat")),
                "lon": float(medoid_point.get("lon")),
                "supporting_predictions": support,
                "cluster_avg_score_0_10": avg_score,
                "stand_score_0_10": float(medoid_point.get("score", 0.0) or 0.0),
                "best_site_score_0_200": _best_site_score_0_200(support=support, avg_stand_score_0_10=avg_score),
                "strategy": medoid_point.get("strategy"),
                "description": medoid_point.get("description"),
                "confidence": medoid_point.get("confidence"),
                "wind_thermal": medoid_point.get("wind_thermal"),
                "wind_overall": medoid_point.get("wind_overall"),
                "context_summary": medoid_point.get("context_summary"),
                "sources": ["cluster_medoid"],
                "reason": "Densest consensus cluster medoid (most repeatable across sample points)",
            }
        elif all_stands:
            best = max(all_stands, key=lambda s: float(s.get("score", 0.0)))

            support = 1
            avg_score = float(best.get("score", 0.0) or 0.0)
            best_stand_site = {
                "lat": float(best["lat"]),
                "lon": float(best["lon"]),
                "supporting_predictions": support,
                "cluster_avg_score_0_10": avg_score,
                "stand_score_0_10": float(best.get("score", 0.0) or 0.0),
                "best_site_score_0_200": _best_site_score_0_200(support=support, avg_stand_score_0_10=avg_score),
                "strategy": best.get("strategy"),
                "description": best.get("description"),
                "confidence": best.get("confidence"),
                "wind_thermal": best.get("wind_thermal"),
                "wind_overall": best.get("wind_overall"),
                "context_summary": best.get("context_summary"),
                "sources": [str(best.get("source"))],
                "reason": "Fallback to highest scoring stand point (no clusters formed)",
            }

        # Back-compat alias (older UI/notes refer to this as "baseline_stand")
        baseline = best_stand_site

        report = {
            "job_id": job_id,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "inputs": {
                "corners": [{"lat": c[0], "lon": c[1]} for c in corners],
                "mode": mode,
                "num_sample_points": num_sample_points,
                "lidar_grid_points": lidar_grid_points,
                "lidar_top_k": lidar_top_k,
                "lidar_sample_radius_m": lidar_sample_radius_m,
                "epsilon_meters": effective_epsilon,
                "min_samples": min_samples,
                "date_time": date_time,
                "season": season,
                "hunting_pressure": hunting_pressure,
            },
            "lidar_shortlist": lidar_shortlist,
            "lidar_meta": lidar_meta,
            "best_stand_site": best_stand_site,
            "baseline_stand": baseline,
            "clusters": clusters,
            "per_sample_point_best": per_point_best,
            "stand_points_count": len(all_stands),
        }

        report_path = job_dir / "hotspot_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        self.update_job(job_id, message="Building map")
        html = _build_map_html(corners, all_stands, clusters, best_stand_site)
        map_path = job_dir / "hotspot_map.html"
        map_path.write_text(html, encoding="utf-8")

        self.update_job(
            job_id,
            status="completed",
            message="Completed",
            report_path=str(report_path),
            map_path=str(map_path),
        )


_hotspot_job_service: Optional[HotspotJobService] = None


def get_hotspot_job_service() -> HotspotJobService:
    global _hotspot_job_service
    if _hotspot_job_service is None:
        _hotspot_job_service = HotspotJobService()
    return _hotspot_job_service
