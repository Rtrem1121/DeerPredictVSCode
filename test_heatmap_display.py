#!/usr/bin/env python3
"""
Test script to verify heatmap display in the frontend
"""

import requests
import streamlit as st
import base64
from io import BytesIO
from PIL import Image

def test_heatmap_generation():
    """Test if backend generates valid heatmap data"""
    print("Testing heatmap generation from backend...")
    
    # Test API call
    payload = {
        "lat": 44.26,
        "lon": -72.58,
        "date_time": "2025-08-10T17:00:00Z",
        "season": "early_season"
    }
    
    try:
        response = requests.post("http://localhost:8000/predict", json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ API Response received")
        print(f"✅ Bedding heatmap size: {len(data.get('bedding_score_heatmap', ''))}")
        print(f"✅ Travel heatmap size: {len(data.get('travel_score_heatmap', ''))}")
        print(f"✅ Feeding heatmap size: {len(data.get('feeding_score_heatmap', ''))}")
        
        # Test if base64 images are valid
        for heatmap_name in ['bedding_score_heatmap', 'travel_score_heatmap', 'feeding_score_heatmap']:
            heatmap_data = data.get(heatmap_name)
            if heatmap_data:
                try:
                    # Decode base64 and check if it's a valid image
                    image_data = base64.b64decode(heatmap_data)
                    image = Image.open(BytesIO(image_data))
                    print(f"✅ {heatmap_name}: Valid {image.format} image ({image.size})")
                except Exception as e:
                    print(f"❌ {heatmap_name}: Invalid image data - {e}")
            else:
                print(f"❌ {heatmap_name}: Missing from response")
        
        return data
        
    except Exception as e:
        print(f"❌ Backend API Error: {e}")
        return None

def test_streamlit_display():
    """Test Streamlit display logic"""
    print("\nTesting Streamlit display logic...")
    
    # Get prediction data
    data = test_heatmap_generation()
    if not data:
        print("❌ Cannot test display - no data from backend")
        return
    
    # Test if st.image would work with the data
    for heatmap_name in ['bedding_score_heatmap', 'travel_score_heatmap', 'feeding_score_heatmap']:
        heatmap_data = data.get(heatmap_name)
        if heatmap_data:
            try:
                # This is what st.image expects
                image_src = f"data:image/png;base64,{heatmap_data}"
                print(f"✅ {heatmap_name}: Ready for st.image display (src length: {len(image_src)})")
            except Exception as e:
                print(f"❌ {heatmap_name}: Display format error - {e}")

if __name__ == "__main__":
    print("🔍 Troubleshooting Heatmap Display Issues")
    print("=" * 50)
    
    test_heatmap_generation()
    test_streamlit_display()
    
    print("\n" + "=" * 50)
    print("💡 If all tests pass, the issue might be:")
    print("1. Frontend container restart needed")
    print("2. Browser cache/cookies need clearing")
    print("3. Conditional logic in app.py hiding heatmaps")
    print("4. JavaScript/CSS blocking image display")
