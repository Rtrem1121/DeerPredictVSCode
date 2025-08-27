#!/usr/bin/env python3
"""
Test the enhanced terrain score calculations
"""

def test_enhanced_road_distance():
    """Test the enhanced road distance calculation"""
    
    def estimate_road_distance(lat: float, lon: float) -> float:
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

    def calculate_road_impact_score(road_distance_yards: float) -> float:
        """Calculate road impact score (higher distance = better score)"""
        road_impact_range = 500.0  # Default value
        distance = road_distance_yards
        
        if distance >= road_impact_range:
            return 95.0
        elif distance >= road_impact_range * 0.7:  # >= 350
            return 70.0 + (distance / road_impact_range * 25.0)
        elif distance >= road_impact_range * 0.3:  # >= 150  
            return 40.0 + (distance / (road_impact_range * 0.7) * 30.0)
        else:
            return 10.0 + (distance / (road_impact_range * 0.3) * 30.0)

    test_locations = [
        {"name": "Mountain", "lat": 44.0708, "lon": -72.8429},
        {"name": "Valley", "lat": 44.0500, "lon": -72.8000},
        {"name": "Ridge", "lat": 44.1000, "lon": -72.9000},
        {"name": "Forest", "lat": 44.2000, "lon": -72.7000},
        {"name": "Lake", "lat": 44.1500, "lon": -72.8500}
    ]
    
    print("Enhanced Road Distance and Isolation Score Test:")
    print("="*60)
    
    for location in test_locations:
        lat, lon = location["lat"], location["lon"]
        
        # Calculate road distance in meters
        road_dist_m = estimate_road_distance(lat, lon)
        # Convert to yards (1 meter = 1.094 yards)
        road_dist_yards = road_dist_m * 1.094
        
        # Calculate road impact score
        road_score = calculate_road_impact_score(road_dist_yards)
        
        print(f"\n{location['name']} ({lat}, {lon}):")
        print(f"  Road distance: {road_dist_m:.0f}m ({road_dist_yards:.0f} yards)")
        print(f"  Isolation score: {road_score:.1f}")
        
        # Check category
        lat_factor = abs(lat * 1000) % 100
        lon_factor = abs(lon * 1000) % 100
        combined_factor = (lat_factor + lon_factor * 1.7) % 100
        
        if combined_factor < 30:
            category = "Urban/Suburban"
        elif combined_factor < 70:
            category = "Rural"
        else:
            category = "Remote"
            
        print(f"  Category: {category}")

def test_enhanced_pressure_resistance():
    """Test the enhanced pressure resistance calculations"""
    
    def calculate_enhanced_terrain_features(lat: float, lon: float):
        """Calculate enhanced terrain features using coordinate variation"""
        lat_factor = abs(lat * 1000) % 100
        lon_factor = abs(lon * 1000) % 100
        
        # Escape cover density (affects pressure resistance)
        cover_base = 30.0 + ((lat_factor + lon_factor * 1.3) % 100) * 0.6  # 30-90%
        escape_cover_density = max(30.0, min(90.0, cover_base))
        
        # Hunter accessibility (affects pressure resistance)
        access_base = 0.2 + ((lat_factor * 1.4 + lon_factor) % 100) * 0.006  # 0.2-0.8
        hunter_accessibility = max(0.2, min(0.8, access_base))
        
        # Wetland proximity (affects pressure resistance)
        wetland_base = 100.0 + ((lat_factor * 1.1 + lon_factor * 1.6) % 100) * 14.0  # 100-1500m
        wetland_proximity = max(100.0, min(1500.0, wetland_base))
        
        # Cliff proximity (affects pressure resistance) 
        cliff_base = 200.0 + ((lat_factor * 1.8 + lon_factor * 0.9) % 100) * 23.0  # 200-2500m
        cliff_proximity = max(200.0, min(2500.0, cliff_base))
        
        # Visibility limitation (affects pressure resistance)
        vis_base = 0.3 + ((lat_factor * 0.7 + lon_factor * 1.2) % 100) * 0.006  # 0.3-0.9
        visibility_limitation = max(0.3, min(0.9, vis_base))
        
        return {
            'escape_cover_density': escape_cover_density,
            'hunter_accessibility': hunter_accessibility, 
            'wetland_proximity': wetland_proximity,
            'cliff_proximity': cliff_proximity,
            'visibility_limitation': visibility_limitation
        }

    def calculate_pressure_resistance(terrain_features):
        """Calculate pressure resistance score"""
        score = 0.0
        
        # Thick escape cover
        escape_cover = terrain_features['escape_cover_density']
        if escape_cover >= 80.0:
            score += 30.0
        elif escape_cover >= 60.0:
            score += 20.0
        
        # Hunter accessibility
        accessibility = terrain_features['hunter_accessibility']
        if accessibility <= 0.3:
            score += 25.0
        elif accessibility <= 0.5:
            score += 15.0
        
        # Wetland proximity
        wetland_dist = terrain_features['wetland_proximity']
        if wetland_dist <= 100:
            score += 20.0
        elif wetland_dist <= 300:
            score += 10.0
        
        # Cliff proximity
        cliff_dist = terrain_features['cliff_proximity']
        if cliff_dist <= 200:
            score += 15.0
        
        # Visibility limitation
        visibility = terrain_features['visibility_limitation']
        if visibility >= 0.8:
            score += 10.0
        
        return min(score, 100.0)

    test_locations = [
        {"name": "Mountain", "lat": 44.0708, "lon": -72.8429},
        {"name": "Valley", "lat": 44.0500, "lon": -72.8000},
        {"name": "Ridge", "lat": 44.1000, "lon": -72.9000},
        {"name": "Forest", "lat": 44.2000, "lon": -72.7000},
        {"name": "Lake", "lat": 44.1500, "lon": -72.8500}
    ]
    
    print("\n\nEnhanced Pressure Resistance Score Test:")
    print("="*60)
    
    for location in test_locations:
        lat, lon = location["lat"], location["lon"]
        
        # Calculate enhanced terrain features
        features = calculate_enhanced_terrain_features(lat, lon)
        
        # Calculate pressure resistance score
        pressure_score = calculate_pressure_resistance(features)
        
        print(f"\n{location['name']} ({lat}, {lon}):")
        print(f"  Escape cover: {features['escape_cover_density']:.1f}%")
        print(f"  Hunter access: {features['hunter_accessibility']:.2f}")
        print(f"  Wetland dist: {features['wetland_proximity']:.0f}m")
        print(f"  Cliff dist: {features['cliff_proximity']:.0f}m")
        print(f"  Visibility: {features['visibility_limitation']:.2f}")
        print(f"  Pressure resistance score: {pressure_score:.1f}")

if __name__ == "__main__":
    test_enhanced_road_distance()
    test_enhanced_pressure_resistance()
