
import sys
import os
import time

# Add project root and backend to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

try:
    import ee
    from backend.gee_docker_setup import GEESetup
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure 'earthengine-api' is installed and 'gee_docker_setup.py' is in the path.")
    sys.exit(1)

def check_gee_status():
    print("🔍 Checking Google Earth Engine Status...")
    
    # 1. Initialize
    setup = GEESetup()
    if not setup.initialize():
        print("❌ GEE Initialization Failed.")
        return

    print("✅ GEE Initialized successfully.")

    # 2. Test Simple Operation
    print("🔄 Attempting simple API call (Get SRTM Info)...")
    try:
        start_time = time.time()
        # Simple metadata request - low cost
        srtm = ee.Image('USGS/SRTMGL1_003')
        info = srtm.get('system:id').getInfo()
        elapsed = time.time() - start_time
        
        print(f"✅ API Call Successful! (Time: {elapsed:.2f}s)")
        print(f"   Result: {info}")
        print("   Status: OPERATIONAL")
        
    except ee.EEException as e:
        error_msg = str(e)
        print(f"\n❌ API Call Failed!")
        print(f"   Error: {error_msg}")
        
        if "Quota exceeded" in error_msg or "429" in error_msg:
            print("\n⚠️  DIAGNOSIS: RATE LIMIT EXCEEDED")
            print("   You have hit the Google Earth Engine request quota.")
            print("   Recommendation: Wait 24 hours or check your Google Cloud Console quotas.")
        elif "authorization" in error_msg.lower():
            print("\n⚠️  DIAGNOSIS: AUTHENTICATION ISSUE")
            print("   Your credentials may be invalid or expired.")
            print("   Recommendation: Re-authenticate using 'earthengine authenticate'.")
        else:
            print("\n⚠️  DIAGNOSIS: UNKNOWN ERROR")
            print("   This might be a network issue or a specific service outage.")

if __name__ == "__main__":
    check_gee_status()
