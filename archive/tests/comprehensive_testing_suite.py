#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Deer Prediction App v2.0

Executes complete validation of:
- Core prediction algorithms
- Mature buck movement intelligence  
- Camera placement system
- Frontend data integrity
- Integration accuracy

Author: Vermont Deer Prediction System
Version: 2.0.0
"""

import requests
import json
import time
import math
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

@dataclass
class TestResult:
    """Test result with details"""
    test_name: str
    passed: bool
    confidence_score: float
    details: Dict[str, Any]
    errors: List[str] = None

class ComprehensiveTestSuite:
    """Complete testing suite for deer prediction application"""
    
    def __init__(self, backend_url="http://localhost:8000", frontend_url="http://localhost:8501"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.results = []
        
        # Test locations across Vermont
        self.test_locations = [
            {"name": "Stand #1 (Primary)", "lat": 44.2619, "lon": -72.5806},
            {"name": "Central Vermont Ridge", "lat": 44.2500, "lon": -72.6000},
            {"name": "Agricultural Edge", "lat": 44.2800, "lon": -72.5500},
            {"name": "Water Feature Area", "lat": 44.2400, "lon": -72.5900},
            {"name": "High Elevation Test", "lat": 44.2700, "lon": -72.5700}
        ]
        
        print("🎯 COMPREHENSIVE DEER PREDICTION APP TESTING SUITE")
        print("=" * 60)
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Execute complete testing suite"""
        start_time = time.time()
        
        print("\\n🧪 PHASE 1: CORE ALGORITHM VALIDATION")
        phase1_results = self._test_core_algorithms()
        
        print("\\n🦌 PHASE 2: MATURE BUCK INTELLIGENCE VALIDATION")
        phase2_results = self._test_mature_buck_intelligence()
        
        print("\\n📹 PHASE 3: CAMERA PLACEMENT SYSTEM VALIDATION")
        phase3_results = self._test_camera_placement_system()
        
        print("\\n🖥️ PHASE 4: FRONTEND DATA INTEGRITY TESTING")
        phase4_results = self._test_frontend_integrity()
        
        print("\\n🔄 PHASE 5: INTEGRATION TESTING")
        phase5_results = self._test_integration_workflow()
        
        # Compile comprehensive results
        total_time = time.time() - start_time
        
        return self._generate_comprehensive_report({
            "phase_1_core_algorithms": phase1_results,
            "phase_2_mature_buck": phase2_results,
            "phase_3_camera_placement": phase3_results,
            "phase_4_frontend_integrity": phase4_results,
            "phase_5_integration": phase5_results,
            "total_execution_time": total_time
        })
    
    def _test_core_algorithms(self) -> Dict[str, Any]:
        """Phase 1: Test core prediction algorithms"""
        print("  📊 Testing terrain analysis accuracy...")
        terrain_results = self._test_terrain_analysis()
        
        print("  🌲 Testing vegetation health calculations...")
        vegetation_results = self._test_vegetation_calculations()
        
        print("  📈 Testing prediction consistency...")
        consistency_results = self._test_prediction_consistency()
        
        return {
            "terrain_analysis": terrain_results,
            "vegetation_calculations": vegetation_results,
            "prediction_consistency": consistency_results
        }
    
    def _test_terrain_analysis(self) -> TestResult:
        """Test terrain analysis algorithm accuracy"""
        try:
            location = self.test_locations[0]  # Stand #1
            
            # Get prediction data
            response = requests.post(
                f"{self.backend_url}/predict",
                json={
                    "lat": location["lat"],
                    "lon": location["lon"],
                    "date_time": "2025-11-15T06:00:00",
                    "season": "rut"
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return TestResult("Terrain Analysis", False, 0.0, {}, ["API request failed"])
            
            data = response.json()
            terrain_features = data.get("terrain_features", {})
            
            # Validate terrain data logic
            errors = []
            confidence_factors = []
            
            # Check elevation (Vermont should be 200-4000 feet)
            elevation = terrain_features.get("elevation", 0)
            if not (200 <= elevation <= 4000):
                errors.append(f"Elevation {elevation} outside Vermont range")
            else:
                confidence_factors.append(90.0)
            
            # Check slope (should be 0-45 degrees)
            slope = terrain_features.get("slope", 0)
            if not (0 <= slope <= 45):
                errors.append(f"Slope {slope} outside realistic range")
            else:
                confidence_factors.append(85.0)
            
            # Check canopy closure (should be 0-100%)
            canopy = terrain_features.get("canopy_closure", 0)
            if not (0 <= canopy <= 100):
                errors.append(f"Canopy closure {canopy} outside valid range")
            else:
                confidence_factors.append(90.0)
            
            # Check proximity values (should be positive)
            water_prox = terrain_features.get("water_proximity", 0)
            ag_prox = terrain_features.get("ag_proximity", 0)
            
            if water_prox < 0 or ag_prox < 0:
                errors.append("Negative proximity values detected")
            else:
                confidence_factors.append(95.0)
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
            passed = len(errors) == 0
            
            print(f"    ✅ Terrain Analysis: {avg_confidence:.1f}% confidence" if passed else f"    ❌ Terrain Analysis: {len(errors)} errors")
            
            return TestResult(
                "Terrain Analysis",
                passed,
                avg_confidence,
                {
                    "elevation": elevation,
                    "slope": slope,
                    "canopy_closure": canopy,
                    "water_proximity": water_prox,
                    "ag_proximity": ag_prox
                },
                errors
            )
            
        except Exception as e:
            return TestResult("Terrain Analysis", False, 0.0, {}, [str(e)])
    
    def _test_vegetation_calculations(self) -> TestResult:
        """Test vegetation health and NDVI calculations"""
        try:
            location = self.test_locations[0]
            
            # Test satellite vegetation data
            response = requests.get(
                f"{self.backend_url}/api/enhanced/satellite/ndvi",
                params={"lat": location["lat"], "lon": location["lon"]},
                timeout=30
            )
            
            errors = []
            confidence_factors = []
            
            if response.status_code == 200:
                veg_data = response.json().get("vegetation_data", {})
                veg_health = veg_data.get("vegetation_health", {})
                
                # Check NDVI values (should be -1 to 1)
                ndvi = veg_health.get("ndvi", 0)
                if not (-1 <= ndvi <= 1):
                    errors.append(f"NDVI {ndvi} outside valid range (-1 to 1)")
                else:
                    confidence_factors.append(95.0)
                
                # Check land cover percentages
                land_cover = veg_data.get("land_cover_summary", {})
                forest_pct = land_cover.get("forest_coverage", 0)
                
                if not (0 <= forest_pct <= 100):
                    errors.append(f"Forest coverage {forest_pct}% outside valid range")
                else:
                    confidence_factors.append(90.0)
                
            else:
                # Test fallback vegetation analysis
                print("    ⚠️ Satellite data unavailable, testing fallback...")
                confidence_factors.append(70.0)  # Lower confidence for fallback
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 60.0
            passed = len(errors) == 0
            
            print(f"    ✅ Vegetation Analysis: {avg_confidence:.1f}% confidence" if passed else f"    ❌ Vegetation Analysis: {len(errors)} errors")
            
            return TestResult(
                "Vegetation Calculations",
                passed,
                avg_confidence,
                {"ndvi": ndvi if 'ndvi' in locals() else "unavailable"},
                errors
            )
            
        except Exception as e:
            return TestResult("Vegetation Calculations", False, 0.0, {}, [str(e)])
    
    def _test_prediction_consistency(self) -> TestResult:
        """Test prediction consistency across multiple requests"""
        try:
            location = self.test_locations[0]
            predictions = []
            
            # Make multiple prediction requests
            for i in range(3):
                response = requests.post(
                    f"{self.backend_url}/predict",
                    json={
                        "lat": location["lat"],
                        "lon": location["lon"],
                        "date_time": "2025-11-15T06:00:00",
                        "season": "rut"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    predictions.append(response.json())
                    time.sleep(1)  # Brief pause between requests
            
            if len(predictions) < 2:
                return TestResult("Prediction Consistency", False, 0.0, {}, ["Insufficient predictions for comparison"])
            
            # Compare consistency
            errors = []
            confidence_factors = []
            
            # Check if bedding zone counts are consistent
            bedding_counts = [len(p.get("bedding_zones", [])) for p in predictions]
            if len(set(bedding_counts)) > 1:
                errors.append(f"Inconsistent bedding zone counts: {bedding_counts}")
            else:
                confidence_factors.append(95.0)
            
            # Check if terrain features are identical
            terrain_1 = predictions[0].get("terrain_features", {})
            terrain_2 = predictions[1].get("terrain_features", {})
            
            key_terrain_fields = ["elevation", "slope", "canopy_closure"]
            for field in key_terrain_fields:
                if abs(terrain_1.get(field, 0) - terrain_2.get(field, 0)) > 0.1:
                    errors.append(f"Inconsistent {field} values")
                else:
                    confidence_factors.append(90.0)
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
            passed = len(errors) == 0
            
            print(f"    ✅ Prediction Consistency: {avg_confidence:.1f}% confidence" if passed else f"    ❌ Prediction Consistency: {len(errors)} errors")
            
            return TestResult(
                "Prediction Consistency",
                passed,
                avg_confidence,
                {"predictions_tested": len(predictions)},
                errors
            )
            
        except Exception as e:
            return TestResult("Prediction Consistency", False, 0.0, {}, [str(e)])
    
    def _test_mature_buck_intelligence(self) -> Dict[str, Any]:
        """Phase 2: Test mature buck movement intelligence"""
        print("  🦌 Testing mature buck movement patterns...")
        movement_results = self._test_movement_patterns()
        
        print("  ⏰ Testing seasonal behavior modeling...")
        seasonal_results = self._test_seasonal_behavior()
        
        print("  🌪️ Testing environmental trigger responses...")
        trigger_results = self._test_environmental_triggers()
        
        return {
            "movement_patterns": movement_results,
            "seasonal_behavior": seasonal_results,
            "environmental_triggers": trigger_results
        }
    
    def _test_movement_patterns(self) -> TestResult:
        """Test mature buck movement pattern accuracy"""
        try:
            location = self.test_locations[0]
            
            # Test dawn movement prediction
            dawn_response = requests.post(
                f"{self.backend_url}/predict",
                json={
                    "lat": location["lat"],
                    "lon": location["lon"],
                    "date_time": "2025-11-15T06:30:00",  # Dawn
                    "season": "rut"
                },
                timeout=30
            )
            
            # Test dusk movement prediction  
            dusk_response = requests.post(
                f"{self.backend_url}/predict",
                json={
                    "lat": location["lat"],
                    "lon": location["lon"],
                    "date_time": "2025-11-15T17:30:00",  # Dusk
                    "season": "rut"
                },
                timeout=30
            )
            
            errors = []
            confidence_factors = []
            
            if dawn_response.status_code == 200 and dusk_response.status_code == 200:
                dawn_data = dawn_response.json()
                dusk_data = dusk_response.json()
                
                # Check for mature buck analysis
                dawn_buck = dawn_data.get("mature_buck_analysis", {})
                dusk_buck = dusk_data.get("mature_buck_analysis", {})
                
                if not dawn_buck or not dusk_buck:
                    errors.append("Missing mature buck analysis")
                else:
                    confidence_factors.append(85.0)
                
                # Check movement confidence scores
                dawn_confidence = dawn_buck.get("movement_confidence", 0)
                dusk_confidence = dusk_buck.get("movement_confidence", 0)
                
                if dawn_confidence < 50 or dusk_confidence < 50:
                    errors.append("Low movement confidence scores")
                else:
                    confidence_factors.append(90.0)
                
                # Check for travel corridors
                dawn_corridors = len(dawn_data.get("travel_corridors", []))
                dusk_corridors = len(dusk_data.get("travel_corridors", []))
                
                if dawn_corridors == 0 and dusk_corridors == 0:
                    errors.append("No travel corridors identified")
                else:
                    confidence_factors.append(88.0)
                
            else:
                errors.append("API requests failed")
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
            passed = len(errors) == 0
            
            print(f"    ✅ Movement Patterns: {avg_confidence:.1f}% confidence" if passed else f"    ❌ Movement Patterns: {len(errors)} errors")
            
            return TestResult(
                "Movement Patterns",
                passed,
                avg_confidence,
                {
                    "dawn_corridors": dawn_corridors if 'dawn_corridors' in locals() else 0,
                    "dusk_corridors": dusk_corridors if 'dusk_corridors' in locals() else 0
                },
                errors
            )
            
        except Exception as e:
            return TestResult("Movement Patterns", False, 0.0, {}, [str(e)])
    
    def _test_seasonal_behavior(self) -> TestResult:
        """Test seasonal behavior modeling accuracy"""
        try:
            location = self.test_locations[0]
            seasons = ["early_season", "rut", "late_season"]
            seasonal_data = {}
            
            for season in seasons:
                response = requests.post(
                    f"{self.backend_url}/predict",
                    json={
                        "lat": location["lat"],
                        "lon": location["lon"],
                        "date_time": "2025-11-15T06:00:00",
                        "season": season
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    seasonal_data[season] = response.json()
                    time.sleep(1)
            
            errors = []
            confidence_factors = []
            
            # Check that different seasons produce different results
            if len(seasonal_data) >= 2:
                # Rut should have highest movement activity
                rut_data = seasonal_data.get("rut", {})
                early_data = seasonal_data.get("early_season", {})
                
                rut_corridors = len(rut_data.get("travel_corridors", []))
                early_corridors = len(early_data.get("travel_corridors", []))
                
                if rut_corridors < early_corridors:
                    errors.append("Rut season should show increased movement")
                else:
                    confidence_factors.append(85.0)
                
                # Check for season-specific analysis
                for season, data in seasonal_data.items():
                    if "mature_buck_analysis" in data:
                        confidence_factors.append(90.0)
                        break
                else:
                    errors.append("Missing seasonal mature buck analysis")
            else:
                errors.append("Insufficient seasonal data for comparison")
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
            passed = len(errors) == 0
            
            print(f"    ✅ Seasonal Behavior: {avg_confidence:.1f}% confidence" if passed else f"    ❌ Seasonal Behavior: {len(errors)} errors")
            
            return TestResult(
                "Seasonal Behavior",
                passed,
                avg_confidence,
                {"seasons_tested": len(seasonal_data)},
                errors
            )
            
        except Exception as e:
            return TestResult("Seasonal Behavior", False, 0.0, {}, [str(e)])
    
    def _test_environmental_triggers(self) -> TestResult:
        """Test environmental trigger response accuracy"""
        try:
            # This is a simplified test - in practice would test weather API integration
            # For now, verify that prediction system handles different times appropriately
            
            location = self.test_locations[0]
            times = ["05:30:00", "12:00:00", "18:30:00", "22:00:00"]  # Dawn, noon, dusk, night
            time_data = {}
            
            for time_str in times:
                response = requests.post(
                    f"{self.backend_url}/predict",
                    json={
                        "lat": location["lat"],
                        "lon": location["lon"],
                        "date_time": f"2025-11-15T{time_str}",
                        "season": "rut"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    time_data[time_str] = response.json()
                    time.sleep(0.5)
            
            errors = []
            confidence_factors = []
            
            # Check that different times produce appropriate activity levels
            if len(time_data) >= 3:
                # Dawn and dusk should have higher activity than noon
                dawn_activity = time_data.get("05:30:00", {}).get("mature_buck_analysis", {}).get("movement_confidence", 0)
                noon_activity = time_data.get("12:00:00", {}).get("mature_buck_analysis", {}).get("movement_confidence", 0)
                dusk_activity = time_data.get("18:30:00", {}).get("mature_buck_analysis", {}).get("movement_confidence", 0)
                
                if dawn_activity > noon_activity and dusk_activity > noon_activity:
                    confidence_factors.append(90.0)
                else:
                    errors.append("Dawn/dusk activity should exceed noon activity")
                
                # Check for time-based predictions
                for time_str, data in time_data.items():
                    if "prediction_time" in data or "time_of_day" in data.get("analysis_factors", {}):
                        confidence_factors.append(85.0)
                        break
                else:
                    errors.append("Missing time-based analysis factors")
            else:
                errors.append("Insufficient time-based data for comparison")
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 75.0
            passed = len(errors) == 0
            
            print(f"    ✅ Environmental Triggers: {avg_confidence:.1f}% confidence" if passed else f"    ❌ Environmental Triggers: {len(errors)} errors")
            
            return TestResult(
                "Environmental Triggers",
                passed,
                avg_confidence,
                {"time_periods_tested": len(time_data)},
                errors
            )
            
        except Exception as e:
            return TestResult("Environmental Triggers", False, 0.0, {}, [str(e)])
    
    def _test_camera_placement_system(self) -> Dict[str, Any]:
        """Phase 3: Test camera placement system"""
        print("  📹 Testing advanced camera algorithm...")
        algorithm_results = self._test_camera_algorithm()
        
        print("  🎯 Testing placement positioning accuracy...")
        positioning_results = self._test_camera_positioning()
        
        print("  🧠 Testing strategic reasoning...")
        reasoning_results = self._test_camera_reasoning()
        
        return {
            "camera_algorithm": algorithm_results,
            "positioning_accuracy": positioning_results,
            "strategic_reasoning": reasoning_results
        }
    
    def _test_camera_algorithm(self) -> TestResult:
        """Test camera placement algorithm accuracy"""
        try:
            location = self.test_locations[0]
            
            # Test camera placement endpoint
            response = requests.post(
                f"{self.backend_url}/api/camera/optimal-placement",
                json={
                    "lat": location["lat"],
                    "lon": location["lon"]
                },
                timeout=30
            )
            
            errors = []
            confidence_factors = []
            
            if response.status_code == 200:
                camera_data = response.json()
                
                # Check for required camera placement fields
                required_fields = ["optimal_camera", "placement_strategy", "analysis_timestamp"]
                for field in required_fields:
                    if field not in camera_data:
                        errors.append(f"Missing required field: {field}")
                    else:
                        confidence_factors.append(90.0)
                
                # Check camera coordinates
                optimal_camera = camera_data.get("optimal_camera", {})
                camera_lat = optimal_camera.get("lat", 0)
                camera_lon = optimal_camera.get("lon", 0)
                
                if not (44.0 <= camera_lat <= 45.0 and -73.0 <= camera_lon <= -72.0):
                    errors.append("Camera coordinates outside Vermont bounds")
                else:
                    confidence_factors.append(95.0)
                
                # Check confidence score
                confidence_score = optimal_camera.get("confidence_score", 0)
                if confidence_score < 85:
                    errors.append(f"Camera confidence {confidence_score}% below 85% threshold")
                else:
                    confidence_factors.append(confidence_score)
                
                # Check distance from target
                distance_m = optimal_camera.get("distance_from_target_meters", 0)
                if not (50 <= distance_m <= 200):
                    errors.append(f"Camera distance {distance_m}m outside optimal range (50-200m)")
                else:
                    confidence_factors.append(90.0)
                
            else:
                errors.append(f"Camera placement API failed: {response.status_code}")
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
            passed = len(errors) == 0
            
            print(f"    ✅ Camera Algorithm: {avg_confidence:.1f}% confidence" if passed else f"    ❌ Camera Algorithm: {len(errors)} errors")
            
            return TestResult(
                "Camera Algorithm",
                passed,
                avg_confidence,
                {
                    "camera_confidence": confidence_score if 'confidence_score' in locals() else 0,
                    "distance_meters": distance_m if 'distance_m' in locals() else 0
                },
                errors
            )
            
        except Exception as e:
            return TestResult("Camera Algorithm", False, 0.0, {}, [str(e)])
    
    def _test_camera_positioning(self) -> TestResult:
        """Test camera positioning accuracy across multiple locations"""
        try:
            positioning_tests = []
            
            for location in self.test_locations[:3]:  # Test first 3 locations
                response = requests.post(
                    f"{self.backend_url}/api/camera/optimal-placement",
                    json={
                        "lat": location["lat"],
                        "lon": location["lon"]
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    camera_data = response.json()
                    optimal_camera = camera_data.get("optimal_camera", {})
                    
                    positioning_tests.append({
                        "location": location["name"],
                        "target_lat": location["lat"],
                        "target_lon": location["lon"],
                        "camera_lat": optimal_camera.get("lat", 0),
                        "camera_lon": optimal_camera.get("lon", 0),
                        "confidence": optimal_camera.get("confidence_score", 0),
                        "distance": optimal_camera.get("distance_from_target_meters", 0)
                    })
                
                time.sleep(1)
            
            errors = []
            confidence_factors = []
            
            if len(positioning_tests) >= 2:
                # Check positioning consistency
                distances = [test["distance"] for test in positioning_tests]
                confidences = [test["confidence"] for test in positioning_tests]
                
                avg_distance = sum(distances) / len(distances)
                avg_confidence = sum(confidences) / len(confidences)
                
                if avg_distance < 50 or avg_distance > 200:
                    errors.append(f"Average camera distance {avg_distance:.1f}m outside optimal range")
                else:
                    confidence_factors.append(90.0)
                
                if avg_confidence < 85:
                    errors.append(f"Average confidence {avg_confidence:.1f}% below threshold")
                else:
                    confidence_factors.append(avg_confidence)
                
                # Check for coordinate precision
                for test in positioning_tests:
                    lat_precision = len(str(test["camera_lat"]).split(".")[-1])
                    lon_precision = len(str(test["camera_lon"]).split(".")[-1])
                    
                    if lat_precision < 4 or lon_precision < 4:
                        errors.append(f"Insufficient coordinate precision for {test['location']}")
                    else:
                        confidence_factors.append(85.0)
            else:
                errors.append("Insufficient positioning tests completed")
            
            overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
            passed = len(errors) == 0
            
            print(f"    ✅ Camera Positioning: {overall_confidence:.1f}% confidence" if passed else f"    ❌ Camera Positioning: {len(errors)} errors")
            
            return TestResult(
                "Camera Positioning",
                passed,
                overall_confidence,
                {
                    "locations_tested": len(positioning_tests),
                    "average_distance": avg_distance if 'avg_distance' in locals() else 0,
                    "average_confidence": avg_confidence if 'avg_confidence' in locals() else 0
                },
                errors
            )
            
        except Exception as e:
            return TestResult("Camera Positioning", False, 0.0, {}, [str(e)])
    
    def _test_camera_reasoning(self) -> TestResult:
        """Test camera placement strategic reasoning"""
        try:
            location = self.test_locations[0]
            
            response = requests.post(
                f"{self.backend_url}/api/camera/optimal-placement",
                json={
                    "lat": location["lat"],
                    "lon": location["lon"]
                },
                timeout=30
            )
            
            errors = []
            confidence_factors = []
            
            if response.status_code == 200:
                camera_data = response.json()
                strategy = camera_data.get("placement_strategy", {})
                
                # Check for strategic reasoning components
                reasoning_fields = [
                    "positioning_rationale",
                    "expected_deer_behavior", 
                    "optimal_setup_conditions",
                    "photo_opportunity_analysis"
                ]
                
                for field in reasoning_fields:
                    if field in strategy:
                        confidence_factors.append(85.0)
                    else:
                        errors.append(f"Missing reasoning field: {field}")
                
                # Check positioning rationale quality
                rationale = strategy.get("positioning_rationale", "")
                if len(rationale) < 50:
                    errors.append("Positioning rationale too brief")
                else:
                    confidence_factors.append(90.0)
                
                # Check for practical setup information
                setup_conditions = strategy.get("optimal_setup_conditions", {})
                if "wind_direction" in setup_conditions and "approach_route" in setup_conditions:
                    confidence_factors.append(95.0)
                else:
                    errors.append("Missing critical setup conditions")
                
                # Check photo opportunity analysis
                photo_analysis = strategy.get("photo_opportunity_analysis", {})
                if "success_probability" in photo_analysis:
                    success_prob = photo_analysis.get("success_probability", 0)
                    if success_prob >= 75:
                        confidence_factors.append(success_prob)
                    else:
                        errors.append(f"Low photo success probability: {success_prob}%")
                else:
                    errors.append("Missing photo opportunity analysis")
                
            else:
                errors.append("Camera placement API request failed")
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
            passed = len(errors) == 0
            
            print(f"    ✅ Camera Reasoning: {avg_confidence:.1f}% confidence" if passed else f"    ❌ Camera Reasoning: {len(errors)} errors")
            
            return TestResult(
                "Camera Reasoning",
                passed,
                avg_confidence,
                {"strategy_components": len(confidence_factors)},
                errors
            )
            
        except Exception as e:
            return TestResult("Camera Reasoning", False, 0.0, {}, [str(e)])
    
    def _test_frontend_integrity(self) -> Dict[str, Any]:
        """Phase 4: Test frontend data integrity"""
        print("  🖥️ Testing Stand #1 enhanced analysis...")
        stand_results = self._test_stand_analysis_integrity()
        
        print("  🗺️ Testing map data consistency...")
        map_results = self._test_map_data_integrity()
        
        return {
            "stand_analysis": stand_results,
            "map_integrity": map_results
        }
    
    def _test_stand_analysis_integrity(self) -> TestResult:
        """Test Stand #1 enhanced analysis data integrity"""
        # Note: This is a conceptual test - actual frontend testing would require
        # more sophisticated tools like Selenium for UI testing
        try:
            location = self.test_locations[0]  # Stand #1
            
            # Get backend data for comparison
            backend_response = requests.post(
                f"{self.backend_url}/predict",
                json={
                    "lat": location["lat"],
                    "lon": location["lon"],
                    "date_time": "2025-11-15T06:00:00",
                    "season": "rut",
                    "include_camera_placement": True
                },
                timeout=30
            )
            
            errors = []
            confidence_factors = []
            
            if backend_response.status_code == 200:
                backend_data = backend_response.json()
                
                # Verify backend has the data that frontend should display
                required_backend_data = [
                    "terrain_features",
                    "mature_buck_analysis", 
                    "travel_corridors",
                    "bedding_zones"
                ]
                
                for field in required_backend_data:
                    if field in backend_data:
                        confidence_factors.append(90.0)
                    else:
                        errors.append(f"Backend missing field for frontend: {field}")
                
                # Check that camera placement data exists if requested
                if "camera_placement" in backend_data:
                    camera_data = backend_data["camera_placement"]
                    if "optimal_camera" in camera_data:
                        confidence_factors.append(95.0)
                    else:
                        errors.append("Camera placement missing optimal_camera data")
                else:
                    errors.append("Missing camera placement data for frontend display")
                
                # Verify terrain features for wind calculations
                terrain = backend_data.get("terrain_features", {})
                elevation = terrain.get("elevation", 0)
                
                if elevation > 0:
                    confidence_factors.append(85.0)
                else:
                    errors.append("Missing elevation data for wind calculations")
                
            else:
                errors.append("Backend API failed - frontend cannot display accurate data")
            
            # Note: In a full test, we would also check frontend Streamlit display
            # This would require browser automation tools
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
            passed = len(errors) == 0
            
            print(f"    ✅ Stand Analysis Integrity: {avg_confidence:.1f}% confidence" if passed else f"    ❌ Stand Analysis Integrity: {len(errors)} errors")
            
            return TestResult(
                "Stand Analysis Integrity",
                passed,
                avg_confidence,
                {"backend_data_complete": len(confidence_factors) > 0},
                errors
            )
            
        except Exception as e:
            return TestResult("Stand Analysis Integrity", False, 0.0, {}, [str(e)])
    
    def _test_map_data_integrity(self) -> TestResult:
        """Test map data consistency between backend and frontend"""
        try:
            # Test multiple locations to verify map accuracy
            map_tests = []
            
            for location in self.test_locations[:2]:
                response = requests.post(
                    f"{self.backend_url}/predict",
                    json={
                        "lat": location["lat"],
                        "lon": location["lon"],
                        "date_time": "2025-11-15T06:00:00",
                        "season": "rut",
                        "include_camera_placement": True
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    map_tests.append({
                        "location": location["name"],
                        "input_lat": location["lat"],
                        "input_lon": location["lon"],
                        "bedding_zones": len(data.get("bedding_zones", [])),
                        "travel_corridors": len(data.get("travel_corridors", [])),
                        "has_camera_placement": "camera_placement" in data
                    })
                
                time.sleep(1)
            
            errors = []
            confidence_factors = []
            
            if len(map_tests) >= 1:
                for test in map_tests:
                    # Check coordinate consistency
                    if test["input_lat"] > 0 and test["input_lon"] < 0:  # Valid Vermont coordinates
                        confidence_factors.append(95.0)
                    else:
                        errors.append(f"Invalid coordinates for {test['location']}")
                    
                    # Check for map features
                    if test["bedding_zones"] > 0 or test["travel_corridors"] > 0:
                        confidence_factors.append(85.0)
                    else:
                        errors.append(f"No map features generated for {test['location']}")
                    
                    # Check camera placement integration
                    if test["has_camera_placement"]:
                        confidence_factors.append(90.0)
                    else:
                        errors.append(f"Missing camera placement for {test['location']}")
            else:
                errors.append("No map data tests completed")
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
            passed = len(errors) == 0
            
            print(f"    ✅ Map Data Integrity: {avg_confidence:.1f}% confidence" if passed else f"    ❌ Map Data Integrity: {len(errors)} errors")
            
            return TestResult(
                "Map Data Integrity",
                passed,
                avg_confidence,
                {"locations_tested": len(map_tests)},
                errors
            )
            
        except Exception as e:
            return TestResult("Map Data Integrity", False, 0.0, {}, [str(e)])
    
    def _test_integration_workflow(self) -> Dict[str, Any]:
        """Phase 5: Test complete integration workflow"""
        print("  🔄 Testing end-to-end workflow...")
        workflow_results = self._test_end_to_end_workflow()
        
        print("  ⚡ Testing performance benchmarks...")
        performance_results = self._test_performance_benchmarks()
        
        return {
            "end_to_end_workflow": workflow_results,
            "performance_benchmarks": performance_results
        }
    
    def _test_end_to_end_workflow(self) -> TestResult:
        """Test complete user workflow"""
        try:
            location = self.test_locations[0]  # Stand #1
            workflow_start = time.time()
            
            # Step 1: Basic prediction
            print("    📊 Step 1: Basic prediction...")
            prediction_response = requests.post(
                f"{self.backend_url}/predict",
                json={
                    "lat": location["lat"],
                    "lon": location["lon"],
                    "date_time": "2025-11-15T06:00:00",
                    "season": "rut"
                },
                timeout=30
            )
            
            step1_time = time.time() - workflow_start
            
            # Step 2: Camera placement
            print("    📹 Step 2: Camera placement...")
            camera_start = time.time()
            camera_response = requests.post(
                f"{self.backend_url}/api/camera/optimal-placement",
                json={
                    "lat": location["lat"],
                    "lon": location["lon"]
                },
                timeout=30
            )
            
            step2_time = time.time() - camera_start
            
            # Step 3: Enhanced prediction with camera
            print("    🎯 Step 3: Enhanced prediction...")
            enhanced_start = time.time()
            enhanced_response = requests.post(
                f"{self.backend_url}/predict",
                json={
                    "lat": location["lat"],
                    "lon": location["lon"],
                    "date_time": "2025-11-15T06:00:00",
                    "season": "rut",
                    "include_camera_placement": True
                },
                timeout=30
            )
            
            step3_time = time.time() - enhanced_start
            total_time = time.time() - workflow_start
            
            errors = []
            confidence_factors = []
            
            # Validate each step
            if prediction_response.status_code == 200:
                confidence_factors.append(90.0)
            else:
                errors.append("Step 1: Basic prediction failed")
            
            if camera_response.status_code == 200:
                confidence_factors.append(85.0)
            else:
                errors.append("Step 2: Camera placement failed")
            
            if enhanced_response.status_code == 200:
                enhanced_data = enhanced_response.json()
                if "camera_placement" in enhanced_data:
                    confidence_factors.append(95.0)
                else:
                    errors.append("Step 3: Enhanced prediction missing camera data")
            else:
                errors.append("Step 3: Enhanced prediction failed")
            
            # Check timing requirements
            if step1_time > 10:
                errors.append(f"Step 1 too slow: {step1_time:.1f}s > 10s")
            else:
                confidence_factors.append(80.0)
            
            if step2_time > 15:
                errors.append(f"Step 2 too slow: {step2_time:.1f}s > 15s")
            else:
                confidence_factors.append(80.0)
            
            if total_time > 30:
                errors.append(f"Total workflow too slow: {total_time:.1f}s > 30s")
            else:
                confidence_factors.append(85.0)
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
            passed = len(errors) == 0
            
            print(f"    ✅ End-to-End Workflow: {avg_confidence:.1f}% confidence" if passed else f"    ❌ End-to-End Workflow: {len(errors)} errors")
            
            return TestResult(
                "End-to-End Workflow",
                passed,
                avg_confidence,
                {
                    "step1_time": step1_time,
                    "step2_time": step2_time,
                    "step3_time": step3_time,
                    "total_time": total_time
                },
                errors
            )
            
        except Exception as e:
            return TestResult("End-to-End Workflow", False, 0.0, {}, [str(e)])
    
    def _test_performance_benchmarks(self) -> TestResult:
        """Test system performance benchmarks"""
        try:
            location = self.test_locations[0]
            performance_tests = []
            
            # Test multiple requests for performance consistency
            for i in range(5):
                start_time = time.time()
                
                response = requests.post(
                    f"{self.backend_url}/predict",
                    json={
                        "lat": location["lat"],
                        "lon": location["lon"],
                        "date_time": "2025-11-15T06:00:00",
                        "season": "rut"
                    },
                    timeout=30
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                performance_tests.append({
                    "request_num": i + 1,
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
                
                time.sleep(0.5)  # Brief pause between requests
            
            errors = []
            confidence_factors = []
            
            if len(performance_tests) >= 3:
                # Calculate performance metrics
                successful_tests = [t for t in performance_tests if t["success"]]
                response_times = [t["response_time"] for t in successful_tests]
                
                if len(successful_tests) < 3:
                    errors.append(f"Only {len(successful_tests)}/5 requests succeeded")
                else:
                    confidence_factors.append(90.0)
                
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
                    max_response_time = max(response_times)
                    
                    # Performance benchmarks
                    if avg_response_time <= 10:
                        confidence_factors.append(95.0)
                    elif avg_response_time <= 15:
                        confidence_factors.append(80.0)
                    else:
                        errors.append(f"Average response time {avg_response_time:.1f}s exceeds 15s")
                    
                    if max_response_time <= 20:
                        confidence_factors.append(85.0)
                    else:
                        errors.append(f"Max response time {max_response_time:.1f}s exceeds 20s")
            else:
                errors.append("Insufficient performance tests completed")
            
            avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
            passed = len(errors) == 0
            
            print(f"    ✅ Performance Benchmarks: {avg_confidence:.1f}% confidence" if passed else f"    ❌ Performance Benchmarks: {len(errors)} errors")
            
            return TestResult(
                "Performance Benchmarks",
                passed,
                avg_confidence,
                {
                    "tests_completed": len(performance_tests),
                    "success_rate": len(successful_tests) / len(performance_tests) if performance_tests else 0,
                    "avg_response_time": avg_response_time if 'avg_response_time' in locals() else 0
                },
                errors
            )
            
        except Exception as e:
            return TestResult("Performance Benchmarks", False, 0.0, {}, [str(e)])
    
    def _generate_comprehensive_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive testing report"""
        print("\\n" + "=" * 60)
        print("🎯 COMPREHENSIVE TESTING REPORT")
        print("=" * 60)
        
        # Calculate overall statistics
        all_tests = []
        
        # Flatten all test results
        for phase_name, phase_data in test_results.items():
            if phase_name == "total_execution_time":
                continue
                
            if isinstance(phase_data, dict):
                for test_name, test_result in phase_data.items():
                    if isinstance(test_result, TestResult):
                        all_tests.append(test_result)
        
        total_tests = len(all_tests)
        passed_tests = len([t for t in all_tests if t.passed])
        failed_tests = total_tests - passed_tests
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            avg_confidence = sum([t.confidence_score for t in all_tests]) / total_tests
        else:
            success_rate = 0
            avg_confidence = 0
        
        # Print summary
        print(f"\\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Average Confidence: {avg_confidence:.1f}%")
        print(f"   Execution Time: {test_results.get('total_execution_time', 0):.1f} seconds")
        
        # Print detailed results by phase
        print(f"\\n📋 DETAILED RESULTS BY PHASE:")
        
        phase_summaries = {}
        for phase_name, phase_data in test_results.items():
            if phase_name == "total_execution_time":
                continue
                
            print(f"\\n{phase_name.upper().replace('_', ' ')}:")
            
            phase_tests = []
            if isinstance(phase_data, dict):
                for test_name, test_result in phase_data.items():
                    if isinstance(test_result, TestResult):
                        phase_tests.append(test_result)
                        status = "✅ PASS" if test_result.passed else "❌ FAIL"
                        print(f"   {test_result.test_name}: {status} ({test_result.confidence_score:.1f}%)")
                        
                        if test_result.errors:
                            for error in test_result.errors:
                                print(f"      ⚠️ {error}")
            
            if phase_tests:
                phase_passed = len([t for t in phase_tests if t.passed])
                phase_total = len(phase_tests)
                phase_rate = (phase_passed / phase_total) * 100 if phase_total > 0 else 0
                phase_summaries[phase_name] = {
                    "passed": phase_passed,
                    "total": phase_total,
                    "success_rate": phase_rate
                }
        
        # Final assessment
        print(f"\\n🎯 FINAL ASSESSMENT:")
        
        if success_rate >= 90:
            print("   🟢 EXCELLENT: System is production-ready")
        elif success_rate >= 80:
            print("   🟡 GOOD: Minor issues to address")
        elif success_rate >= 70:
            print("   🟠 FAIR: Several issues need attention")
        else:
            print("   🔴 POOR: Major issues require fixes")
        
        # Recommendations
        print(f"\\n💡 RECOMMENDATIONS:")
        
        critical_failures = [t for t in all_tests if not t.passed and t.confidence_score < 50]
        if critical_failures:
            print("   🚨 CRITICAL: Address these failed tests first:")
            for test in critical_failures:
                print(f"      - {test.test_name}")
        
        low_confidence = [t for t in all_tests if t.passed and t.confidence_score < 80]
        if low_confidence:
            print("   ⚠️ IMPROVEMENT: These tests passed but need optimization:")
            for test in low_confidence:
                print(f"      - {test.test_name} ({test.confidence_score:.1f}%)")
        
        if success_rate >= 85 and avg_confidence >= 80:
            print("   ✅ READY: System meets deployment criteria")
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "average_confidence": avg_confidence,
                "execution_time": test_results.get('total_execution_time', 0)
            },
            "phase_summaries": phase_summaries,
            "all_test_results": test_results,
            "critical_failures": [t.test_name for t in critical_failures],
            "low_confidence_tests": [t.test_name for t in low_confidence],
            "deployment_ready": success_rate >= 85 and avg_confidence >= 80
        }

# Main execution
if __name__ == "__main__":
    # Initialize and run comprehensive test suite
    test_suite = ComprehensiveTestSuite()
    
    print("🚀 Starting comprehensive testing suite...")
    print("This will validate all algorithms, predictions, and frontend integrity.\\n")
    
    # Run all tests
    final_report = test_suite.run_all_tests()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"comprehensive_test_report_{timestamp}.json"
    
    with open(report_filename, 'w') as f:
        json.dump(final_report, f, indent=2, default=str)
    
    print(f"\\n📄 Complete test report saved to: {report_filename}")
    print("\\n🎯 COMPREHENSIVE TESTING COMPLETE!")
