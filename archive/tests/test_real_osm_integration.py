#!/usr/bin/env python3
"""
Test Real OSM Security Integration

Test script to verify that the real OpenStreetMap security data integration
is working correctly with actual Overpass API queries.

Author: Real Data Testing Team
Version: 1.0.0
"""

import requests
import json
import time
from typing import Dict, Any

def test_real_osm_backend_integration():
    """Test the real OSM integration through the backend API"""
    print("🔍 Testing Real OSM Security Integration")
    print("=" * 50)
    
    # Test coordinates in Vermont (should have some infrastructure)
    test_coordinates = [
        {"name": "Montpelier, VT (Urban)", "lat": 44.2601, "lon": -72.5806},
        {"name": "Remote Vermont Forest", "lat": 44.1500, "lon": -72.8000},
        {"name": "Burlington Area, VT", "lat": 44.4759, "lon": -73.2121}
    ]
    
    for location in test_coordinates:
        print(f"\n📍 Testing: {location['name']}")
        print(f"Coordinates: {location['lat']:.4f}, {location['lon']:.4f}")
        
        # Test the backend prediction API
        backend_url = "http://localhost:8000/predict"
        
        test_data = {
            "lat": location['lat'],
            "lon": location['lon'],
            "date_time": "2024-11-15T06:00:00",  # November rut date
            "season": "rut",
            "time_of_day": 6,
            "weather": {
                "conditions": ["clear"],
                "temperature": 45,
                "wind_speed": 5,
                "barometric_pressure": 30.1
            },
            "behavior_type": "mature_buck"
        }
        
        try:
            print("⏳ Sending prediction request...")
            response = requests.post(backend_url, json=test_data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Backend API response received")
                
                # Check for security analysis in different locations
                security_found = False
                
                # Check terrain_analysis first
                if 'terrain_analysis' in result and 'security_analysis' in result['terrain_analysis']:
                    security_data = result['terrain_analysis']['security_analysis']
                    security_found = True
                    print(f"🔒 Security Analysis Found in terrain_analysis:")
                
                # Check mature_buck_analysis
                elif 'mature_buck_analysis' in result:
                    mature_buck_data = result['mature_buck_analysis']
                    print(f"🎯 Mature Buck Analysis Found:")
                    print(f"   Keys: {list(mature_buck_data.keys())}")
                    
                    # Look for security data in mature buck analysis
                    if 'security_analysis' in mature_buck_data:
                        security_data = mature_buck_data['security_analysis']
                        security_found = True
                        print(f"🔒 Security Analysis Found in mature_buck_analysis:")
                    elif 'security_score' in mature_buck_data:
                        print(f"🔒 Security Score Found: {mature_buck_data.get('security_score', 'N/A')}")
                        security_found = True
                    else:
                        print("🔍 Searching for security-related keys...")
                        security_keys = [k for k in mature_buck_data.keys() if 'security' in k.lower() or 'threat' in k.lower()]
                        if security_keys:
                            print(f"   Security-related keys: {security_keys}")
                            for key in security_keys:
                                print(f"   {key}: {mature_buck_data[key]}")
                            security_found = True
                
                if security_found and 'security_data' in locals():
                    print(f"   Overall Security Score: {security_data.get('overall_security_score', 'N/A'):.1f}")
                    print(f"   Pressure Level: {security_data.get('pressure_level', 'N/A')}")
                    print(f"   Confidence: {security_data.get('confidence', 0):.1%}")
                    print(f"   Data Source: {security_data.get('data_source', 'N/A')}")
                    
                    # Check OSM feature counts
                    osm_data = security_data.get('real_osm_data', {})
                    if osm_data:
                        print(f"🗺️ OSM Features Detected:")
                        print(f"   Parking Areas: {len(osm_data.get('parking_areas', []))}")
                        print(f"   Trail Networks: {len(osm_data.get('trail_networks', []))}")
                        print(f"   Road Network: {len(osm_data.get('road_network', []))}")
                        print(f"   Buildings: {len(osm_data.get('buildings', []))}")
                        print(f"   Access Points: {len(osm_data.get('access_points', []))}")
                        print(f"   Road Density: {osm_data.get('road_density_per_km2', 0):.1f}/km²")
                        print(f"   Access Density: {osm_data.get('access_density_per_km2', 0):.1f}/km²")
                    
                    # Check threat categories
                    threat_categories = security_data.get('threat_categories', {})
                    if threat_categories:
                        print(f"⚠️ Threat Levels:")
                        for threat_type, threat_data in threat_categories.items():
                            threat_level = threat_data.get('threat_level', 'unknown')
                            print(f"   {threat_type}: {threat_level}")
                    
                    # Check recommendations
                    recommendations = security_data.get('security_recommendations', [])
                    if recommendations:
                        print(f"💡 Security Recommendations:")
                        for rec in recommendations[:3]:  # Show first 3
                            print(f"   • {rec}")
                
                if not security_found:
                    print("❌ No security analysis found in response")
                    print("Response keys:", list(result.keys()))
            
            else:
                print(f"❌ Backend API error: {response.status_code}")
                print(f"Response: {response.text}")
        
        except requests.exceptions.Timeout:
            print("⏰ Request timed out (60 seconds) - OSM query may be slow")
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - is the backend running on localhost:8000?")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)
        time.sleep(2)  # Brief pause between tests

def test_direct_osm_overpass_api():
    """Test direct connection to OSM Overpass API"""
    print("\n🌐 Testing Direct OSM Overpass API Connection")
    print("=" * 50)
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Simple test query for parking areas around Montpelier, VT
    test_query = """
    [out:json][timeout:25];
    (
      way["amenity"="parking"](around:1000,44.2601,-72.5806);
      node["amenity"="parking"](around:1000,44.2601,-72.5806);
    );
    out geom;
    """
    
    try:
        print("⏳ Querying OSM Overpass API...")
        response = requests.post(overpass_url, data=test_query, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            elements = data.get('elements', [])
            print(f"✅ OSM Overpass API connection successful")
            print(f"🗺️ Found {len(elements)} parking features around Montpelier, VT")
            
            if elements:
                print("📋 Sample OSM Feature:")
                sample = elements[0]
                print(f"   Type: {sample.get('type', 'unknown')}")
                print(f"   ID: {sample.get('id', 'unknown')}")
                print(f"   Tags: {sample.get('tags', {})}")
            
        else:
            print(f"❌ OSM Overpass API error: {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.Timeout:
        print("⏰ OSM Overpass API timeout (30 seconds)")
    except Exception as e:
        print(f"❌ OSM Overpass API error: {e}")

if __name__ == "__main__":
    print("🚀 Real OSM Security Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Direct OSM API connection
    test_direct_osm_overpass_api()
    
    # Test 2: Backend integration
    test_real_osm_backend_integration()
    
    print("\n✅ Real OSM Integration Testing Complete!")
    print("=" * 60)
