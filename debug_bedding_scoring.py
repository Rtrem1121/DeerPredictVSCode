#!/usr/bin/env python3
"""
Debug Enhanced Bedding Zone Scoring

Debug the scoring logic to understand why locations aren't meeting criteria
"""

from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor
import logging

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def debug_bedding_scoring():
    """Debug the bedding zone scoring for multiple locations"""
    print("🔍 DEBUGGING BEDDING ZONE SCORING")
    print("=" * 50)
    
    predictor = EnhancedBeddingZonePredictor()
    
    # Test multiple locations in Vermont
    test_locations = [
        {"name": "Tinmouth Valley", "lat": 43.3127, "lon": -73.2271},
        {"name": "Green Mountains", "lat": 43.4100, "lon": -72.9500},
        {"name": "Mad River Valley", "lat": 44.1264, "lon": -72.8092},
        {"name": "Northeast Kingdom", "lat": 44.5588, "lon": -72.1234}
    ]
    
    for location in test_locations:
        print(f"\n🗺️ Testing: {location['name']}")
        print(f"📍 Coordinates: {location['lat']}, {location['lon']}")
        print("─" * 40)
        
        try:
            # Get environmental data
            gee_data = predictor.get_dynamic_gee_data_enhanced(location['lat'], location['lon'])
            osm_data = predictor.get_osm_road_proximity(location['lat'], location['lon'])
            weather_data = predictor.get_enhanced_weather_with_trends(location['lat'], location['lon'])
            
            # Evaluate suitability in detail
            suitability = predictor.evaluate_bedding_suitability(gee_data, osm_data, weather_data)
            
            print("📊 CRITERIA SCORES:")
            for score_name, score_value in suitability["scores"].items():
                print(f"   {score_name.replace('_', ' ').title()}: {score_value:.1f}%")
            
            print(f"\n📈 OVERALL SCORE: {suitability['overall_score']:.1f}%")
            print(f"✅ MEETS CRITERIA: {suitability['meets_criteria']}")
            
            print("\n🔍 RAW CRITERIA VALUES:")
            criteria = suitability["criteria"]
            thresholds = suitability["thresholds"]
            
            print(f"   🌲 Canopy: {criteria['canopy_coverage']:.1%} (need >{thresholds['min_canopy']:.0%})")
            print(f"   🛣️ Roads: {criteria['road_distance']:.0f}m (need >{thresholds['min_road_distance']}m)")
            print(f"   🏔️ Slope: {criteria['slope']:.1f}° (need {thresholds['min_slope']}-{thresholds['max_slope']}°)")
            print(f"   🧭 Aspect: {criteria['aspect']:.0f}° (optimal {thresholds['optimal_aspect_min']}-{thresholds['optimal_aspect_max']}°)")
            print(f"   💨 Wind Dir: {criteria['wind_direction']:.0f}°")
            print(f"   🌡️ Temperature: {criteria['temperature']:.1f}°F")
            
            # Check which criteria are failing
            print("\n❌ FAILING CRITERIA:")
            fails = []
            if criteria['canopy_coverage'] <= thresholds['min_canopy']:
                fails.append(f"Canopy too low: {criteria['canopy_coverage']:.1%}")
            if criteria['road_distance'] <= thresholds['min_road_distance']:
                fails.append(f"Too close to roads: {criteria['road_distance']:.0f}m")
            if not (thresholds['min_slope'] <= criteria['slope'] <= thresholds['max_slope']):
                fails.append(f"Slope unsuitable: {criteria['slope']:.1f}°")
            if suitability['overall_score'] < 70:
                fails.append(f"Overall score too low: {suitability['overall_score']:.1f}%")
            
            if fails:
                for fail in fails:
                    print(f"   • {fail}")
            else:
                print("   ✅ All criteria met!")
                
        except Exception as e:
            print(f"❌ Error testing {location['name']}: {e}")
        
        print("=" * 50)

if __name__ == "__main__":
    debug_bedding_scoring()
