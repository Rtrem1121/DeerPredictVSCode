#!/usr/bin/env python3
"""
Quick test to get GPS coordinates for the #1 mature buck stand

This script will make a prediction and extract the exact coordinates
for GPS entry.
"""

import requests
import json

def get_top_stand_coordinates(lat, lon, season="early_season"):
    """Get the GPS coordinates for the #1 predicted mature buck stand"""
    
    # Make prediction request
    url = "http://localhost:8000/predict"
    payload = {
        "lat": lat,
        "lon": lon,
        "date_time": "2025-08-27T06:00:00",
        "season": season
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            prediction = response.json()
            
            # Extract mature buck analysis
            mature_buck_data = prediction.get('mature_buck_analysis', {})
            stand_recommendations = mature_buck_data.get('stand_recommendations', [])
            
            if stand_recommendations:
                # Get #1 stand (highest ranked)
                top_stand = stand_recommendations[0]
                coords = top_stand.get('coordinates', {})
                
                stand_lat = coords.get('lat', 0)
                stand_lon = coords.get('lon', 0)
                confidence = top_stand.get('confidence', 0)
                stand_type = top_stand.get('type', 'Unknown')
                justification = top_stand.get('justification', 'No details')
                
                print("=" * 60)
                print("🎯 #1 MATURE BUCK STAND - GPS COORDINATES")
                print("=" * 60)
                print(f"📍 Latitude:  {stand_lat:.6f}")
                print(f"📍 Longitude: {stand_lon:.6f}")
                print(f"📱 GPS Format: {stand_lat:.6f}, {stand_lon:.6f}")
                print(f"🎯 Stand Type: {stand_type}")
                print(f"📊 Confidence: {confidence:.1f}%")
                print(f"💭 Reasoning: {justification}")
                print("=" * 60)
                
                # Also show all stand recommendations
                if len(stand_recommendations) > 1:
                    print("\n🏆 ALL STAND RECOMMENDATIONS:")
                    print("-" * 40)
                    for i, stand in enumerate(stand_recommendations, 1):
                        coords = stand.get('coordinates', {})
                        lat_coord = coords.get('lat', 0)
                        lon_coord = coords.get('lon', 0)
                        conf = stand.get('confidence', 0)
                        type_name = stand.get('type', 'Unknown')
                        
                        print(f"#{i}. {type_name}")
                        print(f"    📍 GPS: {lat_coord:.6f}, {lon_coord:.6f}")
                        print(f"    📊 Confidence: {conf:.1f}%")
                        print()
                
                return {
                    'lat': stand_lat,
                    'lon': stand_lon,
                    'confidence': confidence,
                    'type': stand_type,
                    'justification': justification
                }
            else:
                print("❌ No stand recommendations found")
                return None
                
        else:
            print(f"❌ API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    # Test with Vermont coordinates (same as before)
    test_lat = 44.26639
    test_lon = -72.58133
    
    print("🦌 Getting #1 Mature Buck Stand Coordinates...")
    print(f"📍 Search Location: {test_lat}, {test_lon}")
    print()
    
    coordinates = get_top_stand_coordinates(test_lat, test_lon)
    
    if coordinates:
        print("\n✅ Coordinates ready for GPS entry!")
        print("📱 Copy this to your GPS device:")
        print(f"   {coordinates['lat']:.6f}, {coordinates['lon']:.6f}")
    else:
        print("\n❌ Could not retrieve stand coordinates")
