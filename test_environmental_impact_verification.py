#!/usr/bin/env python3
"""
Environmental Data Impact Verification Test

This test verifies that the accurate environmental data we're now collecting
is actually being used to generate different stand, feeding, and bedding predictions
across different locations with different environmental conditions.

We'll test multiple locations with contrasting environmental factors to ensure
the positioning algorithms are responsive to the data changes.
"""

import requests
import json
import logging
from datetime import datetime
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)-12s: %(levelname)-8s %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in meters"""
    R = 6371000  # Earth's radius in meters
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat/2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def test_environmental_impact_on_predictions():
    """Test that environmental data impacts prediction positioning"""
    logger.info("🔬 ENVIRONMENTAL DATA IMPACT VERIFICATION TEST")
    logger.info("=" * 80)
    logger.info("Testing if accurate environmental data produces varied predictions")
    
    backend_url = "http://localhost:8000"
    
    # Test locations with very different environmental characteristics
    test_locations = [
        {
            "name": "Valley Floor (Low Elevation)",
            "lat": 43.3110, "lon": -73.2201,
            "expected": "Open field, low slope, SW exposure"
        },
        {
            "name": "Mountain Ridge (High Elevation)", 
            "lat": 44.5366, "lon": -72.8067,
            "expected": "High elevation, steep slopes, varied aspect"
        },
        {
            "name": "River Valley (Different Aspect)",
            "lat": 44.1500, "lon": -72.8000,
            "expected": "Different terrain orientation"
        },
        {
            "name": "Northern Exposure",
            "lat": 44.8000, "lon": -72.5000,
            "expected": "Different climate zone"
        }
    ]
    
    all_results = []
    
    for i, location in enumerate(test_locations, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"🌍 LOCATION {i}: {location['name']}")
        logger.info(f"   Coordinates: {location['lat']}, {location['lon']}")
        logger.info(f"   Expected: {location['expected']}")
        logger.info("=" * 80)
        
        # Make API call
        payload = {
            "lat": location["lat"],
            "lon": location["lon"],
            "date_time": "2025-08-29T07:00:00",
            "hunt_period": "AM",
            "season": "fall",
            "fast_mode": True,
            "include_camera_placement": False
        }
        
        try:
            response = requests.post(f"{backend_url}/predict", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and data.get("data"):
                    prediction_data = data["data"]
                    
                    # Extract environmental factors
                    weather_data = prediction_data.get("weather_data", {})
                    gee_data = prediction_data.get("gee_data", {})
                    
                    env_factors = {
                        "temperature": weather_data.get("temperature", 0),
                        "wind_direction": weather_data.get("wind_direction", 0),
                        "wind_speed": weather_data.get("wind_speed", 0),
                        "elevation": gee_data.get("elevation", 0),
                        "slope": gee_data.get("slope", 0),
                        "aspect": gee_data.get("aspect", 0),
                        "canopy": gee_data.get("canopy_coverage", 0)
                    }
                    
                    logger.info("🌤️ ENVIRONMENTAL FACTORS:")
                    logger.info(f"   Temperature: {env_factors['temperature']:.1f}°F")
                    logger.info(f"   Wind: {env_factors['wind_direction']:.0f}° at {env_factors['wind_speed']:.1f} mph")
                    logger.info(f"   Elevation: {env_factors['elevation']:.0f}m")
                    logger.info(f"   Slope: {env_factors['slope']:.1f}°")
                    logger.info(f"   Aspect: {env_factors['aspect']:.0f}°")
                    logger.info(f"   Canopy: {env_factors['canopy']*100:.0f}%")
                    
                    # Extract prediction coordinates
                    coordinates = {
                        "bedding": [],
                        "stands": [],
                        "feeding": [],
                        "camera": None
                    }
                    
                    # Bedding zones
                    bedding_zones = prediction_data.get("bedding_zones", {})
                    if bedding_zones.get("features"):
                        for feature in bedding_zones["features"]:
                            if feature.get("geometry", {}).get("coordinates"):
                                lon, lat = feature["geometry"]["coordinates"]
                                coordinates["bedding"].append((lat, lon))
                    
                    # Stand recommendations  
                    stands = prediction_data.get("mature_buck_analysis", {}).get("stand_recommendations", [])
                    for stand in stands:
                        coords = stand.get("coordinates", {})
                        if coords:
                            coordinates["stands"].append((coords["lat"], coords["lon"]))
                    
                    # Feeding areas
                    feeding_areas = prediction_data.get("feeding_areas", {})
                    if feeding_areas.get("features"):
                        for feature in feeding_areas["features"]:
                            if feature.get("geometry", {}).get("coordinates"):
                                lon, lat = feature["geometry"]["coordinates"]
                                coordinates["feeding"].append((lat, lon))
                    
                    # Camera placement
                    camera = prediction_data.get("optimal_camera_placement", {})
                    if camera.get("coordinates"):
                        coordinates["camera"] = (camera["coordinates"]["lat"], camera["coordinates"]["lon"])
                    
                    logger.info("\n📍 GENERATED COORDINATES:")
                    logger.info(f"   Bedding Zones: {len(coordinates['bedding'])} zones")
                    for j, (lat, lon) in enumerate(coordinates["bedding"]):
                        offset_lat = lat - location["lat"]
                        offset_lon = lon - location["lon"] 
                        distance = calculate_distance(location["lat"], location["lon"], lat, lon)
                        logger.info(f"     Zone {j+1}: {lat:.6f}, {lon:.6f} (Δ{offset_lat:+.4f}, {offset_lon:+.4f}) [{distance:.0f}m]")
                    
                    logger.info(f"   Stand Sites: {len(coordinates['stands'])} sites")
                    for j, (lat, lon) in enumerate(coordinates["stands"]):
                        offset_lat = lat - location["lat"]
                        offset_lon = lon - location["lon"]
                        distance = calculate_distance(location["lat"], location["lon"], lat, lon)
                        logger.info(f"     Site {j+1}: {lat:.6f}, {lon:.6f} (Δ{offset_lat:+.4f}, {offset_lon:+.4f}) [{distance:.0f}m]")
                    
                    logger.info(f"   Feeding Areas: {len(coordinates['feeding'])} areas")
                    for j, (lat, lon) in enumerate(coordinates["feeding"]):
                        offset_lat = lat - location["lat"]
                        offset_lon = lon - location["lon"]
                        distance = calculate_distance(location["lat"], location["lon"], lat, lon)
                        logger.info(f"     Area {j+1}: {lat:.6f}, {lon:.6f} (Δ{offset_lat:+.4f}, {offset_lon:+.4f}) [{distance:.0f}m]")
                    
                    if coordinates["camera"]:
                        lat, lon = coordinates["camera"]
                        offset_lat = lat - location["lat"]
                        offset_lon = lon - location["lon"]
                        distance = calculate_distance(location["lat"], location["lon"], lat, lon)
                        logger.info(f"   Camera: {lat:.6f}, {lon:.6f} (Δ{offset_lat:+.4f}, {offset_lon:+.4f}) [{distance:.0f}m]")
                    
                    # Store results for comparison
                    all_results.append({
                        "location": location,
                        "environmental_factors": env_factors,
                        "coordinates": coordinates
                    })
                    
                else:
                    logger.error(f"   ❌ No prediction data for {location['name']}")
            else:
                logger.error(f"   ❌ API failed for {location['name']}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"   ❌ Error testing {location['name']}: {e}")
    
    # Analysis of results
    logger.info("\n" + "=" * 80)
    logger.info("📊 ENVIRONMENTAL IMPACT ANALYSIS")
    logger.info("=" * 80)
    
    if len(all_results) >= 2:
        # Compare environmental factors
        logger.info("🌍 ENVIRONMENTAL VARIATION:")
        factors = ["temperature", "wind_direction", "elevation", "slope", "aspect"]
        
        for factor in factors:
            values = [result["environmental_factors"][factor] for result in all_results]
            min_val, max_val = min(values), max(values)
            variation = max_val - min_val
            logger.info(f"   {factor.title()}: {min_val:.1f} - {max_val:.1f} (Δ{variation:.1f})")
        
        # Compare coordinate variations
        logger.info("\n📍 COORDINATE VARIATION ANALYSIS:")
        
        for coord_type in ["bedding", "stands", "feeding"]:
            all_coords = []
            for result in all_results:
                all_coords.extend(result["coordinates"][coord_type])
            
            if all_coords:
                # Calculate coordinate diversity
                lats = [coord[0] for coord in all_coords]
                lons = [coord[1] for coord in all_coords]
                
                lat_range = max(lats) - min(lats) if lats else 0
                lon_range = max(lons) - min(lons) if lons else 0
                
                # Convert to meters (approximate)
                lat_meters = lat_range * 111000
                lon_meters = lon_range * 85000  # Approximate for Vermont latitude
                
                unique_coords = len(set(all_coords))
                total_coords = len(all_coords)
                diversity_pct = (unique_coords / total_coords * 100) if total_coords > 0 else 0
                
                logger.info(f"   {coord_type.title()}:")
                logger.info(f"     Coordinate Range: {lat_range:.6f}° lat, {lon_range:.6f}° lon")
                logger.info(f"     Distance Range: {lat_meters:.0f}m lat, {lon_meters:.0f}m lon")
                logger.info(f"     Diversity: {unique_coords}/{total_coords} unique ({diversity_pct:.1f}%)")
                
                if diversity_pct > 80:
                    logger.info(f"     ✅ HIGH VARIATION - Environmental data is impacting {coord_type} placement")
                elif diversity_pct > 50:
                    logger.info(f"     ⚠️ MODERATE VARIATION - Some environmental impact on {coord_type} placement")
                else:
                    logger.info(f"     ❌ LOW VARIATION - Environmental data may not be affecting {coord_type} placement")
        
        # Overall assessment
        logger.info("\n🎯 OVERALL ASSESSMENT:")
        
        # Check if we have significant environmental variation
        temp_variation = max([r["environmental_factors"]["temperature"] for r in all_results]) - min([r["environmental_factors"]["temperature"] for r in all_results])
        elev_variation = max([r["environmental_factors"]["elevation"] for r in all_results]) - min([r["environmental_factors"]["elevation"] for r in all_results])
        
        if temp_variation > 5 or elev_variation > 200:  # Significant environmental differences
            logger.info("✅ SIGNIFICANT ENVIRONMENTAL VARIATION DETECTED")
            logger.info("✅ Environmental data collection is working correctly")
            
            # Now check if this translates to coordinate variation
            total_unique = 0
            total_coords = 0
            
            for coord_type in ["bedding", "stands", "feeding"]:
                all_coords = []
                for result in all_results:
                    all_coords.extend(result["coordinates"][coord_type])
                if all_coords:
                    total_unique += len(set(all_coords))
                    total_coords += len(all_coords)
            
            if total_coords > 0:
                overall_diversity = total_unique / total_coords * 100
                
                if overall_diversity > 75:
                    logger.info("✅ ENVIRONMENTAL DATA IS EFFECTIVELY IMPACTING PREDICTIONS")
                    logger.info("✅ Coordinate positioning is responsive to environmental changes")
                elif overall_diversity > 50:
                    logger.info("⚠️ PARTIAL ENVIRONMENTAL IMPACT - Some responsiveness detected")
                    logger.info("⚠️ May need to investigate specific positioning algorithms")
                else:
                    logger.info("❌ LIMITED ENVIRONMENTAL IMPACT - Positioning may still use hardcoded logic")
                    logger.info("❌ Need to investigate positioning calculation methods")
        else:
            logger.info("⚠️ Limited environmental variation between test locations")
            logger.info("⚠️ Try testing more contrasting locations for better analysis")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "test_name": "Environmental Data Impact Verification Test",
        "timestamp": timestamp,
        "test_locations": test_locations,
        "results": all_results
    }
    
    filename = f"environmental_impact_verification_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"\n📄 Detailed results saved to: {filename}")

if __name__ == "__main__":
    test_environmental_impact_on_predictions()
