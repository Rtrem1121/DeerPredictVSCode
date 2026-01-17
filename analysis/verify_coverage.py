
import sys
import os
import numpy as np
from shapely.geometry import Point

# Add project root to path
sys.path.append(os.getcwd())

from analysis.property_hotspot_analyzer import PropertyHotspotAnalyzer, PROPERTY_CORNERS

def analyze_coverage():
    print("🔍 Verifying 900-Acre Coverage...")
    
    # Initialize
    analyzer = PropertyHotspotAnalyzer(PROPERTY_CORNERS)
    
    # Generate grid
    points = analyzer.generate_grid(num_points=3000)
    
    # Score with LIDAR
    scored_points = analyzer.score_grid_with_lidar()
    
    if not scored_points:
        print("❌ No scored points available.")
        return

    # Define Quadrants
    lats = [p['lat'] for p in scored_points]
    lons = [p['lon'] for p in scored_points]
    mid_lat = (min(lats) + max(lats)) / 2
    mid_lon = (min(lons) + max(lons)) / 2
    
    quadrants = {
        'NW': {'points': [], 'scores': []},
        'NE': {'points': [], 'scores': []},
        'SW': {'points': [], 'scores': []},
        'SE': {'points': [], 'scores': []}
    }
    
    for p in scored_points:
        if p['lat'] >= mid_lat and p['lon'] <= mid_lon:
            q = 'NW'
        elif p['lat'] >= mid_lat and p['lon'] > mid_lon:
            q = 'NE'
        elif p['lat'] < mid_lat and p['lon'] <= mid_lon:
            q = 'SW'
        else:
            q = 'SE'
            
        quadrants[q]['points'].append(p)
        quadrants[q]['scores'].append(p['score'])

    print("\n📊 SECTOR ANALYSIS (Why are the spots clustered?)")
    print(f"   Property Center: {mid_lat:.5f}, {mid_lon:.5f}")
    print("-" * 60)
    
    for q, data in quadrants.items():
        count = len(data['points'])
        if count > 0:
            max_score = max(data['scores'])
            avg_score = np.mean(data['scores'])
            top_reason = "N/A"
            
            # Find the best point in this quadrant to see why it scored what it did
            best_point = max(data['points'], key=lambda x: x['score'])
            
            print(f"   {q} Sector ({count} points analyzed):")
            print(f"      Max Score: {max_score:.1f}/100")
            print(f"      Avg Score: {avg_score:.1f}/100")
            print(f"      Best Location: {best_point['lat']:.5f}, {best_point['lon']:.5f}")
            print(f"      Terrain: Slope {best_point['slope']:.1f}°, Elev {best_point['elevation']:.1f}m")
            print(f"      Breakdown: Bed:{best_point['bedding_score']} Travel:{best_point['travel_score']} Rut:{best_point['rut_score']}")
            
            if max_score < 60:
                print("      ⚠️  Why low? Likely poor wind advantage or flat terrain.")
            elif max_score > 80:
                print("      ✅  High Potential Area")
            print("")
        else:
            print(f"   {q} Sector: No points (Check boundary)")

if __name__ == "__main__":
    analyze_coverage()
