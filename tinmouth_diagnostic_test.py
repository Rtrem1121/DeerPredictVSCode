#!/usr/bin/env python3
"""
Diagnostic Test for Bedding Suitability in Tinmouth, Vermont

Queries real data from app sources to compute independent bedding suitability,
comparing to app's output for algorithm validation.

Target: Tinmouth, VT (43.3146, -73.2178) - reported 43.1% suitability
Goal: Determine if low score reflects environmental reality or algorithm error

Requirements: Install ee, requests, numpy if needed.
"""

import logging
import requests
import numpy as np
from datetime import datetime
from typing import Dict
import json
import sys
import os

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tinmouth_diagnostic.log'),
        logging.StreamHandler()
    ]
)

def fetch_gee_canopy(lat: float, lon: float) -> float:
    """Fetch canopy cover from GEE"""
    try:
        import ee
        ee.Initialize()
        point = ee.Geometry.Point([lon, lat])
        canopy = ee.Image('UMD/hansen/global_forest_change_2022_v1_10').select('treecover2000')
        canopy_value = canopy.reduceRegion(ee.Reducer.mean(), point, 30).get('treecover2000').getInfo()
        result = canopy_value / 100 if canopy_value else 0.0
        logger.info(f"GEE Canopy Cover: {result:.3f} ({result*100:.1f}%)")
        return result
    except ImportError:
        logger.warning("Google Earth Engine not available, using fallback")
        return 0.65  # Moderate forest cover fallback
    except Exception as e:
        logger.error(f"GEE canopy fetch failed: {e}")
        return 0.65  # Fallback for Vermont forest area

def fetch_osm_road_proximity(lat: float, lon: float) -> float:
    """Fetch road distance from OSM using Overpass API"""
    try:
        overpass_url = "https://overpass-api.de/api/interpreter"
        # Query for roads within 1000m to calculate actual distance
        query = f"""
        [out:json][timeout:25];
        (
          way["highway"~"^(primary|secondary|tertiary|trunk|residential|unclassified)$"](around:1000,{lat},{lon});
        );
        out geom;
        """
        
        logger.info("Querying OSM for road proximity...")
        response = requests.post(overpass_url, data=query, timeout=30)
        
        if response.status_code == 200:
            roads = response.json().get('elements', [])
            logger.info(f"Found {len(roads)} roads in area")
            
            if roads:
                min_distance = float('inf')
                for road in roads:
                    if 'geometry' in road and road['geometry']:
                        for coord in road['geometry']:
                            # Calculate distance using Haversine approximation
                            lat_diff = lat - coord['lat']
                            lon_diff = lon - coord['lon']
                            # Approximate distance in meters (simplified)
                            dist = np.sqrt(lat_diff**2 + lon_diff**2) * 111320
                            min_distance = min(min_distance, dist)
                
                result = min_distance if min_distance != float('inf') else 500.0
                logger.info(f"Nearest road distance: {result:.1f}m")
                return result
        
        logger.warning("No roads found in OSM query, using fallback")
        return 500.0  # Fallback - assume isolated
        
    except Exception as e:
        logger.error(f"OSM road fetch failed: {e}")
        return 500.0  # Conservative fallback

def fetch_open_elevation(lat: float, lon: float) -> Dict:
    """Fetch slope and aspect from Open-Elevation API"""
    try:
        # Sample 5 points in a cross pattern to calculate slope and aspect
        offset = 0.001  # ~111m at this latitude
        locations = f"{lat},{lon}|{lat+offset},{lon}|{lat},{lon+offset}|{lat-offset},{lon}|{lat},{lon-offset}"
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations}"
        
        logger.info("Querying Open-Elevation for terrain data...")
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            results = response.json()["results"]
            if len(results) >= 5:
                elevations = [r["elevation"] for r in results]
                center_elev = elevations[0]
                north_elev = elevations[1]
                east_elev = elevations[2]
                south_elev = elevations[3]
                west_elev = elevations[4]
                
                # Calculate slope
                ns_diff = abs(north_elev - south_elev)
                ew_diff = abs(east_elev - west_elev)
                max_diff = max(ns_diff, ew_diff)
                distance_m = 111.32 * 1000 * offset  # Convert to meters
                slope_deg = np.degrees(np.arctan(max_diff / distance_m))
                
                # Calculate aspect (direction of steepest slope)
                ns_gradient = north_elev - south_elev
                ew_gradient = east_elev - west_elev
                
                if abs(ns_gradient) < 0.1 and abs(ew_gradient) < 0.1:
                    aspect = 180  # Default to south-facing if flat
                else:
                    aspect_rad = np.arctan2(ew_gradient, ns_gradient)
                    aspect = (90 - np.degrees(aspect_rad)) % 360
                
                logger.info(f"Elevation: {center_elev:.1f}m, Slope: {slope_deg:.1f}°, Aspect: {aspect:.1f}°")
                return {"slope": slope_deg, "aspect": aspect, "elevation": center_elev}
        
        logger.warning("Open-Elevation failed, using Vermont defaults")
        return {"slope": 12.0, "aspect": 180.0, "elevation": 400.0}  # Vermont hill defaults
        
    except Exception as e:
        logger.error(f"Open-Elevation fetch failed: {e}")
        return {"slope": 12.0, "aspect": 180.0, "elevation": 400.0}

def fetch_open_meteo_weather(lat: float, lon: float) -> Dict:
    """Fetch current weather from Open-Meteo API"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,wind_direction_10m",
            "temperature_unit": "fahrenheit"
        }
        
        logger.info("Querying Open-Meteo for weather data...")
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            current = response.json()["current"]
            temp_f = current["temperature_2m"]
            wind_speed = current["wind_speed_10m"]
            wind_dir = current["wind_direction_10m"]
            
            logger.info(f"Weather: {temp_f:.1f}°F, Wind: {wind_speed:.1f}mph from {wind_dir:.0f}°")
            return {
                "temperature": temp_f,
                "wind_speed": wind_speed,
                "wind_direction": wind_dir
            }
        
        logger.warning("Open-Meteo failed, using Vermont winter defaults")
        return {"temperature": 35.0, "wind_speed": 8.0, "wind_direction": 270.0}
        
    except Exception as e:
        logger.error(f"Open-Meteo fetch failed: {e}")
        return {"temperature": 35.0, "wind_speed": 8.0, "wind_direction": 270.0}

def calculate_bedding_suitability(canopy: float, road_distance: float, slope: float, 
                                aspect: float, wind_direction: float, temperature: float) -> Dict:
    """
    Compute bedding suitability score (0-100) using biological criteria
    
    Criteria based on mature buck bedding preferences:
    - Canopy: >70% for security
    - Isolation: >200m from roads
    - Slope: 5-20° for visibility/escape routes
    - Aspect: 135-225° (south-facing) for thermal advantage
    - Wind protection: Leeward positioning
    - Temperature: <40°F enhances thermal seeking behavior
    """
    
    # Weights based on biological importance
    weights = {
        "canopy": 0.25,       # Security from overhead cover
        "isolation": 0.25,    # Distance from human disturbance
        "slope": 0.15,        # Visibility and escape routes
        "aspect": 0.15,       # Thermal advantage
        "wind_protection": 0.1, # Shelter from wind
        "thermal": 0.1        # Temperature-driven behavior
    }
    
    scores = {}
    
    # Canopy cover score (0-100)
    # Optimal: >70%, Good: 50-70%, Poor: <50%
    if canopy >= 0.7:
        scores["canopy"] = 100
    elif canopy >= 0.5:
        scores["canopy"] = 50 + ((canopy - 0.5) / 0.2) * 50
    else:
        scores["canopy"] = (canopy / 0.5) * 50
    
    # Road isolation score (0-100)
    # Optimal: >500m, Good: 200-500m, Poor: <200m
    if road_distance >= 500:
        scores["isolation"] = 100
    elif road_distance >= 200:
        scores["isolation"] = 50 + ((road_distance - 200) / 300) * 50
    else:
        scores["isolation"] = (road_distance / 200) * 50
    
    # Slope score (0-100)
    # Optimal: 5-20°, Good: 3-25°, Poor: <3° or >25°
    if 5 <= slope <= 20:
        scores["slope"] = 100
    elif 3 <= slope <= 25:
        if slope < 5:
            scores["slope"] = 60 + ((slope - 3) / 2) * 40
        else:  # slope > 20
            scores["slope"] = 60 + ((25 - slope) / 5) * 40
    else:
        if slope < 3:
            scores["slope"] = (slope / 3) * 60
        else:  # slope > 25
            scores["slope"] = max(0, 60 - ((slope - 25) * 10))
    
    # Aspect score (0-100)
    # Optimal: 135-225° (SE to SW), Good: 90-270°, Poor: other
    if 135 <= aspect <= 225:
        scores["aspect"] = 100
    elif 90 <= aspect <= 270:
        # Distance from optimal range (180°)
        dist_from_optimal = min(abs(aspect - 180), 360 - abs(aspect - 180))
        if dist_from_optimal <= 45:
            scores["aspect"] = 80 + ((45 - dist_from_optimal) / 45) * 20
        else:
            scores["aspect"] = max(40, 80 - ((dist_from_optimal - 45) / 45) * 40)
    else:
        # North-facing aspects
        dist_from_optimal = min(abs(aspect - 180), 360 - abs(aspect - 180))
        scores["aspect"] = max(0, 40 - (dist_from_optimal / 90) * 40)
    
    # Wind protection score (0-100)
    # Optimal: Wind coming from opposite direction (>90° difference)
    wind_diff = min(abs(wind_direction - aspect), 360 - abs(wind_direction - aspect))
    if wind_diff >= 90:
        scores["wind_protection"] = 100
    else:
        scores["wind_protection"] = 50 + (wind_diff / 90) * 50
    
    # Thermal score (0-100)
    # Cold weather enhances thermal seeking behavior
    if temperature < 40:
        scores["thermal"] = scores["aspect"]  # Full thermal bonus
    elif temperature < 60:
        scores["thermal"] = scores["aspect"] * 0.8  # Partial bonus
    else:
        scores["thermal"] = scores["aspect"] * 0.6  # Minimal thermal effect
    
    # Calculate weighted overall score
    overall_score = sum(scores[key] * weights[key] for key in weights)
    
    # Log detailed breakdown
    logger.info("=== BEDDING SUITABILITY BREAKDOWN ===")
    for criterion, score in scores.items():
        weight = weights[criterion]
        contribution = score * weight
        logger.info(f"{criterion.upper():>15}: {score:6.1f} × {weight:.2f} = {contribution:5.1f}")
    
    logger.info(f"{'TOTAL SCORE':>15}: {overall_score:6.1f}%")
    logger.info("=" * 42)
    
    return {
        "overall_score": overall_score,
        "component_scores": scores,
        "weights": weights,
        "raw_data": {
            "canopy": canopy,
            "road_distance": road_distance,
            "slope": slope,
            "aspect": aspect,
            "wind_direction": wind_direction,
            "temperature": temperature
        }
    }

def run_diagnostic_test(lat: float, lon: float) -> Dict:
    """Run comprehensive diagnostic test for bedding suitability"""
    
    logger.info("=" * 60)
    logger.info("TINMOUTH VERMONT BEDDING SUITABILITY DIAGNOSTIC")
    logger.info(f"Location: {lat:.4f}, {lon:.4f}")
    logger.info(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Fetch all data sources
    logger.info("\n1. Fetching environmental data...")
    canopy = fetch_gee_canopy(lat, lon)
    road_distance = fetch_osm_road_proximity(lat, lon)
    elevation_data = fetch_open_elevation(lat, lon)
    weather = fetch_open_meteo_weather(lat, lon)
    
    # Calculate suitability
    logger.info("\n2. Calculating bedding suitability...")
    result = calculate_bedding_suitability(
        canopy=canopy,
        road_distance=road_distance,
        slope=elevation_data["slope"],
        aspect=elevation_data["aspect"],
        wind_direction=weather["wind_direction"],
        temperature=weather["temperature"]
    )
    
    # Compare with app's reported score
    app_score = 43.1
    independent_score = result["overall_score"]
    difference = independent_score - app_score
    
    logger.info("\n3. DIAGNOSTIC RESULTS")
    logger.info(f"App Score:         {app_score:6.1f}%")
    logger.info(f"Independent Score: {independent_score:6.1f}%")
    logger.info(f"Difference:        {difference:+6.1f}%")
    
    if abs(difference) > 15:
        if difference > 0:
            logger.warning("⚠️  ALGORITHM ISSUE SUSPECTED: Independent score significantly higher")
            logger.warning("    Possible causes: Scoring bug, data integration failure, weight miscalibration")
        else:
            logger.warning("⚠️  ALGORITHM ISSUE SUSPECTED: Independent score significantly lower")
            logger.warning("    Possible causes: Different data sources, timing, or criteria interpretation")
    elif independent_score < 50:
        logger.info("✅ LOW SCORE CONFIRMED: Area has marginal suitability for mature buck bedding")
        logger.info("    Environmental factors genuinely limit bedding potential")
    else:
        logger.info("✅ SCORES ALIGNED: Both assessments indicate moderate suitability")
    
    # Identify limiting factors
    limiting_factors = []
    scores = result["component_scores"]
    
    if scores["canopy"] < 60:
        limiting_factors.append(f"Insufficient canopy cover ({canopy*100:.1f}% < 70% optimal)")
    if scores["isolation"] < 60:
        limiting_factors.append(f"Too close to roads ({road_distance:.0f}m < 200m minimum)")
    if scores["slope"] < 60:
        limiting_factors.append(f"Suboptimal slope ({elevation_data['slope']:.1f}° outside 5-20° range)")
    if scores["aspect"] < 60:
        limiting_factors.append(f"Poor aspect ({elevation_data['aspect']:.0f}° not south-facing)")
    if scores["wind_protection"] < 60:
        limiting_factors.append(f"Limited wind protection (exposed to {weather['wind_direction']:.0f}° winds)")
    
    if limiting_factors:
        logger.info("\n4. LIMITING FACTORS:")
        for factor in limiting_factors:
            logger.info(f"   • {factor}")
    else:
        logger.info("\n4. No major limiting factors identified")
    
    # Generate recommendations
    recommendations = []
    if scores["canopy"] < 70:
        recommendations.append("Look for areas with denser forest cover (>70%)")
    if scores["isolation"] < 70:
        recommendations.append("Search further from roads and human activity")
    if scores["slope"] < 70:
        recommendations.append("Target moderate slopes (5-20°) for optimal visibility")
    if scores["aspect"] < 70:
        recommendations.append("Focus on south-facing slopes for thermal advantage")
    
    if recommendations:
        logger.info("\n5. RECOMMENDATIONS:")
        for rec in recommendations:
            logger.info(f"   • {rec}")
    
    # Save detailed results
    detailed_results = {
        "test_info": {
            "location": {"lat": lat, "lon": lon},
            "timestamp": datetime.now().isoformat(),
            "app_reported_score": app_score
        },
        "environmental_data": {
            "canopy_cover": canopy,
            "road_distance_m": road_distance,
            "slope_degrees": elevation_data["slope"],
            "aspect_degrees": elevation_data["aspect"],
            "elevation_m": elevation_data.get("elevation", 0),
            "temperature_f": weather["temperature"],
            "wind_speed_mph": weather["wind_speed"],
            "wind_direction_degrees": weather["wind_direction"]
        },
        "suitability_analysis": result,
        "comparison": {
            "app_score": app_score,
            "independent_score": independent_score,
            "difference": difference,
            "diagnosis": "algorithm_issue" if abs(difference) > 15 else "environmental_limitation"
        },
        "limiting_factors": limiting_factors,
        "recommendations": recommendations
    }
    
    # Save to file
    output_file = f"tinmouth_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(detailed_results, f, indent=2)
    
    logger.info(f"\n6. Detailed results saved to: {output_file}")
    logger.info("=" * 60)
    
    return detailed_results

if __name__ == "__main__":
    # Test coordinates for Tinmouth, Vermont
    test_lat = 43.3146
    test_lon = -73.2178
    
    try:
        results = run_diagnostic_test(test_lat, test_lon)
        
        # Print summary to console
        print(f"\n🎯 DIAGNOSTIC SUMMARY")
        print(f"Location: Tinmouth, VT ({test_lat}, {test_lon})")
        print(f"App Score: {results['comparison']['app_score']}%")
        print(f"Independent Score: {results['comparison']['independent_score']:.1f}%")
        print(f"Diagnosis: {results['comparison']['diagnosis'].replace('_', ' ').title()}")
        
        if results['comparison']['diagnosis'] == 'algorithm_issue':
            print("🔧 Recommendation: Review algorithm implementation")
        else:
            print("🌲 Recommendation: Area has genuine environmental limitations")
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
