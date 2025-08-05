import pytest
import numpy as np
from unittest.mock import Mock, patch
from backend.core import (
    analyze_terrain_and_vegetation,
    run_grid_rule_engine,
    get_time_of_day,
    generate_zones_from_scores
)

class TestTerrainAnalysis:
    def test_analyze_terrain_and_vegetation_basic(self):
        """Test basic terrain and vegetation analysis"""
        # Create simple test grids
        elevation_grid = np.array([[100, 120, 140], [110, 130, 150], [120, 140, 160]])
        vegetation_grid = np.array([[1, 2, 1], [2, 2, 1], [1, 1, 2]])  # 1=field, 2=forest
        
        features = analyze_terrain_and_vegetation(elevation_grid, vegetation_grid)
        
        assert 'slope' in features
        assert 'south_facing_slope' in features
        assert 'forest_edge' in features
        assert 'is_forest' in features
        assert features['slope'].shape == (3, 3)

    def test_forest_edge_detection(self):
        """Test that forest edges are correctly identified"""
        elevation_grid = np.ones((5, 5)) * 100  # Flat elevation
        vegetation_grid = np.array([
            [1, 1, 1, 1, 1],  # field
            [1, 2, 2, 2, 1],  # field, forest, forest, forest, field
            [1, 2, 2, 2, 1],
            [1, 2, 2, 2, 1],
            [1, 1, 1, 1, 1]   # field
        ])
        
        features = analyze_terrain_and_vegetation(elevation_grid, vegetation_grid)
        
        # Check that edges are detected correctly
        assert features['forest_edge'][1, 0] == 1  # Edge cell next to forest
        assert features['forest_edge'][2, 2] == 0  # Deep forest cell should not be edge

class TestRuleEngine:
    def test_run_grid_rule_engine_basic(self):
        """Test basic rule engine functionality"""
        rules = [
            {
                "behavior": "travel",
                "time": "dawn",
                "terrain": "ridge_top",
                "season": "rut",
                "confidence": 0.9,
                "vegetation": "any"
            }
        ]
        
        features = {
            "ridge_top": np.array([[1, 0], [0, 1]]),
            "any": np.ones((2, 2))
        }
        
        conditions = {"time_of_day": "dawn", "season": "rut"}
        
        score_maps = run_grid_rule_engine(rules, features, conditions)
        
        assert "travel" in score_maps
        assert score_maps["travel"][0, 0] == 0.9
        assert score_maps["travel"][0, 1] == 0.0

    def test_rule_engine_time_filtering(self):
        """Test that rules are filtered by time correctly"""
        rules = [
            {
                "behavior": "travel",
                "time": "dawn",
                "terrain": "any",
                "season": "any",
                "confidence": 0.9,
                "vegetation": "any"
            }
        ]
        
        features = {"any": np.ones((2, 2))}
        conditions = {"time_of_day": "dusk", "season": "rut"}  # Different time
        
        score_maps = run_grid_rule_engine(rules, features, conditions)
        
        # Should be zero because time doesn't match
        assert np.all(score_maps["travel"] == 0)

class TestTimeUtils:
    def test_get_time_of_day(self):
        """Test time of day classification"""
        assert get_time_of_day("2023-01-01T07:00:00") == "dawn"
        assert get_time_of_day("2023-01-01T18:00:00") == "dusk"
        assert get_time_of_day("2023-01-01T12:00:00") == "mid-day"
        assert get_time_of_day("2023-01-01T23:00:00") == "night"

class TestZoneGeneration:
    def test_generate_zones_insufficient_points(self):
        """Test zone generation with insufficient high-score points"""
        score_map = np.zeros((5, 5))  # All zeros, no high scores
        
        result = generate_zones_from_scores(score_map, 39.0, -98.0, 5)
        
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 0

    def test_generate_zones_with_high_scores(self):
        """Test zone generation with sufficient high-score points"""
        score_map = np.zeros((5, 5))
        score_map[1:4, 1:4] = 1.0  # High score block
        
        result = generate_zones_from_scores(score_map, 39.0, -98.0, 5, percentile=50)
        
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) > 0

@pytest.fixture
def mock_weather_response():
    """Mock weather API response"""
    return {
        "weather": [{"main": "Clear", "description": "clear sky"}],
        "main": {"temp": 20.5, "humidity": 65},
        "wind": {"speed": 3.2, "deg": 180}
    }

class TestExternalAPIs:
    @patch('requests.get')
    def test_get_weather_data_success(self, mock_get, mock_weather_response):
        """Test successful weather data retrieval"""
        from backend.core import get_weather_data
        
        mock_get.return_value.json.return_value = mock_weather_response
        mock_get.return_value.raise_for_status.return_value = None
        
        result = get_weather_data(39.0, -98.0)
        
        assert result == mock_weather_response
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_weather_data_api_error(self, mock_get):
        """Test weather API error handling"""
        from backend.core import get_weather_data
        
        mock_get.return_value.raise_for_status.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            get_weather_data(39.0, -98.0)
