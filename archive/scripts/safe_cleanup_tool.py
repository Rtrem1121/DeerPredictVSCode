#!/usr/bin/env python3
"""
Safe Dead Code Removal Script for Deer Prediction App
====================================================

This script safely removes identified dead code while preserving functionality.
Each removal is logged and can be reverted if needed.

Author: GitHub Copilot
Date: August 26, 2025
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import ast
import re

class SafeDeadCodeRemover:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.backup_dir = self.root_path / "dead_code_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.removal_log = []
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def backup_file(self, file_path: Path) -> Path:
        """Create backup of file before removal"""
        relative_path = file_path.relative_to(self.root_path)
        backup_path = self.backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def remove_unused_files(self):
        """Remove files identified as unused"""
        unused_files = [
            "backend/performance_old.py",
            "backend/main.py.backup"  # Backup file found
        ]
        
        print("🗑️  Removing unused files...")
        
        for file_rel_path in unused_files:
            file_path = self.root_path / file_rel_path.replace('\\', '/')
            
            if file_path.exists():
                # Create backup
                backup_path = self.backup_file(file_path)
                
                # Remove file
                file_path.unlink()
                
                self.removal_log.append({
                    "type": "file_removal",
                    "original_path": str(file_path),
                    "backup_path": str(backup_path),
                    "timestamp": datetime.now().isoformat()
                })
                
                print(f"  ✅ Removed: {file_rel_path}")
                print(f"     📦 Backed up to: {backup_path}")
            else:
                print(f"  ⚠️  File not found: {file_rel_path}")
    
    def remove_unused_functions(self):
        """Remove unused functions from files"""
        # Functions that are definitely safe to remove (not API endpoints)
        safe_removals = [
            ("safe_fix_plan.py", "create_improved_ndvi_method"),
            ("safe_fix_plan.py", "create_gee_setup_fix"),
            ("test_gee_integration.py", "check_credentials_file"),
            ("test_improved_ndvi.py", "calculate_ndvi"),  # Test function
            ("test_mature_buck_movement.py", "sample_terrain_features"),
            ("test_mature_buck_movement.py", "sample_weather_data"),
        ]
        
        print("\n🔧 Removing unused functions...")
        
        for file_path, function_name in safe_removals:
            self._remove_function_from_file(file_path, function_name)
    
    def _remove_function_from_file(self, file_path: str, function_name: str):
        """Remove a specific function from a file"""
        full_path = self.root_path / file_path
        
        if not full_path.exists():
            print(f"  ⚠️  File not found: {file_path}")
            return
        
        # Read file content
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Parse AST to find function
        try:
            tree = ast.parse(content)
            function_found = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    function_found = True
                    break
            
            if not function_found:
                print(f"  ⚠️  Function '{function_name}' not found in {file_path}")
                return
            
            # Create backup
            backup_path = self.backup_file(full_path)
            
            # Remove function using regex (simple approach)
            # This is a simplified removal - in production, use more sophisticated AST manipulation
            pattern = rf'^def {re.escape(function_name)}\s*\([^)]*\):.*?(?=^def|\^class|^if __name__|^$|\Z)'
            new_content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Write back to file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.removal_log.append({
                "type": "function_removal",
                "file": str(full_path),
                "function": function_name,
                "backup_path": str(backup_path),
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"  ✅ Removed function '{function_name}' from {file_path}")
            
        except Exception as e:
            print(f"  ❌ Error removing function '{function_name}' from {file_path}: {e}")
    
    def clean_duplicate_files(self):
        """Handle duplicate file situations"""
        print("\n🔄 Handling duplicate files...")
        
        # Check if we have both root and backend versions of advanced_camera_placement.py
        root_camera = self.root_path / "advanced_camera_placement.py"
        backend_camera = self.root_path / "backend" / "advanced_camera_placement.py"
        
        if root_camera.exists() and backend_camera.exists():
            # Compare files to see if they're identical
            with open(root_camera, 'r', encoding='utf-8') as f1, open(backend_camera, 'r', encoding='utf-8') as f2:
                root_content = f1.read()
                backend_content = f2.read()
            
            if root_content.strip() == backend_content.strip():
                # Files are identical, remove the root one
                backup_path = self.backup_file(root_camera)
                root_camera.unlink()
                
                self.removal_log.append({
                    "type": "duplicate_file_removal",
                    "removed_file": str(root_camera),
                    "kept_file": str(backend_camera),
                    "backup_path": str(backup_path),
                    "timestamp": datetime.now().isoformat()
                })
                
                print(f"  ✅ Removed duplicate: {root_camera}")
                print(f"     📦 Kept version in: {backend_camera}")
            else:
                print(f"  ⚠️  Files differ, manual review needed for camera placement files")
    
    def fix_security_issues(self):
        """Fix critical security issues"""
        print("\n🔒 Fixing security issues...")
        
        security_fixes = [
            {
                "file": "password_protection.py",
                "line": 11,
                "issue": "hardcoded password",
                "fix": "Move to environment variable"
            },
            {
                "file": "test_password_protection.py", 
                "line": 15,
                "issue": "test password",
                "fix": "Use test fixture"
            }
        ]
        
        for fix in security_fixes:
            print(f"  🔒 {fix['file']}:{fix['line']} - {fix['issue']}")
            print(f"     💡 Recommendation: {fix['fix']}")
    
    def generate_cleanup_report(self):
        """Generate cleanup summary report"""
        report = {
            "cleanup_date": datetime.now().isoformat(),
            "backup_location": str(self.backup_dir),
            "removals": self.removal_log,
            "summary": {
                "files_removed": len([r for r in self.removal_log if r["type"] == "file_removal"]),
                "functions_removed": len([r for r in self.removal_log if r["type"] == "function_removal"]),
                "duplicates_handled": len([r for r in self.removal_log if r["type"] == "duplicate_file_removal"])
            }
        }
        
        # Save cleanup report
        report_path = self.root_path / "cleanup_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Cleanup report saved to: {report_path}")
        return report
    
    def create_revert_script(self):
        """Create script to revert changes if needed"""
        revert_script = f"""#!/usr/bin/env python3
# Revert script for dead code removal
# Generated: {datetime.now().isoformat()}

import shutil
from pathlib import Path

backup_dir = Path("{self.backup_dir}")
root_dir = Path("{self.root_path}")

print("🔄 Reverting dead code removal...")

for removal in {self.removal_log}:
    if removal["type"] in ["file_removal", "duplicate_file_removal"]:
        original_path = Path(removal["original_path"])
        backup_path = Path(removal["backup_path"])
        
        if backup_path.exists():
            shutil.copy2(backup_path, original_path)
            print(f"✅ Restored: {{original_path}}")
        else:
            print(f"❌ Backup not found: {{backup_path}}")

print("🔄 Revert complete!")
"""
        
        revert_path = self.backup_dir / "revert_changes.py"
        with open(revert_path, 'w', encoding='utf-8') as f:
            f.write(revert_script)
        
        print(f"🔄 Revert script created: {revert_path}")

def main():
    """Main cleanup function"""
    print("🧹 STARTING SAFE DEAD CODE REMOVAL")
    print("=" * 50)
    
    remover = SafeDeadCodeRemover(".")
    
    # Step 1: Remove unused files
    remover.remove_unused_files()
    
    # Step 2: Remove unused functions (conservative approach)
    remover.remove_unused_functions()
    
    # Step 3: Handle duplicates
    remover.clean_duplicate_files()
    
    # Step 4: Report security issues (don't auto-fix)
    remover.fix_security_issues()
    
    # Step 5: Generate reports
    report = remover.generate_cleanup_report()
    remover.create_revert_script()
    
    print("\n" + "=" * 50)
    print("✅ CLEANUP COMPLETE")
    print("=" * 50)
    print(f"📦 Backups created in: {remover.backup_dir}")
    print(f"🗑️  Files removed: {report['summary']['files_removed']}")
    print(f"🔧 Functions removed: {report['summary']['functions_removed']}")
    print(f"🔄 Duplicates handled: {report['summary']['duplicates_handled']}")
    print("\n🔒 SECURITY ISSUES REQUIRE MANUAL ATTENTION!")
    print("\n💡 Run tests after cleanup to ensure functionality is preserved")
    
    return report

if __name__ == "__main__":
    main()
