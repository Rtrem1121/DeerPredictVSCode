#!/usr/bin/env python3
"""
Test Audit Script - Phase 2
Analyzes all test files in the workspace to categorize, identify duplicates, and plan migration
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
import re

class TestAuditor:
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.tests = []
        self.categories = defaultdict(list)
        self.duplicates = defaultdict(list)
        self.stats = {
            'total_files': 0,
            'total_tests': 0,
            'by_location': defaultdict(int),
            'by_category': defaultdict(int),
            'by_type': defaultdict(int)
        }
        
    def find_test_files(self) -> List[Path]:
        """Find all test files in workspace"""
        test_files = []
        
        # Find test_*.py files
        for pattern in ['test_*.py', '*_test.py']:
            test_files.extend(self.root.rglob(pattern))
        
        # Exclude virtual environments and cache
        excluded = ['venv', '.venv', 'env', '__pycache__', '.pytest_cache', 'node_modules']
        test_files = [
            f for f in test_files 
            if not any(ex in str(f) for ex in excluded)
        ]
        
        return sorted(set(test_files))
    
    def categorize_by_location(self, file_path: Path) -> str:
        """Categorize test by directory location"""
        rel_path = file_path.relative_to(self.root)
        parts = rel_path.parts
        
        if 'tests' in parts:
            if 'unit' in parts:
                return 'organized_unit'
            elif 'integration' in parts:
                return 'organized_integration'
            elif 'e2e' in parts:
                return 'organized_e2e'
            elif 'fixtures' in parts:
                return 'organized_fixtures'
            else:
                return 'organized_other'
        elif 'backend' in parts:
            if len(parts) > 2 and parts[1] == 'tests':
                return 'backend_organized'
            else:
                return 'backend_scattered'
        elif 'dead_code_backups' in parts:
            return 'archived'
        else:
            return 'root_scattered'
    
    def categorize_by_name(self, file_name: str) -> str:
        """Categorize test by filename pattern"""
        name_lower = file_name.lower()
        
        # Frontend tests
        if 'frontend' in name_lower or 'ui' in name_lower or 'playwright' in name_lower:
            return 'frontend'
        
        # Backend/API tests
        if 'backend' in name_lower or 'api' in name_lower or 'endpoint' in name_lower:
            return 'backend'
        
        # Integration tests
        if 'integration' in name_lower or 'e2e' in name_lower or 'docker' in name_lower:
            return 'integration'
        
        # Specific feature tests
        if 'bedding' in name_lower:
            return 'bedding_zones'
        if 'wind' in name_lower or 'thermal' in name_lower or 'weather' in name_lower:
            return 'wind_thermal'
        if 'camera' in name_lower:
            return 'camera_placement'
        if 'gee' in name_lower or 'satellite' in name_lower:
            return 'gee_data'
        if 'scouting' in name_lower:
            return 'scouting'
        if 'mature_buck' in name_lower or 'buck' in name_lower:
            return 'mature_buck'
        
        # Bug fix tests
        if 'fix' in name_lower or 'bug' in name_lower:
            return 'bugfix'
        
        # Validation tests
        if 'validation' in name_lower or 'accuracy' in name_lower:
            return 'validation'
        
        return 'other'
    
    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze a single test file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to count tests
            try:
                tree = ast.parse(content)
                test_functions = [
                    node.name for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')
                ]
                test_classes = [
                    node.name for node in ast.walk(tree)
                    if isinstance(node, ast.ClassDef) and node.name.startswith('Test')
                ]
            except SyntaxError:
                test_functions = []
                test_classes = []
                # Fallback: regex count
                test_functions = re.findall(r'def (test_\w+)\(', content)
                test_classes = re.findall(r'class (Test\w+)', content)
            
            # Extract imports to understand dependencies
            imports = re.findall(r'^(?:from|import)\s+(\S+)', content, re.MULTILINE)
            
            # Check if it uses pytest
            uses_pytest = 'pytest' in content or '@pytest' in content
            
            # Check if it has fixtures
            has_fixtures = '@pytest.fixture' in content or 'conftest' in str(file_path)
            
            # Detect test type
            if 'docker' in content.lower() or 'container' in content.lower():
                test_type = 'integration'
            elif 'playwright' in content.lower() or 'selenium' in content.lower():
                test_type = 'e2e'
            elif 'mock' in content.lower() or len(test_classes) > 0:
                test_type = 'unit'
            else:
                test_type = 'unknown'
            
            return {
                'path': str(file_path),
                'relative_path': str(file_path.relative_to(self.root)),
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'lines': len(content.splitlines()),
                'test_functions': test_functions,
                'test_classes': test_classes,
                'test_count': len(test_functions) + len(test_classes),
                'imports': imports[:10],  # First 10 imports
                'uses_pytest': uses_pytest,
                'has_fixtures': has_fixtures,
                'test_type': test_type,
                'location_category': self.categorize_by_location(file_path),
                'name_category': self.categorize_by_name(file_path.name)
            }
        except Exception as e:
            return {
                'path': str(file_path),
                'error': str(e)
            }
    
    def find_duplicates(self):
        """Identify potential duplicate tests"""
        test_names = defaultdict(list)
        
        for test in self.tests:
            if 'test_functions' in test:
                for func in test['test_functions']:
                    test_names[func].append(test['relative_path'])
        
        # Find functions that appear in multiple files
        for name, files in test_names.items():
            if len(files) > 1:
                self.duplicates[name] = files
    
    def run_audit(self) -> Dict:
        """Run complete audit"""
        print("🔍 Phase 2: Test Audit Starting...")
        print()
        
        # Find all test files
        test_files = self.find_test_files()
        self.stats['total_files'] = len(test_files)
        print(f"📁 Found {len(test_files)} test files")
        
        # Analyze each file
        print("🔬 Analyzing test files...")
        for i, file_path in enumerate(test_files, 1):
            if i % 20 == 0:
                print(f"   Processed {i}/{len(test_files)} files...")
            
            analysis = self.analyze_file(file_path)
            self.tests.append(analysis)
            
            # Update stats
            if 'error' not in analysis:
                self.stats['total_tests'] += analysis['test_count']
                self.stats['by_location'][analysis['location_category']] += 1
                self.stats['by_category'][analysis['name_category']] += 1
                self.stats['by_type'][analysis['test_type']] += 1
        
        print(f"✅ Analyzed {len(test_files)} files")
        print()
        
        # Find duplicates
        print("🔍 Identifying duplicates...")
        self.find_duplicates()
        print(f"⚠️  Found {len(self.duplicates)} potentially duplicated test names")
        print()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Generate audit report"""
        return {
            'summary': {
                'total_files': self.stats['total_files'],
                'total_test_cases': self.stats['total_tests'],
                'organized_files': (
                    self.stats['by_location']['organized_unit'] +
                    self.stats['by_location']['organized_integration'] +
                    self.stats['by_location']['organized_e2e'] +
                    self.stats['by_location']['backend_organized']
                ),
                'scattered_files': (
                    self.stats['by_location']['root_scattered'] +
                    self.stats['by_location']['backend_scattered']
                ),
                'archived_files': self.stats['by_location']['archived']
            },
            'by_location': dict(self.stats['by_location']),
            'by_category': dict(self.stats['by_category']),
            'by_type': dict(self.stats['by_type']),
            'duplicates': {
                'count': len(self.duplicates),
                'examples': dict(list(self.duplicates.items())[:10])
            },
            'migration_priority': self.calculate_migration_priority(),
            'files': self.tests
        }
    
    def calculate_migration_priority(self) -> List[Dict]:
        """Calculate which files to migrate first"""
        priorities = []
        
        for test in self.tests:
            if 'error' in test:
                continue
            
            # Calculate priority score
            score = 0
            
            # High priority: scattered root files
            if test['location_category'] == 'root_scattered':
                score += 50
            
            # High priority: files with many tests
            score += min(test['test_count'] * 5, 30)
            
            # Medium priority: backend scattered
            if test['location_category'] == 'backend_scattered':
                score += 30
            
            # Bonus for using pytest
            if test['uses_pytest']:
                score += 10
            
            # Bonus for important categories
            important_cats = ['bedding_zones', 'gee_data', 'integration', 'validation']
            if test['name_category'] in important_cats:
                score += 15
            
            # Penalty for archived files
            if test['location_category'] == 'archived':
                score -= 100
            
            # Penalty for already organized
            if 'organized' in test['location_category']:
                score -= 50
            
            priorities.append({
                'file': test['relative_path'],
                'score': score,
                'location': test['location_category'],
                'category': test['name_category'],
                'test_count': test['test_count']
            })
        
        return sorted(priorities, key=lambda x: x['score'], reverse=True)


def main():
    """Main audit execution"""
    auditor = TestAuditor('.')
    report = auditor.run_audit()
    
    # Print summary
    print("=" * 70)
    print("📊 AUDIT SUMMARY")
    print("=" * 70)
    print()
    print(f"Total Test Files: {report['summary']['total_files']}")
    print(f"Total Test Cases: {report['summary']['total_test_cases']}")
    print(f"  ✅ Organized:   {report['summary']['organized_files']}")
    print(f"  ⚠️  Scattered:   {report['summary']['scattered_files']}")
    print(f"  🗄️  Archived:    {report['summary']['archived_files']}")
    print()
    
    print("📍 BY LOCATION:")
    for location, count in sorted(report['by_location'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {location:25} {count:3} files")
    print()
    
    print("🏷️  BY CATEGORY:")
    for category, count in sorted(report['by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {category:25} {count:3} files")
    print()
    
    print("🔬 BY TYPE:")
    for test_type, count in sorted(report['by_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {test_type:25} {count:3} files")
    print()
    
    print("🔝 TOP 10 MIGRATION PRIORITIES:")
    for i, item in enumerate(report['migration_priority'][:10], 1):
        if item['score'] > 0:
            print(f"  {i:2}. [{item['score']:3}] {item['file']}")
            print(f"      Category: {item['category']}, Tests: {item['test_count']}")
    print()
    
    # Save report
    output_file = 'test_audit_report.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"💾 Full report saved to: {output_file}")
    print()
    print("✅ Phase 2 Audit Complete!")
    
    return report


if __name__ == '__main__':
    main()
