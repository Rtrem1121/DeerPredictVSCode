#!/usr/bin/env python3
"""
Test the fixed satellite integration with improved NDVI method
"""
import requests
import json

def test_satellite_integration():
    print("🧪 Testing Fixed Satellite Integration")
    print("=" * 50)
    
    # Test data - known hunting location
    test_data = {
        "lat": 40.7128,
        "lon": -74.0060,
        "date_time": "2025-08-15T12:00:00",
        "season": "early_season",
        "fast_mode": False
    }
    
    try:
        print("📡 Making API request to test satellite integration...")
        response = requests.post(
            "http://localhost:8000/predict",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("🔍 Full API Response Structure:")
            print(f"Keys: {list(result.keys())}")
            
            # Check if vegetation analysis worked
            vegetation = result.get('environmental_factors', {}).get('vegetation_analysis')
            if vegetation:
                ndvi_analysis = vegetation.get('ndvi_analysis', {})
                ndvi_value = ndvi_analysis.get('ndvi_value')
                
                if ndvi_value is not None:
                    print("✅ SUCCESS: Satellite integration working!")
                    print(f"🛰️ NDVI Value: {ndvi_value}")
                    print(f"🌱 Vegetation Health: {ndvi_analysis.get('vegetation_health')}")
                    print(f"📸 Images Used: {ndvi_analysis.get('image_count')}")
                    print(f"🎯 Strategy: {ndvi_analysis.get('strategy_used')}")
                    print(f"📅 Date Range: {ndvi_analysis.get('date_range_days')} days")
                    return True
                else:
                    print("❌ FAILED: NDVI value is None")
                    print(f"🔍 NDVI Analysis: {json.dumps(ndvi_analysis, indent=2)}")
            else:
                print("❌ FAILED: No vegetation analysis in response")
                print(f"🔍 Environmental factors: {result.get('environmental_factors', {}).keys()}")
                
                # Look for any vegetation-related data
                env_factors = result.get('environmental_factors', {})
                for key, value in env_factors.items():
                    if 'vegetation' in key.lower() or 'ndvi' in key.lower():
                        print(f"🌿 Found vegetation data in '{key}': {value}")
        else:
            print(f"❌ API Request Failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing satellite integration: {e}")
    
    return False

if __name__ == "__main__":
    success = test_satellite_integration()
    if success:
        print("\n🎉 Satellite integration fix successful!")
    else:
        print("\n💥 Satellite integration still not working")
