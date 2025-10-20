"""
LIDAR Processing Service

Consolidates Vermont LIDAR data reading and terrain extraction into a reusable service.
Extracted from backend/vermont_lidar_reader.py to enable unit testing and service architecture.

Key Features:
- DEMFileManager: Manages DEM file discovery and caching (0.35m resolution offline capability)
- TerrainExtractor: Extracts terrain metrics from LIDAR data (slope, aspect, elevation)
- BatchLIDARProcessor: Process multiple locations efficiently (52-196 pts in one pass)

Provides 86× better resolution than GEE SRTM (0.35m vs 30m).

Author: GitHub Copilot + Rich Tremaine (Service Extraction)
Date: October 19, 2025
"""

import os
import logging
import numpy as np
from typing import Dict, Optional, Tuple, List
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


class DEMFileManager:
    """
    Manages DEM file discovery and access.
    
    Responsibilities:
    - Find LIDAR data directory (new layout: data/lidar/raw/vermont/)
    - Discover DEM and hillshade TIF files
    - Prioritize DEM files over hillshade (accurate vs visualization)
    - Check coverage for locations
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize DEM file manager.
        
        Args:
            data_dir: Optional custom data directory path
        """
        self.data_dir = data_dir or self._find_data_directory()
        self.lidar_files = self._discover_lidar_files()
        
        if self.lidar_files:
            logger.info(f"✅ Found {len(self.lidar_files)} LiDAR file(s): {list(self.lidar_files.keys())}")
        else:
            logger.warning("⚠️ No LiDAR TIF files found - will use SRTM fallback")
    
    def _find_data_directory(self) -> str:
        """Find the LiDAR data directory with support for new layout"""
        module_dir = Path(__file__).resolve().parent

        # Search both the new raw/ path and the legacy flat structure to stay compatible with older archives.
        candidate_dirs = [
            module_dir / ".." / ".." / "data" / "lidar" / "raw" / "vermont",
            Path.cwd() / "data" / "lidar" / "raw" / "vermont",
            Path("data/lidar/raw/vermont"),
            # Legacy paths kept for backwards compatibility
            module_dir / ".." / ".." / "data" / "lidar" / "vermont",
            Path.cwd() / "data" / "lidar" / "vermont",
            Path("data/lidar/vermont"),
            Path("/app/data/lidar/raw/vermont"),
            Path("/app/data/lidar/vermont")
        ]

        for candidate in candidate_dirs:
            if candidate.exists():
                return str(candidate.resolve())

        # Default to new layout so downstream logs push developers toward the updated structure.
        return str((Path.cwd() / "data" / "lidar" / "raw" / "vermont").resolve())
    
    def _discover_lidar_files(self) -> Dict[str, str]:
        """
        Discover all TIF files in the LiDAR directory.
        Prioritizes DEM files over hillshade files for accurate terrain data.
        
        Returns:
            Dict mapping file names to full paths (DEM files prioritized)
        """
        if not os.path.exists(self.data_dir):
            logger.warning(f"LiDAR directory not found: {self.data_dir}")
            return {}
        
        # Separate DEM and hillshade files
        dem_files = {}
        hillshade_files = {}
        
        for file in os.listdir(self.data_dir):
            if file.lower().endswith(('.tif', '.tiff')):
                full_path = os.path.join(self.data_dir, file)
                
                # Prioritize DEM files (DEMHF = hydro-flattened DEM)
                if 'DEM' in file.upper():
                    dem_files[file] = full_path
                    logger.info(f"📂 Discovered DEM file: {file} ⭐ (priority)")
                elif 'HILSHD' in file.upper():
                    hillshade_files[file] = full_path
                    logger.info(f"📂 Discovered hillshade file: {file}")
                else:
                    # Unknown type, add to hillshade category
                    hillshade_files[file] = full_path
                    logger.info(f"📂 Discovered LiDAR file: {file}")
        
        # Return DEM files first, then hillshade as fallback
        # Python 3.7+ preserves dict insertion order
        lidar_files = {**dem_files, **hillshade_files}
        
        if dem_files:
            logger.info(f"✅ Found {len(dem_files)} DEM file(s) - will use for accurate terrain data")
        if hillshade_files:
            logger.info(f"⚠️ Found {len(hillshade_files)} hillshade file(s) - fallback only")
        
        return lidar_files
    
    def has_coverage(self, lat: float, lon: float) -> bool:
        """
        Check if LiDAR coverage exists for a location.
        
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
            except (rasterio.RasterioIOError, OSError, ValueError) as e:
                logger.debug(f"Could not check {file_name}: {e}")
                continue
        
        return False
    
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
    
    def get_files(self) -> Dict[str, str]:
        """Get discovered LIDAR files (name -> path mapping)"""
        return self.lidar_files


class TerrainExtractor:
    """
    Extracts terrain metrics from LIDAR data.
    
    Responsibilities:
    - Extract point terrain (slope, aspect, elevation) using Horn's method
    - Calculate slope/aspect grids
    - Find terrain features (benches, saddles)
    - Match GEE SRTM algorithm for consistency
    """
    
    @staticmethod
    def extract_point_terrain(lat: float, lon: float, 
                            lidar_files: Dict[str, str],
                            sample_radius_m: int = 30) -> Optional[Dict]:
        """
        Extract point-specific terrain data (slope, aspect, elevation).
        
        This is the LIDAR-first foundation - provides same output format as GEE SRTM
        but at 86× better resolution (0.35m vs 30m).
        
        Args:
            lat: Latitude of point
            lon: Longitude of point
            lidar_files: Dictionary of file_name -> file_path
            sample_radius_m: Radius to sample around point (default 30m to match GEE)
        
        Returns:
            {
                'slope': float,        # Degrees (0-90)
                'aspect': float,       # Degrees (0-360, 0=N, 90=E, 180=S, 270=W)
                'elevation': float,    # Meters above sea level
                'resolution_m': float, # 0.35 typically
                'source': 'LIDAR_DEM' or 'LIDAR_HILLSHADE',
                'accurate_slopes': bool,  # True for DEM, False for hillshade
                'coverage': bool       # True if point has LIDAR coverage
            }
            Returns None if no LIDAR coverage at this point.
        """
        if not RASTERIO_AVAILABLE:
            logger.debug("Rasterio not available - cannot extract LIDAR point terrain")
            return None
        
        if not lidar_files:
            logger.debug("No LIDAR files available")
            return None
        
        # Try each LIDAR file until we find coverage
        for file_name, lidar_file in lidar_files.items():
            try:
                with rasterio.open(lidar_file) as src:
                    # Check if location is within bounds
                    if not TerrainExtractor._is_in_bounds(src, lat, lon):
                        continue
                    
                    # Transform lat/lon to raster coordinates
                    xs, ys = transform('EPSG:4326', src.crs, [lon], [lat])
                    x, y = xs[0], ys[0]
                    
                    # Get pixel coordinates
                    row, col = src.index(x, y)
                    
                    # Calculate pixel radius (30m / 0.35m ≈ 86 pixels)
                    resolution_m = src.res[0]
                    pixel_radius = max(3, int(sample_radius_m / resolution_m))  # Minimum 3 pixels
                    
                    # Define extraction window
                    window = Window(
                        col_off=max(0, col - pixel_radius),
                        row_off=max(0, row - pixel_radius),
                        width=min(pixel_radius * 2, src.width - col + pixel_radius),
                        height=min(pixel_radius * 2, src.height - row + pixel_radius)
                    )
                    
                    # Read elevation data
                    elevation_grid = src.read(1, window=window)
                    
                    # Handle edge cases
                    if elevation_grid.size < 9:  # Need at least 3×3 for calculations
                        logger.warning(f"Insufficient data at ({lat}, {lon}) - edge of coverage")
                        continue
                    
                    # Calculate center point elevation
                    center_row = min(pixel_radius, elevation_grid.shape[0] // 2)
                    center_col = min(pixel_radius, elevation_grid.shape[1] // 2)
                    
                    if center_row < 1 or center_col < 1:
                        logger.warning(f"Edge case at ({lat}, {lon}) - cannot calculate terrain")
                        continue
                    
                    center_elevation = float(elevation_grid[center_row, center_col])
                    
                    # Calculate slope and aspect using Horn's method
                    slope = TerrainExtractor._calculate_point_slope(
                        elevation_grid, resolution_m, center_row, center_col
                    )
                    aspect = TerrainExtractor._calculate_point_aspect(
                        elevation_grid, center_row, center_col
                    )
                    
                    logger.debug(
                        f"✅ LIDAR point terrain: {lat:.5f}, {lon:.5f} -> "
                        f"Slope={slope:.1f}°, Aspect={aspect:.0f}°, Elev={center_elevation:.0f}m"
                    )
                    
                    # Mark data source (DEM = accurate, hillshade = visualization)
                    if 'DEM' in file_name.upper():
                        source_type = 'LIDAR_DEM'
                        accurate_slopes = True
                    else:
                        source_type = 'LIDAR_HILLSHADE'
                        accurate_slopes = False
                    
                    return {
                        'slope': float(slope),
                        'aspect': float(aspect),
                        'elevation': float(center_elevation),
                        'resolution_m': float(resolution_m),
                        'source': source_type,
                        'accurate_slopes': accurate_slopes,
                        'coverage': True,
                        'file': os.path.basename(lidar_file)
                    }
                    
            except Exception as e:
                logger.debug(f"Error extracting point terrain from {file_name}: {e}")
                continue
        
        # No coverage found
        logger.debug(f"No LIDAR coverage for point terrain at ({lat:.5f}, {lon:.5f})")
        return None
    
    @staticmethod
    def _is_in_bounds(src, lat: float, lon: float) -> bool:
        """Check if lat/lon is within raster bounds"""
        try:
            # Transform lat/lon (EPSG:4326) to raster CRS
            xs, ys = transform('EPSG:4326', src.crs, [lon], [lat])
            x, y = xs[0], ys[0]
            
            # Check if transformed coordinates are within bounds
            bounds = src.bounds
            return (bounds.left <= x <= bounds.right and 
                   bounds.bottom <= y <= bounds.top)
        except Exception:
            return False
    
    @staticmethod
    def _calculate_point_slope(elevation_grid: np.ndarray, 
                              resolution_m: float,
                              center_row: int = None,
                              center_col: int = None) -> float:
        """
        Calculate slope at a point using Horn's method (matches GEE SRTM algorithm).
        
        Uses 3×3 kernel around center point:
        [a b c]
        [d e f]
        [g h i]
        
        dz/dx = ((c + 2f + i) - (a + 2d + g)) / (8 × resolution)
        dz/dy = ((g + 2h + i) - (a + 2b + c)) / (8 × resolution)
        slope = atan(sqrt(dz/dx² + dz/dy²)) × (180 / π)
        
        Args:
            elevation_grid: 2D numpy array of elevation values
            resolution_m: Grid resolution in meters
            center_row: Row index of center point (default: middle)
            center_col: Column index of center point (default: middle)
        
        Returns:
            Slope in degrees (0-90)
        """
        # Default to center of grid
        if center_row is None:
            center_row = elevation_grid.shape[0] // 2
        if center_col is None:
            center_col = elevation_grid.shape[1] // 2
        
        # Handle edge cases
        if (center_row < 1 or center_col < 1 or
            center_row >= elevation_grid.shape[0] - 1 or 
            center_col >= elevation_grid.shape[1] - 1):
            return 0.0
        
        # Extract 3×3 neighborhood
        a = float(elevation_grid[center_row - 1, center_col - 1])
        b = float(elevation_grid[center_row - 1, center_col])
        c = float(elevation_grid[center_row - 1, center_col + 1])
        d = float(elevation_grid[center_row, center_col - 1])
        # e = elevation_grid[center_row, center_col]  # center point (not used)
        f = float(elevation_grid[center_row, center_col + 1])
        g = float(elevation_grid[center_row + 1, center_col - 1])
        h = float(elevation_grid[center_row + 1, center_col])
        i = float(elevation_grid[center_row + 1, center_col + 1])
        
        # Horn's method for slope
        dz_dx = ((c + 2*f + i) - (a + 2*d + g)) / (8.0 * resolution_m)
        dz_dy = ((g + 2*h + i) - (a + 2*b + c)) / (8.0 * resolution_m)
        
        # Calculate slope in degrees
        slope_radians = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
        slope_degrees = np.degrees(slope_radians)
        
        # Clamp to valid range
        return float(np.clip(slope_degrees, 0.0, 90.0))
    
    @staticmethod
    def _calculate_point_aspect(elevation_grid: np.ndarray,
                                center_row: int = None,
                                center_col: int = None) -> float:
        """
        Calculate aspect (compass direction of steepest downslope).
        
        Args:
            elevation_grid: 2D numpy array of elevation values
            center_row: Row index of center point (default: middle)
            center_col: Column index of center point (default: middle)
        
        Returns:
            Aspect in degrees (0-360):
            0° = North, 90° = East, 180° = South, 270° = West
            Returns 0 if slope is flat (undefined aspect)
        """
        # Default to center of grid
        if center_row is None:
            center_row = elevation_grid.shape[0] // 2
        if center_col is None:
            center_col = elevation_grid.shape[1] // 2
        
        # Handle edge cases
        if (center_row < 1 or center_col < 1 or
            center_row >= elevation_grid.shape[0] - 1 or 
            center_col >= elevation_grid.shape[1] - 1):
            return 0.0
        
        # Extract 3×3 neighborhood
        a = float(elevation_grid[center_row - 1, center_col - 1])
        b = float(elevation_grid[center_row - 1, center_col])
        c = float(elevation_grid[center_row - 1, center_col + 1])
        d = float(elevation_grid[center_row, center_col - 1])
        f = float(elevation_grid[center_row, center_col + 1])
        g = float(elevation_grid[center_row + 1, center_col - 1])
        h = float(elevation_grid[center_row + 1, center_col])
        i = float(elevation_grid[center_row + 1, center_col + 1])
        
        # Calculate gradients
        dz_dx = ((c + 2*f + i) - (a + 2*d + g)) / 8.0
        dz_dy = ((g + 2*h + i) - (a + 2*b + c)) / 8.0
        
        # Check for flat slope
        if abs(dz_dx) < 0.001 and abs(dz_dy) < 0.001:
            return 0.0  # Flat slope, undefined aspect
        
        # Calculate aspect using atan2
        # atan2 returns angle in radians (-π to π)
        # We want 0=North, 90=East, 180=South, 270=West
        aspect_radians = np.arctan2(-dz_dy, dz_dx)
        
        # Convert to degrees
        aspect_degrees = np.degrees(aspect_radians)
        
        # Adjust to compass bearing (0=N, 90=E, 180=S, 270=W)
        aspect_degrees = 90.0 - aspect_degrees
        
        # Normalize to 0-360
        while aspect_degrees < 0:
            aspect_degrees += 360
        while aspect_degrees >= 360:
            aspect_degrees -= 360
        
        return float(aspect_degrees)
    
    @staticmethod
    def calculate_slope_grid(elevation_grid: np.ndarray) -> np.ndarray:
        """Calculate slope grid from elevation grid"""
        # Simple gradient-based slope calculation
        dy, dx = np.gradient(elevation_grid)
        slope = np.sqrt(dx**2 + dy**2)
        return slope


class BatchLIDARProcessor:
    """
    Process multiple locations efficiently in batch mode.
    
    Responsibilities:
    - Batch extract terrain for 52-196 candidates in one pass
    - Cache results to avoid repeated processing
    - Provide performance metrics
    - Key optimization for alternative search (vs 52 sequential GEE API calls)
    """
    
    def __init__(self, dem_manager: DEMFileManager, terrain_extractor: TerrainExtractor):
        """
        Initialize batch processor.
        
        Args:
            dem_manager: DEMFileManager instance for file access
            terrain_extractor: TerrainExtractor instance for terrain calculations
        """
        self.dem_manager = dem_manager
        self.terrain_extractor = terrain_extractor
    
    def batch_extract(self, 
                     coordinates: List[Tuple[float, float]],
                     sample_radius_m: int = 30) -> Dict[str, Dict]:
        """
        Extract terrain for multiple points simultaneously (batch mode).
        
        This is the key optimization for alternative search - extracts all 52-196 
        candidates in one pass instead of 52 sequential GEE API calls.
        
        Args:
            coordinates: List of (lat, lon) tuples
            sample_radius_m: Radius to sample around each point
        
        Returns:
            Dictionary mapping "lat,lon" to terrain dict
            {
                "44.5009,-72.6988": {
                    'slope': 6.6,
                    'aspect': 169.0,
                    'elevation': 379.0,
                    'source': 'LIDAR_DEM',
                    'coverage': True
                },
                ...
            }
        """
        import time
        
        terrain_cache = {}
        lidar_files = self.dem_manager.get_files()
        
        logger.info(f"🗺️ LIDAR BATCH EXTRACTION: Processing {len(coordinates)} locations")
        start_time = time.time()
        
        for lat, lon in coordinates:
            key = f"{lat:.6f},{lon:.6f}"
            terrain = self.terrain_extractor.extract_point_terrain(
                lat, lon, lidar_files, sample_radius_m
            )
            
            if terrain and terrain.get('coverage'):
                terrain_cache[key] = terrain
            else:
                # Mark as no coverage (will trigger GEE fallback)
                terrain_cache[key] = {'coverage': False}
        
        elapsed = time.time() - start_time
        coverage_count = sum(1 for t in terrain_cache.values() if t.get('coverage'))
        
        # Calculate rate (avoid division by zero)
        rate = len(coordinates) / elapsed if elapsed > 0 else 0
        
        logger.info(
            f"✅ LIDAR BATCH COMPLETE: {coverage_count}/{len(coordinates)} "
            f"with coverage ({elapsed:.2f}s, {rate:.1f} pts/sec)"
        )
        
        return terrain_cache


# Singleton instance for easy access
_lidar_processor_instance = None

def get_lidar_processor() -> Tuple[DEMFileManager, TerrainExtractor, BatchLIDARProcessor]:
    """
    Get singleton LIDAR processor instances.
    
    Returns:
        Tuple of (DEMFileManager, TerrainExtractor, BatchLIDARProcessor)
    """
    global _lidar_processor_instance
    if _lidar_processor_instance is None:
        dem_manager = DEMFileManager()
        terrain_extractor = TerrainExtractor()
        batch_processor = BatchLIDARProcessor(dem_manager, terrain_extractor)
        _lidar_processor_instance = (dem_manager, terrain_extractor, batch_processor)
    return _lidar_processor_instance
