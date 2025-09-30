"""
Scouting Service

Handles scouting observation management and analytics.
This service encapsulates scouting-related endpoints and business logic.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from datetime import datetime, timezone
import logging

# Import scouting models and components
from backend.scouting_models import (
    ScoutingObservation, 
    ScoutingObservationResponse,
    ScoutingQuery,
    ScoutingAnalytics,
    ObservationType,
    ScrapeDetails,
    RubDetails,
    BeddingDetails,
    TrailCameraDetails,
)
from backend.config_manager import get_config
from backend.scouting_data_manager import get_scouting_data_manager
from backend.scouting_prediction_enhancer import get_scouting_enhancer
from backend.scouting_import.importer import ScoutingImporter

logger = logging.getLogger(__name__)


class ScoutingService:
    """Service for managing scouting observations and analytics."""
    
    def __init__(self):
        """Initialize the scouting service."""
        self._data_manager = get_scouting_data_manager()
        self._enhancer = get_scouting_enhancer()
        self._config = get_config()
    
    async def add_observation(self, observation: ScoutingObservation) -> ScoutingObservationResponse:
        """Add a new scouting observation to enhance future predictions."""
        try:
            logger.info(f"Adding scouting observation: {observation.observation_type} at {observation.lat:.5f}, {observation.lon:.5f}")
            
            # Get data manager
            data_manager = self._data_manager
            
            # Add observation to database
            observation_id = data_manager.add_observation(observation)
            
            # Calculate confidence boost that will be applied
            enhancement_config = self._enhancer.enhancement_config.get(observation.observation_type, {})
            confidence_boost = enhancement_config.get("base_boost", 0) * (observation.confidence / 10.0)

            if (
                observation.observation_type == ObservationType.TRAIL_CAMERA
                and observation.camera_details
                and getattr(observation.camera_details, "mature_buck_seen", False)
            ):
                mature_bonus = enhancement_config.get("mature_buck_bonus", enhancement_config.get("base_boost", 0))
                confidence_boost += mature_bonus * (observation.confidence / 10.0)
            
            logger.info(f"Successfully added scouting observation {observation_id} with {confidence_boost:.1f}% confidence boost")
            
            return ScoutingObservationResponse(
                status="success",
                observation_id=observation_id,
                message=f"Added {observation.observation_type.value} observation - predictions enhanced!",
                confidence_boost=confidence_boost
            )
            
        except Exception as e:
            logger.error(f"Failed to add scouting observation: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to add observation: {str(e)}"
            )
    
    async def get_observations(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 2.0,
        observation_types: Optional[str] = None,
        min_confidence: Optional[int] = None,
        days_back: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get scouting observations within a specified area."""
        try:
            # Parse observation types if provided
            types_list = None
            if observation_types:
                try:
                    type_names = observation_types.split(",")
                    types_list = [ObservationType(name.strip()) for name in type_names]
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=f"Invalid observation type: {e}")
            
            # Create query
            query = ScoutingQuery(
                lat=lat,
                lon=lon,
                radius_miles=radius_miles,
                observation_types=types_list,
                min_confidence=min_confidence,
                days_back=days_back
            )
            
            # Get observations
            data_manager = self._data_manager
            observations = data_manager.get_observations(query)
            
            logger.info(f"Retrieved {len(observations)} scouting observations for area ({lat:.5f}, {lon:.5f})")
            
            # Convert to response format
            obs_data = []
            for obs in observations:
                obs_dict = obs.to_dict()
                # Handle timezone-aware vs timezone-naive datetime comparison
                if obs.timestamp.tzinfo is not None:
                    now = datetime.now(timezone.utc)
                else:
                    now = datetime.now()
                obs_dict["age_days"] = (now - obs.timestamp).days
                obs_data.append(obs_dict)
            
            return {
                "observations": obs_data,
                "total_count": len(obs_data),
                "query_parameters": query.dict()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get scouting observations: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve observations: {str(e)}"
            )
    
    async def get_observation_by_id(self, observation_id: str) -> Dict[str, Any]:
        """Get a specific scouting observation by ID."""
        try:
            observation = self._data_manager.get_observation_by_id(observation_id)
            
            if not observation:
                raise HTTPException(status_code=404, detail="Observation not found")
            
            obs_data = observation.to_dict()
            # Handle timezone-aware vs timezone-naive datetime comparison
            if observation.timestamp.tzinfo is not None:
                now = datetime.now(timezone.utc)
            else:
                now = datetime.now()
            obs_data["age_days"] = (now - observation.timestamp).days
            
            return obs_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get observation {observation_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve observation: {str(e)}"
            )
    
    async def delete_observation(self, observation_id: str) -> Dict[str, str]:
        """Delete a scouting observation."""
        try:
            success = self._data_manager.delete_observation(observation_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Observation not found")
            
            logger.info(f"Deleted scouting observation: {observation_id}")
            
            return {"status": "success", "message": "Observation deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete observation {observation_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete observation: {str(e)}"
            )
    
    async def get_analytics(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 10.0
    ) -> Dict[str, Any]:
        """Get analytics for scouting observations in an area."""
        try:
            analytics = self._data_manager.get_analytics(lat, lon, radius_miles)

            # Get enhancement summary
            enhancement_summary = self._enhancer.get_enhancement_summary(lat, lon)
            
            # Combine analytics
            result = {
                "area_center": {"lat": lat, "lon": lon},
                "search_radius_miles": radius_miles,
                "basic_analytics": analytics.dict(),
                "enhancement_summary": enhancement_summary,
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Generated scouting analytics for area ({lat:.5f}, {lon:.5f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get scouting analytics: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate analytics: {str(e)}"
            )
    
    async def get_observation_types(self) -> Dict[str, Any]:
        """Get list of available observation types with descriptions."""
        try:
            types_info = []
            for obs_type in ObservationType:
                config = self._enhancer.enhancement_config.get(obs_type, {})
                indicator_flag = config.get("mature_buck_indicator", False)
                if obs_type == ObservationType.TRAIL_CAMERA:
                    indicator_flag = True  # Cameras can signal mature bucks when a sighting is confirmed
                
                types_info.append({
                    "type": obs_type.value,
                    "enum_name": obs_type.name,
                    "base_boost": config.get("base_boost", 0),
                    "influence_radius_yards": config.get("influence_radius_yards", 0),
                    "mature_buck_indicator": indicator_flag,
                    "decay_days": config.get("decay_days", 7),
                    "description": self._get_type_description(obs_type)
                })
            
            return {
                "observation_types": types_info,
                "total_types": len(types_info),
                "supported_details": {
                    "scrape": ["depth", "freshness", "diameter"],
                    "rub": ["tree_diameter", "height", "bark_removed"],
                    "bedding": ["bed_count", "cover_density", "escape_routes"],
                    "trail_camera": ["photo_count", "buck_sightings", "time_pattern", "mature_confirmation"]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get observation types: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get observation types: {str(e)}"
            )
    
    def _get_type_description(self, obs_type: ObservationType) -> str:
        """Get human-readable description for observation type."""
        descriptions = {
            ObservationType.DEER_SIGHTING: "Visual deer sighting or encounter",
            ObservationType.DEER_TRACKS: "Deer tracks and hoof prints",
            ObservationType.SCAT_DROPPINGS: "Deer droppings and scat",
            ObservationType.RUB_LINE: "Buck rubs on trees",
            ObservationType.FRESH_SCRAPE: "Buck scrapes and ground sign",
            ObservationType.BEDDING_AREA: "Deer bedding areas",
            ObservationType.FEEDING_SIGN: "Feeding areas and browse sign",
            ObservationType.TRAIL_CAMERA: "Trail camera deployment",
            ObservationType.OTHER_SIGN: "Other deer sign and evidence"
        }
        return descriptions.get(obs_type, "Unknown observation type")

    async def import_scouting_data(
        self,
        file_bytes: bytes,
        *,
        filename: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Import scouting observations from an uploaded GPX file."""

        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        import_config = self._config.get("scouting_import", {}) if self._config else {}

        if not import_config.get("enabled", False):
            raise HTTPException(
                status_code=503,
                detail="Scouting import feature is disabled in configuration",
            )

        importer = ScoutingImporter(
            self._data_manager,
            dedupe_radius_miles=import_config.get("dedupe_radius_miles", 0.15),
            dedupe_time_days=import_config.get("dedupe_time_days", 3650),
            dedupe_time_window_hours=import_config.get("dedupe_time_window_hours", 48),
        )

        summary = importer.import_gpx_bytes(
            file_bytes,
            filename=filename,
            dry_run=dry_run,
        )

        result = summary.to_dict()
        result["configuration"] = {
            "dedupe_radius_miles": importer.dedupe_radius_miles,
            "dedupe_time_days": importer.dedupe_time_days,
            "dedupe_time_window_hours": importer.dedupe_time_window_hours,
        }
        return result
