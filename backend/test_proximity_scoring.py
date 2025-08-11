#!/usr/bin/env python3
"""
Test Proximity Scoring System for Mature Buck Predictions

This test validates the proximity scoring functionality that calculates
distances between stand positions and predicted deer activity zones.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_proximity_scoring():
    """Test the proximity scoring system"""
    print("🎯 TESTING PROXIMITY SCORING SYSTEM")
    print("=" * 50)
    
    try:
        # Import required modules
        from mature_buck_predictor import get_mature_buck_predictor, generate_mature_buck_stand_recommendations
        from config_manager import get_config
        
        print("✅ All modules imported successfully")
        
        # Test coordinates (Vermont hunting area)
        test_lat = 44.2601
        test_lon = -72.5806
        
        print(f"\n🎯 Testing Proximity Scoring for {test_lat}, {test_lon}")
        
        # Test basic terrain data
        terrain_features = {
            'elevation': 300.0,
            'slope': 15.0,
            'aspect': 225.0,  # Southwest facing
            'canopy_closure': 85.0,
            'understory_density': 70.0,
            'escape_cover_density': 80.0,
            'agricultural_proximity': 200.0,
            'road_proximity': 150.0
        }
        
        # Test mature buck predictor
        print(f"\n🔍 Testing Core Proximity Functions...")
        buck_predictor = get_mature_buck_predictor()
        
        # Test bedding and feeding predictions
        bedding_locations = buck_predictor._predict_bedding_locations(terrain_features, test_lat, test_lon)
        feeding_locations = buck_predictor._predict_feeding_zones(terrain_features, test_lat, test_lon, 'rut')
        
        print(f"✅ Predicted {len(bedding_locations)} bedding locations")
        print(f"✅ Predicted {len(feeding_locations)} feeding locations")
        
        # Test proximity scoring for a nearby stand position
        stand_lat = test_lat + 0.001  # About 100 meters away
        stand_lon = test_lon + 0.001
        
        proximity_scores = buck_predictor.calculate_zone_proximity_scores(
            stand_lat, stand_lon, bedding_locations, feeding_locations
        )
        
        print(f"\n📊 Proximity Analysis Results:")
        print(f"   Combined Score: {proximity_scores['combined_proximity_score']:.1f}/100")
        
        bedding_prox = proximity_scores['bedding_proximity']
        print(f"   🛏️ Bedding Proximity:")
        print(f"      Closest: {bedding_prox['closest_distance_yards']:.0f} yards")
        print(f"      Score: {bedding_prox['proximity_score']:.1f}/100")
        print(f"      Optimal Range: {bedding_prox['optimal_range']}")
        
        feeding_prox = proximity_scores['feeding_proximity']
        print(f"   🌿 Feeding Proximity:")
        print(f"      Closest: {feeding_prox['closest_distance_yards']:.0f} yards")
        print(f"      Score: {feeding_prox['proximity_score']:.1f}/100")
        print(f"      Optimal Range: {feeding_prox['optimal_range']}")
        
        # Test different distances to validate scoring algorithm
        print(f"\n🧪 Testing Proximity Scoring Algorithm...")
        test_distances = [50, 100, 150, 200, 300, 500]
        
        for distance in test_distances:
            bedding_score = buck_predictor._calculate_proximity_score(
                distance, 75, 200, 400  # Bedding thresholds
            )
            feeding_score = buck_predictor._calculate_proximity_score(
                distance, 25, 150, 300  # Feeding thresholds
            )
            print(f"   {distance:3d} yards -> Bedding: {bedding_score:5.1f}, Feeding: {feeding_score:5.1f}")
        
        # Test mature buck scores
        mature_buck_scores = buck_predictor.analyze_mature_buck_terrain(terrain_features, test_lat, test_lon)
        
        # Test enhanced stand recommendations with proximity
        print(f"\n🎯 Testing Enhanced Stand Recommendations with Proximity...")
        stand_recommendations = generate_mature_buck_stand_recommendations(
            terrain_features, mature_buck_scores, test_lat, test_lon
        )
        
        print(f"✅ Generated {len(stand_recommendations)} proximity-enhanced recommendations")
        
        # Analyze proximity integration in recommendations
        proximity_enhanced_count = 0
        for i, stand in enumerate(stand_recommendations, 1):
            print(f"\n   Stand {i}: {stand['type']}")
            print(f"   Confidence: {stand['confidence']:.1f}/100")
            
            if 'proximity_analysis' in stand and stand['proximity_analysis']:
                proximity_enhanced_count += 1
                prox_data = stand['proximity_analysis']
                proximity_boost = stand.get('proximity_confidence_adjustment', 0)
                
                print(f"   🎯 Proximity Enhanced: YES")
                print(f"   Proximity Score: {prox_data['combined_proximity_score']:.1f}/100")
                print(f"   Confidence Boost: {proximity_boost:+.1f}")
                
                proximity_notes = stand.get('proximity_notes', [])
                for note in proximity_notes:
                    print(f"   {note}")
            else:
                print(f"   🎯 Proximity Enhanced: NO")
        
        print(f"\n📊 Proximity Integration Summary:")
        print(f"   Total stands: {len(stand_recommendations)}")
        print(f"   Proximity-enhanced stands: {proximity_enhanced_count}")
        print(f"   Enhancement rate: {(proximity_enhanced_count/len(stand_recommendations)*100):.1f}%")
        
        # Test edge cases
        print(f"\n🧪 Testing Edge Cases...")
        
        # Test with no bedding/feeding locations
        empty_proximity = buck_predictor.calculate_zone_proximity_scores(
            test_lat, test_lon, [], []
        )
        print(f"   Empty zones score: {empty_proximity['combined_proximity_score']:.1f}")
        
        # Test extreme distances
        extreme_scores = []
        for distance in [1, 10, 1000, 10000]:
            score = buck_predictor._calculate_proximity_score(distance, 75, 200, 400)
            extreme_scores.append(score)
            print(f"   {distance:5d} yards -> Score: {score:.1f}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 PROXIMITY SCORING SYSTEM TEST")
    print("=" * 50)
    print("Testing distance-based confidence adjustments for stand recommendations")
    print("=" * 50)
    
    success = test_proximity_scoring()
    
    if success:
        print("\n✅ All proximity scoring tests passed!")
        print("Proximity-enhanced stand recommendation system is operational.")
    else:
        print("\n❌ Proximity scoring tests failed.")
        sys.exit(1)
