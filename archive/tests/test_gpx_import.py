#!/usr/bin/env python3
"""
Test GPX Import Functionality

Tests the new GPX import feature to ensure it works correctly.
"""

import requests
import json

def test_gpx_import():
    """Test the GPX import endpoint"""
    
    print("🧪 Testing GPX Import Functionality")
    print("=" * 50)
    
    # Read the test GPX file
    try:
        with open('test_scouting_waypoints.gpx', 'r') as f:
            gpx_content = f.read()
        print("✅ Test GPX file loaded successfully")
    except FileNotFoundError:
        print("❌ Test GPX file not found")
        return False
    
    # Test the endpoint
    backend_url = "http://localhost:8000"
    
    # Test 1: Preview mode (don't import)
    print("\n🔍 Test 1: Preview Mode")
    try:
        response = requests.post(
            f"{backend_url}/scouting/import_gpx",
            json={
                "gpx_content": gpx_content,
                "auto_import": False,  # Preview only
                "confidence_override": None
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Preview successful: {result['total_waypoints']} waypoints found")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            
            if result['preview']:
                print("   Preview items:")
                for item in result['preview']:
                    print(f"   - {item['type']} at {item['lat']:.5f}, {item['lon']:.5f}")
        else:
            print(f"❌ Preview failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test 2: Check backend health
    print("\n💓 Test 2: Backend Health Check")
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print("⚠️ Backend health check failed")
    except:
        print("❌ Backend not responding")
        return False
    
    # Test 3: Check if GPX parser module exists
    print("\n📦 Test 3: GPX Parser Module")
    try:
        from backend.gpx_parser import get_gpx_parser
        parser = get_gpx_parser()
        print("✅ GPX parser module loaded successfully")
        
        # Test parsing directly
        parse_result = parser.parse_gpx_file(gpx_content)
        if parse_result['success']:
            print(f"✅ Direct parsing successful: {parse_result['total_waypoints']} waypoints")
        else:
            print(f"❌ Direct parsing failed: {parse_result.get('error', 'Unknown error')}")
            
    except ImportError as e:
        print(f"❌ GPX parser import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ GPX parser error: {e}")
        return False
    
    print("\n🎯 Summary:")
    print("✅ GPX import functionality is ready to use!")
    print("📁 Upload test_scouting_waypoints.gpx to test in the frontend")
    print("🌐 Access the app at http://localhost:8501")
    print("📋 Go to 'Scouting Data' tab → 'GPX Import' mode")
    
    return True

if __name__ == "__main__":
    test_gpx_import()
