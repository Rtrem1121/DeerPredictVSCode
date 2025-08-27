"""
Integration tests for API endpoints.

These tests validate that the API maintains its current excellent behavior
and response structure during refactoring.
"""

import pytest
import requests
import json
import time
from typing import Dict, Any
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.fixtures.test_data import (
    GOLDEN_TEST_LOCATION,
    TEST_LOCATIONS,
    PERFORMANCE_BENCHMARKS,
    EXPECTED_API_RESPONSE_STRUCTURE,
    get_prediction_request_template,
    get_rut_season_request,
    validate_response_structure
)

class TestPredictionAPI:
    """Integration tests for the main prediction API."""
    
    @pytest.fixture(scope="class")
    def backend_url(self):
        """Fixture providing backend URL."""
        return os.getenv("BACKEND_URL", "http://localhost:8000")
    
    def test_backend_health(self, backend_url):
        """Test that backend is running and healthy."""
        try:
            response = requests.get(f"{backend_url}/health", timeout=10)
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Backend not accessible: {e}")
    
    def test_prediction_endpoint_basic(self, backend_url):
        """Test basic prediction endpoint functionality."""
        request_data = get_prediction_request_template()
        
        response = requests.post(
            f"{backend_url}/predict",
            json=request_data,
            timeout=60
        )
        
        assert response.status_code == 200, f"Prediction request failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Validate response structure
        structure_errors = validate_response_structure(data)
        assert len(structure_errors) == 0, f"Response structure errors: {structure_errors}"
    
    def test_golden_location_prediction(self, backend_url):
        """Test prediction for golden test location (89.1% confidence)."""
        request_data = get_prediction_request_template(
            latitude=GOLDEN_TEST_LOCATION["latitude"],
            longitude=GOLDEN_TEST_LOCATION["longitude"],
            include_camera=True
        )
        
        start_time = time.time()
        response = requests.post(
            f"{backend_url}/predict",
            json=request_data,
            timeout=60
        )
        response_time = time.time() - start_time
        
        # Validate response
        assert response.status_code == 200, f"Golden location prediction failed: {response.text}"
        
        data = response.json()
        
        # Validate camera placement confidence
        assert "camera_placement" in data, "Response should include camera placement"
        camera_data = data["camera_placement"]
        
        confidence = camera_data.get("confidence", 0)
        assert 87.0 <= confidence <= 91.0, f"Camera confidence {confidence}% should be around 89.1%"
        
        # Validate response time
        assert response_time <= PERFORMANCE_BENCHMARKS["api_response_time_max"], \
            f"Response time {response_time:.2f}s exceeded limit {PERFORMANCE_BENCHMARKS['api_response_time_max']}s"
        
        # Validate reasoning is present
        reasoning = camera_data.get("reasoning", "")
        assert reasoning, "Camera placement should include reasoning"
        assert len(reasoning) > 10, "Reasoning should be descriptive"
    
    def test_mature_buck_analysis(self, backend_url):
        """Test mature buck analysis in prediction response."""
        request_data = get_rut_season_request()
        
        response = requests.post(
            f"{backend_url}/predict",
            json=request_data,
            timeout=60
        )
        
        assert response.status_code == 200, f"Mature buck prediction failed: {response.text}"
        
        data = response.json()
        
        # Validate mature buck analysis is present
        assert "mature_buck_analysis" in data, "Response should include mature buck analysis"
        buck_data = data["mature_buck_analysis"]
        
        # Validate movement probability during rut
        movement_prob = buck_data.get("movement_probability", 0)
        assert movement_prob >= 0.75, f"Rut movement probability {movement_prob} should be high"
        
        # Validate confidence score is reasonable
        confidence = buck_data.get("confidence_score", 0)
        assert 0.3 <= confidence <= 0.8, f"Mature buck confidence {confidence} should be reasonable"
    
    def test_multiple_locations(self, backend_url):
        """Test prediction API across multiple locations."""
        for location in TEST_LOCATIONS:
            request_data = get_prediction_request_template(
                latitude=location["latitude"],
                longitude=location["longitude"]
            )
            
            response = requests.post(
                f"{backend_url}/predict",
                json=request_data,
                timeout=60
            )
            
            assert response.status_code == 200, \
                f"Prediction failed for {location['name']}: {response.text}"
            
            data = response.json()
            
            # Validate basic structure
            structure_errors = validate_response_structure(data)
            assert len(structure_errors) == 0, \
                f"Structure errors for {location['name']}: {structure_errors}"
            
            # Validate minimum confidence
            pred_confidence = data.get("prediction_confidence", 0)
            assert pred_confidence > 0, f"Prediction confidence should be positive for {location['name']}"
    
    def test_prediction_with_date(self, backend_url):
        """Test prediction with specific hunt date."""
        # Test early season
        early_request = get_prediction_request_template(hunt_date="2025-10-01")
        early_response = requests.post(f"{backend_url}/predict", json=early_request, timeout=60)
        assert early_response.status_code == 200
        
        # Test rut season
        rut_request = get_prediction_request_template(hunt_date="2025-11-15")
        rut_response = requests.post(f"{backend_url}/predict", json=rut_request, timeout=60)
        assert rut_response.status_code == 200
        
        # Rut should show higher mature buck activity
        early_data = early_response.json()
        rut_data = rut_response.json()
        
        if "mature_buck_analysis" in early_data and "mature_buck_analysis" in rut_data:
            early_buck = early_data.get("mature_buck_analysis", {})
            rut_buck = rut_data.get("mature_buck_analysis", {})
            
            early_movement = early_buck.get("movement_probability", 0)
            rut_movement = rut_buck.get("movement_probability", 0)
            
            # Rut should generally have higher movement
            assert rut_movement >= early_movement, \
                f"Rut movement {rut_movement} should be >= early season {early_movement}"

class TestAPIErrorHandling:
    """Test API error handling and edge cases."""
    
    @pytest.fixture(scope="class")
    def backend_url(self):
        """Fixture providing backend URL."""
        return os.getenv("BACKEND_URL", "http://localhost:8000")
    
    def test_invalid_coordinates(self, backend_url):
        """Test API handling of invalid coordinates."""
        invalid_requests = [
            {"latitude": 999, "longitude": 999},  # Out of range
            {"latitude": "invalid", "longitude": "invalid"},  # Wrong type
            {"latitude": None, "longitude": None},  # Null values
        ]
        
        for invalid_data in invalid_requests:
            response = requests.post(
                f"{backend_url}/predict",
                json=invalid_data,
                timeout=30
            )
            
            # Should return error status or handle gracefully
            assert response.status_code in [400, 422, 500], \
                f"Invalid request should return error status, got {response.status_code}"
    
    def test_missing_required_fields(self, backend_url):
        """Test API handling of missing required fields."""
        incomplete_requests = [
            {"latitude": 44.0},  # Missing longitude
            {"longitude": -72.0},  # Missing latitude
            {},  # Empty request
        ]
        
        for incomplete_data in incomplete_requests:
            response = requests.post(
                f"{backend_url}/predict",
                json=incomplete_data,
                timeout=30
            )
            
            # Should return validation error
            assert response.status_code in [400, 422], \
                f"Incomplete request should return validation error, got {response.status_code}"
    
    def test_malformed_json(self, backend_url):
        """Test API handling of malformed JSON."""
        response = requests.post(
            f"{backend_url}/predict",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # Should return JSON parsing error
        assert response.status_code in [400, 422], \
            f"Malformed JSON should return error, got {response.status_code}"

class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    @pytest.fixture(scope="class")
    def backend_url(self):
        """Fixture providing backend URL."""
        return os.getenv("BACKEND_URL", "http://localhost:8000")
    
    def test_prediction_response_time(self, backend_url):
        """Test that prediction API meets response time requirements."""
        request_data = get_prediction_request_template()
        
        response_times = []
        
        # Test multiple requests to get average
        for _ in range(3):
            start_time = time.time()
            response = requests.post(
                f"{backend_url}/predict",
                json=request_data,
                timeout=60
            )
            end_time = time.time()
            
            assert response.status_code == 200, "Request should succeed"
            response_times.append(end_time - start_time)
        
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # Validate performance requirements
        assert avg_response_time <= PERFORMANCE_BENCHMARKS["api_response_time_max"], \
            f"Average response time {avg_response_time:.2f}s exceeds limit"
        
        assert max_response_time <= PERFORMANCE_BENCHMARKS["api_response_time_max"] * 1.5, \
            f"Max response time {max_response_time:.2f}s too slow"
    
    def test_concurrent_requests(self, backend_url):
        """Test API handling of concurrent requests."""
        import threading
        import queue
        
        request_data = get_prediction_request_template()
        results = queue.Queue()
        
        def make_request():
            try:
                start_time = time.time()
                response = requests.post(
                    f"{backend_url}/predict",
                    json=request_data,
                    timeout=60
                )
                end_time = time.time()
                
                results.put({
                    "success": response.status_code == 200,
                    "response_time": end_time - start_time,
                    "status_code": response.status_code
                })
            except Exception as e:
                results.put({
                    "success": False,
                    "error": str(e),
                    "response_time": None
                })
        
        # Launch concurrent requests
        threads = []
        num_concurrent = 3  # Conservative for testing
        
        for _ in range(num_concurrent):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=90)  # Allow extra time for concurrent requests
        
        # Analyze results
        successful_requests = 0
        response_times = []
        
        while not results.empty():
            result = results.get()
            if result["success"]:
                successful_requests += 1
                if result["response_time"]:
                    response_times.append(result["response_time"])
        
        # At least most requests should succeed
        success_rate = successful_requests / num_concurrent
        assert success_rate >= 0.8, f"Success rate {success_rate:.1%} too low for concurrent requests"
        
        # Response times should still be reasonable
        if response_times:
            avg_concurrent_time = sum(response_times) / len(response_times)
            assert avg_concurrent_time <= PERFORMANCE_BENCHMARKS["api_response_time_max"] * 2, \
                f"Concurrent response time {avg_concurrent_time:.2f}s too slow"

class TestAPIRegression:
    """Regression tests to ensure API behavior is preserved."""
    
    @pytest.fixture(scope="class")
    def backend_url(self):
        """Fixture providing backend URL."""
        return os.getenv("BACKEND_URL", "http://localhost:8000")
    
    def test_preserve_api_contract(self, backend_url):
        """Test that API contract is preserved after refactoring."""
        request_data = get_prediction_request_template()
        
        response = requests.post(
            f"{backend_url}/predict",
            json=request_data,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate all expected fields are present
        for field in EXPECTED_API_RESPONSE_STRUCTURE["required_fields"]:
            assert field in data, f"Required field '{field}' missing from API response"
        
        # Validate camera placement structure if present
        if "camera_placement" in data:
            camera_fields = EXPECTED_API_RESPONSE_STRUCTURE["camera_placement_fields"]
            camera_data = data["camera_placement"]
            
            for field in camera_fields:
                assert field in camera_data, f"Camera field '{field}' missing from response"
        
        # Validate mature buck structure if present
        if "mature_buck_analysis" in data:
            buck_fields = EXPECTED_API_RESPONSE_STRUCTURE["mature_buck_fields"]
            buck_data = data["mature_buck_analysis"]
            
            for field in buck_fields:
                assert field in buck_data, f"Mature buck field '{field}' missing from response"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
