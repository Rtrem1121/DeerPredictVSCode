#!/usr/bin/env python3
"""
Test script to validate the aspect consistency fix.
This script verifies that feeding areas no longer show misleading bearing angles
in their descriptions and that all terrain aspects are consistent.
"""

import requests
import json
from typing import Dict, Any

def test_aspect_consistency():
    """Test the aspect consistency fix."""
    
    # Test coordinates in Vermont
    test_data = {
        "latitude": 44.1731,
        "longitude": -72.5808,
        "camera_range": 708,
        "debug": True
    }
    
    print("🔍 TESTING ASPECT CONSISTENCY FIX")
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
            print(response.text)
            return False
            
        data = response.json()
        
        # Test 1: Check feeding areas aspect consistency
        print("\n📍 FEEDING AREAS ASPECT ANALYSIS:")
        print("-" * 40)
        
        feeding_areas = data.get("feeding_areas", [])
        if not feeding_areas:
            print("❌ No feeding areas found")
            return False
            
        base_terrain_aspect = None
        aspect_consistent = True
        
        for i, area in enumerate(feeding_areas):
            description = area.get("description", "")
            terrain_aspect = area.get("terrain_aspect")
            
            print(f"\n  Feeding Area {i}:")
            print(f"    Description: {description}")
            print(f"    Terrain Aspect: {terrain_aspect}°")
            
            # Store first terrain aspect as baseline
            if base_terrain_aspect is None:
                base_terrain_aspect = terrain_aspect
            
            # Check if terrain aspects are consistent
            if terrain_aspect != base_terrain_aspect:
                print(f"    ⚠️  INCONSISTENT TERRAIN ASPECT: Expected {base_terrain_aspect}°, got {terrain_aspect}°")
                aspect_consistent = False
            
            # Check if description contains misleading bearing angles
            # Look for patterns like "xxx°" in descriptions that might be bearing angles
            import re
            angle_matches = re.findall(r'\b(\d{1,3})°\b', description)
            if angle_matches:
                for angle in angle_matches:
                    angle_val = float(angle)
                    # If the angle in description doesn't match terrain aspect, it might be a bearing
                    if abs(angle_val - terrain_aspect) > 5:  # Allow 5° tolerance
                        print(f"    ⚠️  POTENTIAL BEARING ANGLE IN DESCRIPTION: {angle}° (terrain aspect is {terrain_aspect}°)")
                        aspect_consistent = False
        
        # Test 2: Check bedding zones aspect classification
        print("\n🛏️ BEDDING ZONES ASPECT ANALYSIS:")
        print("-" * 40)
        
        bedding_zones = data.get("bedding_zones", [])
        if not bedding_zones:
            print("❌ No bedding zones found")
            return False
            
        for i, zone in enumerate(bedding_zones):
            description = zone.get("description", "")
            aspect = zone.get("aspect")
            
            print(f"\n  Bedding Zone {i}:")
            print(f"    Description: {description}")
            print(f"    Aspect: {aspect}°")
            
            # Check if aspect classification is correct
            if aspect is not None:
                # Classify aspect properly
                if 135 <= aspect <= 225:  # South-facing range
                    expected_class = "south-facing"
                elif 45 <= aspect < 135:  # East-facing range
                    expected_class = "east-facing"
                elif 225 < aspect <= 315:  # West-facing range
                    expected_class = "west-facing"
                else:  # North-facing range
                    expected_class = "north-facing"
                
                print(f"    Expected Classification: {expected_class}")
                
                # Check if description matches classification
                description_lower = description.lower()
                if expected_class.split('-')[0] not in description_lower:
                    print(f"    ⚠️  ASPECT CLASSIFICATION MISMATCH: Description doesn't mention {expected_class}")
                    aspect_consistent = False
        
        # Test 3: Overall consistency check
        print(f"\n📊 CONSISTENCY SUMMARY:")
        print("-" * 40)
        
        if aspect_consistent:
            print("✅ All aspects are consistent and properly classified")
        else:
            print("❌ Aspect inconsistencies detected")
        
        print(f"\n📋 RAW DATA SUMMARY:")
        print(f"  Base Terrain Aspect: {base_terrain_aspect}°")
        print(f"  Feeding Areas: {len(feeding_areas)}")
        print(f"  Bedding Zones: {len(bedding_zones)}")
        
        return aspect_consistent
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_aspect_consistency()
    
    if success:
        print("\n🎉 ASPECT CONSISTENCY FIX VALIDATED!")
        print("   All feeding areas show consistent terrain aspects")
        print("   No misleading bearing angles in descriptions")
        print("   Bedding zones properly classified by aspect")
    else:
        print("\n💥 ASPECT CONSISTENCY ISSUES REMAIN!")
        print("   Further fixes needed")
    
    exit(0 if success else 1)
