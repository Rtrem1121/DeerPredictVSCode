#!/usr/bin/env python3
"""
Scouting Data Service (Refactored)

Specialized service for scouting data management and analysis, extracted from
the monolithic PredictionService for better separation of concerns.

Author: System Refactoring
Version: 2.0.0
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from backend.services.base_service import BaseService, Result, AppError, ErrorCode

logger = logging.getLogger(__name__)


@dataclass
class ScoutingObservation:
    """Individual scouting observation"""
    observation_type: str
    lat: float
    lon: float
    timestamp: datetime
    confidence: float
    metadata: Dict[str, Any]


@dataclass 
class ScoutingData:
    """Structured scouting data result"""
    observations: List[ScoutingObservation]
    summary: Dict[str, Any]
    total_count: int
    coverage_area: Optional[Dict[str, float]]


class ScoutingDataService(BaseService):
    """
    Specialized service for scouting data operations
    
    Responsibilities:
    - Scouting data loading and validation
    - Observation filtering and analysis
    - Data quality assessment
    - Spatial clustering of observations
    """
    
    def __init__(self, scouting_data_path: Optional[str] = None):
        super().__init__()
        self.scouting_data_path = scouting_data_path or "backend/data/scouting_data.json"
        self._cached_data: Optional[List[Dict[str, Any]]] = None
        self._cache_timestamp: Optional[datetime] = None
    
    async def load_scouting_data(self, lat: float, lon: float, 
                               radius_km: float = 10.0) -> Result[ScoutingData]:
        """
        Load and filter scouting data for the specified area
        
        Args:
            lat: Center latitude
            lon: Center longitude  
            radius_km: Search radius in kilometers
            
        Returns:
            Result containing ScoutingData or error information
        """
        try:
            self.log_operation_start("load_scouting_data", lat=lat, lon=lon, radius_km=radius_km)
            
            # Validate inputs
            validation_result = self._validate_coordinates(lat, lon)
            if validation_result.is_failure:
                return validation_result
            
            # Load raw data
            raw_data_result = await self._load_raw_scouting_data()
            if raw_data_result.is_failure:
                return raw_data_result
            
            raw_data = raw_data_result.value
            
            # Filter by geographic area
            filtered_observations = self._filter_by_area(raw_data, lat, lon, radius_km)
            
            # Convert to structured observations
            observations = []
            for obs_data in filtered_observations:
                observation = self._create_observation(obs_data)
                if observation:
                    observations.append(observation)
            
            # Generate summary statistics
            summary = self._generate_summary(observations)
            
            # Calculate coverage area
            coverage_area = self._calculate_coverage_area(observations)
            
            scouting_data = ScoutingData(
                observations=observations,
                summary=summary,
                total_count=len(observations),
                coverage_area=coverage_area
            )
            
            self.log_operation_success("load_scouting_data", 
                                     observation_count=len(observations),
                                     coverage_area=coverage_area)
            
            return Result.success(scouting_data)
            
        except Exception as e:
            error = self.handle_unexpected_error("load_scouting_data", e, 
                                                lat=lat, lon=lon, radius_km=radius_km)
            return Result.failure(error)
    
    async def _load_raw_scouting_data(self) -> Result[List[Dict[str, Any]]]:
        """Load raw scouting data from file with caching"""
        try:
            data_path = Path(self.scouting_data_path)
            
            # Check if file exists
            if not data_path.exists():
                return Result.failure(AppError(
                    ErrorCode.SCOUTING_DATA_NOT_FOUND,
                    f"Scouting data file not found: {data_path}",
                    {"path": str(data_path)}
                ))
            
            # Check cache validity
            file_mtime = datetime.fromtimestamp(data_path.stat().st_mtime)
            if (self._cached_data is not None and 
                self._cache_timestamp is not None and 
                file_mtime <= self._cache_timestamp):
                return Result.success(self._cached_data)
            
            # Load from file
            try:
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                return Result.failure(AppError(
                    ErrorCode.SCOUTING_DATA_INVALID,
                    f"Invalid JSON in scouting data file: {str(e)}",
                    {"path": str(data_path), "error": str(e)}
                ))
            
            # Validate data structure
            if not isinstance(data, list):
                return Result.failure(AppError(
                    ErrorCode.SCOUTING_DATA_INVALID,
                    "Scouting data must be a list of observations",
                    {"path": str(data_path), "type": type(data).__name__}
                ))
            
            # Update cache
            self._cached_data = data
            self._cache_timestamp = datetime.now()
            
            return Result.success(data)
            
        except Exception as e:
            return Result.failure(AppError(
                ErrorCode.SCOUTING_DATA_LOAD_FAILED,
                f"Failed to load scouting data: {str(e)}",
                {"path": self.scouting_data_path, "exception_type": type(e).__name__}
            ))
    
    def _filter_by_area(self, data: List[Dict[str, Any]], 
                       center_lat: float, center_lon: float, 
                       radius_km: float) -> List[Dict[str, Any]]:
        """Filter observations by geographic area"""
        filtered = []
        
        for observation in data:
            obs_lat = observation.get('lat')
            obs_lon = observation.get('lon')
            
            if obs_lat is None or obs_lon is None:
                continue
            
            # Calculate distance (simplified Haversine)
            distance = self._calculate_distance(center_lat, center_lon, obs_lat, obs_lon)
            
            if distance <= radius_km:
                filtered.append(observation)
        
        return filtered
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        import math
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        earth_radius_km = 6371.0
        
        return earth_radius_km * c
    
    def _create_observation(self, obs_data: Dict[str, Any]) -> Optional[ScoutingObservation]:
        """Create a structured observation from raw data"""
        try:
            # Extract required fields
            observation_type = obs_data.get('type', 'unknown')
            lat = obs_data.get('lat')
            lon = obs_data.get('lon')
            timestamp_str = obs_data.get('timestamp')
            confidence = obs_data.get('confidence', 0.5)
            
            # Validate required fields
            if lat is None or lon is None:
                return None
            
            # Parse timestamp
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Create metadata dict from remaining fields
            metadata = {k: v for k, v in obs_data.items() 
                       if k not in ['type', 'lat', 'lon', 'timestamp', 'confidence']}
            
            return ScoutingObservation(
                observation_type=observation_type,
                lat=float(lat),
                lon=float(lon),
                timestamp=timestamp,
                confidence=float(confidence),
                metadata=metadata
            )
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Invalid observation data: {e}")
            return None
    
    def _generate_summary(self, observations: List[ScoutingObservation]) -> Dict[str, Any]:
        """Generate summary statistics from observations"""
        if not observations:
            return {
                "total_observations": 0,
                "observation_types": {},
                "average_confidence": 0.0,
                "date_range": None
            }
        
        # Count observation types
        type_counts = {}
        total_confidence = 0.0
        timestamps = []
        
        for obs in observations:
            type_counts[obs.observation_type] = type_counts.get(obs.observation_type, 0) + 1
            total_confidence += obs.confidence
            timestamps.append(obs.timestamp)
        
        # Calculate date range
        if timestamps:
            min_date = min(timestamps)
            max_date = max(timestamps)
            date_range = {
                "earliest": min_date.isoformat(),
                "latest": max_date.isoformat(),
                "span_days": (max_date - min_date).days
            }
        else:
            date_range = None
        
        return {
            "total_observations": len(observations),
            "observation_types": type_counts,
            "average_confidence": total_confidence / len(observations),
            "date_range": date_range
        }
    
    def _calculate_coverage_area(self, observations: List[ScoutingObservation]) -> Optional[Dict[str, float]]:
        """Calculate the geographic coverage area of observations"""
        if len(observations) < 2:
            return None
        
        lats = [obs.lat for obs in observations]
        lons = [obs.lon for obs in observations]
        
        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons),
            "center_lat": sum(lats) / len(lats),
            "center_lon": sum(lons) / len(lons)
        }
    
    def _validate_coordinates(self, lat: float, lon: float) -> Result[None]:
        """Validate coordinate inputs"""
        if not (-90 <= lat <= 90):
            return Result.failure(AppError(
                ErrorCode.INVALID_COORDINATES,
                f"Invalid latitude: {lat}",
                {"lat": lat, "lon": lon}
            ))
        
        if not (-180 <= lon <= 180):
            return Result.failure(AppError(
                ErrorCode.INVALID_COORDINATES,
                f"Invalid longitude: {lon}",
                {"lat": lat, "lon": lon}
            ))
        
        return Result.success(None)
    
    async def get_observation_types(self) -> Result[List[str]]:
        """Get all available observation types from the dataset"""
        try:
            raw_data_result = await self._load_raw_scouting_data()
            if raw_data_result.is_failure:
                return raw_data_result
            
            raw_data = raw_data_result.value
            observation_types = set()
            
            for obs in raw_data:
                obs_type = obs.get('type')
                if obs_type:
                    observation_types.add(obs_type)
            
            return Result.success(sorted(list(observation_types)))
            
        except Exception as e:
            error = self.handle_unexpected_error("get_observation_types", e)
            return Result.failure(error)


# Factory function for dependency injection
def create_scouting_data_service() -> ScoutingDataService:
    """Create a new ScoutingDataService instance"""
    return ScoutingDataService()
