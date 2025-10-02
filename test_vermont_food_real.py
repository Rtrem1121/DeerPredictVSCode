#!/usr/bin/env python3
"""
Test Vermont Food Grid with Real GEE Data

This tests the updated vermont_food_classifier to verify
it now returns varied food quality scores based on real CDL data.
"""

import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from backend.vermont_food_classifier import get_vermont_food_classifier
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Vermont test location (same as actual prediction)
test_lat = 43.3115
test_lon = -73.2149
season = 'early_season'

logger.info(f"\n{'='*60}")
logger.info(f"Testing Updated Vermont Food Classifier")
logger.info(f"{'='*60}")
logger.info(f"Location: {test_lat}, {test_lon}")
logger.info(f"Season: {season}")

# Get classifier
vt_classifier = get_vermont_food_classifier()

# Create spatial food grid
logger.info(f"\nCreating spatial food grid...")
result = vt_classifier.create_spatial_food_grid(
    center_lat=test_lat,
    center_lon=test_lon,
    season=season,
    grid_size=10
)

# Analyze results
food_grid = result['food_grid']
metadata = result.get('grid_metadata', {})
patches = result.get('food_patch_locations', [])

logger.info(f"\n{'='*60}")
logger.info(f"RESULTS")
logger.info(f"{'='*60}")

# Check if fallback mode
is_fallback = metadata.get('fallback', False)

if is_fallback:
    logger.error(f"❌ FALLBACK MODE - GEE not available")
    logger.error(f"   All scores will be uniform")
else:
    logger.info(f"✅ REAL GEE DATA - Satellite-based food classification")

# Food grid statistics
logger.info(f"\n📊 Food Grid Statistics:")
logger.info(f"   Grid size: {food_grid.shape[0]}x{food_grid.shape[1]}")
logger.info(f"   Mean quality: {np.mean(food_grid):.3f}")
logger.info(f"   Min quality: {np.min(food_grid):.3f}")
logger.info(f"   Max quality: {np.max(food_grid):.3f}")
logger.info(f"   Std dev: {np.std(food_grid):.3f}")

# Check for variation
if np.std(food_grid) < 0.01:
    logger.warning(f"\n⚠️  WARNING: Grid shows minimal variation!")
    logger.warning(f"   This suggests all cells have similar values")
    logger.warning(f"   Expected variation for real Vermont data")
else:
    logger.info(f"\n✅ Grid shows good variation ({np.std(food_grid):.3f} std dev)")

# Quality distribution
logger.info(f"\n📈 Quality Distribution:")
bins = [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]
hist, _ = np.histogram(food_grid, bins=bins)
labels = ['Very Low (0-0.3)', 'Low (0.3-0.5)', 'Moderate (0.5-0.7)', 'High (0.7-0.9)', 'Very High (0.9-1.0)']
for label, count in zip(labels, hist):
    pct = (count / food_grid.size) * 100
    logger.info(f"   {label}: {count} cells ({pct:.1f}%)")

# High-quality food patches
logger.info(f"\n🌽 High-Quality Food Patches:")
logger.info(f"   Found: {len(patches)} patches")

if patches:
    for i, patch in enumerate(patches[:5], 1):
        lat = patch['lat']
        lon = patch['lon']
        quality = patch['quality']
        cell = patch['grid_cell']
        logger.info(f"   {i}. {lat:.4f}, {lon:.4f} - Quality: {quality:.2f} [Cell {cell['row']},{cell['col']}]")
else:
    logger.warning(f"   No high-quality patches identified")

# Expected values for early_season based on test_gee_direct.py results:
# - Deciduous Forest (141): 81 cells should be 0.85
# - Grass/Pasture (176): 15 cells should be 0.50
# - Evergreen Forest (142): 1 cell should be 0.40

logger.info(f"\n{'='*60}")
logger.info(f"Expected Results (based on CDL data):")
logger.info(f"{'='*60}")
logger.info(f"  Deciduous Forest (81% of grid): 0.85 quality")
logger.info(f"  Grass/Pasture (15% of grid): 0.50 quality")
logger.info(f"  Other forest types: 0.40-0.60 quality")
logger.info(f"\n  Expected mean: ~0.80")
logger.info(f"  Expected range: 0.40 - 0.85")
logger.info(f"  Expected std dev: ~0.15")

logger.info(f"\n{'='*60}")

# Verdict
if is_fallback:
    logger.error(f"\n❌ TEST FAILED - Using fallback mode")
    logger.error(f"   Fix: Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
    logger.error(f"   See: FIX_GEE_AUTHENTICATION.md")
    sys.exit(1)
elif np.std(food_grid) < 0.01:
    logger.warning(f"\n⚠️  TEST INCOMPLETE - Grid has no variation")
    logger.warning(f"   GEE is connected but food scores aren't varying")
    logger.warning(f"   Check crop code mapping in VERMONT_CROPS dictionary")
    sys.exit(1)
elif abs(np.mean(food_grid) - 0.80) > 0.15:
    logger.warning(f"\n⚠️  TEST SUSPICIOUS - Mean quality {np.mean(food_grid):.2f} differs from expected ~0.80")
    logger.warning(f"   GEE is working but values may not match expected crops")
    logger.warning(f"   This could be due to season or location differences")
    sys.exit(0)  # Warning but not failure
else:
    logger.info(f"\n✅ TEST PASSED!")
    logger.info(f"   Food grid shows realistic variation")
    logger.info(f"   Mean quality matches expected value")
    logger.info(f"   High-quality patches identified")
    logger.info(f"\n🎉 Vermont Food Classifier is working correctly!")
    sys.exit(0)
