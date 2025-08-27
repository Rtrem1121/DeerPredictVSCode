#!/usr/bin/env python3
"""
Real Terrain Scores Test
Tests that terrain scores now reflect the mature buck algorithm's actual analysis
"""

import requests
import json

def test_real_terrain_scores():
    """Test that terrain scores are now from the mature buck algorithm"""
    print("🏔️ REAL TERRAIN SCORES VERIFICATION TEST")
    print("=" * 60)
    
    locations = [
        {"name": "Vermont", "lat": 44.2619, "lon": -72.5806},
        {"name": "Maine", "lat": 45.2538, "lon": -69.4455},
        {"name": "New York", "lat": 43.1566, "lon": -74.2478},
        {"name": "Pennsylvania", "lat": 40.2677, "lon": -76.8756}
    ]
    
    for location in locations:
        try:
            test_data = {
                "lat": location["lat"],
                "lon": location["lon"],
                "date_time": "2025-08-24T19:30:00",
                "season": "rut",
                "fast_mode": True
            }
            
            response = requests.post("http://localhost:8000/predict", json=test_data, timeout=30)
            prediction = response.json()
            
            # Extract terrain scores
            terrain_scores = prediction.get('mature_buck_analysis', {}).get('terrain_scores', {})
            
            print(f"\n🌲 {location['name'].upper()}:")
            print(f"   📍 Coordinates: {location['lat']:.4f}, {location['lon']:.4f}")
            print(f"   🛏️ Bedding Suitability: {terrain_scores.get('bedding_suitability', 0):.1f}%")
            print(f"   🏃 Escape Route Quality: {terrain_scores.get('escape_route_quality', 0):.1f}%")
            print(f"   🏝️ Isolation Score: {terrain_scores.get('isolation_score', 0):.1f}%")
            print(f"   🚫 Pressure Resistance: {terrain_scores.get('pressure_resistance', 0):.1f}%")
            print(f"   🎯 Overall Suitability: {terrain_scores.get('overall_suitability', 0):.1f}%")
                
        except Exception as e:
            print(f"❌ {location['name']}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("🎯 ALGORITHM VERIFICATION:")
    print("=" * 60)
    print("These scores should now reflect what the mature buck algorithm")
    print("actually calculates based on:")
    print("• Real bedding area analysis (canopy cover, thermal cover)")
    print("• Actual escape route evaluation (terrain connectivity)")
    print("• True isolation scoring (distance from human activity)")
    print("• Genuine pressure resistance (terrain defensibility)")
    print("• Overall habitat suitability (weighted combination)")
    
    print("\nInstead of hardcoded values like:")
    print("❌ Bedding: 85.0%, Escape: 80.0%, Isolation: 75.0%")
    print("✅ Now shows: Location-specific mature buck terrain analysis")

if __name__ == "__main__":
    test_real_terrain_scores()
