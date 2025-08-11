#!/usr/bin/env python3
"""
Test mature buck integration with better terrain
"""

import requests
import json
from datetime import datetime

def test_remote_location():
    """Test mature buck integration in a more remote Vermont location"""
    
    # More remote Vermont location (Green Mountain National Forest area)
    request_data = {
        "lat": 43.9737,
        "lon": -73.1817,  # More remote forest area
        "date_time": datetime.now().isoformat(),
        "season": "rut",
        "suggestion_threshold": 5.0,
        "min_suggestion_rating": 8.0
    }
    
    print("🏹 Testing Mature Buck Integration - Remote Vermont Location")
    print("=" * 60)
    print(f"📍 Location: Remote Green Mountain Area ({request_data['lat']}, {request_data['lon']})")
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
                
                # Check if we get mature buck opportunities
                mature_buck_opportunities = prediction.get('mature_buck_opportunities')
                if mature_buck_opportunities and viable:
                    features = mature_buck_opportunities.get('features', [])
                    print(f"🏹 Mature Buck Opportunities: {len(features)} found")
                    
                    for i, feature in enumerate(features, 1):
                        props = feature.get('properties', {})
                        coords = feature.get('geometry', {}).get('coordinates', [0, 0])
                        
                        print(f"   #{i}: {props.get('description', 'Opportunity')}")
                        print(f"       GPS: {coords[1]:.6f}, {coords[0]:.6f}")
                        print(f"       Confidence: {props.get('confidence', 'N/A')}%")
                        print(f"       Terrain Score: {props.get('terrain_score', 'N/A'):.1f}%")
                        print()
                    
                    print("🎯 SUCCESS! Mature buck opportunities found in remote location!")
                    print("These would appear as dark red crosshair markers on the map.")
                else:
                    print("❌ No mature buck opportunities found - terrain may still be unsuitable")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_remote_location()
