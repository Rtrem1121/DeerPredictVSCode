#!/usr/bin/env python3
"""
Test Migration Script - Phase 2
Automatically migrates test files to organized structure
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class TestMigrator:
    def __init__(self, audit_report_path: str):
        with open(audit_report_path, 'r') as f:
            self.report = json.load(f)
        
        self.root = Path('.')
        self.migrations = []
        self.skipped = []
        self.errors = []
        
        # Define target structure
        self.structure = {
            'unit': self.root / 'tests' / 'unit',
            'integration': self.root / 'tests' / 'integration',
            'e2e': self.root / 'tests' / 'e2e',
            'fixtures': self.root / 'tests' / 'fixtures',
            'regression': self.root / 'tests' / 'regression',
            'archive': self.root / 'archive' / 'tests' / f'migration_{datetime.now().strftime("%Y%m%d")}'
        }
    
    def create_structure(self):
        """Create target directory structure"""
        print("📁 Creating target directory structure...")
        for name, path in self.structure.items():
            path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {path}")
        print()
    
    def determine_target(self, file_info: Dict) -> Path:
        """Determine where a file should be migrated"""
        # Skip already organized files
        if 'organized' in file_info['location_category']:
            return None
        
        # Skip archived files
        if file_info['location_category'] == 'archived':
            return None
        
        # Determine target based on category and type
        category = file_info['name_category']
        test_type = file_info['test_type']
        
        # Frontend E2E tests
        if category == 'frontend' and ('playwright' in file_info['name'].lower() or 
                                      'selenium' in file_info['name'].lower()):
            return self.structure['e2e']
        
        # Integration tests
        if test_type == 'integration' or category == 'integration':
            return self.structure['integration']
        
        # Bug fix tests → regression
        if category == 'bugfix':
            return self.structure['regression']
        
        # Unit tests
        if test_type == 'unit':
            return self.structure['unit']
        
        # Feature-specific tests → unit (assuming they test specific features)
        if category in ['bedding_zones', 'wind_thermal', 'camera_placement', 'gee_data', 'mature_buck']:
            return self.structure['unit']
        
        # Validation tests → integration
        if category == 'validation':
            return self.structure['integration']
        
        # Backend/API tests → integration
        if category == 'backend':
            return self.structure['integration']
        
        # Default: unit tests for unknown
        return self.structure['unit']
    
    def plan_migration(self) -> List[Dict]:
        """Plan file migrations"""
        print("📋 Planning migrations...")
        
        for file_info in self.report['files']:
            if 'error' in file_info:
                self.errors.append(file_info)
                continue
            
            target_dir = self.determine_target(file_info)
            
            if target_dir is None:
                self.skipped.append({
                    'file': file_info['relative_path'],
                    'reason': 'Already organized or archived'
                })
                continue
            
            source = Path(file_info['path'])
            target = target_dir / source.name
            
            # Handle name conflicts
            if target.exists():
                # Add suffix to avoid overwrite
                stem = target.stem
                suffix = target.suffix
                counter = 1
                while target.exists():
                    target = target_dir / f"{stem}_migrated{counter}{suffix}"
                    counter += 1
            
            self.migrations.append({
                'source': source,
                'target': target,
                'category': file_info['name_category'],
                'test_count': file_info['test_count'],
                'reason': f"{file_info['location_category']} → {target_dir.name}"
            })
        
        print(f"  📦 {len(self.migrations)} files to migrate")
        print(f"  ⏭️  {len(self.skipped)} files to skip")
        print(f"  ❌ {len(self.errors)} files with errors")
        print()
        
        return self.migrations
    
    def preview_migration(self):
        """Show migration preview"""
        print("=" * 70)
        print("🔍 MIGRATION PREVIEW")
        print("=" * 70)
        print()
        
        # Group by target directory
        by_target = {}
        for migration in self.migrations:
            target_dir = migration['target'].parent.name
            if target_dir not in by_target:
                by_target[target_dir] = []
            by_target[target_dir].append(migration)
        
        for target_dir, files in sorted(by_target.items()):
            print(f"📂 tests/{target_dir}/ ({len(files)} files)")
            for i, m in enumerate(files[:5], 1):
                print(f"   {i}. {m['source'].name}")
                print(f"      ({m['category']}, {m['test_count']} tests)")
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more")
            print()
    
    def execute_migration(self, dry_run=True):
        """Execute the migration"""
        if dry_run:
            print("🔍 DRY RUN MODE - No files will be moved")
            print()
        
        success = []
        failed = []
        
        for migration in self.migrations:
            try:
                if not dry_run:
                    # Copy file to new location
                    shutil.copy2(migration['source'], migration['target'])
                    
                    # Move original to archive
                    archive_path = self.structure['archive'] / migration['source'].name
                    shutil.move(str(migration['source']), str(archive_path))
                
                success.append(migration)
                if not dry_run:
                    print(f"  ✅ {migration['source'].name} → {migration['target'].parent.name}/")
            
            except Exception as e:
                failed.append({
                    'migration': migration,
                    'error': str(e)
                })
                print(f"  ❌ Failed: {migration['source'].name} - {e}")
        
        print()
        print("=" * 70)
        print("📊 MIGRATION SUMMARY")
        print("=" * 70)
        print(f"  ✅ Successful: {len(success)}")
        print(f"  ❌ Failed:     {len(failed)}")
        print(f"  ⏭️  Skipped:    {len(self.skipped)}")
        print()
        
        # Save migration log
        log = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'successful': [
                {'source': str(m['source']), 'target': str(m['target'])}
                for m in success
            ],
            'failed': failed,
            'skipped': self.skipped
        }
        
        log_file = f'migration_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(log_file, 'w') as f:
            json.dump(log, f, indent=2)
        
        print(f"💾 Migration log saved to: {log_file}")
        print()
        
        return len(success), len(failed)


def main():
    """Main migration execution"""
    print("🚀 Phase 2: Test Migration")
    print()
    
    # Load audit report
    audit_file = 'test_audit_report.json'
    if not Path(audit_file).exists():
        print(f"❌ Error: {audit_file} not found. Run audit_tests.py first.")
        return 1
    
    migrator = TestMigrator(audit_file)
    
    # Create structure
    migrator.create_structure()
    
    # Plan migration
    migrations = migrator.plan_migration()
    
    if not migrations:
        print("✅ No files need migration!")
        return 0
    
    # Preview
    migrator.preview_migration()
    
    # Ask for confirmation
    print("=" * 70)
    print("⚠️  IMPORTANT: This will migrate test files!")
    print("=" * 70)
    print()
    print("Options:")
    print("  1. DRY RUN  - Preview without making changes")
    print("  2. EXECUTE  - Perform actual migration")
    print("  3. CANCEL   - Exit without changes")
    print()
    
    choice = input("Choose [1/2/3]: ").strip()
    
    if choice == '1':
        print()
        print("🔍 Running DRY RUN...")
        print()
        migrator.execute_migration(dry_run=True)
        print("✅ Dry run complete. No files were modified.")
    
    elif choice == '2':
        print()
        confirm = input("⚠️  Are you sure? Type 'YES' to confirm: ").strip()
        if confirm == 'YES':
            print()
            print("🚀 Executing migration...")
            print()
            success, failed = migrator.execute_migration(dry_run=False)
            
            if failed == 0:
                print("✅ Migration completed successfully!")
                print()
                print("📝 Next steps:")
                print("  1. Run pytest to verify all tests still work")
                print("  2. Update imports if needed")
                print("  3. Commit the changes")
            else:
                print(f"⚠️  Migration completed with {failed} errors")
                print("  Check migration log for details")
        else:
            print("❌ Migration cancelled")
    
    else:
        print("❌ Migration cancelled")
    
    return 0


if __name__ == '__main__':
    exit(main())
