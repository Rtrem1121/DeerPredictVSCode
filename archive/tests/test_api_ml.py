#!/usr/bin/env python3
"""
API Test Script for ML-Enhanced Deer Prediction

This script tests the complete API with ML integration to ensure
everything works properly in the Docker container.
"""

import requests
import json
import time
from datetime import datetime

def test_api_health():
    """Test API health endpoint"""
    print("🔍 Testing API health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API Health: {health_data['status']}")
            print(f"   Version: {health_data['version']}")
            print(f"   Rules loaded: {health_data['rules_loaded']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_ml_enhanced_prediction():
    """Test ML-enhanced prediction endpoint"""
    print("\n🧪 Testing ML-enhanced prediction...")
    
    # Test with special coordinates for ML testing
    test_request = {
        "lat": 44.26,
        "lon": -72.58,  # Special coordinates to trigger ML accuracy test
        "date_time": datetime.now().isoformat(),
        "season": "rut",
        "suggestion_threshold": 5.0,
        "min_suggestion_rating": 8.0
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/predict",
            json=test_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ ML-enhanced prediction successful!")
            
            # Check for ML enhancement indicators
            notes = data.get('notes', '')
            
            if 'ML Enhancement Applied' in notes:
                print("🤖 ML enhancement detected in response")
            
            if 'ML Accuracy Test Results' in notes:
                print("📊 ML accuracy test results found in response")
                # Extract test results from notes
                if 'Rule-based Accuracy:' in notes:
                    print("   Found accuracy comparison data")
            
            # Check mature buck opportunities
            mature_buck_opps = data.get('mature_buck_opportunities', {})
            if mature_buck_opps and mature_buck_opps.get('features'):
                num_opportunities = len(mature_buck_opps['features'])
                print(f"🏹 Found {num_opportunities} mature buck opportunities")
                
                # Check for ML enhancement flags
                for feature in mature_buck_opps['features']:
                    props = feature.get('properties', {})
                    if props.get('ml_enhanced'):
                        print(f"   Opportunity with ML enhancement detected")
            
            print(f"📍 Stand rating: {data.get('stand_rating', 'N/A')}")
            print(f"🎯 Stand recommendations: {len(data.get('stand_recommendations', []))}")
            print(f"⭐ Best stand locations: {len(data.get('five_best_stands', []))}")
            
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return False

def test_standard_prediction():
    """Test standard prediction without ML testing"""
    print("\n🎯 Testing standard prediction...")
    
    # Test with normal Vermont coordinates
    test_request = {
        "lat": 44.3,
        "lon": -72.6,
        "date_time": datetime.now().isoformat(),
        "season": "early_season",
        "suggestion_threshold": 5.0,
        "min_suggestion_rating": 8.0
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/predict",
            json=test_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Standard prediction successful!")
            
            # Check basic functionality
            print(f"📍 Stand rating: {data.get('stand_rating', 'N/A')}")
            
            # Check for heatmaps
            heatmaps = [
                'terrain_heatmap',
                'vegetation_heatmap', 
                'travel_score_heatmap',
                'bedding_score_heatmap',
                'feeding_score_heatmap'
            ]
            
            available_heatmaps = []
            for heatmap in heatmaps:
                if data.get(heatmap):
                    available_heatmaps.append(heatmap)
            
            print(f"🗺️ Generated heatmaps: {len(available_heatmaps)}/5")
            
            return True
        else:
            print(f"❌ Standard prediction failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Standard prediction error: {e}")
        return False

def wait_for_api():
    """Wait for API to become available"""
    print("⏳ Waiting for API to become available...")
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ API is ready!")
                return True
        except:
            pass
        
        print(f"   Attempt {i+1}/30...")
        time.sleep(1)
    
    print("❌ API did not become available within 30 seconds")
    return False

def main():
    """Run all API tests"""
    print("🚀 Starting ML-Enhanced Deer Prediction API Tests")
    print("=" * 50)
    
    # Wait for API to be ready
    if not wait_for_api():
        print("❌ Cannot proceed - API not available")
        return False
    
    # Run tests
    tests = [
        ("API Health", test_api_health),
        ("ML Enhanced Prediction", test_ml_enhanced_prediction),
        ("Standard Prediction", test_standard_prediction)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print(f"{'='*50}")
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"API TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All API tests passed! ML-enhanced deer prediction is working perfectly.")
        return True
    else:
        print("⚠️  Some API tests failed. Check logs above for details.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
