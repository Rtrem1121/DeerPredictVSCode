"""Tests for Milestones 2-5: Corridor Engine, Stand Reasoning, Validation.

All tests use synthetic terrain — no LiDAR files required.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

# ── Shared synthetic terrain fixture ────────────────────────────────────

@pytest.fixture
def synthetic_terrain():
    """50×80 grid with a valley, two ridges, and a saddle gap in the middle."""
    rows, cols = 50, 80
    y, x = np.meshgrid(np.linspace(0, 1, rows), np.linspace(0, 1, cols), indexing="ij")
    # Two ridges with a saddle dip at x=0.5
    ridge = np.sin(y * np.pi) * 0.8
    elev = ridge * (1.0 - 0.6 * np.exp(-((x - 0.5) ** 2) / 0.01))

    gy, gx = np.gradient(elev, 10.0, 10.0)
    slope_deg = np.degrees(np.arctan(np.sqrt(gx ** 2 + gy ** 2)))
    # corridor_score highest at saddle
    corridor_score = np.clip(0.6 * np.exp(-((x - 0.5) ** 2) / 0.02), 0, 1)
    ridgeline_score = np.clip(ridge - 0.5, 0, 1) * (1 - corridor_score)
    drainage_score = np.clip(-ridge + 0.3, 0, 1) * 0.5

    return {
        "slope_deg": slope_deg,
        "corridor_score": corridor_score,
        "ridgeline_score": ridgeline_score,
        "drainage_score": drainage_score,
        "rows": rows,
        "cols": cols,
    }


# ═══════════════════════════════════════════════════════════════════════
# M2.1: Cost Surface
# ═══════════════════════════════════════════════════════════════════════

from backend.corridor.cost_surface import compute_movement_cost, SEASON_PROFILES


class TestCostSurface:
    def test_flat_terrain_cost_is_one(self):
        flat = np.zeros((10, 10))
        cost = compute_movement_cost(flat, flat, flat, flat, season="rut")
        assert cost.shape == (10, 10)
        np.testing.assert_allclose(cost, 1.0)

    def test_steep_terrain_high_cost(self):
        steep = np.full((10, 10), 30.0)
        zeros = np.zeros((10, 10))
        cost = compute_movement_cost(steep, zeros, zeros, zeros, season="rut")
        assert cost[0, 0] > 5.0  # 30° at rut sensitivity=0.60 → ~6.06

    def test_impassable_above_45_degrees(self):
        cliff = np.full((10, 10), 50.0)
        zeros = np.zeros((10, 10))
        cost = compute_movement_cost(cliff, zeros, zeros, zeros, season="rut")
        assert np.all(np.isinf(cost))

    def test_corridor_reduces_cost(self):
        slope = np.full((10, 10), 15.0)
        corridor = np.ones((10, 10))
        zeros = np.zeros((10, 10))
        cost_with = compute_movement_cost(slope, corridor, zeros, zeros, season="rut")
        cost_without = compute_movement_cost(slope, zeros, zeros, zeros, season="rut")
        assert cost_with[5, 5] < cost_without[5, 5]

    def test_seasonal_variation(self):
        slope = np.full((10, 10), 20.0)
        zeros = np.zeros((10, 10))
        cost_rut = compute_movement_cost(slope, zeros, zeros, zeros, season="rut")
        cost_late = compute_movement_cost(slope, zeros, zeros, zeros, season="late_season")
        # Late season = higher slope sensitivity → higher cost
        assert cost_late[5, 5] > cost_rut[5, 5]

    def test_all_season_profiles_exist(self):
        expected = {"early_season", "pre_rut", "seeking", "rut", "peak_rut", "post_rut", "late_season"}
        assert expected.issubset(set(SEASON_PROFILES.keys()))

    def test_canopy_influence(self):
        slope = np.full((10, 10), 10.0)
        zeros = np.zeros((10, 10))
        optimal_canopy = np.full((10, 10), 65.0)
        poor_canopy = np.full((10, 10), 10.0)
        cost_optimal = compute_movement_cost(slope, zeros, zeros, zeros, canopy_pct=optimal_canopy, season="early_season")
        cost_poor = compute_movement_cost(slope, zeros, zeros, zeros, canopy_pct=poor_canopy, season="early_season")
        assert cost_optimal[5, 5] < cost_poor[5, 5]


# ═══════════════════════════════════════════════════════════════════════
# M2.2: Dijkstra Pathfinder
# ═══════════════════════════════════════════════════════════════════════

from backend.corridor.pathfinder import dijkstra_path, dijkstra_cost_field, accumulate_corridors


class TestDijkstraPath:
    def test_straight_line_on_uniform_grid(self):
        cost = np.ones((10, 10))
        total, path = dijkstra_path(cost, (0, 0), (0, 9), cell_m=1.0)
        assert len(path) > 0
        assert path[0] == (0, 0)
        assert path[-1] == (0, 9)
        assert total == pytest.approx(9.0, abs=0.5)

    def test_avoids_impassable(self):
        cost = np.ones((10, 10))
        cost[0, 5] = np.inf  # wall at col 5
        total, path = dijkstra_path(cost, (0, 0), (0, 9), cell_m=1.0)
        assert len(path) > 0
        # Path must go around the wall
        assert (0, 5) not in path

    def test_no_path_returns_inf(self):
        cost = np.ones((10, 10))
        cost[5, :] = np.inf  # wall across row 5
        total, path = dijkstra_path(cost, (0, 0), (9, 9), cell_m=1.0)
        assert total == float("inf")
        assert path == []

    def test_out_of_bounds(self):
        cost = np.ones((10, 10))
        total, path = dijkstra_path(cost, (-1, 0), (9, 9))
        assert total == float("inf")

    def test_prefers_low_cost_route(self):
        cost = np.full((10, 10), 10.0)
        cost[5, :] = 1.0  # cheap highway along row 5
        total, path = dijkstra_path(cost, (5, 0), (5, 9), cell_m=1.0)
        # All path cells should be on the cheap row
        assert all(r == 5 for r, c in path)


class TestDijkstraCostField:
    def test_source_has_zero_cost(self):
        cost = np.ones((10, 10))
        field = dijkstra_cost_field(cost, (5, 5), cell_m=1.0)
        assert field[5, 5] == 0.0

    def test_cost_increases_with_distance(self):
        cost = np.ones((20, 20))
        field = dijkstra_cost_field(cost, (10, 10), cell_m=1.0)
        assert field[10, 15] < field[10, 19]


# ═══════════════════════════════════════════════════════════════════════
# M2.3: Corridor Accumulation
# ═══════════════════════════════════════════════════════════════════════

class TestCorridorAccumulation:
    def test_two_nodes_one_path(self):
        cost = np.ones((20, 20))
        nodes = [(5, 0), (5, 19)]
        density, paths = accumulate_corridors(cost, nodes, cell_m=1.0)
        assert len(paths) == 1
        assert density.max() > 0
        # Path should pass through the corridor
        assert density[5, 10] > 0

    def test_three_nodes_three_paths(self):
        cost = np.ones((20, 20))
        nodes = [(0, 0), (0, 19), (19, 10)]
        density, paths = accumulate_corridors(cost, nodes, cell_m=1.0)
        assert len(paths) == 3

    def test_weighted_nodes(self):
        cost = np.ones((20, 20))
        nodes = [(5, 0), (5, 19)]
        _, paths1 = accumulate_corridors(cost, nodes, cell_m=1.0, weights=[1.0, 1.0])
        _, paths2 = accumulate_corridors(cost, nodes, cell_m=1.0, weights=[0.1, 0.1])
        # Both should find paths, but density differs
        assert len(paths1) == 1
        assert len(paths2) == 1

    def test_single_node_no_paths(self):
        cost = np.ones((10, 10))
        density, paths = accumulate_corridors(cost, [(5, 5)], cell_m=1.0)
        assert len(paths) == 0
        assert density.max() == 0


# ═══════════════════════════════════════════════════════════════════════
# M2.4 + M2.5: Corridor Engine (full integration)
# ═══════════════════════════════════════════════════════════════════════

from backend.corridor import CorridorEngine, CorridorConfig, CorridorResult


class TestCorridorEngine:
    def test_basic_run(self, synthetic_terrain):
        nodes = [
            {"lat": 43.310, "lon": -73.220, "kind": "bedding", "weight": 0.8},
            {"lat": 43.310, "lon": -73.213, "kind": "bedding", "weight": 0.8},
        ]
        config = CorridorConfig(cell_m=10.0, max_node_pairs=5)
        engine = CorridorEngine(config)
        result = engine.run_from_metrics(
            synthetic_terrain["slope_deg"],
            synthetic_terrain["corridor_score"],
            synthetic_terrain["ridgeline_score"],
            synthetic_terrain["drainage_score"],
            origin_lat=43.308,
            origin_lon=-73.222,
            nodes=nodes,
            season="rut",
        )
        assert isinstance(result, CorridorResult)
        assert result.corridor_density.shape == (50, 80)
        assert len(result.paths) >= 1

    def test_to_dict_serialisable(self, synthetic_terrain):
        nodes = [
            {"lat": 43.310, "lon": -73.220, "kind": "bedding", "weight": 0.8},
            {"lat": 43.310, "lon": -73.213, "kind": "bedding", "weight": 0.8},
        ]
        engine = CorridorEngine(CorridorConfig(cell_m=10.0))
        result = engine.run_from_metrics(
            synthetic_terrain["slope_deg"],
            synthetic_terrain["corridor_score"],
            synthetic_terrain["ridgeline_score"],
            synthetic_terrain["drainage_score"],
            origin_lat=43.308, origin_lon=-73.222,
            nodes=nodes, season="rut",
        )
        d = result.to_dict()
        assert "polylines" in d
        assert "corridor_coverage_pct" in d
        assert isinstance(d["polylines"], list)
        # Should be JSON-serialisable
        import json
        json.dumps(d)

    def test_evidence_reinforcement_reduces_cost(self, synthetic_terrain):
        evidence_node = {"lat": 43.310, "lon": -73.216, "kind": "evidence", "weight": 1.0}
        bedding_nodes = [
            {"lat": 43.310, "lon": -73.220, "kind": "bedding", "weight": 0.8},
            {"lat": 43.310, "lon": -73.213, "kind": "bedding", "weight": 0.8},
        ]
        config = CorridorConfig(cell_m=10.0, evidence_radius_m=50)
        engine = CorridorEngine(config)

        result_with = engine.run_from_metrics(
            synthetic_terrain["slope_deg"],
            synthetic_terrain["corridor_score"],
            synthetic_terrain["ridgeline_score"],
            synthetic_terrain["drainage_score"],
            origin_lat=43.308, origin_lon=-73.222,
            nodes=bedding_nodes + [evidence_node], season="rut",
        )
        result_without = engine.run_from_metrics(
            synthetic_terrain["slope_deg"],
            synthetic_terrain["corridor_score"],
            synthetic_terrain["ridgeline_score"],
            synthetic_terrain["drainage_score"],
            origin_lat=43.308, origin_lon=-73.222,
            nodes=bedding_nodes, season="rut",
        )
        # Evidence should reduce cost somewhere
        assert result_with.cost_surface.mean() <= result_without.cost_surface.mean()

    def test_seasonal_cost_variation(self, synthetic_terrain):
        nodes = [
            {"lat": 43.310, "lon": -73.220, "kind": "bedding", "weight": 0.8},
            {"lat": 43.310, "lon": -73.213, "kind": "bedding", "weight": 0.8},
        ]
        engine = CorridorEngine(CorridorConfig(cell_m=10.0))
        result_rut = engine.run_from_metrics(
            synthetic_terrain["slope_deg"],
            synthetic_terrain["corridor_score"],
            synthetic_terrain["ridgeline_score"],
            synthetic_terrain["drainage_score"],
            origin_lat=43.308, origin_lon=-73.222,
            nodes=nodes, season="rut",
        )
        result_late = engine.run_from_metrics(
            synthetic_terrain["slope_deg"],
            synthetic_terrain["corridor_score"],
            synthetic_terrain["ridgeline_score"],
            synthetic_terrain["drainage_score"],
            origin_lat=43.308, origin_lon=-73.222,
            nodes=nodes, season="late_season",
        )
        # Late season should have higher mean cost (more conservative movement)
        assert result_late.cost_surface.mean() > result_rut.cost_surface.mean()

    def test_grid_to_latlon_round_trip(self, synthetic_terrain):
        nodes = [
            {"lat": 43.310, "lon": -73.220, "kind": "bedding", "weight": 0.8},
            {"lat": 43.310, "lon": -73.213, "kind": "bedding", "weight": 0.8},
        ]
        engine = CorridorEngine(CorridorConfig(cell_m=10.0))
        result = engine.run_from_metrics(
            synthetic_terrain["slope_deg"],
            synthetic_terrain["corridor_score"],
            synthetic_terrain["ridgeline_score"],
            synthetic_terrain["drainage_score"],
            origin_lat=43.308, origin_lon=-73.222,
            nodes=nodes, season="rut",
        )
        lat, lon = result.grid_to_latlon(25, 40)
        r2, c2 = result.latlon_to_grid(lat, lon)
        assert abs(r2 - 25) <= 1
        assert abs(c2 - 40) <= 1


# ═══════════════════════════════════════════════════════════════════════
# M3: Stand Reasoning
# ═══════════════════════════════════════════════════════════════════════

from backend.corridor.stand_reasoning import (
    generate_stand_narrative,
    enrich_stands_with_corridor_proximity,
)


class TestStandNarrative:
    def test_generates_nonempty_text(self):
        stand = {"bench_score": 0.70, "saddle_score": 0.70, "corridor_score": 0.65}
        text = generate_stand_narrative(stand, rank=1, season="rut")
        assert len(text) > 20
        assert "bench" in text.lower() or "saddle" in text.lower()

    def test_includes_bedding_context(self):
        stand = {
            "bench_score": 0.50,
            "nearest_bedding": {"distance_m": 120, "bearing_deg": 45, "bedding_quality": 0.8},
        }
        text = generate_stand_narrative(stand, rank=2, season="rut")
        assert "120m" in text or "bedding" in text.lower()

    def test_corridor_proximity_mention(self):
        stand = {
            "corridor_proximity_score": 0.8,
            "saddle_score": 0.70,
            "corridor_score": 0.65,
        }
        text = generate_stand_narrative(stand, rank=1, season="rut")
        assert "corridor" in text.lower()

    def test_season_tip(self):
        stand = {"bench_score": 0.50}
        text = generate_stand_narrative(stand, rank=1, season="peak_rut")
        assert "rut" in text.lower() or "all day" in text.lower()


class TestCorridorProximityEnrichment:
    def test_enriches_stands_near_corridors(self):
        stands = [
            {"lat": 43.31, "lon": -73.215},
            {"lat": 43.32, "lon": -73.210},
        ]
        corridor_data = {
            "polylines": [
                [[43.31, -73.215], [43.31, -73.216], [43.31, -73.217]],
            ],
        }
        result = enrich_stands_with_corridor_proximity(stands, corridor_data)
        # First stand is right on the corridor
        assert result[0]["corridor_proximity_score"] > 0.9
        # Second stand is far away
        assert result[1]["corridor_proximity_score"] < 0.5

    def test_no_corridors_returns_none(self):
        stands = [{"lat": 43.31, "lon": -73.215}]
        result = enrich_stands_with_corridor_proximity(stands, None)
        assert result[0]["corridor_proximity_score"] is None


# ═══════════════════════════════════════════════════════════════════════
# M4: Validation / Backtesting
# ═══════════════════════════════════════════════════════════════════════

from backend.corridor.validation import validate_corridors, ValidationResult


class TestValidation:
    def test_events_on_corridor_score_well(self):
        corridor_data = {
            "polylines": [
                [[43.31, -73.215], [43.31, -73.216], [43.31, -73.217]],
            ],
        }
        events = [
            {"lat": 43.31, "lon": -73.2155, "name": "Event right on corridor"},
        ]
        result = validate_corridors(corridor_data, events)
        assert isinstance(result, ValidationResult)
        assert result.hit_rate_50m == 1.0
        assert result.mean_distance_m < 50

    def test_distant_events_score_poorly(self):
        corridor_data = {
            "polylines": [
                [[43.31, -73.215], [43.31, -73.216]],
            ],
        }
        events = [
            {"lat": 43.32, "lon": -73.200, "name": "Far away event"},
        ]
        result = validate_corridors(corridor_data, events)
        assert result.hit_rate_50m == 0.0
        assert result.hit_rate_100m == 0.0
        assert result.mean_distance_m > 500

    def test_mixed_events(self):
        corridor_data = {
            "polylines": [
                [[43.31, -73.215], [43.31, -73.216]],
            ],
        }
        events = [
            {"lat": 43.31, "lon": -73.2155},
            {"lat": 43.32, "lon": -73.200},
        ]
        result = validate_corridors(corridor_data, events)
        assert result.total_events == 2
        assert 0.0 < result.hit_rate_50m < 1.0

    def test_serialisable(self):
        corridor_data = {"polylines": [[[43.31, -73.215]]]}
        events = [{"lat": 43.31, "lon": -73.215}]
        result = validate_corridors(corridor_data, events)
        d = result.to_dict()
        import json
        json.dumps(d)

    def test_empty_corridors(self):
        result = validate_corridors({"polylines": []}, [{"lat": 43.31, "lon": -73.21}])
        assert result.total_events == 0
