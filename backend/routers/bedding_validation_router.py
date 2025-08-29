#!/usr/bin/env python3
"""
Production Bedding Zone Validation API
======================================

Enhanced API endpoint for validating bedding zone generation in production
with detailed logging and frontend integration support.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import json

# Configure logging
logger = logging.getLogger(__name__)

# Create router
bedding_validation_router = APIRouter(prefix="/api/bedding", tags=["bedding-validation"])

@bedding_validation_router.get("/validate/{lat}/{lon}")
async def validate_bedding_zones(
    lat: float,
    lon: float,
    season: str = "fall",
    include_metadata: bool = True,
    debug_mode: bool = False
) -> Dict[str, Any]:
    """
    Validate bedding zone generation for specific coordinates
    
    Args:
        lat: Latitude
        lon: Longitude
        season: Hunting season
        include_metadata: Include production metadata
        debug_mode: Enable detailed debug logging
        
    Returns:
        Comprehensive bedding zone validation results
    """
    
    try:
        # Import here to avoid circular dependencies
        import sys
        import os
        backend_path = os.path.join(os.path.dirname(__file__), '..', '..')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
            
        from services.prediction_service import PredictionService, PredictionContext
        
        logger.info(f"🔍 Validating bedding zones for {lat:.6f}, {lon:.6f}")
        
        # Initialize prediction service
        service = PredictionService()
        
        # Verify bedding fix is loaded
        if not hasattr(service, 'bedding_fix') or not service.bedding_fix:
            raise HTTPException(
                status_code=500,
                detail="Bedding fix not loaded in prediction service"
            )
        
        # Create prediction context
        context = PredictionContext(
            lat=lat,
            lon=lon,
            date_time=datetime.now(),
            season=season,
            fast_mode=False  # Full analysis for validation
        )
        
        # Generate bedding zones using the fix
        bedding_zones = service.bedding_fix.generate_fixed_bedding_zones_for_prediction_service(
            lat, lon, {}, {}, {}
        )
        
        # Extract and analyze results
        features = bedding_zones.get('features', [])
        
        if not features:
            logger.warning(f"No bedding zones generated for {lat:.6f}, {lon:.6f}")
            
        # Calculate validation metrics
        validation_results = {
            'location': {
                'latitude': lat,
                'longitude': lon,
                'season': season
            },
            'bedding_zones': {
                'count': len(features),
                'features': features
            },
            'validation_status': 'PASS' if len(features) >= 2 else 'FAIL',
            'timestamp': datetime.now().isoformat()
        }
        
        if features:
            # Calculate detailed metrics
            suitabilities = [f.get('properties', {}).get('suitability_score', 0) for f in features]
            avg_suitability = sum(suitabilities) / len(suitabilities)
            
            # Calculate coordinate variations
            coordinate_distances = []
            for feature in features:
                coords = feature.get('geometry', {}).get('coordinates', [lat, lon])
                import math
                lat_diff = coords[1] - lat
                lon_diff = coords[0] - lon
                distance_m = math.sqrt((lat_diff * 111000)**2 + (lon_diff * 111000 * math.cos(math.radians(lat)))**2)
                coordinate_distances.append(distance_m)
            
            max_distance = max(coordinate_distances) if coordinate_distances else 0
            min_distance = min(coordinate_distances) if coordinate_distances else 0
            
            validation_results['metrics'] = {
                'average_suitability': round(avg_suitability, 1),
                'suitability_range': [min(suitabilities), max(suitabilities)],
                'coordinate_variation': {
                    'min_distance_m': round(min_distance, 0),
                    'max_distance_m': round(max_distance, 0),
                    'range_description': f"{min_distance:.0f}m-{max_distance:.0f}m"
                },
                'terrain_assessment': {
                    'compatibility': 'EXCELLENT' if avg_suitability > 70 else 'GOOD' if avg_suitability > 50 else 'NEEDS_IMPROVEMENT',
                    'vermont_optimized': True
                }
            }
            
            # Validate against known issues
            validation_results['issue_checks'] = {
                'coordinate_variation_acceptable': max_distance < 300,  # < 300m variation
                'suitability_realistic': avg_suitability > 60,  # > 60% for Vermont
                'zone_count_adequate': len(features) >= 2,  # At least 2 zones
                'scoring_bug_resolved': avg_suitability > 43.1  # Better than original 43.1%
            }
            
            # Overall validation status
            all_checks_pass = all(validation_results['issue_checks'].values())
            validation_results['validation_status'] = 'PASS' if all_checks_pass else 'PARTIAL'
            
        if include_metadata:
            validation_results['production_metadata'] = {
                'algorithm_version': 'fixed_v1.0',
                'integration_status': 'production_validated',
                'api_endpoint': 'bedding_validation',
                'service_instance': str(id(service)),
                'bedding_fix_loaded': bool(service.bedding_fix),
                'debug_mode': debug_mode
            }
        
        if debug_mode:
            validation_results['debug_info'] = {
                'service_attributes': [attr for attr in dir(service) if 'bedding' in attr.lower()],
                'bedding_fix_type': type(service.bedding_fix).__name__ if service.bedding_fix else None,
                'prediction_context': {
                    'lat': context.lat,
                    'lon': context.lon,
                    'season': context.season,
                    'fast_mode': context.fast_mode
                }
            }
        
        logger.info(f"✅ Bedding zone validation complete: {validation_results['validation_status']}")
        logger.info(f"   Zones: {len(features)}, Avg Suitability: {validation_results.get('metrics', {}).get('average_suitability', 'N/A')}%")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"❌ Bedding zone validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Bedding zone validation failed: {str(e)}"
        )

@bedding_validation_router.get("/status")
async def get_bedding_system_status() -> Dict[str, Any]:
    """Get overall bedding zone system status"""
    
    try:
        import sys
        import os
        backend_path = os.path.join(os.path.dirname(__file__), '..', '..')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
            
        from services.prediction_service import PredictionService
        
        service = PredictionService()
        
        status = {
            'system_status': 'OPERATIONAL',
            'bedding_fix_loaded': bool(hasattr(service, 'bedding_fix') and service.bedding_fix),
            'enhanced_predictor_available': bool(hasattr(service, 'enhanced_bedding_predictor') and service.enhanced_bedding_predictor),
            'timestamp': datetime.now().isoformat(),
            'service_info': {
                'service_id': str(id(service)),
                'bedding_components': [attr for attr in dir(service) if 'bedding' in attr.lower()]
            }
        }
        
        # Test basic functionality
        if status['bedding_fix_loaded']:
            try:
                test_zones = service.bedding_fix.generate_fixed_bedding_zones_for_prediction_service(
                    43.3146, -73.2178, {}, {}, {}
                )
                status['functionality_test'] = {
                    'test_passed': len(test_zones.get('features', [])) > 0,
                    'test_location': 'Tinmouth, VT',
                    'zones_generated': len(test_zones.get('features', []))
                }
            except Exception as e:
                status['functionality_test'] = {
                    'test_passed': False,
                    'error': str(e)
                }
        
        return status
        
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        return {
            'system_status': 'ERROR',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
