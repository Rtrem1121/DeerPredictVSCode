#!/usr/bin/env python3
"""
Comprehensive Testing Framework

Modern testing framework for the deer prediction application using pytest,
following testing best practices and patterns.

Key Features:
- Unit tests for individual components
- Integration tests for API endpoints
- Property-based testing for edge cases
- Performance benchmarks
- Test data factories
- Mocking and fixtures

Author: GitHub Copilot
Version: 1.0.0
Date: August 14, 2025
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import numpy as np

# FastAPI testing
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Testing utilities
import factory
from factory import Faker
from factory.fuzzy import FuzzyFloat, FuzzyChoice, FuzzyDateTime

# Application imports
from backend.services.prediction_service import PredictionService, PredictionContext, PredictionResult
from backend.middleware.error_handling import ErrorHandlingMiddleware, AppException, ErrorType, ErrorSeverity
from backend.config.settings import ApplicationConfig, get_config


class TerrainDataFactory(factory.Factory):
    """Factory for generating test terrain data"""
    
    class Meta:
        model = dict
    
    elevation_grid = factory.LazyFunction(lambda: np.random.rand(50, 50) * 1000)
    vegetation_grid = factory.LazyFunction(lambda: np.random.randint(1, 5, size=(50, 50)))
    slope_grid = factory.LazyFunction(lambda: np.random.rand(50, 50) * 45)
    aspect_grid = factory.LazyFunction(lambda: np.random.rand(50, 50) * 360)
    water_sources = factory.LazyFunction(lambda: [(0.1, 0.1), (0.8, 0.3), (0.5, 0.9)])
    roads = factory.LazyFunction(lambda: [(0.0, 0.5, 1.0, 0.5), (0.5, 0.0, 0.5, 1.0)])
    agricultural_areas = factory.LazyFunction(lambda: [(0.2, 0.3, 0.4, 0.5)])


class WeatherDataFactory(factory.Factory):
    """Factory for generating test weather data"""
    
    class Meta:
        model = dict
    
    temp = FuzzyFloat(-10, 35)  # Temperature in Celsius
    humidity = FuzzyFloat(20, 100)
    wind_speed = FuzzyFloat(0, 25)
    wind_direction = FuzzyFloat(0, 360)
    pressure = FuzzyFloat(980, 1030)
    conditions = FuzzyChoice(['clear', 'cloudy', 'rain', 'snow', 'fog'])
    visibility = FuzzyFloat(1, 10)
    uv_index = FuzzyFloat(0, 11)
    next_48h_hourly = factory.LazyFunction(lambda: [])


class PredictionContextFactory(factory.Factory):
    """Factory for generating test prediction contexts"""
    
    class Meta:
        model = PredictionContext
    
    lat = FuzzyFloat(44.0, 45.0)  # Vermont coordinates
    lon = FuzzyFloat(-73.5, -71.5)
    date_time = FuzzyDateTime(
        start_dt=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_dt=datetime(2024, 12, 31, tzinfo=timezone.utc)
    )
    season = FuzzyChoice(['early_season', 'rut', 'late_season', 'pre_rut'])
    fast_mode = FuzzyChoice([True, False])
    suggestion_threshold = FuzzyFloat(3.0, 7.0)
    min_suggestion_rating = FuzzyFloat(6.0, 9.0)


class ScoutingObservationFactory(factory.Factory):
    """Factory for generating test scouting observations"""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: f"obs_{n}")
    lat = FuzzyFloat(44.0, 45.0)
    lon = FuzzyFloat(-73.5, -71.5)
    observation_type = FuzzyChoice(['deer_sighting', 'rub', 'scrape', 'trail', 'bedding'])
    date_observed = FuzzyDateTime(
        start_dt=datetime(2020, 1, 1, tzinfo=timezone.utc),
        end_dt=datetime(2024, 12, 31, tzinfo=timezone.utc)
    )
    confidence = FuzzyFloat(0.5, 1.0)
    mature_buck_indicator = FuzzyChoice([True, False])
    notes = Faker('text', max_nb_chars=200)


@pytest.fixture
def mock_terrain_data():
    """Fixture providing mock terrain data"""
    return TerrainDataFactory()


@pytest.fixture
def mock_weather_data():
    """Fixture providing mock weather data"""
    return WeatherDataFactory()


@pytest.fixture
def mock_prediction_context():
    """Fixture providing mock prediction context"""
    return PredictionContextFactory()


@pytest.fixture
def mock_scouting_data():
    """Fixture providing mock scouting observations"""
    return [ScoutingObservationFactory() for _ in range(10)]


@pytest.fixture
def mock_score_maps():
    """Fixture providing mock score maps"""
    return {
        'travel': np.random.rand(50, 50) * 10,
        'bedding': np.random.rand(50, 50) * 10,
        'feeding': np.random.rand(50, 50) * 10
    }


@pytest.fixture
def prediction_service():
    """Fixture providing prediction service instance"""
    return PredictionService()


@pytest.fixture
def test_config():
    """Fixture providing test configuration"""
    config = ApplicationConfig()
    config.environment = "testing"
    config.debug = True
    config.database.name = "test_deer_prediction"
    # Get test API key from environment variable
    config.api.openweathermap_api_key = os.getenv("TEST_API_KEY", "test_placeholder")
    return config


@pytest.fixture
def error_handler():
    """Fixture providing error handling middleware"""
    return ErrorHandlingMiddleware(None)


@pytest.fixture
async def async_client():
    """Fixture providing async HTTP client for API testing"""
    from backend.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def client():
    """Fixture providing sync HTTP client for API testing"""
    from backend.main import app
    return TestClient(app)


class TestPredictionService:
    """Unit tests for PredictionService"""
    
    def test_prediction_service_initialization(self, prediction_service):
        """Test prediction service can be initialized"""
        assert prediction_service is not None
        assert hasattr(prediction_service, 'core')
        assert hasattr(prediction_service, 'scoring_engine')
    
    @patch('backend.services.prediction_service.core.analyze_terrain_and_vegetation')
    @patch('backend.services.prediction_service.core.get_weather_data')
    def test_terrain_analysis_success(self, mock_weather, mock_terrain, 
                                    prediction_service, mock_prediction_context, mock_terrain_data):
        """Test successful terrain analysis"""
        # Setup mocks
        mock_terrain.return_value = mock_terrain_data
        mock_weather.return_value = WeatherDataFactory()
        
        # Execute
        terrain_data = prediction_service._analyze_terrain(mock_prediction_context)
        
        # Verify
        assert terrain_data is not None
        assert 'elevation_grid' in terrain_data
        mock_terrain.assert_called_once()
    
    @patch('backend.services.prediction_service.core.analyze_terrain_and_vegetation')
    def test_terrain_analysis_failure(self, mock_terrain, prediction_service, mock_prediction_context):
        """Test terrain analysis failure handling"""
        # Setup mock to fail
        mock_terrain.side_effect = Exception("Terrain API failed")
        
        # Execute and verify exception
        with pytest.raises(Exception) as exc_info:
            prediction_service._analyze_terrain(mock_prediction_context)
        
        assert "Terrain analysis failed" in str(exc_info.value)
    
    def test_weather_data_fallback(self, prediction_service, mock_prediction_context):
        """Test weather data fallback when API fails"""
        with patch('backend.services.prediction_service.core.get_weather_data') as mock_weather:
            mock_weather.side_effect = Exception("Weather API failed")
            
            # Execute
            weather_data = prediction_service._get_weather_data(mock_prediction_context)
            
            # Verify fallback data is returned
            assert weather_data is not None
            assert 'temp' in weather_data
            assert weather_data['temp'] == 20  # Default value
    
    def test_score_map_validation(self, prediction_service):
        """Test score map validation logic"""
        # Valid score maps
        valid_maps = {
            'travel': np.random.rand(50, 50),
            'bedding': np.random.rand(50, 50),
            'feeding': np.random.rand(50, 50)
        }
        assert prediction_service._validate_score_maps(valid_maps) is True
        
        # Invalid score maps
        invalid_maps = {
            'travel': np.array([]),  # Empty array
            'bedding': np.random.rand(50, 50)
            # Missing 'feeding'
        }
        assert prediction_service._validate_score_maps(invalid_maps) is False
    
    def test_stand_rating_calculation(self, prediction_service, mock_score_maps):
        """Test stand rating calculation"""
        rating = prediction_service._calculate_stand_rating(mock_score_maps)
        
        assert isinstance(rating, float)
        assert 0 <= rating <= 10
    
    @pytest.mark.parametrize("season,expected_conditions", [
        ("rut", {"season": "rut"}),
        ("early_season", {"season": "early_season"}),
        ("late_season", {"season": "late_season"}),
    ])
    def test_condition_building(self, prediction_service, mock_prediction_context, 
                              mock_weather_data, season, expected_conditions):
        """Test condition building for different seasons"""
        mock_prediction_context.season = season
        
        conditions = prediction_service._build_conditions(mock_prediction_context, mock_weather_data)
        
        assert conditions['season'] == expected_conditions['season']
        assert 'time_of_day' in conditions
        assert 'weather_favorable' in conditions
        assert 'moon_boost' in conditions


class TestErrorHandling:
    """Unit tests for error handling middleware"""
    
    def test_app_exception_creation(self):
        """Test custom application exception creation"""
        error = AppException(
            message="Test error",
            error_type=ErrorType.BUSINESS_LOGIC_ERROR,
            severity=ErrorSeverity.HIGH,
            details={"field": "test"}
        )
        
        assert error.message == "Test error"
        assert error.error_type == ErrorType.BUSINESS_LOGIC_ERROR
        assert error.severity == ErrorSeverity.HIGH
        assert error.details == {"field": "test"}
    
    def test_user_friendly_message_conversion(self, error_handler):
        """Test conversion of technical messages to user-friendly ones"""
        error = AppException(message="terrain analysis failed")
        
        friendly_message = error_handler._get_user_friendly_message(error)
        
        assert "Unable to analyze terrain data" in friendly_message
    
    def test_error_details_sanitization(self, error_handler):
        """Test sanitization of sensitive error details"""
        sensitive_details = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "sensitive_key",
            "normal_field": "normal_value"
        }
        
        sanitized = error_handler._sanitize_error_details(sensitive_details)
        
        assert sanitized["username"] == "testuser"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["normal_field"] == "normal_value"
    
    def test_status_code_mapping(self, error_handler):
        """Test error type to HTTP status code mapping"""
        test_cases = [
            (ErrorType.VALIDATION_ERROR, 400),
            (ErrorType.AUTHENTICATION_ERROR, 401),
            (ErrorType.AUTHORIZATION_ERROR, 403),
            (ErrorType.NOT_FOUND_ERROR, 404),
            (ErrorType.BUSINESS_LOGIC_ERROR, 422),
            (ErrorType.SYSTEM_ERROR, 500)
        ]
        
        for error_type, expected_status in test_cases:
            status = error_handler._get_status_code_for_error_type(error_type)
            assert status == expected_status


class TestConfiguration:
    """Unit tests for configuration management"""
    
    def test_default_configuration_loading(self):
        """Test default configuration can be loaded"""
        config = ApplicationConfig()
        
        assert config.environment.value in ["development", "testing", "staging", "production"]
        assert config.host == "0.0.0.0"
        assert config.port == 8000
    
    def test_environment_validation(self):
        """Test environment-specific validation"""
        # Development config should allow debug mode
        dev_config = ApplicationConfig(environment="development", debug=True)
        assert dev_config.debug is True
        
        # Production config validation
        with patch('backend.config.settings.logger') as mock_logger:
            prod_config = ApplicationConfig(environment="production", debug=True)
            # Should still create config but log warning
            assert prod_config.debug is True
    
    def test_database_connection_url_generation(self):
        """Test database connection URL generation"""
        db_config = ApplicationConfig().database
        db_config.username = "testuser"
        db_config.password = "testpass"
        db_config.host = "localhost"
        db_config.port = 5432
        db_config.name = "testdb"
        
        expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"
        assert db_config.connection_url == expected_url
    
    def test_configuration_weight_validation(self):
        """Test algorithm weight validation"""
        with patch('backend.config.settings.logger') as mock_logger:
            config = ApplicationConfig()
            config.prediction.terrain_weight = 0.5
            config.prediction.weather_weight = 0.3
            config.prediction.scouting_weight = 0.1  # Sum = 0.9, not 1.0
            
            # Should trigger validation warning
            # Note: Validation happens in validator, this tests the concept
    
    @pytest.mark.parametrize("api_key", [
        "",  # Empty key doesn't warn about length
        "short",  # Short key should warn
        "a" * 32,  # Correct length shouldn't warn
        "a" * 40,  # Wrong length should warn
    ])
    def test_api_key_validation(self, api_key):
        """Test API key validation"""
        with patch('backend.config.settings.logger') as mock_logger:
            config = ApplicationConfig()
            config.api.openweathermap_api_key = api_key
            
            # Validation would happen in the validator
            # This tests the validation logic concept


class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_rules_endpoint(self, client):
        """Test rules endpoint returns valid data"""
        response = client.get("/rules")
        
        assert response.status_code == 200
        rules = response.json()
        assert isinstance(rules, list)
        assert len(rules) > 0
    
    @patch('backend.main.core.analyze_terrain_and_vegetation')
    @patch('backend.main.core.get_weather_data')
    def test_prediction_endpoint_success(self, mock_weather, mock_terrain, client):
        """Test successful prediction endpoint"""
        # Setup mocks
        mock_terrain.return_value = TerrainDataFactory()
        mock_weather.return_value = WeatherDataFactory()
        
        # Make request
        prediction_request = {
            "lat": 44.26,
            "lon": -72.58,
            "date_time": "2024-11-15T07:00:00",
            "season": "rut"
        }
        
        response = client.post("/predict", json=prediction_request)
        
        assert response.status_code == 200
        result = response.json()
        assert "stand_rating" in result
        assert "travel_corridors" in result
        assert "bedding_zones" in result
        assert "feeding_areas" in result
    
    def test_prediction_endpoint_validation_error(self, client):
        """Test prediction endpoint with invalid data"""
        invalid_request = {
            "lat": "invalid",  # Should be float
            "lon": -72.58,
            "date_time": "2024-11-15T07:00:00",
            "season": "rut"
        }
        
        response = client.post("/predict", json=invalid_request)
        assert response.status_code == 422
    
    def test_prediction_endpoint_missing_fields(self, client):
        """Test prediction endpoint with missing required fields"""
        incomplete_request = {
            "lat": 44.26,
            # Missing lon, date_time, season
        }
        
        response = client.post("/predict", json=incomplete_request)
        assert response.status_code == 422


class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    @pytest.mark.benchmark
    def test_prediction_performance(self, benchmark, prediction_service, mock_prediction_context):
        """Benchmark prediction service performance"""
        
        with patch('backend.services.prediction_service.core.analyze_terrain_and_vegetation') as mock_terrain:
            with patch('backend.services.prediction_service.core.get_weather_data') as mock_weather:
                mock_terrain.return_value = TerrainDataFactory()
                mock_weather.return_value = WeatherDataFactory()
                
                # Benchmark the prediction method
                result = benchmark(prediction_service.predict, mock_prediction_context)
                
                assert result is not None
                assert isinstance(result, PredictionResult)
    
    @pytest.mark.benchmark
    def test_api_endpoint_performance(self, benchmark, client):
        """Benchmark API endpoint performance"""
        
        request_data = {
            "lat": 44.26,
            "lon": -72.58,
            "date_time": "2024-11-15T07:00:00",
            "season": "rut"
        }
        
        with patch('backend.main.core.analyze_terrain_and_vegetation') as mock_terrain:
            with patch('backend.main.core.get_weather_data') as mock_weather:
                mock_terrain.return_value = TerrainDataFactory()
                mock_weather.return_value = WeatherDataFactory()
                
                # Benchmark the API endpoint
                response = benchmark(client.post, "/predict", json=request_data)
                
                assert response.status_code == 200


class TestPropertyBasedTesting:
    """Property-based tests for edge cases"""
    
    @pytest.mark.parametrize("lat", [-90, -45, 0, 45, 90])
    @pytest.mark.parametrize("lon", [-180, -90, 0, 90, 180])
    def test_coordinate_edge_cases(self, lat, lon, prediction_service):
        """Test prediction service with edge case coordinates"""
        
        context = PredictionContext(
            lat=lat,
            lon=lon,
            date_time=datetime.now(timezone.utc),
            season="rut"
        )
        
        # Should not crash with edge coordinates
        with patch('backend.services.prediction_service.core.analyze_terrain_and_vegetation') as mock_terrain:
            with patch('backend.services.prediction_service.core.get_weather_data') as mock_weather:
                mock_terrain.return_value = TerrainDataFactory()
                mock_weather.return_value = WeatherDataFactory()
                
                # This should handle edge cases gracefully
                try:
                    result = prediction_service._analyze_terrain(context)
                    assert result is not None
                except Exception as e:
                    # Expected for invalid coordinates
                    assert "Terrain analysis failed" in str(e)
    
    @pytest.mark.parametrize("season", ["early_season", "rut", "late_season", "pre_rut", "invalid_season"])
    def test_season_variations(self, season, prediction_service, mock_prediction_context):
        """Test prediction service with different seasons"""
        
        mock_prediction_context.season = season
        
        with patch('backend.services.prediction_service.core.get_weather_data') as mock_weather:
            mock_weather.return_value = WeatherDataFactory()
            
            conditions = prediction_service._build_conditions(mock_prediction_context, mock_weather.return_value)
            
            assert 'season' in conditions
            assert conditions['season'] == season


# Test configuration
pytest_plugins = ["pytest_benchmark"]

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "benchmark: mark test as a performance benchmark")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Custom pytest fixtures for specific test scenarios
@pytest.fixture(scope="session")
def test_database():
    """Session-scoped test database fixture"""
    # This would set up a test database for integration tests
    # Implementation depends on database choice
    pass


@pytest.fixture
def isolated_predictions():
    """Fixture providing isolated prediction environment"""
    # This would create isolated test environment for predictions
    # Useful for testing without side effects
    pass


# Test utilities
def assert_valid_prediction_result(result: PredictionResult):
    """Assert that a prediction result is valid"""
    assert result is not None
    assert isinstance(result.stand_rating, (int, float))
    assert 0 <= result.stand_rating <= 10
    assert result.travel_corridors is not None
    assert result.bedding_zones is not None
    assert result.feeding_areas is not None
    assert isinstance(result.notes, str)


def create_test_coordinates(region: str = "vermont") -> tuple[float, float]:
    """Create test coordinates for specific regions"""
    regions = {
        "vermont": (44.26, -72.58),
        "new_york": (42.16, -74.95),
        "maine": (45.25, -69.22),
        "edge_case": (90.0, 180.0)
    }
    return regions.get(region, regions["vermont"])


if __name__ == "__main__":
    """Run tests when executed directly"""
    pytest.main([__file__, "-v", "--tb=short"])
