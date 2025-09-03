#!/usr/bin/env python3
"""
Test the exact coordinates through the production API
"""

import requests
import json

def test_production_api():
    """Test the exact coordinates from the problem report through production API"""
    print("🌐 TESTING PRODUCTION API WITH EXACT COORDINATES")
    print("=" * 60)
    
    # Exact coordinates from the problem report
    test_lat = 43.3140
    test_lon = -73.2306
    
    print(f"📍 Problem Coordinates: {test_lat:.4f}, {test_lon:.4f}")
    print("🎯 User reported: Only 1 alternative bedding zone generated")
    print()
    
    try:
        # Test the production API endpoint
        api_url = "http://localhost:8000/analyze-prediction-detailed"
        
        payload = {
            "lat": test_lat,
            "lon": test_lon,
            "date_time": "2025-09-02T07:00:00",  # Morning time as seen in logs
            "time_of_day": 7,
            "season": "fall",
            "hunting_pressure": "low"
        }
        
        print("🔗 CALLING PRODUCTION API...")
        print(f"   URL: {api_url}")
        print(f"   Payload: {payload}")
        print()
        
        response = requests.post(api_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API CALL SUCCESSFUL")
            print()
            
            # Debug: Print full result structure
            print("🔍 DEBUG: Full API Response Structure:")
            for key in result.keys():
                if key == "bedding_zones":
                    bedding_zones = result[key]
                    print(f"   {key}: {type(bedding_zones)} with {len(bedding_zones.get('features', []))} features")
                elif key == "prediction":
                    prediction = result[key]
                    print(f"   {key}: {type(prediction)}")
                    if isinstance(prediction, dict):
                        for subkey in prediction.keys():
                            if subkey == "bedding_zones":
                                zones = prediction[subkey]
                                print(f"      {subkey}: {type(zones)} with {len(zones.get('features', []) if isinstance(zones, dict) else zones)} features")
                            else:
                                print(f"      {subkey}: {type(prediction[subkey])}")
                elif key == "detailed_analysis":
                    analysis = result[key]
                    print(f"   {key}: {type(analysis)}")
                    if isinstance(analysis, dict):
                        for subkey in analysis.keys():
                            if subkey == "bedding_zones":
                                zones = analysis[subkey]
                                print(f"      {subkey}: {type(zones)} with {len(zones.get('features', []) if isinstance(zones, dict) else zones)} features")
                            else:
                                print(f"      {subkey}: {type(analysis[subkey])}")
                else:
                    print(f"   {key}: {type(result[key])}")
            print()
            
            # Try to find bedding zones in nested structure
            bedding_zones = result.get("bedding_zones")
            if not bedding_zones:
                bedding_zones = result.get("prediction", {}).get("bedding_zones")
            if not bedding_zones:
                bedding_zones = result.get("detailed_analysis", {}).get("bedding_zones")
            
            if not bedding_zones:
                bedding_zones = {}
                
            features = bedding_zones.get("features", []) if isinstance(bedding_zones, dict) else []
            
            print("📊 PRODUCTION API BEDDING ZONE RESULTS:")
            print("=" * 50)
            print(f"Total Bedding Zones: {len(features)}")
            print(f"Expected: 2-3 zones")
            print(f"Status: {'✅ MEETS REQUIREMENT' if len(features) >= 2 else '❌ FAILS REQUIREMENT'}")
            print()
            
            if features:
                for i, feature in enumerate(features):
                    props = feature.get('properties', {})
                    coords = feature.get('geometry', {}).get('coordinates', [0, 0])
                    
                    print(f"🛏️ Bedding Zone {i+1}:")
                    print(f"   Location: {coords[1]:.4f}, {coords[0]:.4f}")
                    print(f"   Type: {props.get('bedding_type', 'unknown')}")
                    print(f"   Score: {props.get('score', 0):.1f}%")
                    print(f"   Confidence: {props.get('confidence', 0):.2f}")
                    print(f"   Aspect: {props.get('aspect', 'N/A')}°")
                    print(f"   Slope: {props.get('slope', 'N/A')}°")
                    if 'distance_from_primary' in props:
                        print(f"   Distance: {props.get('distance_from_primary', 0)}m")
                    print()
                
                # Check bedding zone properties for search method
                properties = bedding_zones.get('properties', {})
                search_method = properties.get('search_method', 'unknown')
                total_features = properties.get('total_features', len(features))
                
                print("🔍 SEARCH METHOD ANALYSIS:")
                print(f"   Search Method: {search_method}")
                print(f"   Total Features: {total_features}")
                print(f"   Enhancement Version: {properties.get('enhancement_version', 'unknown')}")
                
                if 'bedding_diversity' in properties:
                    diversity = properties['bedding_diversity']
                    print(f"   Zone Types: {diversity.get('zone_types', [])}")
                    print(f"   Distance Range: {diversity.get('distance_range_m', {})}")
                    print(f"   Thermal Diversity: {diversity.get('thermal_diversity', 'unknown')}")
                
                print()
                
                # Compare to user's issue
                print("🎯 ISSUE ANALYSIS:")
                if len(features) == 1:
                    print("   ❌ CONFIRMED: Only 1 bedding zone generated (matches user report)")
                    print("   🦌 IMPACT: Insufficient for mature buck movement patterns")
                    
                    # Check if it's the exact coordinates mentioned
                    if len(features) > 0:
                        zone_coords = features[0].get('geometry', {}).get('coordinates', [0, 0])
                        zone_lat, zone_lon = zone_coords[1], zone_coords[0]
                        expected_lat, expected_lon = 43.3140, -73.2306
                        
                        if abs(zone_lat - expected_lat) < 0.001 and abs(zone_lon - expected_lon) < 0.001:
                            print(f"   ✅ EXACT MATCH: Zone at {zone_lat:.4f}, {zone_lon:.4f} matches user report")
                        else:
                            print(f"   ⚠️  DIFFERENT LOCATION: Zone at {zone_lat:.4f}, {zone_lon:.4f} vs expected {expected_lat:.4f}, {expected_lon:.4f}")
                            
                elif len(features) >= 2:
                    print("   ✅ RESOLVED: Multiple bedding zones now generated")
                    print("   🦌 IMPROVEMENT: Adequate for mature buck movement patterns")
                    
                else:
                    print("   ❌ CRITICAL: No bedding zones generated")
                    
            else:
                print("❌ NO BEDDING ZONES GENERATED")
                print("   This indicates a critical system failure")
                
            # Check for slope rejection issue mentioned by user
            suitability = result.get("suitability_analysis", {})
            if suitability:
                slope = suitability.get("criteria", {}).get("slope")
                if slope:
                    print(f"🔍 SLOPE ANALYSIS:")
                    print(f"   Primary Slope: {slope}°")
                    print(f"   Within Range: {3 <= slope <= 30}")
                    if 20 <= slope <= 26:
                        print(f"   ⚠️  POTENTIAL ISSUE: Slope {slope}° near rejection threshold")
                        
        else:
            print(f"❌ API CALL FAILED: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_production_api()
