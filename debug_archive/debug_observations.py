#!/usr/bin/env python3

import requests
import json

def debug_observations():
    """Debug what the observations API returns"""
    
    print("🔍 Debugging Observations API Response")
    print("=" * 50)
    
    test_lat = 44.2850
    test_lon = -73.0459
    
    try:
        response = requests.get("http://localhost:8000/scouting/observations", params={
            "lat": test_lat,
            "lon": test_lon,
            "radius_miles": 5.0
        })
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Type: {type(data)}")
            print(f"Response Length: {len(data) if isinstance(data, (list, dict)) else 'N/A'}")
            
            if isinstance(data, list) and data:
                print(f"First Item Type: {type(data[0])}")
                print(f"First Item: {data[0]}")
                
                if isinstance(data[0], dict):
                    print(f"First Item Keys: {list(data[0].keys())}")
                else:
                    print(f"First Item Value: {repr(data[0])}")
            elif isinstance(data, dict):
                print(f"Dict Keys: {list(data.keys())}")
                print(f"Dict Sample: {dict(list(data.items())[:3])}")
            else:
                print(f"Unexpected Data: {data}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_observations()
