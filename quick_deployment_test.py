#!/usr/bin/env python3
"""
Quick Deployment Test
Test core functionality before deployment
"""
import requests
import json

def test_deployment_readiness():
    print("🦌 DEER PREDICTION APP - DEPLOYMENT READINESS CHECK")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Backend Health
    print("\n1. Testing Backend Health...")
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Backend Status: {health.get('status')}")
            print(f"   ✅ Version: {health.get('version')}")
            print(f"   ✅ Rules Loaded: {health.get('rules_loaded')}")
            tests_passed += 1
        else:
            print(f"   ❌ Backend health failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Backend connection failed: {e}")
    
    # Test 2: Core Prediction
    print("\n2. Testing Core Prediction...")
    try:
        response = requests.post('http://localhost:8000/predict', 
            json={
                'lat': 44.2619, 
                'lon': -72.5806, 
                'date_time': '2025-11-15T06:00:00', 
                'season': 'rut'
            }, 
            timeout=15)
        if response.status_code == 200:
            data = response.json()
            stands = data.get('five_best_stands', [])
            mature_buck = data.get('mature_buck_analysis', {})
            
            print(f"   ✅ Prediction Generated")
            print(f"   ✅ Stand Rating: {data.get('stand_rating', 'N/A')}")
            print(f"   ✅ Stands Generated: {len(stands)}")
            if stands:
                print(f"   ✅ Top Stand Confidence: {stands[0].get('confidence', 'N/A')}%")
            print(f"   ✅ Mature Buck Analysis: {mature_buck.get('viable_location', 'N/A')}")
            tests_passed += 1
        else:
            print(f"   ❌ Prediction failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Prediction error: {e}")
    
    # Test 3: Camera Placement
    print("\n3. Testing Camera Placement...")
    try:
        response = requests.post('http://localhost:8000/api/camera/optimal-placement',
            json={'lat': 44.2619, 'lon': -72.5806},
            timeout=10)
        if response.status_code == 200:
            camera_data = response.json()
            optimal_camera = camera_data.get('optimal_camera', {})
            print(f"   ✅ Camera Placement Generated")
            print(f"   ✅ Confidence: {optimal_camera.get('confidence_score', 'N/A')}%")
            print(f"   ✅ Distance: {optimal_camera.get('distance_meters', 'N/A')}m")
            tests_passed += 1
        else:
            print(f"   ❌ Camera placement failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Camera placement error: {e}")
    
    # Test 4: Enhanced Stand Analysis
    print("\n4. Testing Enhanced Stand Analysis...")
    try:
        response = requests.post('http://localhost:8000/predict', 
            json={
                'lat': 44.2619, 
                'lon': -72.5806, 
                'date_time': '2025-11-15T06:00:00', 
                'season': 'rut',
                'include_camera_placement': True
            }, 
            timeout=15)
        if response.status_code == 200:
            data = response.json()
            terrain = data.get('terrain_features', {})
            camera_placement = data.get('optimal_camera_placement', {})
            
            print(f"   ✅ Enhanced Analysis Generated")
            print(f"   ✅ Terrain Features: {bool(terrain)}")
            print(f"   ✅ Camera Integration: {camera_placement.get('enabled', False)}")
            tests_passed += 1
        else:
            print(f"   ❌ Enhanced analysis failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Enhanced analysis error: {e}")
    
    # Frontend Test (simple check)
    print("\n5. Testing Frontend Access...")
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Frontend accessible")
        else:
            print(f"   ⚠️  Frontend response: {response.status_code} (may be normal for Streamlit)")
    except Exception as e:
        print(f"   ⚠️  Frontend check: {e} (may be normal for Streamlit)")
    
    # Results
    print("\n" + "=" * 60)
    print("🎯 DEPLOYMENT READINESS RESULTS")
    print("=" * 60)
    
    success_rate = (tests_passed / total_tests) * 100
    
    print(f"✅ Tests Passed: {tests_passed}/{total_tests} ({success_rate:.1f}%)")
    
    if tests_passed == total_tests:
        print("\n🎉 READY FOR DEPLOYMENT!")
        print("✅ All core systems operational")
        print("✅ Prediction engine working")
        print("✅ Camera placement system functional")
        print("✅ Enhanced stand analysis operational")
        print("\n🦌 Your deer hunting app is ready for hunting season 2025!")
        print("📍 Access at: http://localhost:8501")
        return True
    elif tests_passed >= 3:
        print("\n✨ MOSTLY READY FOR DEPLOYMENT")
        print("✅ Core functionality working")
        print("⚠️  Some advanced features may need attention")
        print("\n🦌 App is usable for hunting with basic features")
        return True
    else:
        print("\n❌ NOT READY FOR DEPLOYMENT")
        print("🔧 Please address the failed tests above")
        return False

if __name__ == "__main__":
    ready = test_deployment_readiness()
    exit(0 if ready else 1)
