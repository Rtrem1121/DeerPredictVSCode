#!/usr/bin/env python3
"""
Test Wind Approach Bearing Fix
"""
import requests
import json

def test_approach_bearing():
    """Test the fixed approach bearing logic"""
    
    url = "http://localhost:8000/analyze-prediction-detailed"
    
    # Test coordinates
    payload = {
        "lat": 43.3140,
        "lon": -73.2306,
        "date_time": "2025-09-02T07:00:00",
        "time_of_day": 7,
        "season": "fall",
        "hunting_pressure": "low"
    }
    
    print("🌬️ TESTING APPROACH BEARING FIX")
    print("=" * 50)
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract wind analysis
            wind_analyses = data.get("prediction", {}).get("wind_analyses", [])
            wind_summary = data.get("prediction", {}).get("wind_summary", {})
            
            print(f"\n🌬️ WIND SUMMARY:")
            print(f"   Prevailing Wind Direction: {wind_summary.get('prevailing_wind_direction', 'N/A')}°")
            print(f"   Prevailing Wind Speed: {wind_summary.get('prevailing_wind_speed', 'N/A')} mph")
            print(f"   Effective Wind Direction: {wind_summary.get('effective_wind_direction', 'N/A')}°")
            print(f"   Scent Cone Direction: {wind_summary.get('scent_cone_direction', 'N/A')}°")
            print(f"   Optimal Approach Bearing: {wind_summary.get('optimal_approach_bearing', 'N/A')}°")
            
            # Check the logic
            prevailing = wind_summary.get('prevailing_wind_direction', 0)
            scent_cone = wind_summary.get('scent_cone_direction', 0)
            approach = wind_summary.get('optimal_approach_bearing', 0)
            
            print(f"\n🔍 LOGIC VERIFICATION:")
            print(f"   Wind FROM: {prevailing}° (Southwest)")
            print(f"   Scent TO: {scent_cone}° (Northeast)")  
            print(f"   Approach FROM: {approach}° ({'✅ CORRECT' if abs(approach - scent_cone) < 30 else '❌ WRONG'})")
            
            if abs(approach - scent_cone) < 30:
                print(f"   ✅ LOGIC CORRECT: Approaching from {approach}° walks INTO the wind")
                print(f"   ✅ SCENT MANAGEMENT: Your scent blows AWAY from deer")
            else:
                print(f"   ❌ LOGIC ERROR: Approaching from {approach}° with wind from {prevailing}°")
                print(f"   ❌ SCENT ISSUE: Your scent would blow toward deer")
            
            # Check individual location analyses
            print(f"\n📍 INDIVIDUAL LOCATION ANALYSES:")
            for i, analysis in enumerate(wind_analyses[:3]):  # First 3 locations
                location_type = analysis.get('location_type', 'unknown')
                coords = analysis.get('coordinates', [0, 0])
                wind_analysis = analysis.get('wind_analysis', {})
                
                loc_approach = wind_analysis.get('optimal_approach_bearing', 'N/A')
                loc_scent = wind_analysis.get('scent_cone_direction', 'N/A')
                
                print(f"   Location {i+1} ({location_type}):")
                print(f"     Coordinates: {coords[0]:.4f}, {coords[1]:.4f}")
                print(f"     Approach: {loc_approach}°")
                print(f"     Scent Cone: {loc_scent}°")
                print(f"     Status: {'✅ CORRECT' if abs(float(loc_approach) - float(loc_scent)) < 30 else '❌ WRONG'}")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_approach_bearing()
