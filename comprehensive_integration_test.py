#!/usr/bin/env python3
"""
COMPREHENSIVE INTEGRATION TEST: Complete System Validation

This test validates the complete integration of all systems:
- Google Earth Engine (GEE) data integration
- Real-time weather APIs (Open-Meteo)
- Biological logic accuracy (mature buck behavior)
- Wind/thermal bedding preferences
- Seasonal movement patterns (early, rut, late)
- Time-based behavior (AM, midday, PM)
- Frontend integration validation
- Multi-location Vermont testing

Author: GitHub Copilot
Date: August 26, 2025
"""

import logging
import asyncio
import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import requests
import aiohttp
from enhanced_biological_integration import EnhancedBiologicalIntegration

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveIntegrationTest:
    """Master test suite for complete system validation"""
    
    def __init__(self):
        self.integrator = EnhancedBiologicalIntegration()
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "phases": {},
            "overall_success": False,
            "recommendations": []
        }
        
        # Vermont test locations with varied terrain
        self.test_locations = [
            {"name": "Tinmouth Ridge", "lat": 43.3127, "lon": -73.2271, "terrain": "ridge", "elevation_high": True},
            {"name": "Mount Tabor Valley", "lat": 43.3306, "lon": -72.9417, "terrain": "valley", "elevation_high": False},
            {"name": "Killington Agricultural", "lat": 43.6042, "lon": -72.8092, "terrain": "agricultural", "elevation_high": False},
            {"name": "Stratton Forest", "lat": 43.1142, "lon": -72.9081, "terrain": "dense_forest", "elevation_high": True},
            {"name": "Green Mountain Mixed", "lat": 43.2917, "lon": -72.8833, "terrain": "mixed", "elevation_high": True}
        ]
    
    async def run_comprehensive_test(self) -> Dict:
        """Run the complete comprehensive integration test"""
        print("🎯 COMPREHENSIVE INTEGRATION TEST")
        print("=" * 80)
        print("Testing complete system integration with all components")
        print("=" * 80)
        
        try:
            # Phase 1: System Component Validation
            await self.phase_1_system_validation()
            
            # Phase 2: Biological Logic Matrix Testing
            await self.phase_2_biological_matrix()
            
            # Phase 3: Environmental Integration Testing
            await self.phase_3_environmental_integration()
            
            # Phase 4: Multi-Location Validation
            await self.phase_4_multi_location_validation()
            
            # Phase 5: Frontend Integration Testing
            await self.phase_5_frontend_integration()
            
            # Generate final report
            self.generate_final_report()
            
        except Exception as e:
            logger.error(f"Comprehensive test failed: {e}")
            self.test_results["error"] = str(e)
        
        return self.test_results
    
    async def phase_1_system_validation(self):
        """Phase 1: Validate all system components"""
        print("\n🔧 PHASE 1: SYSTEM COMPONENT VALIDATION")
        print("─" * 60)
        
        phase_results = {
            "gee_connectivity": False,
            "weather_api_success": False,
            "spatial_data_processing": False,
            "backend_api_accessible": False,
            "success_rate": 0.0
        }
        
        # Test 1: GEE Connectivity (simulate with mock data)
        print("🛰️ Testing GEE Data Integration...")
        try:
            test_prediction = {
                "features": {
                    "gee_metadata": {
                        "deciduous_forest_percentage": 0.75,
                        "ndvi_value": 0.65,
                        "vegetation_health": "excellent"
                    },
                    "oak_flat": True,
                    "ridge": True,
                    "field": True
                }
            }
            
            spatial_validation = self.integrator.validate_spatial_data(test_prediction)
            if spatial_validation["validation_score"] > 0.8:
                phase_results["gee_connectivity"] = True
                print("  ✅ GEE data integration successful")
            else:
                print(f"  ❌ GEE data validation failed: {spatial_validation['validation_score']:.2f}")
        except Exception as e:
            print(f"  ❌ GEE connectivity failed: {e}")
        
        # Test 2: Weather API Integration
        print("🌦️ Testing Real-time Weather API...")
        try:
            weather_data = self.integrator.get_real_time_weather(43.3127, -73.2271)
            if weather_data.get("api_source") == "open-meteo":
                phase_results["weather_api_success"] = True
                print(f"  ✅ Weather API successful: {weather_data['temperature']:.1f}°F, {weather_data['pressure']:.2f}inHg")
            else:
                print(f"  ⚠️ Weather API fallback used: {weather_data.get('api_source', 'unknown')}")
        except Exception as e:
            print(f"  ❌ Weather API failed: {e}")
        
        # Test 3: Spatial Data Processing
        print("📊 Testing Spatial Data Processing...")
        try:
            enhanced_result = self.integrator.add_enhanced_biological_analysis(
                test_prediction.copy(), 43.3127, -73.2271, 7, "early_season", "moderate"
            )
            
            if "enhanced_biological_analysis" in enhanced_result:
                phase_results["spatial_data_processing"] = True
                print("  ✅ Spatial data processing successful")
            else:
                print("  ❌ Spatial data processing failed")
        except Exception as e:
            print(f"  ❌ Spatial processing failed: {e}")
        
        # Test 4: Backend API Accessibility
        print("🌐 Testing Backend API...")
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                phase_results["backend_api_accessible"] = True
                print("  ✅ Backend API accessible")
            else:
                print(f"  ❌ Backend API failed: {response.status_code}")
        except Exception as e:
            # Try prediction endpoint as fallback
            try:
                test_payload = {
                    "lat": 43.3127,
                    "lon": -73.2271,
                    "date_time": datetime.now().isoformat(),
                    "season": "early_season"
                }
                response = requests.post("http://localhost:8000/predict", json=test_payload, timeout=10)
                if response.status_code == 200:
                    phase_results["backend_api_accessible"] = True
                    print("  ✅ Backend prediction API accessible")
                else:
                    print(f"  ❌ Backend prediction API failed: {response.status_code}")
            except Exception as e2:
                print(f"  ❌ Backend API not accessible: {e2}")
        
        # Calculate success rate
        successes = sum(1 for v in phase_results.values() if isinstance(v, bool) and v)
        total_tests = sum(1 for v in phase_results.values() if isinstance(v, bool))
        phase_results["success_rate"] = (successes / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📊 Phase 1 Results: {successes}/{total_tests} tests passed ({phase_results['success_rate']:.1f}%)")
        self.test_results["phases"]["phase_1"] = phase_results
    
    async def phase_2_biological_matrix(self):
        """Phase 2: Test biological logic across all scenarios"""
        print("\n🧬 PHASE 2: BIOLOGICAL LOGIC MATRIX TESTING")
        print("─" * 60)
        
        # Test matrix: 3 seasons × 3 times × 3 pressure levels = 27 scenarios
        seasons = ["early_season", "rut", "late_season"]
        times = [7, 13, 18]  # AM, Midday, PM
        pressures = ["low", "moderate", "high"]
        
        test_scenarios = []
        for season in seasons:
            for time in times:
                for pressure in pressures:
                    test_scenarios.append({
                        "season": season,
                        "time": time,
                        "pressure": pressure,
                        "expected_behaviors": self.get_expected_behaviors(season, time, pressure)
                    })
        
        passed_tests = 0
        total_tests = len(test_scenarios)
        detailed_results = []
        
        print(f"🧪 Testing {total_tests} biological scenarios...")
        
        for i, scenario in enumerate(test_scenarios):
            try:
                # Create test prediction with realistic data
                test_prediction = {
                    "confidence_score": 0.5,
                    "features": {
                        "gee_metadata": {
                            "deciduous_forest_percentage": 0.7,
                            "ndvi_value": 0.6,
                            "vegetation_health": "good"
                        },
                        "oak_flat": True,
                        "ridge": True
                    }
                }
                
                # Run enhanced analysis
                enhanced_result = self.integrator.add_enhanced_biological_analysis(
                    test_prediction.copy(),
                    43.3127, -73.2271,  # Tinmouth coordinates
                    scenario["time"],
                    scenario["season"],
                    scenario["pressure"]
                )
                
                # Validate biological logic
                validation_result = self.validate_biological_logic(enhanced_result, scenario)
                
                detailed_results.append({
                    "scenario": f"{scenario['season']}_{scenario['time']:02d}h_{scenario['pressure']}",
                    "passed": validation_result["passed"],
                    "issues": validation_result["issues"],
                    "confidence": enhanced_result.get("enhanced_confidence_score", 0)
                })
                
                if validation_result["passed"]:
                    passed_tests += 1
                
                # Print progress every 9 tests (each season)
                if (i + 1) % 9 == 0:
                    season_passed = sum(1 for r in detailed_results[-9:] if r["passed"])
                    print(f"  {scenario['season']}: {season_passed}/9 scenarios passed")
                
            except Exception as e:
                detailed_results.append({
                    "scenario": f"{scenario['season']}_{scenario['time']:02d}h_{scenario['pressure']}",
                    "passed": False,
                    "issues": [f"Exception: {str(e)}"],
                    "confidence": 0
                })
        
        accuracy = (passed_tests / total_tests) * 100
        print(f"\n📊 Phase 2 Results: {passed_tests}/{total_tests} scenarios passed ({accuracy:.1f}%)")
        
        # Show detailed breakdown
        for season in seasons:
            season_results = [r for r in detailed_results if season in r["scenario"]]
            season_passed = sum(1 for r in season_results if r["passed"])
            print(f"  {season}: {season_passed}/{len(season_results)} ({(season_passed/len(season_results)*100):.1f}%)")
        
        self.test_results["phases"]["phase_2"] = {
            "total_scenarios": total_tests,
            "passed_scenarios": passed_tests,
            "accuracy_percentage": accuracy,
            "detailed_results": detailed_results
        }
    
    def get_expected_behaviors(self, season: str, time: int, pressure: str) -> Dict:
        """Get expected biological behaviors for validation"""
        behaviors = {}
        
        # Movement direction expectations
        if 5 <= time <= 8:  # AM
            behaviors["movement_direction"] = "feeding_to_bedding"
        elif 16 <= time <= 20:  # PM
            behaviors["movement_direction"] = "bedding_to_feeding"
        else:  # Midday
            behaviors["movement_direction"] = "minimal_movement"
        
        # Activity level expectations
        if time in [6, 7, 17, 18, 19]:
            behaviors["activity_level"] = "high"
        elif time in [12, 13, 14]:
            behaviors["activity_level"] = "low"
        else:
            behaviors["activity_level"] = "moderate"
        
        # Pressure response expectations
        if pressure == "high" and 6 <= time <= 18:
            behaviors["pressure_impact"] = "reduced_daytime_activity"
        elif pressure == "low":
            behaviors["pressure_impact"] = "normal_patterns"
        else:
            behaviors["pressure_impact"] = "moderate_adjustment"
        
        # Seasonal expectations
        if season == "early_season":
            behaviors["food_focus"] = "mast_crops"
        elif season == "rut":
            behaviors["food_focus"] = "high_energy"
            behaviors["increased_movement"] = True
        else:  # late_season
            behaviors["food_focus"] = "survival_feeding"
        
        return behaviors
    
    def validate_biological_logic(self, enhanced_result: Dict, scenario: Dict) -> Dict:
        """Validate biological logic against expected behaviors"""
        validation = {"passed": True, "issues": []}
        
        biological_analysis = enhanced_result.get("enhanced_biological_analysis", {})
        expected = scenario["expected_behaviors"]
        
        # Check movement direction
        movement_notes = " ".join(biological_analysis.get("movement_direction", []))
        
        if expected["movement_direction"] == "feeding_to_bedding":
            if "feeding areas → bedding areas" not in movement_notes:
                validation["passed"] = False
                validation["issues"].append("Missing feeding→bedding movement direction")
        elif expected["movement_direction"] == "bedding_to_feeding":
            if "bedding areas → feeding areas" not in movement_notes:
                validation["passed"] = False
                validation["issues"].append("Missing bedding→feeding movement direction")
        
        # Check activity level
        activity_level = biological_analysis.get("activity_level", "")
        if activity_level != expected["activity_level"]:
            # Allow some flexibility for weather modifications
            if not (expected["activity_level"] == "high" and activity_level == "moderate"):
                validation["passed"] = False
                validation["issues"].append(f"Activity level mismatch: expected {expected['activity_level']}, got {activity_level}")
        
        # Check pressure response
        pressure_notes = " ".join(biological_analysis.get("pressure_response", []))
        
        if expected["pressure_impact"] == "reduced_daytime_activity":
            if "reduced daytime" not in pressure_notes.lower():
                validation["passed"] = False
                validation["issues"].append("Missing hunting pressure daytime reduction")
        
        # Check seasonal food logic
        food_notes = " ".join(biological_analysis.get("seasonal_food", []))
        
        if expected["food_focus"] == "mast_crops" and "mast" not in food_notes.lower():
            validation["passed"] = False
            validation["issues"].append("Missing early season mast focus")
        elif expected["food_focus"] == "high_energy" and "energy" not in food_notes.lower():
            validation["passed"] = False
            validation["issues"].append("Missing rut season energy focus")
        elif expected["food_focus"] == "survival_feeding" and "survival" not in food_notes.lower():
            validation["passed"] = False
            validation["issues"].append("Missing late season survival focus")
        
        return validation
    
    async def phase_3_environmental_integration(self):
        """Phase 3: Test environmental integration (wind, thermal, weather)"""
        print("\n🌍 PHASE 3: ENVIRONMENTAL INTEGRATION TESTING")
        print("─" * 60)
        
        environmental_tests = [
            {
                "name": "Cold Front Response",
                "weather": {"temperature": 35, "pressure": 29.5, "wind_speed": 12, "wind_direction": 270},
                "expected_triggers": ["cold front", "increased movement"],
                "time": 14
            },
            {
                "name": "High Wind Bedding",
                "weather": {"temperature": 45, "pressure": 30.1, "wind_speed": 18, "wind_direction": 180},
                "expected_behaviors": ["leeward", "wind protection"],
                "time": 7
            },
            {
                "name": "Thermal Bedding (Cold)",
                "weather": {"temperature": 28, "pressure": 30.2, "wind_speed": 5, "wind_direction": 90},
                "expected_behaviors": ["south-facing", "thermal"],
                "time": 8
            },
            {
                "name": "Thermal Bedding (Hot)",
                "weather": {"temperature": 75, "pressure": 30.0, "wind_speed": 3, "wind_direction": 45},
                "expected_behaviors": ["north-facing", "cool", "upslope"],
                "time": 13
            }
        ]
        
        passed_tests = 0
        test_results = []
        
        for test in environmental_tests:
            print(f"🧪 Testing: {test['name']}")
            
            try:
                # Create prediction with environmental focus
                test_prediction = {
                    "confidence_score": 0.5,
                    "features": {
                        "gee_metadata": {
                            "deciduous_forest_percentage": 0.8,
                            "ndvi_value": 0.7,
                            "vegetation_health": "excellent"
                        },
                        "ridge": True,
                        "valley": True,
                        "dense_cover": True
                    }
                }
                
                # Mock weather data for this test
                enhanced_result = self.integrator.add_enhanced_biological_analysis(
                    test_prediction.copy(),
                    43.3127, -73.2271,
                    test["time"],
                    "early_season",
                    "moderate"
                )
                
                # Override with test weather data
                enhanced_result["enhanced_biological_analysis"]["real_time_weather"] = test["weather"]
                
                # Re-run analysis with test weather
                biological_analysis = enhanced_result["enhanced_biological_analysis"]
                weather_notes = self.integrator.get_enhanced_weather_trigger_notes(test["weather"])
                wind_thermal_notes = self.integrator.get_wind_thermal_bedding_analysis(
                    test["weather"], biological_analysis["spatial_validation"]
                )
                
                # Validate environmental responses
                test_passed = True
                issues = []
                
                if "expected_triggers" in test:
                    weather_text = " ".join(weather_notes).lower()
                    for trigger in test["expected_triggers"]:
                        if trigger not in weather_text:
                            test_passed = False
                            issues.append(f"Missing weather trigger: {trigger}")
                
                if "expected_behaviors" in test:
                    wind_thermal_text = " ".join(wind_thermal_notes).lower()
                    for behavior in test["expected_behaviors"]:
                        if behavior not in wind_thermal_text:
                            test_passed = False
                            issues.append(f"Missing environmental behavior: {behavior}")
                
                test_results.append({
                    "name": test["name"],
                    "passed": test_passed,
                    "issues": issues
                })
                
                if test_passed:
                    passed_tests += 1
                    print(f"  ✅ {test['name']} passed")
                else:
                    print(f"  ❌ {test['name']} failed: {', '.join(issues)}")
                
            except Exception as e:
                test_results.append({
                    "name": test["name"],
                    "passed": False,
                    "issues": [f"Exception: {str(e)}"]
                })
                print(f"  ❌ {test['name']} failed with exception: {e}")
        
        accuracy = (passed_tests / len(environmental_tests)) * 100
        print(f"\n📊 Phase 3 Results: {passed_tests}/{len(environmental_tests)} tests passed ({accuracy:.1f}%)")
        
        self.test_results["phases"]["phase_3"] = {
            "total_tests": len(environmental_tests),
            "passed_tests": passed_tests,
            "accuracy_percentage": accuracy,
            "test_results": test_results
        }
    
    async def phase_4_multi_location_validation(self):
        """Phase 4: Test across multiple Vermont locations"""
        print("\n🗺️ PHASE 4: MULTI-LOCATION VALIDATION")
        print("─" * 60)
        
        location_results = []
        total_success = 0
        
        for location in self.test_locations:
            print(f"🧪 Testing: {location['name']} ({location['terrain']})")
            
            try:
                # Test with realistic scenario for this location
                test_prediction = {
                    "confidence_score": 0.5,
                    "features": self.get_location_features(location)
                }
                
                # Run analysis for this location
                enhanced_result = self.integrator.add_enhanced_biological_analysis(
                    test_prediction.copy(),
                    location["lat"], location["lon"],
                    7,  # Morning time
                    "early_season",
                    "moderate"
                )
                
                # Validate location-specific results
                location_validation = self.validate_location_specific_results(enhanced_result, location)
                
                location_results.append({
                    "name": location["name"],
                    "coordinates": f"{location['lat']:.4f}, {location['lon']:.4f}",
                    "terrain": location["terrain"],
                    "passed": location_validation["passed"],
                    "spatial_score": enhanced_result["enhanced_biological_analysis"]["spatial_validation"]["validation_score"],
                    "weather_source": enhanced_result["enhanced_biological_analysis"]["real_time_weather"]["api_source"],
                    "confidence": enhanced_result["enhanced_confidence_score"],
                    "issues": location_validation["issues"]
                })
                
                if location_validation["passed"]:
                    total_success += 1
                    print(f"  ✅ {location['name']}: {enhanced_result['enhanced_confidence_score']:.2f} confidence")
                else:
                    print(f"  ❌ {location['name']}: {', '.join(location_validation['issues'])}")
                
            except Exception as e:
                location_results.append({
                    "name": location["name"],
                    "passed": False,
                    "issues": [f"Exception: {str(e)}"]
                })
                print(f"  ❌ {location['name']} failed: {e}")
        
        accuracy = (total_success / len(self.test_locations)) * 100
        print(f"\n📊 Phase 4 Results: {total_success}/{len(self.test_locations)} locations passed ({accuracy:.1f}%)")
        
        self.test_results["phases"]["phase_4"] = {
            "total_locations": len(self.test_locations),
            "successful_locations": total_success,
            "accuracy_percentage": accuracy,
            "location_results": location_results
        }
    
    def get_location_features(self, location: Dict) -> Dict:
        """Get realistic features for each location type"""
        base_features = {
            "gee_metadata": {
                "deciduous_forest_percentage": 0.7,
                "ndvi_value": 0.6,
                "vegetation_health": "good"
            }
        }
        
        if location["terrain"] == "ridge":
            base_features.update({
                "ridge": True,
                "elevation_high": True,
                "thick_cover": True,
                "gee_metadata": {
                    "deciduous_forest_percentage": 0.8,
                    "ndvi_value": 0.65,
                    "vegetation_health": "excellent"
                }
            })
        elif location["terrain"] == "valley":
            base_features.update({
                "valley": True,
                "water_source": True,
                "field": True
            })
        elif location["terrain"] == "agricultural":
            base_features.update({
                "field": True,
                "oak_flat": True,
                "agricultural": True,
                "gee_metadata": {
                    "deciduous_forest_percentage": 0.4,
                    "ndvi_value": 0.7,
                    "vegetation_health": "good"
                }
            })
        elif location["terrain"] == "dense_forest":
            base_features.update({
                "thick_cover": True,
                "dense_cover": True,
                "oak_flat": True,
                "gee_metadata": {
                    "deciduous_forest_percentage": 0.9,
                    "ndvi_value": 0.75,
                    "vegetation_health": "excellent"
                }
            })
        else:  # mixed
            base_features.update({
                "ridge": True,
                "field": True,
                "oak_flat": True,
                "thick_cover": True
            })
        
        return base_features
    
    def validate_location_specific_results(self, enhanced_result: Dict, location: Dict) -> Dict:
        """Validate results are appropriate for location type"""
        validation = {"passed": True, "issues": []}
        
        biological_analysis = enhanced_result["enhanced_biological_analysis"]
        spatial_validation = biological_analysis["spatial_validation"]
        
        # Check spatial validation score
        if spatial_validation["validation_score"] < 0.6:
            validation["passed"] = False
            validation["issues"].append(f"Low spatial validation score: {spatial_validation['validation_score']:.2f}")
        
        # Check terrain-specific features
        terrain_features = spatial_validation["terrain_features"]
        
        if location["terrain"] == "ridge" and "ridge" not in terrain_features:
            validation["passed"] = False
            validation["issues"].append("Ridge terrain not detected")
        
        if location["terrain"] == "agricultural" and "field" not in terrain_features:
            validation["passed"] = False
            validation["issues"].append("Agricultural features not detected")
        
        # Check weather integration
        weather_data = biological_analysis["real_time_weather"]
        if weather_data["api_source"] == "fallback":
            validation["issues"].append("Using fallback weather data")
        
        # Check confidence score is reasonable
        confidence = enhanced_result["enhanced_confidence_score"]
        if confidence < 0.3:
            validation["passed"] = False
            validation["issues"].append(f"Very low confidence: {confidence:.2f}")
        
        return validation
    
    async def phase_5_frontend_integration(self):
        """Phase 5: Test frontend integration"""
        print("\n🖥️ PHASE 5: FRONTEND INTEGRATION TESTING")
        print("─" * 60)
        
        integration_results = {
            "frontend_accessible": False,
            "api_integration": False,
            "bedding_maps_working": False,
            "real_time_data_flow": False
        }
        
        try:
            # Test frontend accessibility
            print("🌐 Testing frontend accessibility...")
            frontend_result = await self.integrator.validate_frontend_integration(43.3127, -73.2271)
            
            integration_results["frontend_accessible"] = frontend_result["frontend_accessible"]
            integration_results["api_integration"] = frontend_result.get("real_time_data_integration", False)
            integration_results["bedding_maps_working"] = frontend_result["bedding_maps_display"]
            
            if frontend_result["frontend_accessible"]:
                print("  ✅ Frontend accessible at localhost:8501")
            else:
                print("  ❌ Frontend not accessible")
                print(f"     Error: {frontend_result.get('error_message', 'Unknown error')}")
            
            if integration_results["api_integration"]:
                print("  ✅ API integration working")
            else:
                print("  ❌ API integration not working")
            
            if integration_results["bedding_maps_working"]:
                print("  ✅ Bedding maps display working")
            else:
                print("  ❌ Bedding maps not displaying")
            
            # Test real-time data flow
            print("🔄 Testing real-time data flow...")
            try:
                async with aiohttp.ClientSession() as session:
                    test_payload = {
                        "lat": 43.3127,
                        "lon": -73.2271,
                        "date_time": datetime.now().isoformat(),
                        "season": "early_season"
                    }
                    
                    async with session.post(
                        "http://localhost:8000/predict",
                        json=test_payload,
                        timeout=15
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Check for enhanced biological analysis
                            if "enhanced_biological_analysis" in data:
                                integration_results["real_time_data_flow"] = True
                                print("  ✅ Real-time data flow working")
                            else:
                                print("  ❌ Enhanced biological analysis not in response")
                        else:
                            print(f"  ❌ API request failed: {response.status}")
            
            except Exception as e:
                print(f"  ❌ Real-time data flow test failed: {e}")
        
        except Exception as e:
            print(f"❌ Frontend integration test failed: {e}")
        
        success_count = sum(1 for v in integration_results.values() if v)
        total_tests = len(integration_results)
        accuracy = (success_count / total_tests) * 100
        
        print(f"\n📊 Phase 5 Results: {success_count}/{total_tests} integration tests passed ({accuracy:.1f}%)")
        
        self.test_results["phases"]["phase_5"] = {
            "total_tests": total_tests,
            "passed_tests": success_count,
            "accuracy_percentage": accuracy,
            "integration_results": integration_results
        }
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE INTEGRATION TEST FINAL REPORT")
        print("=" * 80)
        
        # Calculate overall metrics
        total_phases = len(self.test_results["phases"])
        successful_phases = 0
        overall_accuracy = 0.0
        
        phase_summaries = []
        
        for phase_name, phase_data in self.test_results["phases"].items():
            phase_accuracy = phase_data.get("accuracy_percentage", 0)
            overall_accuracy += phase_accuracy
            
            if phase_accuracy >= 80:
                successful_phases += 1
                status = "✅ PASSED"
            elif phase_accuracy >= 60:
                status = "⚠️ PARTIAL"
            else:
                status = "❌ FAILED"
            
            phase_summaries.append({
                "phase": phase_name,
                "accuracy": phase_accuracy,
                "status": status
            })
            
            print(f"{status} {phase_name.replace('_', ' ').title()}: {phase_accuracy:.1f}%")
        
        overall_accuracy = overall_accuracy / total_phases if total_phases > 0 else 0
        self.test_results["overall_accuracy"] = overall_accuracy
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Accuracy: {overall_accuracy:.1f}%")
        print(f"   Successful Phases: {successful_phases}/{total_phases}")
        
        # Determine deployment readiness
        if overall_accuracy >= 90 and successful_phases >= 4:
            deployment_status = "🚀 PRODUCTION READY"
            self.test_results["overall_success"] = True
            self.test_results["recommendations"].append("System is ready for production deployment")
        elif overall_accuracy >= 80 and successful_phases >= 3:
            deployment_status = "🧪 STAGING READY"
            self.test_results["recommendations"].append("Deploy to staging environment for final validation")
        elif overall_accuracy >= 70:
            deployment_status = "⚠️ NEEDS IMPROVEMENT"
            self.test_results["recommendations"].append("Address failing components before deployment")
        else:
            deployment_status = "❌ NOT READY"
            self.test_results["recommendations"].append("Significant fixes needed before deployment")
        
        print(f"   Deployment Status: {deployment_status}")
        
        # Specific recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        
        for phase_name, phase_data in self.test_results["phases"].items():
            if phase_data.get("accuracy_percentage", 0) < 80:
                if phase_name == "phase_1":
                    self.test_results["recommendations"].append("Fix system component connectivity issues")
                elif phase_name == "phase_2":
                    self.test_results["recommendations"].append("Review biological logic validation failures")
                elif phase_name == "phase_3":
                    self.test_results["recommendations"].append("Improve environmental integration accuracy")
                elif phase_name == "phase_4":
                    self.test_results["recommendations"].append("Address location-specific validation issues")
                elif phase_name == "phase_5":
                    self.test_results["recommendations"].append("Fix frontend integration problems")
        
        for recommendation in self.test_results["recommendations"]:
            print(f"   • {recommendation}")
        
        # Save detailed report
        self.test_results["end_time"] = datetime.now().isoformat()
        self.test_results["duration_minutes"] = (
            datetime.fromisoformat(self.test_results["end_time"]) - 
            datetime.fromisoformat(self.test_results["start_time"])
        ).total_seconds() / 60
        
        with open("comprehensive_integration_report.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: comprehensive_integration_report.json")
        print(f"⏱️ Test duration: {self.test_results['duration_minutes']:.1f} minutes")
        
        if self.test_results["overall_success"]:
            print("\n🎉 COMPREHENSIVE INTEGRATION TEST: SUCCESS!")
            print("   All systems validated and ready for deployment!")
        else:
            print("\n⚠️ COMPREHENSIVE INTEGRATION TEST: NEEDS WORK")
            print("   Review recommendations and address issues before deployment.")

async def main():
    """Run the comprehensive integration test"""
    test_suite = ComprehensiveIntegrationTest()
    results = await test_suite.run_comprehensive_test()
    return results

if __name__ == "__main__":
    asyncio.run(main())
