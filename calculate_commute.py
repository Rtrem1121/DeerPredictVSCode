
import math

def calculate_bearing(lat1, lon1, lat2, lon2):
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    d_lon = lon2 - lon1
    
    x = math.sin(d_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(d_lon))
    
    initial_bearing = math.atan2(x, y)
    
    # Convert to degrees
    initial_bearing = math.degrees(initial_bearing)
    
    # Normalize to 0-360
    bearing = (initial_bearing + 360) % 360
    return bearing

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

# The General's Quarters
bed_lat, bed_lon = 44.353632, -72.935610

# Top Hotspots
targets = [
    {"name": "Hotspot #2 (Primary Hub)", "lat": 44.359083, "lon": -72.940267, "desc": "Travel Corridor Interception"},
    {"name": "Hotspot #3 (Secondary Hub)", "lat": 44.356726, "lon": -72.942481, "desc": "Travel Corridor Interception"},
    {"name": "Hotspot #1 (Perimeter Escape)", "lat": 44.348409, "lon": -72.942073, "desc": "Perimeter Escape Route"}
]

print(f"ANALYSIS: Commute from General's Quarters ({bed_lat}, {bed_lon})")
print("-" * 60)

for t in targets:
    dist = calculate_distance(bed_lat, bed_lon, t['lat'], t['lon'])
    bearing = calculate_bearing(bed_lat, bed_lon, t['lat'], t['lon'])
    yards = dist * 1.09361
    
    direction = ""
    if 337.5 <= bearing or bearing < 22.5: direction = "N"
    elif 22.5 <= bearing < 67.5: direction = "NE"
    elif 67.5 <= bearing < 112.5: direction = "E"
    elif 112.5 <= bearing < 157.5: direction = "SE"
    elif 157.5 <= bearing < 202.5: direction = "S"
    elif 202.5 <= bearing < 247.5: direction = "SW"
    elif 247.5 <= bearing < 292.5: direction = "W"
    elif 292.5 <= bearing < 337.5: direction = "NW"
    
    print(f"DESTINATION: {t['name']}")
    print(f"   Distance: {yards:.0f} yards ({dist:.0f}m)")
    print(f"   Direction: {direction} ({bearing:.0f}°)")
    print(f"   Strategy: {t['desc']}")
    
    # Wind Analysis
    print(f"   Wind Check:")
    if 270 <= bearing <= 360: # Target is NW
        print("      ✅ PERFECT for NW Wind (He walks directly into the wind)")
    elif 225 <= bearing < 270: # Target is W/SW
        print("      ⚠️  Good for West Wind (Cross-wind)")
    else:
        print("      ℹ️  Requires specific wind")
    print("-" * 60)
