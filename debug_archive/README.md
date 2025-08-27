# Debug Archive

This directory contains archived debug and validation scripts that were consolidated on 2025-08-25.

## Archived Scripts

### Debug Scripts
These scripts were used for specific debugging tasks and have been replaced by `debug_tool.py`:
- debug_enhanced_accuracy_direct.py
- debug_observations.py
- debug_gpx_import.py
- debug_feeding_scores.py
- debug_gee_isolation.py
- debug_terrain_features.py
- debug_vermont_terrain.py
- debug_bedding_scores.py
- debug_terrain_scores.py
- debug_mature_buck.py
- debug_comprehensive_flow.py

### Validation Scripts  
These scripts were used for validation testing. Results are documented in `docs/TESTING.md`:
- FINAL_VALIDATION_REPORT.py
- final_config_validation.py
- quick_validation.py
- backend_analysis_report.py
- final_testing_report.py

## Current Debug Tools

Use these instead of archived scripts:

### Main Debug Tool
```bash
# Run comprehensive test
python debug_tool.py

# Test specific components
python debug_tool.py health
python debug_tool.py prediction 44.26 -72.58
python debug_tool.py camera 44.26 -72.58
python debug_tool.py buck 44.26 -72.58
```

### Essential Debug Scripts (Still Active)
- debug_api_endpoints.py: Essential for API debugging
- debug_integration.py: Core integration testing
- comprehensive_system_test.py: Main system validation
- comprehensive_testing_suite.py: Core testing framework

## Restoration

If you need to restore any archived script:
```bash
cp debug_archive/script_name.py ./
```
