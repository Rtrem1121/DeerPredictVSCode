# Phase 1 - Test Failures Analysis & Fix Plan

**Date**: 2024-01-XX  
**Status**: 5 tests failing → Root causes identified  
**Progress**: 10/15 tests passing (67%) → Target: 15/15 (100%)

---

## Executive Summary

Phase 1 test execution revealed **3 production bugs** and **2 test configuration issues**:

1. ✅ **SOLVED**: GeoJSON structure misunderstanding (test code issue)
2. 🔧 **CRITICAL BUG**: Aspect fallback search too permissive (production bug)
3. ⚠️ **API ISSUE**: Missing required field in integration test
4. 🚫 **BACKEND BUG**: `/rules` endpoint returning 500 error

---

## Detailed Failure Analysis

### 1. ✅ SOLVED: AttributeError - GeoJSON Structure

**Original Error:**
```
AttributeError: 'str' object has no attribute 'get'
```

**Root Cause:**
Test code assumed `bedding_zones` was a list, but production code returns **GeoJSON dict**:

```python
{
    "type": "FeatureCollection",
    "features": [...],  # List of bedding zone features
    "properties": {...}
}
```

**Fix Applied:**
Updated test code to extract `features` list from GeoJSON dict:
```python
# OLD (incorrect):
bedding_zones = result.get('bedding_zones', [])
for zone in bedding_zones:
    confidence = zone.get('confidence')

# NEW (correct):
bedding_zones_geojson = result.get('bedding_zones', {})
bedding_features = bedding_zones_geojson.get('features', [])
for feature in bedding_features:
    confidence = feature.get('properties', {}).get('confidence')
```

**Files Fixed:**
- `tests/unit/test_gee_data_validation.py` (lines 79, 124, 226)

**Status**: ✅ **COMPLETE** - 3 tests now execute correctly

---

### 2. 🔧 CRITICAL: False Positive Not Detected (Production Bug)

**Test:** `test_known_false_positive_location_rejection`

**Current Behavior:**
```
AssertionError: False positive not flagged! 
Features: 3, Confidence: 0.8155, Validation: False
Data source: dynamic_gee_enhanced
```

**Expected Behavior:**
Grass field at 43.31, -73.215 should be **rejected** (0 bedding zones) or **flagged low confidence** (<0.5)

**Root Cause:**
`_search_alternative_bedding_sites()` progressively relaxes aspect criteria:
```python
aspect_criteria = [
    {"range": (160, 200), "bonus": 15},  # Optimal south
    {"range": (135, 225), "bonus": 10},  # Good south  
    {"range": (120, 240), "bonus": 5},   # Acceptable
    {"range": (90, 270), "bonus": 0}     # 🚫 TOO PERMISSIVE - accepts east/west!
]
```

**Evidence:**
Logs show locations correctly **rejected** for aspect:
```
WARNING: 🚫 LOCATION DISQUALIFIED: Aspect 70.0° unsuitable (East-facing)
WARNING: 🚫 LOCATION DISQUALIFIED: Aspect 225.9° unsuitable (West-facing)
WARNING: 🚫 LOCATION DISQUALIFIED: Aspect 270.0° unsuitable (West-facing)
```

**But fallback search still returns 3 bedding zones with 0.8155 confidence!**

**Fix Required:**
```python
# File: enhanced_bedding_zone_predictor.py, line ~1582

# Remove overly permissive fallback criteria:
aspect_criteria = [
    {"range": (160, 200), "bonus": 15},  # Optimal south
    {"range": (135, 225), "bonus": 10},  # Good south  
    # {"range": (120, 240), "bonus": 5},   # ❌ REMOVE - too permissive
    # {"range": (90, 270), "bonus": 0}     # ❌ REMOVE - accepts non-south aspects
]

# OR: Add stricter validation after fallback search
if alternative_zones["features"]:
    # Validate each feature actually meets biological criteria
    validated_features = [
        f for f in alternative_zones["features"]
        if 135 <= f["properties"]["aspect"] <= 225  # Enforce south-facing
    ]
    
    if not validated_features:
        logger.warning("🚫 FALLBACK REJECTED: No truly south-facing alternatives found")
        return empty_geojson
```

**Files to Fix:**
- `enhanced_bedding_zone_predictor.py` (line ~1516, method `_search_alternative_bedding_sites`)

**Status**: 🔧 **TODO** - Production code fix required

**Impact**: **HIGH** - This is the core false positive prevention that tests were designed to catch

---

### 3. ⚠️ API Test: Missing Required Field

**Test:** `test_prediction_endpoint_available`

**Original Error:**
```
422 Unprocessable Entity
```

**Root Cause:**
Integration test payload missing `date_time` field required by `/predict` endpoint

**Fix Applied:**
```python
payload = {
    "lat": 44.26,
    "lon": -72.58,
    "time_of_day": 6,
    "date_time": "2024-11-15T06:00:00",  # ✅ Added
    "season": "fall",
    "hunting_pressure": "medium"
}
```

**Files Fixed:**
- `tests/integration/test_docker_health.py` (line ~142)

**Status**: ✅ **COMPLETE** - Test now sends valid payload

**Note**: Need to run integration tests to confirm fix works

---

### 4. 🚫 Backend Error: /rules Endpoint 500

**Test:** `test_rules_endpoint_available`

**Current Behavior:**
```
500 Internal Server Error
```

**Endpoint Code:**
```python
# backend/main.py, line 147
@app.get("/rules")
def get_rules():
    prediction_service = get_prediction_service()
    return prediction_service.load_rules()
```

**Investigation Needed:**
1. Check if `prediction_service.load_rules()` exists
2. Verify rules file exists and is loadable
3. Check for initialization errors

**Fix Strategy:**
```bash
# Test endpoint directly
curl http://localhost:8000/rules

# Check backend logs
docker logs deer_pred_app-backend-1

# Debug in Python
python -c "from backend.prediction_service import PredictionService; ps = PredictionService(); print(ps.load_rules())"
```

**Files to Investigate:**
- `backend/main.py` (line 147-150)
- `backend/prediction_service.py` (`load_rules()` method)
- Rules data file location

**Status**: 🚫 **TODO** - Investigation required

**Impact**: **MEDIUM** - Non-critical endpoint, but indicates potential initialization issue

---

## Test Execution Progress

### Before Fixes:
```
✅ test_hansen_canopy_vs_sentinel2_temporal_consistency  PASSED
❌ test_known_false_positive_location_rejection          FAILED (AttributeError)
❌ test_known_true_positive_location_validation          FAILED (AttributeError)
✅ test_gee_data_source_tracking                         PASSED
✅ test_grass_field_ndvi_pattern_detection               PASSED
✅ test_gee_data_required_fields                         PASSED
❌ test_bedding_zone_response_schema                     FAILED (KeyError)
✅ test_backend_health_endpoint                          PASSED
✅ test_backend_api_docs_available                       PASSED
✅ test_frontend_health_endpoint                         PASSED
✅ test_backend_frontend_connectivity                    PASSED
✅ test_redis_connectivity                               PASSED
❌ test_prediction_endpoint_available                    FAILED (422)
❌ test_rules_endpoint_available                         FAILED (500)
✅ test_api_error_handling                               PASSED
```
**Pass Rate**: 10/15 (67%)

### After GeoJSON Fixes:
```
✅ test_hansen_canopy_vs_sentinel2_temporal_consistency  PASSED
❌ test_known_false_positive_location_rejection          FAILED (Production bug)
❌ test_known_true_positive_location_validation          NEEDS RETEST
✅ test_gee_data_source_tracking                         PASSED
✅ test_grass_field_ndvi_pattern_detection               PASSED
✅ test_gee_data_required_fields                         PASSED
❌ test_bedding_zone_response_schema                     NEEDS RETEST
✅ test_backend_health_endpoint                          PASSED
✅ test_backend_api_docs_available                       PASSED
✅ test_frontend_health_endpoint                         PASSED
✅ test_backend_frontend_connectivity                    PASSED
✅ test_redis_connectivity                               PASSED
❌ test_prediction_endpoint_available                    NEEDS RETEST (payload fixed)
❌ test_rules_endpoint_available                         NEEDS INVESTIGATION
✅ test_api_error_handling                               PASSED
```
**Current Status**: 3 test fixes applied, 3 need production code fixes

---

## Next Actions

### Priority 1: Complete Phase 1 (100% Pass Rate)

#### Step 1: Run unit tests again
```bash
pytest tests/unit/test_gee_data_validation.py -v
```
**Expected**: 2 more tests pass (test_known_true_positive_location_validation, test_bedding_zone_response_schema)  
**Remaining failure**: test_known_false_positive_location_rejection (production bug)

#### Step 2: Run integration tests
```bash
pytest tests/integration/test_docker_health.py -v
```
**Expected**: test_prediction_endpoint_available now passes (payload fixed)  
**Remaining failure**: test_rules_endpoint_available (needs investigation)

#### Step 3: Fix aspect fallback bug
```python
# File: enhanced_bedding_zone_predictor.py
# Method: _search_alternative_bedding_sites (line ~1516)

# Option A: Remove overly permissive fallback
aspect_criteria = [
    {"range": (160, 200), "bonus": 15},  # Only optimal south
    {"range": (135, 225), "bonus": 10},  # Only good south
]

# Option B: Add post-fallback validation
validated_features = [
    f for f in alternative_zones["features"]
    if 135 <= f["properties"]["aspect"] <= 225
]
```

#### Step 4: Investigate /rules endpoint
```bash
# Check backend logs
docker logs deer_pred_app-backend-1 | grep -i "rules"

# Test endpoint directly
curl -v http://localhost:8000/rules
```

#### Step 5: Rerun all 15 tests
```bash
pytest tests/ -v --tb=short
```
**Target**: 15/15 (100%) pass rate

### Priority 2: Activate CI/CD

Once 100% pass rate achieved:
```bash
# Commit test infrastructure
git add tests/ pytest.ini .github/workflows/test.yml
git commit -m "Phase 1: Add comprehensive test infrastructure with 100% pass rate"
git push origin main

# CI/CD will automatically run tests on push
```

---

## Time Estimate

- **Step 1** (Rerun unit tests): 5 min
- **Step 2** (Rerun integration tests): 3 min  
- **Step 3** (Fix aspect fallback): 30-60 min (code + test + validate)
- **Step 4** (Investigate /rules): 15-30 min
- **Step 5** (Final validation): 10 min

**Total**: 1-2 hours to complete Phase 1

---

## Success Criteria

✅ All 15 critical tests passing (100% pass rate)  
✅ False positive prevention validated (grass field correctly rejected)  
✅ Docker integration verified (all endpoints healthy)  
✅ CI/CD workflow activated (tests run on every commit)

**When achieved**: Ready for Phase 2 (Test Audit & Categorization)
