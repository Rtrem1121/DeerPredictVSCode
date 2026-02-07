import numpy as np
import pytest
from backend.services.lidar_processor import TerrainExtractor
from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor


@pytest.mark.unit
def test_corridor_features_flat_bench():
    elevation = np.full((9, 9), 100.0, dtype=float)
    features = TerrainExtractor._calculate_corridor_features(elevation, 0.35, 4, 4)
    assert features["bench_score"] >= 0.5
    assert features["corridor_strength"] >= 0.2


@pytest.mark.unit
def test_corridor_features_ridge_like():
    elevation = np.linspace(90, 110, 81, dtype=float).reshape(9, 9)
    features = TerrainExtractor._calculate_corridor_features(elevation, 0.35, 4, 4)
    assert features["ridge_score"] >= 0.0
    assert 0.0 <= features["corridor_strength"] <= 1.0


@pytest.mark.unit
def test_corridor_paths_grouping_and_scores():
    nodes = [
        {"lat": 44.0, "lon": -72.0, "strength": 0.8, "flow_bearing": 90.0},
        {"lat": 44.0005, "lon": -72.0, "strength": 0.7, "flow_bearing": 95.0},
        {"lat": 44.0010, "lon": -72.0, "strength": 0.6, "flow_bearing": 92.0},
        {"lat": 44.01, "lon": -72.01, "strength": 0.9, "flow_bearing": 270.0}
    ]
    paths = EnhancedBeddingZonePredictor._build_corridor_paths(
        nodes,
        max_link_distance_m=120,
        max_bearing_diff_deg=30
    )

    assert len(paths) == 2
    assert any(path["node_count"] == 3 for path in paths)
    multi_path = next(path for path in paths if path["node_count"] == 3)
    assert multi_path["length_m"] > 0
    assert multi_path["flow_score"] >= 0
