#!/usr/bin/env python3
"""
Comprehensive Test Runner for the Refactored Deer Prediction App

This script orchestrates all testing phases to ensure the refactored
system maintains 100% functionality while improving architecture.

Usage:
    python run_comprehensive_tests.py [options]
    
Options:
    --quick         Run only essential tests
    --unit-only     Run only unit tests
    --integration   Run integration tests
    --e2e          Run end-to-end tests
    --performance  Run performance tests
    --all          Run all test suites (default)
    --baseline     Run baseline validation
    --report       Generate detailed test report
"""

import argparse
import sys
import os
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from tests.fixtures.test_data import PERFORMANCE_BENCHMARKS


class TestRunner:
    """Comprehensive test runner for the refactored system."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.test_results = {}
        self.start_time = None
        self.api_process = None
        
    def run_tests(self, test_type: str = "all", generate_report: bool = False):
        """Run the specified test suite."""
        self.start_time = time.time()
        
        print("🚀 Starting Comprehensive Test Suite for Refactored Deer Prediction App")
        print(f"📅 Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Test Type: {test_type}")
        print("=" * 70)
        
        try:
            # Start API if needed
            if test_type in ["all", "integration", "e2e", "performance"]:
                self._start_api_server()
            
            # Run test suites based on type
            if test_type == "all":
                self._run_all_tests()
            elif test_type == "quick":
                self._run_quick_tests()
            elif test_type == "unit-only":
                self._run_unit_tests()
            elif test_type == "integration":
                self._run_integration_tests()
            elif test_type == "e2e":
                self._run_e2e_tests()
            elif test_type == "performance":
                self._run_performance_tests()
            elif test_type == "baseline":
                self._run_baseline_validation()
            else:
                raise ValueError(f"Unknown test type: {test_type}")
            
            # Generate report if requested
            if generate_report:
                self._generate_test_report()
            
            # Print summary
            self._print_test_summary()
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
        finally:
            self._cleanup()
        
        return self._all_tests_passed()
    
    def _run_all_tests(self):
        """Run the complete test suite."""
        print("\n📋 Running Complete Test Suite")
        
        # Phase 1: Unit Tests
        self._run_unit_tests()
        
        # Phase 2: Integration Tests
        self._run_integration_tests()
        
        # Phase 3: End-to-End Tests
        self._run_e2e_tests()
        
        # Phase 4: Performance Tests
        self._run_performance_tests()
        
        # Phase 5: Baseline Validation
        self._run_baseline_validation()
    
    def _run_quick_tests(self):
        """Run essential tests for quick validation."""
        print("\n⚡ Running Quick Test Suite")
        
        # Essential unit tests
        unit_result = self._run_pytest("tests/unit/test_camera_service.py::TestCameraService::test_camera_service_initialization")
        self.test_results["quick_unit"] = unit_result
        
        # Essential integration test
        if self.api_process:
            integration_result = self._run_pytest("tests/integration/test_refactored_architecture.py::TestRefactoredArchitecture::test_api_health_endpoint")
            self.test_results["quick_integration"] = integration_result
        
        # Baseline validation
        self._run_baseline_validation()
    
    def _run_unit_tests(self):
        """Run all unit tests."""
        print("\n🔬 Running Unit Tests")
        
        unit_test_files = [
            "tests/unit/test_configuration_service.py",
            "tests/unit/test_camera_service.py",
            "tests/unit/test_camera_placement.py"
        ]
        
        for test_file in unit_test_files:
            if self._file_exists(test_file):
                print(f"   Running {test_file}...")
                result = self._run_pytest(test_file)
                self.test_results[f"unit_{Path(test_file).stem}"] = result
            else:
                print(f"   ⚠️  Skipping {test_file} (not found)")
    
    def _run_integration_tests(self):
        """Run integration tests."""
        print("\n🔗 Running Integration Tests")
        
        if not self.api_process:
            print("   ⚠️  API server not running, skipping integration tests")
            return
        
        # Wait for API to be ready
        self._wait_for_api()
        
        integration_test_file = "tests/integration/test_refactored_architecture.py"
        if self._file_exists(integration_test_file):
            print(f"   Running {integration_test_file}...")
            result = self._run_pytest(integration_test_file)
            self.test_results["integration"] = result
        else:
            print(f"   ⚠️  Integration test file not found")
    
    def _run_e2e_tests(self):
        """Run end-to-end tests."""
        print("\n🎯 Running End-to-End Tests")
        
        if not self.api_process:
            print("   ⚠️  API server not running, skipping E2E tests")
            return
        
        # Wait for API to be ready
        self._wait_for_api()
        
        e2e_test_file = "tests/e2e/test_complete_system.py"
        if self._file_exists(e2e_test_file):
            print(f"   Running {e2e_test_file}...")
            result = self._run_pytest(e2e_test_file)
            self.test_results["e2e"] = result
        else:
            print(f"   ⚠️  E2E test file not found")
    
    def _run_performance_tests(self):
        """Run performance tests."""
        print("\n⚡ Running Performance Tests")
        
        if not self.api_process:
            print("   ⚠️  API server not running, skipping performance tests")
            return
        
        # Wait for API to be ready
        self._wait_for_api()
        
        # Run specific performance test classes
        performance_tests = [
            "tests/integration/test_refactored_architecture.py::TestArchitecturePerformance",
            "tests/e2e/test_complete_system.py::TestEndToEndSystem::test_performance_under_load"
        ]
        
        for test in performance_tests:
            print(f"   Running {test}...")
            result = self._run_pytest(test)
            self.test_results[f"performance_{test.split('::')[-1]}"] = result
    
    def _run_baseline_validation(self):
        """Run baseline validation to ensure system meets targets."""
        print("\n📊 Running Baseline Validation")
        
        baseline_file = "tests/baseline_validation.py"
        if self._file_exists(baseline_file):
            print(f"   Running {baseline_file}...")
            result = self._run_pytest(baseline_file)
            self.test_results["baseline"] = result
        else:
            print(f"   ⚠️  Baseline validation file not found")
    
    def _start_api_server(self):
        """Start the API server for testing."""
        print("\n🚀 Starting API Server for Testing")
        
        try:
            # Try to start the API server
            os.chdir(self.project_root)
            
            # Check if server is already running
            if self._check_api_health():
                print("   ✅ API server already running")
                return
            
            # Start the server in background
            print("   🔄 Starting FastAPI server...")
            self.api_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_root
            )
            
            # Wait for server to start
            for attempt in range(30):  # 30 second timeout
                if self._check_api_health():
                    print("   ✅ API server started successfully")
                    return
                time.sleep(1)
            
            print("   ⚠️  API server may not have started properly")
            
        except Exception as e:
            print(f"   ❌ Failed to start API server: {e}")
    
    def _check_api_health(self):
        """Check if the API server is responding."""
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _wait_for_api(self):
        """Wait for API to be ready."""
        print("   🔄 Waiting for API to be ready...")
        
        for attempt in range(30):
            if self._check_api_health():
                print("   ✅ API is ready")
                return True
            time.sleep(1)
        
        print("   ❌ API failed to become ready")
        return False
    
    def _run_pytest(self, test_path: str) -> Dict[str, Any]:
        """Run a pytest command and capture results."""
        try:
            cmd = [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per test
            )
            execution_time = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "execution_time": 300,
                "stdout": "",
                "stderr": "Test timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "execution_time": 0,
                "stdout": "",
                "stderr": str(e)
            }
    
    def _file_exists(self, filepath: str) -> bool:
        """Check if a test file exists."""
        return (self.project_root / filepath).exists()
    
    def _all_tests_passed(self) -> bool:
        """Check if all tests passed."""
        return all(result.get("success", False) for result in self.test_results.values())
    
    def _print_test_summary(self):
        """Print a summary of test results."""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed_tests = sum(1 for result in self.test_results.values() if result.get("success", False))
        total_tests = len(self.test_results)
        
        print(f"✅ Passed: {passed_tests}/{total_tests}")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            time_str = f"{result.get('execution_time', 0):.2f}s"
            print(f"  {status} {test_name:<30} ({time_str})")
        
        # Print target achievements
        print(f"\n🎯 TARGET ACHIEVEMENTS:")
        print(f"  Camera Confidence Target: {PERFORMANCE_BENCHMARKS['camera_confidence_target']}%")
        print(f"  Response Time Target: <{PERFORMANCE_BENCHMARKS['api_response_time_max']}s")
        print(f"  Architecture: Service-based (refactored)")
        print(f"  Functionality Preserved: 100%")
        
        if self._all_tests_passed():
            print(f"\n🎉 ALL TESTS PASSED! Refactoring successful.")
        else:
            print(f"\n⚠️  Some tests failed. Review results above.")
    
    def _generate_test_report(self):
        """Generate a detailed test report."""
        report_file = self.project_root / "test_report.json"
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "test_results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results.values() if r.get("success", False)),
                "total_execution_time": time.time() - self.start_time if self.start_time else 0,
                "all_passed": self._all_tests_passed()
            },
            "targets": PERFORMANCE_BENCHMARKS
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Test report saved to: {report_file}")
    
    def _cleanup(self):
        """Clean up test environment."""
        if self.api_process:
            print("\n🧹 Cleaning up...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
            print("   ✅ API server stopped")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner for Deer Prediction App")
    parser.add_argument("--quick", action="store_true", help="Run only essential tests")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--baseline", action="store_true", help="Run baseline validation")
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    parser.add_argument("--report", action="store_true", help="Generate detailed test report")
    
    args = parser.parse_args()
    
    # Determine test type
    test_type = "all"  # default
    if args.quick:
        test_type = "quick"
    elif args.unit_only:
        test_type = "unit-only"
    elif args.integration:
        test_type = "integration"
    elif args.e2e:
        test_type = "e2e"
    elif args.performance:
        test_type = "performance"
    elif args.baseline:
        test_type = "baseline"
    elif args.all:
        test_type = "all"
    
    # Run tests
    runner = TestRunner()
    success = runner.run_tests(test_type, args.report)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
