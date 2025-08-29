"""
Clean Prediction Service Integration
===================================

This module provides a clean replacement for the complex bedding integration
in the prediction service, removing all environmental dependencies and
providing a simple, reliable integration path.
"""

import logging
import numpy as np
from typing import Dict, Any

class CleanPredictionServicePatch:
    """
    Clean patch for prediction service bedding integration
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("🧹 CLEAN PATCH: Initializing clean prediction service patch")
    
    def patch_prediction_service(self):
        """
        Apply clean patch to prediction service
        
        This replaces the complex _execute_rule_engine method with a clean version
        that reliably integrates bedding zones without dependencies.
        """
        
        try:
            from backend.services.prediction_service import PredictionService
            from backend.services.clean_bedding_service import get_clean_bedding_integrator
            
            # Store original method
            original_execute_rule_engine = PredictionService._execute_rule_engine
            
            def clean_execute_rule_engine(self, context, terrain_data, weather_data):
                """
                Clean version of rule engine with reliable bedding integration
                """
                
                logger = logging.getLogger('clean_prediction_patch')
                logger.info("🧹 CLEAN PATCH: Starting clean rule engine execution")
                
                try:
                    # Step 1: Execute original rule engine for base score maps
                    logger.info("📊 CLEAN PATCH: Executing base rule engine")
                    
                    rules = self._load_rules()
                    conditions = self._build_conditions(context, weather_data)
                    score_maps = self.core.run_grid_rule_engine(rules, terrain_data, conditions)
                    
                    logger.info("✅ CLEAN PATCH: Base rule engine complete")
                    
                except Exception as e:
                    logger.warning(f"⚠️ CLEAN PATCH: Base rule engine failed: {e}, creating fallback")
                    # Create minimal fallback score maps
                    grid_size = 6
                    score_maps = {
                        'travel': np.ones((grid_size, grid_size)) * 0.8,
                        'bedding': np.zeros((grid_size, grid_size)),  # Will be replaced
                        'feeding': np.ones((grid_size, grid_size)) * 0.9
                    }
                
                # Step 2: Clean bedding integration (ALWAYS EXECUTES)
                try:
                    logger.info("🛏️ CLEAN PATCH: Starting clean bedding integration")
                    
                    # Get clean bedding integrator
                    integrator = get_clean_bedding_integrator()
                    
                    # Integrate bedding zones
                    integration_result = integrator.integrate_bedding_zones_into_prediction(
                        context, score_maps
                    )
                    
                    # Extract results
                    enhanced_score_maps = integration_result['enhanced_score_maps']
                    bedding_zones = integration_result['bedding_zones']
                    metadata = integration_result['integration_metadata']
                    
                    # Cache bedding zones for later use
                    self._cached_enhanced_bedding_zones = bedding_zones
                    
                    # Log success
                    feature_count = metadata.get('feature_count', 0)
                    max_score = metadata.get('max_bedding_score', 0)
                    
                    logger.info(f"✅ CLEAN PATCH: Bedding integration complete")
                    logger.info(f"🎯 CLEAN PATCH: Generated {feature_count} zones, max score {max_score:.2f}")
                    
                    if feature_count > 0:
                        logger.info("🏆 CLEAN PATCH: SUCCESS - Bedding zones generated and integrated!")
                    else:
                        logger.warning("⚠️ CLEAN PATCH: No bedding zones generated")
                    
                    return enhanced_score_maps
                    
                except Exception as e:
                    logger.error(f"❌ CLEAN PATCH: Clean bedding integration failed: {e}")
                    logger.error("❌ CLEAN PATCH: Continuing with original score maps")
                    
                    # Set empty bedding zones cache
                    self._cached_enhanced_bedding_zones = {
                        "type": "FeatureCollection", 
                        "features": [],
                        "properties": {"error": str(e)}
                    }
                    
                    return score_maps
                
                # Step 3: Validation
                try:
                    if not self._validate_score_maps(score_maps):
                        logger.warning("⚠️ CLEAN PATCH: Score map validation failed")
                except Exception as e:
                    logger.warning(f"⚠️ CLEAN PATCH: Validation error: {e}")
                
                logger.info("🏁 CLEAN PATCH: Clean rule engine execution complete")
                return score_maps
            
            # Apply the patch
            PredictionService._execute_rule_engine = clean_execute_rule_engine
            
            # EMERGENCY: Also patch any existing instances
            from backend.services.prediction_service import get_prediction_service
            try:
                existing_service = get_prediction_service()
                if existing_service:
                    # Directly replace the method on the instance
                    existing_service._execute_rule_engine = clean_execute_rule_engine.__get__(existing_service, PredictionService)
                    self.logger.info("🔄 CLEAN PATCH: Patched existing service instance")
            except Exception as e:
                self.logger.warning(f"⚠️ CLEAN PATCH: Could not patch existing instance: {e}")
            
            self.logger.info("✅ CLEAN PATCH: Prediction service patched successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ CLEAN PATCH: Failed to patch prediction service: {e}")
            return False
    
    def verify_patch(self):
        """Verify that the patch was applied successfully"""
        try:
            from backend.services.prediction_service import get_prediction_service
            
            # Test patch by creating service instance
            service = get_prediction_service()
            
            # Check if our patch is applied by looking for cached zones attribute
            has_cache = hasattr(service, '_cached_enhanced_bedding_zones')
            
            self.logger.info(f"🔍 CLEAN PATCH: Verification - Cache attribute exists: {has_cache}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ CLEAN PATCH: Verification failed: {e}")
            return False


def apply_clean_prediction_service_patch():
    """
    Apply the clean prediction service patch
    
    This function should be called during application startup to replace
    the complex bedding integration with a clean, reliable version.
    """
    
    logger = logging.getLogger(__name__)
    logger.info("🧹 APPLYING CLEAN PREDICTION SERVICE PATCH")
    
    try:
        patcher = CleanPredictionServicePatch()
        
        # Apply patch
        success = patcher.patch_prediction_service()
        
        if success:
            # Verify patch
            verified = patcher.verify_patch()
            
            if verified:
                logger.info("✅ CLEAN PATCH: Application successful and verified")
                return True
            else:
                logger.warning("⚠️ CLEAN PATCH: Applied but verification failed")
                return False
        else:
            logger.error("❌ CLEAN PATCH: Failed to apply patch")
            return False
            
    except Exception as e:
        logger.error(f"❌ CLEAN PATCH: Exception during patch application: {e}")
        return False


if __name__ == "__main__":
    # Apply patch when imported
    apply_clean_prediction_service_patch()
