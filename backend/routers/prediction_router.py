"""
Prediction Router

FastAPI router for deer movement prediction endpoints.
Uses the PredictionService to handle all prediction logic.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging

# Import the prediction service and models
from backend.services.prediction_service import (
    get_prediction_service, 
    PredictionRequest, 
    PredictionResponse
)

logger = logging.getLogger(__name__)

# Create router
prediction_router = APIRouter(tags=["predictions"])


@prediction_router.post("/predict", summary="Generate deer movement predictions", response_model=PredictionResponse)
def predict_movement(request: PredictionRequest) -> PredictionResponse:
    """
    Generate deer movement predictions for the given location and conditions.
    
    This endpoint provides comprehensive deer movement analysis including:
    - Travel corridor identification
    - Bedding area analysis  
    - Feeding location predictions
    - Mature buck opportunities
    - Stand placement recommendations
    - Weather impact analysis
    """
    # Use the prediction service to handle all logic
    prediction_service = get_prediction_service()
    return prediction_service.predict_movement(request)
