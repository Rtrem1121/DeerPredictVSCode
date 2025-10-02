#!/usr/bin/env python3
"""
Test script to identify the slope consistency discrepancy.
This script will trace where different slope values are coming from
in the debug output.
"""

import requests
import json

def test_slope_consistency():
    """Test to identify slope consistency issues."""
    
    # Test coordinates in Vermont
    test_data = {
        "lat": 44.1731,
        "lon": -72.5808,
        "camera_range": 708,
        "date_time": "2025-09-02T20:00:00",
        "debug": True
    }
    
    print("🔍 TESTING SLOPE CONSISTENCY DISCREPANCY")
    print("=" * 50)
    
    try:
        # Make prediction request
        response = requests.post(
            "http://localhost:8000/predict",
            json=test_data,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return False
            
        data = response.json()
        
        # Extract all slope values from the response
        print("\n📐 SLOPE VALUES ANALYSIS:")
        print("-" * 40)
        
        # Check gee_data slope
        if "debug" in data and "gee_data" in data["debug"]:
            gee_slope = data["debug"]["gee_data"].get("slope")
            print(f"  GEE Data Slope: {gee_slope}°")
        
        # Check bedding zones slopes
        if "bedding_zones" in data:
            bedding_zones = data["bedding_zones"]
            for i, zone in enumerate(bedding_zones):
                zone_slope = zone.get("slope")
                if zone_slope is not None:
                    print(f"  Bedding Zone {i} Slope: {zone_slope}°")
        
        # Check scoring analysis if available
        if "debug" in data:
            debug_data = data["debug"]
            
            # Look for suitability analysis
            if "suitability_analysis" in debug_data:
                suitability = debug_data["suitability_analysis"]
                if "criteria" in suitability and "slope" in suitability["criteria"]:
                    criteria_slope = suitability["criteria"]["slope"]
                    print(f"  Suitability Criteria Slope: {criteria_slope}°")
            
            # Look for slope tracking
            if "slope_tracking" in debug_data:
                slope_tracking = debug_data["slope_tracking"]
                print(f"\n📊 SLOPE TRACKING ANALYSIS:")
                for key, value in slope_tracking.items():
                    if "slope" in key.lower() or isinstance(value, (int, float)):
                        print(f"    {key}: {value}")
                    elif isinstance(value, list):
                        print(f"    {key}: {value}")
        
        # Check if there are any scoring sections
        print(f"\n🔍 LOOKING FOR SCORING SECTIONS:")
        
        def find_slopes_recursive(obj, path=""):
            """Recursively find all slope values in nested dictionary"""
            slopes_found = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if "slope" in key.lower() and isinstance(value, (int, float)):
                        slopes_found.append((new_path, value))
                    elif isinstance(value, (dict, list)):
                        slopes_found.extend(find_slopes_recursive(value, new_path))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]"
                    slopes_found.extend(find_slopes_recursive(item, new_path))
                        
            return slopes_found
        
        all_slopes = find_slopes_recursive(data)
        
        if all_slopes:
            print("  Found slope values at:")
            for path, value in all_slopes:
                print(f"    {path}: {value}°")
        else:
            print("  No slope values found in debug output")
        
        # Check for inconsistencies
        slope_values = [value for path, value in all_slopes]
        unique_slopes = list(set([round(v, 2) for v in slope_values]))
        
        print(f"\n📈 CONSISTENCY ANALYSIS:")
        print(f"  Total slope values found: {len(slope_values)}")
        print(f"  Unique slope values: {unique_slopes}")
        
        if len(unique_slopes) > 1:
            print(f"  ⚠️  INCONSISTENCY DETECTED: Multiple different slope values!")
            print(f"  💡  Discrepancy range: {max(unique_slopes) - min(unique_slopes):.2f}°")
            return False
        else:
            print(f"  ✅ CONSISTENCY VERIFIED: All slopes match")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_slope_consistency()
    
    if success:
        print("\n🎉 SLOPE CONSISTENCY VERIFIED!")
    else:
        print("\n💥 SLOPE CONSISTENCY ISSUES DETECTED!")
        print("   Multiple slope values found - investigation needed")
    
    exit(0 if success else 1)
