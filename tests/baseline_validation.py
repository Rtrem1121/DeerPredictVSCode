"""
Baseline validation script to capture current system behavior.

This script establishes baseline metrics for the current excellent functionality
before any refactoring begins. It captures:
- API response times and structures
- Prediction confidence levels
- Camera placement accuracy
- Mature buck analysis results

Run this BEFORE any refactoring to establish what we need to preserve.
"""

import sys
import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.fixtures.test_data import (
    GOLDEN_TEST_LOCATION,
    TEST_LOCATIONS,
    PERFORMANCE_BENCHMARKS,
    get_prediction_request_template,
    get_rut_season_request,
    validate_response_structure,
    save_baseline_response
)

class BaselineValidator:
    """Captures and validates current system performance."""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": {},
            "api_responses": {},
            "validation_errors": [],
            "success_metrics": {}
        }
    
    def test_backend_connectivity(self) -> bool:
        """Test if backend is running and responsive."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Backend connectivity confirmed")
                return True
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend connection failed: {e}")
            print("   Make sure backend is running: python backend/main.py")
            return False
    
    def capture_prediction_baseline(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Capture baseline prediction for a location."""
        print(f"\n🎯 Testing location: {location['name']}")
        
        request_data = get_prediction_request_template(
            latitude=location["latitude"],
            longitude=location["longitude"],
            season="rut"  # Use rut season for baseline testing
        )
        
        # Measure response time
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.backend_url}/predict",
                json=request_data,
                timeout=60
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                
                print(f"   ✅ Response time: {response_time:.2f}s")
                
                # Extract key metrics
                metrics = self.extract_key_metrics(response_data)
                print(f"   📊 Prediction confidence: {metrics.get('prediction_confidence', 'N/A')}")
                print(f"   📷 Camera confidence: {metrics.get('camera_confidence', 'N/A')}")
                print(f"   🦌 Mature buck probability: {metrics.get('mature_buck_probability', 'N/A')}")
                
                # Validate response structure
                structure_errors = validate_response_structure(response_data)
                if structure_errors:
                    print(f"   ⚠️  Structure validation issues: {len(structure_errors)}")
                    for error in structure_errors:
                        print(f"      - {error}")
                
                # Save baseline
                baseline_file = save_baseline_response(location["name"], response_data)
                print(f"   💾 Baseline saved: {baseline_file}")
                
                return {
                    "success": True,
                    "response_time": response_time,
                    "response_data": response_data,
                    "metrics": metrics,
                    "structure_errors": structure_errors
                }
            else:
                print(f"   ❌ API request failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": response_time
                }
                
        except Exception as e:
            response_time = time.time() - start_time
            print(f"   ❌ Request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time
            }
    
    def extract_key_metrics(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from API response."""
        metrics = {}
        
        # Prediction confidence
        if "prediction_confidence" in response_data:
            metrics["prediction_confidence"] = response_data["prediction_confidence"]
        
        # Camera placement confidence - check multiple sources
        camera_confidence = None
        
        # First check direct camera_placement field
        if "camera_placement" in response_data:
            camera_data = response_data["camera_placement"]
            if "confidence" in camera_data:
                camera_confidence = camera_data["confidence"]
            if "distance_meters" in camera_data:
                metrics["camera_distance"] = camera_data["distance_meters"]
        
        # If not found, parse from notes field
        if camera_confidence is None:
            notes = response_data.get('notes', '')
            import re
            confidence_match = re.search(r'Confidence.*?(\d+\.?\d*)%', notes)
            if confidence_match:
                camera_confidence = float(confidence_match.group(1))
        
        if camera_confidence is not None:
            metrics["camera_confidence"] = camera_confidence
        
        # Mature buck analysis
        if "mature_buck_analysis" in response_data:
            buck_data = response_data["mature_buck_analysis"]
            if "movement_probability" in buck_data:
                metrics["mature_buck_probability"] = buck_data["movement_probability"]
            if "confidence_score" in buck_data:
                metrics["mature_buck_confidence"] = buck_data["confidence_score"]
        
        return metrics
    
    def validate_golden_location(self) -> bool:
        """Validate the golden test location maintains excellent camera confidence."""
        print("\n🏆 GOLDEN LOCATION VALIDATION")
        print("=" * 50)
        
        result = self.capture_prediction_baseline(GOLDEN_TEST_LOCATION)
        
        if not result["success"]:
            print("❌ Golden location test FAILED")
            return False
        
        metrics = result["metrics"]
        camera_confidence = metrics.get("camera_confidence", 0)
        
        # Validate camera confidence against acceptable range
        min_confidence, max_confidence = PERFORMANCE_BENCHMARKS["camera_confidence_acceptable_range"]
        target_confidence = PERFORMANCE_BENCHMARKS["camera_confidence_target"]
        
        if min_confidence <= camera_confidence <= max_confidence:
            if abs(camera_confidence - target_confidence) <= 5.0:  # Within 5% of target
                print(f"✅ Camera confidence meets target: {camera_confidence}% (target: {target_confidence}%)")
            else:
                print(f"✅ Camera confidence acceptable: {camera_confidence}% (range: {min_confidence}-{max_confidence}%)")
            success = True
        else:
            print(f"⚠️  Camera confidence outside acceptable range: {camera_confidence}% (acceptable: {min_confidence}-{max_confidence}%)")
            success = False
        
        # Validate response time
        response_time = result["response_time"]
        if response_time <= PERFORMANCE_BENCHMARKS["api_response_time_max"]:
            print(f"✅ Response time acceptable: {response_time:.2f}s")
        else:
            print(f"⚠️  Response time slow: {response_time:.2f}s (max: {PERFORMANCE_BENCHMARKS['api_response_time_max']}s)")
            success = False
        
        self.results["golden_location_test"] = {
            "success": success,
            "camera_confidence": camera_confidence,
            "response_time": response_time,
            "metrics": metrics
        }
        
        return success
    
    def run_comprehensive_baseline(self) -> Dict[str, Any]:
        """Run comprehensive baseline validation."""
        print("🎯 DEER PREDICTION APP - BASELINE VALIDATION")
        print("=" * 60)
        print("Capturing current excellent functionality before refactoring...")
        
        # Test backend connectivity
        if not self.test_backend_connectivity():
            print("\n❌ BASELINE VALIDATION FAILED - Backend not accessible")
            return {"success": False, "error": "Backend not accessible"}
        
        # Test golden location (most critical)
        golden_success = self.validate_golden_location()
        
        # Test all locations
        print("\n📍 TESTING ALL LOCATIONS")
        print("=" * 30)
        
        all_locations_success = True
        for location in TEST_LOCATIONS:
            result = self.capture_prediction_baseline(location)
            if not result["success"]:
                all_locations_success = False
            
            self.results["api_responses"][location["name"]] = result
        
        # Calculate overall success
        overall_success = golden_success and all_locations_success
        
        # Generate summary
        self.generate_baseline_summary(overall_success)
        
        return {
            "success": overall_success,
            "results": self.results
        }
    
    def generate_baseline_summary(self, overall_success: bool):
        """Generate and display baseline summary."""
        print("\n📊 BASELINE VALIDATION SUMMARY")
        print("=" * 40)
        
        if overall_success:
            print("✅ BASELINE VALIDATION SUCCESSFUL")
            print("   Current system is performing excellently")
            print("   Safe to proceed with refactoring")
        else:
            print("⚠️  BASELINE VALIDATION ISSUES DETECTED")
            print("   Review issues before proceeding with refactoring")
        
        # Performance summary
        response_times = []
        camera_confidences = []
        
        for location_name, result in self.results["api_responses"].items():
            if result["success"]:
                response_times.append(result["response_time"])
                metrics = result.get("metrics", {})
                if "camera_confidence" in metrics:
                    camera_confidences.append(metrics["camera_confidence"])
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            print(f"\n⏱️  Response Times:")
            print(f"   Average: {avg_response_time:.2f}s")
            print(f"   Maximum: {max_response_time:.2f}s")
            print(f"   Target: <{PERFORMANCE_BENCHMARKS['api_response_time_max']}s")
        
        if camera_confidences:
            avg_camera_confidence = sum(camera_confidences) / len(camera_confidences)
            max_camera_confidence = max(camera_confidences)
            print(f"\n📷 Camera Placement Confidence:")
            print(f"   Average: {avg_camera_confidence:.1f}%")
            print(f"   Maximum: {max_camera_confidence:.1f}%")
            print(f"   Target: ≥{PERFORMANCE_BENCHMARKS['prediction_confidence_min']}%")
        
        # Save results
        results_file = f"tests/fixtures/baseline_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed results saved: {results_file}")
        
        print("\n🎯 NEXT STEPS:")
        if overall_success:
            print("   1. Review baseline metrics")
            print("   2. Begin Phase 2: Backend Refactoring")
            print("   3. Run this validation after each change")
            print("   4. Ensure metrics remain within acceptable ranges")
        else:
            print("   1. Fix identified issues")
            print("   2. Re-run baseline validation")
            print("   3. Only proceed when all tests pass")

def main():
    """Main execution function."""
    validator = BaselineValidator()
    result = validator.run_comprehensive_baseline()
    
    # Exit with appropriate code
    exit_code = 0 if result["success"] else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
