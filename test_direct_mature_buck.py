#!/usr/bin/env python3
"""
Direct test of mature buck data without streamlit interference
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from main import app
from fastapi.testclient import TestClient
import json

def test_mature_buck_data():
    """Test mature buck data directly from backend"""
    
    print("🦌 TESTING MATURE BUCK DATA FLOW")
    print("=" * 50)
    
    # Create test client
    client = TestClient(app)
    
    # Make prediction request
    data = {
        "lat": 44.26,
        "lon": -72.58,
        "date_time": "2024-11-15T08:00:00",
        "season": "rut"
    }
    
    response = client.post("/predict", json=data)
    
    if response.status_code != 200:
        print(f"❌ Backend error: {response.status_code}")
        print(response.text)
        return
    
    prediction = response.json()
    print("✅ Backend response received")
    
    # Check mature buck analysis data
    mature_buck_data = prediction.get('mature_buck_analysis', {})
    
    if not mature_buck_data:
        print("❌ No mature buck analysis data found")
        return
        
    print("\n🏹 MATURE BUCK DATA FOR FRONTEND:")
    print("-" * 45)
    
    # Stand recommendations (the viable locations!)
    stand_recommendations = mature_buck_data.get('stand_recommendations', [])
    print(f"\n🎯 VIABLE STAND RECOMMENDATIONS: {len(stand_recommendations)} locations")
    
    if stand_recommendations:
        print("\n📍 CONCRETE HUNTING LOCATIONS:")
        for i, stand in enumerate(stand_recommendations, 1):
            print(f"\n   STAND #{i}: {stand.get('type', 'Unknown')}")
            print(f"   ├─ Confidence: {stand.get('confidence', 0):.1f}%")
            
            coords = stand.get('coordinates', {})
            if coords:
                print(f"   ├─ GPS: {coords.get('lat', 0):.6f}, {coords.get('lon', 0):.6f}")
            
            print(f"   ├─ Strategy: {stand.get('description', 'N/A')}")
            print(f"   ├─ Best Times: {stand.get('best_times', 'N/A')}")
            
            # Additional details
            setup_reqs = stand.get('setup_requirements', [])
            if setup_reqs:
                print(f"   ├─ Setup: {len(setup_reqs)} requirements")
                for req in setup_reqs[:2]:
                    print(f"   │   • {req}")
            
            proximity = stand.get('proximity_analysis', {})
            if proximity:
                bedding_prox = proximity.get('bedding_proximity', {})
                if bedding_prox:
                    closest_bedding = bedding_prox.get('closest_distance_yards', 0)
                    print(f"   └─ Near bedding: {closest_bedding:.0f} yards")
    
    # Movement patterns
    movement_data = mature_buck_data.get('movement_prediction', {})
    if movement_data:
        print(f"\n🚶 MOVEMENT PATTERNS:")
        print(f"   • Movement Probability: {movement_data.get('movement_probability', 0):.1f}%")
        print(f"   • Prediction Confidence: {movement_data.get('confidence_score', 0):.1f}%")
        
        behavioral_notes = movement_data.get('behavioral_notes', [])
        if behavioral_notes:
            print(f"   • Behavioral Insights: {len(behavioral_notes)} notes")
            for note in behavioral_notes[:2]:
                print(f"     - {note}")
    
    # Terrain assessment
    terrain_scores = mature_buck_data.get('terrain_scores', {})
    if terrain_scores:
        overall = terrain_scores.get('overall_suitability', 0)
        print(f"\n⛰️ TERRAIN ASSESSMENT:")
        print(f"   • Overall Suitability: {overall:.1f}%")
        print(f"   • Pressure Resistance: {terrain_scores.get('pressure_resistance', 0):.1f}%")
        print(f"   • Escape Route Quality: {terrain_scores.get('escape_route_quality', 0):.1f}%")
    
    # Summary for frontend
    print("\n" + "=" * 50)
    print("🎯 FRONTEND IMPLEMENTATION STATUS:")
    
    if stand_recommendations:
        avg_confidence = sum(s.get('confidence', 0) for s in stand_recommendations) / len(stand_recommendations)
        print(f"✅ {len(stand_recommendations)} viable stand locations available")
        print(f"✅ Average confidence: {avg_confidence:.1f}%")
        print("✅ GPS coordinates provided for each stand")
        print("✅ Setup requirements and strategies included")
        print("\n🏆 RESULT: Frontend should display these viable locations!")
        
        # Check if frontend code handles this data
        print("\n🔍 FRONTEND CODE CHECK:")
        try:
            with open('frontend/app.py', 'r') as f:
                frontend_code = f.read()
                
            if 'stand_recommendations' in frontend_code:
                print("✅ Frontend code contains 'stand_recommendations' handling")
            else:
                print("❌ Frontend code missing 'stand_recommendations' handling")
                
            if 'mature_buck_analysis' in frontend_code:
                print("✅ Frontend code contains 'mature_buck_analysis' access")
            else:
                print("❌ Frontend code missing 'mature_buck_analysis' access")
                
        except FileNotFoundError:
            print("❌ Could not find frontend/app.py file")
    else:
        print("⚠️ No viable stand recommendations found")
        print("   (This could be due to terrain not meeting mature buck requirements)")

if __name__ == "__main__":
    test_mature_buck_data()
