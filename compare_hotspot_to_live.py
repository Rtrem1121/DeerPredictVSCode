"""
Compare static hotspot analysis to live weather-aware prediction
"""
import requests
import json
from datetime import datetime

# Hotspot #1 from our analysis
HOTSPOT_LAT = 43.317275
HOTSPOT_LON = -73.228662

print("=" * 70)
print("🦌 COMPARING HOTSPOT ANALYSIS vs LIVE WEATHER PREDICTION")
print("=" * 70)

print(f"\n📍 Testing Hotspot #1: ({HOTSPOT_LAT}, {HOTSPOT_LON})")
print(f"   Static Analysis: Thermal Bedding Transition - Score: 10/10")
print(f"   Based on: LIDAR terrain + Forest land cover only\n")

print("🌡️  Fetching current weather conditions...")

# Get current weather from Open-Meteo
weather_url = f"https://api.open-meteo.com/v1/forecast"
weather_params = {
    'latitude': HOTSPOT_LAT,
    'longitude': HOTSPOT_LON,
    'current': 'temperature_2m,wind_speed_10m,wind_direction_10m,surface_pressure',
    'temperature_unit': 'fahrenheit',
    'wind_speed_unit': 'mph'
}

try:
    weather_resp = requests.get(weather_url, params=weather_params, timeout=10)
    weather_data = weather_resp.json()
    
    current = weather_data['current']
    temp = current['temperature_2m']
    wind_speed = current['wind_speed_10m']
    wind_dir = current['wind_direction_10m']
    pressure = current['surface_pressure']
    
    # Convert wind direction to cardinal
    def deg_to_cardinal(deg):
        dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        ix = round(deg / (360. / len(dirs)))
        return dirs[ix % len(dirs)]
    
    wind_cardinal = deg_to_cardinal(wind_dir)
    
    print(f"✅ Current conditions retrieved:")
    print(f"   🌡️  Temperature: {temp}°F")
    print(f"   💨 Wind: {wind_speed} mph from {wind_cardinal} ({wind_dir}°)")
    print(f"   📊 Pressure: {pressure} hPa")
    
except Exception as e:
    print(f"❌ Error fetching weather: {e}")
    print("   Using default values for demo...")
    temp = 45
    wind_speed = 8
    wind_dir = 225
    wind_cardinal = "SW"
    pressure = 1013

print(f"\n🔄 Running FULL deer prediction with live weather...")
print(f"   (This includes wind, temp, pressure, time, date, etc.)")

# Call the prediction API with current conditions
api_url = "http://localhost:8000/predict"
api_payload = {
    'lat': HOTSPOT_LAT,
    'lon': HOTSPOT_LON,
    'date_time': datetime.now().isoformat()
}

try:
    api_resp = requests.post(api_url, json=api_payload, timeout=90)
    
    if api_resp.status_code == 200:
        prediction = api_resp.json()
        
        print(f"\n✅ Live prediction complete!\n")
        
        # Extract stand sites from optimized_points
        if 'data' in prediction and 'optimized_points' in prediction['data']:
            stands = prediction['data']['optimized_points'].get('stand_sites', [])
        else:
            stands = []
        
        if not stands:
            print("⚠️  No stand sites found in response")
        else:
            print(f"Found {len(stands)} stand sites in live prediction\n")
            
            print("📍 WEATHER-AWARE STAND PREDICTIONS:")
            print("-" * 70)
            
            distances = []
            for i, stand in enumerate(stands[:3], 1):
                print(f"\n   Stand #{i}:")
                print(f"   📍 Location: ({stand['lat']:.6f}, {stand['lon']:.6f})")
                print(f"   🎯 Strategy: {stand.get('strategy', 'N/A')}")
                print(f"   ⭐ Score: {stand.get('score', 'N/A')}/10")
                
                # Calculate distance from original hotspot
                import math
                lat_diff = stand['lat'] - HOTSPOT_LAT
                lon_diff = stand['lon'] - HOTSPOT_LON
                dist_deg = math.sqrt(lat_diff**2 + lon_diff**2)
                dist_meters = dist_deg * 111000  # rough conversion
                distances.append(dist_meters)
                
                print(f"   📏 Distance from original hotspot: {dist_meters:.0f}m")
            
            avg_distance = sum(distances) / len(distances) if distances else 0
            
            print("\n" + "=" * 70)
            print("🔍 KEY INSIGHTS:")
            print("=" * 70)
            print(f"""
The STATIC hotspot analysis said:
  → "This terrain/forest area is generally good for mature bucks"
  → Based on: slope, aspect, elevation, land cover
  → No weather consideration

The LIVE weather-aware prediction said:
  → "HERE's exactly where to hunt TODAY with {wind_cardinal} wind at {temp}°F"
  → Based on: terrain + land cover + wind + temp + pressure + time + date
  → Accounts for scent travel, thermal activity, seasonal patterns

DIFFERENCE:
  → Static analysis: "Hunt somewhere in this ~100m zone"
  → Live prediction: "Hunt at these 3 specific GPS coordinates accounting for today's conditions"
  → Stands shifted avg {avg_distance:.0f}m from hotspot based on current conditions!
""")
        
    else:
        print(f"❌ API error: {api_resp.status_code}")
        print(f"   Response: {api_resp.text}")
        
except Exception as e:
    print(f"❌ Error calling prediction API: {e}")
    print("   Is the backend running? (docker-compose up)")

