#!/usr/bin/env python3
"""
Test Wind Integration for Mature Buck Predictions

This test validates that the wind analysis system is properly integrated
with the mature buck predictor and stand recommendations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_wind_integration():
    """Test wind system integration with mature buck predictions"""
    print("🌬️ TESTING WIND INTEGRATION FOR MATURE BUCK PREDICTIONS")
    print("=" * 60)
    
    try:
        # Import required modules
        from mature_buck_predictor import get_mature_buck_predictor, generate_mature_buck_stand_recommendations
        from wind_analysis import get_wind_analyzer
        from config_manager import get_config
        
        print("✅ All modules imported successfully")
        
        # Test coordinates (Vermont hunting area)
        test_lat = 44.2601
        test_lon = -72.5806
        
        print(f"\n🌬️ Testing Wind Analyzer...")
        wind_analyzer = get_wind_analyzer()
        print("✅ Wind analyzer initialized")
        
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
        
        # Test mature buck scoring
        print(f"\n🎯 Testing Mature Buck Terrain Scoring...")
        buck_predictor = get_mature_buck_predictor()
        mature_buck_scores = buck_predictor.analyze_mature_buck_terrain(terrain_features, test_lat, test_lon)
        print(f"✅ Mature buck suitability: {mature_buck_scores['overall_suitability']:.1f}/100")
        
        # Test weather data with wind information
        test_weather_data = {
            'temperature': 35.0,
            'wind_speed': 8.0,
            'wind_direction': 270.0,  # West wind
            'pressure': 1015.0,
            'conditions': ['clear']
        }
        
        print(f"\n🌬️ Testing Wind-Optimized Stand Recommendations...")
        stand_recommendations = generate_mature_buck_stand_recommendations(
            terrain_features, mature_buck_scores, test_lat, test_lon, test_weather_data
        )
        
        print(f"✅ Generated {len(stand_recommendations)} wind-optimized stand recommendations")
        
        # Analyze wind optimization in recommendations
        wind_optimized_count = 0
        for i, stand in enumerate(stand_recommendations, 1):
            print(f"\n   Stand {i}: {stand['type']}")
            print(f"   Confidence: {stand['confidence']:.1f}/100")
            
            if stand.get('wind_optimized'):
                wind_optimized_count += 1
                print(f"   🌬️ Wind Optimized: YES")
                
                wind_data = stand.get('wind_analysis', {})
                if wind_data:
                    print(f"   Wind Advantage: {wind_data.get('wind_advantage_score', 'N/A')}")
                    print(f"   Scent Control: {wind_data.get('scent_control_rating', 'N/A')}")
                
                wind_notes = stand.get('wind_notes', [])
                for note in wind_notes:
                    print(f"   {note}")
            else:
                print(f"   🌬️ Wind Optimized: NO")
        
        print(f"\n📊 Wind Integration Summary:")
        print(f"   Total stands: {len(stand_recommendations)}")
        print(f"   Wind-optimized stands: {wind_optimized_count}")
        print(f"   Wind optimization rate: {(wind_optimized_count/len(stand_recommendations)*100):.1f}%")
        
        # Test movement prediction with weather data
        print(f"\n🦌 Testing Enhanced Movement Prediction with Wind...")
        movement_prediction = buck_predictor.predict_with_advanced_terrain_analysis(
            season='rut',
            time_of_day=7,
            terrain_features=terrain_features,
            weather_data=test_weather_data,
            lat=test_lat,
            lon=test_lon
        )
        
        print(f"✅ Enhanced prediction complete")
        print(f"   Movement probability: {movement_prediction['movement_probability']:.1f}%")
        print(f"   Final confidence: {movement_prediction['confidence_score']:.1f}/100")
        
        behavioral_notes = movement_prediction.get('behavioral_notes', [])
        wind_related_notes = [note for note in behavioral_notes if '🌬️' in note or 'wind' in note.lower()]
        if wind_related_notes:
            print(f"   Wind-related insights:")
            for note in wind_related_notes:
                print(f"   • {note}")
        
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
    print("🌬️ WIND INTEGRATION TEST FOR MATURE BUCK PREDICTIONS")
    print("=" * 60)
    print("Testing wind-aware stand positioning and scent management")
    print("=" * 60)
    
    success = test_wind_integration()
    
    if success:
        print("\n✅ All wind integration tests passed!")
        print("Wind-aware mature buck prediction system is operational.")
    else:
        print("\n❌ Wind integration tests failed.")
        sys.exit(1)
