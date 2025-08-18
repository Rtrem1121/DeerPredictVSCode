#!/usr/bin/env python3
"""
🚀 GEE Activation Checker
Quick script to verify Google Earth Engine authorization status
"""

import os
import json
from pathlib import Path

def check_credentials():
    """Check if GEE credentials are properly configured"""
    print("🔍 Checking Google Earth Engine Authorization Status...")
    print("=" * 60)
    
    # Check credentials file
    creds_path = Path("credentials/gee-service-account.json")
    
    if not creds_path.exists():
        print("❌ CREDENTIALS FILE MISSING")
        print(f"   Expected: {creds_path.absolute()}")
        print()
        print("📋 TO ACTIVATE SATELLITE DATA:")
        print("   1. Follow steps in GEE_AUTHORIZATION_GUIDE.md")
        print("   2. Download service account JSON from Google Cloud")
        print("   3. Save as: credentials/gee-service-account.json")
        print("   4. Run this script again")
        print()
        return False
    
    # Validate credentials file
    try:
        with open(creds_path, 'r') as f:
            creds = json.load(f)
        
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri'
        ]
        
        missing_fields = [field for field in required_fields if field not in creds]
        
        if missing_fields:
            print("❌ INVALID CREDENTIALS FILE")
            print(f"   Missing fields: {', '.join(missing_fields)}")
            return False
        
        print("✅ CREDENTIALS FILE FOUND AND VALID")
        print(f"   Project ID: {creds.get('project_id', 'Unknown')}")
        print(f"   Service Account: {creds.get('client_email', 'Unknown')}")
        print()
        
        # Check if GEE can be imported
        try:
            import ee
            print("✅ Google Earth Engine library available")
        except ImportError:
            print("❌ Google Earth Engine library not installed")
            print("   Run: pip install earthengine-api")
            return False
        
        # Test authentication
        try:
            ee.Initialize(ee.ServiceAccountCredentials(
                creds['client_email'], 
                str(creds_path.absolute())
            ))
            print("✅ GEE AUTHENTICATION SUCCESSFUL!")
            print()
            print("🎉 SATELLITE DATA ACTIVATION COMPLETE!")
            print("   Your deer predictions now use real satellite imagery!")
            print()
            print("🧪 Test with: python test_gee_integration.py")
            return True
            
        except Exception as e:
            print("❌ GEE AUTHENTICATION FAILED")
            print(f"   Error: {str(e)}")
            print()
            print("🔧 TROUBLESHOOTING:")
            print("   1. Verify service account has Earth Engine permissions")
            print("   2. Check Earth Engine API is enabled")
            print("   3. Ensure service account is registered with GEE")
            print("   4. Visit: https://code.earthengine.google.com/")
            return False
            
    except json.JSONDecodeError:
        print("❌ CREDENTIALS FILE CORRUPTED")
        print("   File exists but contains invalid JSON")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        return False

def main():
    """Main activation checker"""
    print("🛰️ Google Earth Engine Activation Checker")
    print(f"📅 {os.getcwd()}")
    print()
    
    if check_credentials():
        print("🚀 READY FOR ENHANCED PREDICTIONS!")
        print("   Real satellite data is now active!")
    else:
        print("⏳ AUTHORIZATION NEEDED")
        print("   Follow GEE_AUTHORIZATION_GUIDE.md for setup")

if __name__ == "__main__":
    main()
