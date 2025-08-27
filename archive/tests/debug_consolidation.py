#!/usr/bin/env python3
"""
Debug Script Consolidation Tool
Archives old debug scripts and creates a comprehensive debug utility
"""

import shutil
from pathlib import Path
from datetime import datetime

class DebugScriptConsolidator:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.archive_dir = self.project_root / "debug_archive"
        self.essential_debug_scripts = {
            # Keep these essential debug scripts
            "debug_api_endpoints.py": "Essential for API debugging",
            "debug_integration.py": "Core integration testing",
            "comprehensive_system_test.py": "Main system validation",
            "comprehensive_testing_suite.py": "Core testing framework"
        }
        
        self.debug_scripts_to_archive = [
            # Specific debug scripts that can be archived
            "debug_enhanced_accuracy_direct.py",
            "debug_observations.py", 
            "debug_gpx_import.py",
            "debug_feeding_scores.py",
            "debug_gee_isolation.py",
            "debug_terrain_features.py",
            "debug_vermont_terrain.py",
            "debug_bedding_scores.py",
            "debug_terrain_scores.py",
            "debug_mature_buck.py",
            "debug_comprehensive_flow.py"
        ]
        
        self.validation_scripts_to_archive = [
            # Validation scripts that can be archived (results already documented)
            "FINAL_VALIDATION_REPORT.py",
            "final_config_validation.py",
            "quick_validation.py",
            "backend_analysis_report.py",
            "final_testing_report.py"
        ]
    
    def create_archive_directory(self):
        """Create archive directory for old debug scripts"""
        self.archive_dir.mkdir(exist_ok=True)
        print(f"📁 Created archive directory: {self.archive_dir}")
    
    def archive_debug_scripts(self):
        """Archive old debug scripts"""
        print("📦 Archiving debug scripts...")
        
        archived_count = 0
        for script_name in self.debug_scripts_to_archive:
            script_path = self.project_root / script_name
            if script_path.exists():
                # Move to archive
                archive_path = self.archive_dir / script_name
                shutil.move(str(script_path), str(archive_path))
                print(f"   ✅ Archived: {script_name}")
                archived_count += 1
            else:
                print(f"   ⚠️ Not found: {script_name}")
        
        print(f"📦 Archived {archived_count} debug scripts")
        return archived_count
    
    def archive_validation_scripts(self):
        """Archive completed validation scripts"""
        print("📊 Archiving validation scripts...")
        
        archived_count = 0
        for script_name in self.validation_scripts_to_archive:
            script_path = self.project_root / script_name
            if script_path.exists():
                archive_path = self.archive_dir / script_name
                shutil.move(str(script_path), str(archive_path))
                print(f"   ✅ Archived: {script_name}")
                archived_count += 1
        
        print(f"📊 Archived {archived_count} validation scripts")
        return archived_count
    
    def create_consolidated_debug_tool(self):
        """Create a single comprehensive debug tool"""
        debug_tool_content = '''#!/usr/bin/env python3
"""
Consolidated Debug Tool for Deer Prediction App
Replaces multiple individual debug scripts with a unified interface
"""

import requests
import json
import sys
from datetime import datetime

class DeerPredictionDebugger:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_api_health(self):
        """Test basic API health"""
        print("🔍 Testing API Health...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("   ✅ API is responding")
                return True
            else:
                print(f"   ❌ API returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ API connection failed: {e}")
            return False
    
    def test_prediction_endpoint(self, lat=44.26, lon=-72.58):
        """Test main prediction endpoint"""
        print(f"🎯 Testing prediction for ({lat}, {lon})...")
        try:
            response = self.session.get(f"{self.base_url}/predict/{lat}/{lon}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Prediction successful")
                print(f"   📊 Confidence: {data.get('confidence', 'N/A')}%")
                print(f"   🎯 Score: {data.get('score', 'N/A')}")
                return data
            else:
                print(f"   ❌ Prediction failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return None
        except Exception as e:
            print(f"   ❌ Prediction request failed: {e}")
            return None
    
    def test_camera_placement(self, lat=44.26, lon=-72.58):
        """Test camera placement optimization"""
        print(f"📷 Testing camera placement for ({lat}, {lon})...")
        try:
            response = self.session.get(f"{self.base_url}/camera-placement/{lat}/{lon}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Camera placement successful")
                print(f"   📍 Position: {data.get('camera_lat', 'N/A')}, {data.get('camera_lon', 'N/A')}")
                print(f"   📊 Confidence: {data.get('confidence', 'N/A')}%")
                return data
            else:
                print(f"   ❌ Camera placement failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Camera placement request failed: {e}")
            return None
    
    def test_mature_buck_analysis(self, lat=44.26, lon=-72.58):
        """Test mature buck specific analysis"""
        print(f"🦌 Testing mature buck analysis for ({lat}, {lon})...")
        try:
            response = self.session.get(f"{self.base_url}/mature-buck/{lat}/{lon}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Mature buck analysis successful")
                print(f"   📊 Buck Score: {data.get('buck_score', 'N/A')}")
                print(f"   🎯 Confidence: {data.get('confidence', 'N/A')}%")
                return data
            else:
                print(f"   ❌ Mature buck analysis failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Mature buck request failed: {e}")
            return None
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🔍 COMPREHENSIVE DEBUG TEST")
        print("=" * 40)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {
            "api_health": self.test_api_health(),
            "prediction": None,
            "camera_placement": None,
            "mature_buck": None
        }
        
        if results["api_health"]:
            print()
            results["prediction"] = self.test_prediction_endpoint()
            print()
            results["camera_placement"] = self.test_camera_placement()
            print()
            results["mature_buck"] = self.test_mature_buck_analysis()
        
        print()
        print("📊 SUMMARY")
        print("-" * 20)
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        return results

def main():
    """Main debug interface"""
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
    else:
        action = "comprehensive"
    
    debugger = DeerPredictionDebugger()
    
    if action == "health":
        debugger.test_api_health()
    elif action == "prediction":
        lat = float(sys.argv[2]) if len(sys.argv) > 2 else 44.26
        lon = float(sys.argv[3]) if len(sys.argv) > 3 else -72.58
        debugger.test_prediction_endpoint(lat, lon)
    elif action == "camera":
        lat = float(sys.argv[2]) if len(sys.argv) > 2 else 44.26
        lon = float(sys.argv[3]) if len(sys.argv) > 3 else -72.58
        debugger.test_camera_placement(lat, lon)
    elif action == "buck":
        lat = float(sys.argv[2]) if len(sys.argv) > 2 else 44.26
        lon = float(sys.argv[3]) if len(sys.argv) > 3 else -72.58
        debugger.test_mature_buck_analysis(lat, lon)
    else:
        debugger.run_comprehensive_test()

if __name__ == "__main__":
    main()
'''
        
        debug_tool_path = self.project_root / "debug_tool.py"
        with open(debug_tool_path, 'w', encoding='utf-8') as f:
            f.write(debug_tool_content)
        
        print(f"🛠️ Created consolidated debug tool: debug_tool.py")
        
        # Create usage instructions
        readme_content = f'''# Debug Archive

This directory contains archived debug and validation scripts that were consolidated on {datetime.now().strftime('%Y-%m-%d')}.

## Archived Scripts

### Debug Scripts
These scripts were used for specific debugging tasks and have been replaced by `debug_tool.py`:
{chr(10).join(f"- {script}" for script in self.debug_scripts_to_archive)}

### Validation Scripts  
These scripts were used for validation testing. Results are documented in `docs/TESTING.md`:
{chr(10).join(f"- {script}" for script in self.validation_scripts_to_archive)}

## Current Debug Tools

Use these instead of archived scripts:

### Main Debug Tool
```bash
# Run comprehensive test
python debug_tool.py

# Test specific components
python debug_tool.py health
python debug_tool.py prediction 44.26 -72.58
python debug_tool.py camera 44.26 -72.58
python debug_tool.py buck 44.26 -72.58
```

### Essential Debug Scripts (Still Active)
{chr(10).join(f"- {script}: {desc}" for script, desc in self.essential_debug_scripts.items())}

## Restoration

If you need to restore any archived script:
```bash
cp debug_archive/script_name.py ./
```
'''
        
        readme_path = self.archive_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"📄 Created archive documentation: {readme_path}")
    
    def print_summary(self):
        """Print consolidation summary"""
        print("\n" + "="*50)
        print("🎯 DEBUG SCRIPT CONSOLIDATION SUMMARY")
        print("="*50)
        
        if self.archive_dir.exists():
            archived_files = list(self.archive_dir.glob("*.py"))
            print(f"📦 Archived scripts: {len(archived_files)}")
            
            total_size = sum(f.stat().st_size for f in archived_files) / 1024
            print(f"💾 Space reclaimed: {total_size:.1f} KB")
            
            print(f"🛠️ New consolidated debug tool: debug_tool.py")
            print(f"📁 Archive location: {self.archive_dir}")
            
            print("\n🚀 Usage:")
            print("  python debug_tool.py                    # Run all tests")
            print("  python debug_tool.py health             # API health check")
            print("  python debug_tool.py prediction 44.26 -72.58  # Test prediction")

def main():
    print("🧹 DEBUG SCRIPT CONSOLIDATION")
    print("="*35)
    
    consolidator = DebugScriptConsolidator()
    
    # Create archive directory
    consolidator.create_archive_directory()
    
    # Archive scripts
    debug_archived = consolidator.archive_debug_scripts()
    validation_archived = consolidator.archive_validation_scripts()
    
    # Create consolidated tool
    consolidator.create_consolidated_debug_tool()
    
    # Print summary
    consolidator.print_summary()
    
    print(f"\n✅ Consolidation complete!")
    print(f"   Debug scripts archived: {debug_archived}")
    print(f"   Validation scripts archived: {validation_archived}")

if __name__ == "__main__":
    main()
