#!/usr/bin/env python3

import requests
import json

def debug_api_endpoints():
    """Debug API endpoint issues"""
    
    print("🔍 Debugging API Endpoints...")
    
    # Test 1: Check scouting observations endpoint
    print("\n1. Testing scouting observations endpoint:")
    try:
        response = requests.get("http://localhost:8000/scouting/observations")
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
        else:
            data = response.json()
            print(f"   Success: Found {len(data)} observations")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: Check prediction endpoint
    print("\n2. Testing prediction endpoint:")
    try:
        test_data = {
            "lat": 44.2850,
            "lon": -73.0459,
            "weather_conditions": "clear",
            "temperature": 45,
            "wind_speed": 5,
            "time_of_day": "dawn"
        }
        response = requests.post("http://localhost:8000/predict", json=test_data)
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
        else:
            data = response.json()
            print(f"   Success: Probability {data.get('probability', 'N/A')}%")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Check what endpoints are available
    print("\n3. Testing available endpoints:")
    try:
        response = requests.get("http://localhost:8000/docs")
        print(f"   Docs endpoint status: {response.status_code}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 4: Try root endpoint
    print("\n4. Testing root endpoint:")
    try:
        response = requests.get("http://localhost:8000/")
        print(f"   Root status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    debug_api_endpoints()
