#!/usr/bin/env python3
"""
Debug Weather Analysis - Cold Front Detection Issue
"""
import requests
import json

def test_weather_analysis():
    """Test the production API and examine weather data in detail"""
    
    # Test coordinates from user report
    test_coords = [
        {"lat": 43.3140, "lon": -73.2306, "name": "Location 1"},
        {"lat": 43.3165, "lon": -73.2150, "name": "Location 2"}, 
        {"lat": 43.3180, "lon": -73.2100, "name": "Location 3"}
    ]
    
    url = "http://localhost:8000/analyze-prediction-detailed"
    
    for coord in test_coords:
        print(f"\n🌤️ TESTING WEATHER ANALYSIS - {coord['name']}")
        print("=" * 60)
        print(f"📍 Coordinates: {coord['lat']}, {coord['lon']}")
        
        payload = {
            "lat": coord["lat"],
            "lon": coord["lon"],
            "date_time": "2025-09-02T07:00:00",
            "time_of_day": 7,
            "season": "fall",
            "hunting_pressure": "low"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract weather data
                weather_data = data.get("prediction", {}).get("weather_data", {})
                
                print(f"\n🌡️ WEATHER DATA ANALYSIS:")
                print(f"   Temperature: {weather_data.get('temperature', 'N/A')}°F")
                print(f"   Humidity: {weather_data.get('humidity', 'N/A')}%")
                print(f"   Wind Speed: {weather_data.get('wind_speed', 'N/A')} mph")
                print(f"   Wind Direction: {weather_data.get('wind_direction', 'N/A')}°")
                print(f"   Pressure: {weather_data.get('pressure', 'N/A')} hPa")
                
                # Look for cold front data
                print(f"\n❄️ COLD FRONT ANALYSIS:")
                print(f"   Is Cold Front: {weather_data.get('is_cold_front', 'N/A')}")
                print(f"   Cold Front Strength: {weather_data.get('cold_front_strength', 'N/A')}")
                print(f"   Weather Modifier: {weather_data.get('weather_modifier', 'N/A')}")
                
                # Movement confidence
                movement_conf = data.get("prediction", {}).get("confidence_score", "N/A")
                print(f"   Movement Confidence: {movement_conf}")
                
                # Print all weather keys for debugging
                print(f"\n🔍 ALL WEATHER KEYS:")
                for key, value in weather_data.items():
                    print(f"   {key}: {value}")
                    
                # Check for barometric pressure trends
                if 'pressure_trend' in weather_data:
                    print(f"\n📈 PRESSURE TREND ANALYSIS:")
                    print(f"   Pressure Trend: {weather_data.get('pressure_trend', 'N/A')}")
                    print(f"   Pressure Change: {weather_data.get('pressure_change', 'N/A')}")
                    
        except Exception as e:
            print(f"❌ Error testing {coord['name']}: {str(e)}")

if __name__ == "__main__":
    test_weather_analysis()
