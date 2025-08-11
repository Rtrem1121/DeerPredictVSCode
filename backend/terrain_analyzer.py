#!/usr/bin/env python3
"""
Advanced Terrain Feature Detection for Mature Buck Predictions

This module implements sophisticated terrain analysis using elevation grids and spatial
analysis to detect travel corridors, funnels, and terrain features that mature bucks
prefer for movement and bedding.

Key Features:
- 5x5 elevation grid sampling for detailed terrain analysis
- GeoPandas spatial analysis for corridor detection
- Topographic feature detection (saddles, ridges, drainages)
- Mature buck specific terrain preferences
- Real-time caching for performance optimization

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from scipy import ndimage
from scipy.spatial.distance import cdist
from sklearn.cluster import DBSCAN
from typing import Dict, List, Tuple, Optional, Union
import logging
import time
import hashlib
from dataclasses import dataclass
from enum import Enum
import json

# Import configuration management
try:
    from .config_manager import get_config
except ImportError:
    from config_manager import get_config

logger = logging.getLogger(__name__)

class TerrainFeatureType(Enum):
    """Types of terrain features detected for mature buck analysis"""
    SADDLE = "saddle"                    # Low points between hills (natural funnels)
    RIDGE_SPINE = "ridge_spine"          # Ridge top travel corridors
    DRAINAGE = "drainage"                # Stream/water corridors
    SLOPE_BREAK = "slope_break"          # Transition zones between slope gradients
    BENCH = "bench"                      # Flat areas on slopes (bedding spots)
    FUNNEL = "natural_funnel"            # Terrain-constrained travel routes
    CONVERGENCE = "convergence_zone"     # Where multiple features meet
    ESCAPE_CORRIDOR = "escape_corridor"  # Routes for quick escape

@dataclass
class ElevationGrid:
    """Container for elevation grid data and metadata"""
    elevations: np.ndarray              # 5x5 elevation grid
    coordinates: List[Tuple[float, float]]  # Lat/lon for each grid point
    center_lat: float                   # Center point latitude
    center_lon: float                   # Center point longitude
    grid_spacing: float                 # Spacing between points (meters)
    timestamp: float                    # When data was collected
    
    def get_elevation_at(self, row: int, col: int) -> float:
        """Get elevation at specific grid position"""
        if 0 <= row < 5 and 0 <= col < 5:
            return float(self.elevations[row, col])
        return 0.0
    
    def get_coordinate_at(self, row: int, col: int) -> Tuple[float, float]:
        """Get lat/lon coordinates at specific grid position"""
        idx = row * 5 + col
        if 0 <= idx < len(self.coordinates):
            return self.coordinates[idx]
        return (self.center_lat, self.center_lon)

@dataclass 
class TerrainFeature:
    """Detected terrain feature with spatial and confidence data"""
    feature_type: TerrainFeatureType
    center_lat: float
    center_lon: float
    geometry: Union[Point, LineString, Polygon]
    confidence: float                   # 0-100 confidence in detection
    properties: Dict                    # Feature-specific properties
    mature_buck_score: float           # Suitability for mature bucks (0-100)
    
    def to_dict(self) -> Dict:
        """Convert feature to dictionary for serialization"""
        return {
            'type': self.feature_type.value,
            'lat': self.center_lat,
            'lon': self.center_lon,
            'confidence': self.confidence,
            'mature_buck_score': self.mature_buck_score,
            'properties': self.properties
        }

class TerrainAnalyzer:
    """
    Advanced terrain analyzer for mature buck habitat and movement prediction
    
    This class implements sophisticated terrain analysis using elevation grids and
    spatial analysis to detect features that influence mature buck behavior.
    """
    
    def __init__(self):
        """Initialize terrain analyzer with configuration"""
        self.config = get_config()
        self.analysis_config = self._load_terrain_config()
        self.elevation_cache = {}  # Cache for elevation grids
        self.feature_cache = {}    # Cache for detected features
        self.cache_ttl = 3600      # Cache time-to-live (1 hour)
        
        logger.info("🔍 Advanced Terrain Analyzer initialized")
    
    def _load_terrain_config(self) -> Dict:
        """Load terrain analysis configuration"""
        config = get_config()
        
        # Default terrain analysis parameters
        default_config = {
            'grid_spacing_meters': 50.0,        # 50m between elevation points
            'detection_thresholds': {
                'saddle_depth_min': 5.0,        # Minimum saddle depth (meters)
                'ridge_prominence_min': 8.0,     # Minimum ridge prominence
                'slope_break_threshold': 15.0,   # Slope change threshold (degrees)
                'drainage_gradient_max': 10.0,   # Max gradient for drainage
                'bench_flatness_max': 5.0        # Max slope for bench detection
            },
            'mature_buck_preferences': {
                'saddle_width_preferred': (30.0, 100.0),    # Preferred saddle width range
                'ridge_accessibility': 0.6,                  # Accessibility threshold
                'drainage_concealment_bonus': 15.0,          # Concealment bonus
                'escape_route_priority': 0.8                 # Escape route importance
            },
            'spatial_analysis': {
                'cluster_epsilon': 75.0,         # DBSCAN clustering distance
                'min_samples': 2,               # Minimum samples for cluster
                'corridor_buffer_meters': 25.0  # Buffer around corridors
            }
        }
        
        # Get any overrides from main configuration
        terrain_config = config.get('terrain_analysis', {})
        
        # Merge with defaults
        for key, value in default_config.items():
            if key not in terrain_config:
                terrain_config[key] = value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in terrain_config[key]:
                        terrain_config[key][subkey] = subvalue
        
        return terrain_config
    
    def analyze_terrain_features(self, lat: float, lon: float, 
                               force_refresh: bool = False) -> Dict[str, any]:
        """
        Comprehensive terrain feature analysis for mature buck predictions
        
        Args:
            lat: Center latitude coordinate
            lon: Center longitude coordinate
            force_refresh: Force new analysis (bypass cache)
            
        Returns:
            Dict containing detected features and analysis results
        """
        logger.info(f"🔍 Starting advanced terrain analysis for {lat:.4f}, {lon:.4f}")
        
        # Check cache first
        cache_key = self._generate_cache_key(lat, lon)
        if not force_refresh and cache_key in self.feature_cache:
            cached_result = self.feature_cache[cache_key]
            if time.time() - cached_result['timestamp'] < self.cache_ttl:
                logger.info("📋 Using cached terrain analysis")
                return cached_result['data']
        
        # Get elevation grid
        elevation_grid = self._get_elevation_grid(lat, lon)
        
        # Detect terrain features
        detected_features = self._detect_all_features(elevation_grid)
        
        # Analyze travel corridors
        travel_corridors = self._analyze_travel_corridors(detected_features, elevation_grid)
        
        # Identify natural funnels
        natural_funnels = self._identify_natural_funnels(detected_features, elevation_grid)
        
        # Calculate mature buck suitability scores
        mature_buck_analysis = self._analyze_mature_buck_suitability(
            detected_features, travel_corridors, natural_funnels, elevation_grid
        )
        
        # Create comprehensive analysis result
        analysis_result = {
            'elevation_grid': {
                'center_lat': elevation_grid.center_lat,
                'center_lon': elevation_grid.center_lon,
                'grid_spacing': elevation_grid.grid_spacing,
                'elevation_stats': self._calculate_elevation_stats(elevation_grid),
                'topographic_complexity': self._calculate_topographic_complexity(elevation_grid)
            },
            'detected_features': [f.to_dict() for f in detected_features],
            'travel_corridors': travel_corridors,
            'natural_funnels': natural_funnels,
            'mature_buck_analysis': mature_buck_analysis,
            'spatial_summary': self._create_spatial_summary(
                detected_features, travel_corridors, natural_funnels
            ),
            'confidence_metrics': self._calculate_confidence_metrics(detected_features)
        }
        
        # Cache the result
        self.feature_cache[cache_key] = {
            'data': analysis_result,
            'timestamp': time.time()
        }
        
        logger.info(f"✅ Terrain analysis complete. Found {len(detected_features)} features")
        return analysis_result
    
    def _get_elevation_grid(self, center_lat: float, center_lon: float) -> ElevationGrid:
        """
        Get 5x5 elevation grid around center point
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            
        Returns:
            ElevationGrid with elevation data and coordinates
        """
        cache_key = f"elev_{center_lat:.4f}_{center_lon:.4f}"
        
        # Check elevation cache
        if cache_key in self.elevation_cache:
            cached_grid = self.elevation_cache[cache_key]
            if time.time() - cached_grid.timestamp < self.cache_ttl:
                return cached_grid
        
        grid_spacing = self.analysis_config['grid_spacing_meters']
        
        # Calculate grid coordinates
        # Convert meters to degrees (approximate)
        meters_to_degrees = 1.0 / 111000.0  # Rough conversion at this latitude
        grid_offset = (grid_spacing * 2) * meters_to_degrees  # 2 grid points each direction
        
        # Create 5x5 grid of coordinates
        coordinates = []
        elevations = np.zeros((5, 5))
        
        for row in range(5):
            for col in range(5):
                # Calculate offset from center
                lat_offset = (row - 2) * grid_spacing * meters_to_degrees
                lon_offset = (col - 2) * grid_spacing * meters_to_degrees
                
                grid_lat = center_lat + lat_offset
                grid_lon = center_lon + lon_offset
                coordinates.append((grid_lat, grid_lon))
                
                # Get elevation for this point
                elevation = self._fetch_elevation(grid_lat, grid_lon)
                elevations[row, col] = elevation
        
        # Create elevation grid object
        elevation_grid = ElevationGrid(
            elevations=elevations,
            coordinates=coordinates,
            center_lat=center_lat,
            center_lon=center_lon,
            grid_spacing=grid_spacing,
            timestamp=time.time()
        )
        
        # Cache the result
        self.elevation_cache[cache_key] = elevation_grid
        
        return elevation_grid
    
    def _fetch_elevation(self, lat: float, lon: float) -> float:
        """
        Fetch elevation for a specific coordinate
        
        For now, this generates realistic elevation data based on Vermont topology.
        In production, this would connect to an elevation API or DEM data.
        """
        # Simulate Vermont-like elevation based on coordinate patterns
        # This creates realistic terrain with ridges, valleys, and elevation variation
        
        # Base elevation around Vermont's typical range (200-1000m)
        base_elevation = 300.0
        
        # Add terrain variation based on coordinate patterns
        lat_factor = np.sin(lat * 100) * 50  # Ridge-like patterns
        lon_factor = np.cos(lon * 150) * 40  # Valley patterns
        
        # Add some random variation for realistic terrain
        random_seed = int((lat * 10000 + lon * 10000) % 1000)
        np.random.seed(random_seed)
        random_variation = np.random.normal(0, 25)
        
        # Add drainage patterns (lower elevations near water features)
        drainage_factor = -abs(np.sin(lat * 200) * np.cos(lon * 200)) * 30
        
        total_elevation = base_elevation + lat_factor + lon_factor + random_variation + drainage_factor
        
        # Keep within reasonable Vermont range
        return max(150.0, min(1200.0, total_elevation))
    
    def _detect_all_features(self, elevation_grid: ElevationGrid) -> List[TerrainFeature]:
        """Detect all terrain features in the elevation grid"""
        detected_features = []
        
        # Detect different feature types
        detected_features.extend(self._detect_saddles(elevation_grid))
        detected_features.extend(self._detect_ridge_spines(elevation_grid))
        detected_features.extend(self._detect_drainages(elevation_grid))
        detected_features.extend(self._detect_slope_breaks(elevation_grid))
        detected_features.extend(self._detect_benches(elevation_grid))
        
        return detected_features
    
    def _detect_saddles(self, elevation_grid: ElevationGrid) -> List[TerrainFeature]:
        """Detect saddle features (low points between hills)"""
        saddles = []
        elevations = elevation_grid.elevations
        thresholds = self.analysis_config['detection_thresholds']
        
        for row in range(1, 4):  # Skip edges
            for col in range(1, 4):
                center_elevation = elevations[row, col]
                
                # Check if this is a local minimum with higher points around
                neighbors = [
                    elevations[row-1, col-1], elevations[row-1, col], elevations[row-1, col+1],
                    elevations[row, col-1],                           elevations[row, col+1],
                    elevations[row+1, col-1], elevations[row+1, col], elevations[row+1, col+1]
                ]
                
                # Check for saddle pattern: lower than most neighbors but with "gaps"
                higher_neighbors = sum(1 for n in neighbors if n > center_elevation + thresholds['saddle_depth_min'])
                
                if 4 <= higher_neighbors <= 6:  # Saddle pattern: higher on most sides
                    lat, lon = elevation_grid.get_coordinate_at(row, col)
                    
                    # Calculate saddle properties
                    depth = np.mean([n for n in neighbors if n > center_elevation]) - center_elevation
                    width = self._estimate_saddle_width(elevations, row, col)
                    
                    # Calculate confidence based on depth and clarity
                    confidence = min(95.0, 50.0 + depth * 3.0)
                    
                    # Calculate mature buck score
                    mature_buck_score = self._score_saddle_for_mature_buck(depth, width)
                    
                    saddle = TerrainFeature(
                        feature_type=TerrainFeatureType.SADDLE,
                        center_lat=lat,
                        center_lon=lon,
                        geometry=Point(lon, lat),
                        confidence=confidence,
                        properties={
                            'depth_meters': depth,
                            'width_meters': width,
                            'accessibility': self._calculate_accessibility(elevations, row, col),
                            'concealment_rating': min(depth / 10.0, 1.0)
                        },
                        mature_buck_score=mature_buck_score
                    )
                    saddles.append(saddle)
        
        return saddles
    
    def _detect_ridge_spines(self, elevation_grid: ElevationGrid) -> List[TerrainFeature]:
        """Detect ridge spine features for travel corridors"""
        ridges = []
        elevations = elevation_grid.elevations
        thresholds = self.analysis_config['detection_thresholds']
        
        # Use gradient analysis to find ridge lines
        grad_x, grad_y = np.gradient(elevations)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        for row in range(1, 4):
            for col in range(1, 4):
                center_elevation = elevations[row, col]
                
                # Check if this is a local maximum with good prominence
                neighbors = [
                    elevations[row-1, col-1], elevations[row-1, col], elevations[row-1, col+1],
                    elevations[row, col-1],                           elevations[row, col+1],
                    elevations[row+1, col-1], elevations[row+1, col], elevations[row+1, col+1]
                ]
                
                prominence = center_elevation - np.mean(neighbors)
                
                if prominence >= thresholds['ridge_prominence_min']:
                    lat, lon = elevation_grid.get_coordinate_at(row, col)
                    
                    # Calculate ridge properties
                    connectivity = self._calculate_ridge_connectivity(elevations, row, col)
                    steepness = gradient_magnitude[row, col]
                    
                    confidence = min(90.0, 40.0 + prominence * 4.0)
                    mature_buck_score = self._score_ridge_for_mature_buck(prominence, connectivity, steepness)
                    
                    ridge = TerrainFeature(
                        feature_type=TerrainFeatureType.RIDGE_SPINE,
                        center_lat=lat,
                        center_lon=lon,
                        geometry=Point(lon, lat),
                        confidence=confidence,
                        properties={
                            'prominence_meters': prominence,
                            'connectivity': connectivity,
                            'steepness': steepness,
                            'travel_suitability': min(prominence / 20.0, 1.0)
                        },
                        mature_buck_score=mature_buck_score
                    )
                    ridges.append(ridge)
        
        return ridges
    
    def _detect_drainages(self, elevation_grid: ElevationGrid) -> List[TerrainFeature]:
        """Detect drainage features for concealed travel"""
        drainages = []
        elevations = elevation_grid.elevations
        
        # Find flow paths using steepest descent
        for row in range(1, 4):
            for col in range(1, 4):
                flow_path = self._trace_flow_path(elevations, row, col)
                
                if len(flow_path) >= 3:  # Significant drainage
                    lat, lon = elevation_grid.get_coordinate_at(row, col)
                    
                    # Calculate drainage properties
                    gradient = self._calculate_drainage_gradient(elevations, flow_path)
                    concealment = self._estimate_drainage_concealment(elevations, flow_path)
                    
                    if gradient <= self.analysis_config['detection_thresholds']['drainage_gradient_max']:
                        confidence = min(85.0, 30.0 + concealment * 40.0)
                        mature_buck_score = self._score_drainage_for_mature_buck(gradient, concealment)
                        
                        drainage = TerrainFeature(
                            feature_type=TerrainFeatureType.DRAINAGE,
                            center_lat=lat,
                            center_lon=lon,
                            geometry=Point(lon, lat),
                            confidence=confidence,
                            properties={
                                'gradient_percent': gradient,
                                'concealment_rating': concealment,
                                'flow_path_length': len(flow_path),
                                'water_likelihood': min(concealment, 0.8)
                            },
                            mature_buck_score=mature_buck_score
                        )
                        drainages.append(drainage)
        
        return drainages
    
    def _detect_slope_breaks(self, elevation_grid: ElevationGrid) -> List[TerrainFeature]:
        """Detect slope break features (transition zones)"""
        slope_breaks = []
        elevations = elevation_grid.elevations
        threshold = self.analysis_config['detection_thresholds']['slope_break_threshold']
        
        # Calculate slope for each point
        slopes = self._calculate_slope_grid(elevations)
        
        for row in range(1, 4):
            for col in range(1, 4):
                # Check for significant slope changes
                center_slope = slopes[row, col]
                neighbor_slopes = [
                    slopes[row-1, col], slopes[row+1, col],
                    slopes[row, col-1], slopes[row, col+1]
                ]
                
                slope_variance = np.var(neighbor_slopes + [center_slope])
                
                if slope_variance >= threshold:
                    lat, lon = elevation_grid.get_coordinate_at(row, col)
                    
                    # Calculate transition properties
                    transition_strength = slope_variance
                    accessibility = self._calculate_slope_break_accessibility(slopes, row, col)
                    
                    confidence = min(80.0, 25.0 + transition_strength * 2.0)
                    mature_buck_score = self._score_slope_break_for_mature_buck(
                        transition_strength, accessibility
                    )
                    
                    slope_break = TerrainFeature(
                        feature_type=TerrainFeatureType.SLOPE_BREAK,
                        center_lat=lat,
                        center_lon=lon,
                        geometry=Point(lon, lat),
                        confidence=confidence,
                        properties={
                            'transition_strength': transition_strength,
                            'accessibility': accessibility,
                            'slope_variance': slope_variance,
                            'bedding_potential': accessibility > 0.7
                        },
                        mature_buck_score=mature_buck_score
                    )
                    slope_breaks.append(slope_break)
        
        return slope_breaks
    
    def _detect_benches(self, elevation_grid: ElevationGrid) -> List[TerrainFeature]:
        """Detect bench features (flat areas on slopes for bedding)"""
        benches = []
        elevations = elevation_grid.elevations
        max_slope = self.analysis_config['detection_thresholds']['bench_flatness_max']
        
        slopes = self._calculate_slope_grid(elevations)
        
        for row in range(1, 4):
            for col in range(1, 4):
                if slopes[row, col] <= max_slope:
                    # Check if surrounded by steeper terrain (true bench)
                    neighbor_slopes = [
                        slopes[row-1, col], slopes[row+1, col],
                        slopes[row, col-1], slopes[row, col+1]
                    ]
                    
                    avg_neighbor_slope = np.mean(neighbor_slopes)
                    
                    if avg_neighbor_slope > slopes[row, col] + 5.0:  # Bench criteria
                        lat, lon = elevation_grid.get_coordinate_at(row, col)
                        
                        # Calculate bench properties
                        flatness = max_slope - slopes[row, col]
                        size_estimate = self._estimate_bench_size(slopes, row, col, max_slope)
                        elevation = elevations[row, col]
                        
                        confidence = min(75.0, 40.0 + flatness * 3.0)
                        mature_buck_score = self._score_bench_for_mature_buck(
                            flatness, size_estimate, elevation
                        )
                        
                        bench = TerrainFeature(
                            feature_type=TerrainFeatureType.BENCH,
                            center_lat=lat,
                            center_lon=lon,
                            geometry=Point(lon, lat),
                            confidence=confidence,
                            properties={
                                'flatness_rating': flatness,
                                'size_estimate_sqm': size_estimate,
                                'elevation_meters': elevation,
                                'bedding_suitability': min(flatness / 5.0, 1.0)
                            },
                            mature_buck_score=mature_buck_score
                        )
                        benches.append(bench)
        
        return benches
    
    def _analyze_travel_corridors(self, features: List[TerrainFeature], 
                                elevation_grid: ElevationGrid) -> List[Dict]:
        """Analyze travel corridors based on detected features"""
        corridors = []
        
        # Group features by type for corridor analysis
        saddles = [f for f in features if f.feature_type == TerrainFeatureType.SADDLE]
        ridges = [f for f in features if f.feature_type == TerrainFeatureType.RIDGE_SPINE]
        drainages = [f for f in features if f.feature_type == TerrainFeatureType.DRAINAGE]
        
        # Analyze saddle-based corridors
        for saddle in saddles:
            if saddle.mature_buck_score >= 60.0:
                corridor = {
                    'type': 'saddle_corridor',
                    'primary_feature': saddle.to_dict(),
                    'corridor_lat': saddle.center_lat,
                    'corridor_lon': saddle.center_lon,
                    'confidence': saddle.confidence * 0.9,  # Slight reduction for corridor vs feature
                    'mature_buck_suitability': saddle.mature_buck_score,
                    'properties': {
                        'travel_difficulty': 'low',
                        'concealment': saddle.properties.get('concealment_rating', 0.5),
                        'natural_funnel': True,
                        'seasonal_preference': 'all_seasons'
                    }
                }
                corridors.append(corridor)
        
        # Analyze ridge-based corridors
        for ridge in ridges:
            if ridge.mature_buck_score >= 55.0:
                corridor = {
                    'type': 'ridge_corridor',
                    'primary_feature': ridge.to_dict(),
                    'corridor_lat': ridge.center_lat,
                    'corridor_lon': ridge.center_lon,
                    'confidence': ridge.confidence * 0.85,
                    'mature_buck_suitability': ridge.mature_buck_score,
                    'properties': {
                        'travel_difficulty': 'moderate',
                        'elevation_advantage': True,
                        'escape_routes': 'multiple',
                        'seasonal_preference': 'dry_conditions'
                    }
                }
                corridors.append(corridor)
        
        # Analyze drainage-based corridors
        for drainage in drainages:
            if drainage.mature_buck_score >= 50.0:
                corridor = {
                    'type': 'drainage_corridor',
                    'primary_feature': drainage.to_dict(),
                    'corridor_lat': drainage.center_lat,
                    'corridor_lon': drainage.center_lon,
                    'confidence': drainage.confidence * 0.8,
                    'mature_buck_suitability': drainage.mature_buck_score,
                    'properties': {
                        'travel_difficulty': 'low',
                        'concealment': 'excellent',
                        'water_access': True,
                        'seasonal_preference': 'wet_conditions'
                    }
                }
                corridors.append(corridor)
        
        # Sort by mature buck suitability
        corridors.sort(key=lambda x: x['mature_buck_suitability'], reverse=True)
        
        return corridors[:5]  # Return top 5 corridors
    
    def _identify_natural_funnels(self, features: List[TerrainFeature], 
                                elevation_grid: ElevationGrid) -> List[Dict]:
        """Identify natural terrain funnels for ambush points"""
        funnels = []
        
        # Look for convergence of multiple features
        feature_points = [(f.center_lat, f.center_lon, f) for f in features]
        
        if len(feature_points) >= 2:
            # Use clustering to find convergence zones
            coords = np.array([(lat, lon) for lat, lon, _ in feature_points])
            
            if len(coords) > 1:
                clustering = DBSCAN(
                    eps=self.analysis_config['spatial_analysis']['cluster_epsilon'] / 111000.0,  # Convert to degrees
                    min_samples=self.analysis_config['spatial_analysis']['min_samples']
                ).fit(coords)
                
                # Analyze each cluster as potential funnel
                for cluster_id in set(clustering.labels_):
                    if cluster_id != -1:  # Ignore noise points
                        cluster_mask = clustering.labels_ == cluster_id
                        cluster_features = [feature_points[i][2] for i in range(len(feature_points)) 
                                          if cluster_mask[i]]
                        
                        if len(cluster_features) >= 2:
                            # Calculate funnel center
                            center_lat = np.mean([f.center_lat for f in cluster_features])
                            center_lon = np.mean([f.center_lon for f in cluster_features])
                            
                            # Calculate funnel properties
                            funnel_strength = self._calculate_funnel_strength(cluster_features)
                            approach_angles = self._calculate_approach_angles(cluster_features)
                            
                            # Calculate mature buck score for funnel
                            mature_buck_score = self._score_funnel_for_mature_buck(
                                cluster_features, funnel_strength
                            )
                            
                            funnel = {
                                'type': 'terrain_convergence_funnel',
                                'center_lat': center_lat,
                                'center_lon': center_lon,
                                'confidence': min(85.0, 40.0 + funnel_strength * 30.0),
                                'mature_buck_suitability': mature_buck_score,
                                'contributing_features': [f.to_dict() for f in cluster_features],
                                'properties': {
                                    'funnel_strength': funnel_strength,
                                    'approach_angles': approach_angles,
                                    'feature_count': len(cluster_features),
                                    'ambush_potential': mature_buck_score >= 70.0
                                }
                            }
                            funnels.append(funnel)
        
        # Sort by mature buck suitability
        funnels.sort(key=lambda x: x['mature_buck_suitability'], reverse=True)
        
        return funnels[:3]  # Return top 3 funnels
    
    # Helper methods for terrain analysis calculations
    
    def _estimate_saddle_width(self, elevations: np.ndarray, row: int, col: int) -> float:
        """Estimate saddle width in meters"""
        # Simple estimation based on elevation profile
        center_elevation = elevations[row, col]
        grid_spacing = self.analysis_config['grid_spacing_meters']
        
        # Check width in different directions
        widths = []
        
        # East-West width
        if col > 0 and col < 4:
            if elevations[row, col-1] > center_elevation and elevations[row, col+1] > center_elevation:
                widths.append(grid_spacing)
        
        # North-South width  
        if row > 0 and row < 4:
            if elevations[row-1, col] > center_elevation and elevations[row+1, col] > center_elevation:
                widths.append(grid_spacing)
        
        return np.mean(widths) if widths else grid_spacing * 0.5
    
    def _calculate_ridge_connectivity(self, elevations: np.ndarray, row: int, col: int) -> float:
        """Calculate how well connected a ridge point is to other high points"""
        center_elevation = elevations[row, col]
        connected_count = 0
        total_checked = 0
        
        # Check connectivity in all directions
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                    
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 5 and 0 <= new_col < 5:
                    total_checked += 1
                    if elevations[new_row, new_col] >= center_elevation - 5.0:  # Within 5m
                        connected_count += 1
        
        return connected_count / total_checked if total_checked > 0 else 0.0
    
    def _trace_flow_path(self, elevations: np.ndarray, start_row: int, start_col: int) -> List[Tuple[int, int]]:
        """Trace water flow path from starting point"""
        path = [(start_row, start_col)]
        current_row, current_col = start_row, start_col
        
        for _ in range(10):  # Limit path length
            lowest_elevation = elevations[current_row, current_col]
            next_row, next_col = current_row, current_col
            
            # Find steepest descent direction
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                        
                    new_row, new_col = current_row + dr, current_col + dc
                    if 0 <= new_row < 5 and 0 <= new_col < 5:
                        if elevations[new_row, new_col] < lowest_elevation:
                            lowest_elevation = elevations[new_row, new_col]
                            next_row, next_col = new_row, new_col
            
            # If no lower point found, end path
            if next_row == current_row and next_col == current_col:
                break
                
            path.append((next_row, next_col))
            current_row, current_col = next_row, next_col
        
        return path
    
    def _calculate_slope_grid(self, elevations: np.ndarray) -> np.ndarray:
        """Calculate slope in degrees for each grid point"""
        grad_x, grad_y = np.gradient(elevations)
        grid_spacing = self.analysis_config['grid_spacing_meters']
        
        # Convert to slope in degrees
        slope_radians = np.arctan(np.sqrt(grad_x**2 + grad_y**2) / grid_spacing)
        slope_degrees = np.degrees(slope_radians)
        
        return slope_degrees
    
    # Mature buck specific scoring methods
    
    def _score_saddle_for_mature_buck(self, depth: float, width: float) -> float:
        """Score saddle suitability for mature bucks"""
        preferences = self.analysis_config['mature_buck_preferences']
        preferred_width = preferences['saddle_width_preferred']
        
        score = 40.0  # Base score
        
        # Depth scoring (deeper is better for concealment)
        if depth >= 10.0:
            score += 25.0
        elif depth >= 5.0:
            score += 15.0
        
        # Width scoring (prefer moderate widths)
        if preferred_width[0] <= width <= preferred_width[1]:
            score += 20.0
        elif width < preferred_width[0]:
            score += 10.0  # Narrow is still good
        
        # Concealment bonus
        concealment_bonus = preferences['drainage_concealment_bonus']
        score += concealment_bonus * (depth / 15.0)
        
        return min(score, 100.0)
    
    def _score_ridge_for_mature_buck(self, prominence: float, connectivity: float, steepness: float) -> float:
        """Score ridge suitability for mature bucks"""
        preferences = self.analysis_config['mature_buck_preferences']
        
        score = 35.0  # Base score
        
        # Prominence scoring
        if prominence >= 15.0:
            score += 20.0
        elif prominence >= 8.0:
            score += 15.0
        
        # Connectivity scoring
        if connectivity >= preferences['ridge_accessibility']:
            score += 15.0
        
        # Moderate steepness preferred (not too steep, not too flat)
        if 5.0 <= steepness <= 20.0:
            score += 10.0
        
        # Escape route bonus
        escape_bonus = preferences['escape_route_priority'] * 20.0
        if connectivity >= 0.7:  # Good connectivity = good escape routes
            score += escape_bonus
        
        return min(score, 100.0)
    
    def _score_drainage_for_mature_buck(self, gradient: float, concealment: float) -> float:
        """Score drainage suitability for mature bucks"""
        preferences = self.analysis_config['mature_buck_preferences']
        
        score = 50.0  # Higher base score - drainages are excellent for bucks
        
        # Gradient scoring (prefer gentle gradients)
        if gradient <= 5.0:
            score += 20.0
        elif gradient <= 10.0:
            score += 10.0
        
        # Concealment scoring
        concealment_bonus = preferences['drainage_concealment_bonus']
        score += concealment_bonus * concealment
        
        # Water access bonus
        score += 10.0
        
        return min(score, 100.0)
    
    def _score_slope_break_for_mature_buck(self, transition_strength: float, accessibility: float) -> float:
        """Score slope break suitability for mature bucks"""
        score = 30.0  # Base score
        
        # Transition strength (more pronounced is better)
        if transition_strength >= 25.0:
            score += 15.0
        elif transition_strength >= 15.0:
            score += 10.0
        
        # Accessibility for bedding
        if accessibility >= 0.8:
            score += 25.0  # Excellent bedding potential
        elif accessibility >= 0.6:
            score += 15.0
        
        return min(score, 100.0)
    
    def _score_bench_for_mature_buck(self, flatness: float, size: float, elevation: float) -> float:
        """Score bench suitability for mature bucks"""
        score = 45.0  # Good base score - benches are excellent for bedding
        
        # Flatness scoring
        if flatness >= 4.0:
            score += 20.0
        elif flatness >= 2.0:
            score += 15.0
        
        # Size scoring
        if size >= 100.0:  # Square meters
            score += 15.0
        elif size >= 50.0:
            score += 10.0
        
        # Elevation preference (moderate elevation preferred)
        if 300.0 <= elevation <= 600.0:
            score += 10.0
        
        return min(score, 100.0)
    
    def _score_funnel_for_mature_buck(self, features: List[TerrainFeature], strength: float) -> float:
        """Score funnel suitability for mature buck ambush points"""
        score = 30.0  # Base score
        
        # Feature diversity bonus
        feature_types = set(f.feature_type for f in features)
        score += len(feature_types) * 10.0
        
        # Strength bonus
        if strength >= 0.8:
            score += 25.0
        elif strength >= 0.6:
            score += 15.0
        
        # High scoring features bonus
        high_score_features = sum(1 for f in features if f.mature_buck_score >= 70.0)
        score += high_score_features * 8.0
        
        return min(score, 100.0)
    
    # Additional helper methods
    
    def _calculate_accessibility(self, elevations: np.ndarray, row: int, col: int) -> float:
        """Calculate terrain accessibility (0-1, higher is more accessible)"""
        slopes = self._calculate_slope_grid(elevations)
        center_slope = slopes[row, col]
        
        # Accessibility decreases with slope
        if center_slope <= 5.0:
            return 1.0
        elif center_slope <= 15.0:
            return 0.8
        elif center_slope <= 25.0:
            return 0.6
        elif center_slope <= 35.0:
            return 0.4
        else:
            return 0.2
    
    def _calculate_drainage_gradient(self, elevations: np.ndarray, flow_path: List[Tuple[int, int]]) -> float:
        """Calculate gradient percentage along drainage path"""
        if len(flow_path) < 2:
            return 0.0
        
        start_elevation = elevations[flow_path[0]]
        end_elevation = elevations[flow_path[-1]]
        elevation_change = start_elevation - end_elevation
        
        # Calculate horizontal distance
        grid_spacing = self.analysis_config['grid_spacing_meters']
        horizontal_distance = len(flow_path) * grid_spacing
        
        if horizontal_distance > 0:
            gradient_percent = (elevation_change / horizontal_distance) * 100.0
            return max(0.0, gradient_percent)
        
        return 0.0
    
    def _estimate_drainage_concealment(self, elevations: np.ndarray, flow_path: List[Tuple[int, int]]) -> float:
        """Estimate concealment rating for drainage (0-1)"""
        if not flow_path:
            return 0.0
        
        concealment_score = 0.0
        
        # Check depth of drainage relative to surrounding terrain
        for row, col in flow_path:
            if 0 <= row < 5 and 0 <= col < 5:
                center_elevation = elevations[row, col]
                
                # Check surrounding elevation
                surrounding_elevations = []
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        new_row, new_col = row + dr, col + dc
                        if 0 <= new_row < 5 and 0 <= new_col < 5:
                            surrounding_elevations.append(elevations[new_row, new_col])
                
                if surrounding_elevations:
                    avg_surrounding = np.mean(surrounding_elevations)
                    depth = avg_surrounding - center_elevation
                    concealment_score += min(depth / 20.0, 1.0)  # Normalize depth contribution
        
        return min(concealment_score / len(flow_path), 1.0) if flow_path else 0.0
    
    def _calculate_slope_break_accessibility(self, slopes: np.ndarray, row: int, col: int) -> float:
        """Calculate accessibility of slope break area"""
        center_slope = slopes[row, col]
        
        # Check surrounding slopes for ease of access
        neighbor_slopes = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 5 and 0 <= new_col < 5:
                    neighbor_slopes.append(slopes[new_row, new_col])
        
        if neighbor_slopes:
            avg_neighbor_slope = np.mean(neighbor_slopes)
            # More accessible if center is flatter than surroundings
            accessibility = max(0.0, 1.0 - (center_slope / 30.0))
            return min(accessibility, 1.0)
        
        return 0.5
    
    def _estimate_bench_size(self, slopes: np.ndarray, row: int, col: int, max_slope: float) -> float:
        """Estimate bench size in square meters"""
        grid_spacing = self.analysis_config['grid_spacing_meters']
        flat_cell_count = 0
        
        # Count adjacent cells with similar low slope
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 5 and 0 <= new_col < 5:
                    if slopes[new_row, new_col] <= max_slope:
                        flat_cell_count += 1
        
        # Estimate size based on flat cell count
        cell_area = grid_spacing ** 2
        return flat_cell_count * cell_area
    
    def _calculate_funnel_strength(self, features: List[TerrainFeature]) -> float:
        """Calculate strength of terrain funnel based on contributing features"""
        if not features:
            return 0.0
        
        # Base strength from feature count
        strength = min(len(features) / 5.0, 1.0)
        
        # Bonus for feature diversity
        feature_types = set(f.feature_type for f in features)
        diversity_bonus = len(feature_types) / 5.0  # Max 5 types
        
        # Bonus for high-scoring features
        high_score_ratio = sum(1 for f in features if f.mature_buck_score >= 60.0) / len(features)
        
        total_strength = (strength + diversity_bonus + high_score_ratio) / 3.0
        return min(total_strength, 1.0)
    
    def _calculate_approach_angles(self, features: List[TerrainFeature]) -> List[float]:
        """Calculate possible approach angles through funnel"""
        if len(features) < 2:
            return []
        
        # Calculate angles between feature pairs
        angles = []
        for i in range(len(features)):
            for j in range(i + 1, len(features)):
                f1, f2 = features[i], features[j]
                
                # Calculate angle between features
                delta_lat = f2.center_lat - f1.center_lat
                delta_lon = f2.center_lon - f1.center_lon
                
                angle = np.arctan2(delta_lat, delta_lon) * 180.0 / np.pi
                angles.append(angle)
        
        return angles
    
    def _calculate_elevation_stats(self, elevation_grid: ElevationGrid) -> Dict:
        """Calculate statistical summary of elevation grid"""
        elevations = elevation_grid.elevations.flatten()
        
        return {
            'min_elevation': float(np.min(elevations)),
            'max_elevation': float(np.max(elevations)),
            'mean_elevation': float(np.mean(elevations)),
            'elevation_range': float(np.max(elevations) - np.min(elevations)),
            'std_deviation': float(np.std(elevations)),
            'relief_ratio': float(np.std(elevations) / np.mean(elevations)) if np.mean(elevations) > 0 else 0.0
        }
    
    def _calculate_topographic_complexity(self, elevation_grid: ElevationGrid) -> float:
        """Calculate overall topographic complexity score (0-1)"""
        elevations = elevation_grid.elevations
        
        # Calculate various complexity metrics
        relief = np.max(elevations) - np.min(elevations)
        slopes = self._calculate_slope_grid(elevations)
        avg_slope = np.mean(slopes)
        slope_variance = np.var(slopes)
        
        # Combine metrics for complexity score
        relief_score = min(relief / 100.0, 1.0)  # Normalize to 100m max
        slope_score = min(avg_slope / 30.0, 1.0)  # Normalize to 30 degree max
        variance_score = min(slope_variance / 200.0, 1.0)  # Normalize variance
        
        complexity = (relief_score + slope_score + variance_score) / 3.0
        return min(complexity, 1.0)
    
    def _analyze_mature_buck_suitability(self, features: List[TerrainFeature], 
                                       corridors: List[Dict], funnels: List[Dict], 
                                       elevation_grid: ElevationGrid) -> Dict:
        """Comprehensive mature buck suitability analysis"""
        
        # Calculate feature type scores
        feature_scores = {}
        for feature_type in TerrainFeatureType:
            type_features = [f for f in features if f.feature_type == feature_type]
            if type_features:
                feature_scores[feature_type.value] = {
                    'count': len(type_features),
                    'avg_score': np.mean([f.mature_buck_score for f in type_features]),
                    'max_score': max(f.mature_buck_score for f in type_features),
                    'features': [f.to_dict() for f in type_features]
                }
        
        # Calculate corridor analysis
        corridor_analysis = {
            'total_corridors': len(corridors),
            'avg_suitability': np.mean([c['mature_buck_suitability'] for c in corridors]) if corridors else 0.0,
            'best_corridor_type': max(corridors, key=lambda x: x['mature_buck_suitability'])['type'] if corridors else None,
            'corridor_diversity': len(set(c['type'] for c in corridors))
        }
        
        # Calculate funnel analysis
        funnel_analysis = {
            'total_funnels': len(funnels),
            'avg_suitability': np.mean([f['mature_buck_suitability'] for f in funnels]) if funnels else 0.0,
            'best_funnel_strength': max(funnels, key=lambda x: x['mature_buck_suitability'])['properties']['funnel_strength'] if funnels else 0.0
        }
        
        # Calculate overall area score
        terrain_stats = self._calculate_elevation_stats(elevation_grid)
        complexity = self._calculate_topographic_complexity(elevation_grid)
        
        # Weighted scoring for mature buck habitat
        feature_score = np.mean([f.mature_buck_score for f in features]) if features else 0.0
        corridor_score = corridor_analysis['avg_suitability']
        funnel_score = funnel_analysis['avg_suitability']
        terrain_score = (complexity * 50.0) + (min(terrain_stats['relief_ratio'], 0.5) * 100.0)
        
        overall_score = (
            feature_score * 0.4 +
            corridor_score * 0.3 + 
            funnel_score * 0.2 +
            terrain_score * 0.1
        )
        
        return {
            'overall_suitability': min(overall_score, 100.0),
            'feature_analysis': feature_scores,
            'corridor_analysis': corridor_analysis,
            'funnel_analysis': funnel_analysis,
            'terrain_metrics': {
                'topographic_complexity': complexity,
                'elevation_stats': terrain_stats,
                'terrain_score': terrain_score
            },
            'recommendations': self._generate_terrain_recommendations(
                features, corridors, funnels, overall_score
            )
        }
    
    def _create_spatial_summary(self, features: List[TerrainFeature], 
                              corridors: List[Dict], funnels: List[Dict]) -> Dict:
        """Create spatial summary of detected features"""
        return {
            'total_features': len(features),
            'feature_density': len(features) / 25.0,  # Features per grid cell (5x5 = 25)
            'corridor_count': len(corridors),
            'funnel_count': len(funnels),
            'feature_distribution': {
                feature_type.value: sum(1 for f in features if f.feature_type == feature_type)
                for feature_type in TerrainFeatureType
            },
            'high_value_features': sum(1 for f in features if f.mature_buck_score >= 70.0),
            'spatial_coverage': self._calculate_spatial_coverage(features)
        }
    
    def _calculate_spatial_coverage(self, features: List[TerrainFeature]) -> float:
        """Calculate how well features cover the analysis area"""
        if not features:
            return 0.0
        
        # Simple coverage metric based on feature distribution
        latitudes = [f.center_lat for f in features]
        longitudes = [f.center_lon for f in features]
        
        lat_range = max(latitudes) - min(latitudes) if len(latitudes) > 1 else 0.0
        lon_range = max(longitudes) - min(longitudes) if len(longitudes) > 1 else 0.0
        
        # Normalize to grid size (approximately 200m x 200m)
        grid_size_degrees = 200.0 / 111000.0  # Convert to degrees
        
        coverage = min((lat_range + lon_range) / (2 * grid_size_degrees), 1.0)
        return coverage
    
    def _calculate_confidence_metrics(self, features: List[TerrainFeature]) -> Dict:
        """Calculate confidence metrics for feature detection"""
        if not features:
            return {
                'avg_confidence': 0.0,
                'min_confidence': 0.0,
                'max_confidence': 0.0,
                'high_confidence_features': 0,
                'confidence_distribution': {}
            }
        
        confidences = [f.confidence for f in features]
        
        # Confidence distribution bins
        bins = [0, 50, 70, 85, 100]
        distribution = {}
        for i in range(len(bins) - 1):
            count = sum(1 for c in confidences if bins[i] <= c < bins[i+1])
            distribution[f"{bins[i]}-{bins[i+1]}"] = count
        
        return {
            'avg_confidence': np.mean(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'high_confidence_features': sum(1 for c in confidences if c >= 80.0),
            'confidence_distribution': distribution
        }
    
    def _generate_terrain_recommendations(self, features: List[TerrainFeature], 
                                        corridors: List[Dict], funnels: List[Dict], 
                                        overall_score: float) -> List[str]:
        """Generate actionable terrain-based recommendations"""
        recommendations = []
        
        if overall_score >= 80.0:
            recommendations.append("🎯 EXCELLENT terrain for mature buck hunting - multiple high-value features present")
        elif overall_score >= 60.0:
            recommendations.append("✅ GOOD terrain potential - focus on best corridors and funnels")
        elif overall_score >= 40.0:
            recommendations.append("⚠️ MODERATE terrain - selective approach required")
        else:
            recommendations.append("❌ LIMITED terrain potential - consider alternative locations")
        
        # Feature-specific recommendations
        saddles = [f for f in features if f.feature_type == TerrainFeatureType.SADDLE]
        if saddles:
            best_saddle = max(saddles, key=lambda x: x.mature_buck_score)
            if best_saddle.mature_buck_score >= 70.0:
                recommendations.append(f"🎯 Prime saddle detected - excellent natural funnel at {best_saddle.center_lat:.4f}, {best_saddle.center_lon:.4f}")
        
        # Corridor recommendations
        if corridors:
            best_corridor = max(corridors, key=lambda x: x['mature_buck_suitability'])
            if best_corridor['mature_buck_suitability'] >= 70.0:
                recommendations.append(f"🛤️ Top travel corridor: {best_corridor['type']} with {best_corridor['mature_buck_suitability']:.0f}% suitability")
        
        # Funnel recommendations
        if funnels:
            best_funnel = max(funnels, key=lambda x: x['mature_buck_suitability'])
            if best_funnel['mature_buck_suitability'] >= 75.0:
                recommendations.append(f"🎯 Premium ambush funnel with {best_funnel['properties']['feature_count']} converging features")
        
        # Strategic recommendations
        high_value_features = sum(1 for f in features if f.mature_buck_score >= 70.0)
        if high_value_features >= 3:
            recommendations.append("💎 Multiple high-value features - consider multi-stand strategy")
        
        drainage_features = [f for f in features if f.feature_type == TerrainFeatureType.DRAINAGE]
        if len(drainage_features) >= 2:
            recommendations.append("💧 Multiple drainage systems - excellent concealed travel options")
        
        return recommendations
    
    def _generate_cache_key(self, lat: float, lon: float) -> str:
        """Generate cache key for analysis results"""
        key_string = f"{lat:.4f}_{lon:.4f}_{self.analysis_config['grid_spacing_meters']}"
        return hashlib.md5(key_string.encode()).hexdigest()

def get_terrain_analyzer() -> TerrainAnalyzer:
    """
    Factory function to get a configured terrain analyzer instance
    
    Returns:
        TerrainAnalyzer: Configured analyzer instance
    """
    return TerrainAnalyzer()

# Integration function for mature buck predictor
def enhance_mature_buck_prediction_with_terrain(prediction_data: Dict, lat: float, lon: float) -> Dict:
    """
    Enhance mature buck predictions with advanced terrain analysis
    
    Args:
        prediction_data: Existing prediction data
        lat: Latitude coordinate
        lon: Longitude coordinate
        
    Returns:
        Enhanced prediction data with terrain features
    """
    logger.info(f"🔍 Enhancing mature buck prediction with advanced terrain analysis")
    
    # Get terrain analyzer
    terrain_analyzer = get_terrain_analyzer()
    
    # Perform terrain analysis
    terrain_features = terrain_analyzer.analyze_terrain_features(lat, lon)
    
    # Enhance prediction data
    enhanced_data = prediction_data.copy()
    enhanced_data.update({
        'advanced_terrain_analysis': terrain_features,
        'terrain_enhancement_applied': True,
        'enhancement_timestamp': time.time()
    })
    
    # Adjust confidence based on terrain quality
    terrain_score = terrain_features['mature_buck_analysis']['overall_suitability']
    original_confidence = enhanced_data.get('confidence_score', 50.0)
    
    # Apply terrain-based confidence adjustment
    if terrain_score >= 80.0:
        confidence_bonus = 15.0
    elif terrain_score >= 60.0:
        confidence_bonus = 10.0
    elif terrain_score >= 40.0:
        confidence_bonus = 5.0
    else:
        confidence_bonus = -5.0
    
    enhanced_data['confidence_score'] = min(100.0, original_confidence + confidence_bonus)
    enhanced_data['terrain_confidence_adjustment'] = confidence_bonus
    
    logger.info(f"✅ Terrain enhancement complete. Confidence adjusted by {confidence_bonus:+.1f}")
    
    return enhanced_data
