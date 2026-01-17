#!/usr/bin/env python3
"""
Hunting Strategy Advisor
Generates specific wind and timing strategies for identified hotspots.
"""

import json
import sys
import os
import math
from pathlib import Path

# Add project root and backend to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

try:
    from backend.services.lidar_processor import DEMFileManager, TerrainExtractor
    LIDAR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  LIDAR not available: {e}")
    LIDAR_AVAILABLE = False

def get_cardinal_direction(degrees):
    """Convert degrees to cardinal direction."""
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = round(degrees / (360. / len(dirs)))
    return dirs[ix % len(dirs)]

def get_ideal_wind(aspect_deg, strategy):
    """Calculate ideal wind direction based on terrain aspect and strategy."""
    # Aspect is the direction the slope faces (downhill)
    
    # Strategy: Leeward Ridge / Rut Cruising
    # Bucks cruise on the downwind side of the ridge (Leeward).
    # If slope faces East (90), Leeward side is East.
    # Wind should be blowing FROM the West (270) over the top.
    # So ideal wind is FROM (Aspect + 180).
    
    # Strategy: Bedding
    # Bucks bed looking downhill (Aspect), smelling uphill (Aspect + 180).
    # Hunter should be cross-wind or above (if thermals rise).
    # Ideally, wind blowing parallel to the slope or quartering.
    
    ideal_wind_from = (aspect_deg + 180) % 360
    
    return {
        'direction_deg': ideal_wind_from,
        'cardinal': get_cardinal_direction(ideal_wind_from),
        'logic': "Wind blowing over the ridge (Leeward setup)"
    }

def analyze_hotspots():
    report_path = Path(project_root) / "hotspot_report.json"
    if not report_path.exists():
        print("❌ No hotspot report found. Run analysis first.")
        return

    with open(report_path, 'r') as f:
        report = json.load(f)

    print("\n" + "="*70)
    print("🏹 HUNTING STRATEGY ADVISOR")
    print("="*70)
    
    if LIDAR_AVAILABLE:
        dem_manager = DEMFileManager()
        terrain_extractor = TerrainExtractor()
        lidar_files = dem_manager.lidar_files
    else:
        print("⚠️  LIDAR not available for detailed terrain analysis")
        return

    for hotspot in report['top_5_hotspots']:
        rank = hotspot['rank']
        lat = hotspot['latitude']
        lon = hotspot['longitude']
        strategies = hotspot['strategies']
        
        print(f"\n📍 HOTSPOT #{rank}")
        print(f"   Location: {lat:.6f}, {lon:.6f}")
        print(f"   Primary Strategy: {strategies[0]}")
        
        # Get precise terrain data
        terrain = terrain_extractor.extract_point_terrain(lat, lon, lidar_files, sample_radius_m=30)
        
        if terrain:
            slope = terrain['slope']
            aspect = terrain['aspect']
            elev = terrain['elevation']
            
            aspect_cardinal = get_cardinal_direction(aspect)
            
            print(f"   Terrain: Slope {slope:.1f}°, Facing {aspect_cardinal} ({aspect:.0f}°), Elev {elev:.1f}m")
            
            # 1. WIND STRATEGY
            # Default: Leeward setup (Wind blowing over the feature)
            ideal_wind = get_ideal_wind(aspect, strategies[0])
            
            print(f"\n   💨 WIND STRATEGY:")
            print(f"      Ideal Wind: FROM {ideal_wind['cardinal']} ({ideal_wind['direction_deg']:.0f}°)")
            print(f"      Why: {ideal_wind['logic']}")
            print(f"      Setup: Sit on the {aspect_cardinal} side of the ridge/slope.")
            print(f"             Let the wind blow your scent into the open air/valley below.")
            print(f"             Bucks will cruise slightly uphill from you to scent-check.")

            # 2. TIMING STRATEGY
            print(f"\n   ⏰ TIMING STRATEGY:")
            if "Bedding" in strategies[0]:
                print(f"      Best Time: MORNING (AM) or ALL DAY")
                print(f"      Logic: Catch bucks returning to bed (uphill) in AM.")
                print(f"             Thermals rising in AM carry scent up and away.")
            elif "Travel" in strategies[0]:
                print(f"      Best Time: ALL DAY (Rut Phase)")
                print(f"      Logic: This is a cruising funnel. Bucks move through here at midday too.")
            else:
                print(f"      Best Time: MORNING/EVENING")
            
            # 3. THERMALS
            print(f"\n   🌡️ THERMALS:")
            print(f"      Morning: Thermals rise (Air moves Uphill). Scent goes UP.")
            print(f"      Evening: Thermals fall (Air moves Downhill). Scent goes DOWN.")
            if slope > 5:
                print(f"      Advice: In PM, sit higher so falling thermals don't wash the trail.")
        else:
            print("   ⚠️  Could not extract terrain details.")

    print("\n" + "="*70)

if __name__ == "__main__":
    analyze_hotspots()
