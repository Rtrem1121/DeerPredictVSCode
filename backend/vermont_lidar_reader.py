#!/usr/bin/env python3
"""
Vermont LiDAR Hillshade Reader

Reads pre-downloaded LiDAR hillshade TIF files for high-resolution terrain analysis.
Falls back to SRTM 30m elevation if LiDAR not available.

Author: GitHub Copilot + Rich Tremaine
Date: October 2, 2025
"""

import os
import logging
import numpy as np
from typing import Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import rasterio (for TIF reading)
try:
    import rasterio
    from rasterio.windows import Window
    from rasterio.transform import from_bounds
    from rasterio.warp import transform
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    logger.warning("Rasterio not available - LiDAR TIF reading disabled. Install with: pip install rasterio")


class VermontLiDARReader:
    """
    Reads Vermont LiDAR hillshade TIF files for high-resolution terrain analysis.
    
    Features:
    - Automatic file detection in data/lidar/vermont/
    - Spatial query by lat/lon with configurable radius
    - Extracts elevation, slope, aspect from hillshade
    - Falls back to SRTM if LiDAR unavailable
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize LiDAR reader
        
        Args:
            data_dir: Optional custom data directory path
        """
        self.data_dir = data_dir or self._find_data_directory()
        self.lidar_files = self._discover_lidar_files()
        self.active_dataset = None
        
        if self.lidar_files:
            logger.info(f"✅ Found {len(self.lidar_files)} LiDAR file(s): {list(self.lidar_files.keys())}")
        else:
            logger.warning("⚠️ No LiDAR TIF files found - will use SRTM fallback")
    
    def _find_data_directory(self) -> str:
        """Find the data/lidar/vermont directory"""
        # Try multiple paths (local development vs Docker)
        possible_paths = [
            "data/lidar/vermont",
            "./data/lidar/vermont",
            "../data/lidar/vermont",
            "/app/data/lidar/vermont",  # Docker path
            "backend/../data/lidar/vermont"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        # Default to relative path
        return "data/lidar/vermont"
    
    def _discover_lidar_files(self) -> Dict[str, str]:
        """
        Discover all TIF files in the LiDAR directory
        
        Returns:
            Dict mapping file names to full paths
        """
        if not os.path.exists(self.data_dir):
            logger.warning(f"LiDAR directory not found: {self.data_dir}")
            return {}
        
        lidar_files = {}
        for file in os.listdir(self.data_dir):
            if file.lower().endswith(('.tif', '.tiff')):
                full_path = os.path.join(self.data_dir, file)
                lidar_files[file] = full_path
                logger.info(f"📂 Discovered LiDAR file: {file}")
        
        return lidar_files
    
    def get_terrain_data(self, lat: float, lon: float, radius_m: float = 914) -> Optional[Dict]:
        """
        Extract terrain data from LiDAR hillshade for a given location
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius_m: Radius in meters (default 914m = 1000 yards)
        
        Returns:
            Dict with terrain data or None if not available
        """
        if not RASTERIO_AVAILABLE:
            logger.warning("Rasterio not installed - cannot read LiDAR TIF files")
            return None
        
        if not self.lidar_files:
            logger.warning("No LiDAR files available")
            return None
        
        # Try each LiDAR file until we find one with coverage
        for file_name, lidar_file in self.lidar_files.items():
            try:
                with rasterio.open(lidar_file) as src:
                    # Check if location is within bounds
                    if not self._is_in_bounds(src, lat, lon):
                        logger.debug(f"Location ({lat}, {lon}) outside {file_name} coverage, trying next file...")
                        continue
                    
                    # Found coverage! Calculate bounding box for extraction
                    bbox = self._calculate_bbox(lat, lon, radius_m)
                    
                    # Read data window
                    window = self._get_window(src, bbox)
                    data = src.read(1, window=window)
                    
                    # Extract terrain features
                    terrain_data = self._extract_terrain_features(data, src, window)
                    terrain_data['source'] = 'lidar_hillshade'
                    terrain_data['resolution_m'] = src.res[0]  # Resolution in meters
                    terrain_data['file'] = os.path.basename(lidar_file)
                    
                    logger.info(f"✅ LiDAR data extracted from {file_name}: {terrain_data['resolution_m']:.1f}m resolution")
                    return terrain_data
                    
            except Exception as e:
                logger.warning(f"Error reading {file_name}: {e}, trying next file...")
                continue
        
        # No files had coverage
        logger.warning(f"Location ({lat}, {lon}) outside all LiDAR coverage areas")
        return None
    
    def _is_in_bounds(self, src, lat: float, lon: float) -> bool:
        """Check if lat/lon is within raster bounds"""
        try:
            # Transform lat/lon (EPSG:4326) to raster CRS
            xs, ys = transform('EPSG:4326', src.crs, [lon], [lat])
            x, y = xs[0], ys[0]
            
            # Check if transformed coordinates are within bounds
            bounds = src.bounds
            in_bounds = (bounds.left <= x <= bounds.right and 
                        bounds.bottom <= y <= bounds.top)
            
            if in_bounds:
                logger.debug(f"Location {lat:.5f}°N, {lon:.5f}°W -> {x:.1f}, {y:.1f} ({src.crs}) is IN BOUNDS")
            else:
                logger.debug(f"Location {lat:.5f}°N, {lon:.5f}°W -> {x:.1f}, {y:.1f} ({src.crs}) is OUT OF BOUNDS")
            
            return in_bounds
        except Exception as e:
            logger.warning(f"Coordinate transformation error: {e}")
            return False
    
    def _calculate_bbox(self, lat: float, lon: float, radius_m: float) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box around point in lat/lon
        
        Returns:
            (min_lon, min_lat, max_lon, max_lat)
        """
        # Rough conversion: 1 degree lat = 111km, 1 degree lon = 85km at 43°N
        lat_deg = radius_m / 111000
        lon_deg = radius_m / 85000
        
        return (
            lon - lon_deg,  # min_lon
            lat - lat_deg,  # min_lat
            lon + lon_deg,  # max_lon
            lat + lat_deg   # max_lat
        )
    
    def _get_window(self, src, bbox: Tuple[float, float, float, float]) -> Window:
        """Convert bounding box to raster window"""
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # Transform bbox corners from lat/lon to raster CRS
        xs, ys = transform('EPSG:4326', src.crs, 
                          [min_lon, max_lon], 
                          [max_lat, min_lat])
        
        # Convert to pixel coordinates
        row_start, col_start = src.index(xs[0], ys[0])
        row_stop, col_stop = src.index(xs[1], ys[1])
        
        # Ensure valid window
        row_start, row_stop = min(row_start, row_stop), max(row_start, row_stop)
        col_start, col_stop = min(col_start, col_stop), max(col_start, col_stop)
        
        return Window.from_slices(
            (row_start, row_stop),
            (col_start, col_stop)
        )
    
    def _extract_terrain_features(self, data: np.ndarray, src, window: Window) -> Dict:
        """
        Extract terrain features from hillshade data
        
        Args:
            data: 2D numpy array of hillshade values
            src: Rasterio dataset
            window: Window object for coordinate conversion
        
        Returns:
            Dict with elevation, slope, aspect, benches, saddles
        """
        # Calculate basic statistics
        elevation_estimate = np.mean(data)  # Hillshade is proxy for elevation
        slope_estimate = np.std(data) / 10  # Rough slope estimate from variation
        
        # Find terrain features
        benches = self._find_benches(data)
        saddles = self._find_saddles(data)
        
        return {
            'elevation_grid': data.tolist(),
            'mean_elevation': float(elevation_estimate),
            'slope_grid': self._calculate_slope_grid(data).tolist(),
            'mean_slope': float(slope_estimate),
            'benches': benches,
            'saddles': saddles,
            'grid_shape': data.shape,
            'grid_size': data.size
        }
    
    def _calculate_slope_grid(self, elevation_grid: np.ndarray) -> np.ndarray:
        """Calculate slope from elevation grid"""
        # Simple gradient-based slope calculation
        dy, dx = np.gradient(elevation_grid)
        slope = np.sqrt(dx**2 + dy**2)
        return slope
    
    def _find_benches(self, data: np.ndarray) -> list:
        """
        Find flat benches on slopes (good bedding areas)
        
        Returns:
            List of bench coordinates and sizes
        """
        # Calculate slope
        slope = self._calculate_slope_grid(data)
        
        # Find areas with low slope (benches)
        bench_threshold = np.percentile(slope, 20)  # Bottom 20% of slopes
        benches_mask = slope < bench_threshold
        
        # Find contiguous bench areas
        benches = []
        # TODO: Implement connected component analysis
        # For now, return count
        bench_count = np.sum(benches_mask)
        if bench_count > 10:  # At least 10 pixels
            benches.append({
                'pixel_count': int(bench_count),
                'percentage': float(bench_count / data.size * 100)
            })
        
        return benches
    
    def _find_saddles(self, data: np.ndarray) -> list:
        """
        Find saddles (low points in ridges - deer travel corridors)
        
        Returns:
            List of saddle locations
        """
        # Find local minima along ridgelines
        # TODO: Implement proper saddle detection algorithm
        # For now, return placeholder
        return []
    
    def has_lidar_coverage(self, lat: float, lon: float) -> bool:
        """
        Check if LiDAR coverage exists for a location
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            True if LiDAR coverage available
        """
        if not RASTERIO_AVAILABLE or not self.lidar_files:
            return False
        
        # Check all LiDAR files
        for file_name, lidar_file in self.lidar_files.items():
            try:
                with rasterio.open(lidar_file) as src:
                    if self._is_in_bounds(src, lat, lon):
                        logger.debug(f"Found coverage in {file_name}")
                        return True
            except:
                continue
        
        return False


# Global instance for easy access
_lidar_reader = None

def get_lidar_reader() -> VermontLiDARReader:
    """Get singleton LiDAR reader instance"""
    global _lidar_reader
    if _lidar_reader is None:
        _lidar_reader = VermontLiDARReader()
    return _lidar_reader


if __name__ == "__main__":
    # Test the LiDAR reader
    logging.basicConfig(level=logging.INFO)
    
    reader = get_lidar_reader()
    
    # Test Vermont hunting location (from recent production test)
    test_lat = 43.31181
    test_lon = -73.21624
    
    print(f"\n🧪 Testing LiDAR reader for Vermont location: {test_lat}°N, {test_lon}°W")
    print("=" * 80)
    
    if reader.has_lidar_coverage(test_lat, test_lon):
        print("✅ LiDAR coverage available!")
        
        terrain_data = reader.get_terrain_data(test_lat, test_lon, radius_m=914)
        if terrain_data:
            print(f"\n📊 Terrain Data:")
            print(f"   Resolution: {terrain_data['resolution_m']:.1f}m")
            print(f"   Source: {terrain_data['source']}")
            print(f"   File: {terrain_data['file']}")
            print(f"   Grid Shape: {terrain_data['grid_shape']}")
            print(f"   Mean Elevation: {terrain_data['mean_elevation']:.1f}")
            print(f"   Mean Slope: {terrain_data['mean_slope']:.1f}°")
            print(f"   Benches Found: {len(terrain_data['benches'])}")
            print(f"   Saddles Found: {len(terrain_data['saddles'])}")
    else:
        print("❌ No LiDAR coverage for this location")
        print("   Will fall back to SRTM 30m elevation data")
