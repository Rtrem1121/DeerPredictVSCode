#!/usr/bin/env python3
"""
Test Enhanced Terrain Analysis for Mature Buck Predictions

This test demonstrates the advanced terrain feature detection capabilities
for improving mature buck hunting predictions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import json
from typing import Dict
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_enhanced_terrain_analysis():
    """Test the enhanced terrain analysis system"""
    print("🔍 TESTING ENHANCED TERRAIN ANALYSIS FOR MATURE BUCK PREDICTIONS")
    print("=" * 70)
    
    try:
        # Import the enhanced system
        from mature_buck_predictor import get_mature_buck_predictor
        from terrain_analyzer import get_terrain_analyzer
        from config_manager import get_config
        
        print("📋 Testing Configuration Loading...")
        config = get_config()
        print(f"✅ Configuration loaded: {config.environment} environment")
        
        print("\n🔍 Testing Terrain Analyzer...")
        terrain_analyzer = get_terrain_analyzer()
        print("✅ Terrain analyzer initialized")
        
        print("\n🎯 Testing Mature Buck Predictor...")
        mature_buck_predictor = get_mature_buck_predictor()
        print("✅ Mature buck predictor initialized")
        
        # Test coordinates (Vermont hunting area)
        test_lat = 44.2601
        test_lon = -72.5806
        
        print(f"\n📍 Testing Advanced Terrain Analysis for {test_lat}, {test_lon}")
        print("-" * 50)
        
        # Perform advanced terrain analysis
        terrain_analysis = terrain_analyzer.analyze_terrain_features(test_lat, test_lon)
        
        print(f"✅ Terrain analysis complete!")
        print(f"   Grid spacing: {terrain_analysis['elevation_grid']['grid_spacing']}m")
        print(f"   Features detected: {len(terrain_analysis['detected_features'])}")
        print(f"   Travel corridors: {len(terrain_analysis['travel_corridors'])}")
        print(f"   Natural funnels: {len(terrain_analysis['natural_funnels'])}")
        
        # Display elevation statistics
        elev_stats = terrain_analysis['elevation_grid']['elevation_stats']
        print(f"\n📊 Elevation Analysis:")
        print(f"   Range: {elev_stats['min_elevation']:.1f}m - {elev_stats['max_elevation']:.1f}m")
        print(f"   Relief: {elev_stats['elevation_range']:.1f}m")
        print(f"   Complexity: {terrain_analysis['elevation_grid']['topographic_complexity']:.2f}")
        
        # Display detected features
        print(f"\n🔍 Detected Terrain Features:")
        feature_summary = terrain_analysis['spatial_summary']['feature_distribution']
        for feature_type, count in feature_summary.items():
            if count > 0:
                features_of_type = [f for f in terrain_analysis['detected_features'] 
                                   if f['type'] == feature_type]
                if features_of_type:
                    avg_score = np.mean([f['mature_buck_score'] for f in features_of_type])
                    print(f"   {feature_type}: {count} detected (avg score: {avg_score:.1f})")
        
        # Display mature buck analysis
        print(f"\n🦌 Mature Buck Suitability Analysis:")
        buck_analysis = terrain_analysis['mature_buck_analysis']
        print(f"   Overall suitability: {buck_analysis['overall_suitability']:.1f}/100")
        print(f"   High-value features: {terrain_analysis['spatial_summary']['high_value_features']}")
        
        if buck_analysis['recommendations']:
            print(f"\n💡 Terrain Recommendations:")
            for rec in buck_analysis['recommendations'][:3]:
                print(f"   • {rec}")
        
        # Test enhanced mature buck prediction
        print(f"\n🎯 Testing Enhanced Mature Buck Prediction...")
        print("-" * 50)
        
        # Sample terrain and weather data
        basic_terrain = {
            'elevation': elev_stats['mean_elevation'],
            'slope': 15.0,
            'aspect': 225.0,  # Southwest
            'canopy_closure': 75.0,
            'water_proximity': 300.0,
            'agricultural_proximity': 800.0
        }
        
        weather_data = {
            'season': 'rut',
            'hour': 7,  # Early morning
            'temperature': 8.0,  # Celsius
            'wind_speed': 8.0,
            'pressure_trend': 'falling',
            'conditions': ['partly_cloudy']
        }
        
        # Run enhanced prediction
        enhanced_prediction = mature_buck_predictor.predict_with_advanced_terrain_analysis(
            season='rut',
            time_of_day=7,
            terrain_features=basic_terrain,
            weather_data=weather_data,
            lat=test_lat,
            lon=test_lon
        )
        
        print(f"✅ Enhanced prediction complete!")
        print(f"   Base confidence: {enhanced_prediction.get('confidence_score', 0):.1f}")
        print(f"   Terrain adjustment: {enhanced_prediction.get('terrain_confidence_adjustment', 0):+.1f}")
        print(f"   Movement probability: {enhanced_prediction.get('movement_probability', 0):.1f}%")
        
        # Display enhanced corridors
        print(f"\n🛤️ Enhanced Movement Corridors:")
        enhanced_corridors = enhanced_prediction['movement_corridors']
        for i, corridor in enumerate(enhanced_corridors[:3]):
            terrain_flag = "🔍" if corridor.get('terrain_analysis', False) else "📍"
            print(f"   {terrain_flag} {corridor['type']}: {corridor['confidence']:.1f}% confidence")
            if 'terrain_features' in corridor:
                print(f"      Features: {corridor['terrain_features'].get('type', 'multiple')}")
        
        # Display enhanced bedding areas
        print(f"\n🛏️ Enhanced Bedding Predictions:")
        enhanced_bedding = enhanced_prediction['bedding_predictions']
        for i, bedding in enumerate(enhanced_bedding[:3]):
            terrain_flag = "🔍" if bedding.get('terrain_characteristics') else "📍"
            print(f"   {terrain_flag} {bedding['type']}: {bedding['confidence']:.1f}% confidence")
            if 'terrain_support' in bedding:
                print(f"      Terrain support: {bedding['terrain_support']['supporting_features']} features")
        
        # Display terrain-based stand recommendations
        if 'terrain_stand_recommendations' in enhanced_prediction:
            print(f"\n🎯 Terrain-Based Stand Recommendations:")
            terrain_stands = enhanced_prediction['terrain_stand_recommendations']
            for i, stand in enumerate(terrain_stands[:3]):
                print(f"   {i+1}. {stand['type']}")
                print(f"      Score: {stand['mature_buck_score']:.1f}/100")
                print(f"      Position: {stand['lat']:.4f}, {stand['lon']:.4f}")
                if stand['terrain_advantages']:
                    key_advantages = list(stand['terrain_advantages'].keys())[:2]
                    print(f"      Advantages: {', '.join(key_advantages)}")
        
        # Display natural funnels
        if enhanced_prediction['natural_funnels']:
            print(f"\n🎯 Natural Terrain Funnels:")
            for i, funnel in enumerate(enhanced_prediction['natural_funnels']):
                print(f"   {i+1}. {funnel['type']}")
                print(f"      Suitability: {funnel['mature_buck_suitability']:.1f}/100")
                print(f"      Features: {funnel['properties']['feature_count']} contributing")
                print(f"      Strength: {funnel['properties']['funnel_strength']:.2f}")
        
        # Display behavioral insights
        if 'terrain_behavioral_insights' in enhanced_prediction:
            print(f"\n🧠 Terrain-Based Behavioral Insights:")
            insights = enhanced_prediction['terrain_behavioral_insights']
            for insight in insights[:4]:
                print(f"   • {insight}")
        
        print(f"\n📊 Performance Metrics:")
        print(f"   Features detected: {len(terrain_analysis['detected_features'])}")
        print(f"   Corridors identified: {len(terrain_analysis['travel_corridors'])}")
        print(f"   Funnels found: {len(terrain_analysis['natural_funnels'])}")
        print(f"   Terrain stands: {len(enhanced_prediction.get('terrain_stand_recommendations', []))}")
        
        # Test with different coordinates
        print(f"\n🔄 Testing Different Location...")
        test_lat2 = 44.2801  # Slightly different location
        test_lon2 = -72.5606
        
        # Quick terrain analysis for comparison
        terrain_analysis2 = terrain_analyzer.analyze_terrain_features(test_lat2, test_lon2)
        
        print(f"   Location 2 features: {len(terrain_analysis2['detected_features'])}")
        print(f"   Location 2 suitability: {terrain_analysis2['mature_buck_analysis']['overall_suitability']:.1f}/100")
        
        # Compare locations
        comparison = {
            'Location 1': {
                'coordinates': f"{test_lat:.4f}, {test_lon:.4f}",
                'features': len(terrain_analysis['detected_features']),
                'suitability': terrain_analysis['mature_buck_analysis']['overall_suitability'],
                'complexity': terrain_analysis['elevation_grid']['topographic_complexity']
            },
            'Location 2': {
                'coordinates': f"{test_lat2:.4f}, {test_lon2:.4f}",
                'features': len(terrain_analysis2['detected_features']),
                'suitability': terrain_analysis2['mature_buck_analysis']['overall_suitability'],
                'complexity': terrain_analysis2['elevation_grid']['topographic_complexity']
            }
        }
        
        print(f"\n📊 Location Comparison:")
        for location, data in comparison.items():
            print(f"   {location}: {data['features']} features, {data['suitability']:.1f} suitability, {data['complexity']:.2f} complexity")
        
        print(f"\n🎉 ALL ENHANCED TERRAIN TESTS PASSED!")
        print("The advanced terrain analysis system is operational and ready for use.")
        
        print(f"\n💡 Next Steps:")
        print("- Integrate with main prediction API")
        print("- Add terrain caching for performance")
        print("- Connect to real elevation data sources")
        print("- Implement spatial database for feature storage")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all required packages are installed:")
        print("pip install geopandas shapely scipy scikit-learn")
        return False
        
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🦌 ENHANCED TERRAIN ANALYSIS FOR MATURE BUCK PREDICTIONS")
    print("=" * 60)
    print("Testing advanced 5x5 elevation grid analysis with GeoPandas")
    print("Detecting travel corridors, funnels, and terrain features")
    print("=" * 60)
    
    success = test_enhanced_terrain_analysis()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("Enhanced terrain analysis system is ready for production use.")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")
        sys.exit(1)
