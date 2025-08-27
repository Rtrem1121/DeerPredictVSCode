"""
Integration tests for the refactored API architecture.

These tests ensure that the new router-based architecture maintains
all functionality and performance characteristics.
"""

import pytest
import sys
import os
import requests
import time
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.fixtures.test_data import (
    GOLDEN_TEST_LOCATION,
    get_prediction_request_template,
    validate_response_structure,
    PERFORMANCE_BENCHMARKS
)

# Test configuration
API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 30


class TestRefactoredArchitecture:
    """Test suite for the refactored service-based architecture."""
    
    def test_api_health_endpoint(self):
        """Test that the API health endpoint is working."""
        response = requests.get(f"{API_BASE_URL}/health", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data
        assert "architecture" in data
        assert data["architecture"] == "refactored"
        
        # Check service status
        if "services" in data:
            services = data["services"]
            expected_services = ["configuration_service", "camera_service", "scouting_service", "prediction_service"]
            for service in expected_services:
                assert service in services, f"Service {service} should be reported"
    
    def test_api_root_endpoint(self):
        """Test that the API root endpoint shows refactored status."""
        response = requests.get(f"{API_BASE_URL}/", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "refactored" in data.get("message", "").lower() or data.get("refactored", False)
        assert data.get("architecture") == "service-based"
        assert data.get("preserved_functionality") == "100%"
    
    def test_prediction_endpoint_functionality(self):
        """Test that the main prediction endpoint maintains functionality."""
        request_data = get_prediction_request_template(
            latitude=GOLDEN_TEST_LOCATION["latitude"],
            longitude=GOLDEN_TEST_LOCATION["longitude"],
            season="rut"
        )
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=request_data,
            timeout=REQUEST_TIMEOUT
        )
        response_time = time.time() - start_time
        
        assert response.status_code == 200, f"Prediction request failed: {response.text}"
        
        data = response.json()
        
        # Validate response structure
        structure_errors = validate_response_structure(data)
        assert len(structure_errors) == 0, f"Response structure issues: {structure_errors}"
        
        # Validate performance
        assert response_time < PERFORMANCE_BENCHMARKS["api_response_time_max"], \
            f"Response time {response_time:.2f}s exceeds limit"
        
        # Validate camera confidence is preserved
        notes = data.get("notes", "")
        confidence_match = self._extract_camera_confidence(notes)
        if confidence_match:
            confidence = float(confidence_match)
            min_conf, max_conf = PERFORMANCE_BENCHMARKS["camera_confidence_acceptable_range"]
            assert min_conf <= confidence <= max_conf, \
                f"Camera confidence {confidence}% outside acceptable range"
    
    def test_configuration_endpoints(self):
        """Test configuration management endpoints."""
        # Test config status
        response = requests.get(f"{API_BASE_URL}/config/status", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        
        status_data = response.json()
        assert "environment" in status_data
        assert "version" in status_data
        assert "configuration_sections" in status_data
        
        # Test config parameters
        response = requests.get(f"{API_BASE_URL}/config/parameters", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        
        params_data = response.json()
        expected_sections = ["scoring_factors", "api_settings", "mature_buck_preferences"]
        for section in expected_sections:
            assert section in params_data, f"Config section {section} should be present"
    
    def test_camera_endpoints(self):
        """Test camera placement endpoints."""
        # Test trail camera placement
        camera_request = {
            "lat": GOLDEN_TEST_LOCATION["latitude"],
            "lon": GOLDEN_TEST_LOCATION["longitude"],
            "season": "rut",
            "target_buck_age": "mature"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/trail-cameras",
            json=camera_request,
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        trail_data = response.json()
        assert trail_data["type"] == "FeatureCollection"
        assert "features" in trail_data
        assert len(trail_data["features"]) > 0
        
        # Test optimal camera placement
        optimal_request = {
            "lat": GOLDEN_TEST_LOCATION["latitude"],
            "lon": GOLDEN_TEST_LOCATION["longitude"]
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/camera/optimal-placement",
            json=optimal_request,
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        optimal_data = response.json()
        assert optimal_data["type"] == "FeatureCollection"
        assert "optimal_camera" in optimal_data
        
        # Validate optimal camera confidence
        optimal_camera = optimal_data["optimal_camera"]
        confidence = optimal_camera.get("confidence", 0)
        assert confidence >= PERFORMANCE_BENCHMARKS["camera_confidence_target"] * 0.9, \
            f"Optimal camera confidence {confidence}% should be high"
    
    def test_scouting_endpoints(self):
        """Test scouting observation endpoints."""
        # Test observation types endpoint
        response = requests.get(f"{API_BASE_URL}/scouting/types", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        
        types_data = response.json()
        assert "observation_types" in types_data
        assert len(types_data["observation_types"]) > 0
        
        # Test observations query endpoint
        query_params = {
            "lat": GOLDEN_TEST_LOCATION["latitude"],
            "lon": GOLDEN_TEST_LOCATION["longitude"],
            "radius_miles": 2.0
        }
        
        response = requests.get(
            f"{API_BASE_URL}/scouting/observations",
            params=query_params,
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        observations_data = response.json()
        assert "observations" in observations_data
        assert "total_count" in observations_data
        assert "query_parameters" in observations_data
    
    def test_rules_endpoint_preserved(self):
        """Test that the rules endpoint is preserved."""
        response = requests.get(f"{API_BASE_URL}/rules", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        
        rules_data = response.json()
        assert isinstance(rules_data, list)
        assert len(rules_data) > 0, "Should have prediction rules"
    
    def test_enhanced_endpoints_availability(self):
        """Test that enhanced endpoints are available if the system supports them."""
        # Try to access enhanced endpoint (may not be available in all environments)
        try:
            response = requests.get(f"{API_BASE_URL}/enhanced/status", timeout=5)
            if response.status_code == 200:
                # Enhanced system is available
                enhanced_data = response.json()
                assert "enhanced_predictions" in enhanced_data or "status" in enhanced_data
        except requests.exceptions.RequestException:
            # Enhanced system not available - this is okay
            pass
    
    def _extract_camera_confidence(self, notes: str) -> str:
        """Extract camera confidence percentage from notes."""
        import re
        confidence_match = re.search(r'Confidence.*?(\d+\.?\d*)%', notes)
        return confidence_match.group(1) if confidence_match else None


class TestArchitecturePerformance:
    """Performance tests for the refactored architecture."""
    
    def test_prediction_performance_maintained(self):
        """Test that prediction performance is maintained after refactoring."""
        request_data = get_prediction_request_template()
        
        # Test multiple requests to get average performance
        response_times = []
        
        for _ in range(3):
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/predict",
                json=request_data,
                timeout=REQUEST_TIMEOUT
            )
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # Performance should be maintained
        assert avg_response_time < PERFORMANCE_BENCHMARKS["api_response_time_max"], \
            f"Average response time {avg_response_time:.2f}s exceeds limit"
        assert max_response_time < PERFORMANCE_BENCHMARKS["api_response_time_max"], \
            f"Max response time {max_response_time:.2f}s exceeds limit"
    
    def test_concurrent_requests_handling(self):
        """Test that the refactored system handles concurrent requests."""
        import threading
        import queue
        
        request_data = get_prediction_request_template()
        results_queue = queue.Queue()
        
        def make_request():
            try:
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE_URL}/predict",
                    json=request_data,
                    timeout=REQUEST_TIMEOUT
                )
                response_time = time.time() - start_time
                results_queue.put({
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": response.status_code == 200
                })
            except Exception as e:
                results_queue.put({
                    "status_code": 0,
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                })
        
        # Launch 3 concurrent requests
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=REQUEST_TIMEOUT + 5)
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == 3, "All requests should complete"
        
        successful_requests = [r for r in results if r["success"]]
        assert len(successful_requests) >= 2, "At least 2/3 concurrent requests should succeed"
        
        # Check response times are reasonable
        for result in successful_requests:
            assert result["response_time"] < REQUEST_TIMEOUT, \
                f"Concurrent request took {result['response_time']:.2f}s"


class TestBackwardCompatibility:
    """Test that the refactored system maintains backward compatibility."""
    
    def test_api_response_format_unchanged(self):
        """Test that API response formats haven't changed."""
        request_data = get_prediction_request_template()
        
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=request_data,
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields are present
        required_fields = [
            "travel_corridors", "bedding_zones", "feeding_areas",
            "stand_rating", "notes", "terrain_heatmap", "vegetation_heatmap"
        ]
        
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from response"
        
        # Verify GeoJSON structure
        for geojson_field in ["travel_corridors", "bedding_zones", "feeding_areas"]:
            geojson_data = data[geojson_field]
            assert geojson_data["type"] == "FeatureCollection"
            assert "features" in geojson_data
    
    def test_camera_confidence_preservation(self):
        """Test that camera confidence values are preserved."""
        request_data = get_prediction_request_template(
            latitude=GOLDEN_TEST_LOCATION["latitude"],
            longitude=GOLDEN_TEST_LOCATION["longitude"]
        )
        
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=request_data,
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        
        data = response.json()
        notes = data.get("notes", "")
        
        # Extract camera confidence
        confidence_match = self._extract_camera_confidence(notes)
        if confidence_match:
            confidence = float(confidence_match)
            
            # Should maintain our target of 95% (allow some tolerance)
            target = PERFORMANCE_BENCHMARKS["camera_confidence_target"]
            assert abs(confidence - target) <= 5.0, \
                f"Camera confidence {confidence}% differs significantly from target {target}%"
    
    def _extract_camera_confidence(self, notes: str) -> str:
        """Extract camera confidence percentage from notes."""
        import re
        confidence_match = re.search(r'Confidence.*?(\d+\.?\d*)%', notes)
        return confidence_match.group(1) if confidence_match else None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
