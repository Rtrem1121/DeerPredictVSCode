#!/usr/bin/env python3
"""
Location Variation Test
Tests that different locations now generate unique, location-specific predictions
"""

import requests
import json

def test_location_variations():
    """Test multiple locations to verify unique predictions"""
    print("🗺️ LOCATION VARIATION TEST")
    print("=" * 60)
    
    locations = [
        {"name": "Vermont", "lat": 44.2619, "lon": -72.5806},
        {"name": "New York", "lat": 43.1566, "lon": -74.2478},
        {"name": "Maine", "lat": 45.2538, "lon": -69.4455},
        {"name": "Pennsylvania", "lat": 40.2677, "lon": -76.8756},
        {"name": "New Hampshire", "lat": 43.9334, "lon": -71.5376}
    ]
    
    results = []
    
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
            
            # Extract primary stand info
            stands = prediction.get('mature_buck_analysis', {}).get('stand_recommendations', [])
            if stands:
                primary_stand = stands[0]
                result = {
                    "location": location["name"],
                    "coordinates": f"{location['lat']:.4f}, {location['lon']:.4f}",
                    "stand_type": primary_stand.get("type", "Unknown"),
                    "confidence": primary_stand.get("confidence", 0),
                    "reasoning": primary_stand.get("reasoning", "No reasoning")
                }
                results.append(result)
                print(f"✅ {location['name']}: {result['stand_type']} ({result['confidence']:.1f}%)")
            else:
                print(f"❌ {location['name']}: No stands generated")
                
        except Exception as e:
            print(f"❌ {location['name']}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("📊 DETAILED COMPARISON:")
    print("=" * 60)
    
    for result in results:
        print(f"\n🌲 {result['location'].upper()}:")
        print(f"   📍 Coordinates: {result['coordinates']}")
        print(f"   🎯 Stand Type: {result['stand_type']}")
        print(f"   📊 Confidence: {result['confidence']:.1f}%")
        print(f"   💭 Reasoning: {result['reasoning']}")
    
    # Check for variations
    print("\n" + "=" * 60)
    print("🔍 VARIATION ANALYSIS:")
    print("=" * 60)
    
    stand_types = [r["stand_type"] for r in results]
    confidences = [r["confidence"] for r in results]
    
    unique_types = len(set(stand_types))
    confidence_range = max(confidences) - min(confidences) if confidences else 0
    
    print(f"📈 Stand Type Variations: {unique_types} different types out of {len(results)} locations")
    print(f"📊 Confidence Range: {confidence_range:.1f}% spread")
    
    if unique_types > 1:
        print("✅ SUCCESS: Locations generate DIFFERENT stand types!")
    else:
        print("❌ ISSUE: All locations generate the SAME stand type")
        
    if confidence_range > 10:
        print("✅ SUCCESS: Confidence scores vary significantly by location!")
    else:
        print("❌ ISSUE: Confidence scores are too similar")
    
    print(f"\nStand types found: {', '.join(set(stand_types))}")
    
    return len(results) > 0 and unique_types > 1

if __name__ == "__main__":
    success = test_location_variations()
    print("\n" + "=" * 60)
    if success:
        print("🎉 LOCATION VARIATION TEST: ✅ PASSED")
        print("Different locations now generate unique predictions!")
    else:
        print("❌ LOCATION VARIATION TEST: FAILED")
        print("Locations still generating identical results")
