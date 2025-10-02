#!/usr/bin/env python3
"""
Import Fix Script - Phase 3
Automatically fixes import errors in migrated test files
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

class ImportFixer:
    def __init__(self):
        self.root = Path('.')
        self.fixes_applied = []
        self.errors = []
        
        # Define import mapping rules
        self.import_mappings = {
            # Old module → New module path
            'from mature_buck_predictor import': 'from backend.mature_buck_predictor import',
            'import mature_buck_predictor': 'import backend.mature_buck_predictor as mature_buck_predictor',
            'from scoring_engine import': 'from backend.scoring_engine import',
            'import scoring_engine': 'import backend.scoring_engine as scoring_engine',
            'from terrain_analyzer import': 'from backend.terrain_analyzer import',
            'import terrain_analyzer': 'import backend.terrain_analyzer as terrain_analyzer',
            'from config_manager import': 'from backend.config_manager import',
            'import config_manager': 'import backend.config_manager as config_manager',
            'from prediction_analyzer import': 'from backend.analysis.prediction_analyzer import',
            'import prediction_analyzer': 'import backend.analysis.prediction_analyzer as prediction_analyzer',
            'from analytics import': 'from backend.analytics import',
            'import analytics': 'import backend.analytics as analytics',
        }
    
    def fix_file(self, file_path: Path) -> bool:
        """Fix imports in a single file"""
        try:
            # Read file
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # Track changes
            changes_made = []
            
            # Apply each import mapping
            for old_import, new_import in self.import_mappings.items():
                if old_import in content:
                    # Count occurrences
                    count = content.count(old_import)
                    
                    # Replace
                    content = content.replace(old_import, new_import)
                    
                    changes_made.append(f"{old_import} → {new_import} ({count}x)")
            
            # Write back if changes made
            if changes_made:
                file_path.write_text(content, encoding='utf-8')
                
                self.fixes_applied.append({
                    'file': str(file_path),
                    'changes': changes_made
                })
                
                return True
            
            return False
        
        except Exception as e:
            self.errors.append({
                'file': str(file_path),
                'error': str(e)
            })
            return False
    
    def fix_all_tests(self) -> Tuple[int, int]:
        """Fix imports in all test files"""
        print("🔧 Fixing import statements in test files...")
        print()
        
        # Find all test files with import errors
        test_files = [
            self.root / 'tests' / 'integration' / 'test_analytics_integration.py',
            self.root / 'tests' / 'unit' / 'test_locations.py',
            self.root / 'tests' / 'unit' / 'test_mature_buck_accuracy.py',
            self.root / 'tests' / 'unit' / 'test_step_1_1_analyzer.py',
            self.root / 'tests' / 'unit' / 'test_step_1_2_service.py',
            self.root / 'tests' / 'unit' / 'test_step_2_1_endpoint.py',
            self.root / 'tests' / 'unit' / 'test_step_2_1_simple.py',
            self.root / 'tests' / 'test_frontend_validation.py',
        ]
        
        fixed_count = 0
        skipped_count = 0
        
        for file_path in test_files:
            if not file_path.exists():
                print(f"  ⏭️  {file_path.name} - Not found")
                skipped_count += 1
                continue
            
            if self.fix_file(file_path):
                print(f"  ✅ {file_path.name} - Fixed")
                fixed_count += 1
            else:
                print(f"  ⏭️  {file_path.name} - No changes needed")
                skipped_count += 1
        
        print()
        return fixed_count, skipped_count
    
    def generate_report(self):
        """Generate fix report"""
        print("=" * 70)
        print("📊 IMPORT FIX REPORT")
        print("=" * 70)
        print()
        
        print(f"✅ Files Fixed: {len(self.fixes_applied)}")
        print(f"❌ Errors: {len(self.errors)}")
        print()
        
        if self.fixes_applied:
            print("📝 Changes Applied:")
            print()
            for fix in self.fixes_applied:
                print(f"  📄 {Path(fix['file']).name}")
                for change in fix['changes']:
                    print(f"     • {change}")
                print()
        
        if self.errors:
            print("❌ Errors Encountered:")
            print()
            for error in self.errors:
                print(f"  📄 {Path(error['file']).name}")
                print(f"     • {error['error']}")
                print()


def main():
    """Main execution"""
    print("🚀 Phase 3: Import Fix Tool")
    print()
    
    fixer = ImportFixer()
    
    # Fix all test files
    fixed, skipped = fixer.fix_all_tests()
    
    # Generate report
    fixer.generate_report()
    
    # Summary
    print("=" * 70)
    print("✅ IMPORT FIX COMPLETE")
    print("=" * 70)
    print(f"  Fixed:   {fixed} files")
    print(f"  Skipped: {skipped} files")
    print(f"  Errors:  {len(fixer.errors)} files")
    print()
    
    if fixed > 0:
        print("📝 Next Steps:")
        print("  1. Run pytest --collect-only to verify")
        print("  2. Run pytest tests/ to validate fixes")
        print("  3. Proceed with deduplication")
    
    return 0 if len(fixer.errors) == 0 else 1


if __name__ == '__main__':
    exit(main())
