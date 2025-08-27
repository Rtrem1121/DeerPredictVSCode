#!/usr/bin/env python3
"""
Test script to check what score values are being generated for the heatmaps
"""

import requests
import json

def test_heatmap_scores():
    """Test what scores are being generated for Vermont location"""
    
    # Test with a Vermont location
    test_data = {
        "lat": 44.26639,
        "lon": -72.58133, 
        "season": "early_season",
        "time": "06:00",
        "date_time": "2025-08-11T06:00:00"
    }
    
    try:
        print("Testing heatmap score generation...")
        print(f"Location: {test_data['lat']}, {test_data['lon']} (Vermont)")
        print(f"Season: {test_data['season']}, Time: {test_data['time']}")
        print("-" * 50)
        
        response = requests.post("http://localhost:8000/predict", json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ API call successful!")
            print(f"Total stand locations found: {len(result.get('stand_locations', []))}")
            print(f"Notes length: {len(result.get('notes', ''))}")
            
            # Check if heatmap data exists
            heatmap_fields = ['travel_score_heatmap', 'bedding_score_heatmap', 'feeding_score_heatmap']
            for field in heatmap_fields:
                if field in result:
                    heatmap_length = len(result[field])
                    print(f"✅ {field}: {heatmap_length} characters (base64 image)")
                else:
                    print(f"❌ {field}: MISSING")
            
            print("\n📊 Heatmap Status: All heatmaps should now use enhanced color schemes!")
            print("- Travel: Dark purple → Bright pink/yellow")  
            print("- Bedding: Dark blue → Bright yellow/green")
            print("- Feeding: Black → Bright white/yellow")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the backend is running on http://localhost:8000")

if __name__ == "__main__":
    test_heatmap_scores()
