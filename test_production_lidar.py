#!/usr/bin/env python3
"""
Test Production API with LiDAR Integration

Verifies that the production API endpoint returns LiDAR terrain data
in the prediction results.
"""

import requests
import json
from datetime import datetime

# Production API endpoint (local Docker)
API_URL = "http://localhost:8000"

def test_production_lidar():
    """Test production API for LiDAR integration"""
    print("\n" + "="*80)
    print("🧪 Testing Production API with LiDAR Integration")
    print("="*80)
    
    # Test location (Vermont hunting spot)
    test_lat = 43.31181
    test_lon = -73.21624
    
    print(f"\n📍 Test Location: {test_lat}°N, {test_lon}°W")
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API: {API_URL}/predict")
    
    # Prepare request
    payload = {
        "lat": test_lat,
        "lon": test_lon,
        "date_time": datetime.now().isoformat(),
        "season": "fall",
        "fast_mode": False,
        "hunt_period": "AM",
        "include_camera_placement": False
    }
    
    print("\n🔍 Sending prediction request...")
    print("-" * 80)
    
    try:
        response = requests.post(
            f"{API_URL}/predict",
            json=payload,
            timeout=120  # 2 minute timeout for GEE processing
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Debug: Print full response structure
            print("\n🔍 DEBUG: Full API Response Structure:")
            print(json.dumps(result, indent=2, default=str)[:2000])  # First 2000 chars
            
            print("\n" + "="*80)
            print("📊 PRODUCTION API RESULTS")
            print("="*80)
            
            # Check for data wrapper
            data = result.get('data', result)
            
            # Check LiDAR integration
            gee_data = data.get('gee_data', {})
            lidar_terrain = gee_data.get('lidar_terrain')
            
            if lidar_terrain:
                print("\n✅ LiDAR TERRAIN DATA IN PRODUCTION!")
                print(f"   Resolution: {lidar_terrain['resolution_m']:.2f}m")
                print(f"   Data Source: {lidar_terrain['data_source']}")
                print(f"   File: {lidar_terrain['file']}")
                print(f"   Mean Elevation: {lidar_terrain['mean_elevation']:.1f}m")
                print(f"   Mean Slope: {lidar_terrain['mean_slope']:.1f}°")
                print(f"   Benches Found: {lidar_terrain['benches_count']}")
                print(f"   Saddles Found: {lidar_terrain['saddles_count']}")
            else:
                print("\n❌ No LiDAR terrain data in production response")
            
            # Check canopy data
            print(f"\n🌲 CANOPY COVERAGE:")
            print(f"   Coverage: {gee_data.get('canopy_coverage', 0)*100:.1f}%")
            print(f"   Source: {gee_data.get('canopy_data_source', 'unknown')}")
            print(f"   Resolution: {gee_data.get('canopy_resolution_m', 'N/A')}m")
            
            # Check bedding zones
            bedding_zones = data.get('bedding_zones', {})
            bedding_features = bedding_zones.get('features', [])
            print(f"\n🛏️ BEDDING ZONES:")
            print(f"   Zones Generated: {len(bedding_features)}")
            if bedding_features:
                avg_suitability = sum(f['properties']['suitability_score'] for f in bedding_features) / len(bedding_features)
                print(f"   Average Suitability: {avg_suitability:.1f}/100")
            
            # Check confidence
            confidence = data.get('confidence_score', 0)
            print(f"\n📈 CONFIDENCE SCORE: {confidence:.2f}")
            
            # Check version
            version = data.get('optimization_version', 'unknown')
            print(f"🔧 Version: {version}")
            
            print("\n" + "="*80)
            print("✅ VALIDATION:")
            print("="*80)
            
            checks = [
                ("LiDAR Integration", lidar_terrain is not None),
                ("Real Canopy (Sentinel-2/Landsat)", gee_data.get('canopy_data_source') in ['sentinel2', 'landsat8']),
                ("Bedding Zones Generated", len(bedding_features) > 0),
                ("High Confidence (>0.8)", confidence > 0.8),
                ("Version Updated (v3.1)", 'lidar' in version.lower())
            ]
            
            for check_name, passed in checks:
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"   {status}: {check_name}")
            
            all_passed = all(passed for _, passed in checks)
            
            if all_passed:
                print("\n🎉 PRODUCTION API TEST PASSED! LiDAR integration deployed successfully!")
            else:
                print("\n⚠️ Some checks failed - review above")
            
            return all_passed
            
        else:
            print(f"\n❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n⏱️ Request timed out (GEE processing can take time)")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = test_production_lidar()
    sys.exit(0 if success else 1)
