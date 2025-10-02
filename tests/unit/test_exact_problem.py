#!/usr/bin/env python3
"""
Test the exact coordinates from the user's problem report
"""

import sys
import json
from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor

def test_exact_problem_coordinates():
    """Test the exact coordinates from the problem report"""
    print("🎯 TESTING EXACT COORDINATES FROM PROBLEM REPORT")
    print("=" * 60)
    
    # Exact coordinates from the problem report
    test_lat = 43.3106
    test_lon = -73.2306
    
    print(f"📍 Exact Problem Coordinates: {test_lat:.4f}, {test_lon:.4f}")
    print("🎯 User reported: Only 1 alternative bedding zone generated")
    print("🎯 Expected: 2-3 bedding zones for mature buck movement patterns")
    print()
    
    try:
        predictor = EnhancedBeddingZonePredictor()
        
        # Get full biological analysis (matches user's use case)
        print("🦌 RUNNING FULL BIOLOGICAL ANALYSIS...")
        result = predictor.run_enhanced_biological_analysis(
            lat=test_lat,
            lon=test_lon,
            time_of_day=14,  # Afternoon (as mentioned in warm September conditions)
            season="fall",
            hunting_pressure="low"
        )
        
        print("✅ BIOLOGICAL ANALYSIS COMPLETED")
        print()
        
        # Extract bedding zones
        bedding_zones = result.get("bedding_zones", {})
        bedding_features = bedding_zones.get("features", [])
        
        print("📊 BEDDING ZONE RESULTS:")
        print("=" * 40)
        print(f"Total Bedding Zones: {len(bedding_features)}")
        print(f"User Expected: 2-3 zones")
        print(f"Result Status: {'✅ MEETS REQUIREMENT' if len(bedding_features) >= 2 else '❌ FAILS REQUIREMENT'}")
        print()
        
        # Detailed analysis
        if bedding_features:
            distances = []
            aspects = []
            zone_types = []
            
            for i, feature in enumerate(bedding_features):
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [0, 0])
                
                distance = props.get('distance_from_primary', 0)
                aspect = props.get('aspect')
                zone_type = props.get('bedding_type', 'unknown')
                
                if distance: distances.append(distance)
                if aspect: aspects.append(aspect)
                zone_types.append(zone_type)
                
                print(f"🛏️ Bedding Zone {i+1}:")
                print(f"   Location: {coords[1]:.4f}, {coords[0]:.4f}")
                print(f"   Type: {zone_type}")
                print(f"   Distance: {distance}m from primary")
                print(f"   Aspect: {aspect:.1f}° ({'optimal' if aspect and 135 <= aspect <= 225 else 'suboptimal'})")
                print(f"   Score: {props.get('score', 0):.1f}%")
                print()
            
            # Movement pattern analysis
            print("🦌 MOVEMENT PATTERN ANALYSIS:")
            print(f"   Distance Range: {min(distances) if distances else 0}-{max(distances) if distances else 0}m")
            print(f"   Optimal Range: 200-500m (mature buck bedding pattern)")
            print(f"   Aspect Spread: {max(aspects) - min(aspects) if len(aspects) > 1 else 0:.0f}°")
            print(f"   Zone Types: {len(set(zone_types))} different types")
            print()
            
            # Compare to user's problem
            print("🎯 PROBLEM RESOLUTION STATUS:")
            original_problem = "Only 1 alternative bedding zone generated"
            current_result = f"{len(bedding_features)} bedding zones generated"
            
            print(f"   Original Problem: {original_problem}")
            print(f"   Current Result: {current_result}")
            
            if len(bedding_features) >= 2:
                print("   ✅ PROBLEM RESOLVED: Multiple bedding zones now generated")
                print("   🦌 Mature buck movement model will now have adequate bedding options")
            else:
                print("   ❌ PROBLEM PERSISTS: Still only generating single bedding zone")
            
            # Biological accuracy assessment
            all_south_facing = all(a and 135 <= a <= 225 for a in aspects if a)
            adequate_distances = distances and min(distances) >= 100 and max(distances) <= 800
            multiple_types = len(set(zone_types)) >= 2
            
            print()
            print("🏆 BIOLOGICAL ACCURACY ASSESSMENT:")
            print(f"   ✅ Multiple Zones: {len(bedding_features) >= 2}")
            print(f"   ✅ South-Facing: {all_south_facing}")
            print(f"   ✅ Proper Distances: {adequate_distances}")
            print(f"   ✅ Type Diversity: {multiple_types}")
            
            grade = sum([len(bedding_features) >= 2, all_south_facing, adequate_distances, multiple_types])
            grades = ["F", "D", "C", "B", "A"]
            final_grade = grades[min(grade, 4)]
            
            print(f"   🎯 Final Grade: {final_grade}")
            
        else:
            print("❌ NO BEDDING ZONES GENERATED")
            print("   This indicates a critical failure in the fallback system")
        
        return result
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_exact_problem_coordinates()
