#!/usr/bin/env python3
"""
Backend Response Inspector
Examines exactly what the backend is returning
"""

import requests
import json

def inspect_backend_response():
    """Inspect the exact backend response structure"""
    
    response = requests.post(
        "http://localhost:8000/predict",
        json={
            "lat": 44.2619,
            "lon": -72.5806,
            "date_time": "2025-11-15T06:00:00",
            "season": "rut",
            "include_camera_placement": True
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("🔍 FULL BACKEND RESPONSE STRUCTURE")
        print("=" * 50)
        print(json.dumps(data, indent=2))
        
        print("\\n🔍 TOP-LEVEL KEYS:")
        for key in data.keys():
            print(f"   - {key}: {type(data[key])}")
            
    else:
        print(f"❌ API request failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    inspect_backend_response()
