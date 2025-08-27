#!/usr/bin/env python3
"""
Confidence Score Verification Test
Tests that prediction confidence is now displaying correctly in frontend
"""

import requests
import json

def test_confidence_scores():
    """Test that confidence scores are now working correctly"""
    print("📊 CONFIDENCE SCORE VERIFICATION TEST")
    print("=" * 60)
    
    locations = [
        {"name": "Vermont", "lat": 44.2619, "lon": -72.5806},
        {"name": "Maine", "lat": 45.2538, "lon": -69.4455},
        {"name": "New York", "lat": 43.1566, "lon": -74.2478}
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
            
            # Extract confidence data
            movement_pred = prediction.get('mature_buck_analysis', {}).get('movement_prediction', {})
            movement_prob = movement_pred.get('movement_probability', 0)
            confidence_score = movement_pred.get('confidence_score', 0)
            
            print(f"\n🌲 {location['name'].upper()}:")
            print(f"   📍 Coordinates: {location['lat']:.4f}, {location['lon']:.4f}")
            print(f"   🎯 Movement Probability: {movement_prob}%")
            print(f"   📊 Confidence Score: {confidence_score}%")
            
            if confidence_score > 0:
                print(f"   ✅ Confidence Score: WORKING")
            else:
                print(f"   ❌ Confidence Score: STILL 0")
                
        except Exception as e:
            print(f"❌ {location['name']}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("🎯 FRONTEND DISPLAY EXPECTATION:")
    print("=" * 60)
    print("The frontend should now show:")
    print("• **Prediction Confidence: [NON-ZERO VALUE]%**")
    print("Instead of:")
    print("• **Prediction Confidence: 0%**")
    
    print("\n🌐 To verify in browser:")
    print("1. Go to http://localhost:8501")
    print("2. Enter any coordinates (e.g., 44.2619, -72.5806)")
    print("3. Click 'Generate Hunting Predictions'")
    print("4. Look for 'Prediction Confidence' in stand details")
    print("5. It should show a percentage > 0%")

if __name__ == "__main__":
    test_confidence_scores()
