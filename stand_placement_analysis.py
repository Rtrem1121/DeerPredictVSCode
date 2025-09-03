#!/usr/bin/env python3
"""
Stand Placement Biological Assessment
Analyzing Stand #1 positioning relative to bedding/feeding areas
"""

import requests
import json
import math
from datetime import datetime

def calculate_distance_bearing(lat1, lon1, lat2, lon2):
    """Calculate distance and bearing between two points"""
    # Convert to radians
    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = math.radians(lat2)
    lon2_r = math.radians(lon2)
    
    # Distance calculation (Haversine formula)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance_km = 6371 * c
    distance_m = distance_km * 1000
    
    # Bearing calculation
    y = math.sin(dlon) * math.cos(lat2_r)
    x = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon)
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return distance_m, bearing

def bearing_to_compass(bearing):
    """Convert bearing to compass direction"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = int((bearing + 11.25) / 22.5) % 16
    return directions[index]

def analyze_stand_placement():
    """Analyze the biological logic of stand placement"""
    
    print("🔍 STAND PLACEMENT BIOLOGICAL ASSESSMENT")
    print("=" * 60)
    
    # Stand coordinates from user report  
    # Using coordinates from user's location context
    stand_lat = 43.3161
    stand_lon = -73.2154
    
    print(f"🎯 STAND #1 LOCATION: {stand_lat}, {stand_lon}")
    print(f"📍 Stand Type: Travel Corridor Stand")
    print(f"🎯 Algorithm Confidence: 95%")
    print()
    
    # Get current prediction data to analyze actual bedding/feeding locations
    try:
        print("📡 Fetching current prediction data...")
        response = requests.post("http://localhost:8000/predict", json={
            "lat": stand_lat,
            "lon": stand_lon,
            "date_time": "2025-09-03T18:00:00",
            "hunt_period": "PM",
            "season": "early_season",
            "fast_mode": True,
            "include_camera_placement": False
        }, headers={'Content-Type': 'application/json'}, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ Prediction data retrieved successfully")
            
            # Extract the actual data from the response wrapper
            if 'data' in response_data:
                data = response_data['data']
            else:
                data = response_data
            
            print(f"🔍 Data keys: {list(data.keys())}")
            
            # Check for different possible data structures
            bedding_zones = []
            feeding_areas = []
            
            # Try multiple possible data structures
            if 'bedding_zones' in data:
                if isinstance(data['bedding_zones'], dict) and 'features' in data['bedding_zones']:
                    bedding_zones = data['bedding_zones']['features']
                elif isinstance(data['bedding_zones'], list):
                    bedding_zones = data['bedding_zones']
            
            if 'feeding_areas' in data:
                if isinstance(data['feeding_areas'], dict) and 'features' in data['feeding_areas']:
                    feeding_areas = data['feeding_areas']['features']
                elif isinstance(data['feeding_areas'], list):
                    feeding_areas = data['feeding_areas']
            
            # Check for alternative key names
            if not bedding_zones and 'bedding' in data:
                bedding_zones = data['bedding'] if isinstance(data['bedding'], list) else []
            
            if not feeding_areas and 'feeding' in data:
                feeding_areas = data['feeding'] if isinstance(data['feeding'], list) else []
            
            # If still no data, check optimized_points structure
            if not bedding_zones and not feeding_areas and 'optimized_points' in data:
                opt_points = data['optimized_points']
                if 'bedding_sites' in opt_points:
                    bedding_zones = opt_points['bedding_sites']
                if 'feeding_sites' in opt_points:
                    feeding_areas = opt_points['feeding_sites']
            
            print(f"📊 Found {len(bedding_zones)} bedding zones, {len(feeding_areas)} feeding areas")
            
            stand_recommendations = data.get('mature_buck_analysis', {}).get('stand_recommendations', [])
            
            if not bedding_zones and not feeding_areas:
                print("⚠️ No bedding or feeding data found. Available data structure:")
                print(json.dumps(data, indent=2)[:500] + "...")
                return
            
            print(f"\n🛏️ BEDDING ZONES ANALYSIS ({len(bedding_zones)} zones):")
            print("-" * 50)
            
            bedding_distances = []
            for i, zone in enumerate(bedding_zones):
                coords = zone['geometry']['coordinates']
                bed_lon, bed_lat = coords[0], coords[1]
                distance, bearing = calculate_distance_bearing(stand_lat, stand_lon, bed_lat, bed_lon)
                compass = bearing_to_compass(bearing)
                bedding_distances.append(distance)
                
                print(f"Bedding Zone {i+1}:")
                print(f"  📍 Location: {bed_lat:.6f}, {bed_lon:.6f}")
                print(f"  📏 Distance from Stand: {distance:.0f}m")
                print(f"  🧭 Direction from Stand: {compass} ({bearing:.0f}°)")
                print(f"  🎯 Score: {zone['properties'].get('score', 'N/A')}")
                print(f"  📝 Type: {zone['properties'].get('bedding_type', 'Unknown')}")
                print()
            
            print(f"🌾 FEEDING AREAS ANALYSIS ({len(feeding_areas)} areas):")
            print("-" * 50)
            
            feeding_distances = []
            for i, area in enumerate(feeding_areas):
                coords = area['geometry']['coordinates']
                feed_lon, feed_lat = coords[0], coords[1]
                distance, bearing = calculate_distance_bearing(stand_lat, stand_lon, feed_lat, feed_lon)
                compass = bearing_to_compass(bearing)
                feeding_distances.append(distance)
                
                print(f"Feeding Area {i+1}:")
                print(f"  📍 Location: {feed_lat:.6f}, {feed_lon:.6f}")
                print(f"  📏 Distance from Stand: {distance:.0f}m")
                print(f"  🧭 Direction from Stand: {compass} ({bearing:.0f}°)")
                print(f"  🎯 Score: {area['properties'].get('score', 'N/A')}")
                print(f"  📝 Type: {area['properties'].get('feeding_type', 'Unknown')}")
                print()
            
            # BIOLOGICAL ASSESSMENT
            print("🧠 BIOLOGICAL MOVEMENT ANALYSIS")
            print("=" * 60)
            
            # Calculate average distances
            avg_bedding_distance = sum(bedding_distances) / len(bedding_distances) if bedding_distances else 0
            avg_feeding_distance = sum(feeding_distances) / len(feeding_distances) if feeding_distances else 0
            
            print(f"📊 DISTANCE ANALYSIS:")
            print(f"  🛏️ Average distance to bedding: {avg_bedding_distance:.0f}m")
            print(f"  🌾 Average distance to feeding: {avg_feeding_distance:.0f}m")
            print(f"  📏 Closest bedding: {min(bedding_distances):.0f}m")
            print(f"  📏 Closest feeding: {min(feeding_distances):.0f}m")
            print()
            
            # MATURE BUCK BEHAVIOR ASSESSMENT
            print("🦌 MATURE BUCK BEHAVIOR ASSESSMENT:")
            print("-" * 50)
            
            # Ideal travel corridor positioning
            ideal_distance_bedding = 150-400  # meters
            ideal_distance_feeding = 100-300   # meters
            
            # Check if stand is positioned appropriately
            bedding_assessment = "GOOD" if 150 <= avg_bedding_distance <= 400 else "NEEDS_REVIEW"
            feeding_assessment = "GOOD" if 100 <= avg_feeding_distance <= 300 else "NEEDS_REVIEW"
            
            print(f"✅ Bedding Distance Assessment: {bedding_assessment}")
            if bedding_assessment == "GOOD":
                print("   • Distance allows deer to feel secure in bedding")
                print("   • Stand positioned in likely travel route")
            else:
                if avg_bedding_distance < 150:
                    print("   ⚠️ Stand may be too close to bedding areas")
                    print("   • Risk of pressuring bedding zones")
                    print("   • Mature bucks may avoid area")
                else:
                    print("   ⚠️ Stand may be too far from bedding areas")
                    print("   • Deer may use different travel routes")
                    print("   • Less predictable movement patterns")
            
            print(f"✅ Feeding Distance Assessment: {feeding_assessment}")
            if feeding_assessment == "GOOD":
                print("   • Distance allows interception of feeding movement")
                print("   • Stand positioned for evening approaches")
            else:
                if avg_feeding_distance < 100:
                    print("   ⚠️ Stand may be too close to feeding areas")
                    print("   • Risk of pressuring food sources")
                else:
                    print("   ⚠️ Stand may be too far from feeding areas")
                    print("   • May miss primary feeding movement")
            
            print()
            
            # TRAVEL CORRIDOR LOGIC
            print("🛤️ TRAVEL CORRIDOR LOGIC ASSESSMENT:")
            print("-" * 50)
            
            # Check if stand is between bedding and feeding
            stand_between_bed_feed = False
            
            # Simple check: if stand is roughly between average bedding and feeding locations
            # Calculate center points
            if bedding_zones and feeding_areas:
                avg_bed_lat = sum(zone['geometry']['coordinates'][1] for zone in bedding_zones) / len(bedding_zones)
                avg_bed_lon = sum(zone['geometry']['coordinates'][0] for zone in bedding_zones) / len(bedding_zones)
                avg_feed_lat = sum(area['geometry']['coordinates'][1] for area in feeding_areas) / len(feeding_areas)
                avg_feed_lon = sum(area['geometry']['coordinates'][0] for area in feeding_areas) / len(feeding_areas)
                
                # Check if stand is positioned between bedding and feeding centers
                bed_to_stand_dist, _ = calculate_distance_bearing(avg_bed_lat, avg_bed_lon, stand_lat, stand_lon)
                feed_to_stand_dist, _ = calculate_distance_bearing(avg_feed_lat, avg_feed_lon, stand_lat, stand_lon)
                bed_to_feed_dist, _ = calculate_distance_bearing(avg_bed_lat, avg_bed_lon, avg_feed_lat, avg_feed_lon)
                
                # If stand distances to both bedding and feeding are less than bedding-to-feeding distance,
                # then stand is likely in a good intercept position
                if (bed_to_stand_dist + feed_to_stand_dist) <= (bed_to_feed_dist * 1.2):  # 20% tolerance
                    stand_between_bed_feed = True
                
                print(f"📍 Bedding center: {avg_bed_lat:.6f}, {avg_bed_lon:.6f}")
                print(f"📍 Feeding center: {avg_feed_lat:.6f}, {avg_feed_lon:.6f}")
                print(f"📏 Bedding to feeding distance: {bed_to_feed_dist:.0f}m")
                print(f"📏 Stand to bedding center: {bed_to_stand_dist:.0f}m")
                print(f"📏 Stand to feeding center: {feed_to_stand_dist:.0f}m")
                print()
                
                if stand_between_bed_feed:
                    print("✅ STAND POSITIONING: EXCELLENT")
                    print("   • Stand positioned as travel corridor intercept")
                    print("   • Likely to encounter deer moving between bed/feed")
                    print("   • Strategic positioning for mature buck patterns")
                else:
                    print("⚠️ STAND POSITIONING: NEEDS REVIEW")
                    print("   • Stand may not be optimally positioned for intercept")
                    print("   • Consider moving closer to travel corridor")
                    print("   • Deer may use different routes")
            
            print()
            
            # FINAL BIOLOGICAL VERDICT
            print("🎯 FINAL BIOLOGICAL ASSESSMENT")
            print("=" * 60)
            
            if (bedding_assessment == "GOOD" and 
                feeding_assessment == "GOOD" and 
                stand_between_bed_feed):
                verdict = "BIOLOGICALLY SOUND"
                confidence = "HIGH"
            elif stand_between_bed_feed and (bedding_assessment == "GOOD" or feeding_assessment == "GOOD"):
                verdict = "ACCEPTABLE WITH MONITORING"
                confidence = "MEDIUM"
            else:
                verdict = "NEEDS OPTIMIZATION"
                confidence = "LOW"
            
            print(f"🧠 Biological Logic: {verdict}")
            print(f"🎯 Hunting Confidence: {confidence}")
            print()
            
            if verdict == "BIOLOGICALLY SOUND":
                print("✅ RECOMMENDATIONS:")
                print("   • Stand placement follows mature buck behavior patterns")
                print("   • High probability of deer encounter")
                print("   • Execute hunt plan as designed")
            elif verdict == "ACCEPTABLE WITH MONITORING":
                print("⚠️ RECOMMENDATIONS:")
                print("   • Stand has potential but may need adjustment")
                print("   • Monitor deer sign and movement patterns")
                print("   • Consider backup stand locations")
            else:
                print("🔄 RECOMMENDATIONS:")
                print("   • Consider repositioning stand closer to travel corridor")
                print("   • Analyze actual deer sign in area")
                print("   • May need to scout alternative locations")
            
        else:
            print(f"❌ Failed to get prediction data: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error analyzing stand placement: {str(e)}")

if __name__ == "__main__":
    analyze_stand_placement()
