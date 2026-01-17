"""
Saturday Hunt Analysis - 44.36766, -72.90286
Comprehensive pre-hunt briefing with weather, terrain, and tactical insights
"""

import requests
from datetime import datetime, timedelta
import math

# Hunt location
HUNT_LAT, HUNT_LON = 44.36766, -72.90286

# Previous analysis hotspots (Property 2 from our analysis)
HOTSPOTS = [
    {"id": 1, "lat": 44.36611, "lon": -72.90140, "score": 168.2},
    {"id": 2, "lat": 44.36595, "lon": -72.90170, "score": 165.5},
    {"id": 3, "lat": 44.36530, "lon": -72.90250, "score": 152.1},
]

# Previous stand location analyzed
PREVIOUS_STAND = {"lat": 44.36658, "lon": -72.9022, "score": 39}

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in yards between two coordinates"""
    R = 6371000  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    meters = R * c
    return meters * 1.09361  # Convert to yards

def bearing(lat1, lon1, lat2, lon2):
    """Calculate compass bearing from point 1 to point 2"""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(delta_lambda)
    theta = math.atan2(x, y)
    return (math.degrees(theta) + 360) % 360

def bearing_to_cardinal(deg):
    """Convert bearing to cardinal direction"""
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
            'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    idx = int((deg + 11.25) / 22.5) % 16
    return dirs[idx]

def wind_direction_name(deg):
    """Convert wind direction degrees to cardinal"""
    if deg is None:
        return 'N/A'
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
            'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    idx = int((deg + 11.25) / 22.5) % 16
    return dirs[idx]

def get_saturday_date():
    """Get the date of this coming Saturday"""
    today = datetime.now()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    return today + timedelta(days=days_until_saturday)

def fetch_weather(lat, lon, date_str):
    """Fetch weather forecast from Open-Meteo"""
    url = (f'https://api.open-meteo.com/v1/forecast?'
           f'latitude={lat}&longitude={lon}&'
           f'daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,'
           f'wind_speed_10m_max,wind_direction_10m_dominant,sunrise,sunset&'
           f'hourly=temperature_2m,wind_speed_10m,wind_direction_10m,precipitation_probability,relative_humidity_2m&'
           f'timezone=America/New_York&start_date={date_str}&end_date={date_str}')
    
    response = requests.get(url, timeout=30)
    return response.json()

def main():
    saturday = get_saturday_date()
    saturday_str = saturday.strftime('%Y-%m-%d')
    
    print("=" * 70)
    print(f"  SATURDAY HUNT BRIEFING - {saturday.strftime('%B %d, %Y')}")
    print("=" * 70)
    print(f"\n  Stand Location: ({HUNT_LAT}, {HUNT_LON})")
    
    # Position relative to hotspots
    print("\n" + "=" * 70)
    print("  POSITION RELATIVE TO ANALYZED HOTSPOTS")
    print("=" * 70)
    
    for hs in HOTSPOTS:
        dist = haversine(HUNT_LAT, HUNT_LON, hs['lat'], hs['lon'])
        direction = bearing_to_cardinal(bearing(HUNT_LAT, HUNT_LON, hs['lat'], hs['lon']))
        print(f"  Hotspot #{hs['id']} (Score: {hs['score']}): {dist:.0f} yds {direction}")
    
    # Compare to previous stand
    dist_to_prev = haversine(HUNT_LAT, HUNT_LON, PREVIOUS_STAND['lat'], PREVIOUS_STAND['lon'])
    dir_to_prev = bearing_to_cardinal(bearing(HUNT_LAT, HUNT_LON, PREVIOUS_STAND['lat'], PREVIOUS_STAND['lon']))
    print(f"\n  Previously Analyzed Stand: {dist_to_prev:.0f} yds {dir_to_prev}")
    
    # Weather forecast
    print("\n" + "=" * 70)
    print("  WEATHER FORECAST")
    print("=" * 70)
    
    try:
        data = fetch_weather(HUNT_LAT, HUNT_LON, saturday_str)
        daily = data.get('daily', {})
        hourly = data.get('hourly', {})
        
        high_c = daily.get('temperature_2m_max', [None])[0]
        low_c = daily.get('temperature_2m_min', [None])[0]
        high_f = round(high_c * 9/5 + 32, 1) if high_c else 'N/A'
        low_f = round(low_c * 9/5 + 32, 1) if low_c else 'N/A'
        
        wind_max_kmh = daily.get('wind_speed_10m_max', [None])[0]
        wind_max_mph = round(wind_max_kmh * 0.621, 1) if wind_max_kmh else 'N/A'
        
        wind_dir_deg = daily.get('wind_direction_10m_dominant', [None])[0]
        wind_dir_name = wind_direction_name(wind_dir_deg)
        
        precip = daily.get('precipitation_probability_max', [None])[0]
        sunrise = daily.get('sunrise', [None])[0]
        sunset = daily.get('sunset', [None])[0]
        
        # Parse sunrise/sunset times
        if sunrise:
            sunrise_time = sunrise.split('T')[1][:5]
        else:
            sunrise_time = 'N/A'
        if sunset:
            sunset_time = sunset.split('T')[1][:5]
        else:
            sunset_time = 'N/A'
        
        print(f"""
  Daily Summary:
  ─────────────────────────────────────────
  Temperature:    {low_f}°F - {high_f}°F
  Wind:           {wind_max_mph} mph max from {wind_dir_name} ({wind_dir_deg}°)
  Precip Chance:  {precip}%
  Sunrise:        {sunrise_time} AM
  Sunset:         {sunset_time} PM
""")
        
        # Hourly breakdown
        times = hourly.get('time', [])
        temps = hourly.get('temperature_2m', [])
        winds = hourly.get('wind_speed_10m', [])
        wind_dirs = hourly.get('wind_direction_10m', [])
        precips = hourly.get('precipitation_probability', [])
        humidities = hourly.get('relative_humidity_2m', [])
        
        print("  Hourly Breakdown (Prime Hunting Hours):")
        print("  ─────────────────────────────────────────────────────────────")
        print(f"  {'Hour':<10} {'Temp':<10} {'Wind':<14} {'Direction':<10} {'Humidity':<10}")
        print("  ─────────────────────────────────────────────────────────────")
        
        morning_winds = []
        evening_winds = []
        
        for i, t in enumerate(times):
            hour = int(t.split('T')[1].split(':')[0])
            if (5 <= hour <= 10) or (15 <= hour <= 19):
                temp_f = round(temps[i] * 9/5 + 32, 1) if temps[i] is not None else 'N/A'
                wind_mph = round(winds[i] * 0.621, 1) if winds[i] is not None else 0
                w_dir = wind_direction_name(wind_dirs[i])
                humidity = humidities[i] if humidities[i] is not None else 'N/A'
                
                if hour < 12:
                    hour_str = f"{hour}:00 AM"
                    morning_winds.append((wind_dirs[i], wind_mph))
                elif hour == 12:
                    hour_str = "12:00 PM"
                else:
                    hour_str = f"{hour-12}:00 PM"
                    evening_winds.append((wind_dirs[i], wind_mph))
                
                print(f"  {hour_str:<10} {temp_f}°F{'':<4} {wind_mph:<5} mph    {w_dir:<10} {humidity}%")
        
        # Wind analysis
        print("\n" + "=" * 70)
        print("  WIND ANALYSIS & SCENT CONTROL")
        print("=" * 70)
        
        avg_morning_dir = sum(w[0] for w in morning_winds if w[0]) / len([w for w in morning_winds if w[0]]) if morning_winds else wind_dir_deg
        avg_evening_dir = sum(w[0] for w in evening_winds if w[0]) / len([w for w in evening_winds if w[0]]) if evening_winds else wind_dir_deg
        
        print(f"""
  Dominant Wind:  {wind_dir_name} ({wind_dir_deg}°)
  
  Your scent will blow {bearing_to_cardinal((wind_dir_deg + 180) % 360)} from your stand.
  
  SCENT CONE ANALYSIS:
  ─────────────────────────────────────────""")
        
        # Calculate where scent blows relative to hotspots
        scent_direction = (wind_dir_deg + 180) % 360  # Where scent travels TO
        
        for hs in HOTSPOTS:
            hs_bearing = bearing(HUNT_LAT, HUNT_LON, hs['lat'], hs['lon'])
            angle_diff = abs(hs_bearing - scent_direction)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            
            dist = haversine(HUNT_LAT, HUNT_LON, hs['lat'], hs['lon'])
            
            if angle_diff < 30:
                status = "⚠️  IN SCENT CONE - Deer may smell you!"
            elif angle_diff < 60:
                status = "⚡ EDGE of scent cone - Risky"
            else:
                status = "✅ CLEAR of scent cone"
            
            print(f"  Hotspot #{hs['id']} ({dist:.0f} yds {bearing_to_cardinal(hs_bearing)}): {status}")
        
    except Exception as e:
        print(f"  Error fetching weather: {e}")
    
    # Tactical recommendations
    print("\n" + "=" * 70)
    print("  TACTICAL RECOMMENDATIONS")
    print("=" * 70)
    
    print(f"""
  STAND APPROACH:
  ─────────────────────────────────────────
  • With {wind_dir_name} wind, approach from the {bearing_to_cardinal((wind_dir_deg + 180) % 360)} if possible
  • Be in stand 30-45 min before sunrise ({sunrise_time})
  • Late November = Peak Rut activity likely
  
  TIMING STRATEGY:
  ─────────────────────────────────────────
  • PRIME TIME (AM):  {sunrise_time} - 9:30 AM (post-sunrise movement)
  • MIDDAY:           10:00 AM - 2:00 PM (rut bucks cruise all day)
  • PRIME TIME (PM):  3:00 PM - {sunset_time} (evening feeding movement)
  
  RUT BEHAVIOR NOTES (Late November):
  ─────────────────────────────────────────
  • Bucks still actively cruising for last estrous does
  • Secondary rut possible - watch for younger does
  • Cold temps + stable pressure = increased movement
  • Use grunt calls sparingly - bucks are educated by now
  • Doe bleats can be effective for drawing cruisers
  
  MOON PHASE CONSIDERATION:
  ─────────────────────────────────────────
  • Check moon phase - major/minor feeding times can influence movement
""")

    # Final assessment
    print("=" * 70)
    print("  OVERALL ASSESSMENT")
    print("=" * 70)
    
    # Score the conditions
    conditions_score = 0
    notes = []
    
    if wind_max_mph and wind_max_mph < 15:
        conditions_score += 25
        notes.append("✅ Light winds - good scent control")
    elif wind_max_mph and wind_max_mph < 25:
        conditions_score += 15
        notes.append("⚡ Moderate winds - some scent dispersion")
    else:
        notes.append("⚠️  High winds may reduce deer movement")
    
    if precip and precip < 30:
        conditions_score += 25
        notes.append("✅ Low precipitation chance")
    elif precip and precip < 60:
        conditions_score += 10
        notes.append("⚡ Moderate precip chance - deer may move earlier")
    else:
        notes.append("⚠️  High precip chance - may affect hunt")
    
    if low_f and 25 <= low_f <= 45:
        conditions_score += 25
        notes.append("✅ Ideal temperature range for deer movement")
    elif low_f and (15 <= low_f < 25 or 45 < low_f <= 55):
        conditions_score += 15
        notes.append("⚡ Acceptable temperatures")
    
    # Late November rut bonus
    conditions_score += 20
    notes.append("✅ Late November - Peak/Secondary rut activity")
    
    print(f"\n  Conditions Score: {conditions_score}/100\n")
    for note in notes:
        print(f"  {note}")
    
    print(f"""
  ─────────────────────────────────────────
  VERDICT: {"EXCELLENT" if conditions_score >= 80 else "GOOD" if conditions_score >= 60 else "FAIR" if conditions_score >= 40 else "POOR"} hunting conditions
  
  Good luck on Saturday! 🦌
""")
    print("=" * 70)

if __name__ == "__main__":
    main()
