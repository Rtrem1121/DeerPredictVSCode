
from analysis.property_hotspot_analyzer import PropertyHotspotAnalyzer, PROPERTY_CORNERS
import math

def analyze_specific_stand():
    print("Analyzing Specific Stand Location...")
    analyzer = PropertyHotspotAnalyzer(PROPERTY_CORNERS)
    
    # Points of Interest
    points = {
        "The General's Bed": (44.362383, -72.901422),
        "User's Stand": (44.36658, -72.9022),
        "Hotspot #1 (Primary)": (44.367658, -72.902860),
        "Hotspot #2 (Corridor)": (44.368099, -72.900124)
    }
    
    # 1. Run LIDAR Analysis on the User's Stand
    analyzer.grid_points = [points["User's Stand"]]
    scored = analyzer.score_grid_with_lidar()
    
    if not scored:
        print("❌ LIDAR analysis failed for this point.")
        return

    stand_data = scored[0]
    
    print("\n" + "="*60)
    print(f"📍 STAND ANALYSIS: ({stand_data['lat']:.5f}, {stand_data['lon']:.5f})")
    print("-" * 60)
    print(f"   Elevation: {stand_data['elevation']:.1f}m")
    print(f"   Slope:     {stand_data['slope']:.1f}°")
    print(f"   Aspect:    {stand_data['aspect']:.0f}°")
    print(f"   Score:     {stand_data['score']:.1f}/100")
    print(f"   Breakdown: Bedding:{stand_data['bedding_score']} Travel:{stand_data['travel_score']} Rut:{stand_data['rut_score']}")
    
    # 2. Commute Analysis (Bed -> Stand)
    bed_lat, bed_lon = points["The General's Bed"]
    stand_lat, stand_lon = points["User's Stand"]
    
    dist = analyzer.calculate_distance(bed_lat, bed_lon, stand_lat, stand_lon)
    bearing = analyzer.calculate_bearing(bed_lat, bed_lon, stand_lat, stand_lon)
    yards = dist * 1.09361
    
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    ix = round(bearing / 45) % 8
    cardinal = dirs[ix]
    
    print("\n🦌 COMMUTE DETAILS (Bed -> Stand)")
    print(f"   Distance: {yards:.0f} yards")
    print(f"   Direction: {cardinal} (Bearing {bearing:.0f}°)")
    
    # 3. Proximity to Hotspots
    print("\n🎯 PROXIMITY TO HOTSPOTS")
    h1_dist = analyzer.calculate_distance(stand_lat, stand_lon, points["Hotspot #1 (Primary)"][0], points["Hotspot #1 (Primary)"][1]) * 1.09361
    h2_dist = analyzer.calculate_distance(stand_lat, stand_lon, points["Hotspot #2 (Corridor)"][0], points["Hotspot #2 (Corridor)"][1]) * 1.09361
    
    print(f"   To Hotspot #1: {h1_dist:.0f} yards")
    print(f"   To Hotspot #2: {h2_dist:.0f} yards")
    
    # 4. Wind Strategy
    # Buck moves from Bed -> Stand (Bearing X)
    # He wants wind in his face (Bearing X +/- 45)
    # Hunter needs crosswind (Bearing X +/- 90)
    
    buck_wind = cardinal
    
    w1 = (bearing + 90) % 360
    w2 = (bearing - 90) % 360
    
    def get_cardinal(deg):
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        ix = round(deg / 45) % 8
        return dirs[ix]
    
    hunter_wind_1 = get_cardinal(w1)
    hunter_wind_2 = get_cardinal(w2)
    
    print("\n💨 WIND STRATEGY")
    print(f"   Buck's Safe Wind: {buck_wind} (He walks into it)")
    print(f"   🏹 HUNTER'S WIND: {hunter_wind_1} or {hunter_wind_2} (Crosswind)")
    
    print("="*60)

if __name__ == "__main__":
    analyze_specific_stand()
