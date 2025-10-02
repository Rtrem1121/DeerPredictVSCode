# 🧪 Testing Quick Reference Card

## Daily Commands

```powershell
# Before making changes
& "C:/Program Files/Python312/python.exe" -m pytest -m critical --tb=short

# After making changes  
& "C:/Program Files/Python312/python.exe" -m pytest -m critical --tb=short

# Quick unit tests (fast)
& "C:/Program Files/Python312/python.exe" -m pytest tests/unit -v

# Docker integration tests (slower, requires containers running)
docker compose up -d
& "C:/Program Files/Python312/python.exe" -m pytest tests/integration -v --tb=short
```

## What Tests Catch

| Test Name | What It Protects Against |
|-----------|-------------------------|
| `test_known_false_positive_location_rejection` | 94% confidence on grass fields (like August incident) |
| `test_hansen_canopy_vs_sentinel2_temporal_consistency` | 25-year-old Hansen data mismatches |
| `test_known_true_positive_location_validation` | Breaking working forest predictions |
| `test_backend_health_endpoint` | Docker backend crashes |
| `test_prediction_endpoint_available` | API endpoint failures |

## Test Status Dashboard

```
Current Status: 10/15 passing (67%)

Unit Tests:         [████████░░] 4/7   ⚠️  Need API signature fixes
Integration Tests:  [████████░░] 6/8   ✅  Docker healthy!
Critical Tests:     [███████░░░] 10/15 ⚠️  In progress

Target:             [██████████] 15/15 ✅  All passing
```

## Quick Fixes Needed

1. **3 Unit Tests** - API method signature updates
2. **1 Integration Test** - Add `date_time` to request payload  
3. **1 Production Bug** - `/rules` endpoint returns 500 error

## Why This Matters

**Before:** Made 19 changes → Everything broke → Complete rollback  
**After:** Tests catch issues immediately → Fix before deployment → No rollback

## Test Markers

- `@pytest.mark.critical` - Must pass before deployment
- `@pytest.mark.unit` - Fast, no external dependencies
- `@pytest.mark.integration` - Requires Docker containers
- `@pytest.mark.regression` - Prevents known bugs from returning

## Coverage Report

```powershell
# Generate HTML coverage report
& "C:/Program Files/Python312/python.exe" -m pytest --cov=backend --cov-report=html

# Open in browser
start htmlcov/index.html
```

## CI/CD Status

✅ GitHub Actions workflow configured (`.github/workflows/test.yml`)  
⏸️ Not yet activated (waiting for tests to reach 90%+ pass rate)  
🎯 Target: Auto-run on every push/PR

## Success Metrics

- **Tests Passing:** 67% → Target: 90%+
- **Code Coverage:** 0% → Target: 70%+
- **Docker Health:** 100% ✅
- **Deployment Confidence:** HIGH 🚀

## Next Action

Run this command to see current status:
```powershell
& "C:/Program Files/Python312/python.exe" -m pytest -m critical -v --tb=short
```

Then fix the 5 failing tests to reach 100% pass rate!

---

**Remember:** Every test that passes is one less bug in production! 🐛→✅
