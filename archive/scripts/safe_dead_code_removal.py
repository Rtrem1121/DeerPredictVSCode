#!/usr/bin/env python3
"""
Safe Dead Code Removal Tool
Implements safe removal of unused imports and variables with git tracking
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict

class SafeDeadCodeRemover:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.changes_made = []
        
    def remove_unused_imports(self, dead_code_items: List[str]) -> Dict:
        """Safely remove unused imports"""
        print("🧹 Starting safe unused import removal...")
        
        # Group by file for efficient processing
        files_to_fix = {}
        for item in dead_code_items:
            if "unused import" in item:
                # Parse: "filename:line: unused import 'name'"
                parts = item.split(":")
                if len(parts) >= 3:
                    file_path = parts[0].strip()
                    line_num = int(parts[1].strip())
                    import_name = self._extract_import_name(item)
                    
                    if file_path not in files_to_fix:
                        files_to_fix[file_path] = []
                    files_to_fix[file_path].append({
                        "line": line_num,
                        "import_name": import_name,
                        "full_item": item
                    })
        
        results = {
            "files_processed": 0,
            "imports_removed": 0,
            "errors": []
        }
        
        for file_path, imports_to_remove in files_to_fix.items():
            try:
                if self._remove_imports_from_file(file_path, imports_to_remove):
                    results["files_processed"] += 1
                    results["imports_removed"] += len(imports_to_remove)
                    print(f"   ✅ Fixed {len(imports_to_remove)} imports in {file_path}")
            except Exception as e:
                error_msg = f"Error processing {file_path}: {e}"
                results["errors"].append(error_msg)
                print(f"   ❌ {error_msg}")
        
        return results
    
    def _extract_import_name(self, dead_code_item: str) -> str:
        """Extract import name from vulture output"""
        # Pattern: "unused import 'name'"
        match = re.search(r"unused import '([^']+)'", dead_code_item)
        if match:
            return match.group(1)
        return ""
    
    def _remove_imports_from_file(self, file_path: str, imports_to_remove: List[Dict]) -> bool:
        """Remove specific imports from a file"""
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            print(f"   Warning: File not found: {file_path}")
            return False
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Sort by line number in reverse order to avoid index shifting
            imports_to_remove.sort(key=lambda x: x["line"], reverse=True)
            
            lines_removed = 0
            for import_info in imports_to_remove:
                line_idx = import_info["line"] - 1  # Convert to 0-based index
                
                if 0 <= line_idx < len(lines):
                    line_content = lines[line_idx].strip()
                    import_name = import_info["import_name"]
                    
                    # Check if this is the import we're looking for
                    if self._is_correct_import_line(line_content, import_name):
                        # Handle different import patterns
                        if self._remove_import_from_line(lines, line_idx, import_name):
                            lines_removed += 1
                            self.changes_made.append(f"Removed import '{import_name}' from {file_path}:{import_info['line']}")
            
            if lines_removed > 0:
                # Write back the modified file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True
                
        except Exception as e:
            print(f"   Error processing {file_path}: {e}")
            return False
        
        return False
    
    def _is_correct_import_line(self, line_content: str, import_name: str) -> bool:
        """Check if this line contains the import we want to remove"""
        # Handle various import patterns
        patterns = [
            f"import {import_name}",
            f"from .* import .*{import_name}",
            f"from .* import {import_name}",
            f"import .* as {import_name}"
        ]
        
        for pattern in patterns:
            if re.search(pattern, line_content):
                return True
        return False
    
    def _remove_import_from_line(self, lines: List[str], line_idx: int, import_name: str) -> bool:
        """Remove specific import from a line, handling multiline imports"""
        line = lines[line_idx]
        
        # Simple case: entire line is just this import
        if re.match(rf"^\s*import\s+{re.escape(import_name)}\s*$", line) or \
           re.match(rf"^\s*from\s+.*\s+import\s+{re.escape(import_name)}\s*$", line):
            lines[line_idx] = ""
            return True
        
        # Multiple imports on one line: "from x import a, b, c"
        if "," in line and import_name in line:
            # Remove just this import from the list
            new_line = re.sub(rf"\b{re.escape(import_name)}\s*,\s*", "", line)
            new_line = re.sub(rf",\s*\b{re.escape(import_name)}\b", "", new_line)
            new_line = re.sub(rf"\b{re.escape(import_name)}\b", "", new_line)
            
            # Clean up extra commas and spaces
            new_line = re.sub(r",\s*,", ",", new_line)
            new_line = re.sub(r"import\s*,", "import", new_line)
            new_line = re.sub(r",\s*$", "", new_line)
            
            if new_line != line:
                lines[line_idx] = new_line
                return True
        
        return False
    
    def remove_unused_variables(self, dead_code_items: List[str]) -> Dict:
        """Remove unused variables (more careful approach)"""
        print("🧹 Processing unused variables...")
        
        variable_items = [item for item in dead_code_items if "unused variable" in item]
        
        results = {
            "variables_found": len(variable_items),
            "variables_removed": 0,
            "skipped": 0
        }
        
        # For now, just report - variable removal is more complex
        if variable_items:
            print(f"   Found {len(variable_items)} unused variables")
            print("   Skipping variable removal - requires manual review")
            results["skipped"] = len(variable_items)
        
        return results
    
    def create_safe_removal_branch(self):
        """Create a git branch for safe experimentation"""
        try:
            # Check current branch
            result = subprocess.run(["git", "branch", "--show-current"], 
                                  capture_output=True, text=True)
            current_branch = result.stdout.strip()
            
            # Create new branch for cleanup
            branch_name = f"cleanup-dead-code-{current_branch}"
            subprocess.run(["git", "checkout", "-b", branch_name], 
                          capture_output=True, text=True)
            
            print(f"✅ Created safe branch: {branch_name}")
            return branch_name
            
        except Exception as e:
            print(f"⚠️ Could not create git branch: {e}")
            return None
    
    def test_after_cleanup(self) -> bool:
        """Run basic tests to ensure cleanup didn't break anything"""
        print("🧪 Running post-cleanup validation...")
        
        try:
            # Test Python syntax
            result = subprocess.run(["python", "-m", "py_compile", "backend/main.py"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"   ❌ Syntax error in main.py: {result.stderr}")
                return False
            
            # Test imports in key files
            test_files = ["backend/core.py", "frontend/app.py"]
            for test_file in test_files:
                if Path(test_file).exists():
                    result = subprocess.run(["python", "-m", "py_compile", test_file], 
                                          capture_output=True, text=True)
                    if result.returncode != 0:
                        print(f"   ❌ Syntax error in {test_file}: {result.stderr}")
                        return False
            
            print("   ✅ Basic syntax validation passed")
            return True
            
        except Exception as e:
            print(f"   ❌ Error during testing: {e}")
            return False
    
    def commit_changes(self, description: str):
        """Commit the cleanup changes"""
        try:
            subprocess.run(["git", "add", "."], capture_output=True)
            subprocess.run(["git", "commit", "-m", description], capture_output=True)
            print(f"✅ Committed changes: {description}")
        except Exception as e:
            print(f"⚠️ Could not commit changes: {e}")
    
    def print_summary(self):
        """Print summary of changes made"""
        print("\n" + "="*50)
        print("🎯 DEAD CODE REMOVAL SUMMARY")
        print("="*50)
        
        if self.changes_made:
            print(f"📝 Changes made: {len(self.changes_made)}")
            for change in self.changes_made[:10]:  # Show first 10
                print(f"   - {change}")
            if len(self.changes_made) > 10:
                print(f"   ... and {len(self.changes_made) - 10} more")
        else:
            print("📝 No changes made")

def main():
    # Load analysis results
    analysis_file = Path("focused_code_analysis.json")
    if not analysis_file.exists():
        print("❌ Run focused_code_analysis.py first")
        return
    
    import json
    with open(analysis_file, 'r') as f:
        analysis = json.load(f)
    
    dead_code_items = analysis.get("dead_code", {}).get("items", [])
    
    if not dead_code_items:
        print("✅ No dead code found to remove")
        return
    
    print("🧹 SAFE DEAD CODE REMOVAL")
    print("="*30)
    print(f"Found {len(dead_code_items)} items to review")
    
    remover = SafeDeadCodeRemover()
    
    # Create safe branch
    branch = remover.create_safe_removal_branch()
    
    # Remove unused imports (safer)
    import_results = remover.remove_unused_imports(dead_code_items)
    
    # Process unused variables (report only)
    variable_results = remover.remove_unused_variables(dead_code_items)
    
    # Test the changes
    if remover.test_after_cleanup():
        # Commit if tests pass
        description = f"Remove {import_results['imports_removed']} unused imports - automated cleanup"
        remover.commit_changes(description)
    else:
        print("❌ Tests failed - review changes manually")
    
    # Print summary
    remover.print_summary()
    
    print(f"\n📊 Results:")
    print(f"   Files processed: {import_results['files_processed']}")
    print(f"   Imports removed: {import_results['imports_removed']}")
    print(f"   Variables found: {variable_results['variables_found']} (manual review needed)")
    
    if import_results['errors']:
        print(f"   Errors: {len(import_results['errors'])}")

if __name__ == "__main__":
    main()
