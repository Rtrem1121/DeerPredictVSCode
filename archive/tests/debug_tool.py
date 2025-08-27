#!/usr/bin/env python3
"""
Consolidated Debug Tool for Deer Prediction App
Replaces multiple individual debug scripts with a unified interface
"""

import requests
import json
import sys
from datetime import datetime

class DeerPredictionDebugger:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_api_health(self):
        """Test basic API health"""
        print("🔍 Testing API Health...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("   ✅ API is responding")
                return True
            else:
                print(f"   ❌ API returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ API connection failed: {e}")
            return False
    
    def test_prediction_endpoint(self, lat=44.26, lon=-72.58):
        """Test main prediction endpoint"""
        print(f"🎯 Testing prediction for ({lat}, {lon})...")
        try:
            response = self.session.get(f"{self.base_url}/predict/{lat}/{lon}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Prediction successful")
                print(f"   📊 Confidence: {data.get('confidence', 'N/A')}%")
                print(f"   🎯 Score: {data.get('score', 'N/A')}")
                return data
            else:
                print(f"   ❌ Prediction failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return None
        except Exception as e:
            print(f"   ❌ Prediction request failed: {e}")
            return None
    
    def test_camera_placement(self, lat=44.26, lon=-72.58):
        """Test camera placement optimization"""
        print(f"📷 Testing camera placement for ({lat}, {lon})...")
        try:
            response = self.session.get(f"{self.base_url}/camera-placement/{lat}/{lon}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Camera placement successful")
                print(f"   📍 Position: {data.get('camera_lat', 'N/A')}, {data.get('camera_lon', 'N/A')}")
                print(f"   📊 Confidence: {data.get('confidence', 'N/A')}%")
                return data
            else:
                print(f"   ❌ Camera placement failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Camera placement request failed: {e}")
            return None
    
    def test_mature_buck_analysis(self, lat=44.26, lon=-72.58):
        """Test mature buck specific analysis"""
        print(f"🦌 Testing mature buck analysis for ({lat}, {lon})...")
        try:
            response = self.session.get(f"{self.base_url}/mature-buck/{lat}/{lon}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Mature buck analysis successful")
                print(f"   📊 Buck Score: {data.get('buck_score', 'N/A')}")
                print(f"   🎯 Confidence: {data.get('confidence', 'N/A')}%")
                return data
            else:
                print(f"   ❌ Mature buck analysis failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Mature buck request failed: {e}")
            return None
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🔍 COMPREHENSIVE DEBUG TEST")
        print("=" * 40)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {
            "api_health": self.test_api_health(),
            "prediction": None,
            "camera_placement": None,
            "mature_buck": None
        }
        
        if results["api_health"]:
            print()
            results["prediction"] = self.test_prediction_endpoint()
            print()
            results["camera_placement"] = self.test_camera_placement()
            print()
            results["mature_buck"] = self.test_mature_buck_analysis()
        
        print()
        print("📊 SUMMARY")
        print("-" * 20)
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        return results

def main():
    """Main debug interface"""
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
    else:
        action = "comprehensive"
    
    debugger = DeerPredictionDebugger()
    
    if action == "health":
        debugger.test_api_health()
    elif action == "prediction":
        lat = float(sys.argv[2]) if len(sys.argv) > 2 else 44.26
        lon = float(sys.argv[3]) if len(sys.argv) > 3 else -72.58
        debugger.test_prediction_endpoint(lat, lon)
    elif action == "camera":
        lat = float(sys.argv[2]) if len(sys.argv) > 2 else 44.26
        lon = float(sys.argv[3]) if len(sys.argv) > 3 else -72.58
        debugger.test_camera_placement(lat, lon)
    elif action == "buck":
        lat = float(sys.argv[2]) if len(sys.argv) > 2 else 44.26
        lon = float(sys.argv[3]) if len(sys.argv) > 3 else -72.58
        debugger.test_mature_buck_analysis(lat, lon)
    else:
        debugger.run_comprehensive_test()

if __name__ == "__main__":
    main()
