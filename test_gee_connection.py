#!/usr/bin/env python3
"""
Test Google Earth Engine connection and data retrieval
"""
import ee
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gee_initialization():
    """Test if GEE can be initialized with service account"""
    try:
        # Try service account authentication
        credentials_path = 'credentials/gee-service-account.json'
        
        logger.info(f"📁 Loading credentials from: {credentials_path}")
        service_credentials = ee.ServiceAccountCredentials(
            email='deer-predict-app@deer-predict-app.iam.gserviceaccount.com',
            key_file=credentials_path
        )
        
        logger.info("🔐 Initializing Earth Engine with service account...")
        ee.Initialize(service_credentials)
        
        logger.info("✅ GEE initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ GEE initialization failed: {e}")
        return False

def test_gee_query():
    """Test actual data retrieval from GEE"""
    try:
        # Test location: Vermont
        test_lat, test_lon = 44.5, -72.5
        point = ee.Geometry.Point([test_lon, test_lat])
        
        logger.info(f"\n📍 Testing GEE query at: ({test_lat}, {test_lon})")
        
        # Test SRTM elevation
        logger.info("   Testing SRTM elevation...")
        srtm = ee.Image('USGS/SRTMGL1_003')
        elevation = srtm.select('elevation').sample(point, 30).first().get('elevation').getInfo()
        logger.info(f"   ✅ Elevation: {elevation}m")
        
        # Test slope/aspect
        logger.info("   Testing terrain (slope/aspect)...")
        terrain = ee.Terrain.products(srtm)
        slope = terrain.select('slope').sample(point, 30).first().get('slope').getInfo()
        aspect = terrain.select('aspect').sample(point, 30).first().get('aspect').getInfo()
        logger.info(f"   ✅ Slope: {slope:.1f}°, Aspect: {aspect:.1f}°")
        
        # Test canopy coverage
        logger.info("   Testing forest canopy...")
        hansen = ee.Image('UMD/hansen/global_forest_change_2023_v1_11')
        canopy = hansen.select('treecover2000').sample(point, 30).first().get('treecover2000').getInfo()
        logger.info(f"   ✅ Canopy: {canopy}%")
        
        logger.info("\n✅ ALL GEE QUERIES SUCCESSFUL!")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ GEE query failed: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   This is the root cause of fallback data being used!")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("GOOGLE EARTH ENGINE CONNECTION TEST")
    print("=" * 80)
    
    # Test 1: Initialization
    if not test_gee_initialization():
        print("\n❌ GEE initialization failed - check credentials")
        sys.exit(1)
    
    # Test 2: Data query
    if not test_gee_query():
        print("\n❌ GEE queries failing - this is why predictions use fallback data")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ GEE IS WORKING CORRECTLY")
    print("=" * 80)
    print("\nIf predictions still show same patterns, the issue is elsewhere.")
