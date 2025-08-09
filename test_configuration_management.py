#!/usr/bin/env python3
"""
Test Configuration Management System

This script tests the configuration management implementation to ensure
all modules can load and use configuration values correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config_manager import get_config, reload_config
from backend.mature_buck_predictor import MatureBuckPreferences, MatureBuckBehaviorModel
from backend.scoring_engine import get_scoring_engine, TerrainScoreComponents
from backend.distance_scorer import get_distance_scorer, ProximityFactors

def test_configuration_loading():
    """Test that configuration loads correctly"""
    print("🧪 Testing Configuration Loading...")
    
    config = get_config()
    
    # Test basic configuration access
    version = config.get('version', 'unknown')
    print(f"✅ Configuration version: {version}")
    
    # Test mature buck preferences
    buck_prefs = config.get_mature_buck_preferences()
    print(f"✅ Mature buck preferences loaded: {len(buck_prefs)} categories")
    
    # Test scoring factors
    scoring_factors = config.get_scoring_factors()
    print(f"✅ Scoring factors loaded: {len(scoring_factors)} categories")
    
    # Test seasonal weights
    seasonal_weights = config.get_seasonal_weights()
    print(f"✅ Seasonal weights loaded: {len(seasonal_weights)} seasons")
    
    # Test weather modifiers
    weather_modifiers = config.get_weather_modifiers()
    print(f"✅ Weather modifiers loaded: {len(weather_modifiers)} conditions")
    
    # Test distance parameters
    distance_params = config.get_distance_parameters()
    print(f"✅ Distance parameters loaded: {len(distance_params)} parameters")
    
    # Test API settings
    api_settings = config.get_api_settings()
    print(f"✅ API settings loaded: {len(api_settings)} settings")
    
    return True

def test_mature_buck_integration():
    """Test that mature buck predictor uses configuration"""
    print("\n🦌 Testing Mature Buck Configuration Integration...")
    
    # Test preferences loading from config
    prefs = MatureBuckPreferences()
    print(f"✅ Bedding thickness from config: {prefs.min_bedding_thickness}")
    print(f"✅ Escape route count from config: {prefs.escape_route_count}")
    print(f"✅ Human avoidance buffer from config: {prefs.human_avoidance_buffer}")
    
    # Test behavior model configuration
    model = MatureBuckBehaviorModel()
    factors = model.confidence_factors
    print(f"✅ Confidence factors loaded: {len(factors)} factors")
    print(f"✅ Thick cover bonus: {factors.get('thick_cover_bonus')}")
    print(f"✅ Pressure penalty: {factors.get('pressure_penalty')}")
    
    return True

def test_scoring_engine_integration():
    """Test that scoring engine uses configuration"""
    print("\n🎯 Testing Scoring Engine Configuration Integration...")
    
    engine = get_scoring_engine()
    
    # Test seasonal weights
    rut_weights = engine.seasonal_weights.get('rut', {})
    print(f"✅ Rut travel weight: {rut_weights.get('travel')}")
    print(f"✅ Rut movement weight: {rut_weights.get('movement')}")
    
    # Test weather modifiers
    rain_modifiers = engine.weather_modifiers.get('heavy_rain', {})
    print(f"✅ Heavy rain travel modifier: {rain_modifiers.get('travel')}")
    print(f"✅ Heavy rain bedding modifier: {rain_modifiers.get('bedding')}")
    
    # Test terrain scoring with configuration weights
    terrain_components = TerrainScoreComponents(
        elevation_score=80.0,
        slope_score=70.0,
        cover_score=90.0,
        drainage_score=60.0
    )
    total_score = terrain_components.total_score()
    print(f"✅ Terrain total score with config weights: {total_score:.1f}")
    
    return True

def test_distance_scorer_integration():
    """Test that distance scorer uses configuration"""
    print("\n📏 Testing Distance Scorer Configuration Integration...")
    
    scorer = get_distance_scorer()
    
    # Test proximity factors from configuration
    factors = scorer.factors
    print(f"✅ Road impact range: {factors.road_impact_range} yards")
    print(f"✅ Agricultural benefit range: {factors.agricultural_benefit_range} yards")
    print(f"✅ Stand optimal min: {factors.stand_optimal_min} yards")
    print(f"✅ Stand optimal max: {factors.stand_optimal_max} yards")
    
    # Test scoring with configured parameters
    road_score = scorer.calculate_road_impact_score(600.0)  # Beyond impact range
    ag_score = scorer.calculate_agricultural_proximity_score(150.0)  # Close to ag
    print(f"✅ Road impact score (600 yards): {road_score:.1f}")
    print(f"✅ Agricultural proximity score (150 yards): {ag_score:.1f}")
    
    return True

def test_configuration_validation():
    """Test configuration validation and error handling"""
    print("\n🔍 Testing Configuration Validation...")
    
    config = get_config()
    metadata = config.get_metadata()
    
    print(f"✅ Environment: {metadata.environment}")
    print(f"✅ Last loaded: {metadata.last_loaded}")
    print(f"✅ Source files: {len(metadata.source_files)} files")
    
    if metadata.validation_errors:
        print(f"⚠️ Validation warnings: {len(metadata.validation_errors)}")
        for error in metadata.validation_errors:
            print(f"   - {error}")
    else:
        print("✅ No validation errors")
    
    return True

def test_configuration_updates():
    """Test runtime configuration updates"""
    print("\n🔄 Testing Configuration Updates...")
    
    config = get_config()
    
    # Test getting current value
    current_threshold = config.get('api_settings.suggestion_threshold', 5.0)
    print(f"✅ Current suggestion threshold: {current_threshold}")
    
    # Test updating value
    config.update_config('api_settings.suggestion_threshold', 7.0)
    new_threshold = config.get('api_settings.suggestion_threshold', 5.0)
    print(f"✅ Updated suggestion threshold: {new_threshold}")
    
    # Restore original value
    config.update_config('api_settings.suggestion_threshold', current_threshold)
    restored_threshold = config.get('api_settings.suggestion_threshold', 5.0)
    print(f"✅ Restored suggestion threshold: {restored_threshold}")
    
    return True

def run_comprehensive_test():
    """Run all configuration tests"""
    print("🚀 Starting Comprehensive Configuration Management Test\n")
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Mature Buck Integration", test_mature_buck_integration),
        ("Scoring Engine Integration", test_scoring_engine_integration),
        ("Distance Scorer Integration", test_distance_scorer_integration),
        ("Configuration Validation", test_configuration_validation),
        ("Configuration Updates", test_configuration_updates)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ {test_name}: FAILED - {e}")
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All configuration tests PASSED!")
        return True
    else:
        print("⚠️ Some configuration tests FAILED!")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
