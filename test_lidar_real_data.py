"""Test if LIDAR is returning real terrain data"""
from backend.services.lidar_processor import get_lidar_processor

dm, te, bp = get_lidar_processor()
files = dm.get_files()

# Test 5 different locations
test_locs = [
    (44.5, -72.5, "Burlington"),
    (43.2, -72.9, "Manchester"),
    (44.0, -72.0, "Montpelier"),
    (43.5, -72.5, "Rutland"),
    (44.8, -72.2, "Newport"),
]

print("Testing LIDAR terrain extraction at 5 locations:")
print("="*70)

for lat, lon, name in test_locs:
    terrain = te.extract_point_terrain(lat, lon, files, sample_radius_m=30)
    
    if terrain and terrain.get('coverage'):
        print(f"\n{name} ({lat}, {lon}):")
        print(f"  Coverage: ✓")
        print(f"  Slope: {terrain.get('slope', 0):.1f}°")
        print(f"  Aspect: {terrain.get('aspect', 0):.0f}°")
        print(f"  Elevation: {terrain.get('elevation', 0):.1f}m")
    else:
        print(f"\n{name} ({lat}, {lon}): ❌ No LIDAR coverage")

print("\n" + "="*70)
print("Checking if slope/aspect values are VARYING across locations...")

slopes = []
aspects = []

for lat, lon, name in test_locs:
    terrain = te.extract_point_terrain(lat, lon, files, sample_radius_m=30)
    if terrain and terrain.get('coverage'):
        slopes.append(terrain.get('slope', 0))
        aspects.append(terrain.get('aspect', 0))

if len(slopes) >= 2:
    slope_range = max(slopes) - min(slopes)
    aspect_range = max(aspects) - min(aspects)
    
    print(f"\nSlope range: {min(slopes):.1f}° to {max(slopes):.1f}° (variation: {slope_range:.1f}°)")
    print(f"Aspect range: {min(aspects):.0f}° to {max(aspects):.0f}° (variation: {aspect_range:.0f}°)")
    
    if slope_range > 5 and aspect_range > 30:
        print("\n✅ LIDAR IS RETURNING VARYING TERRAIN DATA!")
    else:
        print("\n⚠️ WARNING: LIDAR values are too similar - possible bug!")
else:
    print("\n❌ Not enough coverage to test variation")
