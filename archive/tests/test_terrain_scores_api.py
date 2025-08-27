#!/usr/bin/env python3
"""
Test terrain scores by making direct API calls to the backend
"""
import requests
import json

def test_terrain_scores_api():
    """Test terrain scores via API calls"""
    backend_url = "http://localhost:8000"
    
    # Test data - Vermont coordinates
    test_requests = [
        {
            "name": "Vermont Mountain Location",
            "lat": 44.0708,
            "lon": -72.8429,
            "date_time": "2024-10-15T06:00:00",
            "season": "early_season",
            "weather": {"temperature": 45, "wind_speed": 5, "wind_direction": 180}
        },
        {
            "name": "Vermont Valley Location", 
            "lat": 44.0500,
            "lon": -72.8000,
            "date_time": "2024-10-15T06:00:00",
            "season": "early_season",
            "weather": {"temperature": 45, "wind_speed": 5, "wind_direction": 180}
        },
        {
            "name": "Vermont Ridge Location",
            "lat": 44.1000,
            "lon": -72.9000,
            "date_time": "2024-10-15T06:00:00",
            "season": "early_season", 
            "weather": {"temperature": 45, "wind_speed": 5, "wind_direction": 180}
        },
        {
            "name": "Vermont Forest Location",
            "lat": 44.2000,
            "lon": -72.7000,
            "date_time": "2024-10-15T06:00:00",
            "season": "early_season", 
            "weather": {"temperature": 45, "wind_speed": 5, "wind_direction": 180}
        },
        {
            "name": "Vermont Lake Location",
            "lat": 44.1500,
            "lon": -72.8500,
            "date_time": "2024-10-15T06:00:00",
            "season": "early_season", 
            "weather": {"temperature": 45, "wind_speed": 5, "wind_direction": 180}
        }
    ]
    
    for i, test_req in enumerate(test_requests, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test_req['name']}")
        print(f"Coordinates: {test_req['lat']}, {test_req['lon']}")
        print("="*60)
        
        try:
            # Make prediction request
            response = requests.post(
                f"{backend_url}/predict",
                json=test_req,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Debug: Print what we're getting
                print("Available keys in response:", list(data.keys()))
                
                # Check if mature_buck_analysis exists
                if 'mature_buck_analysis' in data:
                    mature_buck_data = data['mature_buck_analysis']
                    print("mature_buck_analysis keys:", list(mature_buck_data.keys()))
                    
                    # Extract terrain scores
                    terrain_scores = mature_buck_data.get('terrain_scores', {})
                    
                    print("Terrain Scores:")
                    print(f"  Bedding Suitability: {terrain_scores.get('bedding_suitability', 'N/A'):.1f}%")
                    print(f"  Escape Route Quality: {terrain_scores.get('escape_route_quality', 'N/A'):.1f}%")
                    print(f"  Isolation Score: {terrain_scores.get('isolation_score', 'N/A'):.1f}%")
                    print(f"  Pressure Resistance: {terrain_scores.get('pressure_resistance', 'N/A'):.1f}%")
                    print(f"  Overall Suitability: {terrain_scores.get('overall_suitability', 'N/A'):.1f}%")
                    
                    # Check if we're getting the fallback values
                    isolation = terrain_scores.get('isolation_score', 0)
                    pressure = terrain_scores.get('pressure_resistance', 0)
                    
                    if isolation == 50.0 and pressure == 50.0:
                        print("⚠️  WARNING: Getting fallback values (50.0) - analysis may be timing out")
                    elif isolation == pressure:
                        print(f"❌ BUG: Isolation ({isolation}) and Pressure ({pressure}) scores are identical")
                    else:
                        print("✅ Scores look varied and calculated properly")
                        
                    # Check if we're getting movement prediction fallback too
                    movement = mature_buck_data.get('movement_prediction', {})
                    if movement.get('movement_probability') == 50.0:
                        behavioral_notes = movement.get('behavioral_notes', [])
                        if 'Limited analysis due to timeout' in behavioral_notes:
                            print("⚠️  CONFIRMED: Analysis is timing out - see 'Limited analysis due to timeout'")
                else:
                    print("❌ mature_buck_analysis not found in response!")
                    print("Available keys:", list(data.keys()))
                
                # Check if we're getting the fallback values
                isolation = terrain_scores.get('isolation_score', 0)
                pressure = terrain_scores.get('pressure_resistance', 0)
                
                if isolation == 50.0 and pressure == 50.0:
                    print("⚠️  WARNING: Getting fallback values (50.0) - analysis may be timing out")
                elif isolation == pressure:
                    print("❌ BUG: Isolation and Pressure scores are identical")
                else:
                    print("✅ Scores look varied and calculated properly")
                    
                # Check if we're getting movement prediction fallback too
                movement = data.get('mature_buck_data', {}).get('movement_prediction', {})
                if movement.get('movement_probability') == 50.0:
                    behavioral_notes = movement.get('behavioral_notes', [])
                    if 'Limited analysis due to timeout' in behavioral_notes:
                        print("⚠️  CONFIRMED: Analysis is timing out - see 'Limited analysis due to timeout'")
                
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("Testing terrain scores via API calls...")
    print("This will help us see if the backend is calculating different scores")
    test_terrain_scores_api()
