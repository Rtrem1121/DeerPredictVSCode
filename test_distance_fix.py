#!/usr/bin/env python3
"""
Test script to verify the distance calculation fix
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_distance_calculations():
    """Test the distance calculation to verify the fix"""
    
    print("🔍 Testing distance calculations...")
    
    # Import the functions
    try:
        from backend.main import calculate_distance, calculate_bearing
        print("✅ Successfully imported distance functions from main.py")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return
    
    # Test coordinates (roughly 100-200 yards apart)
    center_lat, center_lon = 44.2619, -72.5806
    
    # Create a test point about 150 yards away
    # 150 yards = ~0.085 miles = ~0.00137 degrees
    test_lat = center_lat + 0.00137
    test_lon = center_lon + 0.00137
    
    # Calculate distance
    distance_miles = calculate_distance(center_lat, center_lon, test_lat, test_lon)
    distance_yards = distance_miles * 1760
    
    print(f"\n📏 Distance Calculation Test:")
    print(f"   Center: {center_lat:.6f}, {center_lon:.6f}")
    print(f"   Test point: {test_lat:.6f}, {test_lon:.6f}")
    print(f"   Distance: {distance_miles:.6f} miles = {distance_yards:.0f} yards")
    
    # Test what 15,429 represents
    problematic_yards = 15429
    problematic_miles = problematic_yards / 1760
    problematic_degrees = problematic_yards / 111000
    
    print(f"\n🐛 Analysis of 15,429 yards bug:")
    print(f"   15,429 yards = {problematic_miles:.6f} miles")
    print(f"   15,429 yards = {problematic_degrees:.6f} degrees (if treated as meters/111000)")
    
    # Show what this degree value would be in a realistic distance
    if problematic_degrees < 0.01:  # Reasonable degree difference
        realistic_miles = problematic_degrees * 69  # Rough miles per degree
        realistic_yards = realistic_miles * 1760
        print(f"   {problematic_degrees:.6f} degrees ≈ {realistic_miles:.3f} miles ≈ {realistic_yards:.0f} yards (realistic)")
    
    print(f"\n✅ If fix is working, stands should show distances like {distance_yards:.0f} yards, not 15,429 yards")

if __name__ == "__main__":
    test_distance_calculations()
