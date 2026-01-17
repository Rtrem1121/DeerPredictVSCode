
from analysis.property_hotspot_analyzer import PropertyHotspotAnalyzer, PROPERTY_CORNERS

def analyze_edge_candidate():
    print("Verifying 'Edge' vs 'Bench' Setup...")
    analyzer = PropertyHotspotAnalyzer(PROPERTY_CORNERS)
    
    points = {
        "User's Point (Bench?)": (43.3185, -73.2135),
        "Proposed Edge (West)": (43.3185, -73.2139),
        "Proposed Edge (East)": (43.3185, -73.2131)
    }
    
    analyzer.grid_points = list(points.values())
    scored = analyzer.score_grid_with_lidar()
    
    print("\n" + "="*60)
    print(f"{'LOCATION':<25} | {'ELEV (m)':<10} | {'SLOPE':<8} | {'ASPECT':<8}")
    print("-" * 60)
    
    results = {}
    for p in scored:
        for name, (lat, lon) in points.items():
            if abs(p['lat'] - lat) < 0.00001 and abs(p['lon'] - lon) < 0.00001:
                results[name] = p
                break
                
    for name in points.keys():
        if name in results:
            p = results[name]
            print(f"{name:<25} | {p['elevation']:<10.1f} | {p['slope']:<8.1f} | {p['aspect']:<8.0f}")
    print("="*60)

if __name__ == "__main__":
    analyze_edge_candidate()
