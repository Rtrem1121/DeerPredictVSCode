"""
Prediction Router

FastAPI router for deer movement prediction endpoints.
Uses the PredictionService to handle all prediction logic.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging

# Import the prediction service
from backend.services.prediction_service import get_prediction_service
from pydantic import BaseModel

# Define request/response models locally since they're not in the streamlined service
class PredictionRequest(BaseModel):
    lat: float
    lon: float
    date_time: str
    season: str = "fall"
    fast_mode: bool = False

class PredictionResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = None
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
        
        # Call the enhanced prediction method
        result = await prediction_service.predict(
            lat=request.lat,
            lon=request.lon, 
            time_of_day=dt.hour,
            season=request.season,
            hunting_pressure="high"  # Default for now
        )
        
        return PredictionResponse(success=True, data=result)
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return PredictionResponse(success=False, error=str(e))
