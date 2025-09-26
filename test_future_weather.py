#!/usr/bin/env python3
"""
Test Future Weather Functionality

This script tests whether the deer hunting app actually fetches
future weather conditions when the hunt date is set to tomorrow.
"""

import requests
import json
from datetime import datetime, timedelta

def test_weather_date_functionality():
    """Test if hunt date affects weather data"""
    
    backend_url = "http://localhost:8000"
    
    # Test coordinates (Vermont)
    lat = 44.26639
    lon = -72.58133
    
    print("🧪 Testing Hunt Date Weather Functionality")
    print("=" * 50)
    
    # Test 1: Today's weather
    today = datetime.now().date()
    today_request = {
        "lat": lat,
        "lon": lon,
        "date_time": f"{today}T07:00:00",
        "hunt_period": "AM",
        "season": "rut"
    }
    
    print(f"\n📅 Test 1: Today's Date ({today})")
    print(f"Request: {today_request['date_time']}")
    
    try:
        response = requests.post(
            f"{backend_url}/predict",
            json=today_request,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            today_data = response.json()
            # Handle API wrapper format
            if 'success' in today_data and today_data.get('success'):
                today_weather = today_data.get('data', {}).get('weather_data', {})
            else:
                today_weather = today_data.get('weather_data', {})
                
            print(f"✅ Today's Weather:")
            print(f"   Temperature: {today_weather.get('temperature', 'N/A')}°F")
            print(f"   Wind: {today_weather.get('wind_direction', 'N/A')}° at {today_weather.get('wind_speed', 'N/A')} mph")
            print(f"   Conditions: {today_weather.get('conditions', 'N/A')}")
        else:
            print(f"❌ Today's request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error testing today's weather: {e}")
        return
    
    # Test 2: Tomorrow's weather
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    tomorrow_request = {
        "lat": lat,
        "lon": lon,
        "date_time": f"{tomorrow}T07:00:00",
        "hunt_period": "AM", 
        "season": "rut"
    }
    
    print(f"\n📅 Test 2: Tomorrow's Date ({tomorrow})")
    print(f"Request: {tomorrow_request['date_time']}")
    
    try:
        response = requests.post(
            f"{backend_url}/predict",
            json=tomorrow_request,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            tomorrow_data = response.json()
            # Handle API wrapper format
            if 'success' in tomorrow_data and tomorrow_data.get('success'):
                tomorrow_weather = tomorrow_data.get('data', {}).get('weather_data', {})
            else:
                tomorrow_weather = tomorrow_data.get('weather_data', {})
                
            print(f"✅ Tomorrow's Weather:")
            print(f"   Temperature: {tomorrow_weather.get('temperature', 'N/A')}°F")
            print(f"   Wind: {tomorrow_weather.get('wind_direction', 'N/A')}° at {tomorrow_weather.get('wind_speed', 'N/A')} mph")
            print(f"   Conditions: {tomorrow_weather.get('conditions', 'N/A')}")
        else:
            print(f"❌ Tomorrow's request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error testing tomorrow's weather: {e}")
        return
    
    # Test 3: Analysis and comparison
    print(f"\n🔍 Analysis:")
    print("=" * 30)
    
    # Compare weather data
    today_temp = today_weather.get('temperature', 0)
    tomorrow_temp = tomorrow_weather.get('temperature', 0)
    
    today_wind_dir = today_weather.get('wind_direction', 0)
    tomorrow_wind_dir = tomorrow_weather.get('wind_direction', 0)
    
    today_wind_speed = today_weather.get('wind_speed', 0)
    tomorrow_wind_speed = tomorrow_weather.get('wind_speed', 0)
    
    print(f"Temperature difference: {abs(today_temp - tomorrow_temp):.1f}°F")
    print(f"Wind direction difference: {abs(today_wind_dir - tomorrow_wind_dir):.0f}°")
    print(f"Wind speed difference: {abs(today_wind_speed - tomorrow_wind_speed):.1f} mph")
    
    # Determine if weather data is dynamic
    if (abs(today_temp - tomorrow_temp) > 0.1 or 
        abs(today_wind_dir - tomorrow_wind_dir) > 1 or 
        abs(today_wind_speed - tomorrow_wind_speed) > 0.1):
        print("\n✅ RESULT: Weather data appears to be DYNAMIC")
        print("   The app is likely using real forecast data for future dates.")
        print("   Changing hunt date DOES affect weather conditions.")
    else:
        print("\n❌ RESULT: Weather data appears to be STATIC")
        print("   The app may be using current weather for all dates.")
        print("   Changing hunt date may NOT affect weather conditions.")
    
    # Test 4: Check if forecast data is available
    print(f"\n📊 Forecast Data Check:")
    print("=" * 25)
    
    # Look for tomorrow_forecast in the data
    today_forecast = today_weather.get('tomorrow_forecast', {})
    tomorrow_forecast = tomorrow_weather.get('tomorrow_forecast', {})
    
    if today_forecast or tomorrow_forecast:
        print("✅ Forecast data structure found in API response")
        if today_forecast:
            print(f"   Today's forecast: {len(today_forecast)} fields")
        if tomorrow_forecast:
            print(f"   Tomorrow's forecast: {len(tomorrow_forecast)} fields")
    else:
        print("⚠️  No forecast data structure found in API response")
    
    # Check for hourly forecast data
    today_hourly = today_weather.get('next_48h_hourly', [])
    tomorrow_hourly = tomorrow_weather.get('next_48h_hourly', [])
    
    if today_hourly or tomorrow_hourly:
        print(f"✅ Hourly forecast data found")
        print(f"   Today's hourly data: {len(today_hourly)} hours")
        print(f"   Tomorrow's hourly data: {len(tomorrow_hourly)} hours")
    else:
        print("⚠️  No hourly forecast data found")
    
    # Final verdict
    print(f"\n🎯 FINAL VERDICT:")
    print("=" * 20)
    
    if (abs(today_temp - tomorrow_temp) > 2 or 
        abs(today_wind_dir - tomorrow_wind_dir) > 10 or 
        abs(today_wind_speed - tomorrow_wind_speed) > 2):
        print("✅ The app DOES use future weather data!")
        print("   Changing hunt date will give you tomorrow's forecast.")
        print("   Wind and weather conditions will be date-specific.")
    elif today_forecast or tomorrow_forecast or today_hourly or tomorrow_hourly:
        print("🟡 The app has forecast capability but may need refinement")
        print("   Forecast data structures exist but may not be fully utilized.")
    else:
        print("❌ The app appears to use STATIC weather data")
        print("   Changing hunt date may not affect weather conditions.")
        print("   Consider this a limitation for future hunting planning.")
    
    print(f"\n💡 Recommendations:")
    print("- Use the app for current day hunting decisions")
    print("- For future dates, check actual weather forecasts separately")
    print("- The terrain and deer movement predictions are still valuable")

if __name__ == "__main__":
    test_weather_date_functionality()