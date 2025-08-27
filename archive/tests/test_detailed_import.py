#!/usr/bin/env python3
"""
Detailed GPX Import Test

Test the complete GPX import process step by step to identify where it's failing.
"""

import requests
import json

def test_detailed_import():
    """Test GPX import with detailed error tracking"""
    
    print("🔍 Detailed GPX Import Test")
    print("=" * 40)
    
    # Read the test GPX file
    with open('test_scouting_waypoints.gpx', 'r') as f:
        gpx_content = f.read()
    
    backend_url = "http://localhost:8000"
    
    # Test with actual import (not preview)
    print("\n📥 Test: Actual Import Mode")
    try:
        response = requests.post(
            f"{backend_url}/scouting/import_gpx",
            json={
                "gpx_content": gpx_content,
                "auto_import": True,  # Actually import
                "confidence_override": 8  # Set a specific confidence
            },
            timeout=15
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response received")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            print(f"   Total waypoints: {result['total_waypoints']}")
            print(f"   Imported: {result['imported_observations']}")
            print(f"   Skipped: {result['skipped_waypoints']}")
            
            if result.get('errors'):
                print(f"\n❌ Errors:")
                for error in result['errors']:
                    print(f"   - {error}")
            
            if result['preview']:
                print(f"\n📋 Preview ({len(result['preview'])} items):")
                for item in result['preview']:
                    print(f"   - {item}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Check if observations were actually saved
    print("\n🔍 Checking saved observations...")
    try:
        response = requests.get(
            f"{backend_url}/scouting/observations",
            params={
                "lat": 44.262,
                "lon": -72.58,
                "radius_miles": 5.0
            },
            timeout=10
        )
        
        if response.status_code == 200:
            observations = response.json()
            print(f"✅ Found {len(observations)} saved observations in area")
            
            for i, obs in enumerate(observations[:3]):  # Show first 3
                print(f"   {i+1}. {obs.get('observation_type', 'Unknown')} at {obs.get('lat', 0):.5f}, {obs.get('lon', 0):.5f}")
                print(f"      Notes: {obs.get('notes', 'No notes')[:50]}...")
                
        else:
            print(f"❌ Failed to retrieve observations: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Failed to check observations: {e}")

if __name__ == "__main__":
    test_detailed_import()
