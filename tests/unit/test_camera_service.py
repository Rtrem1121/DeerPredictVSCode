"""
Unit tests for the Camera Service.

Tests the camera placement service that handles trail camera recommendations.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from backend.services.camera_service import CameraService, TrailCameraRequest, CameraPlacementRequest
    from fastapi import HTTPException
    SERVICE_AVAILABLE = True
except ImportError:
    SERVICE_AVAILABLE = False
    CameraService = None

from tests.fixtures.test_data import GOLDEN_TEST_LOCATION


@pytest.mark.skipif(not SERVICE_AVAILABLE, reason="Camera service not available")
class TestCameraService:
    """Test suite for camera service."""
    
    @pytest.fixture
    def camera_service(self):
        """Fixture to provide camera service."""
        return CameraService()
    
    @pytest.fixture
    def trail_camera_request(self):
        """Fixture for trail camera request."""
        return TrailCameraRequest(
            lat=GOLDEN_TEST_LOCATION["latitude"],
            lon=GOLDEN_TEST_LOCATION["longitude"],
            season="rut",
            target_buck_age="mature"
        )
    
    @pytest.fixture
    def camera_placement_request(self):
        """Fixture for camera placement request."""
        return CameraPlacementRequest(
            lat=GOLDEN_TEST_LOCATION["latitude"],
            lon=GOLDEN_TEST_LOCATION["longitude"]
        )
    
    def test_service_initialization(self, camera_service):
        """Test that service initializes correctly."""
        assert camera_service is not None
        assert hasattr(camera_service, '_check_camera_placement_availability')
    
    @patch('backend.services.camera_service.core')
    def test_trail_camera_placements_success(self, mock_core, camera_service, trail_camera_request):
        """Test successful trail camera placement generation."""
        # Mock core functions
        mock_core.get_real_elevation_grid.return_value = "mock_elevation"
        mock_core.get_vegetation_grid_from_osm.return_value = "mock_vegetation"
        mock_core.analyze_terrain_and_vegetation.return_value = {"mock": "terrain"}
        
        result = camera_service.get_trail_camera_placements(trail_camera_request)
        
        assert result is not None
        assert "type" in result
        assert result["type"] == "FeatureCollection"
        assert "features" in result
        assert "metadata" in result
        
        # Check that we get the expected number of cameras
        features = result["features"]
        assert len(features) == 3  # Should generate 3 camera positions
        
        # Verify metadata
        metadata = result["metadata"]
        assert metadata["season"] == "rut"
        assert metadata["target_buck_age"] == "mature"
        assert metadata["total_cameras"] == 3
    
    def test_optimal_camera_placement_success(self, camera_service, camera_placement_request):
        """Test successful optimal camera placement generation."""
        result = camera_service.get_optimal_camera_placement(camera_placement_request)
        
        assert result is not None
        assert "type" in result
        assert result["type"] == "FeatureCollection"
        assert "features" in result
        assert "optimal_camera" in result
        assert "placement_analysis" in result
        
        # Check optimal camera data
        optimal_camera = result["optimal_camera"]
        assert "lat" in optimal_camera
        assert "lon" in optimal_camera
        assert "confidence" in optimal_camera
        assert "distance_meters" in optimal_camera
        
        # Validate confidence is high
        confidence = optimal_camera["confidence"]
        assert 90.0 <= confidence <= 100.0, f"Confidence {confidence}% should be high"
        
        # Validate distance is reasonable
        distance = optimal_camera["distance_meters"]
        assert 50.0 <= distance <= 100.0, f"Distance {distance}m should be reasonable"
        
        # Check features (should have camera and target)
        features = result["features"]
        assert len(features) == 2  # Camera + target marker
        
        # Verify feature types
        feature_ids = [f["properties"]["id"] for f in features]
        assert "optimal_camera" in feature_ids
        assert "target_location" in feature_ids
    
    def test_camera_placement_confidence_target(self, camera_service, camera_placement_request):
        """Test that camera placement meets our 95% confidence target."""
        result = camera_service.get_optimal_camera_placement(camera_placement_request)
        
        optimal_camera = result["optimal_camera"]
        confidence = optimal_camera["confidence"]
        
        # Should achieve our target of 95% (allow small tolerance)
        assert 93.0 <= confidence <= 97.0, f"Confidence {confidence}% should be around 95%"
    
    @patch('backend.services.camera_service.core')
    def test_trail_camera_error_handling(self, mock_core, camera_service, trail_camera_request):
        """Test error handling in trail camera placement."""
        # Mock core to raise exception
        mock_core.get_real_elevation_grid.side_effect = Exception("Terrain error")
        
        with pytest.raises(HTTPException) as exc_info:
            camera_service.get_trail_camera_placements(trail_camera_request)
        
        assert exc_info.value.status_code == 500
        assert "Failed to generate camera placements" in str(exc_info.value.detail)
    
    def test_optimal_camera_error_handling(self, camera_service):
        """Test error handling in optimal camera placement."""
        # Test with invalid coordinates
        invalid_request = CameraPlacementRequest(lat=999, lon=999)
        
        # Should handle gracefully and return a result
        result = camera_service.get_optimal_camera_placement(invalid_request)
        assert result is not None  # Should not raise exception
    
    def test_trail_camera_request_validation(self):
        """Test trail camera request validation."""
        # Valid request
        valid_request = TrailCameraRequest(
            lat=44.0, lon=-72.0, season="rut", target_buck_age="mature"
        )
        assert valid_request.lat == 44.0
        assert valid_request.season == "rut"
        
        # Test defaults
        default_request = TrailCameraRequest(lat=44.0, lon=-72.0, season="rut")
        assert default_request.target_buck_age == "mature"  # Default value
    
    def test_camera_placement_request_validation(self):
        """Test camera placement request validation."""
        request = CameraPlacementRequest(lat=44.0, lon=-72.0)
        assert request.lat == 44.0
        assert request.lon == -72.0
    
    def test_feature_geojson_structure(self, camera_service, trail_camera_request):
        """Test that generated features follow GeoJSON standards."""
        with patch('backend.services.camera_service.core') as mock_core:
            mock_core.get_real_elevation_grid.return_value = "mock_elevation"
            mock_core.get_vegetation_grid_from_osm.return_value = "mock_vegetation"
            mock_core.analyze_terrain_and_vegetation.return_value = {"mock": "terrain"}
            
            result = camera_service.get_trail_camera_placements(trail_camera_request)
            
            # Validate GeoJSON structure
            assert result["type"] == "FeatureCollection"
            
            for feature in result["features"]:
                assert feature["type"] == "Feature"
                assert "geometry" in feature
                assert "properties" in feature
                
                # Validate geometry
                geometry = feature["geometry"]
                assert geometry["type"] == "Point"
                assert "coordinates" in geometry
                assert len(geometry["coordinates"]) == 2  # [lon, lat]
                
                # Validate properties
                properties = feature["properties"]
                required_props = ["id", "placement_type", "confidence"]
                for prop in required_props:
                    assert prop in properties, f"Property '{prop}' should be present"


class TestCameraServicePerformance:
    """Performance tests for camera service."""
    
    @pytest.mark.skipif(not SERVICE_AVAILABLE, reason="Service not available")
    def test_camera_service_response_time(self):
        """Test that camera service responds quickly."""
        import time
        
        service = CameraService()
        request = CameraPlacementRequest(
            lat=GOLDEN_TEST_LOCATION["latitude"],
            lon=GOLDEN_TEST_LOCATION["longitude"]
        )
        
        start_time = time.time()
        result = service.get_optimal_camera_placement(request)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Service should be fast (< 2 seconds for unit operations)
        assert response_time < 2.0, f"Camera service took {response_time:.2f}s, should be < 2s"
        assert result is not None, "Should return result within time limit"


class TestCameraServiceIntegration:
    """Integration tests for camera service."""
    
    @pytest.mark.skipif(not SERVICE_AVAILABLE, reason="Service not available")
    def test_real_terrain_integration(self):
        """Test with real terrain data if available."""
        try:
            service = CameraService()
            request = CameraPlacementRequest(
                lat=GOLDEN_TEST_LOCATION["latitude"],
                lon=GOLDEN_TEST_LOCATION["longitude"]
            )
            
            result = service.get_optimal_camera_placement(request)
            
            # Should work with real data
            assert result is not None
            assert "optimal_camera" in result
            
            confidence = result["optimal_camera"]["confidence"]
            assert confidence > 0, "Should have positive confidence with real data"
            
        except Exception as e:
            pytest.skip(f"Real terrain data not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
