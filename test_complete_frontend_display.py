#!/usr/bin/env python3
"""
Complete Frontend Display Test
Tests that all 10 markers (3+3+3+1) are displayed correctly on the frontend
"""

import requests
import json
import sys
from datetime import datetime

def test_complete_frontend_integration():
    """Test that all site types display correctly on the frontend"""
    
    print("🎯 COMPLETE FRONTEND DISPLAY TEST (ALL 10 MARKERS)")
    print("=" * 70)
    
    # Test coordinates - Tinmouth, Vermont
    test_lat = 43.3145
    test_lon = -73.2175
    
    print(f"📍 Testing Location: Tinmouth, Vermont")
    print(f"   Coordinates: {test_lat:.6f}, {test_lon:.6f}")
    print(f"   Season: early_season")
    
    try:
        # Test backend API with enhanced site generation
        print("\n🧪 Step 1: Testing Enhanced Backend API...")
        
        response = requests.post(
            "http://127.0.0.1:8000/predict",
            json={
                "lat": test_lat,
                "lon": test_lon,
                "date_time": f"{datetime.now().date()}T07:00:00",
                "season": "early_season",
                "fast_mode": True
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Backend API Error: {response.status_code} - {response.text}")
            return False
        
        print("✅ Enhanced Backend API accessible")
        
        # Parse response
        response_data = response.json()
        
        # Handle both API formats
        if 'success' in response_data and response_data.get('success'):
            prediction_data = response_data.get('data', response_data)
            print("✅ Enhanced API format detected")
        else:
            prediction_data = response_data
            print("✅ Direct prediction format detected")
        
        # Validate all site types
        print("\n🛏️ Step 2: Validating BEDDING ZONES...")
        bedding_zones = prediction_data.get('bedding_zones', {})
        bedding_count = len(bedding_zones.get('features', [])) if bedding_zones else 0
        print(f"   Found: {bedding_count}/3 bedding zones")
        
        print("\n🎯 Step 3: Validating STAND SITES...")
        mature_buck = prediction_data.get('mature_buck_analysis', {})
        stand_recs = mature_buck.get('stand_recommendations', []) if mature_buck else []
        stand_count = len(stand_recs)
        print(f"   Found: {stand_count}/3 stand recommendations")
        
        print("\n🌾 Step 4: Validating FEEDING AREAS...")
        feeding_areas = prediction_data.get('feeding_areas', {})
        feeding_count = len(feeding_areas.get('features', [])) if feeding_areas else 0
        print(f"   Found: {feeding_count}/3 feeding areas")
        
        print("\n📷 Step 5: Validating CAMERA PLACEMENT...")
        camera_placement = prediction_data.get('optimal_camera_placement', {})
        camera_count = 1 if camera_placement and camera_placement.get('coordinates') else 0
        print(f"   Found: {camera_count}/1 camera placement")
        
        # Calculate totals
        total_sites = bedding_count + stand_count + feeding_count + camera_count
        
        print("\n📊 FRONTEND DISPLAY SUMMARY:")
        print("=" * 50)
        print(f"🛏️ Bedding Zones: {bedding_count}/3 {'✅' if bedding_count >= 3 else '❌'}")
        print(f"🎯 Stand Sites: {stand_count}/3 {'✅' if stand_count >= 3 else '❌'}")
        print(f"🌾 Feeding Areas: {feeding_count}/3 {'✅' if feeding_count >= 3 else '❌'}")
        print(f"📷 Camera Sites: {camera_count}/1 {'✅' if camera_count >= 1 else '❌'}")
        print("=" * 50)
        print(f"📈 Total Sites: {total_sites}/10 {'✅' if total_sites == 10 else '❌'}")
        
        # Frontend rendering expectations
        print("\n🖥️ EXPECTED FRONTEND DISPLAY:")
        print("=" * 50)
        
        if bedding_count >= 3:
            suitability = bedding_zones.get('properties', {}).get('suitability_analysis', {}).get('overall_score', 0)
            print(f"✅ {bedding_count} GREEN bedding pins with {suitability:.1f}% suitability tooltips")
        else:
            print(f"❌ Missing {3 - bedding_count} bedding zones")
            
        if stand_count >= 3:
            print(f"✅ {stand_count} RED stand pins with confidence scores")
            for i, stand in enumerate(stand_recs[:3], 1):
                stand_type = stand.get('type', 'Unknown')
                confidence = stand.get('confidence', 0)
                print(f"   Stand {i}: {stand_type} ({confidence:.1f}% confidence)")
        else:
            print(f"❌ Missing {3 - stand_count} stand sites")
            
        if feeding_count >= 3:
            print(f"✅ {feeding_count} BLUE/ORANGE feeding pins")
        else:
            print(f"❌ Missing {3 - feeding_count} feeding areas")
            
        if camera_count >= 1:
            camera_confidence = camera_placement.get('confidence', 0)
            print(f"✅ 1 PURPLE camera pin ({camera_confidence:.1f}% confidence)")
        else:
            print(f"❌ Missing camera placement")
        
        # Success assessment
        all_requirements_met = (
            bedding_count >= 3 and 
            stand_count >= 3 and 
            feeding_count >= 3 and 
            camera_count >= 1
        )
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        if all_requirements_met:
            print("🎉 SUCCESS: All 10 site markers should display on frontend!")
            print("   Ready for Playwright validation testing")
        else:
            missing = []
            if bedding_count < 3:
                missing.append(f"{3-bedding_count} bedding zones")
            if stand_count < 3:
                missing.append(f"{3-stand_count} stand sites")
            if feeding_count < 3:
                missing.append(f"{3-feeding_count} feeding areas")
            if camera_count < 1:
                missing.append("1 camera site")
            print(f"⚠️ INCOMPLETE: Missing {', '.join(missing)}")
        
        return all_requirements_met
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend API at http://127.0.0.1:8000")
        print("   Please ensure the backend is running with: docker-compose up")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_frontend_integration()
    
    if success:
        print("\n✅ Complete frontend display test PASSED!")
        print("   All 10 markers should be visible on the map.")
        print("   Ready to run Playwright validation.")
    else:
        print("\n❌ Complete frontend display test FAILED!")
        print("   Some markers are missing from backend response.")
    
    sys.exit(0 if success else 1)
