#!/usr/bin/env python3
"""
Demo Script: Vermont Deer Prediction with Scouting Integration

This script demonstrates the complete workflow of the new scouting-enhanced
deer prediction system.
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8501"

def test_scouting_workflow():
    """Demonstrate the complete scouting workflow"""
    
    print("🦌 Vermont Deer Prediction with Scouting Demo")
    print("=" * 50)
    
    # Test coordinates (Vermont location)
    lat, lon = 44.5588, -72.5778
    
    print(f"📍 Demo Location: {lat}, {lon}")
    print()
    
    # 1. Add some scouting observations
    print("1. 🔍 Adding Scouting Observations...")
    
    observations = [
        {
            "lat": lat,
            "lon": lon,
            "observation_type": "Fresh Scrape",
            "confidence": 9,
            "scrape_details": {
                "size": "Large",
                "freshness": "Very Fresh",
                "licking_branch": True,
                "multiple_scrapes": False
            },
            "notes": "Huge fresh scrape with strong scent - found this morning"
        },
        {
            "lat": lat + 0.001,  # Slightly offset
            "lon": lon + 0.001,
            "observation_type": "Rub Line",
            "confidence": 8,
            "rub_details": {
                "tree_diameter_inches": 10,
                "rub_height_inches": 42,
                "direction": "North",
                "tree_species": "maple",
                "multiple_rubs": True
            },
            "notes": "Fresh rub line on mature maples - definitely a mature buck"
        },
        {
            "lat": lat - 0.0005,
            "lon": lon - 0.0005,
            "observation_type": "Bedding Area",
            "confidence": 7,
            "bedding_details": {
                "number_of_beds": 3,
                "bed_size": "Large (Mature Buck)",
                "cover_type": "Thick Brush",
                "thermal_advantage": True
            },
            "notes": "Large beds in thick cover with good thermal protection"
        }
    ]
    
    observation_ids = []
    for i, obs in enumerate(observations, 1):
        try:
            response = requests.post(
                f"{BACKEND_URL}/scouting/add_observation",
                json=obs,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                observation_ids.append(result['observation_id'])
                print(f"   ✅ Added {obs['observation_type']} - ID: {result['observation_id']}")
                print(f"      🚀 Confidence Boost: +{result['confidence_boost']:.1f}")
            else:
                print(f"   ❌ Failed to add observation: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print()
    
    # 2. Get scouting analytics
    print("2. 📊 Analyzing Scouting Data...")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/scouting/analytics",
            params={'lat': lat, 'lon': lon, 'radius_miles': 2}
        )
        
        if response.status_code == 200:
            analytics = response.json()
            basic_stats = analytics.get('basic_analytics', {})
            
            print(f"   📝 Total Observations: {basic_stats.get('total_observations', 0)}")
            print(f"   📊 Average Confidence: {basic_stats.get('average_confidence', 0):.1f}/10")
            print(f"   🦌 Mature Buck Indicators: {basic_stats.get('mature_buck_indicators', 0)}")
            
            obs_by_type = basic_stats.get('observations_by_type', {})
            if obs_by_type:
                print("   🔍 Observation Types:")
                for obs_type, count in obs_by_type.items():
                    print(f"      • {obs_type}: {count}")
        
    except Exception as e:
        print(f"   ❌ Analytics Error: {e}")
    
    print()
    
    # 3. Make enhanced prediction
    print("3. 🎯 Generating Enhanced Prediction...")
    
    prediction_data = {
        "lat": lat,
        "lon": lon,
        "date_time": "2024-11-15T06:30:00",  # Rut season morning
        "season": "rut"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/predict",
            json=prediction_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            prediction = response.json()
            
            # Check if prediction was enhanced
            if 'mature_buck_analysis' in prediction:
                mature_data = prediction['mature_buck_analysis']
                movement_data = mature_data.get('movement_prediction', {})
                
                if movement_data:
                    movement_prob = movement_data.get('movement_probability', 0)
                    confidence = movement_data.get('confidence_score', 0)
                    
                    print(f"   🦌 Movement Probability: {movement_prob:.0f}%")
                    print(f"   📊 Prediction Confidence: {confidence:.0f}%")
                    
                    if movement_prob >= 75:
                        print("   🟢 HIGH MOVEMENT PROBABILITY - EXCELLENT HUNTING!")
                    elif movement_prob >= 50:
                        print("   🟡 MODERATE MOVEMENT - GOOD HUNTING POTENTIAL")
                    else:
                        print("   🔴 LOW MOVEMENT - CONSIDER DIFFERENT LOCATION/TIME")
                    
                    # Check for scouting enhancement
                    if confidence > 80:
                        print("   🔍 ✨ PREDICTION ENHANCED BY SCOUTING DATA!")
                
                # Show stand recommendations
                stands = mature_data.get('stand_recommendations', [])
                if stands:
                    print(f"   🪜 Stand Recommendations: {len(stands)} locations found")
                    for i, stand in enumerate(stands[:2], 1):  # Show top 2
                        coords = stand.get('coordinates', {})
                        stand_confidence = stand.get('confidence', 0)
                        print(f"      Stand #{i}: {coords.get('lat', 0):.6f}, {coords.get('lon', 0):.6f}")
                        print(f"                 Confidence: {stand_confidence:.0f}%")
        
    except Exception as e:
        print(f"   ❌ Prediction Error: {e}")
    
    print()
    
    # 4. Show access URLs
    print("4. 🌐 Access Your System:")
    print(f"   🎯 Frontend Interface: {FRONTEND_URL}")
    print(f"   📚 API Documentation: {BACKEND_URL}/docs")
    print(f"   🔍 Scouting Types: {BACKEND_URL}/scouting/types")
    
    print()
    print("=" * 50)
    print("🦌 Demo Complete! Your scouting-enhanced deer prediction system is ready!")
    print()
    print("💡 What you can do now:")
    print("   • Open the frontend to see the new scouting interface")
    print("   • Click on maps to add real scouting observations")
    print("   • View analytics of your scouting data")
    print("   • Get enhanced predictions based on real deer sign")
    print("   • Export/import scouting data for field use")

if __name__ == "__main__":
    test_scouting_workflow()
