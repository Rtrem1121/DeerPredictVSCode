# Test Suite Documentation

## Overview

This directory contains the comprehensive automated test suite for the Deer Prediction App. The tests follow a 3-tier pyramid structure:

```
        /\
       /  \  E2E Tests (5-10)
      /____\  
     /      \ Integration Tests (20-30)
    /________\
   /          \ Unit Tests (100+)
  /__________\
```

## Directory Structure

```
tests/
├── unit/                          # Unit tests for individual components
│   ├── test_gee_data_validation.py   # GEE data validation (CRITICAL)
│   ├── test_mature_buck.py           # Mature buck prediction logic
│   ├── test_configuration_service.py # Configuration management
│   └── test_camera_service.py        # Camera placement logic
│
├── integration/                   # Integration tests for services
│   ├── test_docker_health.py         # Docker container health (CRITICAL)
│   ├── test_api_endpoints.py         # API endpoint validation
│   └── test_refactored_architecture.py
│
├── e2e/                          # End-to-end tests
│   └── test_complete_system.py       # Full prediction pipeline
│
├── fixtures/                     # Shared test data
│   └── test_data.py
│
└── conftest.py                   # Shared pytest fixtures
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=backend --cov-report=html

# Run only critical tests
pytest -m critical

# Run only unit tests
pytest -m unit

# Run with parallel execution (faster)
pytest -n auto
```

### Test Categories

#### Critical Tests (Must Pass)
These tests protect against known issues and validate core functionality:

```bash
pytest -m critical -v
```

**Critical tests include:**
- ✅ GEE data validation (prevents false positives)
- ✅ Docker container health
- ✅ API endpoint availability
- ✅ Known location regression tests

#### Regression Tests
Tests that prevent known bugs from returning:

```bash
pytest -m regression -v
```

**Includes:**
- False positive location rejection (43.31, -73.215)
- Hansen 2000 vs Sentinel-2 temporal consistency
- Known true positive validation

#### Unit Tests
Fast tests for individual components:

```bash
pytest -m unit -v
```

#### Integration Tests
Tests for service interactions:

```bash
pytest -m integration -v
```

**Requires:** Docker containers must be running
```bash
docker compose up -d
```

#### End-to-End Tests
Full system tests through Docker stack:

```bash
pytest -m e2e -v
```

**Requires:** Full Docker stack running

## Test Configuration

### pytest.ini
Main pytest configuration file at project root. Sets:
- Test discovery patterns
- Coverage targets (70% minimum)
- Timeout limits (30 seconds)
- Test markers

### Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Overall   | 70%    | TBD     |
| Core Prediction | 80% | TBD     |
| Data Validation | 90% | TBD     |
| API Endpoints | 80% | TBD     |

## Critical Test Scenarios

### 1. False Positive Prevention

**Test:** `test_known_false_positive_location_rejection`

**Purpose:** Prevent system from classifying mowed grass fields as bedding zones

**Ground Truth:** Location 43.31, -73.215 is a mowed grass field (user confirmed)

**Expected:** Low confidence (<50%) OR validation warning present

**Prevents:** 94% confidence false positives like in August 2025 incident

### 2. Temporal Data Consistency

**Test:** `test_hansen_canopy_vs_sentinel2_temporal_consistency`

**Purpose:** Detect when Hansen 2000 data (25 years old) doesn't match current Sentinel-2

**Example:** Hansen shows 95% canopy, but Sentinel-2 shows 35% (land converted to field)

**Action:** Flag temporal discrepancy > 40% with validation warning

### 3. True Positive Validation

**Test:** `test_known_true_positive_location_validation`

**Purpose:** Ensure system still works correctly on known good locations

**Ground Truth:** Location 44.26, -72.58 is forested Vermont hunting area

**Expected:** Bedding zones with confidence > 40%

## Writing New Tests

### Test Template

```python
import pytest

@pytest.mark.unit  # or integration, e2e
@pytest.mark.critical  # if critical test
class TestYourFeature:
    """Clear description of what's being tested"""
    
    @pytest.fixture
    def your_fixture(self):
        """Setup code"""
        return YourComponent()
    
    def test_specific_behavior(self, your_fixture):
        """
        Test description
        
        Expected: Clear success criteria
        """
        result = your_fixture.method()
        
        assert result == expected, "Failure message"
        print("✅ Success message")
```

### Test Naming Convention

- **test_[component]_[behavior]**: `test_gee_data_temporal_consistency`
- **test_known_[location]_[expected]**: `test_known_false_positive_rejection`
- **test_[api]_endpoint_[scenario]**: `test_prediction_endpoint_invalid_coords`

## Continuous Integration

### GitHub Actions Workflow

Tests run automatically on:
- Every push to master
- Every pull request
- Nightly schedule

**Workflow stages:**
1. Unit tests (fast, no Docker)
2. Integration tests (requires Docker)
3. E2E tests (full stack)
4. Coverage report upload

### Pre-commit Hooks (Future)

```bash
# Run critical tests before commit
pytest -m critical --tb=short
```

## Troubleshooting

### Tests Failing with "Backend not ready"

**Issue:** Integration tests can't connect to Docker containers

**Solution:**
```bash
# Ensure containers are running
docker compose up -d

# Wait for health checks to pass
docker compose ps

# Check logs
docker compose logs backend
```

### Tests Hanging

**Issue:** Test exceeds 30-second timeout

**Solution:**
- Check if backend is actually running
- Verify GEE credentials are valid
- Look for infinite loops in code

### Coverage Too Low

**Issue:** Coverage below 70% threshold

**Solution:**
- Add unit tests for uncovered functions
- Use `pytest --cov-report=html` to see gaps
- Focus on critical paths first

## Contributing

### Adding New Tests

1. **Identify test tier:** Unit, Integration, or E2E?
2. **Add appropriate markers:** `@pytest.mark.unit`, `@pytest.mark.critical`
3. **Follow naming conventions:** `test_component_behavior`
4. **Document expected behavior:** Clear docstrings
5. **Verify test passes:** `pytest tests/path/to/test.py -v`

### Test Quality Checklist

- ✅ Test is isolated (no external dependencies unless integration test)
- ✅ Test is deterministic (same input = same output)
- ✅ Test has clear failure messages
- ✅ Test completes within timeout (30 seconds)
- ✅ Test documents expected behavior

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)

---

**Remember:** Tests are not just for catching bugs—they're executable documentation that shows how the system should behave. Write tests that future developers (including yourself) will thank you for! 🧪✨
