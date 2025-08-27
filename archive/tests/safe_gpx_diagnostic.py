#!/usr/bin/env python3
"""
SAFE GPX Import Diagnostic Tool

This script safely diagnoses GPX import issues without modifying any existing code.
It creates a minimal test environment to understand why waypoints aren't being imported.
"""

import requests
import json
import logging
from datetime import datetime

def safe_diagnostic_test():
    """Safely diagnose the GPX import issue"""
    
    print("🔍 SAFE GPX Import Diagnostic")
    print("=" * 40)
    print("⚠️  This tool only reads/tests - it won't modify any app code")
    
    backend_url = "http://localhost:8000"
    
    # Test 1: Check if backend is responding
    print("\n1️⃣ Backend Health Check...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print(f"⚠️ Backend health issue: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return
    
    # Test 2: Check scouting endpoints
    print("\n2️⃣ Scouting System Check...")
    try:
        # Test observation types endpoint
        response = requests.get(f"{backend_url}/scouting/types", timeout=5)
        if response.status_code == 200:
            print("✅ Scouting system is available")
        else:
            print(f"⚠️ Scouting system issue: {response.status_code}")
    except Exception as e:
        print(f"❌ Scouting system check failed: {e}")
    
    # Test 3: Try a minimal GPX import test
    print("\n3️⃣ Minimal GPX Test...")
    minimal_gpx = '''<?xml version="1.0"?>
<gpx version="1.1">
<wpt lat="44.5" lon="-72.5">
<name>Test Stand</name>
<desc>Test hunting stand</desc>
</wpt>
</gpx>'''
    
    try:
        response = requests.post(
            f"{backend_url}/scouting/import_gpx",
            json={
                "gpx_content": minimal_gpx,
                "auto_import": False,  # Preview only - safe
                "confidence_override": None
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ GPX endpoint responds")
            print(f"   Parsed waypoints: {result.get('total_waypoints', 0)}")
            print(f"   Would import: {len(result.get('preview', []))}")
            if result.get('errors'):
                print(f"   Errors: {result['errors']}")
        else:
            print(f"❌ GPX endpoint error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ GPX test failed: {e}")
    
    # Test 4: Check data directory
    print("\n4️⃣ Data Storage Check...")
    try:
        import os
        data_file = "data/scouting_observations.json"
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                data = json.load(f)
            obs_count = len(data.get('observations', []))
            print(f"✅ Data file exists with {obs_count} observations")
        else:
            print("⚠️ Data file doesn't exist yet")
    except Exception as e:
        print(f"❌ Data check failed: {e}")
    
    print("\n🎯 Diagnostic Summary:")
    print("This diagnostic doesn't modify any code - it's safe to run.")
    print("Based on your issue: 290 waypoints found, 0 imported, 0 skipped")
    print("This suggests waypoints are parsed but conversion/saving fails.")
    
    print("\n📋 Next Steps (all safe):")
    print("1. Check the detailed response from your actual GPX file")
    print("2. Look at specific error messages")
    print("3. Test with a smaller sample first")
    
    return True

def suggest_safe_fixes():
    """Suggest safe debugging approaches"""
    print("\n🔧 SAFE Debugging Suggestions:")
    print("=" * 35)
    
    print("\n✅ Safe Option 1: Use Preview Mode")
    print("   - Always use 'Preview before importing' first")
    print("   - This shows what would be imported without changing anything")
    
    print("\n✅ Safe Option 2: Test Small Sample")
    print("   - Create a small GPX with just 1-2 waypoints")
    print("   - Test the workflow before trying the full file")
    
    print("\n✅ Safe Option 3: Check Browser Console")
    print("   - Press F12 in browser")
    print("   - Look for JavaScript errors in Console tab")
    
    print("\n✅ Safe Option 4: Different File Format")
    print("   - Some GPX files have encoding issues")
    print("   - Try saving your GPX as UTF-8 if possible")
    
    print("\n⚠️ What NOT to do:")
    print("   - Don't modify core app files")
    print("   - Don't restart containers unnecessarily")
    print("   - Don't change database files directly")

if __name__ == "__main__":
    safe_diagnostic_test()
    suggest_safe_fixes()
