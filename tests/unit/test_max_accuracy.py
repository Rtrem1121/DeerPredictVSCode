"""Tests for backend.max_accuracy module — config, grid, terrain, behavior, pipeline."""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from backend.max_accuracy.config import MaxAccuracyConfig
from backend.max_accuracy.grid import generate_dense_grid
from backend.max_accuracy.terrain_metrics import compute_metrics, score_bench_saddle
from backend.max_accuracy.behavior import score_behavior


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class TestMaxAccuracyConfig:
    def test_defaults(self):
        cfg = MaxAccuracyConfig()
        assert cfg.grid_spacing_m == 20
        assert cfg.max_candidates == 5000
        assert cfg.top_k_stands == 30
        assert cfg.enable_gee is True
        assert cfg.enable_wind is True
        assert 0.95 < sum(cfg.weights.values()) < 1.05  # weights should sum to ~1

    def test_override(self):
        cfg = MaxAccuracyConfig(grid_spacing_m=50, enable_gee=False)
        assert cfg.grid_spacing_m == 50
        assert cfg.enable_gee is False

    def test_bedding_thresholds(self):
        cfg = MaxAccuracyConfig()
        assert cfg.bedding_slope_min < cfg.bedding_slope_max
        assert 0.0 < cfg.bedding_proximity_weight < 1.0


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

class TestGrid:
    def test_empty_corners(self):
        assert generate_dense_grid([], 20) == []

    def test_basic_grid(self):
        # Small square ~200m x 200m
        corners = [
            (44.0, -73.0),
            (44.0, -72.998),
            (44.002, -72.998),
            (44.002, -73.0),
        ]
        points = generate_dense_grid(corners, 20)
        assert len(points) > 0
        for lat, lon in points:
            assert 43.999 <= lat <= 44.003
            assert -73.001 <= lon <= -72.997

    def test_spacing_affects_density(self):
        corners = [
            (44.0, -73.0),
            (44.0, -72.998),
            (44.002, -72.998),
            (44.002, -73.0),
        ]
        dense = generate_dense_grid(corners, 10)
        sparse = generate_dense_grid(corners, 50)
        assert len(dense) > len(sparse)

    def test_progress_callback_called(self):
        corners = [
            (44.0, -73.0),
            (44.0, -72.998),
            (44.002, -72.998),
            (44.002, -73.0),
        ]
        calls = []
        generate_dense_grid(corners, 5, progress_callback=lambda r, t, p: calls.append((r, t, p)))
        # Callback is called every 25 rows — with 5m spacing in ~222m grid, that's ~44 rows
        # so at least 1 callback expected
        assert len(calls) >= 1


# ---------------------------------------------------------------------------
# Terrain Metrics
# ---------------------------------------------------------------------------

class TestTerrainMetrics:
    def test_flat_surface(self):
        # Flat DEM — slope should be near zero
        elev = np.full((50, 50), 100.0, dtype="float32")
        metrics = compute_metrics(elev, cell_m=1.0, tpi_small_m=10, tpi_large_m=30)
        assert "slope_deg" in metrics
        assert "roughness" in metrics
        assert np.nanmean(metrics["slope_deg"]) < 1.0
        assert np.nanmean(metrics["roughness"]) < 0.1

    def test_tilted_surface(self):
        # 45-degree slope (rise = run)
        elev = np.zeros((50, 50), dtype="float32")
        for i in range(50):
            elev[i, :] = float(i)  # 1m rise per 1m cell
        metrics = compute_metrics(elev, cell_m=1.0, tpi_small_m=10, tpi_large_m=30)
        mean_slope = np.nanmean(metrics["slope_deg"])
        assert 40.0 < mean_slope < 50.0

    def test_returns_all_keys(self):
        elev = np.random.rand(30, 30).astype("float32") * 100
        metrics = compute_metrics(elev, cell_m=0.35, tpi_small_m=60, tpi_large_m=200)
        expected_keys = {"slope_deg", "aspect_deg", "curvature", "tpi_small", "tpi_large", "relief_small", "roughness"}
        assert expected_keys == set(metrics.keys())

    def test_shape_preserved(self):
        elev = np.random.rand(40, 60).astype("float32") * 50
        metrics = compute_metrics(elev, cell_m=1.0, tpi_small_m=10, tpi_large_m=30)
        for key, arr in metrics.items():
            assert arr.shape == (40, 60), f"{key} shape mismatch"


class TestBenchSaddle:
    def test_perfect_bench(self):
        # Low slope (~6°), neutral TPI, some relief
        bench, saddle = score_bench_saddle(6.0, 0.1, 5.0, 0.01)
        assert bench > 0.5

    def test_steep_slope_low_bench(self):
        bench, saddle = score_bench_saddle(30.0, 0.1, 5.0, 0.01)
        assert bench < 0.3

    def test_saddle_needs_relief_and_curvature(self):
        # High relief, neutral TPI, high curvature
        bench, saddle = score_bench_saddle(10.0, 0.1, 15.0, 0.1)
        assert saddle > 0.3

    def test_scores_bounded_0_1(self):
        for slope in [0, 5, 10, 20, 30, 45]:
            for tpi in [-5, 0, 5]:
                for relief in [0, 5, 15]:
                    for curv in [-0.1, 0, 0.1]:
                        b, s = score_bench_saddle(float(slope), float(tpi), float(relief), float(curv))
                        assert 0.0 <= b <= 1.0, f"bench out of range for ({slope}, {tpi}, {relief}, {curv})"
                        assert 0.0 <= s <= 1.0, f"saddle out of range for ({slope}, {tpi}, {relief}, {curv})"


# ---------------------------------------------------------------------------
# Behavior Scoring
# ---------------------------------------------------------------------------

class TestBehaviorScoring:
    def test_rut_season_weights(self):
        candidate = {
            "bench_score": 0.8,
            "saddle_score": 0.9,
            "corridor_score": 0.7,
            "shelter_score": 0.6,
            "gee_canopy": 80.0,
            "gee_ndvi": 0.6,
        }
        score = score_behavior(candidate, season="rut")
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # strong candidate should score well

    def test_early_season_values_canopy_more(self):
        # In early season, canopy/NDVI matter more
        high_canopy = {
            "bench_score": 0.3,
            "saddle_score": 0.3,
            "corridor_score": 0.3,
            "shelter_score": 0.3,
            "gee_canopy": 95.0,
            "gee_ndvi": 0.7,
        }
        low_canopy = {
            "bench_score": 0.3,
            "saddle_score": 0.3,
            "corridor_score": 0.3,
            "shelter_score": 0.3,
            "gee_canopy": 20.0,
            "gee_ndvi": 0.1,
        }
        s_high = score_behavior(high_canopy, season="early")
        s_low = score_behavior(low_canopy, season="early")
        assert s_high > s_low

    def test_missing_keys_default_to_zero(self):
        score = score_behavior({}, season="rut")
        assert score == 0.0

    def test_score_bounded(self):
        for season in ["rut", "pre_rut", "post_rut", "early", "late"]:
            score = score_behavior(
                {"bench_score": 1, "saddle_score": 1, "corridor_score": 1,
                 "shelter_score": 1, "gee_canopy": 100, "gee_ndvi": 1.0},
                season=season,
            )
            assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Pipeline Integration (with mocks)
# ---------------------------------------------------------------------------

class TestPipelineIntegration:
    """Test the MaxAccuracyPipeline with mocked DEM/GEE."""

    def test_run_no_rasterio(self):
        """Pipeline returns error when rasterio is not available."""
        from backend.max_accuracy.pipeline import MaxAccuracyPipeline

        with patch("backend.max_accuracy.pipeline.RASTERIO_AVAILABLE", False):
            pipe = MaxAccuracyPipeline()
            result = pipe.run(
                corners=[(44.0, -73.0), (44.0, -72.99), (44.01, -72.99)],
                date_time="2025-11-01T07:00:00",
                season="rut",
                hunting_pressure="medium",
            )
            assert result["error"] == "rasterio_not_available"

    def test_run_no_dem(self):
        """Pipeline returns error when no DEM files found."""
        from backend.max_accuracy.pipeline import MaxAccuracyPipeline

        with patch("backend.max_accuracy.pipeline.RASTERIO_AVAILABLE", True), \
             patch.object(MaxAccuracyPipeline, "_get_dem_path", return_value=None):
            pipe = MaxAccuracyPipeline()
            result = pipe.run(
                corners=[(44.0, -73.0), (44.0, -72.99), (44.01, -72.99)],
                date_time="2025-11-01T07:00:00",
                season="rut",
                hunting_pressure="medium",
            )
            assert result["error"] == "no_lidar_files"

    def test_gee_defaults_on_disable(self):
        """When GEE is disabled, candidates get neutral defaults (not zero)."""
        from backend.max_accuracy.pipeline import MaxAccuracyPipeline

        pipe = MaxAccuracyPipeline(MaxAccuracyConfig(enable_gee=False))
        candidates = [{"lat": 44.0, "lon": -73.0, "score": 0.5}]
        result = pipe._enrich_with_gee(candidates)
        assert result[0]["gee_canopy"] == 50.0
        assert result[0]["gee_ndvi"] == 0.5

    def test_gee_parallel_enrichment(self):
        """GEE enrichment uses thread pool and applies results correctly."""
        from backend.max_accuracy.pipeline import MaxAccuracyPipeline

        candidates = [
            {"lat": 44.0 + i * 0.001, "lon": -73.0, "score": 0.5}
            for i in range(5)
        ]

        def mock_gee(lat, lon, radius_km=0.25):
            return {"gee_canopy": 75.0, "gee_ndvi": 0.65}

        with patch("backend.max_accuracy.pipeline.get_gee_summary", side_effect=mock_gee):
            pipe = MaxAccuracyPipeline(MaxAccuracyConfig(enable_gee=True, gee_sample_k=5))
            result = pipe._enrich_with_gee(candidates)
            for c in result:
                assert c["gee_canopy"] == 75.0
                assert c["gee_ndvi"] == 0.65

    def test_identify_bedding_zones(self):
        """Bedding identification filters correctly."""
        from backend.max_accuracy.pipeline import MaxAccuracyPipeline

        pipe = MaxAccuracyPipeline()
        candidates = [
            {  # Good bedding: meets all criteria
                "lat": 44.0, "lon": -73.0,
                "shelter_score": 0.7, "slope_deg": 12.0, "bench_score": 0.6,
                "aspect_score": 0.5, "roughness": 3.0,
            },
            {  # Bad: flat field (no roughness, low slope, no bench)
                "lat": 44.001, "lon": -73.001,
                "shelter_score": 0.3, "slope_deg": 2.0, "bench_score": 0.1,
                "aspect_score": 0.2, "roughness": 0.5,
            },
        ]
        bedding = pipe._identify_bedding_zones(candidates)
        assert len(bedding) == 1
        assert bedding[0]["lat"] == 44.0

    def test_wind_rotation_no_bedding(self):
        """With no nearby bedding, all winds are huntable."""
        from backend.max_accuracy.pipeline import MaxAccuracyPipeline

        pipe = MaxAccuracyPipeline()
        stand = {"lat": 44.0, "lon": -73.0}
        result = pipe._calculate_wind_rotation(stand, [])
        assert len(result["huntable_winds"]) == 8
        assert len(result["avoid_winds"]) == 0

    def test_progress_callback(self):
        """Progress callback is called without crashing."""
        from backend.max_accuracy.pipeline import MaxAccuracyPipeline

        events = []

        def cb(stage, payload):
            events.append(stage)

        with patch("backend.max_accuracy.pipeline.RASTERIO_AVAILABLE", False):
            pipe = MaxAccuracyPipeline()
            pipe.run(
                corners=[(44.0, -73.0), (44.0, -72.99), (44.01, -72.99)],
                date_time="2025-11-01T07:00:00",
                season="rut",
                hunting_pressure="medium",
                progress_callback=cb,
            )
        assert "started" in events
        assert "error" in events
