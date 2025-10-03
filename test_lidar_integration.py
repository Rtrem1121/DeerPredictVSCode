#!/usr/bin/env python3
"""
Test LiDAR Integration with Bedding Zone Predictor

Verifies that LiDAR terrain data (35cm resolution) is properly integrated
into the prediction pipeline.
"""

import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

def test_lidar_integration():
    """Test LiDAR integration with real prediction"""
    print("\n" + "="*80)
    print("🧪 Testing LiDAR Integration with Bedding Zone Predictor")
    print("="*80)
    
    # Import predictor
    from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor
    
    # Test location (Vermont hunting spot from recent production test)
    test_lat = 43.31181
    test_lon = -73.21624
    
    print(f"\n📍 Test Location: {test_lat}°N, {test_lon}°W")
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create predictor
    predictor = EnhancedBeddingZonePredictor()
    
    # Run enhanced analysis
    print("\n🔍 Running enhanced biological analysis with LiDAR integration...")
    print("-" * 80)
    
    result = predictor.run_enhanced_biological_analysis(
        lat=test_lat,
        lon=test_lon,
        time_of_day=7,  # 7 AM
        season="fall",
        hunting_pressure="medium",
        target_datetime=datetime.now()
    )
    
    print("\n" + "="*80)
    print("📊 RESULTS")
    print("="*80)
    
    # Check LiDAR integration
    gee_data = result.get('gee_data', {})
    lidar_terrain = gee_data.get('lidar_terrain')
    
    if lidar_terrain:
        print("\n✅ LiDAR TERRAIN DATA INTEGRATED!")
        print(f"   Resolution: {lidar_terrain['resolution_m']:.2f}m")
        print(f"   Data Source: {lidar_terrain['data_source']}")
        print(f"   File: {lidar_terrain['file']}")
        print(f"   Mean Elevation: {lidar_terrain['mean_elevation']:.1f}m")
        print(f"   Mean Slope: {lidar_terrain['mean_slope']:.1f}°")
        print(f"   Benches Found: {lidar_terrain['benches_count']}")
        print(f"   Saddles Found: {lidar_terrain['saddles_count']}")
        
        if lidar_terrain['benches_count'] > 0:
            print(f"\n   📌 Bench Details:")
            for i, bench in enumerate(lidar_terrain['benches'][:3], 1):  # Show first 3
                print(f"      Bench {i}: {bench['pixel_count']} pixels ({bench['percentage']:.1f}% of area)")
    else:
        print("\n❌ No LiDAR terrain data (using SRTM 30m fallback)")
    
    # Check canopy data
    print(f"\n🌲 CANOPY COVERAGE:")
    print(f"   Coverage: {gee_data.get('canopy_coverage', 0)*100:.1f}%")
    print(f"   Source: {gee_data.get('canopy_data_source', 'unknown')}")
    print(f"   Resolution: {gee_data.get('canopy_resolution_m', 'N/A')}m")
    
    # Check bedding zones
    bedding_zones = result.get('bedding_zones', {})
    bedding_features = bedding_zones.get('features', [])
    print(f"\n🛏️ BEDDING ZONES:")
    print(f"   Zones Generated: {len(bedding_features)}")
    if bedding_features:
        avg_suitability = sum(f['properties']['suitability_score'] for f in bedding_features) / len(bedding_features)
        print(f"   Average Suitability: {avg_suitability:.1f}/100")
    
    # Check confidence
    confidence = result.get('confidence_score', 0)
    print(f"\n📈 CONFIDENCE SCORE: {confidence:.2f}")
    
    # Check version
    version = result.get('optimization_version', 'unknown')
    print(f"🔧 Version: {version}")
    
    # Analysis time
    analysis_time = result.get('analysis_time', 0)
    print(f"⏱️ Analysis Time: {analysis_time:.2f}s")
    
    print("\n" + "="*80)
    
    # Validation
    print("\n✅ VALIDATION:")
    checks = [
        ("LiDAR Integration", lidar_terrain is not None),
        ("Real Canopy (Sentinel-2/Landsat)", gee_data.get('canopy_data_source') in ['sentinel2', 'landsat8']),
        ("Bedding Zones Generated", len(bedding_features) > 0),
        ("High Confidence (>0.8)", confidence > 0.8),
        ("Version Updated", 'lidar' in version.lower())
    ]
    
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {check_name}")
    
    all_passed = all(passed for _, passed in checks)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! LiDAR integration successful!")
    else:
        print("\n⚠️ Some tests failed - review above")
    
    return all_passed


if __name__ == "__main__":
    success = test_lidar_integration()
    sys.exit(0 if success else 1)
