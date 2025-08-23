#!/usr/bin/env python3
"""
Comprehensive Backend Validation Suite
Tests backend accuracy, data quality, and frontend integration
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Backend configuration
BACKEND_URL = "http://127.0.0.1:8000"
TEST_LOCATIONS = [
    {"name": "Vermont Test Location", "lat": 44.26639, "lon": -72.58133},
    {"name": "Adirondacks Location", "lat": 43.314437, "lon": -73.226237},
    {"name": "Northern Vermont", "lat": 44.55, "lon": -72.75},
    {"name": "Southern Vermont", "lat": 42.85, "lon": -72.80}
]

class BackendValidator:
    def __init__(self):
        self.test_results = {}
        self.errors = []
        self.warnings = []
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        self.test_results[test_name] = {
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
            
    def log_warning(self, message: str):
        """Log warning"""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")
        
    def test_backend_health(self) -> bool:
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Backend Health Check", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_result("Backend Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Backend Health Check", False, f"Connection error: {str(e)}")
            return False
            
    def test_prediction_accuracy(self) -> bool:
        """Test prediction endpoints for accuracy and data quality"""
        all_passed = True
        
        for location in TEST_LOCATIONS:
            try:
                # Test prediction request
                payload = {
                    "latitude": location["lat"],
                    "longitude": location["lon"],
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": "06:00",
                    "season": "early_season",
                    "weather": {
                        "temperature": 45,
                        "wind_speed": 8,
                        "wind_direction": 225,
                        "pressure": 30.15,
                        "humidity": 65
                    }
                }
                
                response = requests.post(f"{BACKEND_URL}/predict", json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate response structure
                    required_fields = ['markers', 'stand_locations', 'confidence', 'analysis']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_result(f"Prediction Structure - {location['name']}", False, 
                                      f"Missing fields: {missing_fields}")
                        all_passed = False
                    else:
                        # Validate data quality
                        markers = data.get('markers', [])
                        stands = data.get('stand_locations', [])
                        confidence = data.get('confidence', 0)
                        
                        # Check marker counts
                        marker_types = {}
                        for marker in markers:
                            marker_type = marker.get('type', 'unknown')
                            marker_types[marker_type] = marker_types.get(marker_type, 0) + 1
                            
                        # Validate stand locations
                        valid_stands = 0
                        for stand in stands:
                            if (stand.get('lat') and stand.get('lon') and 
                                abs(stand['lat'] - location['lat']) < 0.1 and
                                abs(stand['lon'] - location['lon']) < 0.1):
                                valid_stands += 1
                                
                        details = f"Markers: {len(markers)}, Stands: {valid_stands}/{len(stands)}, Confidence: {confidence}%"
                        
                        # Quality checks
                        quality_passed = True
                        quality_issues = []
                        
                        if confidence < 50:
                            quality_issues.append(f"Low confidence: {confidence}%")
                            quality_passed = False
                            
                        if len(stands) < 3:
                            quality_issues.append(f"Too few stands: {len(stands)}")
                            quality_passed = False
                            
                        if len(markers) < 5:
                            quality_issues.append(f"Too few markers: {len(markers)}")
                            quality_passed = False
                            
                        if quality_issues:
                            self.log_result(f"Prediction Quality - {location['name']}", False,
                                          f"{details}. Issues: {', '.join(quality_issues)}")
                            all_passed = False
                        else:
                            self.log_result(f"Prediction Quality - {location['name']}", True, details)
                            
                else:
                    self.log_result(f"Prediction Response - {location['name']}", False, 
                                  f"HTTP {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"Prediction Test - {location['name']}", False, f"Error: {str(e)}")
                all_passed = False
                
        return all_passed
        
    def test_seasonal_variations(self) -> bool:
        """Test predictions across different seasons"""
        seasons = ["early_season", "pre_rut", "rut", "post_rut", "late_season"]
        location = TEST_LOCATIONS[1]  # Use Adirondacks location
        all_passed = True
        
        results = {}
        
        for season in seasons:
            try:
                payload = {
                    "latitude": location["lat"],
                    "longitude": location["lon"],
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": "06:00",
                    "season": season,
                    "weather": {
                        "temperature": 35 if season in ["late_season", "post_rut"] else 55,
                        "wind_speed": 5,
                        "wind_direction": 270,
                        "pressure": 30.10,
                        "humidity": 70
                    }
                }
                
                response = requests.post(f"{BACKEND_URL}/predict", json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    confidence = data.get('confidence', 0)
                    stands = len(data.get('stand_locations', []))
                    markers = len(data.get('markers', []))
                    
                    results[season] = {
                        "confidence": confidence,
                        "stands": stands,
                        "markers": markers
                    }
                    
                    if confidence < 40:
                        self.log_warning(f"Low confidence for {season}: {confidence}%")
                        
                else:
                    self.log_result(f"Seasonal Test - {season}", False, f"HTTP {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"Seasonal Test - {season}", False, f"Error: {str(e)}")
                all_passed = False
                
        # Check for seasonal variation
        if results:
            confidences = [r["confidence"] for r in results.values()]
            confidence_range = max(confidences) - min(confidences)
            
            if confidence_range < 5:
                self.log_warning("Limited seasonal variation in confidence scores")
                
            self.log_result("Seasonal Variations", True, 
                          f"Tested {len(results)} seasons, confidence range: {confidence_range:.1f}%")
        
        return all_passed
        
    def test_camera_placement(self) -> bool:
        """Test camera placement endpoints"""
        location = TEST_LOCATIONS[0]
        all_passed = True
        
        try:
            payload = {
                "latitude": location["lat"],
                "longitude": location["lon"],
                "radius_miles": 0.5,
                "terrain_features": ["water", "ridge", "valley"],
                "camera_count": 3
            }
            
            response = requests.post(f"{BACKEND_URL}/trail-cameras", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                cameras = data.get('camera_locations', [])
                
                if len(cameras) >= 2:
                    # Check camera positioning quality
                    valid_positions = 0
                    for camera in cameras:
                        if (camera.get('lat') and camera.get('lon') and 
                            camera.get('confidence', 0) > 50):
                            valid_positions += 1
                            
                    if valid_positions >= len(cameras) * 0.8:  # 80% should be good quality
                        self.log_result("Camera Placement Quality", True, 
                                      f"{valid_positions}/{len(cameras)} high-quality positions")
                    else:
                        self.log_result("Camera Placement Quality", False,
                                      f"Only {valid_positions}/{len(cameras)} high-quality positions")
                        all_passed = False
                else:
                    self.log_result("Camera Placement Count", False, f"Only {len(cameras)} cameras generated")
                    all_passed = False
                    
            else:
                self.log_result("Camera Placement Response", False, f"HTTP {response.status_code}")
                all_passed = False
                
        except Exception as e:
            self.log_result("Camera Placement Test", False, f"Error: {str(e)}")
            all_passed = False
            
        return all_passed
        
    def test_scouting_integration(self) -> bool:
        """Test scouting data endpoints"""
        all_passed = True
        
        try:
            # Test observation types
            response = requests.get(f"{BACKEND_URL}/scouting/types", timeout=10)
            if response.status_code == 200:
                types = response.json()
                if len(types) >= 5:  # Should have multiple observation types
                    self.log_result("Scouting Types", True, f"Found {len(types)} observation types")
                else:
                    self.log_result("Scouting Types", False, f"Only {len(types)} observation types")
                    all_passed = False
            else:
                self.log_result("Scouting Types", False, f"HTTP {response.status_code}")
                all_passed = False
                
            # Test observations retrieval
            location = TEST_LOCATIONS[1]
            response = requests.get(
                f"{BACKEND_URL}/scouting/observations",
                params={
                    "lat": location["lat"],
                    "lon": location["lon"],
                    "radius_miles": 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                observations = response.json()
                self.log_result("Scouting Observations", True, 
                              f"Retrieved {len(observations)} observations")
            else:
                self.log_result("Scouting Observations", False, f"HTTP {response.status_code}")
                all_passed = False
                
        except Exception as e:
            self.log_result("Scouting Integration", False, f"Error: {str(e)}")
            all_passed = False
            
        return all_passed
        
    def test_performance_metrics(self) -> bool:
        """Test API performance and response times"""
        location = TEST_LOCATIONS[0]
        all_passed = True
        
        # Test response time
        start_time = time.time()
        try:
            payload = {
                "latitude": location["lat"],
                "longitude": location["lon"],
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "06:00",
                "season": "early_season"
            }
            
            response = requests.post(f"{BACKEND_URL}/predict", json=payload, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                if response_time < 10:  # Should respond within 10 seconds
                    self.log_result("Response Time", True, f"{response_time:.2f}s")
                else:
                    self.log_result("Response Time", False, f"Slow response: {response_time:.2f}s")
                    all_passed = False
            else:
                self.log_result("Performance Test", False, f"HTTP {response.status_code}")
                all_passed = False
                
        except Exception as e:
            self.log_result("Performance Test", False, f"Error: {str(e)}")
            all_passed = False
            
        return all_passed
        
    def test_data_consistency(self) -> bool:
        """Test data consistency across multiple calls"""
        location = TEST_LOCATIONS[0]
        all_passed = True
        
        try:
            # Make 3 identical requests
            payload = {
                "latitude": location["lat"],
                "longitude": location["lon"],
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "06:00",
                "season": "early_season",
                "weather": {
                    "temperature": 45,
                    "wind_speed": 5,
                    "wind_direction": 180,
                    "pressure": 30.0,
                    "humidity": 60
                }
            }
            
            responses = []
            for i in range(3):
                response = requests.post(f"{BACKEND_URL}/predict", json=payload, timeout=30)
                if response.status_code == 200:
                    responses.append(response.json())
                else:
                    self.log_result(f"Consistency Test Request {i+1}", False, f"HTTP {response.status_code}")
                    all_passed = False
                    
            # Check consistency
            if len(responses) >= 2:
                # Compare stand counts
                stand_counts = [len(r.get('stand_locations', [])) for r in responses]
                marker_counts = [len(r.get('markers', [])) for r in responses]
                confidences = [r.get('confidence', 0) for r in responses]
                
                # Allow for small variations but check major consistency
                stand_variation = max(stand_counts) - min(stand_counts)
                confidence_variation = max(confidences) - min(confidences)
                
                if stand_variation <= 2 and confidence_variation <= 10:
                    self.log_result("Data Consistency", True, 
                                  f"Stand variation: {stand_variation}, Confidence variation: {confidence_variation:.1f}%")
                else:
                    self.log_result("Data Consistency", False,
                                  f"High variation - Stands: {stand_variation}, Confidence: {confidence_variation:.1f}%")
                    all_passed = False
                    
        except Exception as e:
            self.log_result("Data Consistency Test", False, f"Error: {str(e)}")
            all_passed = False
            
        return all_passed
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["passed"])
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%",
                "warnings": len(self.warnings)
            },
            "test_results": self.test_results,
            "warnings": self.warnings,
            "timestamp": datetime.now().isoformat()
        }
        
        return report
        
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Starting Comprehensive Backend Validation")
        print("=" * 50)
        
        # Check if backend is running
        if not self.test_backend_health():
            print("\n❌ Backend not accessible - stopping tests")
            return False
            
        print("\n🎯 Testing Prediction Accuracy...")
        self.test_prediction_accuracy()
        
        print("\n🍂 Testing Seasonal Variations...")
        self.test_seasonal_variations()
        
        print("\n📷 Testing Camera Placement...")
        self.test_camera_placement()
        
        print("\n🔍 Testing Scouting Integration...")
        self.test_scouting_integration()
        
        print("\n⚡ Testing Performance...")
        self.test_performance_metrics()
        
        print("\n🔄 Testing Data Consistency...")
        self.test_data_consistency()
        
        # Generate final report
        report = self.generate_report()
        
        print("\n" + "=" * 50)
        print("📊 VALIDATION REPORT")
        print("=" * 50)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed_tests']}")
        print(f"Failed: {report['summary']['failed_tests']}")
        print(f"Success Rate: {report['summary']['success_rate']}")
        print(f"Warnings: {report['summary']['warnings']}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   - {warning}")
                
        # Save detailed report
        with open('backend_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: backend_validation_report.json")
        
        return report['summary']['failed_tests'] == 0

if __name__ == "__main__":
    validator = BackendValidator()
    success = validator.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - Backend is producing accurate data!")
        sys.exit(0)
    else:
        print("\n🚨 SOME TESTS FAILED - Check report for details")
        sys.exit(1)
