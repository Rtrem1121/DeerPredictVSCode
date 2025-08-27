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
from fastapi import APIRouter, HTTPException
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


@enhanced_router.post("/predict")
async def generate_enhanced_prediction(request: EnhancedPredictionRequest) -> Dict[str, Any]:
    """
    Generate enhanced prediction using satellite data
    
    Combines satellite imagery analysis with traditional prediction methods to:
    - Assess terrain and weather conditions
    - Evaluate vegetation health and food source availability
    - Integrate real-time satellite data for accurate predictions
    
    Args:
        request: Enhanced prediction request parameters
        
    Returns:
        Enhanced prediction results
    """
    
    try:
        logger.info(f"🔮 Generating enhanced prediction for {request.latitude:.4f}, {request.longitude:.4f}")
        
        # Perform the enhanced prediction using the API
        prediction_result = await enhanced_api.get_enhanced_prediction(
            lat=request.latitude,
            lon=request.longitude,
            hunt_date=request.hunt_date,
            season=request.season
        )
        
        logger.info("✅ Enhanced prediction successful")
        
        return {
            "status": "success",
            "prediction_data": prediction_result,
            "message": "Enhanced prediction completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Enhanced prediction endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced prediction failed: {str(e)}"
        )


# Export router for integration with main FastAPI app
__all__ = ['enhanced_router']
