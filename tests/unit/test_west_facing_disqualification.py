#!/usr/bin/env python3
"""
Test script to verify the west-facing aspect disqualification fix.
This script tests that west-facing slopes (225°-315°) are now properly
disqualified for bedding zones.
"""

import requests
import json

def test_west_facing_disqualification():
    """Test that west-facing slopes are properly disqualified."""
    
    # Test coordinates in Vermont
    test_data = {
        "lat": 44.1731,
        "lon": -72.5808,
        "camera_range": 708,
        "date_time": "2025-09-02T20:00:00",
        "debug": True
    }
    
    print("🔍 TESTING WEST-FACING ASPECT DISQUALIFICATION")
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
        
        # Check aspect values and disqualification
        print("\n📐 ASPECT DISQUALIFICATION ANALYSIS:")
        print("-" * 40)
        
        # Check gee_data aspect
        gee_aspect = None
        if "debug" in data and "gee_data" in data["debug"]:
            gee_aspect = data["debug"]["gee_data"].get("aspect")
            print(f"  GEE Data Aspect: {gee_aspect}°")
            
            # Classify the aspect
            if gee_aspect is not None:
                if 135 <= gee_aspect <= 225:
                    aspect_class = "SOUTH-FACING (OPTIMAL)"
                    expected_disqualification = False
                elif 225 < gee_aspect < 315:
                    aspect_class = "WEST-FACING (SHOULD BE DISQUALIFIED)"
                    expected_disqualification = True
                elif 45 < gee_aspect < 135:
                    aspect_class = "EAST-FACING (SHOULD BE DISQUALIFIED)"
                    expected_disqualification = True
                elif 315 <= gee_aspect or gee_aspect <= 45:
                    aspect_class = "NORTH-FACING (SHOULD BE DISQUALIFIED)"
                    expected_disqualification = True
                else:
                    aspect_class = "UNKNOWN RANGE"
                    expected_disqualification = True
                
                print(f"  Aspect Classification: {aspect_class}")
                print(f"  Expected Disqualification: {expected_disqualification}")
        
        # Check bedding zones
        bedding_zones = data.get("bedding_zones", {})
        if isinstance(bedding_zones, dict):
            bedding_features = bedding_zones.get("features", [])
        else:
            bedding_features = bedding_zones if isinstance(bedding_zones, list) else []
        
        print(f"\n🛏️ BEDDING ZONES ANALYSIS:")
        print(f"  Number of bedding zones generated: {len(bedding_features)}")
        
        if len(bedding_features) == 0:
            print("  ✅ NO BEDDING ZONES - Aspect disqualification working!")
            
            # Check if there's a disqualification reason
            if isinstance(bedding_zones, dict) and "properties" in bedding_zones:
                props = bedding_zones["properties"]
                disqualified_reason = props.get("disqualified_reason", "")
                print(f"  Disqualification Reason: {disqualified_reason}")
                
                if "aspect" in disqualified_reason.lower():
                    print("  ✅ Aspect disqualification confirmed in reason!")
                    return True
                else:
                    print("  ⚠️  Disqualified but reason doesn't mention aspect")
                    return False
            else:
                print("  ⚠️  No disqualification reason found")
                return False
        else:
            print("  ❌ BEDDING ZONES GENERATED - Disqualification failed!")
            for i, zone in enumerate(bedding_features):
                if "properties" in zone:
                    zone_aspect = zone["properties"].get("aspect")
                    print(f"    Zone {i} Aspect: {zone_aspect}°")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_west_facing_disqualification()
    
    if success:
        print("\n🎉 WEST-FACING ASPECT DISQUALIFICATION WORKING!")
        print("   System properly rejects west-facing slopes for bedding")
        print("   Biological accuracy maintained for mature buck preferences")
    else:
        print("\n💥 WEST-FACING ASPECT DISQUALIFICATION FAILED!")
        print("   System still allowing unsuitable aspects for bedding")
        print("   Further fixes needed")
    
    exit(0 if success else 1)
