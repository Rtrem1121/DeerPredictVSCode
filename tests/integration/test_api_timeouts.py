#!/usr/bin/env python3
"""
Quick test script to check if API timeout settings are the issue
"""
import requests
import time

def test_weather_api():
    """Test weather API with different timeout settings"""
    print("Testing weather API timeouts...")
    
    # Test coordinates (Montpelier, VT)
    lat, lon = 44.2601, -72.5806
    weather_url = f"https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,precipitation,snowfall,snow_depth,pressure_msl,wind_speed_10m,wind_direction_10m",
        "hourly": "pressure_msl,wind_speed_10m,wind_direction_10m,temperature_2m",
        "daily": "wind_speed_10m_max,wind_direction_10m_dominant,temperature_2m_max,temperature_2m_min",
        "forecast_days": 3,
        "timezone": "America/New_York"
    }
    
    # Test with short timeout (current setting)
    try:
        start_time = time.time()
        response = requests.get(weather_url, params=params, timeout=5)
        end_time = time.time()
        print(f"✅ Weather API (5s timeout): Success in {end_time - start_time:.2f}s")
        print(f"   Status: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"❌ Weather API (5s timeout): TIMEOUT")
    except Exception as e:
        print(f"❌ Weather API (5s timeout): ERROR - {e}")
    
    # Test with longer timeout
    try:
        start_time = time.time()
        response = requests.get(weather_url, params=params, timeout=15)
        end_time = time.time()
        print(f"✅ Weather API (15s timeout): Success in {end_time - start_time:.2f}s")
        print(f"   Status: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"❌ Weather API (15s timeout): TIMEOUT")
    except Exception as e:
        print(f"❌ Weather API (15s timeout): ERROR - {e}")

def test_elevation_api():
    """Test elevation API with different timeout settings"""
    print("\nTesting elevation API timeouts...")
    
    # Test a small chunk of coordinates
    coords = [(44.2601, -72.5806), (44.2602, -72.5807), (44.2603, -72.5808)]
    lat_chunk = [c[0] for c in coords]
    lon_chunk = [c[1] for c in coords]
    
    url = "https://api.open-meteo.com/v1/elevation"
    payload = {
        "latitude": ",".join(map(str, lat_chunk)),
        "longitude": ",".join(map(str, lon_chunk))
    }
    
    # Test with short timeout (current setting)
    try:
        start_time = time.time()
        response = requests.post(url, data=payload, timeout=3)
        end_time = time.time()
        print(f"✅ Elevation API (3s timeout): Success in {end_time - start_time:.2f}s")
        print(f"   Status: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"❌ Elevation API (3s timeout): TIMEOUT")
    except Exception as e:
        print(f"❌ Elevation API (3s timeout): ERROR - {e}")
    
    # Test with longer timeout
    try:
        start_time = time.time()
        response = requests.post(url, data=payload, timeout=10)
        end_time = time.time()
        print(f"✅ Elevation API (10s timeout): Success in {end_time - start_time:.2f}s")
        print(f"   Status: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"❌ Elevation API (10s timeout): TIMEOUT")
    except Exception as e:
        print(f"❌ Elevation API (10s timeout): ERROR - {e}")

def test_overpass_api():
    """Test Overpass API with different timeout settings"""
    print("\nTesting Overpass API timeouts...")
    
    # Simple query for roads near Montpelier, VT
    bbox = (44.25, -72.59, 44.27, -72.57)
    query = f"""[out:json];(
        way["highway"]["highway"!="footway"]["highway"!="path"]["highway"!="track"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
    );out geom;"""
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Test with short timeout (current setting)
    try:
        start_time = time.time()
        response = requests.post(overpass_url, data=query, timeout=3)
        end_time = time.time()
        print(f"✅ Overpass API (3s timeout): Success in {end_time - start_time:.2f}s")
        print(f"   Status: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"❌ Overpass API (3s timeout): TIMEOUT")
    except Exception as e:
        print(f"❌ Overpass API (3s timeout): ERROR - {e}")
    
    # Test with longer timeout
    try:
        start_time = time.time()
        response = requests.post(overpass_url, data=query, timeout=15)
        end_time = time.time()
        print(f"✅ Overpass API (15s timeout): Success in {end_time - start_time:.2f}s")
        print(f"   Status: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"❌ Overpass API (15s timeout): TIMEOUT")
    except Exception as e:
        print(f"❌ Overpass API (15s timeout): ERROR - {e}")

if __name__ == "__main__":
    print("🧪 Testing API Timeout Theory")
    print("=" * 50)
    
    test_weather_api()
    test_elevation_api()
    test_overpass_api()
    
    print("\n" + "=" * 50)
    print("✅ Test complete!")
