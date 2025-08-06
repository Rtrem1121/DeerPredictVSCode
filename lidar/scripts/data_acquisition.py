#!/usr/bin/env python3
"""
Vermont LiDAR Data Acquisition Script
Downloads and manages Vermont statewide LiDAR data from geodata.vermont.gov
"""

import os
import requests
import logging
from pathlib import Path
from typing import List, Dict, Optional
import json
from urllib.parse import urljoin
import zipfile
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VermontLidarDownloader:
    """Handles downloading and managing Vermont LiDAR data"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.raw_data_dir = self.base_dir / "raw_data"
        self.processed_dir = self.base_dir / "processed"
        self.metadata_file = self.base_dir / "lidar_metadata.json"
        
        # Ensure directories exist
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Vermont LiDAR data sources
        self.data_sources = {
            "elevation_1m": {
                "url": "https://geodata.vermont.gov/datasets/vt-elevation-1-meter-dem",
                "description": "1-meter Digital Elevation Model",
                "file_pattern": "*_1m_dem.tif"
            },
            "elevation_3m": {
                "url": "https://geodata.vermont.gov/datasets/vt-elevation-3-meter-dem", 
                "description": "3-meter Digital Elevation Model",
                "file_pattern": "*_3m_dem.tif"
            },
            "lidar_points": {
                "url": "https://geodata.vermont.gov/datasets/vt-lidar-point-cloud",
                "description": "LiDAR Point Cloud Data",
                "file_pattern": "*.las"
            }
        }
    
    def load_metadata(self) -> Dict:
        """Load existing metadata or create new"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            "downloads": {},
            "last_updated": None,
            "data_sources": self.data_sources
        }
    
    def save_metadata(self, metadata: Dict):
        """Save metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def download_file(self, url: str, destination: Path, chunk_size: int = 8192) -> bool:
        """Download file with progress tracking"""
        try:
            logger.info(f"Downloading {url} to {destination}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            logger.info(f"Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")
            
            logger.info(f"Successfully downloaded {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            if destination.exists():
                destination.unlink()  # Remove partial file
            return False
    
    def discover_vermont_tiles(self) -> List[Dict]:
        """Discover available Vermont LiDAR tiles"""
        # This would typically query the Vermont GIS portal API
        # For now, we'll return a sample structure
        
        logger.info("Discovering Vermont LiDAR tiles...")
        
        # Sample tile structure - in real implementation, this would query the API
        sample_tiles = [
            {
                "tile_id": "VT_001_001",
                "bounds": [-73.5, 42.7, -73.4, 42.8],  # [west, south, east, north]
                "county": "Bennington",
                "elevation_1m_url": "https://geodata.vermont.gov/downloads/VT_001_001_1m_dem.tif",
                "lidar_points_url": "https://geodata.vermont.gov/downloads/VT_001_001_lidar.las",
                "size_mb": 125
            },
            {
                "tile_id": "VT_002_001", 
                "bounds": [-73.4, 42.7, -73.3, 42.8],
                "county": "Bennington",
                "elevation_1m_url": "https://geodata.vermont.gov/downloads/VT_002_001_1m_dem.tif",
                "lidar_points_url": "https://geodata.vermont.gov/downloads/VT_002_001_lidar.las",
                "size_mb": 130
            }
            # Add more tiles as discovered
        ]
        
        logger.info(f"Found {len(sample_tiles)} available tiles")
        return sample_tiles
    
    def download_tile(self, tile_info: Dict) -> bool:
        """Download a specific LiDAR tile"""
        tile_id = tile_info["tile_id"]
        logger.info(f"Processing tile {tile_id}")
        
        # Create tile directory
        tile_dir = self.raw_data_dir / tile_id
        tile_dir.mkdir(exist_ok=True)
        
        success = True
        
        # Download elevation data
        if "elevation_1m_url" in tile_info:
            dest_file = tile_dir / f"{tile_id}_1m_dem.tif"
            if not dest_file.exists():
                success &= self.download_file(tile_info["elevation_1m_url"], dest_file)
        
        # Download LiDAR points
        if "lidar_points_url" in tile_info:
            dest_file = tile_dir / f"{tile_id}_lidar.las"
            if not dest_file.exists():
                success &= self.download_file(tile_info["lidar_points_url"], dest_file)
        
        return success
    
    def download_region(self, bounds: List[float], max_tiles: int = 10) -> Dict:
        """Download LiDAR data for a specific region"""
        west, south, east, north = bounds
        logger.info(f"Downloading LiDAR data for region: {bounds}")
        
        # Discover available tiles
        all_tiles = self.discover_vermont_tiles()
        
        # Filter tiles that intersect with requested bounds
        relevant_tiles = []
        for tile in all_tiles:
            tile_west, tile_south, tile_east, tile_north = tile["bounds"]
            
            # Check for overlap
            if not (tile_east < west or tile_west > east or 
                   tile_north < south or tile_south > north):
                relevant_tiles.append(tile)
        
        logger.info(f"Found {len(relevant_tiles)} relevant tiles")
        
        # Limit number of tiles to download
        if len(relevant_tiles) > max_tiles:
            logger.warning(f"Limiting download to {max_tiles} tiles")
            relevant_tiles = relevant_tiles[:max_tiles]
        
        # Download tiles
        results = {
            "requested_bounds": bounds,
            "tiles_found": len(relevant_tiles),
            "tiles_downloaded": 0,
            "failed_downloads": [],
            "success": True
        }
        
        for tile in relevant_tiles:
            if self.download_tile(tile):
                results["tiles_downloaded"] += 1
            else:
                results["failed_downloads"].append(tile["tile_id"])
                results["success"] = False
        
        # Update metadata
        metadata = self.load_metadata()
        metadata["downloads"][f"region_{west}_{south}_{east}_{north}"] = results
        self.save_metadata(metadata)
        
        return results
    
    def list_downloaded_data(self) -> Dict:
        """List all downloaded LiDAR data"""
        data_inventory = {
            "elevation_files": [],
            "lidar_files": [],
            "total_size_mb": 0
        }
        
        for tile_dir in self.raw_data_dir.iterdir():
            if tile_dir.is_dir():
                for file_path in tile_dir.iterdir():
                    if file_path.suffix.lower() in ['.tif', '.tiff']:
                        data_inventory["elevation_files"].append(str(file_path))
                    elif file_path.suffix.lower() in ['.las', '.laz']:
                        data_inventory["lidar_files"].append(str(file_path))
                    
                    # Calculate file size
                    data_inventory["total_size_mb"] += file_path.stat().st_size / (1024 * 1024)
        
        return data_inventory

def main():
    """Main function for testing"""
    downloader = VermontLidarDownloader()
    
    # Example: Download data for a small region around Montpelier, VT
    montpelier_bounds = [-72.65, 44.25, -72.55, 44.35]
    
    logger.info("Starting Vermont LiDAR data acquisition...")
    results = downloader.download_region(montpelier_bounds, max_tiles=3)
    
    logger.info(f"Download results: {results}")
    
    # List downloaded data
    inventory = downloader.list_downloaded_data()
    logger.info(f"Data inventory: {inventory}")

if __name__ == "__main__":
    main()
