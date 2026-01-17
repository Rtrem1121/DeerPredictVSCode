
import sys
import os
from analysis.property_hotspot_analyzer import PropertyHotspotAnalyzer, PROPERTY_CORNERS

def check_point():
    print("Checking specific point: 44.357691, -72.940077")
    
    # Initialize analyzer
    analyzer = PropertyHotspotAnalyzer(PROPERTY_CORNERS)
    
    # Manually set the grid to just this one point
    analyzer.grid_points = [(44.357691, -72.940077)]
    
    # Run LIDAR scoring
    scored_points = analyzer.score_grid_with_lidar()
    
    if not scored_points:
        print("Failed to score point.")
        return

    p = scored_points[0]
    print("\n" + "="*50)
    print(f"POINT ANALYSIS: {p['lat']}, {p['lon']}")
    print("="*50)
    print(f"Total Score: {p['score']:.1f}/100")
    print(f"Elevation: {p['elevation']:.1f}m")
    print(f"Slope: {p['slope']:.1f} degrees")
    print(f"Aspect: {p['aspect']:.1f} degrees")
    print("-" * 30)
    print(f"Bedding Score: {p['bedding_score']:.1f}")
    print(f"Travel Score:  {p['travel_score']:.1f}")
    print(f"Feeding Score: {p['feeding_score']:.1f}")
    print(f"Rut Score:     {p['rut_score']:.1f}")
    print("="*50)

    # Check land cover
    print("\nChecking Land Cover...")
    lc = analyzer.get_land_cover(p['lat'], p['lon'])
    print(f"Class: {lc['class_name']}")
    print(f"Is Forest: {lc['is_forest']}")

if __name__ == "__main__":
    check_point()
