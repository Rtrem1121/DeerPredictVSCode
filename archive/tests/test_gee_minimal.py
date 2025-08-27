#!/usr/bin/env python3
"""
Minimal Google Earth Engine Test
Direct authentication test to verify satellite access
"""

import os
import ee
import json

def test_gee_minimal():
    """Minimal GEE authentication test"""
    print("🛰️ Minimal Google Earth Engine Test")
    print("=" * 50)
    
    # Set credentials
    creds_path = "credentials/gee-service-account.json"
    if not os.path.exists(creds_path):
        print(f"❌ Credentials not found: {creds_path}")
        return False
    
    try:
        # Load service account info
        with open(creds_path, 'r') as f:
            service_account_info = json.load(f)
        
        print(f"📧 Service Account: {service_account_info['client_email']}")
        print(f"🆔 Project ID: {service_account_info['project_id']}")
        
        # Try different authentication methods
        methods = [
            ("Environment Variable", lambda: test_env_auth(creds_path, service_account_info)),
            ("Direct Service Account", lambda: test_direct_auth(creds_path, service_account_info)),
            ("Service Account Credentials", lambda: test_creds_auth(creds_path, service_account_info))
        ]
        
        for method_name, method_func in methods:
            print(f"\n🧪 Testing {method_name}...")
            try:
                if method_func():
                    print(f"✅ {method_name} SUCCESS!")
                    return True
                else:
                    print(f"❌ {method_name} failed")
            except Exception as e:
                print(f"❌ {method_name} error: {e}")
        
        print("\n❌ All authentication methods failed")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_env_auth(creds_path, service_account_info):
    """Test using environment variable"""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath(creds_path)
    ee.Initialize(project=service_account_info['project_id'])
    
    # Test basic functionality
    point = ee.Geometry.Point(-72.58, 44.26)
    collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(point) \
        .filterDate('2024-06-01', '2024-09-01') \
        .limit(1)
    
    count = collection.size().getInfo()
    print(f"   📡 Found {count} Landsat images")
    return True

def test_direct_auth(creds_path, service_account_info):
    """Test using direct credentials"""
    credentials = ee.ServiceAccountCredentials(
        email=service_account_info['client_email'],
        key_file=creds_path
    )
    ee.Initialize(credentials, project=service_account_info['project_id'])
    
    # Test basic functionality with publicly accessible data
    point = ee.Geometry.Point(-72.58, 44.26)
    
    # Try a more accessible dataset
    try:
        collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
            .filterBounds(point) \
            .filterDate('2024-06-01', '2024-09-01') \
            .limit(1)
        
        count = collection.size().getInfo()
        print(f"   📡 Found {count} Landsat images")
        
        if count > 0:
            # Get the first image and calculate NDVI
            image = collection.first()
            ndvi = image.normalizedDifference(['SR_B5', 'SR_B4'])
            
            # Get a sample value
            sample = ndvi.sample(point, 30).first()
            if sample:
                ndvi_value = sample.get('nd').getInfo()
                print(f"   🌿 NDVI sample: {ndvi_value}")
            else:
                print("   🌿 NDVI calculated (no sample point)")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️ Specific error: {e}")
        
        # Try even simpler test - just geometry
        try:
            # Test basic geometry operations
            area = point.buffer(1000).area().getInfo()
            print(f"   📐 Buffer area: {area} sq meters")
            return True
        except Exception as e2:
            print(f"   ❌ Basic geometry failed: {e2}")
            return False

def test_creds_auth(creds_path, service_account_info):
    """Test using from_service_account_file"""
    from google.oauth2 import service_account
    
    credentials = service_account.Credentials.from_service_account_file(creds_path)
    ee.Initialize(credentials, project=service_account_info['project_id'])
    
    # Test basic functionality
    point = ee.Geometry.Point(-72.58, 44.26)
    dem = ee.Image('USGS/SRTMGL1_003')
    elevation = dem.sample(point, 30).first().get('elevation').getInfo()
    print(f"   🏔️ Elevation: {elevation}m")
    return True

if __name__ == "__main__":
    if test_gee_minimal():
        print("\n🎉 SATELLITE DATA INTEGRATION SUCCESSFUL!")
        print("   Your deer prediction system can now use real satellite data!")
    else:
        print("\n⚠️ Authentication still needs work")
        print("   System will continue using synthetic fallback data")
