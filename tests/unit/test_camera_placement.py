"""
Unit tests for camera placement functionality.

These tests ensure that the camera placement algorithm that currently
achieves 95% confidence is preserved during refactoring.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.fixtures.test_data import (
    GOLDEN_TEST_LOCATION,
    EXPECTED_CAMERA_PLACEMENT,
    TEST_LOCATIONS
)

# Test both the new service architecture and original implementation
try:
    from backend.services.camera_service import CameraService, CameraPlacementRequest
    CAMERA_SERVICE_AVAILABLE = True
except ImportError:
    CAMERA_SERVICE_AVAILABLE = False
    CameraService = None

try:
    from backend.advanced_camera_placement import BuckCameraPlacement
    CAMERA_MODULE_AVAILABLE = True
except ImportError:
    CAMERA_MODULE_AVAILABLE = False
    BuckCameraPlacement = None

class TestCameraPlacement:
    """Test suite for camera placement functionality."""
    
    @pytest.fixture
    def camera_placement_service(self):
        """Fixture to provide camera placement service."""
        if not CAMERA_MODULE_AVAILABLE:
            pytest.skip("Camera placement module not available")
        return BuckCameraPlacement()
    
    @pytest.fixture
    def camera_service(self):
        """Fixture to provide the new camera service."""
        if not CAMERA_SERVICE_AVAILABLE:
            pytest.skip("Camera service not available")
        return CameraService()
    
    def test_camera_service_availability(self):
        """Test that camera service is available."""
        assert CAMERA_SERVICE_AVAILABLE, "Camera service should be available"
        assert CameraService is not None
    
    def test_camera_module_availability(self):
        """Test that camera placement module is available."""
        assert CAMERA_MODULE_AVAILABLE, "Camera placement module should be available"
        assert BuckCameraPlacement is not None
    
    @pytest.mark.skipif(not CAMERA_SERVICE_AVAILABLE, reason="Camera service not available")
    def test_golden_location_camera_confidence_service(self, camera_service):
        """Test that golden location maintains 95% camera confidence through service."""
        request = CameraPlacementRequest(
            lat=GOLDEN_TEST_LOCATION["latitude"],
            lon=GOLDEN_TEST_LOCATION["longitude"]
        )
        
        result = camera_service.get_optimal_camera_placement(request)
        
        # Validate response structure
        assert result is not None, "Camera service should return a result"
        assert "optimal_camera" in result, "Result should contain optimal camera data"
        
        # Get camera confidence from the response
        optimal_camera = result["optimal_camera"]
        confidence = optimal_camera.get("confidence", 0)
        
        # Test for the updated 95% confidence target (allow ±3% tolerance)
        assert 92.0 <= confidence <= 98.0, f"Camera confidence {confidence}% should be around 95%"
        
        # Validate distance is reasonable
        distance = optimal_camera.get("distance_meters", 0)
        assert 50 <= distance <= 100, f"Distance {distance}m should be reasonable for deer monitoring"
    
    @pytest.mark.skipif(not CAMERA_MODULE_AVAILABLE, reason="Camera module not available")
    def test_golden_location_camera_confidence(self, camera_placement_service):
        """Test that golden location maintains high camera confidence."""
        # Updated for 95% confidence target
        latitude = GOLDEN_TEST_LOCATION["latitude"]
        longitude = GOLDEN_TEST_LOCATION["longitude"]
        
        # Get camera placement
        result = camera_placement_service.find_optimal_camera_position(latitude, longitude)
        
        # Validate confidence is maintained (allow ±3% tolerance for 95% target)
        assert result is not None, "Camera placement should return a result"
        
        confidence = result.get("confidence", 0)
        assert 92.0 <= confidence <= 98.0, f"Camera confidence {confidence}% should be around 95%"
        
        # Validate reasoning is present
        reasoning = result.get("reasoning", "")
        assert reasoning, "Camera placement should include reasoning"
        assert "optimal" in reasoning.lower(), "Reasoning should mention optimization"
    
    @pytest.mark.skipif(not CAMERA_MODULE_AVAILABLE, reason="Camera module not available")
    def test_camera_placement_structure(self, camera_placement_service):
        """Test that camera placement returns expected data structure."""
        latitude = GOLDEN_TEST_LOCATION["latitude"]
        longitude = GOLDEN_TEST_LOCATION["longitude"]
        
        result = camera_placement_service.find_optimal_camera_position(latitude, longitude)
        
        # Validate required fields
        required_fields = ["confidence", "reasoning", "coordinates", "distance_meters"]
        for field in required_fields:
            assert field in result, f"Camera placement result should contain '{field}'"
        
        # Validate data types
        assert isinstance(result["confidence"], (int, float)), "Confidence should be numeric"
        assert isinstance(result["reasoning"], str), "Reasoning should be string"
        assert isinstance(result["coordinates"], dict), "Coordinates should be dict"
        assert isinstance(result["distance_meters"], (int, float)), "Distance should be numeric"
        
        # Validate coordinate structure
        coords = result["coordinates"]
        assert "latitude" in coords, "Coordinates should contain latitude"
        assert "longitude" in coords, "Coordinates should contain longitude"
    
    @pytest.mark.skipif(not CAMERA_MODULE_AVAILABLE, reason="Camera module not available")
    def test_camera_distance_calculation(self, camera_placement_service):
        """Test that camera distance calculation is reasonable."""
        latitude = GOLDEN_TEST_LOCATION["latitude"]
        longitude = GOLDEN_TEST_LOCATION["longitude"]
        
        result = camera_placement_service.find_optimal_camera_position(latitude, longitude)
        
        distance = result.get("distance_meters", 0)
        
        # Distance should be reasonable for deer cameras (typically 30-150 meters)
        assert 10 <= distance <= 200, f"Camera distance {distance}m should be reasonable for deer monitoring"
    
    @pytest.mark.skipif(not CAMERA_MODULE_AVAILABLE, reason="Camera module not available")
    def test_multiple_locations(self, camera_placement_service):
        """Test camera placement across multiple locations."""
        for location in TEST_LOCATIONS:
            result = camera_placement_service.find_optimal_camera_position(
                location["latitude"], 
                location["longitude"]
            )
            
            assert result is not None, f"Camera placement should work for {location['name']}"
            assert result.get("confidence", 0) > 0, f"Confidence should be positive for {location['name']}"
            assert result.get("reasoning", ""), f"Reasoning should be provided for {location['name']}"
    
    @pytest.mark.skipif(not CAMERA_MODULE_AVAILABLE, reason="Camera module not available")
    def test_edge_case_coordinates(self, camera_placement_service):
        """Test camera placement with edge case coordinates."""
        edge_cases = [
            # Vermont boundary cases
            (44.0, -72.0),   # Southern Vermont
            (45.0, -73.0),   # Northern Vermont
            (44.5, -71.5),   # Eastern Vermont
            (44.5, -73.5),   # Western Vermont
        ]
        
        for lat, lon in edge_cases:
            result = camera_placement_service.find_optimal_camera_position(lat, lon)
            
            # Should handle edge cases gracefully
            assert result is not None, f"Should handle edge case ({lat}, {lon})"
            
            confidence = result.get("confidence", 0)
            assert confidence >= 0, f"Confidence should be non-negative for ({lat}, {lon})"
    
    def test_invalid_coordinates(self):
        """Test handling of invalid coordinates."""
        if not CAMERA_MODULE_AVAILABLE:
            pytest.skip("Camera module not available")
            
        camera_service = BuckCameraPlacement()
        
        invalid_cases = [
            (None, None),
            (999, 999),      # Out of range
            (-999, -999),    # Out of range
            ("invalid", "invalid"),  # Wrong type
        ]
        
        for lat, lon in invalid_cases:
            try:
                result = camera_service.find_optimal_camera_position(lat, lon)
                # If no exception, result should indicate error or have very low confidence
                if result:
                    confidence = result.get("confidence", 0)
                    assert confidence < 50, f"Invalid coordinates should have low confidence: ({lat}, {lon})"
            except (ValueError, TypeError, Exception):
                # Expected for invalid inputs
                pass

class TestCameraPlacementPerformance:
    """Performance tests for camera placement."""
    
    @pytest.mark.skipif(not CAMERA_MODULE_AVAILABLE, reason="Camera module not available")
    def test_camera_placement_response_time(self):
        """Test that camera placement completes in reasonable time."""
        import time
        
        camera_service = BuckCameraPlacement()
        latitude = GOLDEN_TEST_LOCATION["latitude"]
        longitude = GOLDEN_TEST_LOCATION["longitude"]
        
        start_time = time.time()
        result = camera_service.find_optimal_camera_position(latitude, longitude)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Camera placement should be fast (< 5 seconds for unit operations)
        assert response_time < 5.0, f"Camera placement took {response_time:.2f}s, should be < 5s"
        assert result is not None, "Should return result within time limit"

class TestCameraPlacementRegression:
    """Regression tests to ensure refactoring doesn't break functionality."""
    
    @pytest.mark.skipif(not CAMERA_MODULE_AVAILABLE, reason="Camera module not available")
    def test_preserve_golden_metrics(self):
        """Test that exact golden location metrics are preserved."""
        camera_service = BuckCameraPlacement()
        
        result = camera_service.find_optimal_camera_position(
            GOLDEN_TEST_LOCATION["latitude"],
            GOLDEN_TEST_LOCATION["longitude"]
        )
        
        # These are the exact metrics we must preserve
        confidence = result.get("confidence", 0)
        distance = result.get("distance_meters", 0)
        
        # Allow small tolerance for floating point differences
        expected_confidence = EXPECTED_CAMERA_PLACEMENT["confidence"]
        expected_distance = EXPECTED_CAMERA_PLACEMENT["distance_from_target"]
        
        assert abs(confidence - expected_confidence) <= 2.0, \
            f"Confidence {confidence}% should be close to expected {expected_confidence}%"
        
        assert abs(distance - expected_distance) <= 10.0, \
            f"Distance {distance}m should be close to expected {expected_distance}m"
        
        # Verify reasoning contains key phrases
        reasoning = result.get("reasoning", "").lower()
        expected_phrases = ["optimal", "distance", "coverage"]
        
        for phrase in expected_phrases:
            assert phrase in reasoning, f"Reasoning should contain '{phrase}'"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
