#!/usr/bin/env python3
"""
Production Bedding Integration Test
===================================

Validates that the production bedding zone fix is properly integrated into
the prediction service and generating correct bedding zones.

This test:
1. Initializes the prediction service with bedding fix
2. Tests Tinmouth, VT coordinates (43.3146, -73.2178)
3. Validates bedding zone generation and suitability scores
4. Confirms the 21.5% scoring discrepancy is fixed
"""

import sys
import os
import json
import logging
from datetime import datetime

# Add backend to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('production_bedding_integration_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_production_bedding_integration():
    """Test production bedding zone integration"""
    
    logger.info("Starting Production Bedding Zone Integration Test")
    logger.info("=" * 80)
    
    try:
        # Import prediction service
        from services.prediction_service import PredictionService, PredictionContext
        
        # Test coordinates - Tinmouth, VT (known issue location)
        test_lat = 43.3146
        test_lon = -73.2178
        
        logger.info(f"Testing coordinates: {test_lat}, {test_lon} (Tinmouth, VT)")
        
        # Initialize prediction service
        logger.info("Initializing PredictionService with bedding fix...")
        prediction_service = PredictionService()
        
        # Verify bedding fix is loaded
        if hasattr(prediction_service, 'bedding_fix') and prediction_service.bedding_fix:
            logger.info("Bedding fix successfully initialized")
        else:
            logger.warning("Bedding fix not initialized - may use fallback algorithm")
        
        # Create prediction context
        from datetime import datetime
        context = PredictionContext(
            lat=test_lat,
            lon=test_lon,
            date_time=datetime.now(),
            season="fall",
            fast_mode=False
        )
        
        # Generate prediction
        logger.info("Generating prediction with bedding zone integration...")
        prediction_result = prediction_service.predict(context)
        
        # Extract bedding zone information
        bedding_zones = prediction_result.get('bedding_zones', {})
        bedding_features = bedding_zones.get('features', [])
        
        # Analysis results
        logger.info("\n" + "=" * 60)
        logger.info("PRODUCTION INTEGRATION RESULTS")
        logger.info("=" * 60)
        
        logger.info(f"Bedding Zones Generated: {len(bedding_features)}")
        
        if bedding_features:
            # Calculate average suitability from bedding zones
            suitabilities = []
            for i, feature in enumerate(bedding_features):
                props = feature.get('properties', {})
                suitability = props.get('suitability_score', 0)
                suitabilities.append(suitability)
                
                coords = feature.get('geometry', {}).get('coordinates', [0, 0])
                logger.info(f"   Zone {i+1}: {suitability:.1f}% suitability at {coords[1]:.6f}, {coords[0]:.6f}")
            
            avg_suitability = sum(suitabilities) / len(suitabilities)
            logger.info(f"Average Bedding Suitability: {avg_suitability:.1f}%")
            
            # Compare with expected fix results
            expected_suitability = 75.3  # From production fix validation
            expected_zones = 3  # From production fix validation
            
            # Validation checks
            logger.info("\nVALIDATION CHECKS")
            logger.info("-" * 40)
            
            # Check zone count
            if len(bedding_features) >= expected_zones:
                logger.info(f"Zone Count: {len(bedding_features)} zones (Expected: >={expected_zones}) - PASS")
            else:
                logger.warning(f"Zone Count: {len(bedding_features)} zones (Expected: >={expected_zones}) - FAIL")
            
            # Check suitability score
            suitability_tolerance = 10.0  # Allow 10% variance
            if abs(avg_suitability - expected_suitability) <= suitability_tolerance:
                logger.info(f"Suitability Score: {avg_suitability:.1f}% (Expected: ~{expected_suitability}% +/-{suitability_tolerance}%) - PASS")
            else:
                logger.warning(f"Suitability Score: {avg_suitability:.1f}% (Expected: ~{expected_suitability}% +/-{suitability_tolerance}%) - FAIL")
            
            # Check if original issue is fixed
            original_score = 43.1  # Original problematic score
            if avg_suitability > original_score + 15:  # Significant improvement
                logger.info(f"Issue Fixed: {avg_suitability:.1f}% >> {original_score}% (21.5% discrepancy resolved) - PASS")
            else:
                logger.warning(f"Issue Persists: {avg_suitability:.1f}% vs {original_score}% (improvement insufficient) - FAIL")
                
        else:
            logger.error("No bedding zones generated - integration failed!")
            return False
        
        # Additional analysis
        logger.info("\nADDITIONAL ANALYSIS")
        logger.info("-" * 40)
        
        # Check prediction structure
        prediction_keys = list(prediction_result.keys())
        logger.info(f"Prediction Keys: {prediction_keys}")
        
        # Check if enhanced zones are cached
        if hasattr(prediction_service, '_cached_enhanced_bedding_zones') and prediction_service._cached_enhanced_bedding_zones:
            logger.info("Enhanced bedding zones properly cached")
        else:
            logger.warning("Enhanced bedding zones not cached")
        
        # Performance metrics
        response_time = prediction_result.get('metadata', {}).get('processing_time_seconds', 'unknown')
        logger.info(f"Response Time: {response_time}s")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        
        if len(bedding_features) >= 3 and avg_suitability > 65:
            logger.info("INTEGRATION SUCCESSFUL")
            logger.info("   - Bedding zones are being generated")
            logger.info("   - Suitability scores are realistic")
            logger.info("   - Original algorithm issue appears fixed")
            
            # Save detailed results
            test_results = {
                'timestamp': datetime.now().isoformat(),
                'test_coordinates': {'lat': test_lat, 'lon': test_lon},
                'bedding_zones_count': len(bedding_features),
                'average_suitability': avg_suitability,
                'bedding_zones': bedding_zones,
                'validation_status': 'PASSED',
                'integration_status': 'SUCCESSFUL'
            }
            
            with open('production_bedding_integration_results.json', 'w') as f:
                json.dump(test_results, f, indent=2)
                
            logger.info("Results saved to: production_bedding_integration_results.json")
            return True
            
        else:
            logger.error("INTEGRATION FAILED")
            logger.error("   - Insufficient bedding zones or low suitability")
            logger.error("   - Original algorithm issue may persist")
            return False
            
    except Exception as e:
        logger.error(f"Integration test failed with error: {e}")
        import traceback
        logger.error(f"Stack trace:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_production_bedding_integration()
    exit_code = 0 if success else 1
    
    print(f"\n{'='*60}")
    print(f"Production Bedding Integration Test: {'PASSED' if success else 'FAILED'}")
    print(f"{'='*60}")
    
    sys.exit(exit_code)
