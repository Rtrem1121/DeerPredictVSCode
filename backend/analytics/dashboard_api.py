#!/usr/bin/env python3
"""
Analytics Dashboard Backend API

This module provides REST API endpoints for the analytics dashboard,
serving real-time and historical data about deer prediction system performance.

Features:
- Real-time system metrics
- Prediction analytics
- Performance trends
- Configuration tracking
- Alert notifications

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import json

from .data_collector import get_analytics_collector
from .performance_monitor import get_performance_monitor
# Import configuration management
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
from config_manager import get_config

logger = logging.getLogger(__name__)

# Pydantic models for API responses
class AnalyticsSummary(BaseModel):
    total_predictions: int
    avg_confidence_score: float
    avg_response_time_ms: float
    success_rate: float
    active_period_days: int

class DailyStats(BaseModel):
    prediction_date: str
    count: int
    avg_confidence: float

class ConfidenceDistribution(BaseModel):
    confidence_range: str
    count: int

class PredictionAnalytics(BaseModel):
    summary: AnalyticsSummary
    daily_stats: List[DailyStats]
    confidence_distribution: List[ConfidenceDistribution]
    query_period_days: int

class SystemHealthResponse(BaseModel):
    timestamp: str
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    response_time_avg_ms: float
    predictions_per_minute: float
    error_rate_percent: float
    overall_status: str

class PerformanceMetric(BaseModel):
    timestamp: str
    metric_type: str
    value: float

class AlertResponse(BaseModel):
    alert_id: str
    timestamp: str
    severity: str
    metric_type: str
    current_value: float
    threshold_value: float
    message: str

# Initialize FastAPI app
app = FastAPI(
    title="Deer Prediction Analytics API",
    description="Real-time analytics and monitoring for Vermont Deer Prediction System",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analytics components
analytics_collector = get_analytics_collector()
performance_monitor = get_performance_monitor()

@app.on_event("startup")
async def startup_event():
    """Initialize analytics services on startup"""
    logger.info("🚀 Starting Analytics Dashboard API")
    
    # Start performance monitoring
    performance_monitor.start_monitoring()
    
    logger.info("✅ Analytics Dashboard API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Analytics Dashboard API")
    
    # Stop performance monitoring
    performance_monitor.stop_monitoring()
    
    logger.info("✅ Analytics Dashboard API shutdown complete")

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Deer Prediction Analytics API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "analytics_collector": "operational",
            "performance_monitor": "operational" if performance_monitor._monitoring_active else "stopped"
        }
    }

@app.get("/analytics/predictions", response_model=Dict[str, Any])
async def get_prediction_analytics(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    season: Optional[str] = Query(None, description="Filter by season"),
    min_confidence: Optional[float] = Query(None, ge=0, le=100, description="Minimum confidence score")
):
    """Get prediction analytics for specified time period"""
    try:
        analytics_data = analytics_collector.get_prediction_analytics(
            days=days,
            season=season,
            min_confidence=min_confidence
        )
        
        if "error" in analytics_data:
            raise HTTPException(status_code=500, detail=analytics_data["error"])
        
        return analytics_data
        
    except Exception as e:
        logger.error(f"Error getting prediction analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/performance", response_model=Dict[str, Any])
async def get_performance_analytics(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to analyze")
):
    """Get system performance analytics"""
    try:
        performance_data = analytics_collector.get_performance_analytics(hours=hours)
        
        if "error" in performance_data:
            raise HTTPException(status_code=500, detail=performance_data["error"])
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/health", response_model=SystemHealthResponse)
async def get_current_health():
    """Get current system health status"""
    try:
        health = performance_monitor.get_current_health()
        
        return SystemHealthResponse(
            timestamp=health.timestamp.isoformat(),
            cpu_usage_percent=health.cpu_usage_percent,
            memory_usage_percent=health.memory_usage_percent,
            disk_usage_percent=health.disk_usage_percent,
            response_time_avg_ms=health.response_time_avg_ms,
            predictions_per_minute=health.predictions_per_minute,
            error_rate_percent=health.error_rate_percent,
            overall_status=health.overall_status
        )
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/metrics", response_model=List[PerformanceMetric])
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168, description="Hours of metrics to retrieve"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type")
):
    """Get performance metrics history"""
    try:
        history = performance_monitor.get_performance_history(hours=hours)
        
        metrics = []
        for metric_name, data_points in history.items():
            if metric_type and metric_name != metric_type:
                continue
                
            for timestamp, value in data_points:
                metrics.append(PerformanceMetric(
                    timestamp=timestamp.isoformat(),
                    metric_type=metric_name,
                    value=value
                ))
        
        # Sort by timestamp
        metrics.sort(key=lambda x: x.timestamp)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/summary", response_model=Dict[str, Any])
async def get_performance_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours to summarize")
):
    """Get performance summary statistics"""
    try:
        summary = performance_monitor.get_performance_summary(hours=hours)
        return summary
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config/current", response_model=Dict[str, Any])
async def get_current_configuration():
    """Get current system configuration"""
    try:
        config = get_config()
        
        # Convert configuration to dictionary for API response
        config_dict = {
            "metadata": {
                "environment": config.metadata.environment,
                "version": config.metadata.version,
                "loaded_at": config.metadata.loaded_at.isoformat() if config.metadata.loaded_at else None
            },
            "parameters": {
                "mature_buck": config.mature_buck.__dict__,
                "distance": config.distance.__dict__,
                "terrain": config.terrain.__dict__,
                "weather": config.weather.__dict__,
                "timing": config.timing.__dict__,
                "seasonal": config.seasonal.__dict__,
                "stand": config.stand.__dict__
            }
        }
        
        return config_dict
        
    except Exception as e:
        logger.error(f"Error getting current configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/overview", response_model=Dict[str, Any])
async def get_dashboard_overview():
    """Get comprehensive dashboard overview data"""
    try:
        # Get prediction analytics (last 7 days)
        prediction_analytics = analytics_collector.get_prediction_analytics(days=7)
        
        # Get current system health
        current_health = performance_monitor.get_current_health()
        
        # Get performance summary (last 24 hours)
        performance_summary = performance_monitor.get_performance_summary(hours=24)
        
        # Get configuration info
        config = get_config()
        
        overview = {
            "timestamp": datetime.now().isoformat(),
            "system_health": {
                "overall_status": current_health.overall_status,
                "cpu_usage": current_health.cpu_usage_percent,
                "memory_usage": current_health.memory_usage_percent,
                "response_time": current_health.response_time_avg_ms
            },
            "prediction_summary": {
                "total_predictions": prediction_analytics.get("summary", {}).get("total_predictions", 0),
                "avg_confidence": prediction_analytics.get("summary", {}).get("avg_confidence", 0),
                "avg_rating": prediction_analytics.get("summary", {}).get("avg_rating", 0)
            },
            "performance_trends": performance_summary,
            "configuration": {
                "environment": config.metadata.environment,
                "version": config.metadata.version
            }
        }
        
        return overview
        
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/update-summary")
async def update_analytics_summary(background_tasks: BackgroundTasks):
    """Trigger update of analytics summary (for manual refresh)"""
    try:
        background_tasks.add_task(analytics_collector.update_daily_summary)
        
        return {
            "status": "update_scheduled",
            "message": "Analytics summary update scheduled",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error scheduling analytics update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "endpoint_not_found",
        "message": f"Endpoint {request.url.path} not found",
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error on {request.url.path}: {exc}")
    return {
        "error": "internal_server_error",
        "message": "An internal error occurred",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        "dashboard_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
