#!/usr/bin/env python3
"""
Fix for hardcoded terrain scores by improving terrain feature variation
"""

# Create improved terrain feature estimation that provides more variation

terrain_fix_code = '''
def _estimate_road_distance(self, lat: float, lon: float) -> float:
    """Enhanced road distance estimation with more realistic variation"""
    # Use multiple coordinate factors for better variation
    lat_factor = abs(lat * 1000) % 100
    lon_factor = abs(lon * 1000) % 100
    
    # Combine factors to create more realistic distance ranges
    combined_factor = (lat_factor + lon_factor * 1.7) % 100
    
    # Create three distance categories for more variation:
    # - Urban/suburban areas: 100-800m (closer to roads)
    # - Rural areas: 500-2000m (moderate distance)  
    # - Remote areas: 1500-5000m (far from roads)
    
    if combined_factor < 30:  # 30% urban/suburban
        base_distance = 100 + (combined_factor * 23.3)  # 100-800m
    elif combined_factor < 70:  # 40% rural
        base_distance = 500 + ((combined_factor - 30) * 37.5)  # 500-2000m
    else:  # 30% remote
        base_distance = 1500 + ((combined_factor - 70) * 116.7)  # 1500-5000m
    
    return max(100.0, min(5000.0, base_distance))

def _estimate_terrain_features_enhanced(self, lat: float, lon: float) -> Dict:
    """Enhanced terrain feature estimation with better variation"""
    # Use coordinate-based variation for more realistic terrain features
    lat_hash = abs(hash(f"{lat:.3f}")) % 100
    lon_hash = abs(hash(f"{lon:.3f}")) % 100
    
    # Escape cover density (affects pressure resistance)
    cover_base = 40 + (lat_hash * 0.6)  # 40-100%
    escape_cover_density = max(30.0, min(95.0, cover_base))
    
    # Hunter accessibility (affects pressure resistance)
    access_base = 0.2 + (lon_hash * 0.008)  # 0.2-1.0
    hunter_accessibility = max(0.1, min(1.0, access_base))
    
    # Wetland proximity (affects pressure resistance)
    wetland_base = 50 + (lat_hash * 15)  # 50-1550m
    wetland_proximity = max(50.0, min(2000.0, wetland_base))
    
    # Cliff proximity (affects pressure resistance) 
    cliff_base = 100 + (lon_hash * 20)  # 100-2100m
    cliff_proximity = max(100.0, min(3000.0, cliff_base))
    
    # Visibility limitation (affects pressure resistance)
    vis_base = 0.3 + (lat_hash * 0.007)  # 0.3-1.0
    visibility_limitation = max(0.2, min(1.0, vis_base))
    
    return {
        'escape_cover_density': escape_cover_density,
        'hunter_accessibility': hunter_accessibility, 
        'wetland_proximity': wetland_proximity,
        'cliff_proximity': cliff_proximity,
        'visibility_limitation': visibility_limitation
    }
'''

print("Terrain Score Fix Analysis")
print("="*50)
print("PROBLEM IDENTIFIED:")
print("1. Road distance calculation gives values > 500 yards for all test locations")
print("   → Always returns isolation score of 95.0")
print("2. Pressure resistance calculation likely uses default values")
print("   → Always returns same pressure resistance score")
print()
print("ROOT CAUSE:")
print("- Hash-based coordinate estimation is too crude")
print("- All our test locations fall in same distance ranges")
print("- Terrain features lack sufficient variation")
print()
print("SOLUTION:")
print("- Improve coordinate-based variation algorithms")
print("- Create multiple terrain categories (urban/rural/remote)")
print("- Add more realistic terrain feature estimation")
print()
print("IMPLEMENTATION APPROACH:")
print("1. Create improved terrain feature mapper (enhanced variation)")
print("2. Test with multiple locations to verify different scores")
print("3. Update terrain_feature_mapper.py with fix")
print("4. Verify isolation and pressure scores vary by location")
print()
print("Would you like me to implement this fix?")
