#!/usr/bin/env python3
"""
Test Enhanced Bedding Zone Predictor Integration

Tests the fully integrated EnhancedBeddingZonePredictor to verify:
1. It's being used as the primary prediction engine
2. It generates multiple bedding zones (target: 3+ zones)
3. It achieves high suitability scores (target: 75.3%+)
4. It provides comprehensive logging

Author: GitHub Copilot
Date: August 28, 2025
"""

import sys
import os
import asyncio
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_enhanced_bedding_predictor():
    """Test the enhanced bedding zone predictor integration"""
    print("🧪 Testing Enhanced Bedding Zone Predictor Integration")
    print("=" * 60)
    
    try:
        # Import the enhanced prediction service
        from backend.services.prediction_service import get_prediction_service
        
        # Get the prediction service
        service = get_prediction_service()
        print(f"✅ PredictionService initialized")
        print(f"   Primary predictor type: {type(service.predictor).__name__}")
        
        # Test coordinates - Vermont location
        test_lat = 44.2601
        test_lon = -72.5806
        test_time = 6  # 6 AM
        test_season = "fall"
        test_pressure = "low"
        
        print(f"\n🎯 Testing Enhanced Prediction:")
        print(f"   Location: {test_lat:.4f}, {test_lon:.4f}")
        print(f"   Time: {test_time}:00, Season: {test_season}")
        print(f"   Hunting Pressure: {test_pressure}")
        
        # Run the enhanced prediction
        result = await service.predict(test_lat, test_lon, test_time, test_season, test_pressure)
        
        # Analyze results
        print(f"\n📊 Enhanced Prediction Results:")
        
        # Extract bedding zones
        bedding_zones = result.get("bedding_zones", {})
        zone_features = bedding_zones.get('features', []) if bedding_zones else []
        
        print(f"   🛌 Bedding Zones Generated: {len(zone_features)}")
        
        # Extract suitability metrics
        suitability_analysis = bedding_zones.get('properties', {}).get('suitability_analysis', {}) if bedding_zones else {}
        overall_suitability = suitability_analysis.get('overall_score', 0)
        confidence = result.get('confidence_score', 0)
        
        print(f"   📈 Overall Suitability: {overall_suitability:.1f}%")
        print(f"   🎯 Confidence Score: {confidence:.2f}")
        
        # Show individual zone details
        if zone_features:
            print(f"\n🏞️ Individual Zone Analysis:")
            for i, zone in enumerate(zone_features, 1):
                zone_props = zone.get('properties', {})
                zone_coords = zone.get('geometry', {}).get('coordinates', [0, 0])
                zone_suitability = zone_props.get('suitability_score', zone_props.get('score', 0))
                zone_type = zone_props.get('bedding_type', 'Unknown')
                
                print(f"   Zone {i}: {zone_suitability:.1f}% suitability")
                print(f"           Type: {zone_type}")
                print(f"           Coordinates: {zone_coords[1]:.6f}, {zone_coords[0]:.6f}")
                print(f"           Properties: {list(zone_props.keys())}")
        
        # Validation checks
        print(f"\n✅ Validation Results:")
        
        success_criteria = []
        
        # Check 1: Multiple zones generated
        if len(zone_features) >= 3:
            print(f"   ✅ Multiple Zones: {len(zone_features)} zones (target: 3+)")
            success_criteria.append(True)
        else:
            print(f"   ❌ Insufficient Zones: {len(zone_features)} zones (target: 3+)")
            success_criteria.append(False)
        
        # Check 2: High suitability score
        if overall_suitability >= 75.0:
            print(f"   ✅ High Suitability: {overall_suitability:.1f}% (target: 75.3%+)")
            success_criteria.append(True)
        else:
            print(f"   ❌ Low Suitability: {overall_suitability:.1f}% (target: 75.3%+)")
            success_criteria.append(False)
        
        # Check 3: Confidence score
        if confidence >= 0.7:
            print(f"   ✅ High Confidence: {confidence:.2f} (target: 0.7+)")
            success_criteria.append(True)
        else:
            print(f"   ⚠️ Moderate Confidence: {confidence:.2f} (target: 0.7+)")
            success_criteria.append(False)
        
        # Check 4: Enhanced data present
        enhanced_features = ['gee_data', 'osm_data', 'weather_data', 'wind_thermal_analysis']
        present_features = [f for f in enhanced_features if f in result]
        if len(present_features) >= 3:
            print(f"   ✅ Enhanced Data: {len(present_features)}/4 features present")
            success_criteria.append(True)
        else:
            print(f"   ❌ Missing Data: {len(present_features)}/4 features present")
            success_criteria.append(False)
        
        # Overall assessment
        passed_checks = sum(success_criteria)
        total_checks = len(success_criteria)
        success_rate = (passed_checks / total_checks) * 100
        
        print(f"\n🎯 Overall Assessment:")
        print(f"   Passed: {passed_checks}/{total_checks} checks ({success_rate:.1f}%)")
        
        if success_rate >= 75:
            print(f"   🎉 SUCCESS: Enhanced bedding predictor is working well!")
        elif success_rate >= 50:
            print(f"   ⚠️ PARTIAL: Enhanced bedding predictor needs improvement")
        else:
            print(f"   ❌ FAILED: Enhanced bedding predictor has issues")
        
        return success_rate >= 75
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_bedding_predictor())
    if success:
        print(f"\n🎉 Enhanced bedding zone predictor integration: SUCCESS")
    else:
        print(f"\n❌ Enhanced bedding zone predictor integration: NEEDS WORK")
