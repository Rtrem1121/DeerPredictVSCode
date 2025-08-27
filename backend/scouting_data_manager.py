#!/usr/bin/env python3
"""
Scouting Data Manager

Handles storage, retrieval, and management of scouting observation data.
Uses JSON file storage initially with support for future database migration.

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import json
import os
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import math
from threading import Lock

try:
    from .scouting_models import (
        ScoutingObservation, 
        ObservationType,
        ScoutingQuery,
        ScoutingAnalytics
    )
except ImportError:
    from scouting_models import (
        ScoutingObservation, 
        ObservationType,
        ScoutingQuery,
        ScoutingAnalytics
    )

logger = logging.getLogger(__name__)


class ScoutingDataManager:
    """Manages scouting observation data storage and retrieval"""
    
    def __init__(self, data_file: str = "data/scouting_observations.json"):
        self.data_file = Path(data_file)
        self.data_lock = Lock()  # Thread safety for concurrent access
        self._ensure_data_directory()
        self._initialize_data_file()
    
    def _ensure_data_directory(self) -> None:
        """Ensure the data directory exists"""
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Data directory ensured: {self.data_file.parent}")
        except Exception as e:
            logger.error(f"Failed to create data directory: {e}")
            raise
    
    def _initialize_data_file(self) -> None:
        """Initialize data file if it doesn't exist"""
        if not self.data_file.exists():
            try:
                initial_data = {
                    "version": "1.0.0",
                    "created": datetime.now().isoformat(),
                    "observations": [],
                    "metadata": {
                        "total_observations": 0,
                        "last_updated": None
                    }
                }
                with open(self.data_file, 'w') as f:
                    json.dump(initial_data, f, indent=2)
                logger.info(f"Initialized scouting data file: {self.data_file}")
            except Exception as e:
                logger.error(f"Failed to initialize data file: {e}")
                raise
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from file with error handling"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            logger.warning(f"Data file not found: {self.data_file}")
            self._initialize_data_file()
            return self._load_data()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in data file: {e}")
            # Backup corrupted file and reinitialize
            backup_file = f"{self.data_file}.backup.{int(datetime.now().timestamp())}"
            os.rename(self.data_file, backup_file)
            logger.info(f"Backed up corrupted file to: {backup_file}")
            self._initialize_data_file()
            return self._load_data()
        except Exception as e:
            logger.error(f"Unexpected error loading data: {e}")
            raise
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save data to file with atomic write"""
        try:
            # Update metadata
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            data["metadata"]["total_observations"] = len(data.get("observations", []))
            
            # Atomic write using temporary file
            temp_file = f"{self.data_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Replace original file atomically
            os.replace(temp_file, self.data_file)
            logger.debug(f"Saved {len(data.get('observations', []))} observations to file")
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            # Clean up temp file if it exists
            if os.path.exists(f"{self.data_file}.tmp"):
                os.remove(f"{self.data_file}.tmp")
            raise
    
    def add_observation(self, observation: ScoutingObservation) -> str:
        """Add a new scouting observation"""
        with self.data_lock:
            try:
                # Generate unique ID if not provided
                if not observation.id:
                    observation.id = self._generate_observation_id()
                
                # Load existing data
                data = self._load_data()
                
                # Convert observation to dict and add
                obs_dict = observation.to_dict()
                data["observations"].append(obs_dict)
                
                # Save updated data
                self._save_data(data)
                
                logger.info(f"Added scouting observation: {observation.observation_type} at "
                           f"{observation.lat:.5f}, {observation.lon:.5f}")
                
                return observation.id
                
            except Exception as e:
                logger.error(f"Failed to add observation: {e}")
                raise
    
    def get_observations(self, query: ScoutingQuery) -> List[ScoutingObservation]:
        """Get observations matching query parameters"""
        try:
            data = self._load_data()
            observations = []
            
            for obs_dict in data.get("observations", []):
                try:
                    obs = ScoutingObservation.from_dict(obs_dict)
                    
                    # Apply filters
                    if not self._matches_query(obs, query):
                        continue
                    
                    observations.append(obs)
                    
                except Exception as e:
                    logger.warning(f"Skipping invalid observation: {e}")
                    continue
            
            # Sort by timestamp (most recent first)
            observations.sort(key=lambda x: x.timestamp, reverse=True)
            
            logger.info(f"Retrieved {len(observations)} observations for query")
            return observations
            
        except Exception as e:
            logger.error(f"Failed to get observations: {e}")
            return []
    
    def get_observation_by_id(self, observation_id: str) -> Optional[ScoutingObservation]:
        """Get a specific observation by ID"""
        try:
            data = self._load_data()
            
            for obs_dict in data.get("observations", []):
                if obs_dict.get("id") == observation_id:
                    return ScoutingObservation.from_dict(obs_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get observation {observation_id}: {e}")
            return None
    
    def update_observation(self, observation: ScoutingObservation) -> bool:
        """Update an existing observation"""
        with self.data_lock:
            try:
                data = self._load_data()
                
                # Find and update observation
                for i, obs_dict in enumerate(data.get("observations", [])):
                    if obs_dict.get("id") == observation.id:
                        data["observations"][i] = observation.to_dict()
                        self._save_data(data)
                        logger.info(f"Updated observation: {observation.id}")
                        return True
                
                logger.warning(f"Observation not found for update: {observation.id}")
                return False
                
            except Exception as e:
                logger.error(f"Failed to update observation: {e}")
                return False
    
    def delete_observation(self, observation_id: str) -> bool:
        """Delete an observation by ID"""
        with self.data_lock:
            try:
                data = self._load_data()
                original_count = len(data.get("observations", []))
                
                # Filter out the observation to delete
                data["observations"] = [
                    obs for obs in data.get("observations", [])
                    if obs.get("id") != observation_id
                ]
                
                if len(data["observations"]) < original_count:
                    self._save_data(data)
                    logger.info(f"Deleted observation: {observation_id}")
                    return True
                else:
                    logger.warning(f"Observation not found for deletion: {observation_id}")
                    return False
                
            except Exception as e:
                logger.error(f"Failed to delete observation: {e}")
                return False
    
    def get_analytics(self, lat: float, lon: float, radius_miles: float = 10.0) -> ScoutingAnalytics:
        """Get analytics for observations in an area"""
        try:
            query = ScoutingQuery(lat=lat, lon=lon, radius_miles=radius_miles)
            observations = self.get_observations(query)
            
            if not observations:
                return ScoutingAnalytics(
                    total_observations=0,
                    observations_by_type={},
                    average_confidence=0.0
                )
            
            return self._calculate_analytics_metrics(observations)
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return ScoutingAnalytics(
                total_observations=0,
                observations_by_type={},
                average_confidence=0.0
            )

    def _calculate_analytics_metrics(self, observations: List[ScoutingObservation]) -> ScoutingAnalytics:
        """Calculate analytics metrics from a list of observations."""
        total_obs = len(observations)
        obs_by_type = {}
        total_confidence = 0
        
        for obs in observations:
            obs_type = obs.observation_type.value
            obs_by_type[obs_type] = obs_by_type.get(obs_type, 0) + 1
            total_confidence += obs.confidence
        
        avg_confidence = total_confidence / total_obs if total_obs > 0 else 0.0
        most_recent = max(obs.timestamp for obs in observations) if observations else None
        
        hottest_areas = self._find_hottest_areas(observations)
        
        return ScoutingAnalytics(
            total_observations=total_obs,
            observations_by_type=obs_by_type,
            average_confidence=avg_confidence,
            most_recent_observation=most_recent,
            hottest_areas=hottest_areas
        )
    
    def _generate_observation_id(self) -> str:
        """Generate a unique observation ID"""
        timestamp = int(datetime.now().timestamp())
        unique_id = uuid.uuid4().hex[:8]
        return f"obs_{timestamp}_{unique_id}"
    
    def _matches_query(self, observation: ScoutingObservation, query: ScoutingQuery) -> bool:
        """Check if observation matches query parameters"""
        if not self._matches_distance(observation, query):
            return False
        if not self._matches_type(observation, query):
            return False
        if not self._matches_confidence(observation, query):
            return False
        if not self._matches_date(observation, query):
            return False
        return True

    def _matches_distance(self, observation: ScoutingObservation, query: ScoutingQuery) -> bool:
        """Check if observation is within the query radius"""
        distance = self._calculate_distance(
            observation.lat, observation.lon, query.lat, query.lon
        )
        return distance <= query.radius_miles

    def _matches_type(self, observation: ScoutingObservation, query: ScoutingQuery) -> bool:
        """Check if observation matches the query type"""
        if query.observation_types and observation.observation_type not in query.observation_types:
            return False
        return True

    def _matches_confidence(self, observation: ScoutingObservation, query: ScoutingQuery) -> bool:
        """Check if observation meets the minimum confidence"""
        if query.min_confidence and observation.confidence < query.min_confidence:
            return False
        return True

    def _matches_date(self, observation: ScoutingObservation, query: ScoutingQuery) -> bool:
        """Check if observation is within the date range"""
        if query.days_back:
            # Handle timezone-aware vs timezone-naive datetime comparison
            if observation.timestamp.tzinfo is not None:
                # observation.timestamp is timezone-aware, make cutoff_date timezone-aware too
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=query.days_back)
            else:
                # observation.timestamp is timezone-naive, use naive cutoff_date
                cutoff_date = datetime.now() - timedelta(days=query.days_back)
                
            if observation.timestamp < cutoff_date:
                return False
        return True
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in miles"""
        # Haversine formula
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _find_hottest_areas(self, observations: List[ScoutingObservation]) -> List[Dict[str, Any]]:
        """Find areas with highest concentration of observations"""
        observation_groups = self._group_observations(observations)
        hot_areas = []
        for group in observation_groups:
            if len(group) >= 2:
                hot_areas.append(self._calculate_hot_area(group))
        
        # Sort by observation count and confidence
        hot_areas.sort(key=lambda x: (x["observation_count"], x["average_confidence"]), reverse=True)
        return hot_areas[:5]  # Top 5 hottest areas

    def _group_observations(self, observations: List[ScoutingObservation]) -> List[List[ScoutingObservation]]:
        """Group observations by proximity."""
        groups = []
        processed = set()
        for i, obs in enumerate(observations):
            if i in processed:
                continue
            
            # Find nearby observations
            nearby = [obs]
            processed.add(i)
            
            for j, other_obs in enumerate(observations[i+1:], i+1):
                if j in processed:
                    continue
                
                distance = self._calculate_distance(
                    obs.lat, obs.lon, other_obs.lat, other_obs.lon
                )
                
                if distance <= 0.25:  # Within quarter mile
                    nearby.append(other_obs)
                    processed.add(j)
            groups.append(nearby)
        return groups

    def _calculate_hot_area(self, group: List[ScoutingObservation]) -> Dict[str, Any]:
        """Calculate the details of a hot area from a group of observations."""
        avg_lat = sum(o.lat for o in group) / len(group)
        avg_lon = sum(o.lon for o in group) / len(group)
        avg_confidence = sum(o.confidence for o in group) / len(group)
        
        return {
            "lat": avg_lat,
            "lon": avg_lon,
            "observation_count": len(group),
            "average_confidence": avg_confidence,
            "types": list(set(o.observation_type.value for o in group))
        }


# Global instance
_scouting_data_manager = None

def get_scouting_data_manager() -> ScoutingDataManager:
    """Get the global scouting data manager instance"""
    global _scouting_data_manager
    if _scouting_data_manager is None:
        _scouting_data_manager = ScoutingDataManager()
    return _scouting_data_manager
