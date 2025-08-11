#!/usr/bin/env python3
"""
Test Enhanced Mature Buck Integration with Main API

This script tests that the enhanced mature buck predictions integrate properly 
with the main prediction API.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from main import generate_mature_buck_predictions
import json

def test_main_api_integration():
    """Test that the enhanced system integrates with the main API"""
    print("🔗 Testing Enhanced Mature Buck Integration with Main API")
    print("=" * 60)
    
    # Test coordinates (Vermont location)
    lat = 44.2619
    lon = -72.5806
    
    print(f"📍 Test Location: {lat:.4f}, {lon:.4f}")
    print("🔄 Calling main API generate_mature_buck_predictions...")
    print()
    
    try:
        # Call the main API function
        result = generate_mature_buck_predictions(lat, lon)
        
        print("✅ API call successful!")
        print(f"🎯 Overall Suitability: {result.get('overall_suitability', 0):.1f}%")
        print()
        
        # Check movement predictions
        movement_prediction = result.get('movement_prediction', {})
        if movement_prediction:
            print("🦌 MOVEMENT PREDICTION DATA")
            print("-" * 40)
            print(f"Movement Probability: {movement_prediction.get('movement_probability', 0):.1f}%")
            print(f"Confidence Score: {movement_prediction.get('confidence_score', 0):.1f}%")
            
            # Check spatial predictions
            corridors = movement_prediction.get('movement_corridors', [])
            bedding = movement_prediction.get('bedding_predictions', [])
            feeding = movement_prediction.get('feeding_predictions', [])
            
            print(f"Movement Corridors: {len(corridors)} identified")
            print(f"Bedding Locations: {len(bedding)} identified")
            print(f"Feeding Zones: {len(feeding)} identified")
            print()
            
            if corridors:
                print("🛤️  Sample Movement Corridor:")
                corridor = corridors[0]
                print(f"   Type: {corridor.get('type', 'unknown')}")
                print(f"   📍 {corridor.get('lat', 0):.6f}, {corridor.get('lon', 0):.6f}")
                print(f"   Confidence: {corridor.get('confidence', 0):.1f}%")
                print()
        
        # Check stand recommendations
        stand_recommendations = result.get('stand_recommendations', [])
        if stand_recommendations:
            print("🏹 STAND RECOMMENDATIONS")
            print("-" * 40)
            print(f"Number of recommendations: {len(stand_recommendations)}")
            
            # Show first recommendation
            if stand_recommendations:
                rec = stand_recommendations[0]
                print(f"Top Recommendation: {rec.get('type', 'unknown')}")
                coords = rec.get('coordinates', {})
                print(f"📍 {coords.get('lat', 0):.6f}, {coords.get('lon', 0):.6f}")
                print(f"Confidence: {rec.get('confidence', 0):.1f}%")
                print(f"Justification: {rec.get('terrain_justification', 'N/A')}")
                print()
        
        print("✅ Enhanced mature buck integration test successful!")
        
    except Exception as e:
        print(f"❌ API integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_main_api_integration()
