"""
End-to-End test suite for the Deer Prediction App.

This comprehensive test suite validates the entire refactored system
from the Streamlit frontend through the FastAPI backend to ensure
all functionality is preserved and working correctly.
"""

import pytest
import sys
import os
import requests
import time
import subprocess
import threading
import signal
from typing import Dict, Any, Optional
from pathlib import Path

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
FRONTEND_URL = "http://localhost:8501"
REQUEST_TIMEOUT = 45


class TestEndToEndSystem:
    """Complete end-to-end system testing."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        cls.api_process = None
        cls.frontend_process = None
        cls.api_ready = False
        cls.frontend_ready = False
    
    @classmethod
    def teardown_class(cls):
        """Clean up test environment."""
        if cls.api_process:
            cls.api_process.terminate()
        if cls.frontend_process:
            cls.frontend_process.terminate()
    
    def test_complete_prediction_workflow(self):
        """Test the complete prediction workflow from start to finish."""
        print("\n🔍 Testing Complete Prediction Workflow")
        
        # Step 1: Health check
        print("1. Checking API health...")
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=REQUEST_TIMEOUT)
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] in ["healthy", "degraded"]
        print(f"   ✅ API Status: {health_data['status']}")
        
        # Step 2: Test configuration
        print("2. Validating configuration...")
        config_response = requests.get(f"{API_BASE_URL}/config/status", timeout=REQUEST_TIMEOUT)
        assert config_response.status_code == 200
        config_data = config_response.json()
        assert "environment" in config_data
        print(f"   ✅ Environment: {config_data['environment']}")
        
        # Step 3: Full prediction request
        print("3. Making prediction request...")
        request_data = get_prediction_request_template(
            latitude=GOLDEN_TEST_LOCATION["latitude"],
            longitude=GOLDEN_TEST_LOCATION["longitude"],
            season="rut",
            property_size=100,
            target_buck_age="mature"
        )
        
        start_time = time.time()
        prediction_response = requests.post(
            f"{API_BASE_URL}/predict",
            json=request_data,
            timeout=REQUEST_TIMEOUT
        )
        response_time = time.time() - start_time
        
        assert prediction_response.status_code == 200, \
            f"Prediction failed: {prediction_response.text}"
        
        prediction_data = prediction_response.json()
        print(f"   ✅ Prediction completed in {response_time:.2f}s")
        
        # Step 4: Validate response structure
        print("4. Validating response structure...")
        structure_errors = validate_response_structure(prediction_data)
        assert len(structure_errors) == 0, f"Structure issues: {structure_errors}"
        print(f"   ✅ Response structure valid")
        
        # Step 5: Validate key outputs
        print("5. Validating prediction outputs...")
        
        # Check required components
        required_components = ["travel_corridors", "bedding_zones", "feeding_areas"]
        for component in required_components:
            assert component in prediction_data
            component_data = prediction_data[component]
            assert component_data["type"] == "FeatureCollection"
            assert len(component_data["features"]) > 0
        
        # Check stand rating
        stand_rating = prediction_data.get("stand_rating", 0)
        assert 0 <= stand_rating <= 100, f"Stand rating {stand_rating} out of range"
        
        # Check heatmaps
        assert "terrain_heatmap" in prediction_data
        assert "vegetation_heatmap" in prediction_data
        
        print(f"   ✅ Stand Rating: {stand_rating}/100")
        
        # Step 6: Validate camera confidence
        print("6. Validating camera confidence...")
        notes = prediction_data.get("notes", "")
        confidence_match = self._extract_camera_confidence(notes)
        
        if confidence_match:
            confidence = float(confidence_match)
            target = PERFORMANCE_BENCHMARKS["camera_confidence_target"]
            print(f"   ✅ Camera Confidence: {confidence}% (target: {target}%)")
            
            # Validate confidence is within acceptable range
            min_conf, max_conf = PERFORMANCE_BENCHMARKS["camera_confidence_acceptable_range"]
            assert min_conf <= confidence <= max_conf, \
                f"Camera confidence {confidence}% outside acceptable range"
        else:
            print("   ⚠️  Camera confidence not found in notes")
        
        # Step 7: Performance validation
        print("7. Validating performance...")
        max_time = PERFORMANCE_BENCHMARKS["api_response_time_max"]
        assert response_time < max_time, \
            f"Response time {response_time:.2f}s exceeds limit of {max_time}s"
        print(f"   ✅ Performance: {response_time:.2f}s < {max_time}s")
        
        print("\n🎉 Complete workflow test passed!")
        return prediction_data
    
    def test_camera_placement_workflow(self):
        """Test the complete camera placement workflow."""
        print("\n📷 Testing Camera Placement Workflow")
        
        # Step 1: Trail camera placement
        print("1. Testing trail camera placement...")
        camera_request = {
            "lat": GOLDEN_TEST_LOCATION["latitude"],
            "lon": GOLDEN_TEST_LOCATION["longitude"],
            "season": "rut",
            "target_buck_age": "mature"
        }
        
        trail_response = requests.post(
            f"{API_BASE_URL}/trail-cameras",
            json=camera_request,
            timeout=REQUEST_TIMEOUT
        )
        assert trail_response.status_code == 200
        trail_data = trail_response.json()
        
        assert trail_data["type"] == "FeatureCollection"
        trail_cameras = trail_data["features"]
        assert len(trail_cameras) > 0
        print(f"   ✅ Found {len(trail_cameras)} trail camera locations")
        
        # Step 2: Optimal camera placement
        print("2. Testing optimal camera placement...")
        optimal_request = {
            "lat": GOLDEN_TEST_LOCATION["latitude"],
            "lon": GOLDEN_TEST_LOCATION["longitude"]
        }
        
        optimal_response = requests.post(
            f"{API_BASE_URL}/api/camera/optimal-placement",
            json=optimal_request,
            timeout=REQUEST_TIMEOUT
        )
        assert optimal_response.status_code == 200
        optimal_data = optimal_response.json()
        
        assert optimal_data["type"] == "FeatureCollection"
        assert "optimal_camera" in optimal_data
        
        optimal_camera = optimal_data["optimal_camera"]
        confidence = optimal_camera.get("confidence", 0)
        print(f"   ✅ Optimal camera confidence: {confidence}%")
        
        # Validate high confidence
        min_optimal_confidence = PERFORMANCE_BENCHMARKS["camera_confidence_target"] * 0.9
        assert confidence >= min_optimal_confidence, \
            f"Optimal camera confidence {confidence}% should be >= {min_optimal_confidence}%"
        
        print("\n📷 Camera placement workflow passed!")
        return {
            "trail_cameras": trail_data,
            "optimal_camera": optimal_data
        }
    
    def test_scouting_workflow(self):
        """Test the scouting observation workflow."""
        print("\n🔍 Testing Scouting Workflow")
        
        # Step 1: Get observation types
        print("1. Getting observation types...")
        types_response = requests.get(f"{API_BASE_URL}/scouting/types", timeout=REQUEST_TIMEOUT)
        assert types_response.status_code == 200
        types_data = types_response.json()
        
        assert "observation_types" in types_data
        observation_types = types_data["observation_types"]
        assert len(observation_types) > 0
        print(f"   ✅ Found {len(observation_types)} observation types")
        
        # Step 2: Query observations
        print("2. Querying observations...")
        query_params = {
            "lat": GOLDEN_TEST_LOCATION["latitude"],
            "lon": GOLDEN_TEST_LOCATION["longitude"],
            "radius_miles": 2.0
        }
        
        obs_response = requests.get(
            f"{API_BASE_URL}/scouting/observations",
            params=query_params,
            timeout=REQUEST_TIMEOUT
        )
        assert obs_response.status_code == 200
        obs_data = obs_response.json()
        
        assert "observations" in obs_data
        assert "total_count" in obs_data
        print(f"   ✅ Found {obs_data['total_count']} observations")
        
        print("\n🔍 Scouting workflow passed!")
        return obs_data
    
    def test_configuration_workflow(self):
        """Test the configuration management workflow."""
        print("\n⚙️ Testing Configuration Workflow")
        
        # Step 1: Get configuration parameters
        print("1. Getting configuration parameters...")
        params_response = requests.get(f"{API_BASE_URL}/config/parameters", timeout=REQUEST_TIMEOUT)
        assert params_response.status_code == 200
        params_data = params_response.json()
        
        expected_sections = ["scoring_factors", "api_settings", "mature_buck_preferences"]
        for section in expected_sections:
            assert section in params_data, f"Config section {section} missing"
        
        print(f"   ✅ Configuration sections: {list(params_data.keys())}")
        
        # Step 2: Validate scoring factors
        scoring_factors = params_data.get("scoring_factors", {})
        required_factors = ["water_weight", "food_weight", "cover_weight", "terrain_weight"]
        for factor in required_factors:
            assert factor in scoring_factors, f"Scoring factor {factor} missing"
            weight = scoring_factors[factor]
            assert 0 <= weight <= 1, f"Scoring factor {factor} weight {weight} out of range"
        
        print("   ✅ Scoring factors validated")
        
        print("\n⚙️ Configuration workflow passed!")
        return params_data
    
    def test_system_resilience(self):
        """Test system resilience and error handling."""
        print("\n🛡️ Testing System Resilience")
        
        # Test 1: Invalid coordinates
        print("1. Testing invalid coordinates...")
        invalid_request = get_prediction_request_template(
            latitude=999,  # Invalid latitude
            longitude=999  # Invalid longitude
        )
        
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=invalid_request,
            timeout=REQUEST_TIMEOUT
        )
        # Should handle gracefully (may return 400 or 200 with error message)
        assert response.status_code in [200, 400, 422]
        print("   ✅ Invalid coordinates handled")
        
        # Test 2: Missing required fields
        print("2. Testing missing required fields...")
        incomplete_request = {"lat": 40.0}  # Missing required fields
        
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=incomplete_request,
            timeout=REQUEST_TIMEOUT
        )
        # Should return validation error
        assert response.status_code in [400, 422]
        print("   ✅ Missing fields handled")
        
        # Test 3: Large property size
        print("3. Testing edge case values...")
        edge_request = get_prediction_request_template(
            property_size=10000  # Very large property
        )
        
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=edge_request,
            timeout=REQUEST_TIMEOUT
        )
        # Should handle gracefully
        assert response.status_code in [200, 400]
        print("   ✅ Edge cases handled")
        
        print("\n🛡️ System resilience tests passed!")
    
    def test_performance_under_load(self):
        """Test system performance under moderate load."""
        print("\n⚡ Testing Performance Under Load")
        
        import threading
        import queue
        
        request_data = get_prediction_request_template()
        results_queue = queue.Queue()
        
        def make_request(request_id):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE_URL}/predict",
                    json=request_data,
                    timeout=REQUEST_TIMEOUT
                )
                response_time = time.time() - start_time
                
                results_queue.put({
                    "id": request_id,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": response.status_code == 200
                })
            except Exception as e:
                results_queue.put({
                    "id": request_id,
                    "status_code": 0,
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                })
        
        # Launch 5 concurrent requests
        print("1. Launching 5 concurrent prediction requests...")
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=REQUEST_TIMEOUT + 10)
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        print(f"2. Collected {len(results)} results")
        
        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        success_rate = len(successful_requests) / len(results) * 100
        
        print(f"   ✅ Success rate: {success_rate:.1f}% ({len(successful_requests)}/{len(results)})")
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            
            print(f"   ✅ Average response time: {avg_time:.2f}s")
            print(f"   ✅ Maximum response time: {max_time:.2f}s")
            
            # Performance assertions
            assert success_rate >= 80, f"Success rate {success_rate}% too low"
            assert avg_time < REQUEST_TIMEOUT, f"Average time {avg_time:.2f}s too high"
            assert max_time < REQUEST_TIMEOUT, f"Max time {max_time:.2f}s too high"
        
        print("\n⚡ Performance tests passed!")
    
    def test_data_consistency(self):
        """Test data consistency across multiple requests."""
        print("\n🔄 Testing Data Consistency")
        
        request_data = get_prediction_request_template(
            latitude=GOLDEN_TEST_LOCATION["latitude"],
            longitude=GOLDEN_TEST_LOCATION["longitude"],
            season="rut"
        )
        
        # Make 3 identical requests
        responses = []
        for i in range(3):
            print(f"Making request {i+1}/3...")
            response = requests.post(
                f"{API_BASE_URL}/predict",
                json=request_data,
                timeout=REQUEST_TIMEOUT
            )
            assert response.status_code == 200
            responses.append(response.json())
        
        # Compare key metrics
        stand_ratings = [r.get("stand_rating", 0) for r in responses]
        feature_counts = []
        
        for response in responses:
            count = 0
            for component in ["travel_corridors", "bedding_zones", "feeding_areas"]:
                if component in response:
                    count += len(response[component].get("features", []))
            feature_counts.append(count)
        
        # Validate consistency
        stand_rating_variance = max(stand_ratings) - min(stand_ratings)
        feature_count_variance = max(feature_counts) - min(feature_counts)
        
        print(f"   ✅ Stand ratings: {stand_ratings} (variance: {stand_rating_variance})")
        print(f"   ✅ Feature counts: {feature_counts} (variance: {feature_count_variance})")
        
        # Allow some variance but not too much
        assert stand_rating_variance <= 10, f"Stand rating variance {stand_rating_variance} too high"
        assert feature_count_variance <= 5, f"Feature count variance {feature_count_variance} too high"
        
        print("\n🔄 Data consistency tests passed!")
    
    def _extract_camera_confidence(self, notes: str) -> Optional[str]:
        """Extract camera confidence percentage from notes."""
        import re
        confidence_match = re.search(r'Confidence.*?(\d+\.?\d*)%', notes)
        return confidence_match.group(1) if confidence_match else None


class TestSystemIntegration:
    """Test system integration and component interaction."""
    
    def test_service_layer_integration(self):
        """Test that all services integrate correctly."""
        print("\n🔧 Testing Service Layer Integration")
        
        # Test each service individually first
        services_to_test = [
            ("configuration", "/config/status"),
            ("camera", "/api/camera/optimal-placement"),
            ("scouting", "/scouting/types"),
        ]
        
        for service_name, endpoint in services_to_test:
            print(f"Testing {service_name} service...")
            
            if service_name == "camera":
                # Camera service needs POST data
                response = requests.post(
                    f"{API_BASE_URL}{endpoint}",
                    json={"lat": 40.0, "lon": -74.0},
                    timeout=REQUEST_TIMEOUT
                )
            else:
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=REQUEST_TIMEOUT)
            
            assert response.status_code == 200, f"{service_name} service failed"
            print(f"   ✅ {service_name} service working")
        
        print("\n🔧 Service integration tests passed!")
    
    def test_router_layer_integration(self):
        """Test that all routers integrate correctly."""
        print("\n🛣️ Testing Router Layer Integration")
        
        # Test main router endpoints
        main_endpoints = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/rules", "GET"),
        ]
        
        for endpoint, method in main_endpoints:
            print(f"Testing {method} {endpoint}...")
            
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=REQUEST_TIMEOUT)
            else:
                response = requests.post(f"{API_BASE_URL}{endpoint}", timeout=REQUEST_TIMEOUT)
            
            assert response.status_code == 200, f"Router endpoint {endpoint} failed"
            print(f"   ✅ {endpoint} working")
        
        print("\n🛣️ Router integration tests passed!")


if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "-s"])
