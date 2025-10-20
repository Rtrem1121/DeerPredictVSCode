"""
Prediction Router

FastAPI router for deer movement prediction endpoints.
Uses the PredictionService to handle all prediction logic.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging
from zoneinfo import ZoneInfo
import numpy as np

# Import the prediction service and analyzer
from backend.services.prediction_service import get_prediction_service, convert_numpy_types
from backend.analysis.prediction_analyzer import create_prediction_analyzer
from pydantic import BaseModel

# Define request/response models locally since they're not in the streamlined service
class PredictionRequest(BaseModel):
    lat: float
    lon: float
    date_time: str
    season: str = "fall"
    fast_mode: bool = False
    hunt_period: str = "AM"  # Added to match frontend payload
    include_camera_placement: bool = False  # Added to match frontend payload

class PredictionResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = None
    error: str = None

class DetailedAnalysisResponse(BaseModel):
    success: bool
    prediction: Dict[str, Any] = None
    detailed_analysis: Dict[str, Any] = None
    error: str = None

logger = logging.getLogger(__name__)

# Create router
prediction_router = APIRouter(tags=["predictions"])


@prediction_router.post("/predict", summary="Generate deer movement predictions", response_model=PredictionResponse)
async def predict_movement(request: PredictionRequest) -> PredictionResponse:
    """
    Generate deer movement predictions for the given location and conditions.
    
    This endpoint provides comprehensive deer movement analysis including:
    - Travel corridor identification
    - Bedding area analysis with EnhancedBeddingZonePredictor
    - Feeding location predictions
    - Mature buck opportunities
    - Stand placement recommendations
    - Weather impact analysis
    """
    try:
        # Use the prediction service with enhanced bedding predictor
        prediction_service = get_prediction_service()
        
        # Parse datetime and season from request
        from datetime import datetime
        dt = datetime.fromisoformat(request.date_time.replace('Z', '+00:00'))
        eastern = ZoneInfo("America/New_York")
        target_dt = dt.astimezone(eastern) if dt.tzinfo else dt.replace(tzinfo=eastern)
        
        # Call the enhanced prediction method
        result = await prediction_service.predict(
            lat=request.lat,
            lon=request.lon, 
            time_of_day=target_dt.hour,
            season=request.season,
            hunting_pressure="high",  # Default for now
            target_datetime=target_dt
        )
        
        # Convert any numpy types to ensure JSON serialization compatibility
        result = convert_numpy_types(result)
        
        return PredictionResponse(success=True, data=result)
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return PredictionResponse(success=False, error=str(e))


@prediction_router.post("/analyze-prediction-detailed", 
                       summary="Generate detailed prediction analysis", 
                       response_model=DetailedAnalysisResponse)
async def analyze_prediction_detailed(request: PredictionRequest) -> DetailedAnalysisResponse:
    """
    Generate comprehensive prediction analysis with detailed wind and thermal analysis.
    
    This endpoint provides the same prediction as /predict but with additional analysis including:
    - Detailed criteria analysis and scoring breakdowns
    - Data source quality assessment
    - Algorithm decision tracking
    - Comprehensive wind direction analysis
    - Advanced thermal analysis
    - Tactical recommendations based on environmental conditions
    
    This is intended for detailed analysis display and does not affect normal prediction functionality.
    """
    try:
        # Create analyzer for detailed analysis collection
        analyzer = create_prediction_analyzer()
        
        # Use the prediction service with analyzer
        prediction_service = get_prediction_service()
        
        # Parse datetime and season from request
        from datetime import datetime
        dt = datetime.fromisoformat(request.date_time.replace('Z', '+00:00'))
        eastern = ZoneInfo("America/New_York")
        target_dt = dt.astimezone(eastern) if dt.tzinfo else dt.replace(tzinfo=eastern)
        
        # Call the enhanced prediction method with analysis collection
        result = await prediction_service.predict_with_analysis(
            lat=request.lat,
            lon=request.lon, 
            time_of_day=target_dt.hour,
            season=request.season,
            hunting_pressure="high",  # Default for now
            analyzer=analyzer,
            target_datetime=target_dt
        )
        
        # Get comprehensive analysis
        detailed_analysis = analyzer.get_comprehensive_analysis()
        
        # Convert numpy types to ensure JSON serialization
        result = convert_numpy_types(result)
        detailed_analysis = convert_numpy_types(detailed_analysis)
        
        logger.info(f"🔍 Detailed analysis generated: {detailed_analysis['analysis_metadata']['completion_percentage']:.1f}% complete")
        
        return DetailedAnalysisResponse(
            success=True, 
            prediction=result,
            detailed_analysis=detailed_analysis
        )
        
    except Exception as e:
        logger.error(f"Detailed analysis failed: {e}")
        return DetailedAnalysisResponse(success=False, error=str(e))
