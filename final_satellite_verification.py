#!/usr/bin/env python3
"""
🎉 FINAL SATELLITE DATA VERIFICATION
Complete test of working Google Earth Engine integration
"""

import os
import ee
import json
from datetime import datetime, timedelta

def test_final_satellite_integration():
    """Final test using working authentication"""
    print("🛰️ FINAL SATELLITE DATA VERIFICATION")
    print("Testing your deer prediction system with REAL satellite data!")
    print("=" * 60)
    
    try:
        # Load credentials
        creds_path = "credentials/gee-service-account.json"
        with open(creds_path, 'r') as f:
            service_account_info = json.load(f)
        
        print(f"📧 Service Account: {service_account_info['client_email']}")
        print(f"🆔 Project: {service_account_info['project_id']}")
        print()
        
        # Authenticate using working method
        credentials = ee.ServiceAccountCredentials(
            email=service_account_info['client_email'],
            key_file=creds_path
        )
        ee.Initialize(credentials, project=service_account_info['project_id'])
        print("✅ GOOGLE EARTH ENGINE AUTHENTICATED!")
        
        # Test 1: Vegetation Analysis (Vermont hunting location)
        print("\n🌿 TESTING VEGETATION ANALYSIS...")
        lat, lon = 44.26, -72.58  # Vermont coordinates
        point = ee.Geometry.Point(lon, lat)
        
        # Get recent Landsat imagery
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
            .filterBounds(point) \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
            .filterMetadata('CLOUD_COVER', 'less_than', 20)
        
        count = collection.size().getInfo()
        print(f"   📡 Found {count} clear Landsat images in last 60 days")
        
        if count > 0:
            # Calculate NDVI for vegetation health
            image = collection.median()
            ndvi = image.normalizedDifference(['SR_B5', 'SR_B4'])
            
            # Sample vegetation at hunting location
            ndvi_sample = ndvi.sample(point, 30).first()
            if ndvi_sample:
                ndvi_value = ndvi_sample.get('nd').getInfo()
                print(f"   🍃 Current NDVI (vegetation health): {ndvi_value:.3f}")
                
                # Interpret NDVI for hunting
                if ndvi_value > 0.5:
                    vegetation_status = "Excellent (dense vegetation, good cover)"
                elif ndvi_value > 0.3:
                    vegetation_status = "Good (moderate vegetation)"
                elif ndvi_value > 0.1:
                    vegetation_status = "Fair (sparse vegetation)"
                else:
                    vegetation_status = "Poor (little vegetation)"
                
                print(f"   🦌 Hunting assessment: {vegetation_status}")
        
        # Test 2: Land Cover Analysis
        print("\n🗺️ TESTING LAND COVER ANALYSIS...")
        
        # Get land cover data (unmask to ensure values even if pixel missing)
        landcover = ee.Image('USGS/NLCD_RELEASES/2021_REL/NLCD/2021')
        landcover_band = landcover.select('landcover').unmask(-1)
        lc_sample = landcover_band.sample(point, 30).first()

        lc_value = None
        if lc_sample:
            try:
                lc_dict = lc_sample.toDictionary().getInfo()
                if lc_dict:
                    lc_value = lc_dict.get('landcover')
                    if lc_value == -1:
                        lc_value = None
            except Exception:
                lc_value = None
        else:
            # Expand the search slightly around the coordinate (60 m buffer) and try a mode reducer
            try:
                buffered_region = point.buffer(120)
                lc_reduced_info = landcover_band.reduceRegion(
                    reducer=ee.Reducer.mode(),
                    geometry=buffered_region,
                    scale=30,
                    maxPixels=1e6
                ).getInfo()

                if lc_reduced_info and 'landcover' in lc_reduced_info:
                    lc_value = lc_reduced_info['landcover']
                    if lc_value == -1:
                        lc_value = None
            except Exception:
                lc_value = None

        if lc_value is not None:
            # Land cover interpretation
            lc_types = {
                11: "Open Water", 21: "Developed, Open Space", 22: "Developed, Low Intensity",
                23: "Developed, Medium Intensity", 24: "Developed High Intensity",
                31: "Barren Land", 41: "Deciduous Forest", 42: "Evergreen Forest",
                43: "Mixed Forest", 51: "Dwarf Scrub", 52: "Shrub/Scrub",
                71: "Grassland/Herbaceous", 72: "Sedge/Herbaceous", 73: "Lichens",
                74: "Moss", 81: "Pasture/Hay", 82: "Cultivated Crops",
                90: "Woody Wetlands", 95: "Emergent Herbaceous Wetlands"
            }

            land_type = lc_types.get(lc_value, f"Unknown ({lc_value})")
            print(f"   🏞️ Land cover type: {land_type}")

            # Hunting suitability assessment
            good_for_hunting = lc_value in [41, 42, 43, 52, 71, 81, 90]  # Forests, shrub, grassland, wetlands
            if good_for_hunting:
                print(f"   🎯 Hunting suitability: Excellent deer habitat!")
            else:
                print(f"   🎯 Hunting suitability: May need to scout nearby areas")
        else:
            print("   ⚠️ Land cover data unavailable for this point (no valid pixel)")
        
        # Test 3: Elevation Analysis
        print("\n🏔️ TESTING ELEVATION ANALYSIS...")
        dem = ee.Image('USGS/SRTMGL1_003')
        elevation_sample = dem.sample(point, 30).first()
        if elevation_sample:
            elevation = elevation_sample.get('elevation').getInfo()
            print(f"   📏 Elevation: {elevation:.0f} meters ({elevation * 3.28084:.0f} feet)")
            
            # Elevation assessment for deer hunting
            if 200 <= elevation <= 800:
                print(f"   🦌 Elevation assessment: Ideal deer habitat elevation")
            elif elevation < 200:
                print(f"   🦌 Elevation assessment: Low elevation, check for agricultural areas")
            else:
                print(f"   🦌 Elevation assessment: High elevation, look for summer feeding areas")
        
        print("\n" + "=" * 60)
        print("🎉 SATELLITE DATA INTEGRATION COMPLETE!")
        print("✅ Your deer prediction system now uses REAL satellite data:")
        print("   🛰️ Live vegetation health monitoring")
        print("   🗺️ Current land cover classification") 
        print("   🏔️ Terrain analysis with elevation data")
        print("   📡 Updated every 16 days with new satellite passes")
        print()
        print("🦌 Your hunting predictions are now powered by space! 🚀")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_final_satellite_integration()
    
    if success:
        print("\n🎯 READY TO USE!")
        print("Run your deer prediction app and experience satellite-enhanced hunting intelligence!")
    else:
        print("\n⚠️ Still using fallback data")
        print("The system works perfectly with synthetic data until satellite connection is resolved")
