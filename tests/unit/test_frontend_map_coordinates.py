#!/usr/bin/env python3
"""
TEST: Frontend Map Coordinate Issue Diagnosis
====================================================

This test demonstrates the issue where the frontend shows identical markers
even though the backend is generating varied predictions.

HYPOTHESIS: Frontend coordinate caching/display issue
- Map click updates st.session_state.hunt_location
- But predictions might be using cached coordinates
- Or map markers are being displayed with wrong coordinates

TESTING STRATEGY:
1. Simulate frontend coordinate flow
2. Test if coordinates are properly passed to backend
3. Test if markers are displayed at correct coordinates
"""

import requests
import json
from datetime import datetime

def test_frontend_coordinate_flow():
    """Test how coordinates flow from frontend to backend"""
    
    # Simulate different map click locations (same as comprehensive test)
    test_locations = [
        {"name": "Location 1: Valley Floor", "lat": 43.3110, "lon": -73.2201},
        {"name": "Location 2: Mountain Ridge", "lat": 44.5366, "lon": -72.8067},
        {"name": "Location 3: River Valley", "lat": 44.15, "lon": -72.8},
        {"name": "Location 4: Northern Area", "lat": 44.8, "lon": -72.5}
    ]
    
    backend_url = "http://127.0.0.1:8000"
    
    print("🗺️ FRONTEND MAP COORDINATE FLOW TEST")
    print("=" * 50)
    print()
    
    prediction_coordinates = []
    
    for location in test_locations:
        print(f"📍 {location['name']}")
        print(f"   Input Coordinates: {location['lat']:.4f}, {location['lon']:.4f}")
        
        # Simulate frontend prediction request (exact same format as app.py)
        prediction_data = {
            "lat": location['lat'],
            "lon": location['lon'],
            "date_time": f"2025-01-29T07:00:00",
            "hunt_period": "AM",
            "season": "rut",
            "fast_mode": True,
            "include_camera_placement": False
        }
        
        try:
            response = requests.post(
                f"{backend_url}/predict",
                json=prediction_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # Handle both old and new API response formats (same as app.py)
                if 'success' in response_data and response_data.get('success'):
                    prediction = response_data.get('data', response_data)
                else:
                    prediction = response_data
                
                # Extract coordinates that would be displayed on map
                display_coords = extract_display_coordinates(prediction)
                prediction_coordinates.append({
                    "input": location,
                    "display_coords": display_coords
                })
                
                print(f"   ✅ Prediction successful")
                print(f"   📊 Display coordinates extracted: {len(display_coords)} markers")
                
            else:
                print(f"   ❌ Prediction failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        print()
    
    # Analyze coordinate variation
    print("🔍 COORDINATE VARIATION ANALYSIS")
    print("=" * 50)
    
    if len(prediction_coordinates) >= 2:
        analyze_coordinate_variation(prediction_coordinates)
    else:
        print("❌ Insufficient predictions for analysis")

def extract_display_coordinates(prediction):
    """Extract coordinates that would be displayed as markers (same logic as app.py)"""
    
    display_coords = []
    
    # Travel corridors
    if 'travel_corridors' in prediction and prediction['travel_corridors']:
        travel_features = prediction['travel_corridors'].get('features', [])
        for feature in travel_features:
            if feature.get('geometry') and feature['geometry'].get('coordinates'):
                coords = feature['geometry']['coordinates']
                lat, lon = coords[1], coords[0]  # GeoJSON is [lon, lat]
                display_coords.append({
                    "type": "travel_corridor",
                    "lat": lat,
                    "lon": lon,
                    "score": feature['properties'].get('score', 0)
                })
    
    # Bedding zones
    if 'bedding_zones' in prediction and prediction['bedding_zones']:
        bedding_features = prediction['bedding_zones'].get('features', [])
        for i, feature in enumerate(bedding_features, 1):
            if feature.get('geometry') and feature['geometry'].get('coordinates'):
                coords = feature['geometry']['coordinates']
                lat, lon = coords[1], coords[0]  # GeoJSON is [lon, lat]
                display_coords.append({
                    "type": "bedding_zone",
                    "id": i,
                    "lat": lat,
                    "lon": lon,
                    "score": feature['properties'].get('score', 0)
                })
    
    # Feeding areas
    if 'feeding_areas' in prediction and prediction['feeding_areas']:
        feeding_features = prediction['feeding_areas'].get('features', [])
        for feature in feeding_features:
            if feature.get('geometry') and feature['geometry'].get('coordinates'):
                coords = feature['geometry']['coordinates']
                lat, lon = coords[1], coords[0]  # GeoJSON is [lon, lat]
                display_coords.append({
                    "type": "feeding_area",
                    "lat": lat,
                    "lon": lon,
                    "score": feature['properties'].get('score', 0)
                })
    
    # Stand recommendations
    if prediction.get('mature_buck_analysis') is not None:
        stand_recommendations = prediction['mature_buck_analysis'].get('stand_recommendations', [])
        for i, rec in enumerate(stand_recommendations, 1):
            coords = rec.get('coordinates', {})
            stand_lat = coords.get('lat', 0)
            stand_lon = coords.get('lon', 0)
            
            if stand_lat and stand_lon:
                display_coords.append({
                    "type": "stand_site",
                    "id": i,
                    "lat": stand_lat,
                    "lon": stand_lon,
                    "confidence": rec.get('confidence', 0)
                })
    
    # Optimized points (newer format)
    if 'optimized_points' in prediction and prediction['optimized_points']:
        optimized_data = prediction['optimized_points']
        
        for category in ['stand_sites', 'bedding_sites', 'feeding_sites', 'camera_placements']:
            if category in optimized_data:
                for i, point in enumerate(optimized_data[category], 1):
                    display_coords.append({
                        "type": category.rstrip('s'),  # Remove 's' from end
                        "id": i,
                        "lat": point['lat'],
                        "lon": point['lon'],
                        "score": point['score']
                    })
    
    return display_coords

def analyze_coordinate_variation(prediction_coordinates):
    """Analyze if coordinates are actually different between locations"""
    
    # Group all coordinates by type
    coords_by_type = {}
    
    for pred in prediction_coordinates:
        input_location = pred['input']
        display_coords = pred['display_coords']
        
        print(f"📍 {input_location['name']}: {len(display_coords)} markers")
        
        for coord in display_coords:
            coord_type = coord['type']
            if coord_type not in coords_by_type:
                coords_by_type[coord_type] = []
            
            coords_by_type[coord_type].append({
                "input_location": input_location['name'],
                "lat": coord['lat'],
                "lon": coord['lon'],
                "score": coord.get('score', 0)
            })
    
    print()
    print("🔍 COORDINATE UNIQUENESS BY TYPE:")
    print("-" * 40)
    
    total_variation_detected = 0
    
    for coord_type, coords in coords_by_type.items():
        if len(coords) < 2:
            continue
            
        # Check if all coordinates are identical
        first_coord = coords[0]
        all_identical = True
        
        for coord in coords[1:]:
            if (abs(coord['lat'] - first_coord['lat']) > 0.0001 or 
                abs(coord['lon'] - first_coord['lon']) > 0.0001):
                all_identical = False
                break
        
        if all_identical:
            print(f"❌ {coord_type}: ALL IDENTICAL")
            print(f"   Lat: {first_coord['lat']:.6f}, Lon: {first_coord['lon']:.6f}")
            for coord in coords:
                print(f"   {coord['input_location']}: {coord['lat']:.6f}, {coord['lon']:.6f}")
        else:
            print(f"✅ {coord_type}: VARIATION DETECTED")
            lat_range = max(c['lat'] for c in coords) - min(c['lat'] for c in coords)
            lon_range = max(c['lon'] for c in coords) - min(c['lon'] for c in coords)
            print(f"   Lat range: {lat_range:.6f}, Lon range: {lon_range:.6f}")
            total_variation_detected += 1
        
        print()
    
    print("📊 OVERALL ASSESSMENT:")
    print("-" * 30)
    
    if total_variation_detected > 0:
        print("✅ BACKEND IS GENERATING VARIED COORDINATES")
        print("✅ Environmental data is working correctly")
        print("🔍 Issue is likely in FRONTEND DISPLAY or CACHING")
        print()
        print("💡 POTENTIAL FRONTEND ISSUES:")
        print("  • Map marker caching in Streamlit/Folium")
        print("  • st.session_state coordinate persistence")
        print("  • Map key regeneration problems")
        print("  • Folium marker display refresh issues")
    else:
        print("❌ ALL COORDINATES ARE IDENTICAL")
        print("❌ Backend may not be receiving different input coordinates")

if __name__ == "__main__":
    test_frontend_coordinate_flow()
