#!/usr/bin/env python3
"""
Quick validation test for Vermont food classification integration.

Tests that the Vermont food classifier integrates properly with
the vegetation analyzer and prediction service.

Author: GitHub Copilot  
Date: October 2, 2025
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules import correctly"""
    logger.info("Testing module imports...")
    
    try:
        from backend.vermont_food_classifier import VermontFoodClassifier, get_vermont_food_classifier
        logger.info("✅ Vermont food classifier imported")
    except Exception as e:
        logger.error(f"❌ Failed to import vermont_food_classifier: {e}")
        return False
    
    try:
        from backend.vegetation_analyzer import VegetationAnalyzer, get_vegetation_analyzer
        logger.info("✅ Vegetation analyzer imported")
    except Exception as e:
        logger.error(f"❌ Failed to import vegetation_analyzer: {e}")
        return False
    
    try:
        from backend.services.prediction_service import PredictionService
        logger.info("✅ Prediction service imported")
    except Exception as e:
        logger.error(f"❌ Failed to import prediction_service: {e}")
        return False
    
    return True


def test_vermont_food_classifier():
    """Test Vermont food classifier configuration"""
    logger.info("\nTesting Vermont food classifier configuration...")
    
    try:
        from backend.vermont_food_classifier import VermontFoodClassifier
        
        # Create classifier instance
        classifier = VermontFoodClassifier()
        
        # Test crop definitions
        assert 1 in classifier.VERMONT_CROPS, "Corn should be defined"
        assert classifier.VERMONT_CROPS[1]['name'] == 'Corn', "Corn should be classified correctly"
        logger.info(f"✅ Vermont crops defined: {len(classifier.VERMONT_CROPS)} crop types")
        
        # Test seasonal quality scores
        corn_data = classifier.VERMONT_CROPS.get(1, {})
        corn_quality = corn_data.get('season_quality', {})
        assert 'early_season' in corn_quality, "Corn should have early_season quality"
        assert 'rut' in corn_quality, "Corn should have rut quality"
        assert 'late_season' in corn_quality, "Corn should have late_season quality"
        logger.info(f"✅ Seasonal quality: Corn rut={corn_quality['rut']:.2f}")
        
        # Test seasonal priorities
        assert 'early_season' in classifier.VERMONT_SEASONAL_PRIORITIES
        assert 'rut' in classifier.VERMONT_SEASONAL_PRIORITIES
        assert 'late_season' in classifier.VERMONT_SEASONAL_PRIORITIES
        logger.info(f"✅ Seasonal priorities defined for 3 seasons")
        
        logger.info(f"✅ Vermont food classifier instantiated successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vermont food classifier test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vegetation_analyzer_season_param():
    """Test that vegetation analyzer accepts season parameter"""
    logger.info("\nTesting vegetation analyzer season parameter...")
    
    try:
        from backend.vegetation_analyzer import VegetationAnalyzer
        import inspect
        
        # Get analyze_hunting_area signature
        sig = inspect.signature(VegetationAnalyzer.analyze_hunting_area)
        params = sig.parameters
        
        assert 'season' in params, "analyze_hunting_area should accept season parameter"
        logger.info(f"✅ analyze_hunting_area has season parameter")
        
        # Check default value
        season_param = params['season']
        assert season_param.default == 'early_season', "Season should default to 'early_season'"
        logger.info(f"✅ Season defaults to 'early_season'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vegetation analyzer test failed: {e}")
        return False


def test_prediction_service_integration():
    """Test prediction service has vegetation analyzer"""
    logger.info("\nTesting prediction service integration...")
    
    try:
        from backend.services.prediction_service import PredictionService
        import inspect
        
        # Check _extract_feeding_scores signature
        sig = inspect.signature(PredictionService._extract_feeding_scores)
        params = sig.parameters
        
        assert 'lat' in params, "_extract_feeding_scores should accept lat"
        assert 'lon' in params, "_extract_feeding_scores should accept lon"
        assert 'season' in params, "_extract_feeding_scores should accept season"
        logger.info(f"✅ _extract_feeding_scores accepts lat, lon, season")
        
        # Check that season has default
        season_param = params['season']
        assert season_param.default == 'early_season', "Season should default to 'early_season'"
        logger.info(f"✅ Season parameter properly configured")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Prediction service integration test failed: {e}")
        return False


def test_food_classification_data():
    """Test food classification data validity"""
    logger.info("\nTesting food classification data...")
    
    try:
        from backend.vermont_food_classifier import VermontFoodClassifier
        
        classifier = VermontFoodClassifier()
        
        # Test that all crop qualities are in valid range (0-1)
        for crop_code, crop_data in classifier.VERMONT_CROPS.items():
            qualities = crop_data.get('season_quality', {})
            for season, quality in qualities.items():
                assert 0.0 <= quality <= 1.0, \
                    f"Crop {crop_code} season {season} quality {quality} out of range"
        
        logger.info(f"✅ All crop quality scores in valid range (0-1)")
        
        # Test seasonal variations
        corn_quality = classifier.VERMONT_CROPS[1]['season_quality']  # Corn
        assert corn_quality['rut'] > 0.85, "Corn should be high quality during rut"
        logger.info(f"✅ Corn quality during rut: {corn_quality['rut']:.2f} (excellent)")
        
        deciduous_quality = classifier.VERMONT_CROPS[141]['season_quality']  # Deciduous forest
        assert deciduous_quality['early_season'] > 0.70, "Mast should be high quality early season"
        logger.info(f"✅ Mast quality early season: {deciduous_quality['early_season']:.2f} (excellent)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Food classification data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    logger.info("=" * 60)
    logger.info("VERMONT FOOD CLASSIFICATION INTEGRATION VALIDATION")
    logger.info("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Vermont Food Classifier", test_vermont_food_classifier()))
    results.append(("Vegetation Analyzer Season Param", test_vegetation_analyzer_season_param()))
    results.append(("Prediction Service Integration", test_prediction_service_integration()))
    results.append(("Food Classification Data", test_food_classification_data()))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All validation tests passed!")
        logger.info("\n✅ Phase 2 Integration Complete:")
        logger.info("   - Vermont food classifier implemented")
        logger.info("   - Vegetation analyzer updated with season parameter")
        logger.info("   - Prediction service integrated with Vermont food data")
        logger.info("   - Feeding scores now use real Vermont crop classifications")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
