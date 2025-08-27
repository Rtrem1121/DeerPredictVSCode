#!/usr/bin/env python3
"""
Quick Validation Script for Enhanced Deer Prediction Features

Specifically tests:
- Mature buck movement intelligence accuracy
- Stand #1 enhanced analysis with wind/deer approach directions
- Camera placement algorithm confidence scores
- Frontend data consistency

Author: Vermont Deer Prediction System
Version: 2.0.0
"""

import requests
import json
import time
from datetime import datetime

class QuickValidationSuite:
    """Quick validation of key enhanced features"""
    
    def __init__(self, backend_url="http://localhost:8000"):
        self.backend_url = backend_url
        self.stand_1_coords = {"lat": 44.2619, "lon": -72.5806}  # Stand #1
        
    def run_validation(self):
        """Run quick validation of key features"""
        print("🎯 QUICK VALIDATION - ENHANCED DEER PREDICTION FEATURES")
        print("=" * 65)
        
        # Test 1: Mature Buck Movement Intelligence
        print("\\n🦌 TEST 1: MATURE BUCK MOVEMENT INTELLIGENCE")
        buck_results = self.test_mature_buck_intelligence()
        
        # Test 2: Enhanced Stand #1 Analysis
        print("\\n🎯 TEST 2: ENHANCED STAND #1 ANALYSIS")
        stand_results = self.test_stand_analysis()
        
        # Test 3: Camera Placement System
        print("\\n📹 TEST 3: CAMERA PLACEMENT SYSTEM")
        camera_results = self.test_camera_placement()
        
        # Test 4: Frontend Data Integration
        print("\\n🖥️ TEST 4: FRONTEND DATA INTEGRATION")
        frontend_results = self.test_frontend_integration()
        
        # Generate summary
        self.print_validation_summary(buck_results, stand_results, camera_results, frontend_results)
        
        return {
            "mature_buck_intelligence": buck_results,
            "stand_analysis": stand_results,
            "camera_placement": camera_results,
            "frontend_integration": frontend_results,
            "validation_timestamp": datetime.now().isoformat()
        }
    
    def test_mature_buck_intelligence(self):
        """Test mature buck movement predictions"""
        print("  📊 Testing movement pattern predictions...")
        
        try:
            # Test rut season movement during prime time
            response = requests.post(
                f"{self.backend_url}/predict",
                json={
                    "lat": self.stand_1_coords["lat"],
                    "lon": self.stand_1_coords["lon"],
                    "date_time": "2025-11-15T06:30:00",  # Dawn during rut
                    "season": "rut"
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return {"status": "FAILED", "error": f"API request failed: {response.status_code}"}
            
            data = response.json()
            results = {"status": "PASSED", "details": {}}
            
            # Check mature buck analysis
            buck_analysis = data.get("mature_buck_analysis", {})
            if buck_analysis:
                movement_confidence = buck_analysis.get("movement_confidence", 0)
                viable_location = buck_analysis.get("viable_location", False)
                
                results["details"]["movement_confidence"] = movement_confidence
                results["details"]["viable_location"] = viable_location
                
                print(f"    ✅ Movement confidence: {movement_confidence}%")
                print(f"    ✅ Viable location: {viable_location}")
                
                if movement_confidence < 70:
                    results["status"] = "WARNING"
                    results["warning"] = f"Low movement confidence: {movement_confidence}%"
            else:
                results["status"] = "FAILED"
                results["error"] = "Missing mature buck analysis"
            
            # Check travel corridors
            travel_corridors = data.get("travel_corridors", [])
            results["details"]["travel_corridors"] = len(travel_corridors)
            print(f"    ✅ Travel corridors identified: {len(travel_corridors)}")
            
            # Check bedding zones
            bedding_zones = data.get("bedding_zones", [])
            results["details"]["bedding_zones"] = len(bedding_zones)
            print(f"    ✅ Bedding zones identified: {len(bedding_zones)}")
            
            return results
            
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def test_stand_analysis(self):
        """Test enhanced Stand #1 analysis features"""
        print("  🧭 Testing wind direction and deer approach calculations...")
        
        try:
            # Get prediction data that frontend uses for Stand #1 analysis
            response = requests.post(
                f"{self.backend_url}/predict",
                json={
                    "lat": self.stand_1_coords["lat"],
                    "lon": self.stand_1_coords["lon"],
                    "date_time": "2025-11-15T06:00:00",
                    "season": "rut"
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return {"status": "FAILED", "error": f"API request failed: {response.status_code}"}
            
            data = response.json()
            results = {"status": "PASSED", "details": {}}
            
            # Check terrain features for wind calculations
            terrain = data.get("terrain_features", {})
            elevation = terrain.get("elevation", 0)
            slope = terrain.get("slope", 0)
            
            results["details"]["elevation"] = elevation
            results["details"]["slope"] = slope
            
            print(f"    ✅ Elevation: {elevation} feet")
            print(f"    ✅ Slope: {slope}°")
            
            # Validate terrain data is reasonable for Vermont
            if not (200 <= elevation <= 4000):
                results["status"] = "WARNING"
                results["warning"] = f"Elevation {elevation} outside typical Vermont range"
            
            # Check for bedding zones (needed for deer approach calculations)
            bedding_zones = data.get("bedding_zones", [])
            if bedding_zones:
                first_bedding = bedding_zones[0]
                bedding_lat = first_bedding.get("lat", 0)
                bedding_lon = first_bedding.get("lon", 0)
                
                # Calculate bearing (this is what frontend does)
                import math
                lat_diff = bedding_lat - self.stand_1_coords["lat"]
                lon_diff = bedding_lon - self.stand_1_coords["lon"]
                bearing = math.degrees(math.atan2(lon_diff, lat_diff))
                if bearing < 0:
                    bearing += 360
                
                results["details"]["deer_approach_bearing"] = bearing
                print(f"    ✅ Deer approach bearing: {bearing:.1f}°")
                
                # Convert to compass direction
                directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                compass_index = int((bearing + 11.25) / 22.5) % 16
                compass_dir = directions[compass_index]
                
                results["details"]["deer_approach_direction"] = compass_dir
                print(f"    ✅ Deer approach direction: {compass_dir}")
                
                # Calculate wind directions (what frontend displays)
                deer_approach_bearing = (bearing + 180) % 360
                optimal_wind_1 = (deer_approach_bearing + 90) % 360
                optimal_wind_2 = (deer_approach_bearing - 90) % 360
                
                wind_dir_1 = directions[int((optimal_wind_1 + 11.25) / 22.5) % 16]
                wind_dir_2 = directions[int((optimal_wind_2 + 11.25) / 22.5) % 16]
                
                results["details"]["optimal_wind_directions"] = [wind_dir_1, wind_dir_2]
                print(f"    ✅ Optimal wind directions: {wind_dir_1} or {wind_dir_2}")
                
            else:
                results["status"] = "WARNING" 
                results["warning"] = "No bedding zones found for deer approach calculations"
            
            return results
            
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def test_camera_placement(self):
        """Test camera placement algorithm"""
        print("  📸 Testing optimal camera positioning...")
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/camera/optimal-placement",
                json={
                    "lat": self.stand_1_coords["lat"],
                    "lon": self.stand_1_coords["lon"]
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return {"status": "FAILED", "error": f"Camera API request failed: {response.status_code}"}
            
            camera_data = response.json()
            results = {"status": "PASSED", "details": {}}
            
            # Check optimal camera data
            optimal_camera = camera_data.get("optimal_camera", {})
            if optimal_camera:
                camera_lat = optimal_camera.get("lat", 0)
                camera_lon = optimal_camera.get("lon", 0)
                confidence_score = optimal_camera.get("confidence_score", 0)
                distance_meters = optimal_camera.get("distance_from_target_meters", 0)
                
                results["details"]["camera_coordinates"] = [camera_lat, camera_lon]
                results["details"]["confidence_score"] = confidence_score
                results["details"]["distance_meters"] = distance_meters
                
                print(f"    ✅ Camera position: {camera_lat:.4f}, {camera_lon:.4f}")
                print(f"    ✅ Confidence score: {confidence_score}%")
                print(f"    ✅ Distance from stand: {distance_meters:.1f} meters")
                
                # Validate confidence score
                if confidence_score < 85:
                    results["status"] = "WARNING"
                    results["warning"] = f"Confidence score {confidence_score}% below 85% threshold"
                
                # Validate distance is in optimal range
                if not (50 <= distance_meters <= 200):
                    results["status"] = "WARNING"
                    results["warning"] = f"Distance {distance_meters}m outside optimal range (50-200m)"
                
            else:
                results["status"] = "FAILED"
                results["error"] = "Missing optimal camera data"
            
            # Check placement strategy
            strategy = camera_data.get("placement_strategy", {})
            if strategy:
                rationale = strategy.get("positioning_rationale", "")
                results["details"]["has_strategy"] = True
                print(f"    ✅ Strategic reasoning provided")
                
                if len(rationale) < 50:
                    results["status"] = "WARNING"
                    results["warning"] = "Strategic reasoning too brief"
            else:
                results["status"] = "WARNING"
                results["warning"] = "Missing placement strategy"
            
            return results
            
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def test_frontend_integration(self):
        """Test frontend data integration"""
        print("  🔗 Testing frontend data consistency...")
        
        try:
            # Test prediction with camera placement (what frontend requests)
            response = requests.post(
                f"{self.backend_url}/predict",
                json={
                    "lat": self.stand_1_coords["lat"],
                    "lon": self.stand_1_coords["lon"],
                    "date_time": "2025-11-15T06:00:00",
                    "season": "rut",
                    "include_camera_placement": True
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return {"status": "FAILED", "error": f"Frontend integration API failed: {response.status_code}"}
            
            data = response.json()
            results = {"status": "PASSED", "details": {}}
            
            # Check that camera placement is included
            if "camera_placement" in data:
                camera_data = data["camera_placement"]
                optimal_camera = camera_data.get("optimal_camera", {})
                
                if optimal_camera:
                    results["details"]["camera_integrated"] = True
                    print(f"    ✅ Camera placement integrated successfully")
                else:
                    results["status"] = "WARNING"
                    results["warning"] = "Camera placement missing optimal_camera data"
            else:
                results["status"] = "WARNING"
                results["warning"] = "Camera placement not included in response"
            
            # Check for all required data that frontend displays
            required_fields = [
                "terrain_features",
                "mature_buck_analysis",
                "bedding_zones",
                "travel_corridors"
            ]
            
            missing_fields = []
            for field in required_fields:
                if field in data:
                    results["details"][f"has_{field}"] = True
                else:
                    missing_fields.append(field)
            
            if missing_fields:
                results["status"] = "WARNING"
                results["warning"] = f"Missing frontend data: {', '.join(missing_fields)}"
            else:
                print(f"    ✅ All required frontend data present")
            
            # Test data consistency across multiple requests
            print("    🔄 Testing data consistency...")
            second_response = requests.post(
                f"{self.backend_url}/predict",
                json={
                    "lat": self.stand_1_coords["lat"],
                    "lon": self.stand_1_coords["lon"],
                    "date_time": "2025-11-15T06:00:00",
                    "season": "rut",
                    "include_camera_placement": True
                },
                timeout=30
            )
            
            if second_response.status_code == 200:
                second_data = second_response.json()
                
                # Compare terrain features (should be identical)
                terrain_1 = data.get("terrain_features", {})
                terrain_2 = second_data.get("terrain_features", {})
                
                if terrain_1.get("elevation") == terrain_2.get("elevation"):
                    results["details"]["data_consistent"] = True
                    print(f"    ✅ Data consistency verified")
                else:
                    results["status"] = "WARNING"
                    results["warning"] = "Data inconsistency detected between requests"
            
            return results
            
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def print_validation_summary(self, buck_results, stand_results, camera_results, frontend_results):
        """Print comprehensive validation summary"""
        print("\\n" + "=" * 65)
        print("🎯 QUICK VALIDATION SUMMARY")
        print("=" * 65)
        
        all_results = [buck_results, stand_results, camera_results, frontend_results]
        test_names = [
            "Mature Buck Intelligence",
            "Enhanced Stand Analysis", 
            "Camera Placement System",
            "Frontend Integration"
        ]
        
        passed_count = 0
        warning_count = 0
        failed_count = 0
        
        print("\\n📊 TEST RESULTS:")
        for i, (name, result) in enumerate(zip(test_names, all_results)):
            status = result.get("status", "UNKNOWN")
            
            if status == "PASSED":
                print(f"   {i+1}. {name}: ✅ PASSED")
                passed_count += 1
            elif status == "WARNING":
                print(f"   {i+1}. {name}: ⚠️ WARNING")
                warning_count += 1
                if "warning" in result:
                    print(f"      └─ {result['warning']}")
            elif status == "FAILED":
                print(f"   {i+1}. {name}: ❌ FAILED")
                failed_count += 1
                if "error" in result:
                    print(f"      └─ {result['error']}")
            else:
                print(f"   {i+1}. {name}: ❓ ERROR")
                failed_count += 1
        
        # Overall assessment
        total_tests = len(all_results)
        success_rate = (passed_count / total_tests) * 100
        
        print(f"\\n📈 OVERALL ASSESSMENT:")
        print(f"   Passed: {passed_count}/{total_tests} ({success_rate:.1f}%)")
        print(f"   Warnings: {warning_count}")
        print(f"   Failed: {failed_count}")
        
        if failed_count == 0 and warning_count == 0:
            print("\\n🟢 EXCELLENT: All systems functioning optimally!")
        elif failed_count == 0:
            print("\\n🟡 GOOD: System functional with minor optimization opportunities")
        elif failed_count <= 1:
            print("\\n🟠 FAIR: System mostly functional, address failed components")
        else:
            print("\\n🔴 POOR: Multiple system failures require immediate attention")
        
        # Specific recommendations
        print("\\n💡 RECOMMENDATIONS:")
        
        if buck_results.get("status") == "FAILED":
            print("   🚨 CRITICAL: Fix mature buck movement predictions")
        elif buck_results.get("status") == "WARNING":
            print("   ⚠️ Optimize mature buck movement confidence scores")
        
        if camera_results.get("status") == "FAILED":
            print("   🚨 CRITICAL: Fix camera placement algorithm")
        elif camera_results.get("status") == "WARNING":
            print("   ⚠️ Improve camera placement confidence or positioning")
        
        if frontend_results.get("status") == "WARNING":
            print("   ⚠️ Enhance frontend data integration")
        
        if success_rate >= 90:
            print("   ✅ DEPLOY: System ready for production use")

if __name__ == "__main__":
    validator = QuickValidationSuite()
    
    print("🚀 Starting quick validation of enhanced features...")
    print("This will test the most critical algorithmic components.\\n")
    
    # Run validation
    results = validator.run_validation()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"quick_validation_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\\n📄 Validation results saved to: {filename}")
    print("\\n🎯 QUICK VALIDATION COMPLETE!")
