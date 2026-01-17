
from analysis.property_hotspot_analyzer import PropertyHotspotAnalyzer, PROPERTY_CORNERS

def check_elevation():
    analyzer = PropertyHotspotAnalyzer(PROPERTY_CORNERS)
    # Hotspot #2
    lat, lon = 44.359083, -72.940267
    analyzer.grid_points = [(lat, lon)]
    scored = analyzer.score_grid_with_lidar()
    
    if scored:
        p = scored[0]
        print(f"Hotspot #2 Elevation: {p['elevation']:.1f}m")
        print(f"Hotspot #2 Slope: {p['slope']:.1f}")
        print(f"Hotspot #2 Aspect: {p['aspect']:.1f}")

if __name__ == "__main__":
    check_elevation()
