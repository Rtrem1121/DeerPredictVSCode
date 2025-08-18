#!/usr/bin/env python3
"""
Post-Deployment Verification Script
Verifies the v2.0 Satellite Hunter release is fully operational
"""
import requests
import json
import sys
from datetime import datetime

def verify_deployment():
    print("🚀 Verifying Deer Prediction App v2.0 Deployment")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n🔍 Testing Health Endpoints...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend Health: {health_data.get('status', 'unknown')}")
            print(f"   Version: {health_data.get('version', 'unknown')}")
            print(f"   Rules Loaded: {health_data.get('rules_loaded', 'unknown')}")
        else:
            print(f"❌ Backend health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False
    
    # Test 2: Satellite Integration
    print("\n🛰️ Testing Satellite Integration...")
    try:
        response = requests.get(
            "http://localhost:8000/api/enhanced/satellite/ndvi",
            params={"lat": 44.26, "lon": -72.58},
            timeout=30
        )
        if response.status_code == 200:
            ndvi_data = response.json()
            vegetation_health = ndvi_data.get("vegetation_data", {}).get("vegetation_health", {})
            ndvi_value = vegetation_health.get("ndvi")
            data_source = ndvi_data.get("vegetation_data", {}).get("analysis_quality", {}).get("data_source")
            
            if data_source == "google_earth_engine" and ndvi_value is not None:
                print(f"✅ Satellite Data: NDVI = {ndvi_value}")
                print(f"   Data Source: {data_source}")
                print(f"   EVI: {vegetation_health.get('evi', 'N/A')}")
                print(f"   SAVI: {vegetation_health.get('savi', 'N/A')}")
            else:
                print(f"❌ Satellite integration failed: NDVI={ndvi_value}, source={data_source}")
                return False
        else:
            print(f"❌ Satellite request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Satellite connection failed: {e}")
        return False
    
    # Test 3: Prediction Engine
    print("\n🦌 Testing Prediction Engine...")
    try:
        response = requests.post(
            "http://localhost:8000/predict",
            json={
                "lat": 44.26,
                "lon": -72.58,
                "date_time": "2025-11-15T06:00:00",
                "season": "rut"
            },
            timeout=30
        )
        if response.status_code == 200:
            prediction = response.json()
            stands = prediction.get("five_best_stands", [])
            mature_buck = prediction.get("mature_buck_analysis", {})
            
            if stands and len(stands) > 0 and mature_buck:
                print(f"✅ Predictions: {len(stands)} stands generated")
                print(f"   Mature Buck Analysis: {mature_buck.get('viable_location', 'unknown')}")
                print(f"   Top Stand Confidence: {stands[0].get('confidence', 'unknown')}%")
            else:
                print(f"❌ Prediction generation failed")
                return False
        else:
            print(f"❌ Prediction request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Prediction connection failed: {e}")
        return False
    
    # Test 4: Frontend Accessibility
    print("\n🖥️ Testing Frontend Access...")
    try:
        response = requests.get("http://localhost:8501/health", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend: Accessible")
        else:
            print(f"⚠️ Frontend health: {response.status_code} (may be normal)")
    except Exception as e:
        print(f"⚠️ Frontend connection: {e} (may be normal if Streamlit)")
    
    print("\n" + "=" * 60)
    print("🎉 VERIFICATION COMPLETE")
    print("✅ Deer Prediction App v2.0 'Satellite Hunter' is OPERATIONAL!")
    print("🦌 Ready for hunting season 2025!")
    print("🛰️ Satellite integration confirmed working")
    print("📍 Access: http://localhost:8501 (Frontend) | http://localhost:8000 (API)")
    return True

if __name__ == "__main__":
    success = verify_deployment()
    sys.exit(0 if success else 1)
