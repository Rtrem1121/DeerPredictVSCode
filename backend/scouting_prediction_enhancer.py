#!/usr/bin/env python3
"""
Scouting Prediction Enhancer

Enhances mature buck predictions using real-world scouting observation data.
Applies confidence boosts and pattern learning based on confirmed deer sign.

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import numpy as np
import logging
import math
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta

try:
    from .scouting_models import ScoutingObservation, ObservationType
    from .scouting_data_manager import get_scouting_data_manager
except ImportError:
    from scouting_models import ScoutingObservation, ObservationType
    from scouting_data_manager import get_scouting_data_manager

logger = logging.getLogger(__name__)


class ScoutingPredictionEnhancer:
    """Enhances predictions using scouting observation data"""
    
    def __init__(self):
        self.data_manager = get_scouting_data_manager()
        
        # Enhancement parameters for different observation types
        self.enhancement_config = {
            ObservationType.FRESH_SCRAPE: {
                "base_boost": 20.0,  # Base confidence boost percentage
                "influence_radius_yards": 200,  # Influence radius in yards
                "bedding_boost": 15.0,  # Additional boost to nearby bedding areas
                "travel_boost": 10.0,   # Additional boost to travel corridors
                "decay_days": 14,       # How long enhancement lasts
                "mature_buck_indicator": True  # Strong indicator of mature buck presence
            },
            ObservationType.RUB_LINE: {
                "base_boost": 18.0,
                "influence_radius_yards": 150,
                "travel_boost": 25.0,   # Strong travel corridor indicator
                "bedding_boost": 8.0,
                "decay_days": 21,       # Rubs last longer than scrapes
                "mature_buck_indicator": True
            },
            ObservationType.BEDDING_AREA: {
                "base_boost": 25.0,
                "influence_radius_yards": 300,
                "bedding_boost": 30.0,  # Major bedding area boost
                "travel_boost": 5.0,
                "decay_days": 30,       # Bedding areas are more permanent
                "mature_buck_indicator": False  # Could be any deer
            },
            ObservationType.TRAIL_CAMERA: {
                "base_boost": 15.0,
                "influence_radius_yards": 100,
                "travel_boost": 20.0,
                "bedding_boost": 5.0,
                "decay_days": 7,        # Camera data is time-sensitive
                "mature_buck_indicator": False  # Depends on camera data
            },
            ObservationType.DEER_TRACKS: {
                "base_boost": 8.0,
                "influence_radius_yards": 100,
                "travel_boost": 15.0,
                "bedding_boost": 3.0,
                "decay_days": 3,        # Tracks fade quickly
                "mature_buck_indicator": False
            },
            ObservationType.FEEDING_SIGN: {
                "base_boost": 12.0,
                "influence_radius_yards": 150,
                "travel_boost": 5.0,
                "bedding_boost": 2.0,
                "decay_days": 7,
                "mature_buck_indicator": False
            }
        }
    
    def enhance_predictions(self, 
                          lat: float, 
                          lon: float, 
                          score_maps: Dict[str, np.ndarray],
                          span_deg: float = 0.04,
                          grid_size: int = 10) -> Dict[str, Any]:
        """
        Enhance prediction score maps using scouting data
        
        Args:
            lat: Center latitude
            lon: Center longitude  
            score_maps: Dictionary of score maps (travel, bedding, feeding)
            span_deg: Degree span of the prediction area
            grid_size: Grid size for predictions
            
        Returns:
            Enhancement results and boosted score maps
        """
        try:
            observations = self._get_relevant_observations(lat, lon)
            if not observations:
                logger.info("No scouting observations found for enhancement")
                return self._default_enhancement_result(score_maps)

            logger.info(f"Found {len(observations)} scouting observations for enhancement")
            
            enhanced_maps = self._prepare_enhanced_maps(score_maps)
            
            enhancements_applied, mature_buck_indicators = self._apply_enhancements(
                observations, enhanced_maps, lat, lon, span_deg, grid_size
            )
            
            cumulative_bonus = self._apply_cumulative_bonuses(enhanced_maps, mature_buck_indicators)
            
            return {
                "enhanced_score_maps": enhanced_maps,
                "enhancements_applied": enhancements_applied,
                "total_boost_points": sum(e["boost_applied"] for e in enhancements_applied),
                "mature_buck_indicators": mature_buck_indicators,
                "cumulative_bonus": cumulative_bonus
            }
            
        except Exception as e:
            logger.error(f"Failed to enhance predictions: {e}")
            return self._default_enhancement_result(score_maps, error=str(e))

    def _get_relevant_observations(self, lat: float, lon: float) -> List[ScoutingObservation]:
        """Get relevant scouting observations for the given area."""
        from .scouting_models import ScoutingQuery
        query = ScoutingQuery(
            lat=lat,
            lon=lon,
            radius_miles=2.0,  # Search within 2 miles
            days_back=60       # Only use recent observations
        )
        return self.data_manager.get_observations(query)

    def _prepare_enhanced_maps(self, score_maps: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Create copies of the score maps to be enhanced."""
        return {
            "travel": score_maps["travel"].copy(),
            "bedding": score_maps["bedding"].copy(), 
            "feeding": score_maps["feeding"].copy()
        }

    def _apply_enhancements(self, observations: List[ScoutingObservation], enhanced_maps: Dict[str, np.ndarray], lat: float, lon: float, span_deg: float, grid_size: int) -> Tuple[List[Dict[str, Any]], int]:
        """Apply enhancements for each observation."""
        enhancements_applied = []
        mature_buck_indicators = 0
        for obs in observations:
            try:
                enhancement = self._apply_observation_enhancement(
                    obs, enhanced_maps, lat, lon, span_deg, grid_size
                )
                
                if enhancement:
                    enhancements_applied.append(enhancement)
                    if enhancement["mature_buck_indicator"]:
                        mature_buck_indicators += 1
                        
            except Exception as e:
                logger.warning(f"Failed to apply enhancement for observation {obs.id}: {e}")
                continue
        return enhancements_applied, mature_buck_indicators

    def _apply_cumulative_bonuses(self, enhanced_maps: Dict[str, np.ndarray], mature_buck_indicators: int) -> float:
        """Apply cumulative bonuses for multiple mature buck indicators."""
        cumulative_bonus = 0
        if mature_buck_indicators >= 2:
            cumulative_bonus = min(10.0, mature_buck_indicators * 2.0)
            self._apply_cumulative_bonus(enhanced_maps, cumulative_bonus)
            logger.info(f"Applied cumulative bonus: {cumulative_bonus}% for {mature_buck_indicators} mature buck indicators")
        return cumulative_bonus

    def _default_enhancement_result(self, score_maps: Dict[str, np.ndarray], error: Optional[str] = None) -> Dict[str, Any]:
        """Return a default enhancement result when no enhancements are applied."""
        result = {
            "enhanced_score_maps": score_maps,
            "enhancements_applied": [],
            "total_boost_points": 0,
            "mature_buck_indicators": 0,
            "cumulative_bonus": 0
        }
        if error:
            result["error"] = error
        return result
    
    def _apply_observation_enhancement(self,
                                     obs: ScoutingObservation,
                                     score_maps: Dict[str, np.ndarray],
                                     center_lat: float,
                                     center_lon: float,
                                     span_deg: float,
                                     grid_size: int) -> Optional[Dict[str, Any]]:
        """Apply enhancement for a single observation"""
        
        try:
            config = self.enhancement_config.get(obs.observation_type)
            if not config:
                logger.warning(f"No enhancement config for {obs.observation_type}")
                return None
            
            # Calculate age decay factor
            age_days = (datetime.now() - obs.timestamp).days
            decay_factor = max(0.1, 1.0 - (age_days / config["decay_days"]))
            
            # Calculate confidence factor
            confidence_factor = obs.confidence / 10.0
            
            # Calculate base enhancement strength
            base_boost = config["base_boost"] * decay_factor * confidence_factor
            
            # Convert observation coordinates to grid coordinates
            grid_row, grid_col = self._lat_lon_to_grid(
                obs.lat, obs.lon, center_lat, center_lon, span_deg, grid_size
            )
            
            if not self._is_valid_grid_position(grid_row, grid_col, grid_size):
                logger.debug(f"Observation {obs.id} outside grid area")
                return None
            
            # Calculate influence radius in grid cells
            yards_per_degree = 69 * 1760  # Approximate yards per degree latitude
            degrees_per_yard = 1.0 / yards_per_degree
            radius_degrees = config["influence_radius_yards"] * degrees_per_yard
            radius_cells = (radius_degrees / span_deg) * grid_size
            
            # Apply enhancements to score maps
            total_boost = 0
            
            # Apply to travel corridors
            if config["travel_boost"] > 0:
                travel_boost = config["travel_boost"] * decay_factor * confidence_factor
                boost_applied = self._apply_radial_boost(
                    score_maps["travel"], grid_row, grid_col, radius_cells, travel_boost
                )
                total_boost += boost_applied
            
            # Apply to bedding areas
            if config["bedding_boost"] > 0:
                bedding_boost = config["bedding_boost"] * decay_factor * confidence_factor
                boost_applied = self._apply_radial_boost(
                    score_maps["bedding"], grid_row, grid_col, radius_cells, bedding_boost
                )
                total_boost += boost_applied
            
            # Apply specific enhancements based on observation type
            total_boost += self._apply_type_specific_enhancements(
                obs, score_maps, grid_row, grid_col, radius_cells, config, decay_factor, confidence_factor
            )
            
            logger.debug(f"Applied enhancement for {obs.observation_type} at grid ({grid_row}, {grid_col}): {total_boost:.1f}% boost")
            
            return {
                "observation_id": obs.id,
                "observation_type": obs.observation_type.value,
                "boost_applied": total_boost,
                "decay_factor": decay_factor,
                "confidence_factor": confidence_factor,
                "age_days": age_days,
                "grid_position": (grid_row, grid_col),
                "mature_buck_indicator": config["mature_buck_indicator"]
            }
            
        except Exception as e:
            logger.error(f"Error applying enhancement for observation {obs.id}: {e}")
            return None
    
    def _apply_radial_boost(self,
                           score_map: np.ndarray,
                           center_row: int,
                           center_col: int,
                           radius_cells: float,
                           boost_percent: float) -> float:
        """Apply radial boost to score map around a center point"""
        
        rows, cols = score_map.shape
        total_boost_applied = 0
        cells_boosted = 0
        
        # Create coordinate grids
        row_indices, col_indices = np.ogrid[:rows, :cols]
        
        # Calculate distances from center
        distances = np.sqrt((row_indices - center_row)**2 + (col_indices - center_col)**2)
        
        # Create mask for cells within radius
        within_radius = distances <= radius_cells
        
        # Calculate distance-based boost (stronger near center)
        boost_strength = np.where(
            within_radius,
            boost_percent * (1.0 - distances / radius_cells),
            0
        )
        
        # Apply boost
        original_scores = score_map.copy()
        score_map += boost_strength
        
        # Clamp to maximum of 10
        score_map = np.minimum(score_map, 10.0)
        
        # Calculate actual boost applied
        boost_applied = np.sum(score_map - original_scores)
        cells_boosted = np.sum(within_radius)
        
        return boost_applied
    
    def _apply_type_specific_enhancements(self,
                                        obs: ScoutingObservation,
                                        score_maps: Dict[str, np.ndarray],
                                        grid_row: int,
                                        grid_col: int,
                                        radius_cells: float,
                                        config: Dict[str, Any],
                                        decay_factor: float,
                                        confidence_factor: float) -> float:
        """Apply observation-type specific enhancements"""
        
        total_boost = 0
        
        if obs.observation_type == ObservationType.FRESH_SCRAPE:
            total_boost += self._apply_scrape_enhancement(obs, score_maps, grid_row, grid_col, radius_cells, config, decay_factor, confidence_factor)
        elif obs.observation_type == ObservationType.RUB_LINE:
            total_boost += self._apply_rub_line_enhancement(obs, score_maps, grid_row, grid_col, radius_cells, config, decay_factor, confidence_factor)
        elif obs.observation_type == ObservationType.TRAIL_CAMERA:
            total_boost += self._apply_trail_camera_enhancement(obs, score_maps, grid_row, grid_col, radius_cells, config, decay_factor, confidence_factor)
        
        return total_boost

    def _apply_scrape_enhancement(self, obs: ScoutingObservation, score_maps: Dict[str, np.ndarray], grid_row: int, grid_col: int, radius_cells: float, config: Dict[str, Any], decay_factor: float, confidence_factor: float) -> float:
        """Apply scrape-specific enhancements."""
        details = obs.scrape_details
        if not details:
            return 0

        size_multiplier = {
            "Small": 0.7,
            "Medium": 1.0,
            "Large": 1.3,
            "Huge": 1.6
        }.get(details.size, 1.0)
        
        freshness_multiplier = {
            "Old": 0.5,
            "Recent": 0.8,
            "Fresh": 1.0,
            "Very Fresh": 1.3
        }.get(details.freshness, 1.0)
        
        licking_bonus = 1.2 if details.licking_branch else 1.0
        
        enhanced_boost = (config["base_boost"] * size_multiplier * 
                        freshness_multiplier * licking_bonus * 
                        decay_factor * confidence_factor)
        
        return self._apply_radial_boost(
            score_maps["bedding"], grid_row, grid_col, 
            radius_cells * 0.7, enhanced_boost * 0.5
        )

    def _apply_rub_line_enhancement(self, obs: ScoutingObservation, score_maps: Dict[str, np.ndarray], grid_row: int, grid_col: int, radius_cells: float, config: Dict[str, Any], decay_factor: float, confidence_factor: float) -> float:
        """Apply rub-line-specific enhancements."""
        details = obs.rub_details
        if not details:
            return 0

        if details.tree_diameter_inches >= 8:
            mature_buck_bonus = 1.4
        else:
            mature_buck_bonus = 1.0
        
        if details.rub_height_inches >= 36:
            height_bonus = 1.3
        else:
            height_bonus = 1.0
        
        enhanced_boost = (config["travel_boost"] * mature_buck_bonus * 
                        height_bonus * decay_factor * confidence_factor)
        
        return self._apply_radial_boost(
            score_maps["travel"], grid_row, grid_col,
            radius_cells, enhanced_boost
        )

    def _apply_trail_camera_enhancement(self, obs: ScoutingObservation, score_maps: Dict[str, np.ndarray], grid_row: int, grid_col: int, radius_cells: float, config: Dict[str, Any], decay_factor: float, confidence_factor: float) -> float:
        """Apply trail-camera-specific enhancements."""
        details = obs.camera_details
        if not (details and details.mature_buck_photos > 0 and details.deer_photos > 0):
            return 0

        mature_ratio = details.mature_buck_photos / details.deer_photos
        mature_bonus = 1.0 + (mature_ratio * 2.0)  # Up to 3x boost
        
        enhanced_boost = (config["base_boost"] * mature_bonus * 
                        decay_factor * confidence_factor)
        
        return self._apply_radial_boost(
            score_maps["travel"], grid_row, grid_col,
            radius_cells * 0.5, enhanced_boost
        )
    
    def _apply_cumulative_bonus(self, score_maps: Dict[str, np.ndarray], bonus_percent: float) -> None:
        """Apply cumulative bonus for multiple mature buck indicators"""
        for map_name in score_maps:
            # Apply small global boost
            score_maps[map_name] += bonus_percent * 0.1
            # Clamp to maximum
            score_maps[map_name] = np.minimum(score_maps[map_name], 10.0)
    
    def _lat_lon_to_grid(self, 
                        obs_lat: float, 
                        obs_lon: float,
                        center_lat: float, 
                        center_lon: float,
                        span_deg: float, 
                        grid_size: int) -> Tuple[int, int]:
        """Convert lat/lon coordinates to grid coordinates"""
        
        # Calculate relative position within the grid area
        lat_offset = obs_lat - (center_lat - span_deg / 2)
        lon_offset = obs_lon - (center_lon - span_deg / 2)
        
        # Convert to grid coordinates
        grid_row = int((lat_offset / span_deg) * grid_size)
        grid_col = int((lon_offset / span_deg) * grid_size)
        
        return grid_row, grid_col
    
    def _is_valid_grid_position(self, row: int, col: int, grid_size: int) -> bool:
        """Check if grid position is valid"""
        return 0 <= row < grid_size and 0 <= col < grid_size
    
    def get_enhancement_summary(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get summary of enhancements for an area"""
        try:
            try:
                from .scouting_models import ScoutingQuery
            except ImportError:
                from scouting_models import ScoutingQuery
            query = ScoutingQuery(lat=lat, lon=lon, radius_miles=1.0, days_back=30)
            observations = self.data_manager.get_observations(query)
            
            summary = {
                "total_observations": len(observations),
                "by_type": {},
                "mature_buck_indicators": 0,
                "avg_confidence": 0.0,
                "recent_activity": []
            }
            
            if observations:
                for obs in observations:
                    obs_type = obs.observation_type.value
                    summary["by_type"][obs_type] = summary["by_type"].get(obs_type, 0) + 1
                    
                    config = self.enhancement_config.get(obs.observation_type, {})
                    if config.get("mature_buck_indicator"):
                        summary["mature_buck_indicators"] += 1
                
                summary["avg_confidence"] = sum(obs.confidence for obs in observations) / len(observations)
                
                # Recent activity (last 7 days)
                recent_cutoff = datetime.now() - timedelta(days=7)
                summary["recent_activity"] = [
                    {
                        "type": obs.observation_type.value,
                        "date": obs.timestamp.date().isoformat(),
                        "confidence": obs.confidence,
                        "distance_miles": self._calculate_distance_miles(obs.lat, obs.lon, lat, lon)
                    }
                    for obs in observations 
                    if obs.timestamp >= recent_cutoff
                ]
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get enhancement summary: {e}")
            return {"error": str(e)}
    
    def _calculate_distance_miles(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in miles"""
        # Haversine formula (simplified for small distances)
        R = 3959  # Earth's radius in miles
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c


# Global instance
_scouting_enhancer = None

def get_scouting_enhancer() -> ScoutingPredictionEnhancer:
    """Get the global scouting prediction enhancer instance"""
    global _scouting_enhancer
    if _scouting_enhancer is None:
        _scouting_enhancer = ScoutingPredictionEnhancer()
    return _scouting_enhancer
