#!/usr/bin/env python3
"""
Debug GPX Import Issue

Test the scouting data manager directly to identify the problem.
"""

import requests
import json

def debug_gpx_import():
    """Debug the GPX import issue"""
    
    print("🔍 Debugging GPX Import Issue")
    print("=" * 50)
    
    backend_url = "http://localhost:8000"
    
    # Test 1: Try adding a simple observation directly
    print("\n🧪 Test 1: Direct Observation Add")
    try:
        test_observation = {
            "lat": 44.2619,
            "lon": -72.5806,
            "observation_type": "Fresh Scrape",
            "notes": "Test observation to debug import",
            "confidence": 8,
            "timestamp": "2025-08-13T19:00:00"
        }
        
        response = requests.post(
            f"{backend_url}/scouting/add_observation",
            json=test_observation,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Direct observation add works!")
        else:
            print(f"❌ Direct observation add failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Direct observation add error: {e}")
    
    # Test 2: Check GPX import with minimal data
    print("\n🧪 Test 2: Minimal GPX Import")
    try:
        minimal_gpx = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <wpt lat="44.2619" lon="-72.5806">
    <name>Test Scrape</name>
    <desc>Test scrape for debugging</desc>
    <type>Fresh Scrape</type>
  </wpt>
</gpx>'''
        
        import_request = {
            "gpx_content": minimal_gpx,
            "auto_import": True,
            "confidence_override": 8
        }
        
        response = requests.post(
            f"{backend_url}/scouting/import_gpx",
            json=import_request,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            print(f"Total waypoints: {result['total_waypoints']}")
            print(f"Imported: {result['imported_observations']}")
            print(f"Errors: {result.get('errors', [])}")
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ GPX import error: {e}")
    
    # Test 3: Check existing observations
    print("\n🧪 Test 3: Check Existing Observations")
    try:
        response = requests.get(
            f"{backend_url}/scouting/observations",
            params={
                "lat": 44.2619,
                "lon": -72.5806,
                "radius_miles": 50
            },
            timeout=10
        )
        
        if response.status_code == 200:
            observations = response.json()
            print(f"Found {len(observations)} existing observations")
            for obs in observations[:3]:  # Show first 3
                print(f"  - {obs.get('observation_type', 'Unknown')} at {obs.get('lat', 0):.4f}, {obs.get('lon', 0):.4f}")
        else:
            print(f"Failed to get observations: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Get observations error: {e}")

if __name__ == "__main__":
    debug_gpx_import()
