#!/usr/bin/env python3
"""
LiDAR Data Processing Pipeline
Processes raw LiDAR data into formats suitable for deer prediction analysis
"""

import os
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
import subprocess
import tempfile
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TerrainMetrics:
    """Container for terrain analysis metrics"""
    elevation_min: float
    elevation_max: float
    elevation_mean: float
    slope_mean: float
    slope_max: float
    aspect_mean: float
    roughness: float
    canopy_height_mean: float
    canopy_density: float

@dataclass
class LidarTile:
    """Container for LiDAR tile information"""
    tile_id: str
    bounds: List[float]  # [west, south, east, north]
    elevation_file: Optional[Path]
    lidar_file: Optional[Path]
    processed_files: Dict[str, Path]
    metrics: Optional[TerrainMetrics]

class LidarProcessor:
    """Processes LiDAR data for deer prediction analysis"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.raw_data_dir = self.base_dir / "raw_data"
        self.processed_dir = self.base_dir / "processed"
        self.cache_dir = self.processed_dir / "cache"
        
        # Ensure directories exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Processing parameters
        self.target_resolution = 1.0  # meters
        self.slope_window_size = 3    # 3x3 window for slope calculation
        self.roughness_window_size = 5 # 5x5 window for roughness
    
    def discover_tiles(self) -> List[LidarTile]:
        """Discover all available LiDAR tiles"""
        tiles = []
        
        for tile_dir in self.raw_data_dir.iterdir():
            if tile_dir.is_dir():
                tile_id = tile_dir.name
                
                # Find elevation and LiDAR files
                elevation_file = None
                lidar_file = None
                
                for file_path in tile_dir.iterdir():
                    if file_path.suffix.lower() in ['.tif', '.tiff'] and 'dem' in file_path.name.lower():
                        elevation_file = file_path
                    elif file_path.suffix.lower() in ['.las', '.laz']:
                        lidar_file = file_path
                
                if elevation_file or lidar_file:
                    tile = LidarTile(
                        tile_id=tile_id,
                        bounds=[0, 0, 0, 0],  # Will be calculated from file
                        elevation_file=elevation_file,
                        lidar_file=lidar_file,
                        processed_files={},
                        metrics=None
                    )
                    tiles.append(tile)
        
        logger.info(f"Discovered {len(tiles)} LiDAR tiles")
        return tiles
    
    def calculate_slope_aspect(self, elevation_array: np.ndarray, 
                             pixel_size: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate slope and aspect from elevation data"""
        # Use numpy gradient to calculate slope
        grad_x, grad_y = np.gradient(elevation_array, pixel_size)
        
        # Calculate slope in degrees
        slope = np.arctan(np.sqrt(grad_x**2 + grad_y**2)) * 180 / np.pi
        
        # Calculate aspect in degrees (0-360)
        aspect = np.arctan2(-grad_x, grad_y) * 180 / np.pi
        aspect = np.where(aspect < 0, aspect + 360, aspect)
        
        return slope, aspect
    
    def calculate_roughness(self, elevation_array: np.ndarray, 
                          window_size: int = 5) -> np.ndarray:
        """Calculate terrain roughness using standard deviation"""
        from scipy.ndimage import generic_filter
        
        def std_filter(values):
            return np.std(values)
        
        roughness = generic_filter(elevation_array, std_filter, 
                                 size=window_size, mode='constant')
        return roughness
    
    def process_elevation_data(self, tile: LidarTile) -> Dict[str, np.ndarray]:
        """Process elevation data to extract terrain metrics"""
        if not tile.elevation_file or not tile.elevation_file.exists():
            logger.warning(f"No elevation file found for tile {tile.tile_id}")
            return {}
        
        logger.info(f"Processing elevation data for tile {tile.tile_id}")
        
        try:
            # For now, simulate processing - in real implementation would use GDAL
            # to read the GeoTIFF file and extract elevation data
            
            # Simulate elevation data (replace with actual GDAL reading)
            elevation_data = self._simulate_elevation_data()
            
            # Calculate slope and aspect
            slope, aspect = self.calculate_slope_aspect(elevation_data)
            
            # Calculate roughness
            roughness = self.calculate_roughness(elevation_data)
            
            processed_data = {
                'elevation': elevation_data,
                'slope': slope,
                'aspect': aspect,
                'roughness': roughness
            }
            
            # Save processed data
            output_dir = self.processed_dir / tile.tile_id
            output_dir.mkdir(exist_ok=True)
            
            for data_type, data_array in processed_data.items():
                output_file = output_dir / f"{data_type}.npy"
                np.save(output_file, data_array)
                tile.processed_files[data_type] = output_file
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to process elevation data for {tile.tile_id}: {e}")
            return {}
    
    def _simulate_elevation_data(self, size: Tuple[int, int] = (500, 500)) -> np.ndarray:
        """Simulate elevation data for testing (remove when GDAL is integrated)"""
        np.random.seed(42)  # For reproducible results
        
        # Create realistic terrain with hills and valleys
        x = np.linspace(0, 10, size[0])
        y = np.linspace(0, 10, size[1])
        X, Y = np.meshgrid(x, y)
        
        # Base elevation with some hills
        elevation = (
            100 + 
            20 * np.sin(X * 0.5) * np.cos(Y * 0.3) +
            15 * np.sin(X * 0.8) * np.sin(Y * 0.6) +
            5 * np.random.normal(0, 1, size)  # Add noise
        )
        
        return elevation.astype(np.float32)
    
    def extract_canopy_metrics(self, tile: LidarTile) -> Dict[str, float]:
        """Extract canopy height and density from LiDAR point cloud"""
        if not tile.lidar_file or not tile.lidar_file.exists():
            logger.warning(f"No LiDAR file found for tile {tile.tile_id}")
            return {}
        
        logger.info(f"Processing LiDAR points for tile {tile.tile_id}")
        
        try:
            # For now, simulate canopy metrics - in real implementation would use
            # laspy or PDAL to process the point cloud
            
            canopy_metrics = {
                'canopy_height_mean': np.random.uniform(8, 25),  # meters
                'canopy_height_max': np.random.uniform(25, 40),
                'canopy_density': np.random.uniform(0.3, 0.9),  # 0-1 scale
                'understory_density': np.random.uniform(0.1, 0.6),
                'ground_visibility': np.random.uniform(0.2, 0.8)
            }
            
            logger.info(f"Extracted canopy metrics: {canopy_metrics}")
            return canopy_metrics
            
        except Exception as e:
            logger.error(f"Failed to extract canopy metrics for {tile.tile_id}: {e}")
            return {}
    
    def calculate_terrain_metrics(self, tile: LidarTile) -> TerrainMetrics:
        """Calculate comprehensive terrain metrics for a tile"""
        # Process elevation data
        elevation_data = self.process_elevation_data(tile)
        
        # Extract canopy metrics
        canopy_data = self.extract_canopy_metrics(tile)
        
        if not elevation_data:
            logger.warning(f"No elevation data available for metrics calculation: {tile.tile_id}")
            return None
        
        # Calculate metrics
        elevation = elevation_data['elevation']
        slope = elevation_data['slope']
        aspect = elevation_data['aspect']
        roughness = elevation_data['roughness']
        
        metrics = TerrainMetrics(
            elevation_min=float(np.min(elevation)),
            elevation_max=float(np.max(elevation)),
            elevation_mean=float(np.mean(elevation)),
            slope_mean=float(np.mean(slope)),
            slope_max=float(np.max(slope)),
            aspect_mean=float(np.mean(aspect)),
            roughness=float(np.mean(roughness)),
            canopy_height_mean=canopy_data.get('canopy_height_mean', 0.0),
            canopy_density=canopy_data.get('canopy_density', 0.0)
        )
        
        # Save metrics
        metrics_file = self.processed_dir / tile.tile_id / "metrics.json"
        metrics_file.parent.mkdir(exist_ok=True)
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics.__dict__, f, indent=2)
        
        tile.metrics = metrics
        return metrics
    
    def process_all_tiles(self) -> List[LidarTile]:
        """Process all discovered tiles"""
        tiles = self.discover_tiles()
        
        logger.info(f"Processing {len(tiles)} tiles...")
        
        processed_tiles = []
        for tile in tiles:
            logger.info(f"Processing tile {tile.tile_id}")
            
            try:
                metrics = self.calculate_terrain_metrics(tile)
                if metrics:
                    processed_tiles.append(tile)
                    logger.info(f"Successfully processed {tile.tile_id}")
                else:
                    logger.warning(f"Failed to calculate metrics for {tile.tile_id}")
                    
            except Exception as e:
                logger.error(f"Error processing tile {tile.tile_id}: {e}")
        
        logger.info(f"Successfully processed {len(processed_tiles)} tiles")
        return processed_tiles
    
    def get_terrain_data(self, lat: float, lng: float, radius: float = 100) -> Dict:
        """Get terrain data for a specific location"""
        # Find relevant tiles
        relevant_tiles = []
        for tile in self.discover_tiles():
            # Simple check - in real implementation would use proper spatial queries
            if tile.processed_files:
                relevant_tiles.append(tile)
        
        if not relevant_tiles:
            logger.warning(f"No processed tiles found for location {lat}, {lng}")
            return {}
        
        # For now, return data from first relevant tile
        # In real implementation, would interpolate from multiple tiles
        tile = relevant_tiles[0]
        
        terrain_data = {}
        for data_type, file_path in tile.processed_files.items():
            if file_path.exists():
                data_array = np.load(file_path)
                
                # Extract data around the specified location
                # For now, return a sample from the center of the array
                center_idx = (data_array.shape[0] // 2, data_array.shape[1] // 2)
                sample_size = min(int(radius / self.target_resolution), 50)
                
                start_row = max(0, center_idx[0] - sample_size)
                end_row = min(data_array.shape[0], center_idx[0] + sample_size)
                start_col = max(0, center_idx[1] - sample_size)
                end_col = min(data_array.shape[1], center_idx[1] + sample_size)
                
                terrain_data[data_type] = data_array[start_row:end_row, start_col:end_col]
        
        return terrain_data

def main():
    """Main function for testing"""
    processor = LidarProcessor()
    
    logger.info("Starting LiDAR processing pipeline...")
    
    # Process all tiles
    processed_tiles = processor.process_all_tiles()
    
    logger.info(f"Processing complete. {len(processed_tiles)} tiles processed.")
    
    # Test terrain data extraction
    if processed_tiles:
        test_lat, test_lng = 44.26, -72.58  # Montpelier area
        terrain_data = processor.get_terrain_data(test_lat, test_lng)
        logger.info(f"Sample terrain data keys: {list(terrain_data.keys())}")

if __name__ == "__main__":
    main()
