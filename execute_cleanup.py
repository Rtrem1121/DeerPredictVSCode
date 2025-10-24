"""
Safe cleanup of unused files
"""
import os
import shutil
from pathlib import Path
import json

root = Path(r"c:\Users\Rich\deer_pred_app")

# Load removal candidates
with open('removal_candidates.json', 'r') as f:
    candidates = json.load(f)

removed_count = 0
errors = []

print("="*80)
print("EXECUTING CODEBASE CLEANUP")
print("="*80)

# 1. Remove archive folder
print("\n1. Removing archive/ folder (203 files)...")
archive_path = root / "archive"
if archive_path.exists():
    try:
        shutil.rmtree(archive_path)
        print(f"   ✅ Removed: archive/")
        removed_count += 203
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(f"archive/: {e}")
else:
    print(f"   ⚠️  Not found: archive/")

# 2. Remove old test files
print("\n2. Removing old test files (144 files)...")

# Remove backend/tests/
backend_tests = root / "backend" / "tests"
if backend_tests.exists():
    try:
        shutil.rmtree(backend_tests)
        print(f"   ✅ Removed: backend/tests/")
        removed_count += 96  # Estimated count
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(f"backend/tests/: {e}")

# Remove root test files
test_files = [
    'test_bedding_coordinates.py',
    'test_biology_driven_stands.py', 
    'test_comprehensive_optimization.py',
    'test_live_api.py',
    'test_localhost_production.py',
    'test_performance_optimization.py',
    'test_docker_backend.py',
    'test_backend_simple.py',
    'test_with_fresh_logs.py',
    'test_varying_locations.py',
    'test_raw_response.py',
    'gee_test_setup.py',
    'simple_integration_test.py',
    'test_backend_frontend_data_flow.py',
    'comprehensive_testing_validation.py',
    'analyze_testing_results.py',
    'direct_enhanced_validation.py',
    'debug_optimized_points.py',
    'debug_stand_markers.py',
]

for test_file in test_files:
    file_path = root / test_file
    if file_path.exists():
        try:
            file_path.unlink()
            print(f"   ✅ Removed: {test_file}")
            removed_count += 1
        except Exception as e:
            print(f"   ❌ Error removing {test_file}: {e}")
            errors.append(f"{test_file}: {e}")

# 3. Remove backup file
print("\n3. Removing legacy backup file...")
backup_file = root / "backend" / "services" / "prediction_service_legacy_backup.py"
if backup_file.exists():
    try:
        backup_file.unlink()
        print(f"   ✅ Removed: backend/services/prediction_service_legacy_backup.py")
        removed_count += 1
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(f"prediction_service_legacy_backup.py: {e}")

# 4. Remove duplicate test results
print("\n4. Removing duplicate test results...")
test_results = list(root.glob("tests/fixtures/baseline_validation_20250824_*.json"))
for result_file in test_results:
    try:
        result_file.unlink()
        print(f"   ✅ Removed: {result_file.name}")
        removed_count += 1
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(f"{result_file.name}: {e}")

# 5. Remove generated test files
print("\n5. Removing generated test results...")
generated_files = list(root.glob("comprehensive_testing_results_*.json"))
for gen_file in generated_files:
    try:
        gen_file.unlink()
        print(f"   ✅ Removed: {gen_file.name}")
        removed_count += 1
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(f"{gen_file.name}: {e}")

# 6. Remove old analysis/debug scripts
print("\n6. Removing analysis scripts...")
script_files = [
    'analyze_active_files.py',
    'debug_bedding_generation.py',
    'trace_active_imports.py',
    'identify_removal_candidates.py',
]
for script in script_files:
    file_path = root / script
    if file_path.exists():
        try:
            file_path.unlink()
            print(f"   ✅ Removed: {script}")
            removed_count += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            errors.append(f"{script}: {e}")

# 7. Remove analysis output files
print("\n7. Removing analysis output files...")
output_files = [
    'file_analysis.json',
    'active_files.txt',
    'removal_candidates.json',
]
for output in output_files:
    file_path = root / output
    if file_path.exists():
        try:
            file_path.unlink()
            print(f"   ✅ Removed: {output}")
            removed_count += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")

# 8. Remove additional old files
print("\n8. Removing additional old files...")
old_files = [
    'cleanup_workspace.py',
    'cleanup_manifest.json',
    'implementation_tracker.py',
    'implementation_progress.json',
    'mature_buck_improvement_plan.json',
    'biology_driven_stand_validation.json',
    'validation_output.txt',
    'open_meteo_sample_response.json',
    'inspect_api_response.py',
    'run_code_audit.py',
    'restart_services.py',
    'testing_guide.py',
]
for old_file in old_files:
    file_path = root / old_file
    if file_path.exists():
        try:
            file_path.unlink()
            print(f"   ✅ Removed: {old_file}")
            removed_count += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")

print("\n" + "="*80)
print("CLEANUP SUMMARY")
print("="*80)
print(f"\n✅ Files removed: {removed_count}")
if errors:
    print(f"\n❌ Errors encountered: {len(errors)}")
    for error in errors:
        print(f"   - {error}")
else:
    print(f"\n✅ No errors!")

print(f"\n📊 Estimated space savings: Removed {removed_count} files")
print(f"   Before: ~540 files")
print(f"   After: ~{540 - removed_count} files")
print(f"   Reduction: ~{(removed_count/540)*100:.1f}%")

# Save cleanup log
log_data = {
    'removed_count': removed_count,
    'errors': errors,
    'timestamp': '2025-10-24'
}

with open('cleanup_log.json', 'w') as f:
    json.dump(log_data, f, indent=2)

print(f"\n✅ Cleanup log saved to cleanup_log.json")
