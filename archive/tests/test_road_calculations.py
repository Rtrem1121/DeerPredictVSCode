#!/usr/bin/env python3
"""
Test the exact road distance calculation for our locations
"""

def estimate_road_distance(lat: float, lon: float) -> float:
    """Replicate the road distance calculation from terrain_feature_mapper.py"""
    coord_hash = abs(hash(f"{lat:.4f},{lon:.4f}")) % 1000
    base_distance = 500 + (coord_hash * 2.5)
    return max(200.0, min(5000.0, base_distance))

def calculate_road_impact_score(road_distance_yards: float) -> float:
    """Replicate road impact score calculation from distance_scorer.py"""
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

def test_road_scores():
    """Test road scores for our locations"""
    test_locations = [
        {"name": "Mountain", "lat": 44.0708, "lon": -72.8429},
        {"name": "Valley", "lat": 44.0500, "lon": -72.8000},
        {"name": "Ridge", "lat": 44.1000, "lon": -72.9000}
    ]
    
    print("Road distance and scoring analysis:")
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
        print(f"  Road distance: {road_dist_m:.1f}m ({road_dist_yards:.1f} yards)")
        print(f"  Road impact score: {road_score:.1f}")
        
        # Check which range it falls into
        road_impact_range = 500.0
        if road_dist_yards >= road_impact_range:
            print(f"  Range: >= {road_impact_range} (Max score: 95.0)")
        elif road_dist_yards >= road_impact_range * 0.7:
            print(f"  Range: >= {road_impact_range * 0.7:.1f} (Score: 70.0-95.0)")
        elif road_dist_yards >= road_impact_range * 0.3:
            print(f"  Range: >= {road_impact_range * 0.3:.1f} (Score: 40.0-70.0)")
        else:
            print(f"  Range: < {road_impact_range * 0.3:.1f} (Score: 10.0-40.0)")

if __name__ == "__main__":
    test_road_scores()
