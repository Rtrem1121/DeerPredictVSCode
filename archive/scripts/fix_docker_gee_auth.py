#!/usr/bin/env python3
"""
Docker GEE Authentication Fix

This script fixes Google Earth Engine authentication specifically for Docker containers.
It ensures service account authentication works properly in containerized environments.
"""
import os
import json
import logging
from pathlib import Path

def fix_docker_gee_auth():
    """Fix GEE authentication for Docker environment"""
    print("🔧 Fixing GEE Authentication for Docker")
    print("=" * 50)
    
    # Check if service account file exists
    service_account_path = "/app/config/deer-pred-service-account.json"
    
    if not os.path.exists(service_account_path):
        print(f"❌ Service account file not found: {service_account_path}")
        print("📋 Available files in /app/config:")
        if os.path.exists("/app/config"):
            for f in os.listdir("/app/config"):
                print(f"   - {f}")
        return False
    
    try:
        # Test service account file
        with open(service_account_path, 'r') as f:
            credentials = json.load(f)
        
        print(f"✅ Service account file found: {credentials.get('client_email', 'unknown')}")
        
        # Set environment variables for GEE
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path
        os.environ['EE_ACCOUNT'] = credentials.get('client_email', '')
        
        # Test GEE initialization
        import ee
        
        try:
            # Initialize with service account
            ee.Initialize(ee.ServiceAccountCredentials(
                credentials.get('client_email'),
                service_account_path
            ))
            
            # Test a simple GEE operation
            image = ee.Image('LANDSAT/LC08/C02/T1_L2/LC08_044034_20200101')
            geometry = ee.Geometry.Point([-74.0060, 40.7128])
            
            # This should work if authentication is successful
            test_info = image.get('CLOUD_COVER').getInfo()
            
            print(f"✅ GEE Authentication successful!")
            print(f"🛰️ Test image cloud cover: {test_info}%")
            return True
            
        except Exception as e:
            print(f"❌ GEE Authentication failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error reading service account file: {e}")
        return False

if __name__ == "__main__":
    success = fix_docker_gee_auth()
    exit(0 if success else 1)
