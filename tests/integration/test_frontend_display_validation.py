"""
Simple Frontend Display Validation Test
Validates that enhanced bedding predictor data is flowing correctly to frontend
"""

import requests
import json
import sys
from datetime import datetime

def test_backend_frontend_integration():
    """Test the complete backend-frontend data flow"""
    
    print("🎯 ENHANCED BEDDING PREDICTOR - FRONTEND DISPLAY VALIDATION")
    print("=" * 70)
    
    # Test coordinates - Tinmouth, Vermont
    test_lat = 43.3145
    test_lon = -73.2175
    
    print(f"📍 Testing Location: Tinmouth, Vermont")
    print(f"   Coordinates: {test_lat:.6f}, {test_lon:.6f}")
    print(f"   Season: early_season")
    
    try:
        # Test backend API
        print("\n🧪 Step 1: Testing Backend API...")
        
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
        
        print("✅ Backend API accessible")
        
        # Parse response
        response_data = response.json()
        
        # Handle both API formats
        if 'success' in response_data and response_data.get('success'):
            prediction_data = response_data.get('data', response_data)
            print("✅ New enhanced API format detected")
        else:
            prediction_data = response_data
            print("✅ Direct prediction format detected")
        
        # Validate bedding zones
        print("\n🛏️ Step 2: Validating Bedding Zone Data...")
        
        bedding_zones = prediction_data.get('bedding_zones', {})
        
        if not bedding_zones:
            print("❌ No bedding zones found in response")
            return False
        
        # Check for GeoJSON format (EnhancedBeddingZonePredictor signature)
        if 'features' in bedding_zones:
            features = bedding_zones['features']
            zone_count = len(features)
            
            print(f"✅ Found {zone_count} bedding zones in GeoJSON format")
            
            # Extract suitability score
            properties = bedding_zones.get('properties', {})
            suitability_analysis = properties.get('suitability_analysis', {})
            overall_score = suitability_analysis.get('overall_score', 0)
            
            print(f"✅ Overall Suitability: {overall_score:.1f}%")
            
            # Check individual zones
            print("\n📊 Bedding Zone Details:")
            for i, feature in enumerate(features, 1):
                coords = feature.get('geometry', {}).get('coordinates', [])
                props = feature.get('properties', {})
                score = props.get('score', 0)
                
                if len(coords) == 2:
                    lat, lon = coords[1], coords[0]  # GeoJSON is [lon, lat]
                    print(f"   Zone {i}: {lat:.6f}, {lon:.6f} (Score: {score:.1f})")
            
            # Validate frontend display readiness
            print("\n🖥️ Step 3: Frontend Display Validation...")
            
            frontend_ready = True
            frontend_issues = []
            
            # Check GeoJSON structure for map rendering
            for i, feature in enumerate(features, 1):
                geometry = feature.get('geometry', {})
                properties = feature.get('properties', {})
                
                if not geometry.get('coordinates'):
                    frontend_ready = False
                    frontend_issues.append(f"Zone {i} missing coordinates")
                
                if not properties:
                    frontend_issues.append(f"Zone {i} missing properties for tooltip")
            
            if frontend_ready:
                print("✅ GeoJSON structure valid for map rendering")
                print(f"✅ Expected frontend display: {zone_count} green bedding pins")
                print(f"✅ Expected tooltips with suitability: {overall_score:.1f}%")
            else:
                print("❌ Frontend display issues detected:")
                for issue in frontend_issues:
                    print(f"   • {issue}")
            
            # Check stand recommendations
            mature_buck = prediction_data.get('mature_buck_analysis', {})
            stand_recs = mature_buck.get('stand_recommendations', [])
            
            if stand_recs:
                print(f"✅ Found {len(stand_recs)} stand recommendations")
                print(f"✅ Expected frontend display: {len(stand_recs)} red stand pins")
            
            # Final assessment
            print("\n🎯 FINAL ASSESSMENT:")
            
            if zone_count >= 3 and overall_score >= 90:
                print("✅ EXCELLENT: Meets user expectations (3+ zones, 90%+ suitability)")
            elif zone_count >= 2 and overall_score >= 70:
                print("✅ GOOD: Solid performance")
            elif zone_count >= 1:
                print("⚠️ FAIR: Some bedding zones generated but below expectations")
            else:
                print("❌ POOR: No bedding zones generated")
            
            print(f"\n📋 Summary for Frontend:")
            print(f"   • Bedding Zones: {zone_count} (expect {zone_count} green pins)")
            print(f"   • Suitability: {overall_score:.1f}% (show in tooltips)")
            print(f"   • Stand Sites: {len(stand_recs)} (expect {len(stand_recs)} red pins)")
            print(f"   • API Format: Enhanced with GeoJSON structure")
            
            # Success criteria
            success = (
                zone_count >= 3 and 
                overall_score >= 90 and 
                frontend_ready and
                len(stand_recs) >= 1
            )
            
            if success:
                print("\n🎉 VALIDATION PASSED: Backend data ready for excellent frontend display!")
                return True
            else:
                print("\n⚠️ VALIDATION ISSUES: Frontend may not display optimally")
                return False
        
        else:
            print("❌ Bedding zones not in expected GeoJSON format")
            print("   This suggests EnhancedBeddingZonePredictor may not be active")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend API at http://127.0.0.1:8000")
        print("   Please ensure the backend is running with: docker-compose up")
        return False
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_backend_frontend_integration()
    
    if success:
        print("\n✅ Ready for frontend display! The enhanced bedding predictor data")
        print("   should render as green bedding pins with accurate tooltips.")
    else:
        print("\n❌ Issues detected. Frontend may not display backend data correctly.")
    
    sys.exit(0 if success else 1)
