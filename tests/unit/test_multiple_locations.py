#!/usr/bin/env python3
"""
Test Enhanced Bedding Zone Prediction Across Multiple Vermont Locations

Tests the enhanced bedding zone predictor across various Vermont locations
to find areas that naturally meet biological criteria for mature buck bedding.
"""

from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor
import logging
import time

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_multiple_locations():
    """Test bedding zone prediction across diverse Vermont locations"""
    print("🗺️ TESTING MULTIPLE VERMONT LOCATIONS")
    print("=" * 60)
    
    predictor = EnhancedBeddingZonePredictor()
    
    # Diverse Vermont test locations with different terrain characteristics
    test_locations = [
        {
            "name": "Tinmouth Valley (Current)",
            "lat": 43.3127, 
            "lon": -73.2271,
            "description": "Current test location - valley terrain"
        },
        {
            "name": "Green Mountain Ridge",
            "lat": 43.4100, 
            "lon": -72.9500,
            "description": "Mountain ridge - higher elevation, steeper slopes"
        },
        {
            "name": "Mad River Valley",
            "lat": 44.1264, 
            "lon": -72.8092,
            "description": "Protected valley with mixed terrain"
        },
        {
            "name": "Northeast Kingdom Hills",
            "lat": 44.5588, 
            "lon": -72.1234,
            "description": "Rolling hills, remote area"
        },
        {
            "name": "Worcester Range",
            "lat": 44.3567, 
            "lon": -72.5234,
            "description": "Mountain range with varied slopes"
        },
        {
            "name": "Mount Tabor Area",
            "lat": 43.3234, 
            "lon": -73.0567,
            "description": "Forested hills near Rutland"
        },
        {
            "name": "Camel's Hump Foothills",
            "lat": 44.3212, 
            "lon": -72.8876,
            "description": "Mountain foothills with diverse terrain"
        },
        {
            "name": "Jay Peak Area",
            "lat": 44.9345, 
            "lon": -72.5123,
            "description": "Northern Vermont mountain terrain"
        },
        {
            "name": "Mount Equinox Slopes",
            "lat": 43.1789, 
            "lon": -73.0654,
            "description": "Southern Vermont mountain slopes"
        },
        {
            "name": "Cold Hollow Mountains",
            "lat": 44.7123, 
            "lon": -72.7890,
            "description": "Northern mountain region"
        }
    ]
    
    successful_locations = []
    total_tests = len(test_locations)
    
    for i, location in enumerate(test_locations):
        print(f"\n🏞️ LOCATION {i+1}/{total_tests}: {location['name']}")
        print(f"📍 Coordinates: {location['lat']:.4f}, {location['lon']:.4f}")
        print(f"📝 Description: {location['description']}")
        print("─" * 50)
        
        try:
            start_time = time.time()
            
            # Run enhanced analysis
            result = predictor.run_enhanced_biological_analysis(
                location['lat'], location['lon'], 7, "early_season", "moderate"
            )
            
            analysis_time = time.time() - start_time
            bedding_zones = result["bedding_zones"]
            features = bedding_zones.get("features", [])
            
            print(f"⚡ Analysis Time: {analysis_time:.2f}s")
            print(f"🏡 Bedding Zones Generated: {len(features)}")
            print(f"📊 Confidence Score: {result['confidence_score']:.2f}")
            
            # Show elevation method used
            gee_data = result.get("gee_data", {})
            elevation_method = gee_data.get("api_source", "unknown")
            print(f"🏔️ Elevation Method: {elevation_method}")
            
            if features:
                # SUCCESS - bedding zones found!
                successful_locations.append({
                    "location": location,
                    "zone_count": len(features),
                    "confidence": result['confidence_score'],
                    "analysis_time": analysis_time,
                    "features": features
                })
                
                print("🎉 SUCCESS - Bedding zones generated!")
                avg_suitability = sum(f["properties"]["suitability_score"] for f in features) / len(features)
                print(f"📈 Average Suitability: {avg_suitability:.1f}%")
                
                # Show first zone details
                zone = features[0]["properties"]
                print(f"🏡 Primary Zone Details:")
                print(f"   🌲 Canopy: {zone['canopy_coverage']:.1%}")
                print(f"   🛣️ Road Distance: {zone['road_distance']:.0f}m")
                print(f"   🏔️ Slope: {zone['slope']:.1f}°")
                print(f"   🧭 Aspect: {zone['aspect']:.0f}°")
                print(f"   💨 Wind Protection: {zone['wind_protection'].title()}")
                print(f"   🌡️ Thermal Advantage: {zone['thermal_advantage'].title()}")
                
            else:
                # Show why it failed
                suitability = bedding_zones.get("properties", {}).get("suitability_analysis", {})
                print("❌ No bedding zones generated")
                
                if suitability:
                    criteria = suitability.get("criteria", {})
                    thresholds = suitability.get("thresholds", {})
                    overall_score = suitability.get("overall_score", 0)
                    
                    print(f"📊 Overall Score: {overall_score:.1f}% (need >80%)")
                    print("🔍 Criteria Analysis:")
                    
                    # Canopy check
                    canopy_pass = criteria.get('canopy_coverage', 0) > thresholds.get('min_canopy', 0.7)
                    canopy_icon = "✅" if canopy_pass else "❌"
                    print(f"   {canopy_icon} Canopy: {criteria.get('canopy_coverage', 0):.1%} (need >{thresholds.get('min_canopy', 0.7):.0%})")
                    
                    # Road distance check
                    road_pass = criteria.get('road_distance', 0) > thresholds.get('min_road_distance', 200)
                    road_icon = "✅" if road_pass else "❌"
                    print(f"   {road_icon} Roads: {criteria.get('road_distance', 0):.0f}m (need >{thresholds.get('min_road_distance', 200)}m)")
                    
                    # Slope check
                    slope = criteria.get('slope', 0)
                    min_slope = thresholds.get('min_slope', 5)
                    max_slope = thresholds.get('max_slope', 20)
                    slope_pass = min_slope <= slope <= max_slope
                    slope_icon = "✅" if slope_pass else "❌"
                    print(f"   {slope_icon} Slope: {slope:.1f}° (need {min_slope}-{max_slope}°)")
                    
                    # Overall score check
                    score_pass = overall_score >= 80
                    score_icon = "✅" if score_pass else "❌"
                    print(f"   {score_icon} Overall: {overall_score:.1f}% (need >80%)")
                    
                    # Identify the main issue
                    if not canopy_pass:
                        print("🔧 Main Issue: Insufficient canopy coverage")
                    elif not road_pass:
                        print("🔧 Main Issue: Too close to roads")
                    elif not slope_pass:
                        if slope < min_slope:
                            print("🔧 Main Issue: Terrain too flat")
                        else:
                            print("🔧 Main Issue: Terrain too steep")
                    elif not score_pass:
                        print("🔧 Main Issue: Overall environmental conditions")
                
        except Exception as e:
            print(f"❌ Error testing location: {e}")
        
        print("=" * 50)
    
    # Summary report
    print(f"\n📋 SUMMARY REPORT")
    print("=" * 60)
    print(f"🗺️ Total Locations Tested: {total_tests}")
    print(f"✅ Successful Locations: {len(successful_locations)}")
    print(f"📊 Success Rate: {len(successful_locations)/total_tests*100:.1f}%")
    
    if successful_locations:
        print(f"\n🎉 SUCCESSFUL LOCATIONS:")
        for i, success in enumerate(successful_locations):
            loc = success["location"]
            print(f"   {i+1}. {loc['name']}")
            print(f"      📍 {loc['lat']:.4f}, {loc['lon']:.4f}")
            print(f"      🏡 {success['zone_count']} bedding zones")
            print(f"      📊 {success['confidence']:.2f} confidence")
            print(f"      ⚡ {success['analysis_time']:.2f}s analysis")
            
            # Show best zone details
            if success["features"]:
                zone = success["features"][0]["properties"]
                print(f"      🌲 {zone['canopy_coverage']:.0%} canopy, "
                      f"🛣️ {zone['road_distance']:.0f}m roads, "
                      f"🏔️ {zone['slope']:.1f}° slope")
            print()
        
        print("🎯 RECOMMENDATIONS:")
        best_location = max(successful_locations, key=lambda x: x['confidence'])
        print(f"   🥇 Best Location: {best_location['location']['name']}")
        print(f"   📊 Confidence: {best_location['confidence']:.2f}")
        print(f"   🏡 Zones: {best_location['zone_count']}")
        
    else:
        print(f"\n⚠️ NO SUCCESSFUL LOCATIONS FOUND")
        print("🔧 RECOMMENDATIONS:")
        print("   • Consider adjusting biological criteria for Vermont terrain")
        print("   • Test additional locations in steeper terrain")
        print("   • Review canopy coverage requirements")
        print("   • Check road proximity data accuracy")
    
    return len(successful_locations) > 0

if __name__ == "__main__":
    success = test_multiple_locations()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 MULTIPLE LOCATION TEST: SUCCESS!")
        print("✅ Found suitable bedding zone locations")
        print("✅ Biological criteria validation complete")
    else:
        print("⚠️ MULTIPLE LOCATION TEST: ALL LOCATIONS FAILED")
        print("🔧 Consider terrain-specific criteria adjustments")
    
    print("🗺️ MULTIPLE LOCATION TEST COMPLETE")
    print("=" * 60)
