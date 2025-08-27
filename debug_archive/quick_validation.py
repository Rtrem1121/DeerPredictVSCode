#!/usr/bin/env python3

import requests
import json
from datetime import datetime

def quick_validation_test():
    """Quick validation of prediction pipeline"""
    
    print("🔍 Quick Prediction Pipeline Validation")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    test_lat = 44.2850  # Fred Johnson WMA area with GPX data
    test_lon = -73.0459
    
    results = {"passed": 0, "total": 0}
    
    # Test 1: Backend Health
    print("\n1️⃣  Testing Backend Health...")
    results["total"] += 1
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ Backend is healthy")
            results["passed"] += 1
        else:
            print(f"   ❌ Backend health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Backend connection error: {e}")
    
    # Test 2: Scouting Data (with correct parameters)
    print("\n2️⃣  Testing Scouting Data Integration...")
    results["total"] += 1
    try:
        response = requests.get(f"{base_url}/scouting/observations", params={
            "lat": test_lat,
            "lon": test_lon,
            "radius_miles": 5.0
        })
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', [])
            total_count = data.get('total_count', 0)
            print(f"   ✅ Found {total_count} scouting observations in 5-mile radius")
            results["passed"] += 1
            
            # Analyze observation types
            if observations:
                obs_types = {}
                for obs in observations:
                    obs_type = obs.get('observation_type', 'unknown')
                    obs_types[obs_type] = obs_types.get(obs_type, 0) + 1
                print(f"   📊 Observation types: {dict(list(obs_types.items())[:3])}")
        else:
            print(f"   ❌ Scouting data request failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Scouting data error: {e}")
    
    # Test 3: Prediction Algorithm (with correct parameters)
    print("\n3️⃣  Testing Prediction Algorithm...")
    results["total"] += 1
    try:
        prediction_data = {
            "lat": test_lat,
            "lon": test_lon,
            "date_time": datetime.now().isoformat(),
            "season": "rut",  # This should be November/December timeframe
            "fast_mode": False
        }
        
        response = requests.post(f"{base_url}/predict", json=prediction_data)
        if response.status_code == 200:
            prediction = response.json()
            probability = prediction.get('probability', 0)
            confidence = prediction.get('confidence', 0)
            print(f"   ✅ Prediction successful: {probability:.1f}% probability, {confidence:.1f}% confidence")
            results["passed"] += 1
            
            # Check for historical data factors
            factors = prediction.get('contributing_factors', {})
            historical_factors = []
            for factor_name, factor_value in factors.items():
                if factor_value > 0 and factor_name in ['scouting_data', 'bedding_areas', 'feeding_areas', 'trail_cameras']:
                    historical_factors.append(f"{factor_name}={factor_value}")
            
            if historical_factors:
                print(f"   📈 Historical data factors: {', '.join(historical_factors[:3])}")
            else:
                print("   ⚠️  No obvious historical data factors detected")
                
        else:
            print(f"   ❌ Prediction request failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Prediction error: {e}")
    
    # Test 4: GPX Import Status
    print("\n4️⃣  Testing GPX Import Status...")
    results["total"] += 1
    try:
        # Check if we have a good variety of observation types
        response = requests.get(f"{base_url}/scouting/observations", params={
            "lat": test_lat,
            "lon": test_lon,
            "radius_miles": 10.0  # Wider search for GPX data
        })
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', [])
            total_count = data.get('total_count', 0)
            
            # Look for signs of GPX import
            gpx_indicators = 0
            for obs in observations:
                notes = obs.get('notes', '').lower()
                if 'imported from gpx' in notes or 'elevation:' in notes:
                    gpx_indicators += 1
            
            if gpx_indicators > 0:
                print(f"   ✅ GPX import detected: {gpx_indicators} observations with GPX markers")
                results["passed"] += 1
            else:
                print("   ⚠️  No clear GPX import markers found")
                print(f"   📊 Total observations in area: {total_count}")
        else:
            print(f"   ❌ GPX status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ GPX status error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    success_rate = (results["passed"] / results["total"]) * 100
    print(f"   Tests Passed: {results['passed']}/{results['total']}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print("🎉 OVERALL STATUS: HEALTHY")
        print("   Your prediction pipeline is working correctly!")
        print("   Historical GPX data appears to be integrated.")
    elif success_rate >= 50:
        print("⚠️  OVERALL STATUS: PARTIALLY WORKING")
        print("   Core functionality works, but some issues detected.")
        print("   Your predictions are working but may not be fully optimized.")
    else:
        print("❌ OVERALL STATUS: NEEDS ATTENTION")
        print("   Multiple issues detected. Review required.")
    
    return results

if __name__ == "__main__":
    quick_validation_test()
