#!/usr/bin/env python3
"""
Direct GEE Test - Test Vermont food grid sampling

This tests the actual CDL sampling at grid points to verify
why we're getting uniform 0.55 values.
"""

import ee
import os
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize GEE
creds_path = 'credentials/gee-service-account.json'
if os.path.exists(creds_path):
    logger.info(f"Using credentials: {creds_path}")
    credentials = ee.ServiceAccountCredentials(None, creds_path)
    ee.Initialize(credentials)
else:
    logger.info("Using default authentication")
    ee.Initialize()

# Vermont test location
center_lat = 43.3115
center_lon = -73.2149
grid_size = 10
span_deg = 0.04

logger.info(f"\n{'='*60}")
logger.info(f"Testing Vermont Food Grid Sampling")
logger.info(f"{'='*60}")
logger.info(f"Location: {center_lat}, {center_lon}")
logger.info(f"Grid: {grid_size}x{grid_size}, span={span_deg}°")

# Create grid coordinates
lats = np.linspace(center_lat + span_deg/2, center_lat - span_deg/2, grid_size)
lons = np.linspace(center_lon - span_deg/2, center_lon + span_deg/2, grid_size)

logger.info(f"\nLat range: {lats.min():.4f} to {lats.max():.4f}")
logger.info(f"Lon range: {lons.min():.4f} to {lons.max():.4f}")

# Get CDL data
logger.info(f"\nLoading USDA CDL for 2024...")
try:
    cdl = ee.ImageCollection('USDA/NASS/CDL') \
        .filter(ee.Filter.date('2024-01-01', '2024-12-31')) \
        .first() \
        .select('cropland')
    logger.info("✅ CDL loaded successfully")
except Exception as e:
    logger.error(f"❌ CDL load failed: {e}")
    exit(1)

# Sample a few grid cells
test_cells = [(0, 0), (0, grid_size-1), (grid_size-1, 0), (grid_size-1, grid_size-1), (grid_size//2, grid_size//2)]

logger.info(f"\n{'='*60}")
logger.info(f"Sampling {len(test_cells)} test grid cells:")
logger.info(f"{'='*60}")

for i, j in test_cells:
    cell_lat = lats[i]
    cell_lon = lons[j]
    
    logger.info(f"\nCell [{i},{j}]: {cell_lat:.4f}, {cell_lon:.4f}")
    
    try:
        # Create point
        point = ee.Geometry.Point([cell_lon, cell_lat])
        
        # Sample CDL at this point
        sample = cdl.reduceRegion(
            reducer=ee.Reducer.mode(),
            geometry=point.buffer(100),
            scale=30,
            maxPixels=1e6
        ).getInfo()
        
        crop_code = sample.get('cropland')
        
        if crop_code is not None:
            logger.info(f"  ✅ Crop code: {crop_code}")
            
            # Look up crop type
            VERMONT_CROPS = {
                1: 'Corn',
                36: 'Alfalfa',
                37: 'Other Hay',
                141: 'Deciduous Forest',
                142: 'Evergreen Forest',
                152: 'Shrubland',
                176: 'Grass/Pasture'
            }
            
            crop_name = VERMONT_CROPS.get(crop_code, f'Unknown ({crop_code})')
            logger.info(f"  🌾 Crop type: {crop_name}")
        else:
            logger.warning(f"  ⚠️  No crop data returned")
            logger.warning(f"  Sample result: {sample}")
            
    except Exception as e:
        logger.error(f"  ❌ Sampling failed: {e}")

# Try sampling entire grid at once (more efficient)
logger.info(f"\n{'='*60}")
logger.info(f"Testing Efficient Batch Sampling:")
logger.info(f"{'='*60}")

try:
    # Create feature collection of all grid points
    points = []
    for i in range(grid_size):
        for j in range(grid_size):
            cell_lat = lats[i]
            cell_lon = lons[j]
            point = ee.Geometry.Point([cell_lon, cell_lat])
            feature = ee.Feature(point, {'row': i, 'col': j})
            points.append(feature)
    
    grid_points = ee.FeatureCollection(points)
    logger.info(f"✅ Created {grid_size * grid_size} grid points")
    
    # Sample CDL at all points
    sampled = cdl.reduceRegions(
        collection=grid_points,
        reducer=ee.Reducer.mode(),
        scale=30
    ).getInfo()
    
    logger.info(f"✅ Batch sampling complete")
    logger.info(f"\nFirst 5 results:")
    
    for idx, feature in enumerate(sampled['features'][:5]):
        props = feature['properties']
        row = props.get('row')
        col = props.get('col')
        crop_code = props.get('mode')
        logger.info(f"  Cell [{row},{col}]: Crop code {crop_code}")
    
    # Count unique crop codes
    crop_codes = [f['properties'].get('mode') for f in sampled['features'] if f['properties'].get('mode') is not None]
    unique_crops = set(crop_codes)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Summary:")
    logger.info(f"  Total cells sampled: {len(crop_codes)}")
    logger.info(f"  Unique crop codes: {len(unique_crops)}")
    logger.info(f"  Crop distribution: {dict(zip(*np.unique(crop_codes, return_counts=True)))}")
    logger.info(f"{'='*60}")
    
except Exception as e:
    logger.error(f"❌ Batch sampling failed: {e}")
    import traceback
    traceback.print_exc()

logger.info(f"\n✅ Test complete!")
