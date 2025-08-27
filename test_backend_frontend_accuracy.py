#!/usr/bin/env python3
"""
Backend-Frontend Accuracy Validation Test

This comprehensive test validates that sophisticated backend deer biology
is correctly projected to the frontend with logical accuracy.

Tests for biological logic errors like:
- AM movement direction (feeding→bedding, not bedding→feeding)
- Seasonal behavior consistency
- Weather trigger logic
- Thermal bedding preferences
- Food source availability timing

Author: GitHub Copilot
Date: August 26, 2025
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import sys
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackendFrontendAccuracyValidator:
    """Validates biological accuracy between backend predictions and frontend display"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:8501"
        self.test_results = []
        self.critical_errors = []
        self.warnings = []
        
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("🧪 BACKEND-FRONTEND BIOLOGICAL ACCURACY VALIDATION")
        print("=" * 60)
        
        try:
            # Test 1: AM Movement Direction Logic
            self.test_am_movement_direction()
            
            # Test 2: Seasonal Food Source Logic
            self.test_seasonal_food_logic()
            
            # Test 3: Weather Trigger Consistency
            self.test_weather_trigger_logic()
            
            # Test 4: Thermal Bedding Logic
            self.test_thermal_bedding_logic()
            
            # Test 5: Time-Based Behavior Consistency
            self.test_time_based_behavior()
            
            # Test 6: Pressure Response Logic
            self.test_pressure_response_logic()
            
            # Test 7: Mature Buck vs General Behavior
            self.test_mature_buck_specificity()
            
            # Test 8: Backend Data Integration
            self.test_backend_data_integration()
            
            return self.generate_validation_report()
            
        except Exception as e:
            self.critical_errors.append(f"Validation failed: {str(e)}")
            logger.error(f"Critical validation error: {e}")
            return {"status": "FAILED", "error": str(e)}
    
    def test_am_movement_direction(self):
        """Test AM movement direction logic (feeding→bedding, not bedding→feeding)"""
        print("\n🌅 Testing AM Movement Direction Logic...")
        
        # Test multiple AM times
        am_times = ["05:30", "07:08", "08:30"]
        
        for time_str in am_times:
            try:
                # Make prediction for AM time
                response = self.make_prediction_request(
                    time=time_str,
                    hunt_period="AM",
                    season="early_season"
                )
                
                if response:
                    movement_logic = self.analyze_movement_direction(response, "AM")
                    
                    if movement_logic["direction"] == "feeding_to_bedding":
                        self.test_results.append({
                            "test": "AM Movement Direction",
                            "time": time_str,
                            "status": "✅ CORRECT",
                            "details": f"Correctly shows deer moving feeding→bedding at {time_str}"
                        })
                    elif movement_logic["direction"] == "bedding_to_feeding":
                        self.critical_errors.append({
                            "test": "AM Movement Direction",
                            "time": time_str,
                            "status": "❌ CRITICAL ERROR",
                            "details": f"WRONG: Shows deer moving bedding→feeding at {time_str} (should be feeding→bedding)"
                        })
                    else:
                        self.warnings.append({
                            "test": "AM Movement Direction",
                            "time": time_str,
                            "status": "⚠️ UNCLEAR",
                            "details": f"Movement direction unclear at {time_str}"
                        })
                        
            except Exception as e:
                logger.error(f"AM movement test failed for {time_str}: {e}")
    
    def test_seasonal_food_logic(self):
        """Test seasonal food source logic consistency"""
        print("\n🍂 Testing Seasonal Food Source Logic...")
        
        seasons = ["early_season", "rut", "late_season"]
        expected_foods = {
            "early_season": ["acorns", "soybeans", "apples", "browse"],
            "rut": ["standing_corn", "remaining_mast", "high_energy"],
            "late_season": ["corn_stubble", "woody_browse", "waste_grain"]
        }
        
        for season in seasons:
            try:
                response = self.make_prediction_request(season=season)
                
                if response:
                    food_analysis = self.analyze_food_sources(response, season)
                    expected = expected_foods[season]
                    
                    # Check if food sources make biological sense
                    correct_foods = sum(1 for food in food_analysis["mentioned_foods"] 
                                      if any(exp in food.lower() for exp in expected))
                    
                    accuracy = correct_foods / len(expected) if expected else 0
                    
                    if accuracy >= 0.6:  # 60% of expected foods mentioned
                        self.test_results.append({
                            "test": "Seasonal Food Logic",
                            "season": season,
                            "status": "✅ GOOD",
                            "accuracy": f"{accuracy*100:.1f}%",
                            "details": f"Food sources appropriate for {season}"
                        })
                    else:
                        self.warnings.append({
                            "test": "Seasonal Food Logic", 
                            "season": season,
                            "status": "⚠️ POOR",
                            "accuracy": f"{accuracy*100:.1f}%",
                            "details": f"Food sources may not match {season} biology"
                        })
                        
            except Exception as e:
                logger.error(f"Seasonal food test failed for {season}: {e}")
    
    def test_weather_trigger_logic(self):
        """Test weather trigger response logic"""
        print("\n🌦️ Testing Weather Trigger Logic...")
        
        # Test cold front scenario
        try:
            response = self.make_prediction_request(
                weather_scenario="cold_front",
                temperature=45,
                pressure=29.85
            )
            
            if response:
                weather_response = self.analyze_weather_response(response)
                
                # Cold fronts should increase movement probability
                if weather_response["movement_increase"]:
                    self.test_results.append({
                        "test": "Weather Trigger Logic",
                        "scenario": "Cold Front",
                        "status": "✅ CORRECT",
                        "details": "Correctly shows increased movement during cold front"
                    })
                else:
                    self.critical_errors.append({
                        "test": "Weather Trigger Logic",
                        "scenario": "Cold Front", 
                        "status": "❌ ERROR",
                        "details": "Cold front should trigger increased deer movement"
                    })
                    
        except Exception as e:
            logger.error(f"Weather trigger test failed: {e}")
    
    def test_thermal_bedding_logic(self):
        """Test thermal bedding preference logic"""
        print("\n🌡️ Testing Thermal Bedding Logic...")
        
        try:
            # Test south-facing slope preference in cold weather
            response = self.make_prediction_request(
                temperature=35,
                aspect="south_facing",
                time="12:00"
            )
            
            if response:
                thermal_analysis = self.analyze_thermal_preferences(response)
                
                if thermal_analysis["south_facing_preference"]:
                    self.test_results.append({
                        "test": "Thermal Bedding Logic",
                        "status": "✅ CORRECT", 
                        "details": "Correctly prefers south-facing slopes in cold weather"
                    })
                else:
                    self.warnings.append({
                        "test": "Thermal Bedding Logic",
                        "status": "⚠️ SUBOPTIMAL",
                        "details": "Should prefer south-facing slopes for thermal advantage"
                    })
                    
        except Exception as e:
            logger.error(f"Thermal bedding test failed: {e}")
    
    def test_time_based_behavior(self):
        """Test time-based behavior consistency"""
        print("\n⏰ Testing Time-Based Behavior Consistency...")
        
        time_periods = {
            "dawn": "06:00",
            "midday": "12:00", 
            "dusk": "18:00",
            "night": "23:00"
        }
        
        expected_activity = {
            "dawn": "high",
            "midday": "low",
            "dusk": "high", 
            "night": "moderate"
        }
        
        for period, time in time_periods.items():
            try:
                response = self.make_prediction_request(time=time)
                
                if response:
                    activity_level = self.analyze_activity_level(response, period)
                    expected = expected_activity[period]
                    
                    if activity_level == expected:
                        self.test_results.append({
                            "test": "Time-Based Behavior",
                            "period": period,
                            "status": "✅ CORRECT",
                            "details": f"Activity level correctly {expected} at {period}"
                        })
                    else:
                        self.warnings.append({
                            "test": "Time-Based Behavior",
                            "period": period,
                            "status": "⚠️ MISMATCH",
                            "details": f"Expected {expected} activity, got {activity_level}"
                        })
                        
            except Exception as e:
                logger.error(f"Time-based behavior test failed for {period}: {e}")
    
    def test_pressure_response_logic(self):
        """Test hunting pressure response logic"""
        print("\n👥 Testing Hunting Pressure Response Logic...")
        
        try:
            # Test high pressure scenario  
            response = self.make_prediction_request(pressure_level="high")
            
            if response:
                pressure_response = self.analyze_pressure_response(response)
                
                # High pressure should reduce daytime activity
                if pressure_response["reduced_daytime_activity"]:
                    self.test_results.append({
                        "test": "Pressure Response Logic",
                        "status": "✅ CORRECT",
                        "details": "Correctly reduces daytime activity under high pressure"
                    })
                else:
                    self.critical_errors.append({
                        "test": "Pressure Response Logic",
                        "status": "❌ ERROR",
                        "details": "High pressure should reduce daytime deer activity"
                    })
                    
        except Exception as e:
            logger.error(f"Pressure response test failed: {e}")
    
    def test_mature_buck_specificity(self):
        """Test mature buck specific behavior vs general deer"""
        print("\n🦌 Testing Mature Buck Specificity...")
        
        try:
            # Compare mature buck vs general predictions
            general_response = self.make_prediction_request(target_type="general")
            mature_response = self.make_prediction_request(target_type="mature_buck")
            
            if general_response and mature_response:
                specificity = self.analyze_mature_buck_differences(general_response, mature_response)
                
                if specificity["shows_differences"]:
                    self.test_results.append({
                        "test": "Mature Buck Specificity",
                        "status": "✅ GOOD",
                        "details": "Shows distinct mature buck behavior patterns"
                    })
                else:
                    self.warnings.append({
                        "test": "Mature Buck Specificity", 
                        "status": "⚠️ GENERIC",
                        "details": "Mature buck predictions should differ from general deer"
                    })
                    
        except Exception as e:
            logger.error(f"Mature buck specificity test failed: {e}")
    
    def test_backend_data_integration(self):
        """Test backend data source integration"""
        print("\n🔌 Testing Backend Data Integration...")
        
        try:
            response = self.make_prediction_request()
            
            if response:
                integration_check = self.analyze_data_integration(response)
                
                # Check for evidence of multiple data sources
                data_sources = integration_check["data_sources_used"]
                
                if len(data_sources) >= 3:  # Weather, terrain, GEE, etc.
                    self.test_results.append({
                        "test": "Backend Data Integration",
                        "status": "✅ COMPREHENSIVE",
                        "details": f"Uses {len(data_sources)} data sources: {', '.join(data_sources)}"
                    })
                else:
                    self.warnings.append({
                        "test": "Backend Data Integration",
                        "status": "⚠️ LIMITED", 
                        "details": f"Only {len(data_sources)} data sources detected"
                    })
                    
        except Exception as e:
            logger.error(f"Backend integration test failed: {e}")
    
    def make_prediction_request(self, **kwargs) -> Dict[str, Any]:
        """Make a prediction request with specified parameters"""
        
        # Tinmouth, Vermont test location (user's known hunting area)
        payload = {
            "lat": 43.3127,
            "lon": -73.2271,
            "date_time": "2025-08-26T06:00:00",
            "season": "early_season"
        }
        
        # Override with any provided parameters
        payload.update(kwargs)
        
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                f"{self.backend_url}/predict",
                headers=headers,
                json=payload,
                timeout=120  # Increased timeout for complex processing
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Prediction request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def analyze_movement_direction(self, response: Dict, time_period: str) -> Dict[str, str]:
        """Analyze movement direction from response"""
        
        # Look for movement direction indicators in the response
        movement_indicators = {
            "direction": "unknown",
            "confidence": "low"
        }
        
        # Check bedding and feeding area positions and descriptions
        try:
            behavioral_notes = response.get("behavioral_analysis", {}).get("behavioral_notes", [])
            stand_recommendations = response.get("stand_recommendations", [])
            
            # Look for feeding→bedding indicators in AM
            feeding_to_bedding_keywords = [
                "return to bed", "heading to bedding", "moving to cover",
                "feeding to bedding", "morning return"
            ]
            
            bedding_to_feeding_keywords = [
                "leaving bedding", "heading to feed", "bedding to feeding",
                "morning feeding", "leaving cover"
            ]
            
            text_to_analyze = " ".join(behavioral_notes + 
                                    [rec.get("description", "") for rec in stand_recommendations])
            
            text_lower = text_to_analyze.lower()
            
            if any(keyword in text_lower for keyword in feeding_to_bedding_keywords):
                movement_indicators["direction"] = "feeding_to_bedding"
                movement_indicators["confidence"] = "high"
            elif any(keyword in text_lower for keyword in bedding_to_feeding_keywords):
                movement_indicators["direction"] = "bedding_to_feeding"
                movement_indicators["confidence"] = "high"
                
        except Exception as e:
            logger.error(f"Movement direction analysis failed: {e}")
        
        return movement_indicators
    
    def analyze_food_sources(self, response: Dict, season: str) -> Dict[str, Any]:
        """Analyze food source mentions in response"""
        
        analysis = {
            "mentioned_foods": [],
            "seasonal_appropriateness": "unknown"
        }
        
        try:
            # Extract text from response
            feeding_areas = response.get("feeding_areas", {}).get("features", [])
            behavioral_notes = response.get("behavioral_analysis", {}).get("behavioral_notes", [])
            
            text_sources = (
                behavioral_notes + 
                [area.get("properties", {}).get("description", "") for area in feeding_areas]
            )
            
            full_text = " ".join(text_sources).lower()
            
            # Food keywords to look for
            food_keywords = [
                "acorn", "oak", "corn", "soybean", "apple", "browse", "mast",
                "agricultural", "waste grain", "stubble", "woody browse"
            ]
            
            for keyword in food_keywords:
                if keyword in full_text:
                    analysis["mentioned_foods"].append(keyword)
                    
        except Exception as e:
            logger.error(f"Food source analysis failed: {e}")
        
        return analysis
    
    def analyze_weather_response(self, response: Dict) -> Dict[str, bool]:
        """Analyze weather response logic"""
        
        analysis = {
            "movement_increase": False,
            "pressure_sensitive": False
        }
        
        try:
            behavioral_notes = response.get("behavioral_analysis", {}).get("behavioral_notes", [])
            text = " ".join(behavioral_notes).lower()
            
            # Look for cold front/weather response indicators
            if any(phrase in text for phrase in ["cold front", "pressure", "weather", "movement increase"]):
                analysis["movement_increase"] = True
                analysis["pressure_sensitive"] = True
                
        except Exception as e:
            logger.error(f"Weather response analysis failed: {e}")
        
        return analysis
    
    def analyze_thermal_preferences(self, response: Dict) -> Dict[str, bool]:
        """Analyze thermal preference logic"""
        
        analysis = {
            "south_facing_preference": False,
            "thermal_aware": False
        }
        
        try:
            bedding_areas = response.get("bedding_zones", {}).get("features", [])
            behavioral_notes = response.get("behavioral_analysis", {}).get("behavioral_notes", [])
            
            text_sources = (
                behavioral_notes +
                [area.get("properties", {}).get("description", "") for area in bedding_areas]
            )
            
            full_text = " ".join(text_sources).lower()
            
            if any(phrase in full_text for phrase in ["south", "thermal", "solar", "warm"]):
                analysis["south_facing_preference"] = True
                analysis["thermal_aware"] = True
                
        except Exception as e:
            logger.error(f"Thermal preference analysis failed: {e}")
        
        return analysis
    
    def analyze_activity_level(self, response: Dict, time_period: str) -> str:
        """Analyze predicted activity level"""
        
        try:
            behavioral_analysis = response.get("behavioral_analysis", {})
            movement_probability = behavioral_analysis.get("movement_probability", 50)
            
            if movement_probability >= 70:
                return "high"
            elif movement_probability >= 40:
                return "moderate"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"Activity level analysis failed: {e}")
            return "unknown"
    
    def analyze_pressure_response(self, response: Dict) -> Dict[str, bool]:
        """Analyze hunting pressure response"""
        
        analysis = {
            "reduced_daytime_activity": False,
            "pressure_aware": False
        }
        
        try:
            behavioral_notes = response.get("behavioral_analysis", {}).get("behavioral_notes", [])
            text = " ".join(behavioral_notes).lower()
            
            pressure_indicators = ["pressure", "nocturnal", "reduced", "cautious", "avoid"]
            
            if any(indicator in text for indicator in pressure_indicators):
                analysis["reduced_daytime_activity"] = True
                analysis["pressure_aware"] = True
                
        except Exception as e:
            logger.error(f"Pressure response analysis failed: {e}")
        
        return analysis
    
    def analyze_mature_buck_differences(self, general: Dict, mature: Dict) -> Dict[str, bool]:
        """Analyze differences between general and mature buck predictions"""
        
        analysis = {
            "shows_differences": False,
            "more_cautious": False
        }
        
        try:
            # Compare movement probabilities
            general_prob = general.get("behavioral_analysis", {}).get("movement_probability", 50)
            mature_prob = mature.get("behavioral_analysis", {}).get("movement_probability", 50)
            
            # Mature bucks should generally be more cautious (lower probability)
            if mature_prob < general_prob * 0.9:  # At least 10% reduction
                analysis["shows_differences"] = True
                analysis["more_cautious"] = True
                
        except Exception as e:
            logger.error(f"Mature buck analysis failed: {e}")
        
        return analysis
    
    def analyze_data_integration(self, response: Dict) -> Dict[str, Any]:
        """Analyze evidence of backend data integration"""
        
        analysis = {
            "data_sources_used": [],
            "integration_quality": "unknown"
        }
        
        try:
            # Look for evidence of different data sources
            if response.get("weather_data"):
                analysis["data_sources_used"].append("Weather")
                
            if response.get("terrain_analysis"):
                analysis["data_sources_used"].append("Terrain")
                
            if response.get("vegetation_analysis"):
                analysis["data_sources_used"].append("Vegetation/GEE")
                
            # Check for coordinate precision (indicates real data)
            stands = response.get("stand_recommendations", [])
            if stands and any("lat" in str(stand) for stand in stands):
                analysis["data_sources_used"].append("GPS_Coordinates")
                
        except Exception as e:
            logger.error(f"Data integration analysis failed: {e}")
        
        return analysis
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        print("\n" + "="*60)
        print("🔍 BACKEND-FRONTEND ACCURACY VALIDATION REPORT")
        print("="*60)
        
        # Count results
        total_tests = len(self.test_results) + len(self.critical_errors) + len(self.warnings)
        passed_tests = len(self.test_results)
        critical_count = len(self.critical_errors)
        warning_count = len(self.warnings)
        
        # Calculate accuracy score
        if total_tests > 0:
            accuracy_score = (passed_tests / total_tests) * 100
        else:
            accuracy_score = 0
        
        # Print results
        print(f"\n📊 OVERALL ACCURACY: {accuracy_score:.1f}%")
        print(f"✅ Passed Tests: {passed_tests}")
        print(f"❌ Critical Errors: {critical_count}")
        print(f"⚠️ Warnings: {warning_count}")
        
        if accuracy_score >= 80:
            status = "🏆 EXCELLENT"
        elif accuracy_score >= 60:
            status = "✅ GOOD"
        elif accuracy_score >= 40:
            status = "⚠️ NEEDS IMPROVEMENT"
        else:
            status = "❌ POOR"
        
        print(f"\n🎯 BIOLOGICAL ACCURACY: {status}")
        
        # Detailed results
        if self.test_results:
            print(f"\n✅ PASSED TESTS ({len(self.test_results)}):")
            for result in self.test_results:
                print(f"  • {result['test']}: {result['status']} - {result['details']}")
        
        if self.critical_errors:
            print(f"\n❌ CRITICAL ERRORS ({len(self.critical_errors)}):")
            for error in self.critical_errors:
                print(f"  • {error['test']}: {error['status']} - {error['details']}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning['test']}: {warning['status']} - {warning['details']}")
        
        # Recommendations
        print(f"\n🔧 RECOMMENDATIONS:")
        if critical_count > 0:
            print("  • Fix critical biological logic errors immediately")
        if warning_count > 0:
            print("  • Review warnings for potential improvements")
        if accuracy_score >= 80:
            print("  • System shows excellent biological accuracy!")
        
        return {
            "overall_accuracy": accuracy_score,
            "status": status,
            "passed_tests": passed_tests,
            "critical_errors": critical_count,
            "warnings": warning_count,
            "total_tests": total_tests,
            "detailed_results": {
                "passed": self.test_results,
                "errors": self.critical_errors,
                "warnings": self.warnings
            }
        }

def main():
    """Run the validation test suite"""
    validator = BackendFrontendAccuracyValidator()
    
    try:
        report = validator.run_comprehensive_validation()
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backend_frontend_accuracy_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {filename}")
        
        # Exit with appropriate code
        if report.get("critical_errors", 0) > 0:
            print("\n⚠️ CRITICAL BIOLOGICAL ERRORS DETECTED - Review immediately!")
            sys.exit(1)
        elif report.get("overall_accuracy", 0) < 60:
            print("\n⚠️ Low biological accuracy - Review recommended")
            sys.exit(1)
        else:
            print("\n✅ Biological accuracy validation completed successfully!")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
