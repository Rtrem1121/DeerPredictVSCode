"""
Test configuration and utilities for deer prediction app testing.
"""

import pytest
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TEST_TIMEOUT = 60  # seconds
PERFORMANCE_TIMEOUT = 30  # seconds for performance tests

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "regression: marks tests as regression tests")

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on location."""
    for item in items:
        # Mark tests in unit/ directory as unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Mark tests in integration/ directory as integration tests
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark tests in e2e/ directory as end-to-end tests
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Mark performance tests
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)
        
        # Mark regression tests
        if "regression" in item.name.lower():
            item.add_marker(pytest.mark.regression)

# Global fixtures
@pytest.fixture(scope="session")
def backend_url():
    """Session-scoped backend URL fixture."""
    return BACKEND_URL

@pytest.fixture(scope="session")
def verify_backend_running(backend_url):
    """Verify backend is running before tests."""
    import requests
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code != 200:
            pytest.skip(f"Backend not healthy: {response.status_code}")
    except requests.exceptions.RequestException:
        pytest.skip("Backend not accessible - start backend with: python backend/main.py")
