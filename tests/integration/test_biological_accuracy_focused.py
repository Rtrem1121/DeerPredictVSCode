#!/usr/bin/env python3
"""
Focused Biological Accuracy Test

This test validates biological accuracy with improved timeout handling
and focused testing on specific biological logic errors like AM movement direction.

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
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FocusedBiologicalAccuracyTest:
    """Focused test for biological accuracy with improved error handling"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.test_results = []
        self.critical_errors = []
        self.warnings = []
        self.timeout = 60  # Increased timeout
        
    def run_focused_tests(self) -> Dict[str, Any]:
        """Run focused biological accuracy tests"""
        print("🧪 FOCUSED BIOLOGICAL ACCURACY TEST")
        print("=" * 50)
        
        # First, check if backend is responsive
        if not self.check_backend_health():
            print("❌ Backend not responsive - cannot run tests")
            return {"status": "BACKEND_DOWN", "error": "Backend service not available"}
        
        try:
            # Test 1: Critical AM Movement Direction Test
            self.test_am_movement_critical()
            
            # Test 2: Basic Prediction Logic Test  
            self.test_basic_prediction_logic()
            
            # Test 3: Wind Direction Logic Test
            self.test_wind_direction_logic()
            
            # Test 4: Seasonal Behavior Test
            self.test_seasonal_behavior_basic()
            
            # Test 5: Time-based Activity Test
            self.test_time_activity_patterns()
            
            return self.generate_focused_report()
            
        except Exception as e:
            self.critical_errors.append(f"Test suite failed: {str(e)}")
            logger.error(f"Critical test error: {e}")
            return {"status": "FAILED", "error": str(e)}
    
    def check_backend_health(self) -> bool:
        """Check if backend is responsive"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            return response.status_code == 200
        except:
            # Try basic predict endpoint with minimal payload
            try:
                payload = {"lat": 44.26639, "lon": -72.58133}
                response = requests.post(
                    f"{self.backend_url}/predict",
                    json=payload,
                    timeout=15
                )
                return response.status_code in [200, 422]  # 422 is acceptable (validation error)
            except:
                return False
    
    def test_am_movement_critical(self):
        """Critical test for AM movement direction (the specific issue you found)"""
        print("\n🌅 CRITICAL TEST: AM Movement Direction Logic...")
        
        # Test specific AM scenario that was problematic
        test_time = "07:00"  # Peak morning movement time
        
        try:
            response = self.make_prediction_request_safe(
                date_time="2025-08-26T07:00:00",
                season="early_season"
            )
            
            if response:
                # Analyze the response for movement direction indicators
                movement_analysis = self.analyze_am_movement_direction(response)
                
                print(f"  Movement analysis: {movement_analysis}")
                
                if movement_analysis["is_biologically_correct"]:
                    self.test_results.append({
                        "test": "Critical AM Movement Direction",
                        "status": "✅ CORRECT",
                        "details": movement_analysis["explanation"]
                    })
                    print(f"  ✅ PASSED: {movement_analysis['explanation']}")
                else:
                    self.critical_errors.append({
                        "test": "Critical AM Movement Direction", 
                        "status": "❌ CRITICAL BUG",
                        "details": movement_analysis["explanation"]
                    })
                    print(f"  ❌ CRITICAL BUG: {movement_analysis['explanation']}")
            else:
                self.warnings.append({
                    "test": "Critical AM Movement Direction",
                    "status": "⚠️ NO DATA",
                    "details": "Could not get prediction response for AM test"
                })
                
        except Exception as e:
            logger.error(f"AM movement test failed: {e}")
            self.warnings.append({
                "test": "Critical AM Movement Direction",
                "status": "⚠️ ERROR", 
                "details": f"Test failed due to: {str(e)}"
            })
    
    def test_basic_prediction_logic(self):
        """Test basic prediction logic structure"""
        print("\n🔧 Testing Basic Prediction Logic...")
        
        try:
            response = self.make_prediction_request_safe()
            
            if response:
                # Check for required prediction components
                required_components = [
                    "stand_recommendations", 
                    "behavioral_analysis"
                ]
                
                missing_components = []
                for component in required_components:
                    if component not in response:
                        missing_components.append(component)
                
                if not missing_components:
                    self.test_results.append({
                        "test": "Basic Prediction Structure",
                        "status": "✅ CORRECT",
                        "details": "All required prediction components present"
                    })
                else:
                    self.warnings.append({
                        "test": "Basic Prediction Structure",
                        "status": "⚠️ INCOMPLETE",
                        "details": f"Missing components: {missing_components}"
                    })
                    
                # Check for biological reasoning
                behavioral_analysis = response.get("behavioral_analysis", {})
                if behavioral_analysis.get("behavioral_notes"):
                    self.test_results.append({
                        "test": "Biological Reasoning",
                        "status": "✅ PRESENT",
                        "details": "Behavioral analysis includes reasoning"
                    })
                else:
                    self.warnings.append({
                        "test": "Biological Reasoning", 
                        "status": "⚠️ MISSING",
                        "details": "No behavioral reasoning provided"
                    })
                    
        except Exception as e:
            logger.error(f"Basic prediction test failed: {e}")
    
    def test_wind_direction_logic(self):
        """Test wind direction integration"""
        print("\n🌬️ Testing Wind Direction Logic...")
        
        try:
            response = self.make_prediction_request_safe()
            
            if response:
                # Look for wind-related analysis
                wind_mentions = self.find_wind_mentions(response)
                
                if wind_mentions["has_wind_analysis"]:
                    self.test_results.append({
                        "test": "Wind Integration",
                        "status": "✅ PRESENT",
                        "details": f"Wind analysis found: {wind_mentions['mentions']}"
                    })
                else:
                    self.warnings.append({
                        "test": "Wind Integration",
                        "status": "⚠️ MISSING", 
                        "details": "No wind direction analysis found in response"
                    })
                    
        except Exception as e:
            logger.error(f"Wind direction test failed: {e}")
    
    def test_seasonal_behavior_basic(self):
        """Test basic seasonal behavior differences"""
        print("\n🍂 Testing Seasonal Behavior Logic...")
        
        seasons = ["early_season", "rut", "late_season"]
        seasonal_responses = {}
        
        for season in seasons:
            try:
                response = self.make_prediction_request_safe(season=season)
                if response:
                    seasonal_responses[season] = response
                    
            except Exception as e:
                logger.error(f"Seasonal test failed for {season}: {e}")
        
        # Compare responses
        if len(seasonal_responses) >= 2:
            differences_found = self.compare_seasonal_responses(seasonal_responses)
            
            if differences_found:
                self.test_results.append({
                    "test": "Seasonal Behavior Differences",
                    "status": "✅ CORRECT",
                    "details": "Different predictions for different seasons"
                })
            else:
                self.warnings.append({
                    "test": "Seasonal Behavior Differences",
                    "status": "⚠️ STATIC", 
                    "details": "Predictions appear identical across seasons"
                })
        else:
            self.warnings.append({
                "test": "Seasonal Behavior Differences",
                "status": "⚠️ INCOMPLETE",
                "details": "Could not test multiple seasons"
            })
    
    def test_time_activity_patterns(self):
        """Test time-based activity patterns"""
        print("\n⏰ Testing Time-Based Activity Patterns...")
        
        times = [
            ("06:00", "dawn"),
            ("12:00", "midday"), 
            ("18:00", "dusk")
        ]
        
        time_responses = {}
        
        for time_str, period in times:
            try:
                response = self.make_prediction_request_safe(
                    date_time=f"2025-08-26T{time_str}:00"
                )
                if response:
                    time_responses[period] = response
                    
            except Exception as e:
                logger.error(f"Time test failed for {period}: {e}")
        
        # Analyze time-based differences
        if len(time_responses) >= 2:
            time_differences = self.analyze_time_differences(time_responses)
            
            if time_differences["shows_variation"]:
                self.test_results.append({
                    "test": "Time-Based Activity Patterns",
                    "status": "✅ CORRECT",
                    "details": "Predictions vary appropriately by time of day"
                })
            else:
                self.warnings.append({
                    "test": "Time-Based Activity Patterns",
                    "status": "⚠️ STATIC",
                    "details": "Predictions don't vary significantly by time"
                })
        else:
            self.warnings.append({
                "test": "Time-Based Activity Patterns", 
                "status": "⚠️ INCOMPLETE",
                "details": "Could not test multiple times"
            })
    
    def make_prediction_request_safe(self, **kwargs) -> Dict[str, Any]:
        """Make a prediction request with better error handling"""
        
        # Default Vermont test location
        payload = {
            "lat": 44.26639,
            "lon": -72.58133,
            "date_time": "2025-08-26T06:00:00",
            "season": "early_season"
        }
        
        # Override with any provided parameters
        payload.update(kwargs)
        
        try:
            headers = {"Content-Type": "application/json"}
            
            # Add retry logic
            for attempt in range(2):
                try:
                    response = requests.post(
                        f"{self.backend_url}/predict",
                        headers=headers,
                        json=payload,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        logger.warning(f"Request failed with status {response.status_code}: {response.text}")
                        if attempt == 0:
                            time.sleep(2)  # Wait before retry
                            continue
                        return None
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"Request timeout on attempt {attempt + 1}")
                    if attempt == 0:
                        time.sleep(3)  # Wait longer before retry
                        continue
                    return None
                    
            return None
                
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def analyze_am_movement_direction(self, response: Dict) -> Dict[str, Any]:
        """Analyze AM movement direction for biological correctness"""
        
        analysis = {
            "is_biologically_correct": False,
            "explanation": "Could not determine movement direction",
            "confidence": "low"
        }
        
        try:
            # Look for behavioral notes and stand recommendations
            behavioral_notes = response.get("behavioral_analysis", {}).get("behavioral_notes", [])
            stand_recommendations = response.get("stand_recommendations", [])
            
            # Combine all text for analysis
            all_text = " ".join(behavioral_notes)
            for stand in stand_recommendations:
                all_text += " " + stand.get("description", "")
                all_text += " " + stand.get("strategy", "")
            
            text_lower = all_text.lower()
            
            # Look for biological correctness indicators
            correct_am_indicators = [
                "return to bed", "returning to bed", "heading to bedding", 
                "moving to cover", "feeding to bedding", "back to bedding",
                "morning return", "retreat to cover", "seeking bedding"
            ]
            
            incorrect_am_indicators = [
                "leaving bedding", "heading to feed", "bedding to feeding",
                "morning feeding", "leaving cover", "moving to food"
            ]
            
            # Check for correct AM behavior
            correct_matches = sum(1 for indicator in correct_am_indicators if indicator in text_lower)
            incorrect_matches = sum(1 for indicator in incorrect_am_indicators if indicator in text_lower)
            
            if correct_matches > incorrect_matches and correct_matches > 0:
                analysis.update({
                    "is_biologically_correct": True,
                    "explanation": f"Correctly shows deer returning to bedding in AM (found {correct_matches} correct indicators)",
                    "confidence": "high"
                })
            elif incorrect_matches > correct_matches and incorrect_matches > 0:
                analysis.update({
                    "is_biologically_correct": False,
                    "explanation": f"INCORRECT: Shows deer leaving bedding in AM (found {incorrect_matches} wrong indicators)",
                    "confidence": "high"
                })
            else:
                # Look at movement probability and timing
                movement_prob = response.get("behavioral_analysis", {}).get("movement_probability", 50)
                
                if movement_prob >= 70:
                    analysis.update({
                        "is_biologically_correct": True,
                        "explanation": f"High movement probability ({movement_prob}%) appropriate for AM",
                        "confidence": "medium"
                    })
                elif movement_prob <= 30:
                    analysis.update({
                        "is_biologically_correct": False,
                        "explanation": f"Low movement probability ({movement_prob}%) inappropriate for peak AM time",
                        "confidence": "medium"
                    })
                
        except Exception as e:
            logger.error(f"AM movement analysis failed: {e}")
            analysis["explanation"] = f"Analysis failed: {str(e)}"
        
        return analysis
    
    def find_wind_mentions(self, response: Dict) -> Dict[str, Any]:
        """Find wind-related mentions in response"""
        
        wind_analysis = {
            "has_wind_analysis": False,
            "mentions": []
        }
        
        try:
            # Check various parts of response for wind mentions
            sections_to_check = [
                response.get("behavioral_analysis", {}).get("behavioral_notes", []),
                [stand.get("description", "") for stand in response.get("stand_recommendations", [])],
                [stand.get("strategy", "") for stand in response.get("stand_recommendations", [])]
            ]
            
            wind_keywords = ["wind", "scent", "thermal", "breeze", "airflow", "downwind", "upwind"]
            
            for section in sections_to_check:
                for text in section:
                    text_lower = text.lower()
                    for keyword in wind_keywords:
                        if keyword in text_lower:
                            wind_analysis["mentions"].append(f"{keyword} in: {text[:50]}...")
                            wind_analysis["has_wind_analysis"] = True
                            
        except Exception as e:
            logger.error(f"Wind mention analysis failed: {e}")
        
        return wind_analysis
    
    def compare_seasonal_responses(self, seasonal_responses: Dict) -> bool:
        """Compare seasonal responses for differences"""
        
        try:
            # Compare movement probabilities
            probs = []
            for season, response in seasonal_responses.items():
                prob = response.get("behavioral_analysis", {}).get("movement_probability", 50)
                probs.append(prob)
            
            # Check if there's variation (>10% difference)
            if max(probs) - min(probs) > 10:
                return True
            
            # Compare number of stand recommendations
            stand_counts = []
            for season, response in seasonal_responses.items():
                count = len(response.get("stand_recommendations", []))
                stand_counts.append(count)
            
            # Check for variation in recommendations
            if len(set(stand_counts)) > 1:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Seasonal comparison failed: {e}")
            return False
    
    def analyze_time_differences(self, time_responses: Dict) -> Dict[str, Any]:
        """Analyze time-based differences"""
        
        analysis = {
            "shows_variation": False,
            "details": []
        }
        
        try:
            # Compare movement probabilities across times
            time_probs = {}
            for period, response in time_responses.items():
                prob = response.get("behavioral_analysis", {}).get("movement_probability", 50)
                time_probs[period] = prob
            
            # Dawn and dusk should be higher than midday
            dawn_prob = time_probs.get("dawn", 50)
            dusk_prob = time_probs.get("dusk", 50)
            midday_prob = time_probs.get("midday", 50)
            
            if dawn_prob > midday_prob or dusk_prob > midday_prob:
                analysis["shows_variation"] = True
                analysis["details"].append(f"Dawn: {dawn_prob}%, Midday: {midday_prob}%, Dusk: {dusk_prob}%")
            
        except Exception as e:
            logger.error(f"Time analysis failed: {e}")
        
        return analysis
    
    def generate_focused_report(self) -> Dict[str, Any]:
        """Generate focused test report"""
        
        print("\n" + "="*50)
        print("🔍 FOCUSED BIOLOGICAL ACCURACY REPORT")
        print("="*50)
        
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
        
        if critical_count == 0 and accuracy_score >= 70:
            status = "🏆 GOOD"
        elif critical_count == 0 and accuracy_score >= 50:
            status = "✅ ACCEPTABLE"
        elif critical_count > 0:
            status = "❌ CRITICAL ISSUES FOUND"
        else:
            status = "⚠️ NEEDS REVIEW"
        
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
            print("  • URGENT: Fix critical biological logic errors")
        if warning_count > 3:
            print("  • Review warnings for potential improvements")
        if accuracy_score >= 70 and critical_count == 0:
            print("  • System shows good biological accuracy!")
        
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
    """Run the focused biological accuracy tests"""
    tester = FocusedBiologicalAccuracyTest()
    
    try:
        report = tester.run_focused_tests()
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"focused_biological_accuracy_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {filename}")
        
        # Exit with appropriate code
        if report.get("critical_errors", 0) > 0:
            print("\n⚠️ CRITICAL BIOLOGICAL ERRORS DETECTED!")
            sys.exit(1)
        elif report.get("overall_accuracy", 0) < 50:
            print("\n⚠️ Low biological accuracy detected")
            sys.exit(1)
        else:
            print("\n✅ Focused biological accuracy test completed!")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
