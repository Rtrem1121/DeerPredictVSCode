#!/usr/bin/env python3
"""
Terrain Analysis Service

Specialized service for terrain and elevation analysis, extracted from the
monolithic PredictionService to improve maintainability and testability.

Author: System Refactoring
Version: 2.0.0
"""

import logging
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass

from backend import core
from backend.services.base_service import BaseService, Result, AppError, ErrorCode

logger = logging.getLogger(__name__)


@dataclass
class TerrainData:
    """Structured terrain analysis result"""
    elevation_grid: np.ndarray
    vegetation_grid: np.ndarray
    features: Dict[str, Any]
    slope_analysis: Dict[str, float]
    aspect_analysis: Dict[str, float]
    terrain_roughness: float


class TerrainAnalysisService(BaseService):
    """
    Specialized service for terrain analysis operations
    
    Responsibilities:
    - Elevation grid retrieval and processing
    - Vegetation analysis from OSM data
    - Slope and aspect calculations
    - Terrain feature extraction
    """
    
    def __init__(self, core_module=None):
        super().__init__()
        self.core = core_module or core
        self.logger = logging.getLogger(__name__)
    
    async def analyze_terrain(self, lat: float, lon: float, fast_mode: bool = False) -> Result[TerrainData]:
        """
        Comprehensive terrain analysis for given coordinates
        
        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            fast_mode: Skip expensive calculations for speed
            
        Returns:
            Result containing TerrainData or error information
        """
        try:
            # Validate coordinates
            validation_result = self._validate_coordinates(lat, lon)
            if validation_result.is_failure:
                return validation_result
            
            self.logger.info(f"Starting terrain analysis for {lat:.6f}, {lon:.6f}")
            
            # Get elevation and vegetation grids
            elevation_result = await self._get_elevation_grid(lat, lon)
            if elevation_result.is_failure:
                return elevation_result
            
            vegetation_result = await self._get_vegetation_grid(lat, lon)
            if vegetation_result.is_failure:
                return vegetation_result
            
            # Perform terrain feature analysis
            features_result = await self._analyze_terrain_features(
                elevation_result.value, vegetation_result.value, fast_mode
            )
            if features_result.is_failure:
                return features_result
            
            # Calculate slope and aspect if not in fast mode
            slope_analysis = {}
            aspect_analysis = {}
            terrain_roughness = 0.0
            
            if not fast_mode:
                slope_analysis = self._calculate_slope_metrics(elevation_result.value)
                aspect_analysis = self._calculate_aspect_metrics(elevation_result.value)
                terrain_roughness = self._calculate_terrain_roughness(elevation_result.value)
            
            terrain_data = TerrainData(
                elevation_grid=elevation_result.value,
                vegetation_grid=vegetation_result.value,
                features=features_result.value,
                slope_analysis=slope_analysis,
                aspect_analysis=aspect_analysis,
                terrain_roughness=terrain_roughness
            )
            
            self.logger.info(f"Terrain analysis completed for {lat:.6f}, {lon:.6f}")
            return Result(value=terrain_data)
            
        except Exception as e:
            self.logger.exception("Unexpected error in terrain analysis")
            return Result(error=AppError(
                ErrorCode.TERRAIN_ANALYSIS_FAILED,
                f"Terrain analysis failed: {str(e)}",
                {"lat": lat, "lon": lon, "exception_type": type(e).__name__}
            ))
    
    async def _get_elevation_grid(self, lat: float, lon: float) -> Result[np.ndarray]:
        """Get elevation grid for the specified location"""
        try:
            elevation_grid = self.core.get_real_elevation_grid(lat, lon)
            if elevation_grid is None or elevation_grid.size == 0:
                return Result(error=AppError(
                    ErrorCode.ELEVATION_DATA_UNAVAILABLE,
                    "Elevation data unavailable for location",
                    {"lat": lat, "lon": lon}
                ))
            return Result(value=elevation_grid)
        except Exception as e:
            return Result(error=AppError(
                ErrorCode.ELEVATION_FETCH_FAILED,
                f"Failed to fetch elevation data: {str(e)}",
                {"lat": lat, "lon": lon}
            ))
    
    async def _get_vegetation_grid(self, lat: float, lon: float) -> Result[np.ndarray]:
        """Get vegetation grid from OSM data"""
        try:
            vegetation_grid = self.core.get_vegetation_grid_from_osm(lat, lon)
            if vegetation_grid is None:
                # Return default vegetation grid instead of error
                vegetation_grid = np.ones((self.core.GRID_SIZE, self.core.GRID_SIZE)) * 0.5
                self.logger.warning(f"Using default vegetation grid for {lat:.6f}, {lon:.6f}")
            return Result(value=vegetation_grid)
        except Exception as e:
            return Result(error=AppError(
                ErrorCode.VEGETATION_DATA_FAILED,
                f"Failed to fetch vegetation data: {str(e)}",
                {"lat": lat, "lon": lon}
            ))
    
    async def _analyze_terrain_features(self, elevation_grid: np.ndarray, 
                                      vegetation_grid: np.ndarray, 
                                      fast_mode: bool) -> Result[Dict[str, Any]]:
        """Analyze terrain features using core module"""
        try:
            features = self.core.analyze_terrain_and_vegetation(elevation_grid, vegetation_grid)
            
            # Add road proximity for hunting pressure analysis
            road_proximity = np.ones((self.core.GRID_SIZE, self.core.GRID_SIZE)) * 0.5
            features["road_proximity"] = road_proximity
            
            return Result(value=features)
        except Exception as e:
            return Result(error=AppError(
                ErrorCode.TERRAIN_FEATURE_ANALYSIS_FAILED,
                f"Terrain feature analysis failed: {str(e)}"
            ))
    
    def _calculate_slope_metrics(self, elevation_grid: np.ndarray) -> Dict[str, float]:
        """Calculate slope statistics"""
        try:
            # Calculate gradient
            dy, dx = np.gradient(elevation_grid)
            slope = np.arctan(np.sqrt(dx*dx + dy*dy)) * 180.0 / np.pi
            
            return {
                "mean_slope": float(np.mean(slope)),
                "max_slope": float(np.max(slope)),
                "slope_std": float(np.std(slope)),
                "steep_area_percentage": float(np.sum(slope > 15) / slope.size * 100)
            }
        except Exception as e:
            self.logger.warning(f"Slope calculation failed: {e}")
            return {"mean_slope": 0.0, "max_slope": 0.0, "slope_std": 0.0, "steep_area_percentage": 0.0}
    
    def _calculate_aspect_metrics(self, elevation_grid: np.ndarray) -> Dict[str, float]:
        """Calculate aspect statistics"""
        try:
            dy, dx = np.gradient(elevation_grid)
            aspect = np.arctan2(-dx, dy) * 180.0 / np.pi
            aspect = (aspect + 360) % 360  # Convert to 0-360 degrees
            
            # Calculate aspect distribution
            north_facing = np.sum((aspect >= 315) | (aspect <= 45)) / aspect.size * 100
            south_facing = np.sum((aspect >= 135) & (aspect <= 225)) / aspect.size * 100
            
            return {
                "mean_aspect": float(np.mean(aspect)),
                "north_facing_percentage": float(north_facing),
                "south_facing_percentage": float(south_facing),
                "aspect_variability": float(np.std(aspect))
            }
        except Exception as e:
            self.logger.warning(f"Aspect calculation failed: {e}")
            return {"mean_aspect": 0.0, "north_facing_percentage": 0.0, "south_facing_percentage": 0.0, "aspect_variability": 0.0}
    
    def _calculate_terrain_roughness(self, elevation_grid: np.ndarray) -> float:
        """Calculate terrain roughness index"""
        try:
            # Simple roughness calculation using elevation standard deviation
            return float(np.std(elevation_grid))
        except Exception as e:
            self.logger.warning(f"Terrain roughness calculation failed: {e}")
            return 0.0
    
    def _validate_coordinates(self, lat: float, lon: float) -> Result[None]:
        """Validate coordinate inputs"""
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            return Result(error=AppError(
                ErrorCode.INVALID_COORDINATES,
                "Coordinates must be numeric values",
                {"lat": lat, "lon": lon, "lat_type": type(lat).__name__, "lon_type": type(lon).__name__}
            ))
        
        if not (-90 <= lat <= 90):
            return Result(error=AppError(
                ErrorCode.INVALID_COORDINATES,
                f"Latitude must be between -90 and 90 degrees: {lat}",
                {"lat": lat, "lon": lon}
            ))
        
        if not (-180 <= lon <= 180):
            return Result(error=AppError(
                ErrorCode.INVALID_COORDINATES,
                f"Longitude must be between -180 and 180 degrees: {lon}",
                {"lat": lat, "lon": lon}
            ))
        
        return Result(value=None)


# Singleton instance
_terrain_service = None

def get_terrain_service() -> TerrainAnalysisService:
    """Get the singleton terrain analysis service instance"""
    global _terrain_service
    if _terrain_service is None:
        _terrain_service = TerrainAnalysisService()
    return _terrain_service
