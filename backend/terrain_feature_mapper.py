#!/usr/bin/env python3
"""
Terrain Feature Mapper for Mature Buck Predictor

Maps existing terrain analysis features to the specific features expected
by the mature buck predictor, converting static defaults to location-specific
calculations based on real terrain data.

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import numpy as np
import logging
from typing import Dict, Tuple
from scipy.ndimage import distance_transform_edt

logger = logging.getLogger(__name__)

class TerrainFeatureMapper:
    """Maps existing terrain features to mature buck predictor expected features"""
    
    def __init__(self):
        """Initialize the terrain feature mapper"""
        pass
    
    def map_terrain_features(self, terrain_features: Dict, lat: float, lon: float) -> Dict:
        """
        Convert existing terrain features to mature buck predictor expected features
        
        Args:
            terrain_features: Original terrain analysis from core.py
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Dict with additional calculated features for mature buck analysis
        """
        logger.info(f"Mapping terrain features for mature buck analysis at {lat}, {lon}")
        
        # Create enhanced feature set
        enhanced_features = terrain_features.copy()
        
        # Add missing features with location-specific calculations
        enhanced_features.update({
            'escape_cover_density': self._calculate_escape_cover_density(terrain_features),
            'hunter_accessibility': self._calculate_hunter_accessibility(terrain_features),
            'wetland_proximity': self._calculate_wetland_proximity(terrain_features, lat, lon),
            'cliff_proximity': self._calculate_cliff_proximity(terrain_features, lat, lon),
            'visibility_limitation': self._calculate_visibility_limitation(terrain_features),
            'canopy_closure': self._calculate_canopy_closure(terrain_features),
            'nearest_road_distance': self._estimate_road_distance(lat, lon),
            'nearest_building_distance': self._estimate_building_distance(lat, lon),
            'trail_density': self._estimate_trail_density(terrain_features),
            'drainage_density': self._calculate_drainage_density(terrain_features),
            'ridge_connectivity': self._calculate_ridge_connectivity(terrain_features),
            'terrain_roughness': self._calculate_terrain_roughness(terrain_features),
            'cover_type_diversity': self._calculate_cover_diversity(terrain_features)
        })
        
        logger.info(f"Enhanced terrain features calculated for {lat}, {lon}")
        return enhanced_features
    
    def _calculate_escape_cover_density(self, features: Dict) -> float:
        """Calculate escape cover density from existing forest features"""
        try:
            deep_forest = features.get('deep_forest', np.zeros((50, 50)))
            conifer_dense = features.get('conifer_dense', np.zeros((50, 50)))
            
            # Combine deep forest and conifer coverage
            escape_cover = deep_forest | conifer_dense
            
            if isinstance(escape_cover, np.ndarray):
                density = np.mean(escape_cover) * 100.0  # Convert to percentage
                # Ensure reasonable range (20-95%)
                return max(20.0, min(95.0, density))
            else:
                return 50.0  # Fallback
                
        except Exception as e:
            logger.warning(f"Failed to calculate escape cover density: {e}")
            return 50.0
    
    def _calculate_hunter_accessibility(self, features: Dict) -> float:
        """Calculate hunter accessibility based on terrain difficulty"""
        try:
            slope = features.get('slope', np.zeros((50, 50)))
            swamp = features.get('swamp', np.zeros((50, 50)))
            bluff_pinch = features.get('bluff_pinch', np.zeros((50, 50)))
            
            if isinstance(slope, np.ndarray):
                # Higher slopes = lower accessibility
                mean_slope = np.mean(slope)
                slope_difficulty = min(1.0, mean_slope / 30.0)  # Normalize to 0-1
                
                # Swamps and bluffs reduce accessibility
                swamp_factor = np.mean(swamp.astype(float)) if isinstance(swamp, np.ndarray) else 0.0
                bluff_factor = np.mean(bluff_pinch.astype(float)) if isinstance(bluff_pinch, np.ndarray) else 0.0
                
                # Calculate accessibility (0 = very difficult, 1 = very easy)
                accessibility = 1.0 - (slope_difficulty * 0.7 + swamp_factor * 0.2 + bluff_factor * 0.1)
                
                # Ensure reasonable range (0.1-0.9)
                return max(0.1, min(0.9, accessibility))
            else:
                return 0.7  # Fallback
                
        except Exception as e:
            logger.warning(f"Failed to calculate hunter accessibility: {e}")
            return 0.7
    
    def _calculate_wetland_proximity(self, features: Dict, lat: float, lon: float) -> float:
        """Calculate distance to nearest wetland features"""
        try:
            water = features.get('water', np.zeros((50, 50)))
            swamp = features.get('swamp', np.zeros((50, 50)))
            creek_bottom = features.get('creek_bottom', np.zeros((50, 50)))
            
            # Combine all water features
            wetlands = water | swamp | creek_bottom
            
            if isinstance(wetlands, np.ndarray) and np.any(wetlands):
                # Calculate distance transform from wetland features
                distance_map = distance_transform_edt(~wetlands)
                
                # Get distance at center of grid
                center_y, center_x = wetlands.shape[0] // 2, wetlands.shape[1] // 2
                distance_pixels = distance_map[center_y, center_x]
                
                # Convert pixels to approximate meters (assuming ~30m per pixel)
                distance_meters = distance_pixels * 30.0
                
                # Ensure reasonable range (50-2000m)
                return max(50.0, min(2000.0, distance_meters))
            else:
                # No wetlands detected, return moderate distance
                return 800.0
                
        except Exception as e:
            logger.warning(f"Failed to calculate wetland proximity: {e}")
            return 1000.0
    
    def _calculate_cliff_proximity(self, features: Dict, lat: float, lon: float) -> float:
        """Calculate distance to steep terrain/cliff features"""
        try:
            slope = features.get('slope', np.zeros((50, 50)))
            bluff_pinch = features.get('bluff_pinch', np.zeros((50, 50)))
            
            if isinstance(slope, np.ndarray):
                # Define cliff areas as very steep slopes (>35 degrees) or bluff pinches
                cliff_areas = (slope > 35) | bluff_pinch
                
                if np.any(cliff_areas):
                    # Calculate distance transform from cliff features
                    distance_map = distance_transform_edt(~cliff_areas)
                    
                    # Get distance at center of grid
                    center_y, center_x = cliff_areas.shape[0] // 2, cliff_areas.shape[1] // 2
                    distance_pixels = distance_map[center_y, center_x]
                    
                    # Convert pixels to approximate meters
                    distance_meters = distance_pixels * 30.0
                    
                    # Ensure reasonable range (100-3000m)
                    return max(100.0, min(3000.0, distance_meters))
                else:
                    # No steep terrain detected
                    return 1500.0
            else:
                return 1000.0  # Fallback
                
        except Exception as e:
            logger.warning(f"Failed to calculate cliff proximity: {e}")
            return 1000.0
    
    def _calculate_visibility_limitation(self, features: Dict) -> float:
        """Calculate visibility limitation based on forest density"""
        try:
            deep_forest = features.get('deep_forest', np.zeros((50, 50)))
            conifer_dense = features.get('conifer_dense', np.zeros((50, 50)))
            
            # Dense vegetation limits visibility
            visibility_blockers = deep_forest | conifer_dense
            
            if isinstance(visibility_blockers, np.ndarray):
                limitation = np.mean(visibility_blockers.astype(float))
                
                # Ensure reasonable range (0.1-0.95)
                return max(0.1, min(0.95, limitation))
            else:
                return 0.5  # Fallback
                
        except Exception as e:
            logger.warning(f"Failed to calculate visibility limitation: {e}")
            return 0.5
    
    def _calculate_canopy_closure(self, features: Dict) -> float:
        """Calculate canopy closure percentage"""
        try:
            forest = features.get('forest', np.zeros((50, 50)))
            deep_forest = features.get('deep_forest', np.zeros((50, 50)))
            
            if isinstance(forest, np.ndarray):
                # Base canopy from forest coverage
                forest_coverage = np.mean(forest.astype(float))
                
                # Bonus for deep forest areas
                deep_forest_bonus = 0.0
                if isinstance(deep_forest, np.ndarray):
                    deep_forest_bonus = np.mean(deep_forest.astype(float)) * 0.3
                
                canopy_closure = (forest_coverage * 70.0) + (deep_forest_bonus * 100.0)
                
                # Ensure reasonable range (10-95%)
                return max(10.0, min(95.0, canopy_closure))
            else:
                return 50.0  # Fallback
                
        except Exception as e:
            logger.warning(f"Failed to calculate canopy closure: {e}")
            return 50.0
    
    def _estimate_road_distance(self, lat: float, lon: float) -> float:
        """Estimate road distance based on coordinates (simplified)"""
        # Simplified estimation - in reality would use road network data
        # Rural areas generally have less road density
        
        # Use coordinate variation to simulate different road proximities
        coord_hash = abs(hash(f"{lat:.4f},{lon:.4f}")) % 1000
        
        # Convert to distance estimate (500-3000m range)
        base_distance = 500 + (coord_hash * 2.5)
        
        return max(200.0, min(5000.0, base_distance))
    
    def _estimate_building_distance(self, lat: float, lon: float) -> float:
        """Estimate building distance based on coordinates (simplified)"""
        # Buildings typically further than roads in rural areas
        road_distance = self._estimate_road_distance(lat, lon)
        
        # Buildings are typically 1.5-3x further than roads
        building_distance = road_distance * (1.5 + (abs(hash(f"{lon:.4f}")) % 100) / 100.0)
        
        return max(500.0, min(8000.0, building_distance))
    
    def _estimate_trail_density(self, features: Dict) -> float:
        """Estimate trail density based on terrain accessibility"""
        try:
            slope = features.get('slope', np.zeros((50, 50)))
            forest_edge = features.get('forest_edge', np.zeros((50, 50)))
            
            if isinstance(slope, np.ndarray):
                # Lower slopes tend to have more trails
                mean_slope = np.mean(slope)
                slope_factor = max(0.0, 1.0 - (mean_slope / 25.0))
                
                # Forest edges often have trails
                edge_factor = 0.0
                if isinstance(forest_edge, np.ndarray):
                    edge_factor = np.mean(forest_edge.astype(float)) * 0.5
                
                trail_density = slope_factor + edge_factor
                
                # Convert to trails per km² (0.1-3.0 range)
                return max(0.1, min(3.0, trail_density * 2.0))
            else:
                return 0.5  # Fallback
                
        except Exception as e:
            logger.warning(f"Failed to estimate trail density: {e}")
            return 0.5
    
    def _calculate_drainage_density(self, features: Dict) -> float:
        """Calculate drainage density from terrain features"""
        try:
            creek_bottom = features.get('creek_bottom', np.zeros((50, 50)))
            water = features.get('water', np.zeros((50, 50)))
            slope = features.get('slope', np.zeros((50, 50)))
            
            if isinstance(creek_bottom, np.ndarray):
                # Water features and creek bottoms indicate drainage
                drainage_features = creek_bottom | water
                drainage_coverage = np.mean(drainage_features.astype(float))
                
                # Add slope variation factor (more varied slopes = more drainage)
                if isinstance(slope, np.ndarray):
                    slope_variation = np.std(slope) / 10.0  # Normalize
                    drainage_coverage += slope_variation * 0.1
                
                # Convert to reasonable drainage density (0.2-2.5)
                return max(0.2, min(2.5, drainage_coverage * 3.0))
            else:
                return 0.5  # Fallback
                
        except Exception as e:
            logger.warning(f"Failed to calculate drainage density: {e}")
            return 0.5
    
    def _calculate_ridge_connectivity(self, features: Dict) -> float:
        """Calculate ridge connectivity for escape routes"""
        try:
            ridge_top = features.get('ridge_top', np.zeros((50, 50)))
            
            if isinstance(ridge_top, np.ndarray):
                ridge_coverage = np.mean(ridge_top.astype(float))
                
                # More ridge coverage = better connectivity
                connectivity = ridge_coverage * 2.0
                
                # Ensure reasonable range (0.1-1.0)
                return max(0.1, min(1.0, connectivity))
            else:
                return 0.3  # Fallback
                
        except Exception as e:
            logger.warning(f"Failed to calculate ridge connectivity: {e}")
            return 0.3
    
    def _calculate_terrain_roughness(self, features: Dict) -> float:
        """Calculate terrain roughness/complexity"""
        try:
            slope = features.get('slope', np.zeros((50, 50)))
            curvature = features.get('curvature', np.zeros((50, 50)))
            
            if isinstance(slope, np.ndarray):
                # Combine slope variation and curvature for roughness
                slope_std = np.std(slope) / 20.0  # Normalize
                
                curvature_factor = 0.0
                if isinstance(curvature, np.ndarray):
                    curvature_factor = np.std(curvature) / 100.0  # Normalize
                
                roughness = slope_std + curvature_factor
                
                # Ensure reasonable range (0.1-1.5)
                return max(0.1, min(1.5, roughness))
            else:
                return 0.5  # Fallback
                
        except Exception as e:
            logger.warning(f"Failed to calculate terrain roughness: {e}")
            return 0.5
    
    def _calculate_cover_diversity(self, features: Dict) -> float:
        """Calculate cover type diversity"""
        try:
            # Count different cover types present
            cover_types = [
                'forest', 'field', 'water', 'hardwood', 'conifer_dense',
                'corn_field', 'soybean_field', 'hay_field', 'oak_trees'
            ]
            
            diversity_count = 0
            for cover_type in cover_types:
                cover_data = features.get(cover_type, np.zeros((50, 50)))
                if isinstance(cover_data, np.ndarray) and np.any(cover_data):
                    diversity_count += 1
            
            # Convert to diversity score (1.0-5.0 range)
            diversity = max(1.0, min(5.0, diversity_count * 0.8))
            
            return diversity
            
        except Exception as e:
            logger.warning(f"Failed to calculate cover diversity: {e}")
            return 2.0

# Create singleton instance
_terrain_mapper = None

def get_terrain_mapper() -> TerrainFeatureMapper:
    """Get the singleton terrain feature mapper instance"""
    global _terrain_mapper
    if _terrain_mapper is None:
        _terrain_mapper = TerrainFeatureMapper()
    return _terrain_mapper
