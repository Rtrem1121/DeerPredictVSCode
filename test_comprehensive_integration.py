#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite

This script runs a complete set of integration tests across all major system components.
"""

import sys
import os
from pathlib import Path
import logging
from typing import Dict, Any, List
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config_manager import get_config
from backend.mature_buck_predictor import get_mature_buck_predictor
from backend.scoring_engine import get_scoring_engine
from backend.terrain_analyzer import get_terrain_analyzer
from backend.distance_scorer import get_distance_scorer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_end_to_end_prediction():
    """Test complete prediction flow from input to output"""
    logger.info("🔄 Testing End-to-End Prediction Flow")
    
    # Initialize all components
    config = get_config()
    predictor = get_mature_buck_predictor()
    scorer = get_scoring_engine()
    terrain = get_terrain_analyzer()
    
    # Test location
    test_data = {
        'lat': 44.2601,
        'lon': -72.5806,
        'season': 'rut',
        'date_time': '2024-11-15T08:00:00',
        'weather_conditions': ['clear', 'calm']
    }
    
    try:
        # 1. Terrain Analysis
        logger.info("📊 Running terrain analysis...")
        terrain_results = terrain.analyze_terrain_features(test_data['lat'], test_data['lon'])
        assert terrain_results is not None
        logger.info(f"✅ Terrain analysis complete - {len(terrain_results.get('detected_features', []))} features detected")
        
        # 2. Scoring
        logger.info("🎯 Calculating scores...")
        scores = scorer.calculate_scores(terrain_results)
        assert scores is not None
        logger.info(f"✅ Scoring complete - Overall: {scores.get('overall_score', 0):.1f}")
        
        # 3. Mature Buck Prediction
        logger.info("🦌 Generating mature buck prediction...")
        prediction = predictor.predict(
            terrain_results=terrain_results,
            scores=scores,
            season=test_data['season'],
            date_time=test_data['date_time'],
            weather_conditions=test_data['weather_conditions']
        )
        assert prediction is not None
        logger.info("✅ Prediction complete")
        
        # Validate prediction components
        required_components = [
            'stand_recommendations',
            'travel_corridors',
            'bedding_zones',
            'feeding_areas',
            'mature_buck_analysis'
        ]
        
        for component in required_components:
            assert component in prediction, f"Missing {component} in prediction"
        
        # Validate stand recommendations
        stands = prediction['stand_recommendations']
        assert len(stands) > 0, "No stand recommendations generated"
        logger.info(f"✅ Generated {len(stands)} stand recommendations")
        
        # 4. Configuration Integration
        logger.info("⚙️ Validating configuration integration...")
        config_values = {
            'seasonal_weights': config.get_seasonal_weights('rut'),
            'distance_params': config.get_distance_parameters(),
            'terrain_weights': config.get_terrain_weights()
        }
        
        for key, value in config_values.items():
            assert value is not None and len(value) > 0, f"Missing {key} configuration"
        logger.info("✅ Configuration integration verified")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {str(e)}")
        raise

def test_cross_component_data_flow():
    """Test data flow and consistency between components"""
    logger.info("\n🔄 Testing Cross-Component Data Flow")
    
    predictor = get_mature_buck_predictor()
    scorer = get_scoring_engine()
    terrain = get_terrain_analyzer()
    
    # Test location
    test_lat, test_lon = 44.2601, -72.5806
    
    try:
        # 1. Test terrain to scoring flow
        terrain_data = terrain.analyze_terrain_features(test_lat, test_lon)
        scorer_input = terrain_data.get('elevation_grid')
        assert scorer_input is not None, "Missing elevation data for scorer"
        
        scores = scorer.calculate_terrain_scores(scorer_input)
        assert scores is not None, "Scoring failed"
        logger.info("✅ Terrain → Scoring data flow verified")
        
        # 2. Test scoring to prediction flow
        pred_input = {
            'terrain_data': terrain_data,
            'scores': scores,
            'season': 'rut'
        }
        prediction = predictor.predict(**pred_input)
        assert prediction is not None, "Prediction failed"
        logger.info("✅ Scoring → Prediction data flow verified")
        
        # 3. Validate data consistency
        terrain_features = terrain_data.get('detected_features', [])
        pred_features = prediction.get('terrain_features', [])
        assert len(terrain_features) == len(pred_features), "Feature count mismatch"
        logger.info("✅ Data consistency verified")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data flow test failed: {str(e)}")
        raise

def test_error_handling_integration():
    """Test error handling across component boundaries"""
    logger.info("\n🛡️ Testing Error Handling Integration")
    
    predictor = get_mature_buck_predictor()
    scorer = get_scoring_engine()
    terrain = get_terrain_analyzer()
    
    test_cases = [
        {
            'name': "Invalid coordinates",
            'lat': 999,
            'lon': 999
        },
        {
            'name': "Missing terrain data",
            'lat': None,
            'lon': None
        },
        {
            'name': "Invalid season",
            'lat': 44.2601,
            'lon': -72.5806,
            'season': 'invalid_season'
        }
    ]
    
    results = []
    for test in test_cases:
        logger.info(f"\nTesting: {test['name']}")
        try:
            # Attempt prediction with invalid data
            terrain_data = terrain.analyze_terrain_features(test['lat'], test['lon'])
            scores = scorer.calculate_terrain_scores(terrain_data)
            prediction = predictor.predict(
                terrain_data=terrain_data,
                scores=scores,
                season=test.get('season', 'rut')
            )
            results.append({
                'test': test['name'],
                'success': False,
                'message': "Failed to catch invalid input"
            })
        except Exception as e:
            results.append({
                'test': test['name'],
                'success': True,
                'message': str(e)
            })
            logger.info(f"✅ Expected error caught: {str(e)}")
    
    # Validate results
    failures = [r for r in results if not r['success']]
    if failures:
        for f in failures:
            logger.error(f"❌ {f['test']}: {f['message']}")
        raise AssertionError("Error handling tests failed")
    
    logger.info("✅ All error handling tests passed")
    return True

def main():
    """Run all integration tests"""
    print("\n🧪 RUNNING COMPREHENSIVE INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        ("End-to-End Prediction", test_end_to_end_prediction),
        ("Cross-Component Data Flow", test_cross_component_data_flow),
        ("Error Handling Integration", test_error_handling_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ {test_name}: FAILED - {str(e)}")
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
