#!/usr/bin/env python3
# Revert script for dead code removal
# Generated: 2025-08-26T07:54:37.088785

import shutil
from pathlib import Path

backup_dir = Path("dead_code_backups\20250826_075437")
root_dir = Path(".")

print("🔄 Reverting dead code removal...")

for removal in [{'type': 'file_removal', 'original_path': 'backend\\performance_old.py', 'backup_path': 'dead_code_backups\\20250826_075437\\backend\\performance_old.py', 'timestamp': '2025-08-26T07:54:37.053919'}, {'type': 'file_removal', 'original_path': 'backend\\main.py.backup', 'backup_path': 'dead_code_backups\\20250826_075437\\backend\\main.py.backup', 'timestamp': '2025-08-26T07:54:37.054448'}, {'type': 'function_removal', 'file': 'safe_fix_plan.py', 'function': 'create_improved_ndvi_method', 'backup_path': 'dead_code_backups\\20250826_075437\\safe_fix_plan.py', 'timestamp': '2025-08-26T07:54:37.055961'}, {'type': 'function_removal', 'file': 'safe_fix_plan.py', 'function': 'create_gee_setup_fix', 'backup_path': 'dead_code_backups\\20250826_075437\\safe_fix_plan.py', 'timestamp': '2025-08-26T07:54:37.065047'}, {'type': 'function_removal', 'file': 'test_gee_integration.py', 'function': 'check_credentials_file', 'backup_path': 'dead_code_backups\\20250826_075437\\test_gee_integration.py', 'timestamp': '2025-08-26T07:54:37.067048'}, {'type': 'function_removal', 'file': 'test_improved_ndvi.py', 'function': 'calculate_ndvi', 'backup_path': 'dead_code_backups\\20250826_075437\\test_improved_ndvi.py', 'timestamp': '2025-08-26T07:54:37.075733'}, {'type': 'function_removal', 'file': 'test_mature_buck_movement.py', 'function': 'sample_terrain_features', 'backup_path': 'dead_code_backups\\20250826_075437\\test_mature_buck_movement.py', 'timestamp': '2025-08-26T07:54:37.077274'}, {'type': 'function_removal', 'file': 'test_mature_buck_movement.py', 'function': 'sample_weather_data', 'backup_path': 'dead_code_backups\\20250826_075437\\test_mature_buck_movement.py', 'timestamp': '2025-08-26T07:54:37.086781'}, {'type': 'duplicate_file_removal', 'removed_file': 'advanced_camera_placement.py', 'kept_file': 'backend\\advanced_camera_placement.py', 'backup_path': 'dead_code_backups\\20250826_075437\\advanced_camera_placement.py', 'timestamp': '2025-08-26T07:54:37.087783'}]:
    if removal["type"] in ["file_removal", "duplicate_file_removal"]:
        original_path = Path(removal["original_path"])
        backup_path = Path(removal["backup_path"])
        
        if backup_path.exists():
            shutil.copy2(backup_path, original_path)
            print(f"✅ Restored: {original_path}")
        else:
            print(f"❌ Backup not found: {backup_path}")

print("🔄 Revert complete!")
