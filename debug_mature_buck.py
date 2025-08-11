#!/usr/bin/env python3
"""
Debug mature buck terrain scoring to understand low suitability
"""

import requests
import json
from datetime import datetime

def debug_mature_buck_scoring():
    """Debug why mature buck scores are low"""
    
    # Test location
    request_data = {
        "lat": 44.2601,
        "lon": -72.5806,
        "date_time": datetime.now().isoformat(),
        "season": "rut",
        "suggestion_threshold": 5.0,
        "min_suggestion_rating": 8.0
    }
    
    print("🔍 Debugging Mature Buck Terrain Scoring")
    print("=" * 60)
    print(f"📍 Location: {request_data['lat']}, {request_data['lon']}")
    print()
    
    try:
        response = requests.post(
            "http://localhost:8000/predict",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            prediction = response.json()
            
            # Get mature buck analysis
            mature_buck_analysis = prediction.get('mature_buck_analysis')
            if mature_buck_analysis:
                terrain_scores = mature_buck_analysis.get('terrain_scores', {})
                confidence_summary = mature_buck_analysis.get('confidence_summary', {})
                
                print("🏔️ Detailed Terrain Breakdown:")
                print(f"   Bedding Suitability: {terrain_scores.get('bedding_suitability', 0):.1f}%")
                print(f"   Escape Route Quality: {terrain_scores.get('escape_route_quality', 0):.1f}%") 
                print(f"   Isolation Score: {terrain_scores.get('isolation_score', 0):.1f}%")
                print(f"   Pressure Resistance: {terrain_scores.get('pressure_resistance', 0):.1f}%")
                print()
                print(f"📊 Overall Suitability: {confidence_summary.get('overall_suitability', 0):.1f}%")
                print(f"🎯 Threshold for markers: ≥60%")
                print()
                
                overall = confidence_summary.get('overall_suitability', 0)
                if overall >= 60:
                    print("✅ VIABLE: Dark red crosshair markers would appear!")
                    print("🎯 Users would see mature buck opportunities on the map")
                else:
                    print("❌ NOT VIABLE: No crosshair markers generated")
                    print("🚫 Terrain unsuitable for mature buck targeting")
                    print()
                    print("💡 Why this location failed:")
                    if terrain_scores.get('bedding_suitability', 0) < 20:
                        print("   • Poor bedding habitat (needs thick cover, elevation)")
                    if terrain_scores.get('escape_route_quality', 0) < 20:
                        print("   • Limited escape routes (needs terrain complexity)")
                    if terrain_scores.get('isolation_score', 0) < 60:
                        print("   • Too close to human activity (needs >800m isolation)")
                    if terrain_scores.get('pressure_resistance', 0) < 20:
                        print("   • Low pressure resistance (needs thick cover, difficult access)")
                
                print()
                print("🗺️ On the map you will see:")
                
                # Check what regular markers are present
                travel_features = len(prediction.get('travel_corridors', {}).get('features', []))
                bedding_features = len(prediction.get('bedding_zones', {}).get('features', []))
                feeding_features = len(prediction.get('feeding_areas', {}).get('features', []))
                mature_buck_features = len(prediction.get('mature_buck_opportunities', {}).get('features', []))
                
                if travel_features > 0:
                    print(f"   🔵 {travel_features} blue travel corridor markers")
                if bedding_features > 0:
                    print(f"   🔴 {bedding_features} red bedding area markers")
                if feeding_features > 0:
                    print(f"   🟢 {feeding_features} green feeding area markers")
                if mature_buck_features > 0:
                    print(f"   🎯 {mature_buck_features} DARK RED CROSSHAIR mature buck markers")
                else:
                    print(f"   🚫 0 dark red crosshair markers (terrain not suitable)")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_mature_buck_scoring()
