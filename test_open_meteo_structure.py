#!/usr/bin/env python3
"""
Test Open-Meteo API Response Structure

This script tests the Open-Meteo API to understand
the forecast data structure that's already available.
"""

import requests
import json
from datetime import datetime, timedelta

def test_open_meteo_api():
    """Test Open-Meteo API to see available forecast data"""
    
    print("🌤️ Testing Open-Meteo API Response Structure")
    print("=" * 50)
    
    # Vermont coordinates
    lat = 44.26639
    lon = -72.58133
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,precipitation,snowfall,snow_depth,pressure_msl,wind_speed_10m,wind_direction_10m",
        "hourly": "pressure_msl,wind_speed_10m,wind_direction_10m,temperature_2m",
        "daily": "wind_speed_10m_max,wind_direction_10m_dominant,temperature_2m_max,temperature_2m_min",
        "forecast_days": 3,
        "timezone": "America/New_York"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        print("✅ API Response Received")
        
        # Analyze structure
        print(f"\n📋 Top-level keys: {list(data.keys())}")
        
        # Current data
        current = data.get("current", {})
        print(f"\n🌡️ Current Weather Keys: {list(current.keys())}")
        
        if current:
            print("Current Conditions:")
            print(f"  Temperature: {current.get('temperature_2m', 'N/A')}°C")
            print(f"  Wind: {current.get('wind_direction_10m', 'N/A')}° at {current.get('wind_speed_10m', 'N/A')} km/h")
            print(f"  Pressure: {current.get('pressure_msl', 'N/A')} hPa")
        
        # Hourly data structure
        hourly = data.get("hourly", {})
        if hourly:
            print(f"\n⏰ Hourly Data Keys: {list(hourly.keys())}")
            times = hourly.get("time", [])
            temps = hourly.get("temperature_2m", [])
            wind_speeds = hourly.get("wind_speed_10m", [])
            wind_dirs = hourly.get("wind_direction_10m", [])
            
            print(f"  Hours available: {len(times)}")
            if len(times) >= 48:
                print("  ✅ 48+ hours of forecast data available!")
                
                # Show today vs tomorrow samples
                print(f"\n📅 Sample Forecast Data:")
                now = datetime.now()
                
                for i, time_str in enumerate(times[:6]):  # First 6 hours
                    dt = datetime.fromisoformat(time_str)
                    temp = temps[i] if i < len(temps) else "N/A"
                    ws = wind_speeds[i] if i < len(wind_speeds) else "N/A"
                    wd = wind_dirs[i] if i < len(wind_dirs) else "N/A"
                    
                    print(f"    {dt.strftime('%Y-%m-%d %H:%M')}: {temp}°C, Wind {wd}°@{ws}km/h")
                
                # Check tomorrow's data specifically
                print(f"\n🌅 Tomorrow's Data Available:")
                tomorrow = now + timedelta(days=1)
                tomorrow_start = tomorrow.replace(hour=6, minute=0, second=0, microsecond=0)
                
                tomorrow_data_points = []
                for i, time_str in enumerate(times):
                    dt = datetime.fromisoformat(time_str)
                    if dt.date() == tomorrow.date():
                        temp = temps[i] if i < len(temps) else "N/A"
                        ws = wind_speeds[i] if i < len(wind_speeds) else "N/A" 
                        wd = wind_dirs[i] if i < len(wind_dirs) else "N/A"
                        tomorrow_data_points.append({
                            'time': dt,
                            'temp': temp,
                            'wind_speed': ws,
                            'wind_direction': wd
                        })
                
                if tomorrow_data_points:
                    print(f"  ✅ Found {len(tomorrow_data_points)} data points for tomorrow")
                    # Show sample morning and evening data
                    morning_data = [dp for dp in tomorrow_data_points if 6 <= dp['time'].hour <= 10]
                    evening_data = [dp for dp in tomorrow_data_points if 16 <= dp['time'].hour <= 20]
                    
                    if morning_data:
                        avg_morning_temp = sum(dp['temp'] for dp in morning_data if dp['temp'] != "N/A") / len(morning_data)
                        avg_morning_wind = sum(dp['wind_speed'] for dp in morning_data if dp['wind_speed'] != "N/A") / len(morning_data)
                        print(f"    Morning (6-10 AM): Avg {avg_morning_temp:.1f}°C, Wind {avg_morning_wind:.1f} km/h")
                    
                    if evening_data:
                        avg_evening_temp = sum(dp['temp'] for dp in evening_data if dp['temp'] != "N/A") / len(evening_data)
                        avg_evening_wind = sum(dp['wind_speed'] for dp in evening_data if dp['wind_speed'] != "N/A") / len(evening_data)
                        print(f"    Evening (4-8 PM): Avg {avg_evening_temp:.1f}°C, Wind {avg_evening_wind:.1f} km/h")
                else:
                    print("  ❌ No tomorrow data found")
            else:
                print("  ❌ Insufficient forecast data")
        
        # Daily data structure  
        daily = data.get("daily", {})
        if daily:
            print(f"\n📅 Daily Data Keys: {list(daily.keys())}")
            daily_times = daily.get("time", [])
            daily_temp_max = daily.get("temperature_2m_max", [])
            daily_temp_min = daily.get("temperature_2m_min", [])
            daily_wind_max = daily.get("wind_speed_10m_max", [])
            
            print(f"  Days available: {len(daily_times)}")
            
            for i, day_str in enumerate(daily_times[:3]):
                dt = datetime.fromisoformat(day_str)
                temp_max = daily_temp_max[i] if i < len(daily_temp_max) else "N/A"
                temp_min = daily_temp_min[i] if i < len(daily_temp_min) else "N/A"
                wind_max = daily_wind_max[i] if i < len(daily_wind_max) else "N/A"
                
                day_label = "Today" if i == 0 else f"Day +{i}"
                print(f"    {day_label} ({dt.strftime('%Y-%m-%d')}): {temp_min}-{temp_max}°C, Max Wind {wind_max} km/h")
        
        print(f"\n🎯 Implementation Assessment:")
        print("=" * 30)
        
        current_available = bool(current and current.get('temperature_2m') is not None)
        hourly_available = bool(hourly and len(hourly.get('time', [])) >= 48)
        daily_available = bool(daily and len(daily.get('time', [])) >= 3)
        
        print(f"✅ Current weather: {'Available' if current_available else 'Not available'}")
        print(f"✅ Hourly forecasts: {'Available ({} hours)'.format(len(hourly.get('time', []))) if hourly_available else 'Not available'}")
        print(f"✅ Daily forecasts: {'Available ({} days)'.format(len(daily.get('time', []))) if daily_available else 'Not available'}")
        
        if current_available and hourly_available:
            print(f"\n🟢 VERDICT: Future weather forecasting is TECHNICALLY FEASIBLE")
            print("   The Open-Meteo API provides all necessary forecast data")
            print("   Implementation requires date-aware weather extraction")
        else:
            print(f"\n🔴 VERDICT: Insufficient data for future forecasting")
        
        # Save sample for analysis
        with open("open_meteo_sample_response.json", "w") as f:
            json.dump(data, f, indent=2)
        print(f"\n💾 Sample response saved to open_meteo_sample_response.json")
        
        return data
        
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        return None

if __name__ == "__main__":
    test_open_meteo_api()