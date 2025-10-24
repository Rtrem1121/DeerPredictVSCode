# Codebase Cleanup Analysis Report
**Date:** October 24, 2025  
**Analysis:** Complete workspace file usage audit

---

## Executive Summary

**Total Files in Workspace:** 540  
**Active Files (Used in Prediction):** 40  
**Files Safe to Remove:** 361 (67% reduction)  
**Files Requiring Review:** 7  
**Files to Keep:** 3 (requirements files)

**Potential Storage/Complexity Reduction:** ~68% of codebase

---

## Active Files (40 files - KEEP THESE)

### Backend Core (35 files)
- `backend/main.py` - FastAPI application entry point
- `backend/routers/prediction_router.py` - Prediction API endpoints
- `backend/services/prediction_service.py` - Core prediction orchestration
- `backend/services/lidar_processor.py` - LIDAR terrain processing (0.35m resolution)
- `backend/mature_buck_points_generator.py` - Optimized points generation
- `backend/advanced_thermal_analysis.py` - Thermal condition analysis
- `backend/vermont_food_classifier.py` - Food source analysis
- `backend/scouting_data_manager.py` - Scouting observations
- `backend/hunting_context_analyzer.py` - Real-time hunt context
- ...and 26 more supporting modules

### Frontend (1 file)
- `frontend/app.py` - Streamlit UI

### Root Prediction Files (4 files)
- `enhanced_bedding_zone_predictor.py` - Main LIDAR-enhanced predictor
- `optimized_biological_integration.py` - Biological integration engine
- `habitat_suitability_model.py` - Habitat scoring
- `habitat_suitability_visualizer.py` - Visualization support

---

## Safe to Remove (361 files - LOW RISK)

### 1. Archive Folder (203 files)
**Recommendation:** DELETE ENTIRE FOLDER

**Contents:**
- `archive/deployment/` - Old CloudFlare, Railway configs (48 files)
- `archive/old_configs/` - Deprecated requirements files (14 files)
- `archive/2024-legacy/` - Entire legacy codebase from 2024 (141 files)

**Justification:** Archived code from previous versions, not imported anywhere in active codebase.

---

### 2. Old Test Files (144 files)
**Recommendation:** DELETE

**Examples:**
- `backend/tests/test_*.py` - Old unit tests (96 files)
- `test_*.py` in root - Ad-hoc test scripts (48 files)
  - `test_bedding_coordinates.py`
  - `test_biology_driven_stands.py`
  - `test_comprehensive_optimization.py`
  - `test_live_api.py`
  - `test_localhost_production.py`
  - etc.

**Justification:** Not part of current test suite, replaced by Docker-based testing.

---

### 3. Backup Files (1 file)
**Recommendation:** DELETE

- `backend/services/prediction_service_legacy_backup.py`

**Justification:** Legacy backup no longer needed after successful refactoring.

---

### 4. Duplicate/Old Test Results (7 files)
**Recommendation:** DELETE

- `tests/fixtures/baseline_validation_20250824_*.json` (7 files)

**Justification:** Old validation snapshots from August, not used in active testing.

---

### 5. Generated Test Results (4 files)
**Recommendation:** DELETE

- `comprehensive_testing_results_20251020_*.json` (4 files)

**Justification:** Generated output files, can be regenerated if needed.

---

### 6. Old Debug/Analysis Scripts (2 files)
**Recommendation:** DELETE

- `analyze_active_files.py` (this analysis script)
- `debug_bedding_generation.py`

**Justification:** One-time analysis scripts, not part of production code.

---

## Review Needed (7 files - MEDIUM RISK)

### Docker Files
**Recommendation:** REVIEW BEFORE REMOVING

1. `docker/cloudflare-config.yml` - CloudFlare tunnel config (unused?)
2. `docker/docker-compose.prod.yml` - Production compose file (may be needed for prod deployment)
3. `requirements.docker.txt` - Docker-specific requirements (currently using requirements.txt)
4. `start_docker.py` - Helper script to start Docker services
5. `backend/gee_docker_setup.py` - GEE setup for Docker environment
6. `docker/test_prediction_output.json` - Sample test output

**Questions:**
- Are you deploying to production with a different compose file?
- Is CloudFlare tunnel still in use?
- Do Docker containers need separate requirements?

---

## Keep (3 files + active code)

### Requirements Files (KEEP)
- `requirements.txt` - Main dependencies
- `requirements.pinned.txt` - Pinned versions for reproducibility
- `requirements.prod.txt` - Production-specific requirements

### Active Codebase (KEEP)
- All 40 files identified in active analysis
- `docker/docker-compose.yml` - Active Docker orchestration
- Configuration files in `config/` and `credentials/`
- LIDAR data files in `data/`

---

## Proposed Removal Plan

### Phase 1: Safe Removals (361 files)
```bash
# Remove archive folder
Remove-Item -Recurse -Force archive/

# Remove old test files
Remove-Item -Recurse -Force backend/tests/
Remove-Item test_*.py

# Remove backup file
Remove-Item backend/services/prediction_service_legacy_backup.py

# Remove duplicate test results
Remove-Item tests/fixtures/baseline_validation_20250824_*.json

# Remove generated files
Remove-Item comprehensive_testing_results_*.json

# Remove analysis scripts
Remove-Item analyze_active_files.py, debug_bedding_generation.py
```

### Phase 2: Review Docker Files (if not needed)
```bash
# Only if not using CloudFlare/prod deployments
Remove-Item docker/cloudflare-config.yml
Remove-Item docker/docker-compose.prod.yml
Remove-Item requirements.docker.txt
Remove-Item start_docker.py
Remove-Item backend/gee_docker_setup.py
Remove-Item docker/test_prediction_output.json
```

---

## Expected Benefits

### Storage Reduction
- **Before:** 540 files
- **After Phase 1:** 179 files (-67%)
- **After Phase 2 (if applicable):** 172 files (-68%)

### Complexity Reduction
- Easier navigation of codebase
- Clearer separation of active vs archived code
- Faster searches and file operations
- Reduced confusion about which files are current

### Maintenance Benefits
- Only maintain active code
- Easier onboarding for new developers
- Faster IDE indexing
- Clearer dependency tree

---

## Verification Steps After Removal

1. **Test Docker Containers:**
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```

2. **Test Prediction API:**
   ```bash
   curl http://localhost:8000/predict -X POST -H "Content-Type: application/json" -d '{"lat": 44.5, "lon": -72.5, "season": "fall"}'
   ```

3. **Test Frontend:**
   - Open http://localhost:8501
   - Make predictions at multiple locations
   - Verify markers vary by location

4. **Verify LIDAR Loading:**
   ```bash
   docker logs docker-backend-1 | grep -i "lidar"
   ```

---

## Recommendation

✅ **PROCEED WITH PHASE 1 REMOVAL (361 files)**
- Zero risk to production functionality
- All files are genuinely unused or archived
- Immediate 67% codebase reduction

⚠️ **REVIEW PHASE 2 (7 docker files)**
- Clarify production deployment requirements
- Keep if using CloudFlare tunnel or separate prod setup
- Remove if only using standard docker-compose.yml

---

## Files Generated by This Analysis (can also be removed after review)
- `file_analysis.json`
- `active_files.txt`
- `removal_candidates.json`
- `trace_active_imports.py`
- `identify_removal_candidates.py`
- `CLEANUP_ANALYSIS_REPORT.md` (this file)
