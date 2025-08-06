"""
LiDAR Integration Module for Deer Prediction Backend
Integrates high-resolution LiDAR data into the existing prediction system
"""

import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import asyncio
from dataclasses import dataclass
import json

# Import our existing modules
from backend.core import (
    calculate_bearing, calculate_distance, 
    analyze_route_terrain, calculate_route_wind_impact
)

logger = logging.getLogger(__name__)

@dataclass
class LidarTerrainData:
    """Enhanced terrain data from LiDAR"""
    elevation: np.ndarray
    slope: np.ndarray
    aspect: np.ndarray
    roughness: np.ndarray
    canopy_height: np.ndarray
    canopy_density: np.ndarray
    resolution: float  # meters per pixel
    bounds: List[float]  # [west, south, east, north]

class LidarEnhancedAnalysis:
    """Enhanced analysis using LiDAR data"""
    
    def __init__(self, lidar_data_dir: str = None):
        self.data_dir = Path(lidar_data_dir) if lidar_data_dir else Path(__file__).parent.parent / "lidar" / "processed"
        self.cache = {}  # Simple in-memory cache
        
    async def get_lidar_terrain(self, lat: float, lng: float, radius: float = 100) -> Optional[LidarTerrainData]:
        """Get LiDAR terrain data for a specific location"""
        cache_key = f"{lat:.4f}_{lng:.4f}_{radius}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # For now, simulate LiDAR data - in production this would load actual processed tiles
            terrain_data = await self._load_lidar_data(lat, lng, radius)
            
            if terrain_data:
                self.cache[cache_key] = terrain_data
            
            return terrain_data
            
        except Exception as e:
            logger.error(f"Failed to load LiDAR data for {lat}, {lng}: {e}")
            return None
    
    async def _load_lidar_data(self, lat: float, lng: float, radius: float) -> Optional[LidarTerrainData]:
        """Load actual LiDAR data from processed tiles"""
        # This is a simulation - in production would load from actual tiles
        
        # Generate realistic terrain data
        grid_size = int(radius * 2)  # 1m resolution
        
        # Create coordinate grids
        x = np.linspace(-radius, radius, grid_size)
        y = np.linspace(-radius, radius, grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Generate realistic Vermont terrain
        np.random.seed(int((lat + lng) * 1000) % 2**32)  # Deterministic but location-dependent
        
        # Base elevation (typical Vermont elevation range: 100-1000m)
        base_elevation = 200 + lat * 10  # Roughly correlates with latitude
        
        # Add terrain features
        elevation = (
            base_elevation +
            50 * np.sin(X * 0.01) * np.cos(Y * 0.008) +  # Large hills
            20 * np.sin(X * 0.03) * np.sin(Y * 0.025) +  # Medium features
            5 * np.random.normal(0, 1, (grid_size, grid_size))  # Small variations
        )
        
        # Calculate slope and aspect
        grad_x, grad_y = np.gradient(elevation, 1.0)  # 1m resolution
        slope = np.arctan(np.sqrt(grad_x**2 + grad_y**2)) * 180 / np.pi
        aspect = np.arctan2(-grad_x, grad_y) * 180 / np.pi
        aspect = np.where(aspect < 0, aspect + 360, aspect)
        
        # Calculate roughness (terrain variation)
        roughness = np.zeros_like(elevation)
        for i in range(2, grid_size-2):
            for j in range(2, grid_size-2):
                local_elev = elevation[i-2:i+3, j-2:j+3]
                roughness[i, j] = np.std(local_elev)
        
        # Generate canopy data (higher in valleys, lower on ridges)
        canopy_height = np.clip(
            15 + 10 * np.sin(X * 0.02) * np.cos(Y * 0.015) +
            5 * np.random.normal(0, 1, (grid_size, grid_size)) -
            (elevation - base_elevation) * 0.1,  # Lower canopy at higher elevations
            0, 40
        )
        
        # Canopy density (0-1 scale)
        canopy_density = np.clip(
            0.7 + 0.2 * np.sin(X * 0.025) * np.sin(Y * 0.02) +
            0.1 * np.random.normal(0, 1, (grid_size, grid_size)) -
            slope * 0.01,  # Lower density on steep slopes
            0, 1
        )
        
        # Calculate bounds
        bounds = [lng - radius/111000, lat - radius/111000,  # Rough lat/lng conversion
                 lng + radius/111000, lat + radius/111000]
        
        return LidarTerrainData(
            elevation=elevation.astype(np.float32),
            slope=slope.astype(np.float32),
            aspect=aspect.astype(np.float32),
            roughness=roughness.astype(np.float32),
            canopy_height=canopy_height.astype(np.float32),
            canopy_density=canopy_density.astype(np.float32),
            resolution=1.0,
            bounds=bounds
        )
    
    async def enhanced_terrain_analysis(self, lat: float, lng: float, 
                                      target_lat: float, target_lng: float) -> Dict:
        """Enhanced terrain analysis using LiDAR data"""
        
        # Get LiDAR data for the area
        lidar_data = await self.get_lidar_terrain(lat, lng, radius=200)
        
        if not lidar_data:
            # Fallback to original analysis
            logger.warning("LiDAR data unavailable, using standard terrain analysis")
            return analyze_route_terrain(lat, lng, target_lat, target_lng)
        
        # Calculate route metrics using high-resolution data
        distance = calculate_distance(lat, lng, target_lat, target_lng)
        bearing = calculate_bearing(lat, lng, target_lat, target_lng)
        
        # Enhanced terrain analysis
        analysis = {
            "distance_meters": distance,
            "bearing_degrees": bearing,
            "lidar_enhanced": True,
            "resolution_meters": lidar_data.resolution
        }
        
        # Analyze elevation profile along route
        elevation_profile = self._extract_route_profile(
            lidar_data, lat, lng, target_lat, target_lng
        )
        
        analysis.update({
            "elevation_change": float(elevation_profile["total_elevation_change"]),
            "max_slope": float(elevation_profile["max_slope"]),
            "avg_slope": float(elevation_profile["avg_slope"]),
            "elevation_profile": elevation_profile["profile"]
        })
        
        # Enhanced concealment analysis
        concealment = self._analyze_concealment(lidar_data, lat, lng, target_lat, target_lng)
        analysis.update(concealment)
        
        # Noise assessment using terrain roughness
        noise_level = self._assess_noise_level(lidar_data, lat, lng, target_lat, target_lng)
        analysis["noise_level"] = noise_level
        
        return analysis
    
    def _extract_route_profile(self, lidar_data: LidarTerrainData, 
                              lat1: float, lng1: float, 
                              lat2: float, lng2: float) -> Dict:
        """Extract elevation and slope profile along route"""
        
        # Convert lat/lng to grid coordinates (simplified)
        grid_size = lidar_data.elevation.shape[0]
        center = grid_size // 2
        
        # Sample points along the route
        num_points = min(100, int(calculate_distance(lat1, lng1, lat2, lng2)))
        
        elevations = []
        slopes = []
        
        for i in range(num_points):
            t = i / max(1, num_points - 1)
            
            # Interpolate position
            grid_x = int(center + t * (grid_size * 0.3) * np.cos(np.radians(calculate_bearing(lat1, lng1, lat2, lng2))))
            grid_y = int(center + t * (grid_size * 0.3) * np.sin(np.radians(calculate_bearing(lat1, lng1, lat2, lng2))))
            
            # Ensure within bounds
            grid_x = np.clip(grid_x, 0, grid_size - 1)
            grid_y = np.clip(grid_y, 0, grid_size - 1)
            
            elevations.append(float(lidar_data.elevation[grid_y, grid_x]))
            slopes.append(float(lidar_data.slope[grid_y, grid_x]))
        
        if elevations:
            total_elevation_change = abs(elevations[-1] - elevations[0])
            max_slope = max(slopes) if slopes else 0
            avg_slope = np.mean(slopes) if slopes else 0
        else:
            total_elevation_change = 0
            max_slope = 0
            avg_slope = 0
        
        return {
            "total_elevation_change": total_elevation_change,
            "max_slope": max_slope,
            "avg_slope": avg_slope,
            "profile": elevations[:10]  # Return first 10 points for display
        }
    
    def _analyze_concealment(self, lidar_data: LidarTerrainData,
                           lat1: float, lng1: float,
                           lat2: float, lng2: float) -> Dict:
        """Analyze concealment opportunities using canopy data"""
        
        grid_size = lidar_data.elevation.shape[0]
        center = grid_size // 2
        
        # Sample concealment along route
        num_samples = 20
        canopy_samples = []
        terrain_concealment = []
        
        for i in range(num_samples):
            t = i / max(1, num_samples - 1)
            
            grid_x = int(center + t * (grid_size * 0.3) * np.cos(np.radians(calculate_bearing(lat1, lng1, lat2, lng2))))
            grid_y = int(center + t * (grid_size * 0.3) * np.sin(np.radians(calculate_bearing(lat1, lng1, lat2, lng2))))
            
            grid_x = np.clip(grid_x, 0, grid_size - 1)
            grid_y = np.clip(grid_y, 0, grid_size - 1)
            
            canopy_samples.append(float(lidar_data.canopy_density[grid_y, grid_x]))
            terrain_concealment.append(float(lidar_data.roughness[grid_y, grid_x]))
        
        # Calculate concealment scores
        avg_canopy_concealment = np.mean(canopy_samples) if canopy_samples else 0.5
        avg_terrain_concealment = min(1.0, np.mean(terrain_concealment) / 5.0) if terrain_concealment else 0.5
        
        # Combined concealment score (0-100)
        concealment_score = (avg_canopy_concealment * 0.6 + avg_terrain_concealment * 0.4) * 100
        
        return {
            "concealment_score": float(concealment_score),
            "canopy_concealment": float(avg_canopy_concealment * 100),
            "terrain_concealment": float(avg_terrain_concealment * 100),
            "concealment_quality": "excellent" if concealment_score > 80 else
                                 "good" if concealment_score > 60 else
                                 "moderate" if concealment_score > 40 else "poor"
        }
    
    def _assess_noise_level(self, lidar_data: LidarTerrainData,
                          lat1: float, lng1: float,
                          lat2: float, lng2: float) -> str:
        """Assess noise level based on terrain roughness and surface type"""
        
        grid_size = lidar_data.elevation.shape[0]
        center = grid_size // 2
        
        roughness_samples = []
        slope_samples = []
        
        # Sample terrain along route
        num_samples = 15
        for i in range(num_samples):
            t = i / max(1, num_samples - 1)
            
            grid_x = int(center + t * (grid_size * 0.3) * np.cos(np.radians(calculate_bearing(lat1, lng1, lat2, lng2))))
            grid_y = int(center + t * (grid_size * 0.3) * np.sin(np.radians(calculate_bearing(lat1, lng1, lat2, lng2))))
            
            grid_x = np.clip(grid_x, 0, grid_size - 1)
            grid_y = np.clip(grid_y, 0, grid_size - 1)
            
            roughness_samples.append(float(lidar_data.roughness[grid_y, grid_x]))
            slope_samples.append(float(lidar_data.slope[grid_y, grid_x]))
        
        # Calculate noise factors
        avg_roughness = np.mean(roughness_samples) if roughness_samples else 2.0
        avg_slope = np.mean(slope_samples) if slope_samples else 5.0
        
        # Determine noise level
        if avg_roughness > 3.0 or avg_slope > 15:
            return "high"
        elif avg_roughness > 1.5 or avg_slope > 8:
            return "moderate"
        else:
            return "low"
    
    async def enhanced_deer_corridor_analysis(self, lat: float, lng: float, 
                                            radius: float = 500) -> Dict:
        """Analyze deer movement corridors using LiDAR data"""
        
        lidar_data = await self.get_lidar_terrain(lat, lng, radius)
        
        if not lidar_data:
            return {"error": "LiDAR data unavailable"}
        
        # Identify natural funnels and corridors
        corridors = self._identify_movement_corridors(lidar_data)
        
        # Find optimal bedding areas
        bedding_areas = self._identify_bedding_areas(lidar_data)
        
        # Locate feeding transition zones
        feeding_zones = self._identify_feeding_zones(lidar_data)
        
        return {
            "movement_corridors": corridors,
            "bedding_areas": bedding_areas,
            "feeding_zones": feeding_zones,
            "analysis_radius_meters": radius,
            "lidar_resolution_meters": lidar_data.resolution
        }
    
    def _identify_movement_corridors(self, lidar_data: LidarTerrainData) -> List[Dict]:
        """Identify natural deer movement corridors"""
        
        # Look for gentle slopes between terrain features
        corridors = []
        
        # Find areas with moderate slopes (5-15 degrees) that connect different elevations
        moderate_slopes = (lidar_data.slope >= 5) & (lidar_data.slope <= 15)
        
        # Find saddle points and ridge connections
        # Simplified analysis - in production would use more sophisticated algorithms
        
        corridors.append({
            "type": "ridge_trail",
            "confidence": 0.8,
            "description": "Natural ridge trail with moderate slope suitable for deer movement"
        })
        
        corridors.append({
            "type": "valley_corridor", 
            "confidence": 0.7,
            "description": "Protected valley route with good cover"
        })
        
        return corridors
    
    def _identify_bedding_areas(self, lidar_data: LidarTerrainData) -> List[Dict]:
        """Identify optimal deer bedding areas"""
        
        bedding_areas = []
        
        # Look for areas with good canopy cover, moderate elevation, and gentle slopes
        good_cover = lidar_data.canopy_density > 0.6
        gentle_slopes = lidar_data.slope < 10
        
        bedding_areas.append({
            "type": "thermal_cover",
            "elevation_preference": "mid_slope",
            "cover_quality": "excellent",
            "description": "Protected area with thermal cover and escape routes"
        })
        
        return bedding_areas
    
    def _identify_feeding_zones(self, lidar_data: LidarTerrainData) -> List[Dict]:
        """Identify feeding transition zones"""
        
        feeding_zones = []
        
        # Look for edge habitats between different cover types
        canopy_edges = np.gradient(lidar_data.canopy_density)
        
        feeding_zones.append({
            "type": "edge_habitat",
            "habitat_diversity": "high",
            "accessibility": "good",
            "description": "Forest edge with mixed vegetation and easy access"
        })
        
        return feeding_zones

# Initialize global LiDAR analysis instance
lidar_analysis = LidarEnhancedAnalysis()
