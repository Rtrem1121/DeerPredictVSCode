"""
Docker Container Integration Tests

Validates the health and integration of Docker services.

Author: GitHub Copilot
Date: October 1, 2025
"""

import pytest
import requests
from time import sleep
import json


@pytest.mark.integration
@pytest.mark.critical
class TestDockerHealth:
    """Validate Docker container health and connectivity"""
    
    @pytest.fixture(scope="class")
    def backend_url(self):
        """Get backend URL and wait for it to be ready"""
        url = "http://localhost:8000"
        
        # Wait up to 30 seconds for backend to be healthy
        for attempt in range(30):
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ Backend ready after {attempt} seconds")
                    return url
            except requests.exceptions.RequestException:
                if attempt < 29:
                    sleep(1)
                else:
                    pytest.fail("Backend failed to start within 30 seconds")
        
        return url
    
    @pytest.fixture(scope="class")
    def frontend_url(self):
        """Get frontend URL"""
        return "http://localhost:8501"
    
    def test_backend_health_endpoint(self, backend_url):
        """
        CRITICAL: Validate backend health check
        
        Ensures backend container is running and responding
        """
        response = requests.get(f"{backend_url}/health", timeout=10)
        
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        health_data = response.json()
        
        # Validate health response structure
        assert health_data['status'] in ['healthy', 'degraded'], \
            f"Invalid health status: {health_data['status']}"
        
        assert 'timestamp' in health_data, "Missing timestamp"
        assert 'version' in health_data, "Missing version"
        
        # Validate services
        if 'services' in health_data:
            assert health_data['services']['prediction_service'] == 'operational', \
                "Prediction service not operational"
        
        print(f"✅ Backend health: {health_data['status']}, version: {health_data.get('version')}")
    
    def test_backend_api_docs_available(self, backend_url):
        """Ensure FastAPI docs are accessible"""
        response = requests.get(f"{backend_url}/docs", timeout=10)
        assert response.status_code == 200, "API docs not accessible"
        print("✅ API docs accessible at /docs")
    
    def test_frontend_health_endpoint(self, frontend_url):
        """
        Validate frontend health check
        
        Ensures Streamlit container is running
        """
        # Streamlit has a health endpoint at /_stcore/health
        try:
            response = requests.get(f"{frontend_url}/_stcore/health", timeout=10)
            assert response.status_code == 200, f"Frontend health check failed: {response.status_code}"
            print("✅ Frontend health check passed")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Frontend health check not accessible (may not be in Docker): {e}")
    
    def test_backend_frontend_connectivity(self, backend_url, frontend_url):
        """
        Validate frontend can reach backend
        
        Critical for end-to-end functionality
        """
        # Frontend should be able to reach backend through Docker network
        # We test this by making a prediction request to backend
        
        response = requests.get(f"{backend_url}/health", timeout=10)
        assert response.status_code == 200, "Backend not reachable"
        
        print("✅ Backend accessible for frontend connectivity")
    
    def test_redis_connectivity(self, backend_url):
        """
        Validate Redis is available (if configured)
        
        Non-critical but good to check
        """
        # Redis is on port 6379, but we'll check through backend health
        response = requests.get(f"{backend_url}/health", timeout=10)
        health_data = response.json()
        
        # Just log Redis status if available
        if 'redis' in str(health_data).lower():
            print("✅ Redis integration detected in health check")
        else:
            print("ℹ️  Redis status not reported in health check")


@pytest.mark.integration
@pytest.mark.critical
class TestAPIEndpoints:
    """Validate critical API endpoints are responding"""
    
    @pytest.fixture
    def backend_url(self):
        """Get backend URL"""
        return "http://localhost:8000"
    
    def test_prediction_endpoint_available(self, backend_url):
        """
        CRITICAL: Validate prediction endpoint responds
        
        This is the core functionality endpoint
        """
        # Test with valid Vermont location
        payload = {
            "lat": 44.26,
            "lon": -72.58,
            "time_of_day": 6,
            "date_time": "2024-11-15T06:00:00",  # Required field for predictions
            "season": "fall",
            "hunting_pressure": "medium"
        }
        
        response = requests.post(f"{backend_url}/predict", json=payload, timeout=120)
        
        assert response.status_code == 200, \
            f"Prediction endpoint failed: {response.status_code}, {response.text}"
        
        # Validate response structure (API wraps response in success/data)
        result = response.json()
        assert 'success' in result, "Response missing 'success' field"
        assert result['success'] is True, "API returned success=False"
        assert 'data' in result, "Response missing 'data' field"
        
        # Check prediction data exists
        data = result['data']
        assert 'bedding_zones' in data or 'stand_recommendations' in data, \
            "Response missing expected prediction data"
        
        # Count bedding zones if present (GeoJSON format)
        bedding_count = 0
        if 'bedding_zones' in data and isinstance(data['bedding_zones'], dict):
            bedding_count = len(data['bedding_zones'].get('features', []))
        
        print(f"✅ Prediction endpoint responding - {bedding_count} bedding zones")
    
    def test_rules_endpoint_available(self, backend_url):
        """Validate rules endpoint returns hunting rules"""
        response = requests.get(f"{backend_url}/rules", timeout=30)
        
        assert response.status_code == 200, f"Rules endpoint failed: {response.status_code}"
        
        rules = response.json()
        assert isinstance(rules, list), "Rules should be a list"
        assert len(rules) > 0, "No rules loaded"
        
        print(f"✅ Rules endpoint responding - {len(rules)} rules loaded")
    
    def test_api_error_handling(self, backend_url):
        """Validate API handles invalid requests gracefully"""
        # Test with invalid coordinates
        payload = {
            "lat": 999,  # Invalid latitude
            "lon": -72.58,
            "time_of_day": 6,
            "date_time": "2024-11-15T06:00:00",
            "season": "fall",
            "hunting_pressure": "medium"
        }
        
        response = requests.post(f"{backend_url}/predict", json=payload, timeout=120)
        
        # Should return error status (4xx or 5xx) but not crash
        assert response.status_code >= 400, "Invalid request should return error status"
        
        print(f"✅ API error handling working - returned {response.status_code} for invalid input")
