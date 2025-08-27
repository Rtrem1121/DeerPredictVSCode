#!/usr/bin/env python3
"""
Quick test of mature buck integration with single prediction
"""

import requests
import json
from datetime import datetime

def test_single_prediction():
    """Test one prediction with mature buck integration"""
    
    # Vermont test location
    request_data = {
        "lat": 44.2601,
        "lon": -72.5806,
        "date_time": datetime.now().isoformat(),
        "season": "rut",
        "suggestion_threshold": 5.0,
        "min_suggestion_rating": 8.0
    }
    
    print("🏹 Testing Mature Buck Integration - Single Prediction")
    print("=" * 60)
    print(f"📍 Location: Montpelier, VT ({request_data['lat']}, {request_data['lon']})")
    print(f"🦌 Season: {request_data['season']}")
    print()
    
    try:
        response = requests.post(
            "http://localhost:8000/predict",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            prediction = response.json()
            
            print("✅ Prediction successful!")
            print()
            
            # Check regular deer predictions
            travel_features = len(prediction.get('travel_corridors', {}).get('features', []))
            bedding_features = len(prediction.get('bedding_zones', {}).get('features', []))
            feeding_features = len(prediction.get('feeding_areas', {}).get('features', []))
            
            print(f"🦌 Regular Deer Predictions:")
            print(f"   Travel Corridors: {travel_features}")
            print(f"   Bedding Zones: {bedding_features}")
            print(f"   Feeding Areas: {feeding_features}")
            print()
            
            # Check mature buck predictions
            mature_buck_opportunities = prediction.get('mature_buck_opportunities')
            if mature_buck_opportunities:
                features = mature_buck_opportunities.get('features', [])
                print(f"🏹 Mature Buck Opportunities: {len(features)} found")
                
                for i, feature in enumerate(features, 1):
                    props = feature.get('properties', {})
                    coords = feature.get('geometry', {}).get('coordinates', [0, 0])
                    
                    print(f"   #{i}: {props.get('description', 'Opportunity')}")
                    print(f"       GPS: {coords[1]:.6f}, {coords[0]:.6f}")
                    print(f"       Confidence: {props.get('confidence', 'N/A')}%")
                    print(f"       Terrain Score: {props.get('terrain_score', 'N/A'):.1f}%")
                    print(f"       Movement Probability: {props.get('movement_probability', 'N/A'):.1f}%")
                    print(f"       Pressure Resistance: {props.get('pressure_resistance', 'N/A'):.1f}%")
                    print()
            else:
                print("❌ No mature buck opportunities found")
                print()
            
            # Check mature buck analysis
            mature_buck_analysis = prediction.get('mature_buck_analysis')
            if mature_buck_analysis:
                viable = mature_buck_analysis.get('viable_location', False)
                confidence_summary = mature_buck_analysis.get('confidence_summary', {})
                
                print(f"📊 Mature Buck Analysis:")
                print(f"   Viable Location: {viable}")
                print(f"   Overall Suitability: {confidence_summary.get('overall_suitability', 0):.1f}%")
                print(f"   Movement Confidence: {confidence_summary.get('movement_confidence', 0):.1f}%")
                print(f"   Pressure Tolerance: {confidence_summary.get('pressure_tolerance', 0):.1f}%")
                print()
                
                # Show terrain scores
                terrain_scores = mature_buck_analysis.get('terrain_scores', {})
                if terrain_scores:
                    print(f"🏔️ Terrain Assessment:")
                    print(f"   Bedding Suitability: {terrain_scores.get('bedding_suitability', 0):.1f}%")
                    print(f"   Escape Route Quality: {terrain_scores.get('escape_route_quality', 0):.1f}%")
                    print(f"   Isolation Score: {terrain_scores.get('isolation_score', 0):.1f}%")
                    print(f"   Pressure Resistance: {terrain_scores.get('pressure_resistance', 0):.1f}%")
                    print()
            
            print("=" * 60)
            print("🎯 Success! Mature buck integration is working properly.")
            print()
            print("To view in browser:")
            print("1. Open http://localhost:8501")
            print("2. Click on the map at the test location")
            print("3. Look for dark red crosshair markers (🎯)")
            print("4. Check the prediction notes for mature buck details")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_single_prediction()
