"""
Camera Router

FastAPI router for trail camera placement endpoints.
Uses the CameraService for business logic.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from backend.services.camera_service import CameraService, TrailCameraRequest, CameraPlacementRequest

# Create router
camera_router = APIRouter(tags=["hunting"])

# Initialize service
camera_service = CameraService()


@camera_router.post("/trail-cameras", summary="Get trail camera placement recommendations")
def get_trail_camera_placements(request: TrailCameraRequest) -> Dict[str, Any]:
    """Get optimal trail camera placement recommendations for mature buck photography."""
    return camera_service.get_trail_camera_placements(request)


@camera_router.post("/api/camera/optimal-placement", summary="Get optimal single camera placement")
def get_optimal_camera_placement(request: CameraPlacementRequest) -> Dict[str, Any]:
    """Get the single optimal trail camera placement using advanced analysis."""
    return camera_service.get_optimal_camera_placement(request)
