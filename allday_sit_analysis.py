"""
All-Day Sit Analysis: 6 AM - 5 PM
Buck Movement Timeline for Saturday, November 29, 2025
Stand Location: 44.36766, -72.90286
Buck Bed: 44.36238, -72.90142 (654 yards SOUTH)
"""

import requests
from datetime import datetime, timedelta
import math

# Locations
STAND = {'lat': 44.36766, 'lon': -72.90286}
BUCK_BED = {'lat': 44.36238, 'lon': -72.90142}

def get_saturday_date():
    today = datetime.now()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    return today + timedelta(days=days_until_saturday)

def fetch_hourly_weather(lat, lon, date_str):
    url = (f'https://api.open-meteo.com/v1/forecast?'
           f'latitude={lat}&longitude={lon}&'
           f'hourly=temperature_2m,wind_speed_10m,wind_direction_10m,cloud_cover,precipitation_probability&'
           f'daily=sunrise,sunset&'
           f'timezone=America/New_York&start_date={date_str}&end_date={date_str}')
    response = requests.get(url, timeout=30)
    return response.json()

def wind_dir_name(deg):
    if deg is None: return 'N/A'
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
            'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    return dirs[int((deg + 11.25) / 22.5) % 16]

saturday = get_saturday_date()
saturday_str = saturday.strftime('%Y-%m-%d')

print("=" * 75)
print(f"  ALL-DAY SIT BUCK MOVEMENT TIMELINE")
print(f"  Saturday, {saturday.strftime('%B %d, %Y')} | 6:00 AM - 5:00 PM")
print("=" * 75)
print(f"""
  📍 Your Stand: (44.36766, -72.90286)
  🦌 Buck Bed:   (44.36238, -72.90142) - 654 yards SOUTH of you
  
  Buck Travel Direction: SOUTH → NORTH (toward you)
""")

# Fetch weather
try:
    data = fetch_hourly_weather(STAND['lat'], STAND['lon'], saturday_str)
    hourly = data.get('hourly', {})
    daily = data.get('daily', {})
    
    sunrise = daily.get('sunrise', [''])[0].split('T')[1][:5]  # "07:05"
    sunset = daily.get('sunset', [''])[0].split('T')[1][:5]    # "16:14"
    
    times = hourly.get('time', [])
    temps = hourly.get('temperature_2m', [])
    winds = hourly.get('wind_speed_10m', [])
    wind_dirs = hourly.get('wind_direction_10m', [])
    clouds = hourly.get('cloud_cover', [])
    precip = hourly.get('precipitation_probability', [])
    
except Exception as e:
    print(f"Weather fetch failed: {e}")
    sunrise, sunset = "07:05", "16:14"
    times, temps, winds, wind_dirs, clouds, precip = [], [], [], [], [], []

print("=" * 75)
print("  HOURLY BUCK MOVEMENT FORECAST")
print("=" * 75)

# Define movement phases with detailed insights
phases = [
    {
        'time': '5:30-6:00 AM',
        'hour': 5,
        'phase': '🌙 PRE-DAWN ENTRY',
        'movement': 'NONE (You entering)',
        'buck_location': 'IN BED',
        'activity': 1,
        'notes': [
            "Enter from EAST/NORTHEAST to keep wind (WNW) blowing away from bed",
            "Use darkness to cover noise - buck is still in bed",
            "Be in stand and settled by 6:00 AM",
            "NO flashlight near stand - use red light only"
        ]
    },
    {
        'time': '6:00-6:30 AM',
        'hour': 6,
        'phase': '🌑 DARK / PRE-DAWN',
        'movement': 'LOW',
        'buck_location': 'IN BED (Alert)',
        'activity': 2,
        'notes': [
            "Buck is awake but still bedded",
            "Listening for does moving to feed",
            "May stand/stretch in bed - not traveling yet",
            "Get your grunt call and rattles ready"
        ]
    },
    {
        'time': f'6:30-7:05 AM',
        'hour': 6.5,
        'phase': '🌅 FIRST LIGHT',
        'movement': 'BUILDING',
        'buck_location': 'LEAVING BED',
        'activity': 5,
        'notes': [
            f"Sunrise: {sunrise} - Buck starts moving",
            "He'll leave bed heading NORTH toward doe feeding areas",
            "Travel route brings him past your stand (654 yds)",
            "At 3-4 mph walking speed = ~6-8 min from bed to you",
            "⚠️ HIGH ALERT - He could appear 6:45-7:15 AM"
        ]
    },
    {
        'time': '7:05-8:30 AM',
        'hour': 7,
        'phase': '☀️ PRIME MORNING',
        'movement': 'PEAK',
        'buck_location': 'CRUISING NORTH',
        'activity': 9,
        'notes': [
            "🔥 HIGHEST probability window of the day",
            "Buck actively cruising, scent-checking doe trails",
            "If he left bed at first light, he's in YOUR zone now",
            "Stay motionless - he's looking for movement",
            "Grunt call: Single contact grunt every 15-20 min",
            "Watch downwind side - he may circle to verify"
        ]
    },
    {
        'time': '8:30-10:00 AM',
        'hour': 9,
        'phase': '🌤️ MID-MORNING',
        'movement': 'MODERATE-HIGH',
        'buck_location': 'CRUISING / CHECKING DOES',
        'activity': 7,
        'notes': [
            "Still excellent - late November rut keeps bucks moving",
            "He may be with a doe OR still searching",
            "If you haven't seen him, he may have gone east/west",
            "Blind rattling sequence can pull him back",
            "Does feeding nearby will hold his attention"
        ]
    },
    {
        'time': '10:00 AM-12:00 PM',
        'hour': 10,
        'phase': '🌞 LATE MORNING',
        'movement': 'MODERATE',
        'buck_location': 'CRUISING OR BEDDED WITH DOE',
        'activity': 5,
        'notes': [
            "Traditional slow time BUT late rut changes this",
            "Bucks often cruise through midday seeking last estrous does",
            "If hot doe nearby, buck stays with her",
            "If no doe, he may bed temporarily (1-2 hours)",
            "Stay alert - movement can happen any time"
        ]
    },
    {
        'time': '12:00-2:00 PM',
        'hour': 12,
        'phase': '☀️ MIDDAY',
        'movement': 'LOW-MODERATE',
        'buck_location': 'BEDDED OR SLOW CRUISING',
        'activity': 4,
        'notes': [
            "Traditional lull - good time to eat lunch quietly",
            "Late November: 30% chance of random cruiser",
            "Secondary rut does can trigger movement",
            "Stretch carefully if needed - stay in stand",
            "Glass thick cover for bedded deer"
        ]
    },
    {
        'time': '2:00-3:30 PM',
        'hour': 14,
        'phase': '🌤️ EARLY AFTERNOON',
        'movement': 'BUILDING',
        'buck_location': 'WAKING / STARTING TO MOVE',
        'activity': 5,
        'notes': [
            "Movement starts picking up",
            "Does begin drifting toward evening feed",
            "Buck follows or anticipates their route",
            "Temperature dropping = deer more comfortable moving",
            "Rattling/calling can be effective now"
        ]
    },
    {
        'time': '3:30-4:15 PM',
        'hour': 15.5,
        'phase': '🔥 PRIME EVENING',
        'movement': 'HIGH',
        'buck_location': 'INTERCEPTING DOE MOVEMENT',
        'activity': 8,
        'notes': [
            "🔥 SECOND BEST window of the day",
            "Does heading to feed, buck follows",
            f"Sunset at {sunset} - Last hour is golden",
            "Buck may travel same route as morning (SOUTH to NORTH)",
            "OR circle around checking doe groups",
            "Stay extra alert - this is money time"
        ]
    },
    {
        'time': f'4:15-5:00 PM',
        'hour': 16,
        'phase': '🌅 LAST LIGHT',
        'movement': 'PEAK',
        'buck_location': 'ACTIVELY CRUISING',
        'activity': 9,
        'notes': [
            "🔥🔥 PRIME TIME - Equal to morning peak",
            f"Shooting light ends ~{sunset} (4:14 PM)",
            "Last 30 min often produces mature bucks",
            "They feel safer moving as light fades",
            "If he's coming, this is when",
            "Stay until you cannot legally shoot"
        ]
    }
]

print()
for phase in phases:
    hour = phase['hour']
    
    # Get weather for this hour if available
    weather_str = ""
    if times and hour < 24:
        hour_idx = int(hour)
        if hour_idx < len(temps):
            temp_f = round(temps[hour_idx] * 9/5 + 32) if temps[hour_idx] else '?'
            wind_mph = round(winds[hour_idx] * 0.621) if winds[hour_idx] else '?'
            w_dir = wind_dir_name(wind_dirs[hour_idx]) if wind_dirs[hour_idx] else '?'
            weather_str = f" | {temp_f}°F, {wind_mph}mph {w_dir}"
    
    # Activity bar
    activity_bar = "█" * phase['activity'] + "░" * (10 - phase['activity'])
    
    print(f"─" * 75)
    print(f"  {phase['time']} {phase['phase']}{weather_str}")
    print(f"  Movement: [{activity_bar}] {phase['movement']}")
    print(f"  Buck Location: {phase['buck_location']}")
    print()
    for note in phase['notes']:
        print(f"    • {note}")
    print()

print("=" * 75)
print("  SUMMARY: YOUR BEST WINDOWS")
print("=" * 75)
print("""
  🥇 #1 WINDOW: 7:00-8:30 AM (Post-sunrise cruising)
     - Buck leaving bed, traveling NORTH past your stand
     - 654 yards at 3-4 mph = arrives 7-15 min after leaving bed
     
  🥈 #2 WINDOW: 4:00-4:14 PM (Last light)  
     - Does moving to feed, buck following
     - Reduced light = buck feels safer
     - Often when mature bucks finally show
     
  🥉 #3 WINDOW: 3:30-4:00 PM (Pre-sunset buildup)
     - Evening movement starting
     - Can call/rattle more aggressively
     
  ⚡ WILDCARD: 10:00 AM - 2:00 PM (Midday cruiser)
     - Late November rut = bucks cruise all day
     - Don't sleep on midday!
""")

print("=" * 75)
print("  CALLING STRATEGY TIMELINE")
print("=" * 75)
print("""
  6:00-7:00 AM:  🔇 SILENT - Let woods settle, don't alert him
  
  7:00-7:30 AM:  📢 Light contact grunts (1 every 15-20 min)
                   - Short, soft grunts
                   - He's close, don't overcall
  
  7:30-9:00 AM:  📢 Moderate calling
                   - Grunt sequence (3-4 grunts)
                   - Light rattling (30 seconds)
                   - Doe bleat if no response to grunts
  
  9:00-11:00 AM: 📢 Aggressive if no sightings
                   - Blind rattling (60-90 seconds)
                   - Tending grunts
                   - Snort-wheeze (last resort)
  
  11:00-2:00 PM: 🔇 Quiet period
                   - Very light calling only
                   - Save energy for PM
  
  2:00-4:00 PM:  📢 Rebuild intensity
                   - Same as morning sequence
                   - Doe bleats effective now
  
  4:00-5:00 PM:  📢 Go for broke
                   - Aggressive rattling OK
                   - He's running out of time too
""")

print("=" * 75)
print("  WIND TIMELINE")
print("=" * 75)

if times:
    print("\n  Your scent blows EAST (away from buck's travel route) ✅\n")
    print(f"  {'Hour':<12} {'Wind':<15} {'Scent Risk':<20}")
    print(f"  {'-'*12} {'-'*15} {'-'*20}")
    
    for i, t in enumerate(times):
        hour = int(t.split('T')[1].split(':')[0])
        if 6 <= hour <= 17:
            wind_mph = round(winds[i] * 0.621) if winds[i] else 0
            w_dir = wind_dir_name(wind_dirs[i])
            
            # Assess scent risk (buck coming from SOUTH, wind from WEST)
            # Safe winds: W, NW, WNW, SW (blow scent east, away from his path)
            if w_dir in ['W', 'WNW', 'NW', 'WSW', 'SW']:
                risk = "✅ LOW - You're good"
            elif w_dir in ['NNW', 'SSW']:
                risk = "⚡ MODERATE - Watch it"
            else:
                risk = "⚠️ HIGH - Scent problem"
            
            hour_str = f"{hour}:00 {'AM' if hour < 12 else 'PM'}"
            print(f"  {hour_str:<12} {wind_mph} mph {w_dir:<8} {risk}")

print()
print("=" * 75)
print("  GOOD LUCK! Stay patient, stay warm, stay alert. 🦌")
print("=" * 75)
