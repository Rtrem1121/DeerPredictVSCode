#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis for Deer Prediction App
=====================================================

This script analyzes the codebase for:
1. Dead/unused code
2. Duplicate functionality
3. Code quality issues
4. Security vulnerabilities
5. Performance bottlenecks
6. Architecture improvements

Author: GitHub Copilot
Date: August 26, 2025
"""

import os
import ast
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from collections import defaultdict, Counter
from datetime import datetime
import importlib.util

class CodebaseAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.analysis_results = {
            "summary": {},
            "dead_code": {
                "unused_files": [],
                "unused_functions": [],
                "unused_classes": [],
                "unused_imports": [],
                "commented_code": []
            },
            "duplicates": {
                "duplicate_files": [],
                "duplicate_functions": [],
                "similar_code_blocks": []
            },
            "quality_issues": {
                "long_functions": [],
                "complex_functions": [],
                "magic_numbers": [],
                "todo_comments": [],
                "print_statements": []
            },
            "security_issues": {
                "hardcoded_secrets": [],
                "sql_injection_risks": [],
                "unsafe_imports": []
            },
            "performance_issues": {
                "inefficient_loops": [],
                "large_files": [],
                "memory_leaks": []
            },
            "architecture": {
                "circular_imports": [],
                "tight_coupling": [],
                "missing_abstractions": []
            }
        }
        
        # Patterns for analysis
        self.test_file_patterns = [
            r'test_.*\.py$',
            r'.*_test\.py$',
            r'.*test.*\.py$',
            r'debug_.*\.py$',
            r'demo_.*\.py$',
            r'check_.*\.py$',
            r'analyze_.*\.py$'
        ]
        
        self.backup_patterns = [
            r'.*\.backup$',
            r'.*\.old$',
            r'.*_backup\.py$',
            r'.*_old\.py$',
            r'.*_copy\.py$'
        ]

    def analyze(self) -> Dict[str, Any]:
        """Run comprehensive analysis"""
        print("🔍 Starting Comprehensive Codebase Analysis...")
        
        # Get all Python files
        python_files = self._get_python_files()
        print(f"📁 Found {len(python_files)} Python files")
        
        # Analyze each category
        self._analyze_file_usage(python_files)
        self._analyze_imports_and_functions(python_files)
        self._analyze_code_quality(python_files)
        self._analyze_duplicates(python_files)
        self._analyze_security(python_files)
        self._analyze_performance(python_files)
        self._generate_summary()
        
        return self.analysis_results

    def _get_python_files(self) -> List[Path]:
        """Get all Python files excluding virtual environments"""
        python_files = []
        exclude_dirs = {'.venv', '__pycache__', '.git', 'node_modules', '.pytest_cache'}
        
        for file_path in self.root_path.rglob('*.py'):
            # Skip virtual environment and cache directories
            if any(part in exclude_dirs for part in file_path.parts):
                continue
            python_files.append(file_path)
        
        return python_files

    def _analyze_file_usage(self, files: List[Path]):
        """Analyze file usage patterns"""
        print("📋 Analyzing file usage patterns...")
        
        # Identify test files
        test_files = []
        backup_files = []
        
        for file_path in files:
            file_name = file_path.name
            
            # Check for test files
            if any(re.match(pattern, file_name) for pattern in self.test_file_patterns):
                test_files.append(str(file_path.relative_to(self.root_path)))
            
            # Check for backup files
            if any(re.match(pattern, file_name) for pattern in self.backup_patterns):
                backup_files.append(str(file_path.relative_to(self.root_path)))
        
        # Check for duplicate main files
        main_files = [f for f in files if 'main' in f.name and f.suffix == '.py']
        if len(main_files) > 1:
            self.analysis_results["duplicates"]["duplicate_files"].extend([
                str(f.relative_to(self.root_path)) for f in main_files
            ])
        
        self.analysis_results["dead_code"]["unused_files"] = backup_files
        self.analysis_results["summary"]["test_files"] = len(test_files)
        self.analysis_results["summary"]["backup_files"] = len(backup_files)

    def _analyze_imports_and_functions(self, files: List[Path]):
        """Analyze imports and function usage"""
        print("🔗 Analyzing imports and function usage...")
        
        all_imports = defaultdict(list)
        all_functions = defaultdict(list)
        function_calls = defaultdict(set)
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                file_rel_path = str(file_path.relative_to(self.root_path))
                
                # Analyze imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            all_imports[alias.name].append(file_rel_path)
                    
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ''
                        for alias in node.names:
                            full_name = f"{module}.{alias.name}" if module else alias.name
                            all_imports[full_name].append(file_rel_path)
                    
                    elif isinstance(node, ast.FunctionDef):
                        all_functions[node.name].append(file_rel_path)
                    
                    elif isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            function_calls[node.func.id].add(file_rel_path)
                        elif isinstance(node.func, ast.Attribute):
                            function_calls[node.func.attr].add(file_rel_path)
            
            except Exception as e:
                print(f"⚠️  Error parsing {file_path}: {e}")
        
        # Find unused imports and functions
        unused_functions = []
        for func_name, defined_in in all_functions.items():
            if func_name not in function_calls or len(function_calls[func_name]) == 0:
                # Skip if it's a main function or special methods
                if func_name not in ['main', '__init__', '__str__', '__repr__'] and not func_name.startswith('test_'):
                    unused_functions.append({
                        'function': func_name,
                        'defined_in': defined_in
                    })
        
        self.analysis_results["dead_code"]["unused_functions"] = unused_functions[:20]  # Limit output

    def _analyze_code_quality(self, files: List[Path]):
        """Analyze code quality issues"""
        print("✨ Analyzing code quality...")
        
        long_functions = []
        todo_comments = []
        print_statements = []
        magic_numbers = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                file_rel_path = str(file_path.relative_to(self.root_path))
                
                # Check for TODO comments
                for i, line in enumerate(lines, 1):
                    if re.search(r'#.*TODO|#.*FIXME|#.*HACK', line, re.IGNORECASE):
                        todo_comments.append({
                            'file': file_rel_path,
                            'line': i,
                            'content': line.strip()
                        })
                    
                    # Check for print statements (potential debug code)
                    if re.search(r'\bprint\s*\(', line) and 'logging' not in line:
                        print_statements.append({
                            'file': file_rel_path,
                            'line': i,
                            'content': line.strip()
                        })
                
                # Parse AST for detailed analysis
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Calculate function length
                        func_length = node.end_lineno - node.lineno + 1
                        if func_length > 50:  # Functions longer than 50 lines
                            long_functions.append({
                                'function': node.name,
                                'file': file_rel_path,
                                'length': func_length,
                                'start_line': node.lineno
                            })
                    
                    # Check for magic numbers
                    elif isinstance(node, ast.Constant):
                        if isinstance(node.value, (int, float)) and node.value not in [0, 1, -1]:
                            magic_numbers.append({
                                'value': node.value,
                                'file': file_rel_path,
                                'line': node.lineno
                            })
            
            except Exception as e:
                print(f"⚠️  Error analyzing quality for {file_path}: {e}")
        
        self.analysis_results["quality_issues"]["long_functions"] = long_functions[:10]
        self.analysis_results["quality_issues"]["todo_comments"] = todo_comments[:20]
        self.analysis_results["quality_issues"]["print_statements"] = print_statements[:15]
        self.analysis_results["quality_issues"]["magic_numbers"] = magic_numbers[:15]

    def _analyze_duplicates(self, files: List[Path]):
        """Analyze code duplication"""
        print("🔄 Analyzing code duplication...")
        
        # Look for similar function names
        function_signatures = defaultdict(list)
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                file_rel_path = str(file_path.relative_to(self.root_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Create a signature based on function name and parameters
                        params = [arg.arg for arg in node.args.args]
                        signature = f"{node.name}({', '.join(params)})"
                        function_signatures[signature].append(file_rel_path)
            
            except Exception as e:
                continue
        
        # Find duplicate function signatures
        duplicate_functions = []
        for signature, files_list in function_signatures.items():
            if len(files_list) > 1:
                duplicate_functions.append({
                    'signature': signature,
                    'files': files_list
                })
        
        self.analysis_results["duplicates"]["duplicate_functions"] = duplicate_functions[:10]

    def _analyze_security(self, files: List[Path]):
        """Analyze security issues"""
        print("🔒 Analyzing security issues...")
        
        hardcoded_secrets = []
        unsafe_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                file_rel_path = str(file_path.relative_to(self.root_path))
                
                for i, line in enumerate(lines, 1):
                    for pattern in unsafe_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            hardcoded_secrets.append({
                                'file': file_rel_path,
                                'line': i,
                                'content': line.strip()[:100]  # Truncate for safety
                            })
            
            except Exception as e:
                continue
        
        self.analysis_results["security_issues"]["hardcoded_secrets"] = hardcoded_secrets[:10]

    def _analyze_performance(self, files: List[Path]):
        """Analyze performance issues"""
        print("⚡ Analyzing performance issues...")
        
        large_files = []
        
        for file_path in files:
            try:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                if size_mb > 1:  # Files larger than 1MB
                    large_files.append({
                        'file': str(file_path.relative_to(self.root_path)),
                        'size_mb': round(size_mb, 2)
                    })
            except Exception as e:
                continue
        
        self.analysis_results["performance_issues"]["large_files"] = sorted(
            large_files, key=lambda x: x['size_mb'], reverse=True
        )[:10]

    def _generate_summary(self):
        """Generate analysis summary"""
        results = self.analysis_results
        
        summary = {
            "total_issues": (
                len(results["dead_code"]["unused_files"]) +
                len(results["dead_code"]["unused_functions"]) +
                len(results["quality_issues"]["long_functions"]) +
                len(results["quality_issues"]["todo_comments"]) +
                len(results["duplicates"]["duplicate_functions"]) +
                len(results["security_issues"]["hardcoded_secrets"])
            ),
            "critical_issues": len(results["security_issues"]["hardcoded_secrets"]),
            "dead_code_items": (
                len(results["dead_code"]["unused_files"]) +
                len(results["dead_code"]["unused_functions"])
            ),
            "quality_score": self._calculate_quality_score()
        }
        
        self.analysis_results["summary"].update(summary)

    def _calculate_quality_score(self) -> int:
        """Calculate overall code quality score (0-100)"""
        total_issues = self.analysis_results["summary"].get("total_issues", 0)
        
        # Base score of 100, subtract points for issues
        score = 100
        score -= min(total_issues * 2, 50)  # Max 50 points deducted for issues
        score -= len(self.analysis_results["security_issues"]["hardcoded_secrets"]) * 10
        score -= len(self.analysis_results["performance_issues"]["large_files"]) * 5
        
        return max(score, 0)

    def generate_report(self) -> str:
        """Generate formatted analysis report"""
        results = self.analysis_results
        report = []
        
        report.append("=" * 80)
        report.append("🦌 DEER PREDICTION APP - CODEBASE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📁 Root Path: {self.root_path}")
        report.append("")
        
        # Summary
        summary = results["summary"]
        report.append("📊 SUMMARY")
        report.append("-" * 40)
        report.append(f"Quality Score: {summary.get('quality_score', 0)}/100")
        report.append(f"Total Issues: {summary.get('total_issues', 0)}")
        report.append(f"Critical Issues: {summary.get('critical_issues', 0)}")
        report.append(f"Dead Code Items: {summary.get('dead_code_items', 0)}")
        report.append("")
        
        # Dead Code Analysis
        if results["dead_code"]["unused_files"]:
            report.append("🗑️  DEAD CODE - UNUSED FILES")
            report.append("-" * 40)
            for file in results["dead_code"]["unused_files"][:10]:
                report.append(f"  ❌ {file}")
            report.append("")
        
        if results["dead_code"]["unused_functions"]:
            report.append("🗑️  DEAD CODE - UNUSED FUNCTIONS")
            report.append("-" * 40)
            for func in results["dead_code"]["unused_functions"][:10]:
                report.append(f"  ❌ {func['function']} in {func['defined_in'][0]}")
            report.append("")
        
        # Duplicates
        if results["duplicates"]["duplicate_functions"]:
            report.append("🔄 DUPLICATE CODE")
            report.append("-" * 40)
            for dup in results["duplicates"]["duplicate_functions"][:5]:
                report.append(f"  🔄 {dup['signature']}")
                for file in dup['files']:
                    report.append(f"     📄 {file}")
            report.append("")
        
        # Quality Issues
        if results["quality_issues"]["long_functions"]:
            report.append("📏 QUALITY ISSUES - LONG FUNCTIONS")
            report.append("-" * 40)
            for func in results["quality_issues"]["long_functions"][:5]:
                report.append(f"  📏 {func['function']} ({func['length']} lines) in {func['file']}")
            report.append("")
        
        if results["quality_issues"]["todo_comments"]:
            report.append("📝 QUALITY ISSUES - TODO COMMENTS")
            report.append("-" * 40)
            for todo in results["quality_issues"]["todo_comments"][:5]:
                report.append(f"  📝 {todo['file']}:{todo['line']} - {todo['content']}")
            report.append("")
        
        # Security Issues
        if results["security_issues"]["hardcoded_secrets"]:
            report.append("🔒 SECURITY ISSUES")
            report.append("-" * 40)
            for secret in results["security_issues"]["hardcoded_secrets"][:5]:
                report.append(f"  🔒 {secret['file']}:{secret['line']} - Potential hardcoded secret")
            report.append("")
        
        # Performance Issues
        if results["performance_issues"]["large_files"]:
            report.append("⚡ PERFORMANCE ISSUES - LARGE FILES")
            report.append("-" * 40)
            for file in results["performance_issues"]["large_files"][:5]:
                report.append(f"  ⚡ {file['file']} ({file['size_mb']} MB)")
            report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 40)
        self._add_recommendations(report, results)
        
        return "\n".join(report)

    def _add_recommendations(self, report: List[str], results: Dict[str, Any]):
        """Add specific recommendations based on analysis"""
        recommendations = []
        
        # Dead code recommendations
        if results["dead_code"]["unused_files"]:
            recommendations.append("🗑️  Remove backup and unused files to reduce codebase size")
            recommendations.append("   • Safely delete .backup files after verification")
            recommendations.append("   • Archive old test files or move to separate directory")
        
        if results["dead_code"]["unused_functions"]:
            recommendations.append("🔧 Clean up unused functions to improve maintainability")
            recommendations.append("   • Use static analysis tools like 'vulture' or 'unimport'")
            recommendations.append("   • Review functions before deletion - they might be API endpoints")
        
        # Quality improvements
        if results["quality_issues"]["long_functions"]:
            recommendations.append("📏 Refactor long functions for better maintainability")
            recommendations.append("   • Break functions > 50 lines into smaller, focused functions")
            recommendations.append("   • Apply Single Responsibility Principle")
        
        if results["duplicates"]["duplicate_functions"]:
            recommendations.append("🔄 Eliminate code duplication")
            recommendations.append("   • Extract common functionality into shared modules")
            recommendations.append("   • Use inheritance or composition patterns")
        
        # Security improvements
        if results["security_issues"]["hardcoded_secrets"]:
            recommendations.append("🔒 Fix security issues immediately")
            recommendations.append("   • Move secrets to environment variables")
            recommendations.append("   • Use proper configuration management")
            recommendations.append("   • Add .env files to .gitignore")
        
        # Architecture improvements
        recommendations.append("🏗️  Architecture improvements:")
        recommendations.append("   • Implement dependency injection for better testing")
        recommendations.append("   • Add comprehensive logging strategy")
        recommendations.append("   • Consider using design patterns (Factory, Strategy)")
        recommendations.append("   • Implement proper error handling and custom exceptions")
        
        # Tools recommendations
        recommendations.append("🛠️  Recommended tools:")
        recommendations.append("   • Code quality: black, isort, mypy, pylint")
        recommendations.append("   • Dead code detection: vulture, unimport")
        recommendations.append("   • Security: bandit, safety")
        recommendations.append("   • Testing: pytest with coverage (pytest-cov)")
        recommendations.append("   • Performance: cProfile, memory_profiler")
        
        report.extend(recommendations)

def main():
    """Main analysis function"""
    from datetime import datetime
    
    # Initialize analyzer
    root_path = "."
    analyzer = CodebaseAnalyzer(root_path)
    
    # Run analysis
    results = analyzer.analyze()
    
    # Generate and save report
    report = analyzer.generate_report()
    
    # Save results
    with open("codebase_analysis_results.json", "w", encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    with open("codebase_analysis_report.txt", "w", encoding='utf-8') as f:
        f.write(report)
    
    # Print summary
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"📊 Quality Score: {results['summary'].get('quality_score', 0)}/100")
    print(f"🔍 Total Issues Found: {results['summary'].get('total_issues', 0)}")
    print(f"🗑️  Dead Code Items: {results['summary'].get('dead_code_items', 0)}")
    print(f"🔒 Security Issues: {results['summary'].get('critical_issues', 0)}")
    print("")
    print("📄 Reports saved:")
    print("   • codebase_analysis_results.json (detailed data)")
    print("   • codebase_analysis_report.txt (human-readable)")
    print("")
    
    # Show top priority issues
    if results["security_issues"]["hardcoded_secrets"]:
        print("🚨 CRITICAL: Security issues found! Review immediately.")
    
    if results["dead_code"]["unused_files"]:
        print(f"🗑️  Found {len(results['dead_code']['unused_files'])} files that can be safely removed.")
    
    return results

if __name__ == "__main__":
    main()
