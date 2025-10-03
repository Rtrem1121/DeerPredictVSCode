# Vermont LiDAR Data Directory

## Purpose
This directory stores pre-downloaded Vermont LiDAR hillshade TIF files for fast local access during deer prediction analysis.

## File Naming Convention
Use descriptive names that include coverage area:
- `vermont_south_hillshade.tif` - Southern Vermont hillshade
- `vermont_north_hillshade.tif` - Northern Vermont hillshade
- `vermont_central_hillshade.tif` - Central Vermont hillshade

## Recommended File
**Primary File**: `vermont_south_hillshade.tif`
- Coverage: Southern half of Vermont (primary hunting area)
- Source: USGS 3DEP or Vermont LiDAR dataset
- Resolution: 1-2m (recommended)
- Format: GeoTIFF (.tif)
- Coordinate System: WGS84 (EPSG:4326) or NAD83/Vermont (EPSG:32145)

## Usage
The app will automatically detect and use TIF files in this directory for:
- High-resolution terrain analysis (1m vs 30m SRTM)
- Micro-topography detection (benches, saddles, draws)
- Precise slope/aspect calculations
- Movement corridor detection
- Enhanced bedding zone prediction

## File Size Expectations
- Southern Vermont: ~500MB - 2GB (depending on resolution)
- Full state: ~2-5GB
- Compressed formats (.tif with LZW compression) recommended

## Data Sources
1. **USGS 3DEP**: https://apps.nationalmap.gov/downloader/
2. **Vermont Center for Geographic Information**: https://vcgi.vermont.gov/
3. **OpenTopography**: https://opentopography.org/

## Notes
- Files are gitignored (won't be committed to repository)
- Docker volume mount: `/app/data/lidar` maps to this directory
- App will fall back to SRTM 30m if LiDAR not available

---
**Last Updated**: October 2, 2025
**Hunting Area**: Southern Vermont (43.0°N - 43.5°N, -73.5°W - -72.5°W)
