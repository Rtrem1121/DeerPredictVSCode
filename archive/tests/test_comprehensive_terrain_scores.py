#!/usr/bin/env python3
"""
Comprehensive test to verify each terrain score calculation step by step
"""
import requests
import json

def test_specific_location_calculation():
    """Test the exact location from the user's example"""
    backend_url = "http://localhost:8000"
    
    # Test the specific coordinates from the user's example
    test_request = {
        "name": "User Example Location",
        "lat": 44.074565,
        "lon": -72.647567,
        "date_time": "2024-10-15T06:00:00",
        "season": "early_season",
        "weather": {"temperature": 45, "wind_speed": 8, "wind_direction": 190}
    }
    
    print("Testing User's Specific Location:")
    print("="*60)
    print(f"Coordinates: {test_request['lat']}, {test_request['lon']}")
    print(f"Expected: Isolation=95.0%, Pressure=60.0%")
    print("="*60)
    
    try:
        # Make prediction request
        response = requests.post(
            f"{backend_url}/predict",
            json=test_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'mature_buck_analysis' in data:
                mature_buck_data = data['mature_buck_analysis']
                terrain_scores = mature_buck_data.get('terrain_scores', {})
                
                print("ACTUAL API RESULTS:")
                print(f"  Bedding Suitability: {terrain_scores.get('bedding_suitability', 'N/A'):.1f}%")
                print(f"  Escape Route Quality: {terrain_scores.get('escape_route_quality', 'N/A'):.1f}%")
                print(f"  Isolation Score: {terrain_scores.get('isolation_score', 'N/A'):.1f}%")
                print(f"  Pressure Resistance: {terrain_scores.get('pressure_resistance', 'N/A'):.1f}%")
                print(f"  Overall Suitability: {terrain_scores.get('overall_suitability', 'N/A'):.1f}%")
                
                # Check if we're still getting the problematic values
                isolation = terrain_scores.get('isolation_score', 0)
                pressure = terrain_scores.get('pressure_resistance', 0)
                
                if isolation == 95.0:
                    print("\n❌ ISOLATION SCORE STILL HARDCODED AT 95.0!")
                if pressure == 60.0:
                    print("❌ PRESSURE RESISTANCE STILL HARDCODED AT 60.0!")
                    
                if isolation == 95.0 or pressure == 60.0:
                    print("\n🔍 DEBUGGING WHY SCORES ARE STILL HARDCODED...")
                    return True  # Still has issues
                else:
                    print("\n✅ SCORES ARE NOW PROPERLY CALCULATED!")
                    return False  # Fixed
                    
            else:
                print("❌ mature_buck_analysis not found!")
                return True
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return True

def manual_calculation_test():
    """Manually calculate what the terrain scores should be for this location"""
    lat, lon = 44.074565, -72.647567
    
    print("\n" + "="*60)
    print("MANUAL CALCULATION VERIFICATION:")
    print("="*60)
    
    # 1. Test enhanced road distance calculation
    def calculate_enhanced_road_distance(lat: float, lon: float) -> float:
        lat_factor = abs(lat * 1000) % 100
        lon_factor = abs(lon * 1000) % 100
        combined_factor = (lat_factor + lon_factor * 1.7) % 100
        
        if combined_factor < 30:  # 30% urban/suburban
            base_distance = 100 + (combined_factor * 23.3)  # 100-800m
            category = "Urban/Suburban"
        elif combined_factor < 70:  # 40% rural
            base_distance = 500 + ((combined_factor - 30) * 37.5)  # 500-2000m
            category = "Rural"
        else:  # 30% remote
            base_distance = 1500 + ((combined_factor - 70) * 116.7)  # 1500-5000m
            category = "Remote"
        
        return max(100.0, min(5000.0, base_distance)), category, combined_factor
    
    road_dist_m, category, factor = calculate_enhanced_road_distance(lat, lon)
    road_dist_yards = road_dist_m * 1.094
    
    print(f"1. ROAD DISTANCE CALCULATION:")
    print(f"   lat_factor: {abs(lat * 1000) % 100:.1f}")
    print(f"   lon_factor: {abs(lon * 1000) % 100:.1f}")
    print(f"   combined_factor: {factor:.1f}")
    print(f"   Category: {category}")
    print(f"   Road distance: {road_dist_m:.0f}m ({road_dist_yards:.0f} yards)")
    
    # Calculate isolation score
    road_impact_range = 500.0
    if road_dist_yards >= road_impact_range:
        isolation_score = 95.0
    elif road_dist_yards >= road_impact_range * 0.7:  # >= 350
        isolation_score = 70.0 + (road_dist_yards / road_impact_range * 25.0)
    elif road_dist_yards >= road_impact_range * 0.3:  # >= 150  
        isolation_score = 40.0 + (road_dist_yards / (road_impact_range * 0.7) * 30.0)
    else:
        isolation_score = 10.0 + (road_dist_yards / (road_impact_range * 0.3) * 30.0)
    
    print(f"   Expected Isolation Score: {isolation_score:.1f}")
    
    # 2. Test enhanced pressure resistance calculation
    print(f"\n2. PRESSURE RESISTANCE CALCULATION:")
    
    lat_factor = abs(lat * 1000) % 100
    lon_factor = abs(lon * 1000) % 100
    
    # Enhanced terrain features
    cover_base = 30.0 + ((lat_factor + lon_factor * 1.3) % 100) * 0.6
    escape_cover_density = max(30.0, min(90.0, cover_base))
    
    access_base = 0.2 + ((lat_factor * 1.4 + lon_factor) % 100) * 0.006
    hunter_accessibility = max(0.2, min(0.8, access_base))
    
    wetland_base = 100.0 + ((lat_factor * 1.1 + lon_factor * 1.6) % 100) * 14.0
    wetland_proximity = max(100.0, min(1500.0, wetland_base))
    
    cliff_base = 200.0 + ((lat_factor * 1.8 + lon_factor * 0.9) % 100) * 23.0
    cliff_proximity = max(200.0, min(2500.0, cliff_base))
    
    vis_base = 0.3 + ((lat_factor * 0.7 + lon_factor * 1.2) % 100) * 0.006
    visibility_limitation = max(0.3, min(0.9, vis_base))
    
    print(f"   Enhanced terrain features:")
    print(f"     Escape cover: {escape_cover_density:.1f}%")
    print(f"     Hunter accessibility: {hunter_accessibility:.2f}")
    print(f"     Wetland proximity: {wetland_proximity:.0f}m")
    print(f"     Cliff proximity: {cliff_proximity:.0f}m")
    print(f"     Visibility limitation: {visibility_limitation:.2f}")
    
    # Calculate pressure resistance score
    pressure_score = 0.0
    
    # Thick escape cover
    if escape_cover_density >= 80.0:
        pressure_score += 30.0
        cover_points = 30.0
    elif escape_cover_density >= 60.0:
        pressure_score += 20.0
        cover_points = 20.0
    else:
        cover_points = 0.0
    
    # Hunter accessibility
    if hunter_accessibility <= 0.3:
        pressure_score += 25.0
        access_points = 25.0
    elif hunter_accessibility <= 0.5:
        pressure_score += 15.0
        access_points = 15.0
    else:
        access_points = 0.0
    
    # Wetland proximity
    if wetland_proximity <= 100:
        pressure_score += 20.0
        wetland_points = 20.0
    elif wetland_proximity <= 300:
        pressure_score += 10.0
        wetland_points = 10.0
    else:
        wetland_points = 0.0
    
    # Cliff proximity
    if cliff_proximity <= 200:
        pressure_score += 15.0
        cliff_points = 15.0
    else:
        cliff_points = 0.0
    
    # Visibility limitation
    if visibility_limitation >= 0.8:
        pressure_score += 10.0
        vis_points = 10.0
    else:
        vis_points = 0.0
    
    final_pressure = min(pressure_score, 100.0)
    
    print(f"   Pressure resistance scoring:")
    print(f"     Cover points: +{cover_points}")
    print(f"     Access points: +{access_points}")
    print(f"     Wetland points: +{wetland_points}")
    print(f"     Cliff points: +{cliff_points}")
    print(f"     Visibility points: +{vis_points}")
    print(f"   Expected Pressure Resistance: {final_pressure:.1f}")
    
    return isolation_score, final_pressure

def run_comprehensive_test():
    """Run the comprehensive test"""
    print("COMPREHENSIVE TERRAIN SCORES TEST")
    print("="*80)
    
    # Test API response
    has_issues = test_specific_location_calculation()
    
    # Show what the calculation should be
    expected_isolation, expected_pressure = manual_calculation_test()
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    print(f"Expected Isolation Score: {expected_isolation:.1f}")
    print(f"Expected Pressure Resistance: {expected_pressure:.1f}")
    
    if has_issues:
        print("\n❌ THE FIX IS NOT WORKING PROPERLY")
        print("🔧 NEED TO DEBUG WHY ENHANCED CALCULATIONS AREN'T BEING USED")
    else:
        print("\n✅ THE FIX IS WORKING!")

if __name__ == "__main__":
    run_comprehensive_test()
