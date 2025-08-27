#!/usr/bin/env python3
"""
Focused Code Analysis for Deer Prediction App Project Files Only
"""

import os
import ast
import json
import subprocess
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class FocusedCodeAnalyzer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        
        # Define project-specific directories to analyze
        self.target_dirs = [
            "backend",
            "frontend", 
            "."  # Root level Python files
        ]
        
        # Exclude patterns
        self.exclude_patterns = [
            "__pycache__",
            ".git",
            "venv",
            "env",
            ".pytest_cache",
            "node_modules",
            "docs/archives"
        ]
        
        self.python_files = self._get_project_files()
        self.results = {
            "analysis_date": datetime.now().isoformat(),
            "total_python_files": len(self.python_files),
            "dead_code": {},
            "large_functions": {},
            "duplicate_functions": {},
            "test_debug_files": {},
            "recommendations": []
        }
    
    def _get_project_files(self):
        """Get only project-relevant Python files"""
        files = []
        
        for target_dir in self.target_dirs:
            dir_path = self.project_root / target_dir
            if dir_path.exists():
                if target_dir == ".":
                    # Root level - only direct .py files
                    pattern = "*.py"
                else:
                    # Subdirectories - recursive
                    pattern = "**/*.py"
                
                for py_file in dir_path.glob(pattern):
                    # Skip if in excluded patterns
                    if not any(exc in str(py_file) for exc in self.exclude_patterns):
                        files.append(py_file)
        
        # Remove duplicates
        files = list(set(files))
        return files
    
    def run_focused_vulture(self):
        """Run vulture on specific project directories"""
        print("🔍 Running focused vulture analysis...")
        
        # Create temporary file list for vulture
        target_paths = []
        for target_dir in self.target_dirs:
            dir_path = self.project_root / target_dir
            if dir_path.exists():
                if target_dir == ".":
                    # Add individual root Python files
                    for py_file in dir_path.glob("*.py"):
                        if not any(exc in str(py_file) for exc in self.exclude_patterns):
                            target_paths.append(str(py_file))
                else:
                    target_paths.append(str(dir_path))
        
        try:
            cmd = ["vulture"] + target_paths + ["--min-confidence", "80"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 or result.stdout:
                dead_items = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('vulture') and ':' in line:
                        dead_items.append(line)
                
                self.results["dead_code"] = {
                    "items": dead_items,
                    "count": len(dead_items)
                }
                print(f"   Found {len(dead_items)} potentially unused items")
            else:
                print(f"   No dead code found")
                
        except FileNotFoundError:
            print("   ⚠️ Vulture not installed")
        except Exception as e:
            print(f"   Error running vulture: {e}")
    
    def analyze_project_functions(self):
        """Analyze functions in project files only"""
        print("🔧 Analyzing project functions...")
        
        large_functions = []
        duplicate_functions = defaultdict(list)
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Calculate function size
                        func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                        
                        if func_lines > 50:
                            large_functions.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "function": node.name,
                                "lines": func_lines,
                                "start_line": node.lineno
                            })
                        
                        # Track function names across files
                        duplicate_functions[node.name].append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": node.lineno
                        })
                        
            except Exception as e:
                print(f"   Warning: Could not parse {py_file}: {e}")
        
        # Filter real duplicates (same name, different files)
        real_duplicates = {}
        for func_name, locations in duplicate_functions.items():
            if len(locations) > 1:
                unique_files = set(loc["file"] for loc in locations)
                if len(unique_files) > 1:
                    real_duplicates[func_name] = locations
        
        self.results["large_functions"] = large_functions
        self.results["duplicate_functions"] = real_duplicates
        
        print(f"   Found {len(large_functions)} functions over 50 lines")
        print(f"   Found {len(real_duplicates)} duplicate function names across files")
    
    def categorize_project_files(self):
        """Categorize project files by type and purpose"""
        print("📂 Categorizing project files...")
        
        categories = {
            "core_backend": [],
            "frontend": [],
            "api_routers": [],
            "services": [],
            "tests": [],
            "debug_scripts": [],
            "configuration": [],
            "utilities": []
        }
        
        test_debug_files = []
        
        for py_file in self.python_files:
            rel_path = str(py_file.relative_to(self.project_root))
            file_name = py_file.name.lower()
            
            # Categorize by path and name
            if "frontend" in rel_path:
                categories["frontend"].append(rel_path)
            elif "backend/routers" in rel_path:
                categories["api_routers"].append(rel_path)
            elif "backend/services" in rel_path:
                categories["services"].append(rel_path)
            elif "backend" in rel_path and not any(x in file_name for x in ["test", "debug"]):
                categories["core_backend"].append(rel_path)
            elif any(x in file_name for x in ["test_", "_test.py"]):
                categories["tests"].append(rel_path)
            elif "debug_" in file_name or "validation" in file_name:
                categories["debug_scripts"].append(rel_path)
                test_debug_files.append({
                    "file": rel_path,
                    "size_kb": py_file.stat().st_size / 1024,
                    "type": "debug" if "debug_" in file_name else "validation"
                })
            elif any(x in file_name for x in ["config", "setup"]):
                categories["configuration"].append(rel_path)
            else:
                categories["utilities"].append(rel_path)
        
        self.results["file_categories"] = categories
        self.results["test_debug_files"] = test_debug_files
        
        print("   File distribution:")
        for category, files in categories.items():
            if files:
                print(f"     {category}: {len(files)} files")
        
        if test_debug_files:
            print(f"   Found {len(test_debug_files)} debug/validation scripts")
    
    def identify_cleanup_opportunities(self):
        """Identify specific cleanup opportunities"""
        print("🎯 Identifying cleanup opportunities...")
        
        opportunities = []
        
        # Large functions that should be refactored
        large_funcs = self.results.get("large_functions", [])
        if large_funcs:
            # Group by file
            files_with_large_funcs = defaultdict(list)
            for func in large_funcs:
                files_with_large_funcs[func["file"]].append(func)
            
            opportunities.append({
                "type": "REFACTORING",
                "priority": "MEDIUM",
                "description": f"Refactor {len(large_funcs)} large functions in {len(files_with_large_funcs)} files",
                "details": dict(files_with_large_funcs),
                "action": "Break down functions into smaller, focused functions"
            })
        
        # Debug/validation script consolidation
        debug_files = self.results.get("test_debug_files", [])
        if len(debug_files) > 5:
            total_size = sum(f["size_kb"] for f in debug_files)
            opportunities.append({
                "type": "FILE_CLEANUP",
                "priority": "LOW",
                "description": f"Consolidate {len(debug_files)} debug scripts ({total_size:.1f} KB total)",
                "details": debug_files,
                "action": "Archive old debug scripts, keep only essential ones"
            })
        
        # Dead code removal
        dead_code = self.results.get("dead_code", {})
        if dead_code.get("count", 0) > 0:
            opportunities.append({
                "type": "DEAD_CODE",
                "priority": "HIGH",
                "description": f"Remove {dead_code['count']} unused code items",
                "details": dead_code.get("items", []),
                "action": "Safely remove unused functions and variables"
            })
        
        # Duplicate function review
        duplicates = self.results.get("duplicate_functions", {})
        if duplicates:
            opportunities.append({
                "type": "DEDUPLICATION", 
                "priority": "MEDIUM",
                "description": f"Review {len(duplicates)} duplicate function names",
                "details": duplicates,
                "action": "Check if functions are truly duplicated or just same names"
            })
        
        self.results["cleanup_opportunities"] = opportunities
        
        print("   Cleanup opportunities found:")
        for opp in opportunities:
            print(f"     {opp['priority']}: {opp['description']}")
    
    def save_results(self, output_file="focused_code_analysis.json"):
        """Save focused analysis results"""
        output_path = self.project_root / output_file
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Focused analysis saved to {output_path}")
    
    def print_summary(self):
        """Print analysis summary"""
        print("\n" + "="*60)
        print("🎯 FOCUSED CODE ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"📁 Project Python files analyzed: {self.results['total_python_files']}")
        
        categories = self.results.get("file_categories", {})
        print("\n📂 File Categories:")
        for category, files in categories.items():
            if files:
                print(f"   {category}: {len(files)} files")
        
        opportunities = self.results.get("cleanup_opportunities", [])
        print(f"\n💡 Cleanup opportunities: {len(opportunities)}")
        for opp in opportunities:
            print(f"   {opp['priority']}: {opp['description']}")
        
        dead_code = self.results.get("dead_code", {})
        if dead_code.get("count", 0) > 0:
            print(f"\n💀 Dead code items: {dead_code['count']}")
        
        large_funcs = self.results.get("large_functions", [])
        if large_funcs:
            print(f"🔧 Large functions: {len(large_funcs)}")
        
        print("\n🚀 Recommended next steps:")
        print("1. Review focused_code_analysis.json for details")
        print("2. Start with HIGH priority items")
        print("3. Use git branches for safe changes")
        print("4. Test after each cleanup step")

def main():
    print("🔍 DEER PREDICTION APP - FOCUSED CODE ANALYSIS")
    print("="*55)
    
    analyzer = FocusedCodeAnalyzer()
    
    print(f"📁 Analyzing {len(analyzer.python_files)} project Python files...")
    print("   Target directories: backend/, frontend/, root .py files")
    print()
    
    # Run focused analysis
    analyzer.run_focused_vulture()
    analyzer.analyze_project_functions()
    analyzer.categorize_project_files()
    analyzer.identify_cleanup_opportunities()
    
    # Save and display results
    analyzer.save_results()
    analyzer.print_summary()

if __name__ == "__main__":
    main()
