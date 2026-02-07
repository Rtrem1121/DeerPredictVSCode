"""Unit tests for the backend.services.hotspot sub-modules."""

from __future__ import annotations

import math
from typing import Any, Dict, List

import pytest

from backend.services.hotspot.polygon import (
    points_center,
    try_make_polygon,
    point_in_polygon,
    sample_points_in_polygon,
    stable_seed_from_corners,
    generate_grid_points_in_polygon,
)
from backend.services.hotspot.clustering import (
    extract_stand_points,
    stand_summary_for_report,
    best_site_score_0_200,
    cluster_stands,
)


# ---------------------------------------------------------------------------
# polygon.py
# ---------------------------------------------------------------------------

class TestPointsCenter:
    def test_empty_returns_default(self):
        lat, lon = points_center([])
        assert lat == 44.0
        assert lon == -72.5

    def test_single_point(self):
        lat, lon = points_center([(43.5, -72.0)])
        assert lat == pytest.approx(43.5)
        assert lon == pytest.approx(-72.0)

    def test_multiple_points(self):
        pts = [(44.0, -73.0), (44.2, -72.0)]
        lat, lon = points_center(pts)
        assert lat == pytest.approx(44.1)
        assert lon == pytest.approx(-72.5)


class TestTryMakePolygon:
    def test_fewer_than_3_returns_none(self):
        assert try_make_polygon([(1, 2), (3, 4)]) is None

    def test_3_corners_returns_polygon(self):
        poly = try_make_polygon([(44.0, -73.0), (44.1, -72.9), (44.0, -72.9)])
        assert poly is not None

    def test_shapely_unavailable_returns_none(self, monkeypatch):
        import builtins
        real_import = builtins.__import__

        def _no_shapely(name, *args, **kwargs):
            if "shapely" in name:
                raise ImportError("no shapely")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _no_shapely)
        assert try_make_polygon([(44.0, -73.0), (44.1, -72.9), (44.0, -72.9)]) is None


class TestPointInPolygon:
    def test_none_polygon_always_true(self):
        assert point_in_polygon(99.0, 99.0, None) is True

    def test_inside(self):
        poly = try_make_polygon([(44.0, -73.0), (44.1, -73.0), (44.1, -72.9), (44.0, -72.9)])
        assert point_in_polygon(44.05, -72.95, poly) is True

    def test_outside(self):
        poly = try_make_polygon([(44.0, -73.0), (44.1, -73.0), (44.1, -72.9), (44.0, -72.9)])
        assert point_in_polygon(45.0, -71.0, poly) is False


class TestSamplePointsInPolygon:
    def test_empty_corners(self):
        assert sample_points_in_polygon([], 5) == []

    def test_returns_requested_count(self):
        corners = [(44.0, -73.0), (44.1, -73.0), (44.1, -72.9), (44.0, -72.9)]
        pts = sample_points_in_polygon(corners, 10, seed=42)
        assert len(pts) == 10

    def test_deterministic_with_seed(self):
        corners = [(44.0, -73.0), (44.1, -73.0), (44.1, -72.9), (44.0, -72.9)]
        a = sample_points_in_polygon(corners, 5, seed=99)
        b = sample_points_in_polygon(corners, 5, seed=99)
        assert a == b

    def test_first_point_is_center(self):
        corners = [(44.0, -73.0), (44.1, -73.0), (44.1, -72.9), (44.0, -72.9)]
        pts = sample_points_in_polygon(corners, 3, seed=1)
        center = points_center(corners)
        assert pts[0] == center


class TestStableSeedFromCorners:
    def test_empty(self):
        assert stable_seed_from_corners([]) == 0

    def test_deterministic(self):
        corners = [(44.0, -73.0), (44.1, -72.9)]
        a = stable_seed_from_corners(corners)
        b = stable_seed_from_corners(corners)
        assert a == b
        assert isinstance(a, int)
        assert a > 0

    def test_different_corners_different_seed(self):
        a = stable_seed_from_corners([(44.0, -73.0), (44.1, -72.9)])
        b = stable_seed_from_corners([(43.0, -72.0), (43.1, -71.9)])
        assert a != b


class TestGenerateGridPoints:
    def test_empty_corners(self):
        assert generate_grid_points_in_polygon([], 100) == []

    def test_returns_points(self):
        corners = [(44.0, -73.0), (44.1, -73.0), (44.1, -72.9), (44.0, -72.9)]
        pts = generate_grid_points_in_polygon(corners, 50)
        assert len(pts) > 0
        assert len(pts) <= 50

    def test_all_points_inside_bbox(self):
        corners = [(44.0, -73.0), (44.1, -73.0), (44.1, -72.9), (44.0, -72.9)]
        pts = generate_grid_points_in_polygon(corners, 100)
        for lat, lon in pts:
            assert 43.99 <= lat <= 44.11
            assert -73.01 <= lon <= -72.89


# ---------------------------------------------------------------------------
# clustering.py
# ---------------------------------------------------------------------------

class TestExtractStandPoints:
    def test_empty_prediction(self):
        assert extract_stand_points({}) == []

    def test_extracts_from_optimized_points(self):
        pred = {
            "optimized_points": {
                "stand_sites": [
                    {"lat": 44.0, "lon": -72.5, "score": 7.5, "strategy": "thermal_hub"},
                ]
            }
        }
        stands = extract_stand_points(pred)
        assert len(stands) == 1
        assert stands[0]["lat"] == 44.0
        assert stands[0]["score"] == 7.5
        assert stands[0]["source"] == "optimized_points.stand_sites"

    def test_extracts_from_mature_buck_analysis(self):
        pred = {
            "mature_buck_analysis": {
                "stand_recommendations": [
                    {"lat": 44.1, "lon": -72.6, "score": 8.0, "type": "ambush"},
                ]
            }
        }
        stands = extract_stand_points(pred)
        assert len(stands) == 1
        assert stands[0]["strategy"] == "ambush"

    def test_skips_entries_without_coordinates(self):
        pred = {
            "optimized_points": {
                "stand_sites": [
                    {"lat": None, "lon": -72.5},
                    {"lat": 44.0, "lon": None},
                    {"lat": 44.0, "lon": -72.5, "score": 5.0},
                ]
            }
        }
        stands = extract_stand_points(pred)
        assert len(stands) == 1

    def test_captures_wind_context(self):
        pred = {
            "wind_thermal_analysis": {"wind_direction": 270, "wind_speed": 8.0},
            "optimized_points": {
                "stand_sites": [
                    {"lat": 44.0, "lon": -72.5, "score": 6.0},
                ]
            },
        }
        stands = extract_stand_points(pred)
        assert stands[0]["wind_thermal"]["wind_direction"] == 270


class TestStandSummaryForReport:
    def test_basic(self):
        stand = {"lat": 44.0, "lon": -72.5, "score": 7.5, "strategy": "bench"}
        summary = stand_summary_for_report(stand)
        assert summary["lat"] == 44.0
        assert summary["score"] == 7.5
        assert "raw" not in summary

    def test_missing_optional_fields(self):
        summary = stand_summary_for_report({"lat": 44.0, "lon": -72.5})
        assert summary["score"] == 0.0
        assert summary["strategy"] is None


class TestBestSiteScore:
    def test_minimum(self):
        s = best_site_score_0_200(support=0, avg_stand_score_0_10=0.0)
        assert s == 15.0

    def test_maximum_capped(self):
        s = best_site_score_0_200(support=100, avg_stand_score_0_10=10.0)
        assert s == 200.0

    def test_typical(self):
        s = best_site_score_0_200(support=5, avg_stand_score_0_10=6.0)
        # 15 + 5*5 + 10*6 = 15 + 25 + 60 = 100
        assert s == pytest.approx(100.0)


class TestClusterStands:
    def test_empty(self):
        assert cluster_stands([], 100, 2) == []

    def test_clusters_nearby_points(self):
        # 4 points very close together, should form 1 cluster
        points = [
            {"lat": 44.0000, "lon": -72.5000, "score": 5.0, "strategy": "a"},
            {"lat": 44.0001, "lon": -72.5001, "score": 6.0, "strategy": "b"},
            {"lat": 44.0001, "lon": -72.4999, "score": 7.0, "strategy": "a"},
            {"lat": 44.0002, "lon": -72.5000, "score": 4.0, "strategy": "c"},
        ]
        clusters = cluster_stands(points, epsilon_m=500, min_samples=2)
        assert len(clusters) >= 1
        c0 = clusters[0]
        assert c0["size"] >= 2
        assert "centroid" in c0
        assert "medoid" in c0

    def test_far_apart_points_no_cluster(self):
        points = [
            {"lat": 44.0, "lon": -72.5, "score": 5.0, "strategy": "a"},
            {"lat": 45.0, "lon": -71.5, "score": 6.0, "strategy": "b"},
        ]
        clusters = cluster_stands(points, epsilon_m=50, min_samples=2)
        assert len(clusters) == 0
