#!/usr/bin/env python3
"""
Dead Code Analysis Tool for Deer Prediction App
Identifies unused functions, variables, imports, and potential duplicate code
"""

import os
import ast
import json
import subprocess
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class CodeAnalyzer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.python_files = list(self.project_root.rglob("*.py"))
        self.results = {
            "analysis_date": datetime.now().isoformat(),
            "total_python_files": len(self.python_files),
            "dead_code": {},
            "unused_imports": {},
            "duplicate_functions": {},
            "large_functions": {},
            "test_coverage": {},
            "recommendations": []
        }
    
    def run_vulture_analysis(self):
        """Run vulture to find dead code"""
        print("🔍 Running vulture analysis for dead code...")
        
        try:
            result = subprocess.run(
                ["vulture", ".", "--min-confidence", "80", "--sort-by-size"],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            if result.returncode == 0:
                self.results["dead_code"]["vulture_output"] = result.stdout
                # Parse vulture output
                dead_items = []
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('vulture'):
                        dead_items.append(line.strip())
                self.results["dead_code"]["items"] = dead_items
                print(f"   Found {len(dead_items)} potentially unused items")
            else:
                print(f"   Vulture analysis failed: {result.stderr}")
                
        except FileNotFoundError:
            print("   ⚠️ Vulture not installed or not in PATH")
    
    def run_unimport_analysis(self):
        """Run unimport to find unused imports"""
        print("📦 Running unimport analysis for unused imports...")
        
        try:
            result = subprocess.run(
                ["unimport", "--check", "--diff"],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            self.results["unused_imports"]["unimport_output"] = result.stdout
            if result.stdout:
                print(f"   Found unused imports (see detailed output)")
            else:
                print("   No unused imports found")
                
        except FileNotFoundError:
            print("   ⚠️ Unimport not installed or not in PATH")
    
    def analyze_function_complexity(self):
        """Find large functions that should be refactored"""
        print("🔧 Analyzing function complexity...")
        
        large_functions = []
        duplicate_functions = defaultdict(list)
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Calculate function size (lines)
                        func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                        
                        if func_lines > 50:  # Large function threshold
                            large_functions.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "function": node.name,
                                "lines": func_lines,
                                "start_line": node.lineno
                            })
                        
                        # Track potential duplicates by function name
                        duplicate_functions[node.name].append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": node.lineno
                        })
            
            except Exception as e:
                print(f"   Error analyzing {py_file}: {e}")
        
        # Filter actual duplicates (same name in different files)
        actual_duplicates = {}
        for func_name, locations in duplicate_functions.items():
            if len(locations) > 1:
                # Only count as duplicate if in different files
                files = set(loc["file"] for loc in locations)
                if len(files) > 1:
                    actual_duplicates[func_name] = locations
        
        self.results["large_functions"] = large_functions
        self.results["duplicate_functions"] = actual_duplicates
        
        print(f"   Found {len(large_functions)} functions over 50 lines")
        print(f"   Found {len(actual_duplicates)} potentially duplicate function names")
    
    def analyze_test_files(self):
        """Analyze test files for potential consolidation"""
        print("🧪 Analyzing test files...")
        
        test_patterns = ["test_", "debug_", "_test", "validation", "comprehensive"]
        test_files = []
        
        for py_file in self.python_files:
            file_name = py_file.name.lower()
            if any(pattern in file_name for pattern in test_patterns):
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = len(content.splitlines())
                    
                    test_files.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "lines": lines,
                        "size_kb": py_file.stat().st_size / 1024
                    })
                except Exception as e:
                    print(f"   Error analyzing {py_file}: {e}")
        
        self.results["test_files"] = test_files
        print(f"   Found {len(test_files)} test/debug files")
    
    def run_test_coverage(self):
        """Run test coverage analysis if pytest is available"""
        print("📊 Running test coverage analysis...")
        
        try:
            result = subprocess.run(
                ["pytest", "--cov=backend", "--cov=frontend", "--cov-report=term-missing", "--tb=no", "-q"],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            self.results["test_coverage"]["coverage_output"] = result.stdout
            
            # Extract coverage percentage
            for line in result.stdout.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    parts = line.split()
                    for part in parts:
                        if '%' in part:
                            self.results["test_coverage"]["total_coverage"] = part
                            break
            
            print(f"   Test coverage analysis completed")
            
        except FileNotFoundError:
            print("   ⚠️ Pytest not available for coverage analysis")
    
    def identify_file_categories(self):
        """Categorize Python files by purpose"""
        print("📂 Categorizing Python files...")
        
        categories = {
            "core_backend": [],
            "frontend": [],
            "tests": [],
            "debug_scripts": [],
            "utilities": [],
            "configuration": [],
            "other": []
        }
        
        for py_file in self.python_files:
            file_path = str(py_file.relative_to(self.project_root))
            file_name = py_file.name.lower()
            
            if "frontend" in file_path or "streamlit" in file_name:
                categories["frontend"].append(file_path)
            elif "backend" in file_path and not any(x in file_name for x in ["test", "debug"]):
                categories["core_backend"].append(file_path)
            elif any(x in file_name for x in ["test_", "debug_", "_test"]):
                if "debug" in file_name:
                    categories["debug_scripts"].append(file_path)
                else:
                    categories["tests"].append(file_path)
            elif any(x in file_name for x in ["config", "setup", "install"]):
                categories["configuration"].append(file_path)
            elif any(x in file_name for x in ["util", "helper", "tool", "script"]):
                categories["utilities"].append(file_path)
            else:
                categories["other"].append(file_path)
        
        self.results["file_categories"] = categories
        
        for category, files in categories.items():
            if files:
                print(f"   {category}: {len(files)} files")
    
    def generate_recommendations(self):
        """Generate specific recommendations based on analysis"""
        print("💡 Generating cleanup recommendations...")
        
        recommendations = []
        
        # Dead code recommendations
        if self.results["dead_code"].get("items"):
            dead_count = len(self.results["dead_code"]["items"])
            recommendations.append({
                "priority": "HIGH",
                "category": "Dead Code Removal",
                "description": f"Remove {dead_count} unused functions/variables identified by vulture",
                "action": "Review vulture output and safely remove unused code",
                "risk": "LOW - Static analysis identified"
            })
        
        # Large functions
        large_funcs = self.results.get("large_functions", [])
        if large_funcs:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Code Refactoring", 
                "description": f"Refactor {len(large_funcs)} functions over 50 lines",
                "action": "Break down large functions into smaller, focused functions",
                "risk": "MEDIUM - Requires testing"
            })
        
        # Duplicate functions
        duplicates = self.results.get("duplicate_functions", {})
        if duplicates:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Code Deduplication",
                "description": f"Review {len(duplicates)} duplicate function names",
                "action": "Consolidate or rename duplicate functions",
                "risk": "MEDIUM - May require refactoring"
            })
        
        # Test files
        test_files = self.results.get("test_files", [])
        debug_files = [f for f in test_files if "debug" in f["file"]]
        if len(debug_files) > 10:
            recommendations.append({
                "priority": "LOW",
                "category": "Test Cleanup",
                "description": f"Consolidate {len(debug_files)} debug scripts",
                "action": "Archive or consolidate debug/validation scripts",
                "risk": "LOW - Non-production scripts"
            })
        
        self.results["recommendations"] = recommendations
        
        for rec in recommendations:
            print(f"   {rec['priority']}: {rec['description']}")
    
    def save_results(self, output_file="code_analysis_results.json"):
        """Save analysis results to JSON file"""
        output_path = self.project_root / output_file
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Analysis results saved to {output_path}")
    
    def print_summary(self):
        """Print a summary of the analysis"""
        print("\n" + "="*60)
        print("🎯 CODE ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"📁 Total Python files analyzed: {self.results['total_python_files']}")
        
        if self.results["dead_code"].get("items"):
            print(f"💀 Dead code items found: {len(self.results['dead_code']['items'])}")
        
        if self.results.get("large_functions"):
            print(f"🔧 Large functions (>50 lines): {len(self.results['large_functions'])}")
        
        if self.results.get("duplicate_functions"):
            print(f"🔄 Duplicate function names: {len(self.results['duplicate_functions'])}")
        
        if self.results.get("test_files"):
            print(f"🧪 Test/debug files: {len(self.results['test_files'])}")
        
        if self.results["test_coverage"].get("total_coverage"):
            print(f"📊 Test coverage: {self.results['test_coverage']['total_coverage']}")
        
        print(f"💡 Recommendations generated: {len(self.results['recommendations'])}")
        
        print("\n🚀 Next steps:")
        print("1. Review code_analysis_results.json for detailed findings")
        print("2. Start with HIGH priority recommendations")
        print("3. Test thoroughly after each change")
        print("4. Use git branches for safe experimentation")

def main():
    print("🔍 DEER PREDICTION APP - CODE ANALYSIS")
    print("="*50)
    
    analyzer = CodeAnalyzer()
    
    # Run all analyses
    analyzer.run_vulture_analysis()
    analyzer.run_unimport_analysis()
    analyzer.analyze_function_complexity()
    analyzer.analyze_test_files()
    analyzer.run_test_coverage()
    analyzer.identify_file_categories()
    analyzer.generate_recommendations()
    
    # Save and display results
    analyzer.save_results()
    analyzer.print_summary()

if __name__ == "__main__":
    main()
