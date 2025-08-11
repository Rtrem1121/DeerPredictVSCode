#!/usr/bin/env python3
"""
Test script to verify mature buck data is properly flowing to frontend
"""

import requests
import json

def test_mature_buck_frontend_data():
    """Test what mature buck data is available to the frontend"""
    
    print("🦌 TESTING MATURE BUCK DATA FOR FRONTEND")
    print("=" * 50)
    
    # Make prediction request to backend
    url = "http://localhost:8000/predict"
    data = {
        "latitude": 44.26,
        "longitude": -72.58,
        "terrain_grid_size": 50
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        prediction = response.json()
        
        print("✅ Backend response received")
        
        # Check mature buck analysis data
        mature_buck_data = prediction.get('mature_buck_analysis', {})
        
        if not mature_buck_data:
            print("❌ No mature buck analysis data found")
            return
            
        print("\n🏹 MATURE BUCK DATA AVAILABLE TO FRONTEND:")
        print("-" * 45)
        
        # 1. Terrain Scores
        terrain_scores = mature_buck_data.get('terrain_scores', {})
        print("\n1️⃣ TERRAIN SUITABILITY SCORES:")
        for key, value in terrain_scores.items():
            print(f"   • {key}: {value:.1f}%")
        
        # 2. Movement Prediction
        movement_data = mature_buck_data.get('movement_prediction', {})
        print("\n2️⃣ MOVEMENT PREDICTION DATA:")
        print(f"   • Movement Probability: {movement_data.get('movement_probability', 0):.1f}%")
        print(f"   • Confidence Score: {movement_data.get('confidence_score', 0):.1f}%")
        
        behavioral_notes = movement_data.get('behavioral_notes', [])
        print(f"   • Behavioral Notes: {len(behavioral_notes)} insights")
        for i, note in enumerate(behavioral_notes[:3], 1):
            print(f"      {i}. {note}")
        
        # 3. Stand Recommendations (THE VIABLE LOCATIONS!)
        stand_recommendations = mature_buck_data.get('stand_recommendations', [])
        print(f"\n3️⃣ VIABLE STAND RECOMMENDATIONS: {len(stand_recommendations)} locations")
        
        if stand_recommendations:
            print("\n🎯 DETAILED STAND LOCATIONS:")
            for i, stand in enumerate(stand_recommendations, 1):
                print(f"\n   STAND #{i}:")
                print(f"   • Type: {stand.get('type', 'Unknown')}")
                print(f"   • Confidence: {stand.get('confidence', 0):.1f}%")
                
                coords = stand.get('coordinates', {})
                if coords:
                    print(f"   • GPS: {coords.get('lat', 0):.6f}, {coords.get('lon', 0):.6f}")
                
                print(f"   • Description: {stand.get('description', 'N/A')}")
                print(f"   • Best Times: {stand.get('best_times', 'N/A')}")
                
                # Check for additional details
                if stand.get('wind_optimized'):
                    wind_notes = stand.get('wind_notes', [])
                    print(f"   • Wind Notes: {len(wind_notes)} considerations")
                
                proximity = stand.get('proximity_analysis', {})
                if proximity:
                    bedding_prox = proximity.get('bedding_proximity', {})
                    feeding_prox = proximity.get('feeding_proximity', {})
                    if bedding_prox:
                        closest_bedding = bedding_prox.get('closest_distance_yards', 0)
                        print(f"   • Closest Bedding: {closest_bedding:.0f} yards")
                    if feeding_prox:
                        closest_feeding = feeding_prox.get('closest_distance_yards', 0)
                        if closest_feeding is not None:
                            print(f"   • Closest Feeding: {closest_feeding:.0f} yards")
        
        # 4. Opportunity Markers (High-Threshold Locations)
        opportunity_markers = mature_buck_data.get('opportunity_markers', [])
        print(f"\n4️⃣ HIGH-THRESHOLD OPPORTUNITY MARKERS: {len(opportunity_markers)} locations")
        
        if opportunity_markers:
            for i, marker in enumerate(opportunity_markers, 1):
                print(f"   • Marker #{i}: {marker.get('description', 'Unknown')}")
        else:
            overall_suitability = terrain_scores.get('overall_suitability', 0)
            print(f"   ℹ️ No markers (terrain suitability {overall_suitability:.1f}% < 60% threshold)")
        
        # 5. Confidence Summary
        confidence_summary = mature_buck_data.get('confidence_summary', {})
        print(f"\n5️⃣ CONFIDENCE SUMMARY:")
        for key, value in confidence_summary.items():
            print(f"   • {key}: {value:.1f}%")
        
        # Summary for frontend display
        print("\n" + "=" * 50)
        print("🎯 FRONTEND DISPLAY SUMMARY:")
        print(f"✅ Terrain Assessment: {len(terrain_scores)} metrics available")
        print(f"✅ Movement Patterns: {len(behavioral_notes)} behavioral insights")
        print(f"✅ Viable Stand Locations: {len(stand_recommendations)} concrete recommendations")
        print(f"✅ Opportunity Markers: {len(opportunity_markers)} high-confidence zones")
        
        if stand_recommendations:
            avg_confidence = sum(s.get('confidence', 0) for s in stand_recommendations) / len(stand_recommendations)
            print(f"🎯 Average Stand Confidence: {avg_confidence:.1f}%")
            print("\n🏆 RESULT: Frontend has viable mature buck locations to display!")
        else:
            print("\n⚠️ WARNING: No viable stand recommendations found")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_mature_buck_frontend_data()
