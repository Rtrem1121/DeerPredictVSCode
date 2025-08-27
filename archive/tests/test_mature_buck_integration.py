#!/usr/bin/env python3
"""
Test script to verify mature buck integration is working correctly
"""

import requests
import json
from datetime import datetime

def test_mature_buck_integration():
    """Test the integrated mature buck prediction system"""
    
    # Test coordinates - Vermont location
    test_locations = [
        {"lat": 44.2601, "lon": -72.5806, "name": "Montpelier, VT"},
        {"lat": 44.4759, "lon": -73.2121, "name": "Burlington, VT"},
        {"lat": 43.6106, "lon": -72.9726, "name": "Rutland, VT"}
    ]
    
    # Test different seasons
    test_seasons = ["early_season", "rut", "late_season"]
    
    backend_url = "http://localhost:8000"
    
    print("🏹 Testing Mature Buck Integration...")
    print("=" * 60)
    
    for location in test_locations:
        print(f"\n📍 Testing location: {location['name']}")
        print(f"   Coordinates: {location['lat']}, {location['lon']}")
        
        for season in test_seasons:
            print(f"\n   🦌 Season: {season}")
            
            # Prepare prediction request
            request_data = {
                "lat": location["lat"],
                "lon": location["lon"],
                "date_time": datetime.now().isoformat(),
                "season": season,
                "suggestion_threshold": 5.0,
                "min_suggestion_rating": 8.0
            }
            
            try:
                # Make prediction request
                response = requests.post(
                    f"{backend_url}/predict",
                    json=request_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    prediction = response.json()
                    
                    # Check for mature buck opportunities
                    mature_buck_opportunities = prediction.get('mature_buck_opportunities')
                    mature_buck_analysis = prediction.get('mature_buck_analysis')
                    
                    if mature_buck_opportunities:
                        features = mature_buck_opportunities.get('features', [])
                        print(f"     ✅ Mature buck opportunities: {len(features)} found")
                        
                        for i, feature in enumerate(features, 1):
                            props = feature.get('properties', {})
                            confidence = props.get('confidence', 'N/A')
                            terrain_score = props.get('terrain_score', 'N/A')
                            print(f"        #{i}: Confidence {confidence}%, Terrain {terrain_score}%")
                    else:
                        print(f"     ❌ No mature buck opportunities found")
                    
                    if mature_buck_analysis:
                        viable = mature_buck_analysis.get('viable_location', False)
                        confidence_summary = mature_buck_analysis.get('confidence_summary', {})
                        overall_suitability = confidence_summary.get('overall_suitability', 0)
                        
                        print(f"     📊 Analysis: Viable={viable}, Suitability={overall_suitability:.1f}%")
                        
                        if overall_suitability >= 60:
                            print(f"     🎯 EXCELLENT mature buck location!")
                        elif overall_suitability >= 40:
                            print(f"     ⚠️  Moderate mature buck potential")
                        else:
                            print(f"     ❌ Poor mature buck habitat")
                    
                    # Check that regular deer predictions still work
                    travel_corridors = prediction.get('travel_corridors', {}).get('features', [])
                    bedding_zones = prediction.get('bedding_zones', {}).get('features', [])
                    feeding_areas = prediction.get('feeding_areas', {}).get('features', [])
                    
                    print(f"     🦌 Regular predictions: Travel={len(travel_corridors)}, "
                          f"Bedding={len(bedding_zones)}, Feeding={len(feeding_areas)}")
                    
                else:
                    print(f"     ❌ Request failed: {response.status_code}")
                    print(f"        Error: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"     ❌ Connection error: {e}")
    
    print("\n" + "=" * 60)
    print("🏹 Mature Buck Integration Test Complete!")
    print("\nTo view the integrated predictions:")
    print("1. Open http://localhost:8501 in your browser")
    print("2. Click on a Vermont location on the map")
    print("3. Look for dark red crosshair markers for mature buck opportunities")
    print("4. Check the prediction notes for mature buck analysis details")

if __name__ == "__main__":
    test_mature_buck_integration()
