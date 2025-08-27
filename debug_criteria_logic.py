#!/usr/bin/env python3
"""
Quick debug of the bedding zone criteria logic
"""

from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def debug_criteria_logic():
    print("🔍 DEBUGGING BEDDING ZONE CRITERIA LOGIC")
    print("=" * 50)
    
    predictor = EnhancedBeddingZonePredictor()
    lat, lon = 43.3127, -73.2271
    
    # Get data
    gee_data = predictor.get_dynamic_gee_data_enhanced(lat, lon)
    osm_data = predictor.get_osm_road_proximity(lat, lon)
    weather_data = predictor.get_enhanced_weather_with_trends(lat, lon)
    
    # Evaluate suitability
    suitability = predictor.evaluate_bedding_suitability(gee_data, osm_data, weather_data)
    
    criteria = suitability["criteria"]
    thresholds = suitability["thresholds"]
    
    print("📊 DETAILED CRITERIA ANALYSIS:")
    print(f"   🌲 Canopy: {criteria['canopy_coverage']:.1%} (threshold: >{thresholds['min_canopy']:.0%})")
    print(f"      ✅ Passes: {criteria['canopy_coverage'] > thresholds['min_canopy']}")
    
    print(f"   🛣️ Roads: {criteria['road_distance']:.0f}m (threshold: >{thresholds['min_road_distance']}m)")
    print(f"      ✅ Passes: {criteria['road_distance'] > thresholds['min_road_distance']}")
    
    print(f"   🏔️ Slope: {criteria['slope']:.1f}° (range: {thresholds['min_slope']}-{thresholds['max_slope']}°)")
    slope_ok = thresholds['min_slope'] <= criteria['slope'] <= thresholds['max_slope']
    print(f"      ✅ Passes: {slope_ok}")
    
    print(f"   📊 Overall: {suitability['overall_score']:.1f}% (threshold: >70%)")
    overall_ok = suitability['overall_score'] >= 70
    print(f"      ✅ Passes: {overall_ok}")
    
    print(f"\n🎯 MEETS_CRITERIA: {suitability['meets_criteria']}")
    
    print("\n📋 INDIVIDUAL SCORES:")
    for score_name, score_value in suitability["scores"].items():
        print(f"   {score_name.replace('_', ' ').title()}: {score_value:.1f}%")

if __name__ == "__main__":
    debug_criteria_logic()
