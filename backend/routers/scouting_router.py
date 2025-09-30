"""
Scouting Router

FastAPI router for scouting observation endpoints.
Uses the ScoutingService for business logic.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, File, HTTPException, UploadFile
from backend.services.scouting_service import ScoutingService
from backend.scouting_models import ScoutingObservation, ScoutingObservationResponse

# Create router
scouting_router = APIRouter(prefix="/scouting", tags=["scouting"])

# Initialize service
scouting_service = ScoutingService()


@scouting_router.post("/add_observation", response_model=ScoutingObservationResponse)
async def add_scouting_observation(observation: ScoutingObservation) -> ScoutingObservationResponse:
    """Add a new scouting observation to enhance future predictions."""
    return await scouting_service.add_observation(observation)


@scouting_router.get("/observations")
async def get_scouting_observations(
    lat: float,
    lon: float,
    radius_miles: float = 2.0,
    observation_types: Optional[str] = None,
    min_confidence: Optional[int] = None,
    days_back: Optional[int] = None
) -> Dict[str, Any]:
    """Get scouting observations within a specified area."""
    return await scouting_service.get_observations(
        lat, lon, radius_miles, observation_types, min_confidence, days_back
    )


@scouting_router.get("/observation/{observation_id}")
async def get_scouting_observation(observation_id: str) -> Dict[str, Any]:
    """Get a specific scouting observation by ID."""
    return await scouting_service.get_observation_by_id(observation_id)


@scouting_router.delete("/observation/{observation_id}")
async def delete_scouting_observation(observation_id: str) -> Dict[str, str]:
    """Delete a scouting observation."""
    return await scouting_service.delete_observation(observation_id)


@scouting_router.get("/analytics")
async def get_scouting_analytics(
    lat: float,
    lon: float,
    radius_miles: float = 10.0
) -> Dict[str, Any]:
    """Get analytics for scouting observations in an area."""
    return await scouting_service.get_analytics(lat, lon, radius_miles)


@scouting_router.get("/types")
async def get_observation_types() -> Dict[str, Any]:
    """Get list of available observation types with descriptions."""
    return await scouting_service.get_observation_types()


@scouting_router.post("/import")
async def import_scouting_data(
    file: UploadFile = File(..., description="GPX file containing scouting waypoints"),
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Import scouting observations from a GPX upload."""

    try:
        file_bytes = await file.read()
    except Exception as exc:  # pragma: no cover - defensive I/O guard
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}")

    return await scouting_service.import_scouting_data(
        file_bytes,
        filename=file.filename,
        dry_run=dry_run,
    )
