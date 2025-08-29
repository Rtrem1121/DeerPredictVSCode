#!/usr/bin/env python3
"""
Test Frontend Bedding Integration
=================================

Quick test to verify the frontend can display the enhanced bedding zones.
"""

import requests
import json

def test_frontend_backend_integration():
    """Test that frontend gets enhanced bedding data from backend"""
    
    print("🔗 Testing Frontend-Backend Integration with Enhanced Bedding Predictor")
    print("=" * 70)
    
    # Test the API call that the frontend makes
    test_data = {
        "lat": 43.3144,
        "lon": -73.2182,
        "date_time": "2025-08-28T17:00:00",
        "season": "early_season",
        "fast_mode": True
    }
    
    try:
        print("📡 Making API call to backend...")
        response = requests.post(
            "http://localhost:8000/predict",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful!")
            
            # Check response structure
            if data.get('success') and 'data' in data:
                prediction_data = data['data']
                print("✅ Enhanced API response structure confirmed")
                
                # Check bedding zones
                bedding_zones = prediction_data.get('bedding_zones', {})
                if bedding_zones and 'features' in bedding_zones:
                    zone_count = len(bedding_zones['features'])
                    print(f"🛌 Bedding Zones: {zone_count} zones found")
                    
                    if zone_count > 0:
                        # Show sample zone
                        sample_zone = bedding_zones['features'][0]
                        coords = sample_zone.get('geometry', {}).get('coordinates', [0, 0])
                        props = sample_zone.get('properties', {})
                        suitability = props.get('suitability_score', 0)
                        
                        print(f"   📍 Sample Zone: {coords[1]:.6f}, {coords[0]:.6f}")
                        print(f"   📈 Suitability: {suitability:.1f}%")
                        print("   ✅ Zones ready for frontend display!")
                        
                        # Check overall suitability
                        suitability_analysis = bedding_zones.get('properties', {}).get('suitability_analysis', {})
                        overall_score = suitability_analysis.get('overall_score', 0)
                        print(f"   🏆 Overall Score: {overall_score:.1f}%")
                        
                        if overall_score > 70:
                            print("   🎉 Enhanced bedding predictor working perfectly!")
                            return True
                        else:
                            print("   ⚠️ Scores lower than expected")
                            return False
                    else:
                        print("   ❌ No bedding zones in response")
                        return False
                else:
                    print("   ❌ No bedding_zones key in prediction data")
                    return False
            else:
                print(f"   ❌ Unexpected response structure: {list(data.keys())}")
                return False
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run the integration test"""
    success = test_frontend_backend_integration()
    
    print(f"\n🏁 FRONTEND INTEGRATION TEST RESULT")
    print("=" * 50)
    
    if success:
        print("✅ SUCCESS: Frontend can display enhanced bedding zones")
        print("🗺️ The map should now show the new bedding zone logic")
        print("🔗 Frontend URL: http://localhost:8501")
        print("📍 Test with Tinmouth coordinates: 43.3144, -73.2182")
    else:
        print("❌ FAILED: Frontend integration needs more work")
        print("🔧 Check the response structure and data handling")
    
    return success

if __name__ == "__main__":
    main()
