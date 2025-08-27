#!/usr/bin/env python3
"""
Single test to trigger debug logging
"""
import requests

def single_debug_test():
    """Test a single location to trigger debug logging"""
    
    test_request = {
        "name": "Debug Test",
        "lat": 44.074565,
        "lon": -72.647567,
        "date_time": "2024-10-15T06:00:00",
        "season": "early_season",
        "weather": {"temperature": 45, "wind_speed": 8, "wind_direction": 190}
    }
    
    print("Making single API call for debug purposes...")
    
    try:
        response = requests.post('http://localhost:8000/predict', 
                               json=test_request,
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            mature_buck_data = data.get('mature_buck_analysis', {})
            terrain_scores = mature_buck_data.get('terrain_scores', {})
            
            print(f"API Response:")
            print(f"  Isolation Score: {terrain_scores.get('isolation_score', 'N/A'):.1f}")
            print(f"  Pressure Resistance: {terrain_scores.get('pressure_resistance', 'N/A'):.1f}")
            
        else:
            print(f"API Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    single_debug_test()
