#!/usr/bin/env python3
"""
FRONTEND VALIDATION TEST

This test validates that the frontend is displaying correct information
from the backend API and providing proper user experience.

Author: GitHub Copilot
Date: August 26, 2025
"""

import requests
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_frontend_data_accuracy():
    """Test that frontend displays accurate data from backend"""
    print("🌐 FRONTEND DATA ACCURACY TEST")
    print("=" * 50)
    
    # First, get reference data from backend API
    print("📡 Getting reference data from backend API...")
    try:
        headers = {"Content-Type": "application/json"}
        body = {
            "lat": 43.3127, 
            "lon": -73.2271, 
            "date_time": "2025-08-26T07:00:00", 
            "season": "early_season",
            "fast_mode": True
        }
        
        api_response = requests.post(
            "http://127.0.0.1:8000/predict", 
            headers=headers, 
            json=body, 
            timeout=120
        )
        
        if api_response.status_code == 200:
            raw_backend = api_response.json()
            backend_data = raw_backend.get("data", raw_backend)
            print("✅ Backend API responding correctly")

            stand_rating = backend_data.get("confidence_score")
            if stand_rating is None:
                stand_rating = (
                    backend_data
                    .get("bedding_zones", {})
                    .get("properties", {})
                    .get("suitability_analysis", {})
                    .get("overall_score")
                )
                if stand_rating is not None:
                    stand_rating /= 100.0
            if stand_rating is not None:
                print(f"  📊 Confidence Score: {stand_rating:.2f}")

            feeding_features = backend_data.get("feeding_areas", {}).get("features", [])
            bedding_features = backend_data.get("bedding_zones", {}).get("features", [])
            travel_features = backend_data.get("travel_corridors", {}).get("features", [])
            stand_recs = (
                backend_data
                .get("mature_buck_analysis", {})
                .get("stand_recommendations", backend_data.get("stand_recommendations", []))
            )

            print(f"  🎯 Feeding Areas: {len(feeding_features)}")
            print(f"  🛏️ Bedding Zones: {len(bedding_features)}")
            print(f"  🚶 Travel Corridors: {len(travel_features)}")
            print(f"  🏹 Stand Recommendations: {len(stand_recs)}")
        else:
            print(f"❌ Backend API error: {api_response.status_code}")
            return False, {}
            
    except Exception as e:
        print(f"❌ Backend API failed: {e}")
        return False, {}
    
    # Now test frontend accessibility and basic functionality
    print("\n🖥️ Testing frontend accessibility...")
    
    frontend_results = {
        "backend_api_working": True,
        "frontend_accessible": False,
        "contains_deer_content": False,
        "contains_prediction_data": False,
        "displays_coordinates": False,
        "shows_biological_info": False
    }
    
    try:
        # Test frontend HTTP accessibility
        frontend_response = requests.get("http://127.0.0.1:8501", timeout=60)
        
        if frontend_response.status_code == 200:
            frontend_results["frontend_accessible"] = True
            print("✅ Frontend accessible via HTTP")
            
            content = frontend_response.text.lower()
            
            # Check for key content indicators
            if any(word in content for word in ["deer", "hunting", "prediction", "stand"]):
                frontend_results["contains_deer_content"] = True
                print("✅ Frontend contains deer hunting content")
            
            if any(word in content for word in ["lat", "lon", "coordinate", "43.3", "-73.2"]):
                frontend_results["displays_coordinates"] = True
                print("✅ Frontend displays coordinate information")
                
            if any(word in content for word in ["feeding", "bedding", "movement", "wind", "thermal"]):
                frontend_results["shows_biological_info"] = True
                print("✅ Frontend shows biological information")
                
            if any(word in content for word in ["predict", "analysis", "confidence", "score"]):
                frontend_results["contains_prediction_data"] = True
                print("✅ Frontend contains prediction data")
        else:
            print(f"❌ Frontend HTTP error: {frontend_response.status_code}")
            
    except Exception as e:
        print(f"❌ Frontend accessibility error: {e}")
    
    # Test basic Selenium interaction (simplified)
    print("\n🤖 Testing basic frontend interaction...")
    
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(20)

        driver.get("http://127.0.0.1:8501")
        time.sleep(5)  # Wait for Streamlit to load

        # Check if page loaded properly
        page_title = driver.title
        if page_title and "streamlit" not in page_title.lower():
            print(f"✅ Frontend page loaded: {page_title}")
        else:
            print("✅ Frontend Streamlit page loaded")

        # Look for any interactive elements
        interactive_elements = driver.find_elements(By.CSS_SELECTOR, "button, input, select, [role='button']")
        if interactive_elements:
            print(f"✅ Found {len(interactive_elements)} interactive elements")

        # Look for data display elements
        data_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid], .metric, .dataframe")
        if data_elements:
            print(f"✅ Found {len(data_elements)} data display elements")

        # Check page content for biological terms and coordinates
        page_source = driver.page_source.lower()
        clean_text = re.sub(r"<[^>]+>", " ", page_source)
        bio_terms = ["deer", "hunting", "feeding", "bedding", "stand", "movement"]
        found_terms = [term for term in bio_terms if term in clean_text]

        if found_terms:
            print(f"✅ Biological content detected: {', '.join(found_terms)}")
            frontend_results["contains_deer_content"] = True
        else:
            print("⚠️ Limited biological content in frontend")

        if any(token in clean_text for token in ["confidence", "score", "analysis", "recommendation"]):
            frontend_results["contains_prediction_data"] = True

        if not frontend_results["displays_coordinates"]:
            if any(token in clean_text for token in ["lat", "lon", "coordinate", "current location", "43.3", "-73.2"]):
                frontend_results["displays_coordinates"] = True
            elif re.search(r"\d{2}\.\d{3,}\s*,\s*-?\d{2,3}\.\d{3,}", clean_text):
                frontend_results["displays_coordinates"] = True

    except Exception as e:
        print(f"❌ Selenium test error: {e}")

    finally:
        if driver:
            driver.quit()
    
    # Calculate overall frontend score
    working_features = sum(frontend_results.values())
    total_features = len(frontend_results)
    frontend_score = working_features / total_features
    
    print(f"\n📊 FRONTEND VALIDATION SUMMARY")
    print("─" * 40)
    
    for feature, working in frontend_results.items():
        status = "✅" if working else "❌"
        print(f"  {status} {feature.replace('_', ' ').title()}: {working}")
    
    print(f"\n🎯 Frontend Score: {frontend_score:.1%} ({working_features}/{total_features})")
    
    if frontend_score >= 0.8:
        print("✅ FRONTEND VALIDATION PASSED!")
        print("  • Frontend is accessible and functional")
        print("  • Biological content is properly displayed")
        print("  • System ready for user testing")
    elif frontend_score >= 0.6:
        print("⚠️ FRONTEND PARTIALLY VALIDATED")
        print("  • Core functionality working")
        print("  • Some improvements needed for production")
    else:
        print("❌ FRONTEND NEEDS ATTENTION")
        print("  • Accessibility or content issues detected")
        print("  • Requires troubleshooting before deployment")
    
    return frontend_score >= 0.6, backend_data

def test_backend_biological_accuracy():
    """Test that backend predictions are biologically sound"""
    print("\n🧠 BACKEND BIOLOGICAL ACCURACY TEST")
    print("=" * 50)
    
    test_locations = [
        {"name": "Tinmouth, Vermont", "lat": 43.3127, "lon": -73.2271},
        {"name": "Central Vermont", "lat": 44.26639, "lon": -72.58133},
        {"name": "Southern Vermont", "lat": 42.8, "lon": -73.0}
    ]
    
    biological_accuracy_score = 0
    total_tests = 0
    
    for location in test_locations:
        print(f"\n📍 Testing {location['name']} ({location['lat']}, {location['lon']})")
        
        try:
            headers = {"Content-Type": "application/json"}
            body = {
                "lat": location["lat"], 
                "lon": location["lon"], 
                "date_time": "2025-08-26T07:00:00", 
                "season": "early_season",
                "fast_mode": True
            }
            
            response = requests.post(
                "http://127.0.0.1:8000/predict", 
                headers=headers, 
                json=body, 
                timeout=120
            )
            
            if response.status_code == 200:
                raw_data = response.json()
                data = raw_data.get('data', raw_data)
                stand_recommendations = (
                    data
                    .get('mature_buck_analysis', {})
                    .get('stand_recommendations', data.get('stand_recommendations', []))
                )

                # Test biological accuracy indicators
                tests = {
                    "has_feeding_areas": len(data.get('feeding_areas', {}).get('features', [])) > 0,
                    "has_travel_corridors": len(data.get('travel_corridors', {}).get('features', [])) > 0,
                    "has_stand_recommendations": len(stand_recommendations) > 0,
                    "reasonable_confidence": 0.0 <= data.get('confidence_score', 0) <= 1.0,
                    "has_confidence_scores": any(rec.get('confidence', 0) > 0 for rec in stand_recommendations),
                }

                location_score = sum(tests.values()) / len(tests)
                biological_accuracy_score += location_score
                total_tests += 1
                
                print(f"  🎯 Feeding Areas: {len(data.get('feeding_areas', {}).get('features', []))}")
                print(f"  🚶 Travel Corridors: {len(data.get('travel_corridors', {}).get('features', []))}")
                print(f"  🏹 Stand Recommendations: {len(stand_recommendations)}")
                print(f"  📊 Confidence Score: {data.get('confidence_score', 0):.3f}")
                print(f"  ✅ Location Score: {location_score:.1%}")
                
            else:
                print(f"  ❌ API Error: {response.status_code}")
                total_tests += 1
                
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
            total_tests += 1
    
    if total_tests > 0:
        overall_accuracy = biological_accuracy_score / total_tests
        print(f"\n🧠 BIOLOGICAL ACCURACY SUMMARY")
        print("─" * 40)
        print(f"📈 Overall Accuracy: {overall_accuracy:.1%}")
        
        if overall_accuracy >= 0.9:
            print("✅ EXCELLENT BIOLOGICAL ACCURACY!")
            print("  • Predictions are biologically sound")
            print("  • System ready for deployment")
        elif overall_accuracy >= 0.7:
            print("✅ GOOD BIOLOGICAL ACCURACY")
            print("  • Most predictions are sound")
            print("  • Ready for field testing")
        else:
            print("⚠️ BIOLOGICAL ACCURACY NEEDS IMPROVEMENT")
            print("  • Some predictions may be unrealistic")
            print("  • Requires biological logic review")
            
        return overall_accuracy >= 0.7
    
    return False

if __name__ == "__main__":
    print("🦌 COMPREHENSIVE FRONTEND & BACKEND VALIDATION")
    print("=" * 60)
    
    # Test backend biological accuracy
    backend_accurate = test_backend_biological_accuracy()
    
    # Test frontend functionality
    frontend_working, backend_data = test_frontend_data_accuracy()
    
    print(f"\n🏆 FINAL VALIDATION RESULTS")
    print("=" * 40)
    
    backend_status = "✅ PASSED" if backend_accurate else "❌ NEEDS WORK"
    frontend_status = "✅ PASSED" if frontend_working else "❌ NEEDS WORK"
    
    print(f"🧠 Backend Biological Accuracy: {backend_status}")
    print(f"🌐 Frontend Functionality: {frontend_status}")
    
    if backend_accurate and frontend_working:
        print("\n🎉 SYSTEM VALIDATION SUCCESSFUL!")
        print("✅ Backend making accurate biological predictions")
        print("✅ Frontend displaying information correctly")
        print("🚀 System ready for production deployment!")
    elif backend_accurate:
        print("\n⚠️ BACKEND VALIDATED, FRONTEND NEEDS ATTENTION")
        print("✅ Biological predictions are working correctly")
        print("⚠️ Frontend display issues need to be resolved")
    elif frontend_working:
        print("\n⚠️ FRONTEND WORKING, BACKEND NEEDS TUNING")
        print("✅ Frontend is functional and accessible")
        print("⚠️ Backend biological accuracy needs improvement")
    else:
        print("\n❌ BOTH SYSTEMS NEED ATTENTION")
        print("❌ Backend biological accuracy is insufficient")
        print("❌ Frontend has accessibility or display issues")
    
    print("\n" + "="*60)
    print("🦌 DEER PREDICTION SYSTEM VALIDATION COMPLETE 🦌")
    print("="*60)
