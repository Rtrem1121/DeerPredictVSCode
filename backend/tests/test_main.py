import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json

from backend.main import app

client = TestClient(app)

class TestMainAPI:
    def test_root_endpoint(self):
        """Test the root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Welcome to the Deer Movement Prediction API" in response.json()["message"]

    def test_rules_endpoint(self):
        """Test the rules endpoint returns rules data"""
        response = client.get("/rules")
        assert response.status_code == 200
        rules = response.json()
        assert isinstance(rules, list)
        assert len(rules) > 0
        
        # Check rule structure
        rule = rules[0]
        required_fields = ["behavior", "time", "terrain", "season", "confidence"]
        for field in required_fields:
            assert field in rule

    @patch('backend.core.get_weather_data')
    @patch('backend.core.get_real_elevation_grid')
    @patch('backend.core.get_vegetation_grid_from_osm')
    def test_predict_endpoint_success(self, mock_vegetation, mock_elevation, mock_weather):
        """Test successful prediction endpoint"""
        # Mock external API responses
        mock_weather.return_value = {"temp": 20, "humidity": 60}
        mock_elevation.return_value = [[100, 110, 120], [105, 115, 125], [110, 120, 130]]
        mock_vegetation.return_value = [[1, 2, 1], [2, 2, 1], [1, 1, 2]]
        
        prediction_request = {
            "lat": 39.8283,
            "lon": -98.5795,
            "date_time": "2023-10-15T07:00:00",
            "season": "rut"
        }
        
        response = client.post("/predict", json=prediction_request)
        assert response.status_code == 200
        
        result = response.json()
        assert "stand_rating" in result
        assert "travel_corridors" in result
        assert "bedding_zones" in result
        assert "feeding_areas" in result
        assert 0 <= result["stand_rating"] <= 10

    def test_predict_endpoint_invalid_data(self):
        """Test prediction endpoint with invalid data"""
        invalid_request = {
            "lat": "invalid",  # Should be float
            "lon": -98.5795,
            "date_time": "2023-10-15T07:00:00",
            "season": "rut"
        }
        
        response = client.post("/predict", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_predict_endpoint_missing_fields(self):
        """Test prediction endpoint with missing required fields"""
        incomplete_request = {
            "lat": 39.8283,
            # Missing lon, date_time, season
        }
        
        response = client.post("/predict", json=incomplete_request)
        assert response.status_code == 422  # Validation error

class TestPredictionModels:
    def test_prediction_request_validation(self):
        """Test PredictionRequest model validation"""
        from backend.main import PredictionRequest
        
        # Valid request
        valid_data = {
            "lat": 39.8283,
            "lon": -98.5795,
            "date_time": "2023-10-15T07:00:00",
            "season": "rut"
        }
        request = PredictionRequest(**valid_data)
        assert request.lat == 39.8283
        assert request.season == "rut"

    def test_prediction_response_structure(self):
        """Test PredictionResponse model structure"""
        from backend.main import PredictionResponse
        
        response_data = {
            "travel_corridors": {"type": "FeatureCollection", "features": []},
            "bedding_zones": {"type": "FeatureCollection", "features": []},
            "feeding_areas": {"type": "FeatureCollection", "features": []},
            "stand_rating": 7.5,
            "notes": "Test prediction",
            "terrain_heatmap": "base64string",
            "vegetation_heatmap": "base64string",
            "travel_score_heatmap": "base64string",
            "bedding_score_heatmap": "base64string",
            "feeding_score_heatmap": "base64string"
        }
        
        response = PredictionResponse(**response_data)
        assert response.stand_rating == 7.5
        assert response.notes == "Test prediction"
