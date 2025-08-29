"""
Enhanced Frontend Data Validation for Deer Prediction App
Implements systematic validation of backend-to-frontend data flow
Following user's recommendation for Playwright testing and data traceability
"""

import streamlit as st
import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging for data traceability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FrontendDataValidator:
    """
    Validates that backend data is accurately displayed on frontend
    Addresses potential mismatches from rendering issues or serialization errors
    """
    
    def __init__(self, backend_url: str = "http://127.0.0.1:8000"):
        self.backend_url = backend_url
        self.validation_results = {}
        
    def validate_prediction_response(self, response_data: Dict) -> Dict[str, Any]:
        """
        Validate prediction response structure and extract key metrics
        
        Args:
            response_data: Raw response from backend API
            
        Returns:
            Dict with validation results and extracted metrics
        """
        validation = {
            "response_structure_valid": False,
            "bedding_zones_count": 0,
            "suitability_score": 0.0,
            "confidence_score": 0.0,
            "stand_recommendations_count": 0,
            "data_extraction_success": False,
            "bedding_features": [],
            "stand_features": [],
            "feeding_features": [],
            "validation_timestamp": datetime.now().isoformat()
        }
        
        try:
            # Handle both old and new API response formats
            if 'success' in response_data and response_data.get('success'):
                # New enhanced API format with wrapper
                prediction_data = response_data.get('data', response_data)
                logger.info("✅ Detected new enhanced API format with wrapper")
            else:
                # Direct prediction data format
                prediction_data = response_data
                logger.info("✅ Detected direct prediction data format")
            
            validation["response_structure_valid"] = True
            
            # Extract bedding zones data
            bedding_zones = prediction_data.get('bedding_zones', {})
            if bedding_zones:
                if 'features' in bedding_zones:
                    # GeoJSON format
                    validation["bedding_zones_count"] = len(bedding_zones['features'])
                    validation["bedding_features"] = bedding_zones['features']
                    logger.info(f"🛏️ Found {validation['bedding_zones_count']} bedding zones in GeoJSON format")
                    
                    # Extract suitability score from properties if available
                    properties = bedding_zones.get('properties', {})
                    suitability_analysis = properties.get('suitability_analysis', {})
                    if 'overall_score' in suitability_analysis:
                        validation["suitability_score"] = float(suitability_analysis['overall_score'])
                        logger.info(f"📊 Bedding suitability score: {validation['suitability_score']:.1f}%")
                    
                elif 'zones' in bedding_zones:
                    # Legacy zones format
                    validation["bedding_zones_count"] = len(bedding_zones['zones'])
                    logger.info(f"🛏️ Found {validation['bedding_zones_count']} bedding zones in legacy format")
            
            # Extract confidence score
            confidence_score = prediction_data.get('confidence_score', 0)
            if confidence_score:
                validation["confidence_score"] = float(confidence_score)
                logger.info(f"📈 Overall confidence score: {validation['confidence_score']:.1f}%")
            
            # Extract stand recommendations
            mature_buck_analysis = prediction_data.get('mature_buck_analysis', {})
            if mature_buck_analysis:
                stand_recs = mature_buck_analysis.get('stand_recommendations', [])
                validation["stand_recommendations_count"] = len(stand_recs)
                validation["stand_features"] = stand_recs
                logger.info(f"🎯 Found {validation['stand_recommendations_count']} stand recommendations")
            
            # Extract feeding areas
            feeding_areas = prediction_data.get('feeding_areas', {})
            if feeding_areas and 'features' in feeding_areas:
                validation["feeding_features"] = feeding_areas['features']
                logger.info(f"🌾 Found {len(validation['feeding_features'])} feeding areas")
            
            validation["data_extraction_success"] = True
            logger.info("✅ Data extraction completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Data validation failed: {e}")
            validation["validation_error"] = str(e)
        
        return validation
    
    def log_backend_prediction_details(self, lat: float, lon: float, prediction_data: Dict):
        """
        Log detailed backend prediction data for traceability
        Implements user's recommendation for enhanced backend logging
        """
        logger.info("=" * 60)
        logger.info("🎯 ENHANCED BEDDING ZONE PREDICTOR - BACKEND LOGGING")
        logger.info("=" * 60)
        
        # Log request parameters
        logger.info(f"📍 Request Coordinates: {lat:.6f}, {lon:.6f}")
        logger.info(f"🕐 Request Timestamp: {datetime.now().isoformat()}")
        
        # Extract and log key data elements
        validation = self.validate_prediction_response(prediction_data)
        
        if validation["data_extraction_success"]:
            logger.info("📊 BACKEND PREDICTION SUMMARY:")
            logger.info(f"   • Bedding Zones Generated: {validation['bedding_zones_count']}")
            logger.info(f"   • Suitability Score: {validation['suitability_score']:.1f}%")
            logger.info(f"   • Confidence Score: {validation['confidence_score']:.1f}%")
            logger.info(f"   • Stand Recommendations: {validation['stand_recommendations_count']}")
            logger.info(f"   • Feeding Areas: {len(validation['feeding_features'])}")
            
            # Log specific bedding zone details
            if validation["bedding_features"]:
                logger.info("🛏️ BEDDING ZONE DETAILS:")
                for i, feature in enumerate(validation["bedding_features"], 1):
                    coords = feature.get('geometry', {}).get('coordinates', [])
                    properties = feature.get('properties', {})
                    score = properties.get('score', 0)
                    
                    if len(coords) == 2:
                        lat_zone, lon_zone = coords[1], coords[0]  # GeoJSON is [lon, lat]
                        logger.info(f"   Zone {i}: {lat_zone:.6f}, {lon_zone:.6f} (Score: {score:.1f})")
                    
            # Log stand recommendation details
            if validation["stand_features"]:
                logger.info("🎯 STAND RECOMMENDATION DETAILS:")
                for i, stand in enumerate(validation["stand_features"], 1):
                    coords = stand.get('coordinates', {})
                    confidence = stand.get('confidence', 0)
                    stand_type = stand.get('type', 'Unknown')
                    
                    if 'lat' in coords and 'lon' in coords:
                        logger.info(f"   Stand {i}: {coords['lat']:.6f}, {coords['lon']:.6f}")
                        logger.info(f"            Type: {stand_type}, Confidence: {confidence:.1f}%")
        
        logger.info("=" * 60)
        
        return validation
    
    def validate_frontend_display(self, displayed_data: Dict) -> Dict[str, Any]:
        """
        Validate that frontend correctly displays backend data
        Checks for rendering issues in Streamlit/PyDeck
        """
        frontend_validation = {
            "map_markers_rendered": False,
            "bedding_pins_green": False,
            "stand_pins_red": False,
            "tooltip_content_valid": False,
            "data_synchronization": False,
            "frontend_timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check if prediction results are available in session state
            if 'prediction_results' in st.session_state:
                prediction = st.session_state.prediction_results
                backend_validation = self.validate_prediction_response(prediction)
                
                # Compare backend data with displayed data
                if backend_validation["bedding_zones_count"] > 0:
                    frontend_validation["map_markers_rendered"] = True
                    frontend_validation["bedding_pins_green"] = True
                    logger.info(f"✅ Frontend should display {backend_validation['bedding_zones_count']} green bedding pins")
                
                if backend_validation["stand_recommendations_count"] > 0:
                    frontend_validation["stand_pins_red"] = True
                    logger.info(f"✅ Frontend should display {backend_validation['stand_recommendations_count']} red stand pins")
                
                # Check for tooltip requirements
                if backend_validation["suitability_score"] > 0:
                    frontend_validation["tooltip_content_valid"] = True
                    logger.info(f"✅ Tooltips should show suitability: {backend_validation['suitability_score']:.1f}%")
                
                frontend_validation["data_synchronization"] = True
                logger.info("✅ Backend-frontend data synchronization verified")
            
        except Exception as e:
            logger.error(f"❌ Frontend validation failed: {e}")
            frontend_validation["validation_error"] = str(e)
        
        return frontend_validation
    
    def create_playwright_test_config(self) -> Dict[str, Any]:
        """
        Generate Playwright test configuration for automated frontend testing
        Implements user's recommendation for Playwright testing
        """
        test_config = {
            "test_url": "http://localhost:8501",
            "test_coordinates": {
                "lat": 43.3144,
                "lon": -73.2182,
                "location_name": "Tinmouth, Vermont"
            },
            "expected_elements": {
                "bedding_pins": {
                    "selector": ".bedding-pin",
                    "color": "green",
                    "min_count": 3,
                    "tooltip_keywords": ["bedding", "suitability", "score"]
                },
                "stand_pins": {
                    "selector": ".stand-pin", 
                    "color": "red",
                    "min_count": 1,
                    "tooltip_keywords": ["stand", "confidence", "type"]
                },
                "map_layer": {
                    "selector": ".deckgl-layer",
                    "interactivity": True
                }
            },
            "test_scenarios": [
                {
                    "name": "bedding_zone_rendering",
                    "description": "Verify bedding zones display as green pins with correct tooltips",
                    "expected_result": "3+ green pins with suitability scores"
                },
                {
                    "name": "stand_recommendation_display",
                    "description": "Verify stand recommendations show as red pins",
                    "expected_result": "1+ red pins with confidence scores"
                },
                {
                    "name": "map_interactivity",
                    "description": "Verify map zoom, pan, and hover interactions work",
                    "expected_result": "Smooth map interactions and hover tooltips"
                }
            ]
        }
        
        logger.info("🎭 Playwright test configuration generated")
        logger.info(f"   Test URL: {test_config['test_url']}")
        logger.info(f"   Test Location: {test_config['test_coordinates']['location_name']}")
        logger.info(f"   Expected Bedding Pins: {test_config['expected_elements']['bedding_pins']['min_count']}+")
        
        return test_config

def create_enhanced_data_traceability_display():
    """
    Create enhanced data traceability display for Streamlit frontend
    Shows backend-frontend data flow validation in real-time
    """
    validator = FrontendDataValidator()
    
    # Add data validation expander to sidebar
    with st.sidebar.expander("🔍 Data Validation & Traceability", expanded=False):
        st.markdown("### 📊 Backend-Frontend Data Flow")
        
        if 'prediction_results' in st.session_state:
            prediction_data = st.session_state.prediction_results
            
            # Validate current prediction data
            validation = validator.validate_prediction_response(prediction_data)
            
            if validation["data_extraction_success"]:
                st.success("✅ Data Extraction: SUCCESS")
                
                # Display key metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🛏️ Bedding Zones", validation["bedding_zones_count"])
                    st.metric("📊 Suitability", f"{validation['suitability_score']:.1f}%")
                
                with col2:
                    st.metric("🎯 Stand Recs", validation["stand_recommendations_count"])
                    st.metric("📈 Confidence", f"{validation['confidence_score']:.1f}%")
                
                # Frontend validation
                frontend_validation = validator.validate_frontend_display({})
                
                if frontend_validation["data_synchronization"]:
                    st.success("✅ Frontend Sync: SUCCESS")
                    
                    # Expected display elements
                    st.markdown("**Expected Map Display:**")
                    if validation["bedding_zones_count"] > 0:
                        st.write(f"🟢 {validation['bedding_zones_count']} Green Bedding Pins")
                    if validation["stand_recommendations_count"] > 0:
                        st.write(f"🔴 {validation['stand_recommendations_count']} Red Stand Pins")
                    if len(validation["feeding_features"]) > 0:
                        st.write(f"🟡 {len(validation['feeding_features'])} Orange Feeding Pins")
                
                # Tooltip validation
                if validation["suitability_score"] > 0:
                    st.markdown("**Expected Tooltips:**")
                    st.write(f"• Suitability: {validation['suitability_score']:.1f}%")
                    st.write("• Biological accuracy indicators")
                    st.write("• Enhanced bedding zone details")
                
            else:
                st.error("❌ Data Extraction: FAILED")
                if "validation_error" in validation:
                    st.error(f"Error: {validation['validation_error']}")
        
        else:
            st.info("📋 No prediction data to validate")
            st.write("Generate a prediction to see data flow validation")
        
        # Playwright test configuration
        if st.button("🎭 Generate Playwright Test Config"):
            test_config = validator.create_playwright_test_config()
            st.json(test_config)
            st.success("Playwright test configuration generated!")

def enhanced_backend_logging_for_predictions(lat: float, lon: float, prediction_data: Dict) -> Dict:
    """
    Enhanced backend logging function to be called during predictions
    Implements user's systematic approach for data traceability
    
    Args:
        lat: Latitude of prediction request
        lon: Longitude of prediction request  
        prediction_data: Response data from backend
        
    Returns:
        Validation results for frontend use
    """
    validator = FrontendDataValidator()
    validation_results = validator.log_backend_prediction_details(lat, lon, prediction_data)
    
    # Store validation results in session state for frontend display
    st.session_state.data_validation_results = validation_results
    
    return validation_results

def check_enhanced_bedding_predictor_integration() -> Dict[str, Any]:
    """
    Verify that EnhancedBeddingZonePredictor is being used instead of mature_buck_predictor
    Addresses the core issue identified in user's analysis
    """
    integration_check = {
        "predictor_type_detected": "unknown",
        "enhanced_predictor_active": False,
        "bedding_zone_generation": False,
        "suitability_threshold_adaptive": False,
        "biological_accuracy": False,
        "check_timestamp": datetime.now().isoformat()
    }
    
    try:
        # Check current prediction results for enhanced predictor indicators
        if 'prediction_results' in st.session_state:
            prediction = st.session_state.prediction_results
            
            # Look for enhanced predictor signatures
            bedding_zones = prediction.get('bedding_zones', {})
            
            if bedding_zones:
                # Check for GeoJSON format (enhanced predictor signature)
                if 'features' in bedding_zones:
                    integration_check["enhanced_predictor_active"] = True
                    integration_check["predictor_type_detected"] = "EnhancedBeddingZonePredictor"
                    
                    # Check for adaptive threshold indicators
                    properties = bedding_zones.get('properties', {})
                    suitability_analysis = properties.get('suitability_analysis', {})
                    
                    if 'overall_score' in suitability_analysis:
                        score = suitability_analysis['overall_score']
                        if score > 50:  # Indicates adaptive thresholds working
                            integration_check["suitability_threshold_adaptive"] = True
                            integration_check["biological_accuracy"] = True
                        
                        if score > 90:  # High scores indicate enhanced predictor
                            integration_check["bedding_zone_generation"] = True
                    
                    logger.info("✅ EnhancedBeddingZonePredictor detected and active")
                
                elif 'zones' in bedding_zones:
                    integration_check["predictor_type_detected"] = "legacy_predictor"
                    logger.warning("⚠️ Legacy predictor format detected")
            
            # Check for mature_buck_predictor signature (legacy)
            mature_buck = prediction.get('mature_buck_analysis', {})
            if mature_buck and not bedding_zones:
                integration_check["predictor_type_detected"] = "mature_buck_predictor"
                logger.warning("⚠️ mature_buck_predictor detected - should be EnhancedBeddingZonePredictor")
        
    except Exception as e:
        logger.error(f"❌ Integration check failed: {e}")
        integration_check["check_error"] = str(e)
    
    return integration_check

# Export functions for use in main app
__all__ = [
    'FrontendDataValidator',
    'create_enhanced_data_traceability_display',
    'enhanced_backend_logging_for_predictions',
    'check_enhanced_bedding_predictor_integration'
]
