#!/usr/bin/env python3
"""
Deer Movement Prediction API - Refactored

Modern FastAPI application following best practices:
- Service layer architecture
- Comprehensive error handling
- Configuration management
- Type safety
- Structured logging
- Performance monitoring

Author: GitHub Copilot
Version: 2.0.0
Date: August 14, 2025
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn

# Application imports
from backend.services.prediction_service import (
    PredictionService, 
    PredictionContext, 
    PredictionResult,
    get_prediction_service
)
from backend.middleware.error_handling import (
    ErrorHandlingMiddleware,
    AppException,
    ErrorType,
    ErrorSeverity,
    ValidationError,
    BusinessLogicError
)
from backend.config.settings import (
    ApplicationConfig,
    get_config,
    get_config_manager
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# --- Pydantic Models ---

class PredictionRequest(BaseModel):
    """Request model for deer movement predictions"""
    
    lat: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees") 
    date_time: str = Field(..., description="Hunt date/time in ISO format")
    season: str = Field(..., description="Hunting season")
    fast_mode: bool = Field(default=False, description="Enable fast prediction mode")
    suggestion_threshold: Optional[float] = Field(default=None, ge=0, le=10, description="Suggestion threshold")
    min_suggestion_rating: Optional[float] = Field(default=None, ge=0, le=10, description="Minimum suggestion rating")
    
    @validator('season')
    def validate_season(cls, v):
        """Validate season parameter"""
        valid_seasons = ['early_season', 'pre_rut', 'rut', 'late_season']
        if v.lower() not in valid_seasons:
            raise ValueError(f"Season must be one of: {', '.join(valid_seasons)}")
        return v.lower()
    
    @validator('date_time')
    def validate_datetime(cls, v):
        """Validate datetime format"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Invalid datetime format. Use ISO format (e.g., '2024-11-15T07:00:00')")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "lat": 44.26,
                "lon": -72.58,
                "date_time": "2024-11-15T07:00:00",
                "season": "rut",
                "fast_mode": False,
                "suggestion_threshold": 5.0,
                "min_suggestion_rating": 8.0
            }
        }
    }


class PredictionResponse(BaseModel):
    """Response model for deer movement predictions"""
    
    # Core prediction results
    travel_corridors: Dict[str, Any] = Field(..., description="Predicted travel corridors")
    bedding_zones: Dict[str, Any] = Field(..., description="Predicted bedding areas")
    feeding_areas: Dict[str, Any] = Field(..., description="Predicted feeding zones")
    
    # Analysis results
    stand_rating: float = Field(..., ge=0, le=10, description="Overall stand rating")
    notes: str = Field(..., description="Detailed prediction analysis")
    
    # Heatmap data
    terrain_heatmap: str = Field(default="", description="Base64 encoded terrain heatmap")
    vegetation_heatmap: str = Field(default="", description="Base64 encoded vegetation heatmap")
    travel_score_heatmap: str = Field(default="", description="Base64 encoded travel score heatmap")
    bedding_score_heatmap: str = Field(default="", description="Base64 encoded bedding score heatmap")
    feeding_score_heatmap: str = Field(default="", description="Base64 encoded feeding score heatmap")
    
    # Advanced features
    mature_buck_opportunities: Optional[Dict[str, Any]] = Field(default=None, description="Mature buck analysis")
    suggested_spots: List[Dict[str, Any]] = Field(default=[], description="Alternative location suggestions")
    stand_recommendations: List[Dict[str, Any]] = Field(default=[], description="Stand placement recommendations")
    five_best_stands: List[Dict[str, Any]] = Field(default=[], description="Top 5 stand locations")
    hunt_schedule: List[Dict[str, Any]] = Field(default=[], description="48-hour hunt schedule")
    mature_buck_analysis: Optional[Dict[str, Any]] = Field(default=None, description="Detailed mature buck analysis")
    
    # Metadata
    prediction_id: Optional[str] = Field(default=None, description="Unique prediction identifier")
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Generation timestamp")
    processing_time_ms: Optional[float] = Field(default=None, description="Processing time in milliseconds")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "travel_corridors": {"features": [], "confidence": 0.85},
                "bedding_zones": {"features": [], "confidence": 0.78},
                "feeding_areas": {"features": [], "confidence": 0.82},
                "stand_rating": 7.5,
                "notes": "Excellent rut conditions with multiple travel corridors...",
                "mature_buck_opportunities": {"viable_location": True, "confidence": 0.73},
                "stand_recommendations": [],
                "five_best_stands": [],
                "hunt_schedule": [],
                "prediction_id": "pred_123456",
                "generated_at": "2024-11-15T12:00:00.000Z",
                "processing_time_ms": 1250.5
            }
        }
    }


class HealthResponse(BaseModel):
    """Health check response model"""
    
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    
    # Service status
    services: Dict[str, str] = Field(default={}, description="Dependent service status")
    
    # System metrics
    memory_usage_mb: Optional[float] = Field(default=None, description="Memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(default=None, description="CPU usage percentage")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "timestamp": "2024-11-15T12:00:00.000Z",
                "version": "2.0.0",
                "environment": "production",
                "uptime_seconds": 3600.5,
                "services": {
                    "database": "healthy",
                    "weather_api": "healthy",
                    "terrain_api": "healthy"
                },
                "memory_usage_mb": 256.7,
                "cpu_usage_percent": 15.3
            }
        }
    }


# --- Application Factory ---

def create_application() -> FastAPI:
    """
    Create and configure FastAPI application with all middleware and dependencies.
    
    Returns:
        FastAPI: Configured application instance
    """
    
    # Load configuration
    config = get_config()
    
    # Create FastAPI app
    app = FastAPI(
        title="Deer Movement Prediction API",
        description="Advanced API for predicting whitetail deer movement patterns using terrain analysis, weather data, and machine learning.",
        version="2.0.0",
        docs_url="/docs" if config.enable_docs else None,
        redoc_url="/redoc" if config.enable_docs else None,
        openapi_tags=[
            {
                "name": "predictions",
                "description": "Deer movement prediction operations",
            },
            {
                "name": "health",
                "description": "API health and monitoring",
            },
            {
                "name": "configuration",
                "description": "Configuration management",
            }
        ]
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.security.allowed_origins,
        allow_credentials=config.security.allow_credentials,
        allow_methods=config.security.allowed_methods,
        allow_headers=config.security.allowed_headers,
    )
    
    # Add error handling middleware
    error_middleware = ErrorHandlingMiddleware(app)
    app.middleware("http")(error_middleware)
    
    # Application startup time for uptime calculation
    app.state.startup_time = time.time()
    
    return app


# Create application instance
app = create_application()


# --- Dependencies ---

def get_prediction_service_dependency() -> PredictionService:
    """Dependency injection for prediction service"""
    return get_prediction_service()


def get_config_dependency() -> ApplicationConfig:
    """Dependency injection for configuration"""
    return get_config()


# --- API Endpoints ---

@app.get("/", 
         summary="Root endpoint", 
         response_model=Dict[str, str],
         tags=["health"])
async def root() -> Dict[str, str]:
    """
    Root endpoint providing basic API information.
    
    Returns:
        Dict containing welcome message and API information
    """
    config = get_config()
    
    return {
        "message": "Welcome to the Deer Movement Prediction API",
        "version": "2.0.0",
        "environment": config.environment.value,
        "documentation": "/docs",
        "health": "/health"
    }


@app.get("/health",
         summary="Health check endpoint",
         response_model=HealthResponse,
         tags=["health"])
async def health_check() -> HealthResponse:
    """
    Comprehensive health check endpoint for monitoring and load balancers.
    
    Returns:
        HealthResponse: Detailed health status information
    """
    try:
        config = get_config()
        current_time = time.time()
        uptime = current_time - app.state.startup_time
        
        # Check dependent services
        services_status = {}
        
        # Check weather API
        try:
            # TODO: Implement actual health checks for external services
            services_status["weather_api"] = "healthy"
        except Exception:
            services_status["weather_api"] = "degraded"
        
        # Check Google Earth Engine
        if config.enable_gee_integration:
            try:
                services_status["google_earth_engine"] = "healthy"
            except Exception:
                services_status["google_earth_engine"] = "degraded"
        
        # Get system metrics
        memory_usage = None
        cpu_usage = None
        
        try:
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
            cpu_usage = process.cpu_percent()
        except ImportError:
            logger.debug("psutil not available for system metrics")
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="2.0.0",
            environment=config.environment.value,
            uptime_seconds=uptime,
            services=services_status,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )


@app.post("/predict",
          summary="Generate deer movement predictions",
          response_model=PredictionResponse,
          tags=["predictions"])
async def predict_movement(
    request: PredictionRequest,
    prediction_service: PredictionService = Depends(get_prediction_service_dependency),
    config: ApplicationConfig = Depends(get_config_dependency)
) -> PredictionResponse:
    """
    Generate comprehensive deer movement predictions for a specific location and time.
    
    This endpoint analyzes terrain, weather, and historical data to predict deer behavior
    patterns including travel corridors, bedding areas, and feeding zones.
    
    Args:
        request: Prediction parameters including location, time, and season
        prediction_service: Injected prediction service
        config: Application configuration
        
    Returns:
        PredictionResponse: Comprehensive prediction analysis
        
    Raises:
        ValidationError: If input parameters are invalid
        BusinessLogicError: If prediction cannot be generated
        ExternalServiceError: If external APIs fail
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting prediction for {request.lat:.4f}, {request.lon:.4f}")
        
        # Parse datetime
        try:
            hunt_datetime = datetime.fromisoformat(request.date_time.replace('Z', '+00:00'))
            if hunt_datetime.tzinfo is None:
                hunt_datetime = hunt_datetime.replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise ValidationError(f"Invalid datetime format: {str(e)}", "date_time", request.date_time)
        
        # Apply configuration defaults
        suggestion_threshold = request.suggestion_threshold or config.prediction.suggestion_threshold
        min_suggestion_rating = request.min_suggestion_rating or config.prediction.min_suggestion_rating
        
        # Create prediction context
        context = PredictionContext(
            lat=request.lat,
            lon=request.lon,
            date_time=hunt_datetime,
            season=request.season,
            fast_mode=request.fast_mode,
            suggestion_threshold=suggestion_threshold,
            min_suggestion_rating=min_suggestion_rating
        )
        
        # Generate prediction
        prediction_result = prediction_service.predict(context)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Convert to response model
        response = PredictionResponse(
            travel_corridors=prediction_result.travel_corridors,
            bedding_zones=prediction_result.bedding_zones,
            feeding_areas=prediction_result.feeding_areas,
            stand_rating=prediction_result.stand_rating,
            notes=prediction_result.notes,
            terrain_heatmap=prediction_result.terrain_heatmap,
            vegetation_heatmap=prediction_result.vegetation_heatmap,
            travel_score_heatmap=prediction_result.travel_score_heatmap,
            bedding_score_heatmap=prediction_result.bedding_score_heatmap,
            feeding_score_heatmap=prediction_result.feeding_score_heatmap,
            mature_buck_opportunities=prediction_result.mature_buck_opportunities,
            suggested_spots=prediction_result.suggested_spots,
            stand_recommendations=prediction_result.stand_recommendations,
            five_best_stands=prediction_result.five_best_stands,
            hunt_schedule=prediction_result.hunt_schedule,
            mature_buck_analysis=prediction_result.mature_buck_analysis,
            prediction_id=f"pred_{int(time.time())}",
            processing_time_ms=processing_time
        )
        
        logger.info(f"Prediction completed in {processing_time:.2f}ms with rating: {response.stand_rating}")
        return response
        
    except ValidationError:
        raise  # Re-raise validation errors as-is
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise BusinessLogicError(
            message="Failed to generate prediction",
            operation="deer_movement_prediction",
            details={
                "location": f"{request.lat}, {request.lon}",
                "season": request.season,
                "error": str(e)
            }
        ) from e


@app.get("/config",
         summary="Get application configuration",
         response_model=Dict[str, Any],
         tags=["configuration"])
async def get_configuration(
    config_manager = Depends(lambda: get_config_manager())
) -> Dict[str, Any]:
    """
    Get current application configuration summary.
    
    Returns:
        Dict containing non-sensitive configuration information
    """
    try:
        config_summary = config_manager.get_config_summary()
        return config_summary
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve configuration"
        )


@app.get("/metrics",
         summary="Get application metrics",
         response_model=Dict[str, Any],
         tags=["health"])
async def get_metrics() -> Dict[str, Any]:
    """
    Get application performance metrics.
    
    Returns:
        Dict containing performance and usage metrics
    """
    try:
        # Get metrics from error handling middleware
        error_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'ErrorHandlingMiddleware':
                error_middleware = middleware.cls
                break
        
        if error_middleware and hasattr(error_middleware, 'get_error_summary'):
            metrics = error_middleware.get_error_summary()
        else:
            metrics = {"status": "metrics_not_available"}
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve metrics"
        )


# --- Application Events ---

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("Starting Deer Movement Prediction API v2.0.0")
    
    config = get_config()
    logger.info(f"Environment: {config.environment.value}")
    logger.info(f"Debug mode: {config.debug}")
    
    # Initialize services
    try:
        prediction_service = get_prediction_service()
        logger.info("Prediction service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize prediction service: {e}")
    
    logger.info("Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down Deer Movement Prediction API")
    
    # Cleanup tasks here
    # - Close database connections
    # - Flush logs
    # - Cancel background tasks
    
    logger.info("Application shutdown completed")


# --- Development Server ---

if __name__ == "__main__":
    """Run development server"""
    config = get_config()
    
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.is_development(),
        log_level=config.monitoring.log_level.value.lower(),
        access_log=True
    )
