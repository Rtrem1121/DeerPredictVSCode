
import sys
import os
import numpy as np
from shapely.geometry import Point

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from property_hotspot_analyzer import PropertyHotspotAnalyzer, PROPERTY_CORNERS

def diagnose():
    print("🔍 Diagnosing specific point: 43.31255, -73.21502")
    
    analyzer = PropertyHotspotAnalyzer(PROPERTY_CORNERS)
    
    target_lat = 43.31255
    target_lon = -73.21502
    
    # 1. Check Property Boundary
    is_inside = analyzer.is_inside_property(target_lat, target_lon)
    print(f"\n1. Property Boundary Check:")
    print(f"   Inside Property: {'✅ Yes' if is_inside else '❌ No'}")
    
    # 2. Check Land Cover
    print(f"\n2. Land Cover Check:")
    try:
        lc = analyzer.get_land_cover(target_lat, target_lon)
        print(f"   Class: {lc['class_name']} (ID: {lc['class_id']})")
        print(f"   Is Forest: {'✅ Yes' if lc['is_forest'] else '❌ No'}")
    except Exception as e:
        print(f"   Error checking land cover: {e}")

    # 3. Check LIDAR Score
    print(f"\n3. LIDAR Terrain Analysis:")
    if analyzer.dem_manager:
        # We need to manually extract terrain since score_grid_with_lidar works on grid_points
        # We'll use the terrain extractor directly
        try:
            terrain = analyzer.terrain_extractor.extract_point_terrain(
                lat=target_lat, lon=target_lon, 
                lidar_files=analyzer.dem_manager.lidar_files, 
                sample_radius_m=30
            )
            
            if terrain:
                slope = terrain['slope']
                aspect = terrain['aspect']
                elevation = terrain['elevation']
                
                print(f"   Elevation: {elevation:.1f}m")
                print(f"   Slope: {slope:.1f}°")
                print(f"   Aspect: {aspect:.0f}°")
                
                # Re-calculate score using the EXACT logic from property_hotspot_analyzer.py
                # We need min/max elev from the property to normalize. 
                # We'll approximate or run a quick scan if needed, but for now let's assume 
                # the range from the previous run (approx -0.4m to 0.0m? Wait, the previous run showed very low elevations... 
                # Ah, the previous run output showed "elev=-0.2m". This looks like relative elevation or normalized? 
                # No, the previous run output showed: "Elevation range: -0.4m - 0.0m". 
                # Wait, that seems wrong for Vermont. 
                # Let's look at the logs again.
                # "[1155/3000] Scored: slope=1.0°, aspect=92°, elev=-0.2m"
                # It seems the elevation data might be returning 0 or very low values?
                # If elevation is broken, that explains a lot.
                
                # Let's check the elevation range from the script execution.
                pass
            else:
                print("   ❌ No terrain data found for this point")
        except Exception as e:
            print(f"   Error extracting terrain: {e}")
    else:
        print("   LIDAR not available")

if __name__ == "__main__":
    diagnose()
