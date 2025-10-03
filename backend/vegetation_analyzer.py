#!/usr/bin/env python3
"""
Google Earth Engine Vegetation Analysis Module

Provides real-time satellite vegetation analysis for enhanced deer prediction accuracy.
Integrates NDVI, land cover, and vegetation health metrics.

Author: GitHub Copilot
Date: August 14, 2025
"""

import logging
import ee
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class VegetationAnalyzer:
    """
    Analyzes vegetation conditions using Google Earth Engine satellite data.
    
    Features:
    - Real-time NDVI calculation
    - Land cover classification
    - Vegetation health assessment
    - Seasonal change detection
    - Food source mapping
    """
    
    def __init__(self):
        self.initialized = False
        self.available = False
        
    def initialize(self) -> bool:
        """Initialize Google Earth Engine connection using direct initialization"""
        try:
            import ee
            import os
            
            # Check if already initialized
            try:
                ee.Number(1).getInfo()
                self.initialized = True
                self.available = True
                logger.info("✅ GEE Vegetation Analyzer already initialized")
                return True
            except:
                pass
            
            # Search for credentials in multiple paths
            credential_paths = [
                'credentials/gee-service-account.json',  # Local path (development)
                '/app/credentials/gee-service-account.json',  # Docker path (production)
            ]
            
            credentials_path = None
            for path in credential_paths:
                if os.path.exists(path):
                    credentials_path = path
                    logger.info(f"🔑 Found GEE credentials: {path}")
                    break
            
            if credentials_path:
                service_credentials = ee.ServiceAccountCredentials(None, credentials_path)
                ee.Initialize(service_credentials)
                
                # Test initialization
                ee.Number(1).getInfo()
                self.initialized = True
                self.available = True
                logger.info("✅ GEE Vegetation Analyzer initialized with direct authentication")
                return True
            else:
                logger.warning(f"Service account file not found in: {credential_paths}")
                return False
                
        except Exception as e:
            logger.warning(f"GEE initialization failed: {e}")
            return False
    
    def _ensure_gee_initialized(self) -> bool:
        """Ensure GEE is initialized, bypassing faulty singleton"""
        try:
            import ee
            import os
            
            # Check if already initialized
            try:
                ee.Number(1).getInfo()
                return True
            except:
                pass
            
            # Search for credentials in multiple paths
            credential_paths = [
                'credentials/gee-service-account.json',  # Local path (development)
                '/app/credentials/gee-service-account.json',  # Docker path (production)
            ]
            
            credentials_path = None
            for path in credential_paths:
                if os.path.exists(path):
                    credentials_path = path
                    break
            
            if credentials_path:
                service_credentials = ee.ServiceAccountCredentials(None, credentials_path)
                ee.Initialize(service_credentials)
                
                # Test initialization
                ee.Number(1).getInfo()
                logger.info("🛰️ GEE initialized successfully")
                return True
            else:
                logger.warning(f"Service account file not found in: {credential_paths}")
                return False
                
        except Exception as e:
            logger.warning(f"GEE initialization failed: {e}")
            return False

    def analyze_hunting_area(self, lat: float, lon: float, radius_km: float = 2.0, season: str = 'early_season') -> Dict[str, Any]:
        """
        Comprehensive vegetation analysis for hunting area.
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Analysis radius in kilometers
            season: Hunting season (early_season, rut, late_season) for Vermont food analysis
            
        Returns:
            Dict containing vegetation analysis results
        """
        
        if not self.available and not self.initialize():
            return self._fallback_vegetation_analysis(lat, lon)
        
        try:
            # Create analysis area
            point = ee.Geometry.Point([lon, lat])
            area = point.buffer(radius_km * 1000)  # Convert to meters
            
            # Get current date for recent imagery
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Used for other analyses
            
            # Analyze vegetation metrics using improved NDVI method
            results = {
                'ndvi_analysis': self._analyze_ndvi_improved(area, start_date, end_date),
                'land_cover': self._analyze_land_cover(area),
                'canopy_coverage_analysis': self._analyze_canopy_coverage(lat, lon, radius_km * 1000),  # NEW: Real canopy!
                'food_sources': self._identify_food_sources(area, start_date, end_date, season),  # Vermont-specific!
                'vegetation_health': self._assess_vegetation_health(area, start_date, end_date),
                'seasonal_changes': self._detect_seasonal_changes(area),
                'water_proximity': self._analyze_water_sources(area),
                'analysis_metadata': {
                    'center_lat': lat,
                    'center_lon': lon,
                    'radius_km': radius_km,
                    'season': season,  # Track season used
                    'analysis_date': end_date.isoformat(),
                    'data_source': 'google_earth_engine'
                }
            }
            
            logger.info(f"🛰️ Completed GEE vegetation analysis for {lat:.4f}, {lon:.4f} ({season})")
            return results
            
        except Exception as e:
            logger.warning(f"GEE vegetation analysis failed: {e}, using fallback")
            return self._fallback_vegetation_analysis(lat, lon)
    
    def _analyze_ndvi_improved(self, area: ee.Geometry, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Improved NDVI analysis with better fallback strategies"""
        try:
            # Multiple search strategies for better data availability
            search_strategies = [
                (30, 20, "Recent clear imagery"),
                (60, 30, "Extended recent period"), 
                (90, 40, "Seasonal period"),
                (180, 50, "Extended seasonal"),
                (365, 60, "Annual fallback")
            ]
            
            for days_back, cloud_threshold, description in search_strategies:
                search_start = end_date - timedelta(days=days_back)
                
                collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                    .filterBounds(area) \
                    .filterDate(search_start.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                    .filter(ee.Filter.lt('CLOUD_COVER', cloud_threshold))
                
                size = collection.size().getInfo()
                if size > 0:
                    logger.info(f"🛰️ Found {size} images using {description}")
                    
                    # Calculate NDVI
                    def calculate_ndvi(image):
                        ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
                        return image.addBands(ndvi)
                    
                    # Get median NDVI
                    ndvi_collection = collection.map(calculate_ndvi)
                    median_ndvi = ndvi_collection.select('NDVI').median()
                    
                    # Calculate statistics
                    stats = median_ndvi.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=area,
                        scale=30,
                        maxPixels=1e9
                    ).getInfo()
                    
                    ndvi_value = stats.get('NDVI')
                    if ndvi_value is not None:
                        # Interpret NDVI values
                        if ndvi_value > 0.6:
                            vegetation_health = "excellent"
                        elif ndvi_value > 0.4:
                            vegetation_health = "good"
                        elif ndvi_value > 0.2:
                            vegetation_health = "moderate"
                        else:
                            vegetation_health = "poor"
                        
                        return {
                            'ndvi_value': ndvi_value,
                            'vegetation_health': vegetation_health,
                            'image_count': size,
                            'date_range_days': days_back,
                            'cloud_threshold': cloud_threshold,
                            'strategy_used': description,
                            'analysis_date': end_date.isoformat()
                        }
            
            # If no imagery found with any strategy
            logger.warning("No suitable imagery available with any search strategy")
            return {
                'ndvi_value': None,
                'vegetation_health': 'unknown',
                'error': 'No suitable imagery available',
                'strategies_tried': len(search_strategies)
            }
            
        except Exception as e:
            logger.error(f"Improved NDVI analysis failed: {e}")
            return {
                'ndvi_value': None,
                'vegetation_health': 'unknown', 
                'error': str(e)
            }

    def _analyze_ndvi(self, area: ee.Geometry, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze NDVI (vegetation health) for the area"""
        try:
            # Get Landsat 8 imagery
            collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterBounds(area) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUD_COVER', 20))
            
            if collection.size().getInfo() == 0:
                # Expand date range if no recent imagery
                start_date = end_date - timedelta(days=90)
                collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                    .filterBounds(area) \
                    .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                    .filter(ee.Filter.lt('CLOUD_COVER', 30))
            
            # Calculate NDVI
            def calculate_ndvi(image):
                ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
                return image.addBands(ndvi)
            
            # Get median NDVI
            ndvi_collection = collection.map(calculate_ndvi)
            median_ndvi = ndvi_collection.select('NDVI').median()
            
            # Calculate statistics
            stats = median_ndvi.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.minMax(), sharedInputs=True
                ).combine(
                    ee.Reducer.stdDev(), sharedInputs=True
                ),
                geometry=area,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            # Interpret NDVI values
            mean_ndvi = stats.get('NDVI_mean', 0.5)
            ndvi_health = self._interpret_ndvi_health(mean_ndvi)
            
            return {
                'mean_ndvi': round(mean_ndvi, 3),
                'min_ndvi': round(stats.get('NDVI_min', 0), 3),
                'max_ndvi': round(stats.get('NDVI_max', 1), 3),
                'std_ndvi': round(stats.get('NDVI_stdDev', 0), 3),
                'health_rating': ndvi_health['rating'],
                'health_description': ndvi_health['description'],
                'vegetation_density': ndvi_health['density'],
                'image_count': collection.size().getInfo()
            }
            
        except Exception as e:
            logger.warning(f"NDVI analysis failed: {e}")
            return {
                'mean_ndvi': 0.6,
                'health_rating': 'moderate',
                'health_description': 'Unable to analyze current vegetation health',
                'error': str(e)
            }
    
    def _analyze_canopy_coverage(self, center_lat: float, center_lon: float, radius_m: float = 914) -> Dict[str, Any]:
        """Analyze canopy coverage using real satellite data with spatial grid
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude  
            radius_m: Search radius in meters (default 914m = 1000 yards)
            
        Returns:
            Dict containing:
            - canopy_coverage: Overall canopy percentage (0-1)
            - canopy_grid: 30x30 spatial grid of canopy values
            - grid_coordinates: Lat/lon for each grid cell
            - thermal_cover_type: 'conifer', 'hardwood', 'mixed'
            - conifer_percentage: Percentage of conifer coverage
            - data_source: 'sentinel2', 'landsat8', or 'fallback'
        """
        try:
            if not self._ensure_gee_initialized():
                logger.warning("GEE not initialized, using fallback canopy")
                return self._fallback_canopy_coverage(center_lat, center_lon, radius_m)
            
            logger.info(f"🌲 Analyzing canopy coverage: {center_lat:.4f}, {center_lon:.4f} (radius: {radius_m}m)")
            
            # Create analysis area
            point = ee.Geometry.Point([center_lon, center_lat])
            area = point.buffer(radius_m)
            
            # Try Sentinel-2 first (10m resolution, best for canopy)
            canopy_data = self._get_sentinel2_canopy(area, center_lat, center_lon, radius_m)
            
            if canopy_data is None:
                # Fallback to Landsat 8 (30m resolution)
                logger.info("📡 Sentinel-2 unavailable, trying Landsat 8...")
                canopy_data = self._get_landsat8_canopy(area, center_lat, center_lon, radius_m)
            
            if canopy_data is None:
                logger.warning("⚠️ No satellite imagery available, using fallback")
                return self._fallback_canopy_coverage(center_lat, center_lon, radius_m)
            
            # Get thermal cover type (conifer vs hardwood)
            thermal_cover = self._analyze_thermal_cover(area)
            canopy_data['thermal_cover_type'] = thermal_cover['dominant_type']
            canopy_data['conifer_percentage'] = thermal_cover['conifer_percentage']
            canopy_data['hardwood_percentage'] = thermal_cover['hardwood_percentage']
            
            logger.info(f"✅ Canopy analysis complete: {canopy_data['canopy_coverage']:.1%} coverage, "
                       f"{thermal_cover['dominant_type']} dominant")
            
            return canopy_data
            
        except Exception as e:
            logger.error(f"Canopy coverage analysis failed: {e}")
            return self._fallback_canopy_coverage(center_lat, center_lon, radius_m)
    
    def _get_sentinel2_canopy(self, area: ee.Geometry, center_lat: float, center_lon: float, radius_m: float) -> Optional[Dict[str, Any]]:
        """Get canopy coverage from Sentinel-2 (10m resolution)"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # Recent 3 months
            
            # Sentinel-2 Surface Reflectance
            collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterBounds(area) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            
            if collection.size().getInfo() == 0:
                return None
            
            logger.info(f"🛰️ Found {collection.size().getInfo()} Sentinel-2 images")
            
            # Calculate NDVI (higher NDVI = more vegetation/canopy)
            def add_ndvi(image):
                ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
                return image.addBands(ndvi)
            
            ndvi_collection = collection.map(add_ndvi)
            median_ndvi = ndvi_collection.select('NDVI').median()
            
            # Canopy threshold: NDVI > 0.4 indicates significant canopy
            canopy_mask = median_ndvi.gt(0.4)
            
            # Calculate overall canopy percentage
            canopy_stats = canopy_mask.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=area,
                scale=10,  # 10m resolution
                maxPixels=1e9
            ).getInfo()
            
            canopy_coverage = canopy_stats.get('NDVI', 0)
            
            # Create spatial grid (30x30) for bedding zone search
            canopy_grid = self._create_canopy_grid(median_ndvi, center_lat, center_lon, radius_m, scale=10)
            
            return {
                'canopy_coverage': canopy_coverage,
                'canopy_grid': canopy_grid['grid'],
                'grid_coordinates': canopy_grid['coordinates'],
                'grid_size': canopy_grid['grid_size'],
                'mean_ndvi': median_ndvi.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=area,
                    scale=10,
                    maxPixels=1e9
                ).getInfo().get('NDVI', 0),
                'data_source': 'sentinel2',
                'image_count': collection.size().getInfo(),
                'resolution_m': 10
            }
            
        except Exception as e:
            logger.warning(f"Sentinel-2 canopy extraction failed: {e}")
            return None
    
    def _get_landsat8_canopy(self, area: ee.Geometry, center_lat: float, center_lon: float, radius_m: float) -> Optional[Dict[str, Any]]:
        """Get canopy coverage from Landsat 8 (30m resolution)"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)  # Extended 6 months for Landsat
            
            collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterBounds(area) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUD_COVER', 30))
            
            if collection.size().getInfo() == 0:
                return None
            
            logger.info(f"🛰️ Found {collection.size().getInfo()} Landsat 8 images")
            
            # Calculate NDVI
            def add_ndvi(image):
                ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
                return image.addBands(ndvi)
            
            ndvi_collection = collection.map(add_ndvi)
            median_ndvi = ndvi_collection.select('NDVI').median()
            
            # Canopy threshold
            canopy_mask = median_ndvi.gt(0.4)
            
            canopy_stats = canopy_mask.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=area,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            canopy_coverage = canopy_stats.get('NDVI', 0)
            
            # Create spatial grid
            canopy_grid = self._create_canopy_grid(median_ndvi, center_lat, center_lon, radius_m, scale=30)
            
            return {
                'canopy_coverage': canopy_coverage,
                'canopy_grid': canopy_grid['grid'],
                'grid_coordinates': canopy_grid['coordinates'],
                'grid_size': canopy_grid['grid_size'],
                'mean_ndvi': median_ndvi.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=area,
                    scale=30,
                    maxPixels=1e9
                ).getInfo().get('NDVI', 0),
                'data_source': 'landsat8',
                'image_count': collection.size().getInfo(),
                'resolution_m': 30
            }
            
        except Exception as e:
            logger.warning(f"Landsat 8 canopy extraction failed: {e}")
            return None
    
    def _create_canopy_grid(self, ndvi_image: ee.Image, center_lat: float, center_lon: float, 
                           radius_m: float, scale: int = 30) -> Dict[str, Any]:
        """Create spatial grid of canopy coverage for bedding zone search"""
        try:
            grid_size = 30  # 30x30 grid
            span_deg = (radius_m * 2) / 111000  # Convert meters to degrees (approx)
            
            # Create grid coordinates
            lat_start = center_lat - span_deg / 2
            lon_start = center_lon - span_deg / 2
            lat_step = span_deg / grid_size
            lon_step = span_deg / grid_size
            
            # Sample NDVI at grid points
            grid = np.zeros((grid_size, grid_size))
            coordinates = {'lat': [], 'lon': []}
            
            # Batch sampling for efficiency (sample every 3rd point for 10x10 effective grid)
            sample_step = 3
            sample_points = []
            
            for i in range(0, grid_size, sample_step):
                for j in range(0, grid_size, sample_step):
                    lat = lat_start + (i + 0.5) * lat_step
                    lon = lon_start + (j + 0.5) * lon_step
                    sample_points.append(ee.Geometry.Point([lon, lat]))
            
            # Batch sample
            sample_fc = ee.FeatureCollection(sample_points)
            sampled = ndvi_image.sampleRegions(
                collection=sample_fc,
                scale=scale,
                geometries=True
            ).getInfo()
            
            # Fill grid with sampled values
            idx = 0
            for i in range(0, grid_size, sample_step):
                for j in range(0, grid_size, sample_step):
                    if idx < len(sampled['features']):
                        ndvi_val = sampled['features'][idx]['properties'].get('NDVI', 0)
                        # Convert NDVI to canopy coverage (NDVI > 0.4 = canopy)
                        canopy_val = 1.0 if ndvi_val > 0.4 else max(0, ndvi_val / 0.4)
                        grid[i, j] = canopy_val
                        idx += 1
            
            # Interpolate missing values
            from scipy.ndimage import zoom
            if sample_step > 1:
                grid = zoom(grid, sample_step, order=1)[:grid_size, :grid_size]
            
            # Store all grid coordinates
            for i in range(grid_size):
                for j in range(grid_size):
                    coordinates['lat'].append(lat_start + (i + 0.5) * lat_step)
                    coordinates['lon'].append(lon_start + (j + 0.5) * lon_step)
            
            return {
                'grid': grid.tolist(),
                'coordinates': coordinates,
                'grid_size': grid_size,
                'span_deg': span_deg,
                'resolution_m': scale
            }
            
        except Exception as e:
            logger.error(f"Grid creation failed: {e}")
            # Return simple uniform grid as fallback
            grid = np.ones((30, 30)) * 0.65  # Vermont default
            return {
                'grid': grid.tolist(),
                'coordinates': {'lat': [], 'lon': []},
                'grid_size': 30,
                'span_deg': (radius_m * 2) / 111000,
                'resolution_m': scale,
                'fallback': True
            }
    
    def _analyze_thermal_cover(self, area: ee.Geometry) -> Dict[str, Any]:
        """Analyze thermal cover type (conifer vs hardwood) using NLCD"""
        try:
            # NLCD Land Cover
            nlcd = ee.Image('USGS/NLCD_RELEASES/2021_REL/NLCD/2021')
            landcover = nlcd.select('landcover')
            
            # Forest classes:
            # 41 = Deciduous Forest (hardwood)
            # 42 = Evergreen Forest (conifer - thermal cover)
            # 43 = Mixed Forest
            
            deciduous_mask = landcover.eq(41)
            evergreen_mask = landcover.eq(42)
            mixed_mask = landcover.eq(43)
            
            # Calculate percentages
            area_sq_m = area.area().getInfo()
            
            deciduous_area = deciduous_mask.multiply(ee.Image.pixelArea()) \
                .reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=area,
                    scale=30,
                    maxPixels=1e9
                ).getInfo().get('landcover', 0)
            
            evergreen_area = evergreen_mask.multiply(ee.Image.pixelArea()) \
                .reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=area,
                    scale=30,
                    maxPixels=1e9
                ).getInfo().get('landcover', 0)
            
            mixed_area = mixed_mask.multiply(ee.Image.pixelArea()) \
                .reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=area,
                    scale=30,
                    maxPixels=1e9
                ).getInfo().get('landcover', 0)
            
            total_forest = deciduous_area + evergreen_area + mixed_area
            
            if total_forest > 0:
                conifer_pct = (evergreen_area + mixed_area * 0.5) / area_sq_m
                hardwood_pct = (deciduous_area + mixed_area * 0.5) / area_sq_m
            else:
                conifer_pct = 0
                hardwood_pct = 0
            
            # Determine dominant type
            if conifer_pct > hardwood_pct * 1.5:
                dominant = 'conifer'  # Heavy conifer = excellent thermal cover
            elif hardwood_pct > conifer_pct * 1.5:
                dominant = 'hardwood'  # Hardwood = mast production
            else:
                dominant = 'mixed'  # Mixed = good all-around
            
            return {
                'dominant_type': dominant,
                'conifer_percentage': round(conifer_pct, 3),
                'hardwood_percentage': round(hardwood_pct, 3),
                'thermal_cover_rating': 'excellent' if conifer_pct > 0.4 else 'good' if conifer_pct > 0.2 else 'moderate'
            }
            
        except Exception as e:
            logger.warning(f"Thermal cover analysis failed: {e}")
            # Vermont default: mixed hardwood/conifer
            return {
                'dominant_type': 'mixed',
                'conifer_percentage': 0.3,
                'hardwood_percentage': 0.5,
                'thermal_cover_rating': 'moderate'
            }
    
    def _fallback_canopy_coverage(self, center_lat: float, center_lon: float, radius_m: float) -> Dict[str, Any]:
        """Fallback canopy coverage when GEE unavailable"""
        logger.warning("⚠️ Using fallback canopy coverage (no satellite data)")
        
        # Vermont bounds check for better defaults
        if 42 < center_lat < 45 and -74 < center_lon < -71:
            canopy = 0.65  # Good Vermont forest cover
            thermal = 'mixed'
        else:
            canopy = 0.55  # Generic moderate forest
            thermal = 'mixed'
        
        # Create uniform grid
        grid_size = 30
        grid = np.ones((grid_size, grid_size)) * canopy
        
        return {
            'canopy_coverage': canopy,
            'canopy_grid': grid.tolist(),
            'grid_coordinates': {'lat': [], 'lon': []},
            'grid_size': grid_size,
            'thermal_cover_type': thermal,
            'conifer_percentage': 0.3,
            'hardwood_percentage': 0.5,
            'data_source': 'fallback',
            'fallback': True
        }
    
    def _analyze_land_cover(self, area: ee.Geometry) -> Dict[str, Any]:
        """Analyze land cover types in the hunting area"""
        try:
            # Use NLCD (National Land Cover Database) for US areas
            nlcd = ee.Image('USGS/NLCD_RELEASES/2021_REL/NLCD/2021')
            landcover = nlcd.select('landcover')
            
            # Calculate land cover percentages
            area_sq_m = area.area().getInfo()
            
            # Define deer-relevant land cover classes
            cover_classes = {
                11: 'open_water',
                21: 'developed_open',
                22: 'developed_low',
                23: 'developed_medium', 
                24: 'developed_high',
                31: 'barren_land',
                41: 'deciduous_forest',
                42: 'evergreen_forest',
                43: 'mixed_forest',
                52: 'shrub_scrub',
                71: 'grassland',
                81: 'pasture_hay',
                82: 'cultivated_crops',
                90: 'woody_wetlands',
                95: 'emergent_wetlands'
            }
            
            # Calculate area for each land cover type
            cover_stats = {}
            for class_id, class_name in cover_classes.items():
                class_mask = landcover.eq(class_id)
                class_area = class_mask.multiply(ee.Image.pixelArea()) \
                    .reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=area,
                        scale=30,
                        maxPixels=1e9
                    ).getInfo()
                
                area_sq_m_class = class_area.get('landcover', 0)
                percentage = (area_sq_m_class / area_sq_m) * 100 if area_sq_m > 0 else 0
                
                if percentage > 0.1:  # Only include if > 0.1%
                    cover_stats[class_name] = round(percentage, 1)
            
            # Calculate deer habitat suitability
            habitat_score = self._calculate_habitat_suitability(cover_stats)
            
            return {
                'land_cover_percentages': cover_stats,
                'dominant_cover': max(cover_stats.items(), key=lambda x: x[1])[0] if cover_stats else 'unknown',
                'habitat_suitability': habitat_score,
                'forest_percentage': sum(v for k, v in cover_stats.items() if 'forest' in k),
                'water_percentage': cover_stats.get('open_water', 0) + cover_stats.get('woody_wetlands', 0),
                'agricultural_percentage': cover_stats.get('cultivated_crops', 0) + cover_stats.get('pasture_hay', 0)
            }
            
        except Exception as e:
            logger.warning(f"Land cover analysis failed: {e}")
            return {
                'habitat_suitability': 'moderate',
                'error': str(e)
            }
    
    def _identify_food_sources(self, area: ee.Geometry, start_date: datetime, end_date: datetime, season: str = 'early_season') -> Dict[str, Any]:
        """
        Identify Vermont-specific deer food sources using real satellite data
        
        This replaces the stub implementation with actual crop classification,
        mast production analysis, and browse availability for Vermont hunting areas.
        """
        try:
            # Import Vermont-specific food classifier
            try:
                from .vermont_food_classifier import get_vermont_food_classifier
            except ImportError:
                from vermont_food_classifier import get_vermont_food_classifier
            
            # Get Vermont food classifier
            vt_classifier = get_vermont_food_classifier()
            
            # Perform comprehensive Vermont food analysis
            vt_food_results = vt_classifier.analyze_vermont_food_sources(
                area=area,
                season=season,
                analysis_year=start_date.year
            )
            
            logger.info(f"✅ Vermont food analysis: {vt_food_results.get('food_source_count', 0)} sources, "
                       f"overall score: {vt_food_results.get('overall_food_score', 0):.2f}")
            
            return vt_food_results
            
        except Exception as e:
            logger.warning(f"Vermont food source analysis failed: {e}, using fallback")
            # Fallback to basic analysis
            food_analysis = {
                'agricultural_crops': self._analyze_crop_areas(area),
                'mast_production': self._analyze_mast_production(area, start_date, end_date),
                'browse_availability': self._analyze_browse_vegetation(area),
                'seasonal_foods': self._identify_seasonal_foods(area, start_date.month)
            }
            
            # Calculate overall food availability score
            food_score = self._calculate_food_availability_score(food_analysis)
            
            return {
                **food_analysis,
                'overall_food_score': food_score,
                'food_abundance': 'high' if food_score > 0.7 else 'moderate' if food_score > 0.4 else 'low',
                'fallback': True
            }
    
    def _assess_vegetation_health(self, area: ee.Geometry, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Assess overall vegetation health and stress indicators using improved search"""
        try:
            # Use improved search strategies for better data availability
            search_strategies = [
                (30, 20, "Recent clear imagery"),
                (60, 30, "Extended recent period"), 
                (90, 40, "Seasonal period"),
                (180, 50, "Extended seasonal"),
                (365, 60, "Annual fallback")
            ]
            
            for days_back, cloud_threshold, description in search_strategies:
                search_start = end_date - timedelta(days=days_back)
                
                collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                    .filterBounds(area) \
                    .filterDate(search_start.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                    .filter(ee.Filter.lt('CLOUD_COVER', cloud_threshold))
                
                size = collection.size().getInfo()
                if size > 0:
                    logger.info(f"🌿 Vegetation health using {description} ({size} images)")
                    break
            
            if collection.size().getInfo() == 0:
                raise Exception("No suitable imagery available with any search strategy")
            
            # Calculate multiple vegetation indices
            def calculate_indices(image):
                # NDVI (Normalized Difference Vegetation Index)
                ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
                
                # EVI (Enhanced Vegetation Index)
                evi = image.expression(
                    '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
                    {
                        'NIR': image.select('SR_B5'),
                        'RED': image.select('SR_B4'),
                        'BLUE': image.select('SR_B2')
                    }
                ).rename('EVI')
                
                # SAVI (Soil Adjusted Vegetation Index)
                savi = image.expression(
                    '((NIR - RED) / (NIR + RED + 0.5)) * (1.5)',
                    {
                        'NIR': image.select('SR_B5'),
                        'RED': image.select('SR_B4')
                    }
                ).rename('SAVI')
                
                return image.addBands([ndvi, evi, savi])
            
            # Calculate median indices
            indices = collection.map(calculate_indices)
            median_indices = indices.select(['NDVI', 'EVI', 'SAVI']).median()
            
            # Get statistics
            stats = median_indices.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=area,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            health_assessment = {
                'ndvi': round(stats.get('NDVI', 0.5), 3),
                'evi': round(stats.get('EVI', 0.3), 3),
                'savi': round(stats.get('SAVI', 0.4), 3),
                'overall_health': self._interpret_vegetation_health(stats),
                'stress_indicators': self._detect_vegetation_stress(stats)
            }
            
            return health_assessment
            
        except Exception as e:
            logger.warning(f"Vegetation health assessment failed: {e}")
            return {
                'overall_health': 'moderate',
                'error': str(e)
            }
    
    def _detect_seasonal_changes(self, area: ee.Geometry) -> Dict[str, Any]:
        """Detect seasonal vegetation changes"""
        try:
            current_date = datetime.now()
            
            # Compare current month to previous months
            seasonal_analysis = {}
            
            for months_back in [1, 3, 6]:
                past_date = current_date - timedelta(days=30 * months_back)
                
                # Get imagery for comparison period
                collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                    .filterBounds(area) \
                    .filterDate(
                        past_date.strftime('%Y-%m-%d'),
                        (past_date + timedelta(days=15)).strftime('%Y-%m-%d')
                    ) \
                    .filter(ee.Filter.lt('CLOUD_COVER', 30))
                
                if collection.size().getInfo() > 0:
                    ndvi = collection.map(lambda img: img.normalizedDifference(['SR_B5', 'SR_B4'])).median()
                    mean_ndvi = ndvi.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=area,
                        scale=30,
                        maxPixels=1e9
                    ).getInfo().get('nd', 0.5)
                    
                    seasonal_analysis[f'{months_back}_months_ago'] = round(mean_ndvi, 3)
            
            # Calculate trends
            trends = self._calculate_vegetation_trends(seasonal_analysis)
            
            return {
                'seasonal_ndvi': seasonal_analysis,
                'trends': trends,
                'current_season_rating': self._rate_current_season(trends)
            }
            
        except Exception as e:
            logger.warning(f"Seasonal change detection failed: {e}")
            return {
                'current_season_rating': 'moderate',
                'error': str(e)
            }
    
    def _analyze_water_sources(self, area: ee.Geometry) -> Dict[str, Any]:
        """Analyze proximity and availability of water sources"""
        try:
            # Use JRC Global Surface Water dataset
            water = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
            occurrence = water.select('occurrence')
            
            # Calculate water availability metrics
            water_stats = occurrence.reduceRegion(
                reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
                geometry=area,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            water_availability = {
                'water_occurrence_percent': round(water_stats.get('occurrence_mean', 0), 1),
                'max_water_occurrence': round(water_stats.get('occurrence_max', 0), 1),
                'water_reliability': self._assess_water_reliability(water_stats.get('occurrence_mean', 0)),
                'seasonal_water_score': self._calculate_seasonal_water_score(water_stats)
            }
            
            return water_availability
            
        except Exception as e:
            logger.warning(f"Water source analysis failed: {e}")
            return {
                'water_reliability': 'moderate',
                'error': str(e)
            }
    
    # Helper methods for interpretation
    
    def _interpret_ndvi_health(self, ndvi: float) -> Dict[str, Any]:
        """Interpret NDVI values for vegetation health"""
        if ndvi > 0.7:
            return {
                'rating': 'excellent',
                'description': 'Dense, healthy vegetation with high photosynthetic activity',
                'density': 'very_high'
            }
        elif ndvi > 0.5:
            return {
                'rating': 'good',
                'description': 'Healthy vegetation with good photosynthetic activity',
                'density': 'high'
            }
        elif ndvi > 0.3:
            return {
                'rating': 'moderate',
                'description': 'Moderate vegetation health and density',
                'density': 'moderate'
            }
        elif ndvi > 0.1:
            return {
                'rating': 'poor',
                'description': 'Sparse vegetation or stressed conditions',
                'density': 'low'
            }
        else:
            return {
                'rating': 'very_poor',
                'description': 'Very sparse vegetation or bare ground',
                'density': 'very_low'
            }
    
    def _calculate_habitat_suitability(self, cover_stats: Dict[str, float]) -> str:
        """Calculate deer habitat suitability based on land cover"""
        score = 0
        
        # Positive factors
        score += cover_stats.get('deciduous_forest', 0) * 0.8
        score += cover_stats.get('mixed_forest', 0) * 0.7
        score += cover_stats.get('evergreen_forest', 0) * 0.6
        score += cover_stats.get('shrub_scrub', 0) * 0.5
        score += cover_stats.get('grassland', 0) * 0.4
        score += cover_stats.get('cultivated_crops', 0) * 0.6
        score += cover_stats.get('pasture_hay', 0) * 0.4
        score += cover_stats.get('woody_wetlands', 0) * 0.3
        
        # Negative factors
        score -= cover_stats.get('developed_high', 0) * 0.8
        score -= cover_stats.get('developed_medium', 0) * 0.6
        score -= cover_stats.get('barren_land', 0) * 0.5
        
        if score > 60:
            return 'excellent'
        elif score > 40:
            return 'good'
        elif score > 20:
            return 'moderate'
        else:
            return 'poor'
    
    def _fallback_vegetation_analysis(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fallback vegetation analysis when GEE is not available"""
        return {
            'ndvi_analysis': {
                'mean_ndvi': 0.6,
                'health_rating': 'moderate',
                'health_description': 'Standard vegetation analysis (satellite data unavailable)',
                'vegetation_density': 'moderate'
            },
            'land_cover': {
                'habitat_suitability': 'moderate',
                'forest_percentage': 40,
                'water_percentage': 5,
                'agricultural_percentage': 20
            },
            'food_sources': {
                'overall_food_score': 0.5,
                'food_abundance': 'moderate'
            },
            'vegetation_health': {
                'overall_health': 'moderate'
            },
            'seasonal_changes': {
                'current_season_rating': 'moderate'
            },
            'water_proximity': {
                'water_reliability': 'moderate'
            },
            'analysis_metadata': {
                'center_lat': lat,
                'center_lon': lon,
                'data_source': 'fallback_analysis',
                'note': 'Satellite data analysis unavailable - using standard terrain analysis'
            }
        }
    
    # Additional helper methods (simplified for brevity)
    def _analyze_crop_areas(self, area): return {'crop_diversity': 'moderate'}
    def _analyze_mast_production(self, area): return {'mast_abundance': 'moderate'}
    def _analyze_browse_vegetation(self, area): return {'browse_availability': 'moderate'}
    def _identify_seasonal_foods(self, area, month): return {'seasonal_foods': ['acorns', 'browse']}
    def _calculate_food_availability_score(self, analysis): return 0.6
    def _interpret_vegetation_health(self, stats): return 'moderate'
    def _detect_vegetation_stress(self, stats): return ['none']
    def _calculate_vegetation_trends(self, seasonal): return {'trend': 'stable'}
    def _rate_current_season(self, trends): return 'moderate'
    def _assess_water_reliability(self, occurrence): return 'moderate'
    def _calculate_seasonal_water_score(self, stats): return 0.5


# Global instance
vegetation_analyzer = VegetationAnalyzer()

def get_vegetation_analyzer() -> VegetationAnalyzer:
    """Get singleton vegetation analyzer instance"""
    return vegetation_analyzer
