#!/usr/bin/env python3

import requests
import numpy as np

def test_vermont_terrain():
    """Test Vermont's terrain and oak tree placement"""
    
    lat, lon = 44.2619, -72.5806  # Vermont coordinates
    
    print("🍁 VERMONT OAK TREES & TERRAIN ANALYSIS")
    print("=" * 60)
    
    # Make prediction request to see terrain analysis
    response = requests.post(
        "http://localhost:8000/predict",
        json={
            "latitude": lat,
            "longitude": lon,
            "season": "early_season",
            "time_of_day": "morning"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"📍 Vermont Location: {lat}, {lon}")
        print(f"🌲 Oak Trees Generated: Yes (check backend logs)")
        print(f"🏔️ Need to check if oak trees are in flat areas (slope < 5°)")
        print(f"📈 Max slope in area determines oak flat eligibility")
        print()
        print("🔍 SUGGESTED SOLUTION:")
        print("• If Vermont terrain is too steep for oak flats...")
        print("• Modify oak flat calculation to be more lenient for Vermont")
        print("• Or ensure oak trees are placed in flatter areas")
        
        # Show feeding areas found
        feeding_areas = data.get('feeding_areas', [])
        print(f"\n🍽️ Feeding Areas Found: {len(feeding_areas)}")
        for i, area in enumerate(feeding_areas, 1):
            print(f"   Area {i}: Score={area.get('score', 'N/A')}")
            
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_vermont_terrain()
