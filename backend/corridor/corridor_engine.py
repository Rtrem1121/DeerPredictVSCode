"""Corridor engine — orchestrates cost surface, pathfinding, and evidence.

The engine works on a regular rectangular grid of terrain metrics.  It
can receive pre-computed numpy arrays *or* build them from a raw DEM.

Typical usage inside the max-accuracy pipeline::

    engine = CorridorEngine(CorridorConfig(cell_m=10))
    result = engine.run_from_metrics(
        slope_deg=slope_grid,
        corridor_score=corridor_grid,
        ridgeline_score=ridge_grid,
        drainage_score=drain_grid,
        origin_lat=min_lat,
        origin_lon=min_lon,
        nodes=bedding_and_evidence_latlons,
        season="rut",
    )
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.corridor.cost_surface import compute_movement_cost
from backend.corridor.pathfinder import accumulate_corridors, dijkstra_path

logger = logging.getLogger(__name__)

# ── Approximate metres-per-degree at Vermont latitude (~44 °N) ──
_M_PER_DEG_LAT = 111_132.0
_M_PER_DEG_LON_44N = 111_320.0 * math.cos(math.radians(44.0))  # ≈ 80 070


@dataclass
class CorridorConfig:
    """Tuning knobs for corridor generation."""

    cell_m: float = 10.0
    max_node_pairs: int = 50

    # Evidence reinforcement
    evidence_radius_m: float = 75.0
    evidence_cost_reduction: float = 0.30  # up to 30 % cost reduction at evidence sites

    # Corridor extraction thresholds (from config/defaults.yaml)
    corridor_threshold: float = 0.15  # minimum density to call "corridor"
    min_corridor_strength: float = 0.35


@dataclass
class CorridorResult:
    """Output bundle from a corridor analysis run."""

    cost_surface: np.ndarray  # 2-D cost grid
    corridor_density: np.ndarray  # 0-1 normalised corridor probability
    paths: List[Dict[str, Any]]  # per-path metadata (from/to/cost/cells)
    nodes: List[Dict[str, Any]]  # nodes used (lat, lon, kind, weight)
    season: str
    cell_m: float
    origin_lat: float
    origin_lon: float
    m_per_deg_lat: float
    m_per_deg_lon: float

    # ── Coordinate helpers ──────────────────────────────────────────
    def grid_to_latlon(self, row: int, col: int) -> Tuple[float, float]:
        lat = self.origin_lat + row * self.cell_m / self.m_per_deg_lat
        lon = self.origin_lon + col * self.cell_m / self.m_per_deg_lon
        return lat, lon

    def latlon_to_grid(self, lat: float, lon: float) -> Tuple[int, int]:
        row = int(round((lat - self.origin_lat) * self.m_per_deg_lat / self.cell_m))
        col = int(round((lon - self.origin_lon) * self.m_per_deg_lon / self.cell_m))
        rows, cols = self.corridor_density.shape
        return max(0, min(row, rows - 1)), max(0, min(col, cols - 1))

    # ── Polylines for map display ───────────────────────────────────
    def get_corridor_polylines(self, min_density: float = 0.15) -> List[List[Tuple[float, float]]]:
        """Extract corridor paths as lat/lon polylines for Folium display."""
        polylines: List[List[Tuple[float, float]]] = []
        for p in self.paths:
            cells = p.get("cells", [])
            if not cells:
                continue
            # Check average density along path
            densities = [float(self.corridor_density[r, c]) for r, c in cells
                         if 0 <= r < self.corridor_density.shape[0]
                         and 0 <= c < self.corridor_density.shape[1]]
            if not densities:
                continue
            avg_density = sum(densities) / len(densities)
            if avg_density < min_density:
                continue
            # Subsample long paths for efficient map rendering
            step = max(1, len(cells) // 100)
            sampled = cells[::step]
            if cells[-1] not in sampled:
                sampled.append(cells[-1])
            polylines.append([self.grid_to_latlon(r, c) for r, c in sampled])
        return polylines

    # ── Serialisable summary for API response ───────────────────────
    def to_dict(self) -> Dict[str, Any]:
        corridor_cells = int(np.sum(self.corridor_density >= 0.15))
        total_cells = max(1, self.corridor_density.size)
        polylines = self.get_corridor_polylines()
        return {
            "season": self.season,
            "cell_m": self.cell_m,
            "grid_shape": list(self.corridor_density.shape),
            "corridor_coverage_pct": round(corridor_cells / total_cells * 100, 1),
            "num_paths": len(self.paths),
            "num_nodes": len(self.nodes),
            "nodes": self.nodes,
            "polylines": [
                [[round(lat, 6), round(lon, 6)] for lat, lon in pl]
                for pl in polylines
            ],
            "paths_summary": [
                {
                    "from_idx": p["from_idx"],
                    "to_idx": p["to_idx"],
                    "cost": p["cost"],
                    "length_cells": p["length_cells"],
                }
                for p in self.paths
            ],
        }


class CorridorEngine:
    """Builds movement corridors from terrain grids and evidence clusters."""

    def __init__(self, config: CorridorConfig | None = None) -> None:
        self.config = config or CorridorConfig()

    def run_from_metrics(
        self,
        slope_deg: np.ndarray,
        corridor_score: np.ndarray,
        ridgeline_score: np.ndarray,
        drainage_score: np.ndarray,
        *,
        origin_lat: float,
        origin_lon: float,
        nodes: List[Dict[str, Any]],
        season: str = "rut",
        canopy_pct: Optional[np.ndarray] = None,
        m_per_deg_lat: float = _M_PER_DEG_LAT,
        m_per_deg_lon: float = _M_PER_DEG_LON_44N,
    ) -> CorridorResult:
        """Run corridor analysis on pre-computed metric grids.

        Parameters
        ----------
        slope_deg, corridor_score, ridgeline_score, drainage_score :
            Same-shape 2-D numpy arrays from terrain analysis.
        origin_lat, origin_lon :
            Geographic coordinates of grid cell ``[0, 0]`` (SW corner).
        nodes :
            Each dict needs ``lat``, ``lon``, and optionally ``kind``
            (``"bedding"`` | ``"evidence"`` | ``"food"``), ``weight`` (float),
            and ``name`` (str).
        season :
            Season key for cost profile selection.
        canopy_pct :
            Optional canopy cover grid 0-100 from GEE.
        """
        cell_m = self.config.cell_m
        rows, cols = slope_deg.shape
        logger.info(
            "CorridorEngine: grid=%dx%d cell_m=%.1f nodes=%d season=%s",
            rows, cols, cell_m, len(nodes), season,
        )

        # ── 1. Cost surface ──
        cost = compute_movement_cost(
            slope_deg, corridor_score, ridgeline_score, drainage_score,
            canopy_pct=canopy_pct, season=season,
        )

        # ── 2. Evidence reinforcement ──
        # Reduce cost around evidence clusters (field-confirmed activity)
        cost = self._apply_evidence_reinforcement(
            cost, nodes, origin_lat, origin_lon, m_per_deg_lat, m_per_deg_lon,
        )

        # ── 3. Convert nodes to grid indices ──
        grid_nodes: List[Tuple[int, int]] = []
        node_weights: List[float] = []
        enriched_nodes: List[Dict[str, Any]] = []
        for n in nodes:
            lat, lon = n["lat"], n["lon"]
            r = int(round((lat - origin_lat) * m_per_deg_lat / cell_m))
            c = int(round((lon - origin_lon) * m_per_deg_lon / cell_m))
            if 0 <= r < rows and 0 <= c < cols and not np.isinf(cost[r, c]):
                grid_nodes.append((r, c))
                node_weights.append(float(n.get("weight", 1.0)))
                enriched_nodes.append({
                    "lat": round(lat, 6),
                    "lon": round(lon, 6),
                    "kind": n.get("kind", "unknown"),
                    "name": n.get("name", ""),
                    "weight": round(float(n.get("weight", 1.0)), 3),
                    "grid_rc": [r, c],
                })

        logger.info("CorridorEngine: %d/%d nodes mapped to grid", len(grid_nodes), len(nodes))

        # ── 4. Accumulate corridors ──
        density, path_records = accumulate_corridors(
            cost, grid_nodes,
            cell_m=cell_m,
            max_pairs=self.config.max_node_pairs,
            weights=node_weights,
        )
        logger.info(
            "CorridorEngine: %d paths found, corridor_coverage=%.1f%%",
            len(path_records),
            float(np.sum(density >= 0.15)) / max(1, density.size) * 100,
        )

        return CorridorResult(
            cost_surface=cost,
            corridor_density=density,
            paths=path_records,
            nodes=enriched_nodes,
            season=season,
            cell_m=cell_m,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            m_per_deg_lat=m_per_deg_lat,
            m_per_deg_lon=m_per_deg_lon,
        )

    # ── Evidence reinforcement ──────────────────────────────────────
    def _apply_evidence_reinforcement(
        self,
        cost: np.ndarray,
        nodes: List[Dict[str, Any]],
        origin_lat: float,
        origin_lon: float,
        m_per_deg_lat: float,
        m_per_deg_lon: float,
    ) -> np.ndarray:
        """Reduce cost near evidence-backed nodes with Gaussian falloff."""
        radius_m = self.config.evidence_radius_m
        max_reduction = self.config.evidence_cost_reduction
        cell_m = self.config.cell_m
        rows, cols = cost.shape
        radius_cells = int(math.ceil(radius_m / cell_m))

        evidence_nodes = [n for n in nodes if n.get("kind") == "evidence"]
        if not evidence_nodes:
            return cost

        cost = cost.copy()  # don't mutate caller's array
        sigma = radius_m / 2.0  # hoisted — same for every node
        two_sigma_sq = 2.0 * sigma * sigma

        for n in evidence_nodes:
            lat, lon = n["lat"], n["lon"]
            cr = int(round((lat - origin_lat) * m_per_deg_lat / cell_m))
            cc = int(round((lon - origin_lon) * m_per_deg_lon / cell_m))
            w = float(n.get("weight", 1.0))
            clamped_w = min(w, 1.0)

            r_lo = max(0, cr - radius_cells)
            r_hi = min(rows, cr + radius_cells + 1)
            c_lo = max(0, cc - radius_cells)
            c_hi = min(cols, cc + radius_cells + 1)

            # Vectorized Gaussian reduction over the bounding box slice
            rr, cc_grid = np.ogrid[r_lo:r_hi, c_lo:c_hi]
            dist_sq_cells = (rr - cr) ** 2 + (cc_grid - cc) ** 2
            dist_sq_m = dist_sq_cells * (cell_m * cell_m)
            within = dist_sq_m <= (radius_m * radius_m)
            falloff = np.exp(-dist_sq_m / two_sigma_sq)
            reduction = max_reduction * falloff * clamped_w  # shape (r_hi-r_lo, c_hi-c_lo)

            slice_ = cost[r_lo:r_hi, c_lo:c_hi]
            finite_mask = within & ~np.isinf(slice_)
            slice_[finite_mask] *= (1.0 - reduction[finite_mask])

        # Floor at 1.0; nan_to_num guards against any inf*0 that slipped through
        cost = np.maximum(np.nan_to_num(cost, nan=1.0, posinf=np.inf), 1.0)
        return cost
