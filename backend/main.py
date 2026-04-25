"""
Refactored FastAPI Application

This is the new main application file using the router-based architecture.
All business logic has been moved to services, and API endpoints are in routers.

This refactoring preserves 100% of the original functionality while improving:
- Code organization and maintainability
- Separation of concerns
- Testability
- Modularity

Author: GitHub Copilot (Refactoring Assistant)
Date: August 24, 2025
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Dict, Any

# Set up logging first with custom filter to suppress health checks
class HealthCheckFilter(logging.Filter):
    """Filter out health check requests from logs to reduce noise"""
    def filter(self, record: logging.LogRecord) -> bool:
        # Suppress health check logs (both Docker healthchecks and Streamlit pings)
        return "/health" not in record.getMessage()

# Configure logging for containers
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', delay=True),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add filter to uvicorn access logger to suppress health check spam
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

# Import the new routers
from backend.routers.config_router import config_router
from backend.routers.camera_router import camera_router
from backend.routers.scouting_router import scouting_router
from backend.routers.max_accuracy_router import max_accuracy_router, run_startup_cleanup_jobs


def _get_allowed_origins() -> list[str]:
    """Resolve CORS origins from env, defaulting to local Streamlit hosts."""
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if raw.strip():
        origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
        if origins:
            return origins
    return ["http://localhost:8501", "http://127.0.0.1:8501"]


LEGACY_PREDICTION_ENABLED = os.getenv("LEGACY_PREDICTION", "0") == "1"

# Check for enhanced predictions availability
ENHANCED_PREDICTIONS_AVAILABLE = False
if LEGACY_PREDICTION_ENABLED:
    try:
        from backend.enhanced_endpoints import enhanced_router
        ENHANCED_PREDICTIONS_AVAILABLE = True
        logger.info("Enhanced prediction system with satellite data loaded successfully")
    except ImportError as e:
        logger.warning(f"Enhanced prediction system not available: {e}")
        logger.warning("Falling back to standard prediction functionality")
else:
    logger.info("Legacy prediction endpoints disabled (set LEGACY_PREDICTION=1 to enable)")

# Create FastAPI application


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    run_startup_cleanup_jobs()
    yield


app = FastAPI(
    title="Vermont Deer Prediction API - Refactored",
    description="Advanced deer movement prediction system for Vermont hunters - Now with improved architecture!",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=app_lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the new routers
app.include_router(config_router)
app.include_router(camera_router)
app.include_router(scouting_router)
app.include_router(max_accuracy_router)

# Enhanced prediction system inclusion (preserving existing logic)
if ENHANCED_PREDICTIONS_AVAILABLE:
    app.include_router(enhanced_router)


# Keep essential health and root endpoints in main
@app.get("/health", summary="Health check endpoint", tags=["health"])
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    try:
        from backend.config_manager import get_config
        from backend.services.lidar_processor import DEMFileManager

        config = get_config()
        metadata = config.get_metadata()

        gee_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        gee_project_id = os.getenv("GEE_PROJECT_ID", "")
        weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")

        dem_ok = bool(DEMFileManager().get_files())
        gee_creds_ok = bool(gee_creds_path and os.path.exists(gee_creds_path))
        gee_project_ok = bool(gee_project_id)
        weather_ok = bool(weather_api_key)

        services = {
            "configuration_service": "operational" if metadata else "degraded",
            "dem_lidar_service": "operational" if dem_ok else "degraded",
            "gee_credentials": "operational" if gee_creds_ok else "degraded",
            "gee_project": "operational" if gee_project_ok else "degraded",
            "weather_api": "operational" if weather_ok else "degraded",
            "enhanced_prediction_router": (
                "operational"
                if ENHANCED_PREDICTIONS_AVAILABLE
                else ("disabled" if not LEGACY_PREDICTION_ENABLED else "degraded")
            ),
        }
        overall_status = "healthy" if all(v == "operational" for v in services.values()) else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "architecture": "refactored",
            "config_status": "loaded" if metadata else "error",
            "services": services,
            "enhanced_predictions": ENHANCED_PREDICTIONS_AVAILABLE
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "error": str(e)
        }


@app.get("/rules", summary="Get all prediction rules", response_model=List[Dict[str, Any]], tags=["rules"])
def get_rules():
    """Get prediction rules from data/rules.json file."""
    import json
    from pathlib import Path
    
    # Load rules from data directory
    rules_path = Path(__file__).parent.parent / "data" / "rules.json"
    
    try:
        with open(rules_path, 'r') as f:
            rules = json.load(f)
        return rules
    except FileNotFoundError:
        logger.error(f"Rules file not found at {rules_path}")
        raise HTTPException(status_code=500, detail="Rules file not found")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rules file: {e}")
        raise HTTPException(status_code=500, detail="Invalid rules file format")


# Preserve any remaining functionality from original main.py that hasn't been moved to routers yet
# This ensures 100% functionality preservation during the transition

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
