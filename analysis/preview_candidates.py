
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from analysis.property_hotspot_analyzer import PropertyHotspotAnalyzer, PROPERTY_CORNERS

def preview():
    print("🔍 Previewing Top Candidates with New LIDAR Data...")
    analyzer = PropertyHotspotAnalyzer(PROPERTY_CORNERS)
    
    # Generate grid
    analyzer.generate_grid(num_points=3000)
    
    # Score with LIDAR
    scored_points = analyzer.score_grid_with_lidar()
    
    if not scored_points:
        print("❌ No points scored.")
        return

    # Filter top 50
    top_50 = scored_points[:50]
    
    print(f"\n🌲 Analyzing Land Cover for Top 10 Candidates...")
    
    # Check land cover for top 10 just to give a quick preview
    candidates = []
    for i, site in enumerate(top_50[:10], 1):
        lc = analyzer.get_land_cover(site['lat'], site['lon'])
        if lc['is_forest']:
            # Apply thermal bonus if applicable
            if lc['class_id'] in [42, 43]:
                site['score'] += 10
            
            candidates.append(site)
            print(f"#{len(candidates)}: ({site['lat']:.5f}, {site['lon']:.5f}) - Score: {site['score']:.1f}")
            print(f"    Elev: {site['elevation']:.1f}m, Slope: {site['slope']:.1f}°, Aspect: {site['aspect']:.0f}°")
            print(f"    Cover: {lc['class_name']}")
            
        if len(candidates) >= 4:
            break
            
    print("\nThese are the first 4 locations that would be sent to the API.")

if __name__ == "__main__":
    preview()
