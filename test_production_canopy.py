#!/usr/bin/env python3
"""
Production Canopy Integration Test

Tests if the Docker backend is using real satellite canopy data
by making an API call and checking for new canopy fields.

Author: GitHub Copilot
Date: October 2, 2025
"""

import requests
import json
import sys
from datetime import datetime

def test_production_canopy(lat=43.31157, lon=-73.21577):
    """
    Test production API for real canopy integration
    
    Args:
        lat: Test latitude (default: Vermont)
        lon: Test longitude (default: Vermont)
    """
    print("=" * 80)
    print("🧪 PRODUCTION CANOPY INTEGRATION TEST")
    print("=" * 80)
    print(f"\n📍 Test Location: {lat:.5f}°N, {lon:.5f}°W")
    print(f"🕐 Timestamp: {datetime.now().isoformat()}")
    
    # API endpoint (adjust if needed)
    api_url = "http://localhost:8000/api/v1/predict"
    
    payload = {
        "lat": lat,
        "lon": lon,
        "season": "early_season"
    }
    
    print(f"\n🌐 Calling API: {api_url}")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(api_url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        print("\n" + "=" * 80)
        print("✅ API RESPONSE RECEIVED")
        print("=" * 80)
        
        # Extract GEE data
        gee_data = result.get('gee_data', {})
        
        print("\n🏔️  GEE DATA ANALYSIS:")
        print("-" * 80)
        print(f"  Canopy Coverage: {gee_data.get('canopy_coverage', 'N/A')}")
        print(f"  Data Source: {gee_data.get('data_source', 'N/A')}")
        
        # Check for NEW canopy fields
        canopy_source = gee_data.get('canopy_data_source')
        thermal_cover = gee_data.get('thermal_cover_type')
        canopy_grid = gee_data.get('canopy_grid')
        conifer_pct = gee_data.get('conifer_percentage')
        resolution = gee_data.get('canopy_resolution_m')
        
        print("\n🌲 CANOPY INTEGRATION FIELDS:")
        print("-" * 80)
        
        # Track validation results
        passed = 0
        failed = 0
        
        # Test 1: Canopy Data Source
        if canopy_source:
            print(f"  ✅ canopy_data_source: {canopy_source}")
            passed += 1
        else:
            print(f"  ❌ canopy_data_source: MISSING")
            failed += 1
        
        # Test 2: Thermal Cover Type
        if thermal_cover:
            print(f"  ✅ thermal_cover_type: {thermal_cover}")
            passed += 1
        else:
            print(f"  ❌ thermal_cover_type: MISSING")
            failed += 1
        
        # Test 3: Canopy Grid
        if canopy_grid:
            grid_size = len(canopy_grid) if isinstance(canopy_grid, list) else 0
            print(f"  ✅ canopy_grid: {grid_size}x{grid_size} array")
            passed += 1
        else:
            print(f"  ❌ canopy_grid: MISSING")
            failed += 1
        
        # Test 4: Conifer Percentage
        if conifer_pct is not None:
            print(f"  ✅ conifer_percentage: {conifer_pct:.1%}")
            passed += 1
        else:
            print(f"  ❌ conifer_percentage: MISSING")
            failed += 1
        
        # Test 5: Canopy Resolution
        if resolution:
            print(f"  ✅ canopy_resolution_m: {resolution}m")
            passed += 1
        else:
            print(f"  ❌ canopy_resolution_m: MISSING")
            failed += 1
        
        # Extract bedding zones
        bedding_zones = result.get('bedding_zones', {})
        features = bedding_zones.get('features', [])
        
        print("\n🛏️  BEDDING ZONES:")
        print("-" * 80)
        print(f"  Total Zones: {len(features)}")
        
        if features:
            for i, zone in enumerate(features[:3], 1):
                props = zone.get('properties', {})
                canopy = props.get('canopy_coverage', 0)
                score = props.get('suitability_score', 0)
                confidence = props.get('confidence', 0)
                print(f"  Zone {i}: Canopy={canopy:.1%}, Score={score:.0f}, Confidence={confidence:.2f}")
        
        # Final verdict
        print("\n" + "=" * 80)
        print("📊 INTEGRATION TEST RESULTS")
        print("=" * 80)
        print(f"  ✅ Tests Passed: {passed}/5")
        print(f"  ❌ Tests Failed: {failed}/5")
        
        if failed == 0:
            print("\n🎉 SUCCESS! Real canopy integration is ACTIVE in production!")
            print("\n📝 Evidence:")
            print(f"  - Canopy source: {canopy_source} (Sentinel-2 or Landsat 8)")
            print(f"  - Spatial grid: {grid_size}x{grid_size} = {grid_size**2} cells")
            print(f"  - Thermal cover: {thermal_cover} classification")
            print(f"  - Resolution: {resolution}m satellite imagery")
            return True
        else:
            print("\n⚠️ PARTIAL INTEGRATION - Some canopy fields missing")
            print("\n🔍 Troubleshooting:")
            print("  1. Check backend logs: docker logs deer_pred_app-backend-1")
            print("  2. Verify VegetationAnalyzer initialization")
            print("  3. Check GEE authentication in Docker container")
            print("  4. Rebuild Docker: docker-compose build --no-cache")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API REQUEST FAILED: {e}")
        print("\n🔍 Troubleshooting:")
        print("  1. Check if Docker containers are running: docker ps")
        print("  2. Start containers: docker-compose up -d")
        print("  3. Check backend logs: docker logs deer_pred_app-backend-1")
        return False
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


if __name__ == "__main__":
    # Run test
    success = test_production_canopy()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
