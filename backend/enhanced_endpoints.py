#!/usr/bin/env python3
"""
Enhanced Prediction FastAPI Endpoints

FastAPI endpoints for satellite-enhanced deer prediction functionality.
Integrates with existing main.py backend architecture.

Author: GitHub Copilot
Date: August 14, 2025
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from backend.enhanced_prediction_api import get_enhanced_prediction_api

logger = logging.getLogger(__name__)

# Router for enhanced prediction endpoints
enhanced_router = APIRouter(prefix="/api/enhanced", tags=["Enhanced Predictions"])

# Enhanced prediction API instance
enhanced_api = get_enhanced_prediction_api()

# Request/Response Models
class EnhancedPredictionRequest(BaseModel):
    """Request model for enhanced predictions"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    hunt_date: Optional[str] = Field(None, description="Target hunt date (ISO format)")
    season: str = Field("early_season", description="Hunting season")

class PredictionComparisonRequest(BaseModel):
    """Request model for prediction method comparison"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    hunt_date: Optional[str] = Field(None, description="Target hunt date (ISO format)")

class VegetationRequest(BaseModel):
    """Request model for vegetation analysis"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


@enhanced_router.get("/satellite/ndvi")
async def get_ndvi_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
) -> Dict[str, Any]:
    """Get NDVI satellite data for a location"""
    try:
        vegetation_data = await enhanced_api.get_vegetation_summary(lat, lon)
        logger.info(f"Vegetation data received: {vegetation_data}")
        
        if vegetation_data:
            # Try to extract NDVI from vegetation_health section
            vegetation_health = vegetation_data.get('vegetation_health', {})
            if 'ndvi_value' in vegetation_health:
                return {
                    "ndvi": vegetation_health['ndvi_value'],
                    "vegetation_health": vegetation_health.get('health_status', 'unknown'),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Also check if it's directly in the response
            if 'ndvi_analysis' in vegetation_data:
                ndvi_analysis = vegetation_data['ndvi_analysis']
                return {
                    "ndvi": ndvi_analysis.get('ndvi_value'),
                    "vegetation_health": ndvi_analysis.get('vegetation_health', 'unknown'),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Return whatever vegetation data we have
            return {
                "ndvi": None,
                "vegetation_data": vegetation_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"ndvi": None, "error": "No satellite data available"}
    except Exception as e:
        logger.error(f"NDVI data retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Satellite data error: {str(e)}")

@enhanced_router.post("/predict")
async def generate_enhanced_prediction(request: EnhancedPredictionRequest) -> Dict[str, Any]:
    """
    Generate enhanced deer movement prediction with satellite data integration
    
    This endpoint provides satellite-enhanced predictions including:
    - NDVI vegetation health analysis
    - Land cover classification
    - Food source mapping
    - Hunting pressure assessment
    - Movement corridor identification
    - Optimal stand recommendations
    
    Args:
        request: Enhanced prediction request parameters
        
    Returns:
        Comprehensive prediction results with satellite insights
    """
    
    try:
        logger.info(f"🎯 Enhanced prediction requested for {request.latitude:.4f}, {request.longitude:.4f}")
        
        result = await enhanced_api.generate_enhanced_prediction(
            lat=request.latitude,
            lon=request.longitude,
            hunt_date=request.hunt_date,
            season=request.season
        )
        
        logger.info(f"✅ Enhanced prediction completed with {result.get('enhancement_level', 'unknown')} level")
        
        return {
            "status": "success",
            "prediction_data": result,
            "message": f"Enhanced prediction generated with {result.get('enhancement_level', 'standard')} satellite enhancement"
        }
        
    except Exception as e:
        logger.error(f"Enhanced prediction endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced prediction failed: {str(e)}"
        )


@enhanced_router.post("/compare")
async def compare_prediction_methods(request: PredictionComparisonRequest) -> Dict[str, Any]:
    """
    Compare standard vs enhanced prediction methods
    
    Provides side-by-side comparison of:
    - Standard terrain/weather prediction
    - Enhanced satellite-integrated prediction
    - Improvement metrics
    - Method recommendation
    
    Args:
        request: Comparison request parameters
        
    Returns:
        Detailed comparison of prediction methods
    """
    
    try:
        logger.info(f"📊 Prediction comparison requested for {request.latitude:.4f}, {request.longitude:.4f}")
        
        comparison_result = await enhanced_api.compare_prediction_methods(
            lat=request.latitude,
            lon=request.longitude,
            hunt_date=request.hunt_date
        )
        
        logger.info("✅ Prediction comparison completed")
        
        return {
            "status": "success",
            "comparison_data": comparison_result,
            "message": "Prediction method comparison completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Prediction comparison endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction comparison failed: {str(e)}"
        )


@enhanced_router.post("/vegetation")
async def get_vegetation_analysis(request: VegetationRequest) -> Dict[str, Any]:
    """
    Get detailed vegetation analysis for hunting area
    
    Provides satellite-derived vegetation insights including:
    - Vegetation health (NDVI analysis)
    - Food source availability
    - Land cover breakdown
    - Habitat suitability assessment
    - Water source proximity
    
    Args:
        request: Vegetation analysis request parameters
        
    Returns:
        Comprehensive vegetation analysis results
    """
    
    try:
        logger.info(f"🌿 Vegetation analysis requested for {request.latitude:.4f}, {request.longitude:.4f}")
        
        vegetation_summary = await enhanced_api.get_vegetation_summary(
            lat=request.latitude,
            lon=request.longitude
        )
        
        logger.info("✅ Vegetation analysis completed")
        
        return {
            "status": "success",
            "vegetation_data": vegetation_summary,
            "message": "Vegetation analysis completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Vegetation analysis endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Vegetation analysis failed: {str(e)}"
        )


@enhanced_router.get("/predict/{lat}/{lon}")
async def get_enhanced_prediction_simple(
    lat: float = Path(..., ge=-90, le=90, description="Latitude coordinate"),
    lon: float = Path(..., ge=-180, le=180, description="Longitude coordinate"),
    hunt_date: Optional[str] = Query(None, description="Target hunt date (ISO format)"),
    season: str = Query("early_season", description="Hunting season")
) -> Dict[str, Any]:
    """
    Simple GET endpoint for enhanced prediction (for easy URL-based access)
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        hunt_date: Optional target hunt date
        season: Hunting season
        
    Returns:
        Enhanced prediction results
    """
    
    request = EnhancedPredictionRequest(
        latitude=lat,
        longitude=lon,
        hunt_date=hunt_date,
        season=season
    )
    
    return await generate_enhanced_prediction(request)


@enhanced_router.get("/vegetation/{lat}/{lon}")
async def get_vegetation_analysis_simple(
    lat: float = Path(..., ge=-90, le=90, description="Latitude coordinate"),
    lon: float = Path(..., ge=-180, le=180, description="Longitude coordinate")
) -> Dict[str, Any]:
    """
    Simple GET endpoint for vegetation analysis (for easy URL-based access)
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        
    Returns:
        Vegetation analysis results
    """
    
    request = VegetationRequest(latitude=lat, longitude=lon)
    return await get_vegetation_analysis(request)


@enhanced_router.get("/health")
async def enhanced_prediction_health() -> Dict[str, Any]:
    """
    Health check endpoint for enhanced prediction system
    
    Returns:
        System health status and capabilities
    """
    
    try:
        # Test basic functionality
        test_result = await enhanced_api.get_vegetation_summary(39.7392, -104.9903)  # Denver, CO
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "capabilities": {
                "satellite_analysis": "available",
                "vegetation_health_assessment": "operational",
                "enhanced_predictions": "functional",
                "prediction_comparison": "enabled"
            },
            "test_result": "vegetation_analysis_successful" if test_result else "test_failed",
            "message": "Enhanced prediction system is operational"
        }
        
    except Exception as e:
        logger.warning(f"Enhanced prediction health check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "capabilities": {
                "satellite_analysis": "limited",
                "vegetation_health_assessment": "fallback_mode",
                "enhanced_predictions": "basic_functionality",
                "prediction_comparison": "standard_only"
            },
            "error": str(e),
            "message": "Enhanced prediction system running in fallback mode"
        }


# Export router for integration with main FastAPI app
__all__ = ['enhanced_router']
