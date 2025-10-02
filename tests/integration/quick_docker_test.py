#!/usr/bin/env python3
"""
Quick Docker Validation Test
===========================

Tests that our enhanced bedding zone fix works in the Docker container
without all the complex dependencies.
"""

import requests
import json
import time

def test_docker_containers():
    """Test Docker container endpoints"""
    
    print("🔍 Testing Docker Container Integration...")
    
    # Test backend health
    try:
        backend_url = "http://localhost:8000"
        health_response = requests.get(f"{backend_url}/health", timeout=10)
        
        if health_response.status_code == 200:
            print("✅ Backend health check passed")
            health_data = health_response.json()
            print(f"   Version: {health_data.get('version', 'unknown')}")
            print(f"   Status: {health_data.get('status', 'unknown')}")
        else:
            print(f"❌ Backend health check failed: {health_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False
    
    # Test bedding validation endpoint
    try:
        # Test Tinmouth coordinates
        test_lat, test_lon = 43.3146, -73.2178
        validation_url = f"{backend_url}/api/bedding/validate/{test_lat}/{test_lon}"
        
        validation_response = requests.get(validation_url, timeout=30)
        
        if validation_response.status_code == 200:
            print("✅ Bedding validation endpoint accessible")
            validation_data = validation_response.json()
            
            # Check for expected data structure
            if 'bedding_zones' in validation_data and 'metrics' in validation_data:
                print("✅ Bedding validation returns correct structure")
                
                metrics = validation_data['metrics']
                avg_suitability = metrics.get('average_suitability', 0)
                zone_count = metrics.get('zone_count', 0)
                
                print(f"   Average Suitability: {avg_suitability}%")
                print(f"   Zone Count: {zone_count}")
                
                # Check if fix is working (should be much higher than original 43.1%)
                if avg_suitability > 60 and zone_count > 0:
                    print("✅ Bedding zone fix appears to be working!")
                    return True
                else:
                    print(f"⚠️ Results may indicate issues (avg: {avg_suitability}%, zones: {zone_count})")
                    return False
            else:
                print("❌ Bedding validation missing expected data structure")
                return False
        else:
            print(f"❌ Bedding validation endpoint failed: {validation_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Bedding validation test failed: {e}")
        return False

def test_frontend_container():
    """Test frontend container"""
    
    print("\n🖥️ Testing Frontend Container...")
    
    try:
        frontend_url = "http://localhost:8501"
        frontend_response = requests.get(frontend_url, timeout=10)
        
        if frontend_response.status_code == 200:
            print("✅ Frontend accessible")
            return True
        else:
            print(f"❌ Frontend not accessible: {frontend_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")
        return False

def main():
    """Run Docker validation tests"""
    
    print("=" * 60)
    print("🐳 DOCKER CONTAINER VALIDATION")
    print("=" * 60)
    
    # Wait a moment for containers to be ready
    print("⏳ Waiting for containers to be ready...")
    time.sleep(5)
    
    backend_success = test_docker_containers()
    frontend_success = test_frontend_container()
    
    print(f"\n📊 RESULTS:")
    print(f"Backend: {'✅ PASS' if backend_success else '❌ FAIL'}")
    print(f"Frontend: {'✅ PASS' if frontend_success else '❌ FAIL'}")
    
    if backend_success and frontend_success:
        print(f"\n🎉 All Docker containers are working correctly!")
        print(f"🌐 Access the app at: http://localhost:8501")
        print(f"📡 Backend API at: http://localhost:8000")
        return True
    else:
        print(f"\n🔧 Some containers need attention.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
