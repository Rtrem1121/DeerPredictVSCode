"""Least-cost path routing and corridor probability accumulation.

Pure numpy + heapq implementation — no scipy or networkx required.
Works on 2-D cost grids produced by :func:`cost_surface.compute_movement_cost`.
"""

from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple

import numpy as np

_SQRT2 = 1.4142135623730951

# 8-connected neighbourhood: (row_offset, col_offset, distance_factor)
_NEIGHBOURS = [
    (-1, 0, 1.0),
    (1, 0, 1.0),
    (0, -1, 1.0),
    (0, 1, 1.0),
    (-1, -1, _SQRT2),
    (-1, 1, _SQRT2),
    (1, -1, _SQRT2),
    (1, 1, _SQRT2),
]


def dijkstra_path(
    cost: np.ndarray,
    start_rc: Tuple[int, int],
    end_rc: Tuple[int, int],
    cell_m: float = 10.0,
) -> Tuple[float, List[Tuple[int, int]]]:
    """Find the least-cost path on *cost* from *start_rc* to *end_rc*.

    Uses Dijkstra with 8-connected neighbours.  Edge cost is the average
    of the two adjacent cells multiplied by real-world distance.

    Returns ``(total_cost, path)`` where *path* is a list of ``(row, col)``
    indices.  Returns ``(inf, [])`` if no path exists.
    """
    rows, cols = cost.shape
    sr, sc = start_rc
    er, ec = end_rc

    if not (0 <= sr < rows and 0 <= sc < cols and 0 <= er < rows and 0 <= ec < cols):
        return float("inf"), []
    if np.isinf(cost[sr, sc]) or np.isinf(cost[er, ec]):
        return float("inf"), []

    dist = np.full((rows, cols), np.inf, dtype=np.float64)
    dist[sr, sc] = 0.0
    parent_r = np.full((rows, cols), -1, dtype=np.int32)
    parent_c = np.full((rows, cols), -1, dtype=np.int32)
    visited = np.zeros((rows, cols), dtype=bool)

    pq: list = [(0.0, sr, sc)]

    while pq:
        d, r, c = heapq.heappop(pq)
        if visited[r, c]:
            continue
        visited[r, c] = True
        if r == er and c == ec:
            break
        for dr, dc, df in _NEIGHBOURS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr, nc]:
                edge = 0.5 * (cost[r, c] + cost[nr, nc]) * df * cell_m
                nd = d + edge
                if nd < dist[nr, nc]:
                    dist[nr, nc] = nd
                    parent_r[nr, nc] = r
                    parent_c[nr, nc] = c
                    heapq.heappush(pq, (nd, nr, nc))

    if np.isinf(dist[er, ec]):
        return float("inf"), []

    # Reconstruct
    path: List[Tuple[int, int]] = []
    r, c = er, ec
    while r != -1:
        path.append((r, c))
        pr, pc = int(parent_r[r, c]), int(parent_c[r, c])
        r, c = pr, pc
    path.reverse()
    return float(dist[er, ec]), path


def dijkstra_cost_field(
    cost: np.ndarray,
    source_rc: Tuple[int, int],
    cell_m: float = 10.0,
) -> np.ndarray:
    """Compute full cost-distance field from a single source cell.

    Returns a 2-D array of cumulative travel cost from *source_rc* to every
    reachable cell.  Unreachable cells stay ``inf``.
    """
    rows, cols = cost.shape
    sr, sc = source_rc

    dist = np.full((rows, cols), np.inf, dtype=np.float64)
    if not (0 <= sr < rows and 0 <= sc < cols) or np.isinf(cost[sr, sc]):
        return dist
    dist[sr, sc] = 0.0
    visited = np.zeros((rows, cols), dtype=bool)
    pq: list = [(0.0, sr, sc)]

    while pq:
        d, r, c = heapq.heappop(pq)
        if visited[r, c]:
            continue
        visited[r, c] = True
        for dr, dc, df in _NEIGHBOURS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr, nc]:
                edge = 0.5 * (cost[r, c] + cost[nr, nc]) * df * cell_m
                nd = d + edge
                if nd < dist[nr, nc]:
                    dist[nr, nc] = nd
                    heapq.heappush(pq, (nd, nr, nc))
    return dist


def accumulate_corridors(
    cost: np.ndarray,
    nodes: List[Tuple[int, int]],
    *,
    cell_m: float = 10.0,
    max_pairs: int = 50,
    weights: Optional[List[float]] = None,
) -> Tuple[np.ndarray, List[Dict]]:
    """Build a corridor probability raster by routing between node pairs.

    For each pair of nodes the least-cost path is found and cells along
    the path are incremented (optionally weighted by the node-pair weight).
    The result is normalised to 0-1.

    Parameters
    ----------
    cost : 2-D cost grid.
    nodes : list of ``(row, col)`` grid indices (bedding zones, evidence
        clusters, food sources …).
    cell_m : grid cell size in metres.
    max_pairs : cap on number of pairs to route (closest first).
    weights : optional per-node importance weight.  When two nodes are
        connected, the path gets ``min(w_i, w_j)`` weight.

    Returns
    -------
    (density, paths) — *density* is a 0-1 normalised grid, *paths* is a
    list of dicts ``{"from_idx", "to_idx", "cost", "cells"}``.
    """
    rows, cols = cost.shape
    density = np.zeros((rows, cols), dtype=np.float64)
    path_records: List[Dict] = []

    if len(nodes) < 2:
        return density, path_records

    if weights is None:
        weights = [1.0] * len(nodes)

    # Build candidate pairs sorted by grid distance
    pairs: List[Tuple[float, int, int]] = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            r1, c1 = nodes[i]
            r2, c2 = nodes[j]
            grid_dist = ((r1 - r2) ** 2 + (c1 - c2) ** 2) ** 0.5
            pairs.append((grid_dist, i, j))
    pairs.sort()
    pairs = pairs[:max_pairs]

    for _, i, j in pairs:
        total_cost, path = dijkstra_path(cost, nodes[i], nodes[j], cell_m)
        if not path:
            continue
        path_weight = min(weights[i], weights[j])
        for r, c in path:
            density[r, c] += path_weight
        path_records.append(
            {
                "from_idx": i,
                "to_idx": j,
                "cost": round(total_cost, 1),
                "length_cells": len(path),
                "cells": path,
            }
        )

    mx = density.max()
    if mx > 0:
        density /= mx
    return density, path_records
