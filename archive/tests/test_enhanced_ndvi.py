#!/usr/bin/env python3
"""Test the enhanced NDVI endpoint directly"""
import requests
import json

# Test the enhanced NDVI endpoint
response = requests.get("http://localhost:8000/api/enhanced/satellite/ndvi?lat=40.7128&lon=-74.0060")

if response.status_code == 200:
    data = response.json()
    print("🛰️ Enhanced NDVI Endpoint Response:")
    print("=" * 50)
    print(json.dumps(data, indent=2))
    
    # Check the specific NDVI value
    ndvi_value = data.get('ndvi')
    if ndvi_value is not None:
        print(f"\n✅ SUCCESS: NDVI = {ndvi_value}")
    else:
        print(f"\n❌ NDVI is null, but we have other vegetation data")
        vegetation_data = data.get('vegetation_data', {})
        vegetation_health = vegetation_data.get('vegetation_health', {})
        if 'ndvi' in vegetation_health:
            print(f"🌿 NDVI in vegetation health: {vegetation_health['ndvi']}")
        
else:
    print(f"❌ Request failed: {response.status_code}")
    print(response.text)
