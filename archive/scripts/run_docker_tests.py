#!/usr/bin/env python3
"""
Docker-based Test Runner for the Refactored Deer Prediction App

This script runs comprehensive tests within the Docker containerized environment
to ensure the refactored system works correctly in its intended deployment context.

Usage:
    python run_docker_tests.py [options]
    
Options:
    --quick         Run only essential tests
    --integration   Run integration tests against containers
    --e2e          Run end-to-end tests
    --performance  Run performance tests
    --all          Run all test suites (default)
    --cleanup      Clean up Docker containers after tests
    --build        Force rebuild containers before testing
"""

import argparse
import sys
import os
import subprocess
import time
import json
import requests
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent


class DockerTestRunner:
    """Test runner for Docker containerized environment."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.test_results = {}
        self.start_time = None
        self.containers_started = False
        
    def run_tests(self, test_type: str = "all", force_build: bool = False, cleanup: bool = True):
        """Run tests in Docker environment."""
        self.start_time = time.time()
        
        print("🐳 Starting Docker-based Test Suite for Refactored Deer Prediction App")
        print(f"📅 Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Test Type: {test_type}")
        print("=" * 70)
        
        try:
            # Build and start containers
            if force_build:
                self._build_containers()
            
            self._start_containers()
            
            # Wait for services to be ready
            self._wait_for_services()
            
            # Run test suites
            if test_type == "all":
                self._run_all_docker_tests()
            elif test_type == "quick":
                self._run_quick_docker_tests()
            elif test_type == "integration":
                self._run_integration_tests()
            elif test_type == "e2e":
                self._run_e2e_tests()
            elif test_type == "performance":
                self._run_performance_tests()
            else:
                raise ValueError(f"Unknown test type: {test_type}")
            
            # Print summary
            self._print_test_summary()
            
        except Exception as e:
            print(f"❌ Docker test execution failed: {e}")
            return False
        finally:
            if cleanup:
                self._cleanup_containers()
        
        return self._all_tests_passed()
    
    def _build_containers(self):
        """Build Docker containers."""
        print("\n🔨 Building Docker Containers")
        
        try:
            cmd = ["docker-compose", "build", "--no-cache"]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ Containers built successfully")
            else:
                print(f"   ❌ Container build failed: {result.stderr}")
                raise Exception("Container build failed")
                
        except Exception as e:
            print(f"   ❌ Build error: {e}")
            raise
    
    def _start_containers(self):
        """Start Docker containers."""
        print("\n🚀 Starting Docker Containers")
        
        try:
            # Stop any existing containers
            subprocess.run(["docker-compose", "down"], cwd=self.project_root, capture_output=True)
            
            # Start containers
            cmd = ["docker-compose", "up", "-d"]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ Containers started successfully")
                self.containers_started = True
            else:
                print(f"   ❌ Container start failed: {result.stderr}")
                raise Exception("Container start failed")
                
        except Exception as e:
            print(f"   ❌ Start error: {e}")
            raise
    
    def _wait_for_services(self):
        """Wait for Docker services to be ready."""
        print("\n⏳ Waiting for Services to be Ready")
        
        services = {
            "backend": "http://localhost:8000/health",
            "frontend": "http://localhost:8501/_stcore/health"
        }
        
        for service_name, health_url in services.items():
            print(f"   🔄 Waiting for {service_name}...")
            
            for attempt in range(60):  # 60 second timeout
                try:
                    response = requests.get(health_url, timeout=5)
                    if response.status_code == 200:
                        print(f"   ✅ {service_name} is ready")
                        break
                except:
                    pass
                
                time.sleep(1)
            else:
                print(f"   ❌ {service_name} failed to become ready")
                raise Exception(f"{service_name} not ready")
    
    def _run_all_docker_tests(self):
        """Run all tests in Docker environment."""
        print("\n📋 Running Complete Docker Test Suite")
        
        # Test 1: Container Health
        self._test_container_health()
        
        # Test 2: API Functionality
        self._test_api_functionality()
        
        # Test 3: Frontend Accessibility
        self._test_frontend_accessibility()
        
        # Test 4: Integration
        self._test_service_integration()
        
        # Test 5: Performance
        self._test_docker_performance()
    
    def _run_quick_docker_tests(self):
        """Run quick validation tests."""
        print("\n⚡ Running Quick Docker Tests")
        
        # Essential tests for Docker environment
        self._test_container_health()
        self._test_api_functionality()
        self._test_refactored_architecture()
    
    def _test_container_health(self):
        """Test that all containers are healthy."""
        print("\n🏥 Testing Container Health")
        
        try:
            # Check container status
            cmd = ["docker-compose", "ps", "--format", "json"]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.test_results["container_health"] = {
                    "success": False,
                    "error": "Failed to get container status"
                }
                return
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        containers.append(json.loads(line))
                    except:
                        pass
            
            # Validate container states
            expected_services = ["backend", "frontend"]
            healthy_services = []
            
            for container in containers:
                service = container.get("Service", "")
                state = container.get("State", "")
                
                if service in expected_services:
                    if state == "running":
                        healthy_services.append(service)
                        print(f"   ✅ {service} container: {state}")
                    else:
                        print(f"   ❌ {service} container: {state}")
            
            success = len(healthy_services) == len(expected_services)
            self.test_results["container_health"] = {
                "success": success,
                "healthy_services": healthy_services,
                "expected_services": expected_services
            }
            
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            self.test_results["container_health"] = {
                "success": False,
                "error": str(e)
            }
    
    def _test_api_functionality(self):
        """Test API functionality in Docker."""
        print("\n🔌 Testing API Functionality")
        
        try:
            # Test health endpoint
            response = requests.get("http://localhost:8000/health", timeout=10)
            health_success = response.status_code == 200
            
            if health_success:
                health_data = response.json()
                print(f"   ✅ Health endpoint: {health_data.get('status', 'unknown')}")
            else:
                print(f"   ❌ Health endpoint failed: {response.status_code}")
            
            # Test prediction endpoint
            prediction_request = {
                "lat": 40.0,
                "lon": -74.0,
                "date_time": "2025-08-24T19:30:00Z",
                "season": "rut",
                "fast_mode": True
            }
            
            start_time = time.time()
            response = requests.post(
                "http://localhost:8000/predict",
                json=prediction_request,
                timeout=30
            )
            response_time = time.time() - start_time
            
            prediction_success = response.status_code == 200
            
            if prediction_success:
                prediction_data = response.json()
                print(f"   ✅ Prediction endpoint: {response_time:.2f}s")
                
                # Validate response structure
                required_fields = ["travel_corridors", "bedding_zones", "feeding_areas", "stand_rating"]
                structure_valid = all(field in prediction_data for field in required_fields)
                
                if structure_valid:
                    print(f"   ✅ Response structure valid")
                else:
                    print(f"   ❌ Response structure invalid")
                    prediction_success = False
                
            else:
                print(f"   ❌ Prediction endpoint failed: {response.status_code}")
            
            self.test_results["api_functionality"] = {
                "success": health_success and prediction_success,
                "health_success": health_success,
                "prediction_success": prediction_success,
                "response_time": response_time if prediction_success else None
            }
            
        except Exception as e:
            print(f"   ❌ API test failed: {e}")
            self.test_results["api_functionality"] = {
                "success": False,
                "error": str(e)
            }
    
    def _test_frontend_accessibility(self):
        """Test frontend accessibility."""
        print("\n🖥️ Testing Frontend Accessibility")
        
        try:
            # Test frontend health
            response = requests.get("http://localhost:8501/_stcore/health", timeout=10)
            frontend_success = response.status_code == 200
            
            if frontend_success:
                print(f"   ✅ Frontend health check passed")
            else:
                print(f"   ❌ Frontend health check failed: {response.status_code}")
            
            # Test main frontend page
            try:
                response = requests.get("http://localhost:8501/", timeout=10)
                main_page_success = response.status_code == 200
                
                if main_page_success:
                    print(f"   ✅ Frontend main page accessible")
                else:
                    print(f"   ❌ Frontend main page failed: {response.status_code}")
            except:
                main_page_success = False
                print(f"   ❌ Frontend main page not accessible")
            
            self.test_results["frontend_accessibility"] = {
                "success": frontend_success and main_page_success,
                "health_success": frontend_success,
                "main_page_success": main_page_success
            }
            
        except Exception as e:
            print(f"   ❌ Frontend test failed: {e}")
            self.test_results["frontend_accessibility"] = {
                "success": False,
                "error": str(e)
            }
    
    def _test_refactored_architecture(self):
        """Test that the refactored architecture is working."""
        print("\n🏗️ Testing Refactored Architecture")
        
        try:
            # Test configuration endpoint
            config_response = requests.get("http://localhost:8000/config/status", timeout=10)
            config_success = config_response.status_code == 200
            
            if config_success:
                print("   ✅ Configuration service working")
            else:
                print(f"   ❌ Configuration service failed: {config_response.status_code}")
            
            # Test camera service
            camera_request = {"lat": 40.0, "lon": -74.0}
            camera_response = requests.post(
                "http://localhost:8000/api/camera/optimal-placement",
                json=camera_request,
                timeout=15
            )
            camera_success = camera_response.status_code == 200
            
            if camera_success:
                print("   ✅ Camera service working")
            else:
                print(f"   ❌ Camera service failed: {camera_response.status_code}")
            
            # Test scouting service
            scouting_response = requests.get("http://localhost:8000/scouting/types", timeout=10)
            scouting_success = scouting_response.status_code == 200
            
            if scouting_success:
                print("   ✅ Scouting service working")
            else:
                print(f"   ❌ Scouting service failed: {scouting_response.status_code}")
            
            self.test_results["refactored_architecture"] = {
                "success": config_success and camera_success and scouting_success,
                "config_success": config_success,
                "camera_success": camera_success,
                "scouting_success": scouting_success
            }
            
        except Exception as e:
            print(f"   ❌ Architecture test failed: {e}")
            self.test_results["refactored_architecture"] = {
                "success": False,
                "error": str(e)
            }
    
    def _test_service_integration(self):
        """Test service integration in Docker."""
        print("\n🔗 Testing Service Integration")
        
        try:
            # Test that frontend can communicate with backend
            # This is implicit if both services are up and responsive
            
            # Test inter-service communication by making a full prediction
            # that exercises multiple services
            full_request = {
                "lat": 40.0,
                "lon": -74.0,
                "date_time": "2025-08-24T19:30:00Z",
                "season": "rut",
                "fast_mode": True
            }
            
            response = requests.post(
                "http://localhost:8000/predict",
                json=full_request,
                timeout=30
            )
            
            integration_success = response.status_code == 200
            
            if integration_success:
                data = response.json()
                
                # Check that all services contributed to the response
                has_terrain = "terrain_heatmap" in data
                has_camera = "travel_corridors" in data
                has_config = "stand_rating" in data
                
                if has_terrain and has_camera and has_config:
                    print("   ✅ Full service integration working")
                else:
                    print("   ⚠️  Partial service integration")
                    integration_success = False
            else:
                print(f"   ❌ Service integration failed: {response.status_code}")
            
            self.test_results["service_integration"] = {
                "success": integration_success,
                "has_terrain": has_terrain if integration_success else False,
                "has_camera": has_camera if integration_success else False,
                "has_config": has_config if integration_success else False
            }
            
        except Exception as e:
            print(f"   ❌ Integration test failed: {e}")
            self.test_results["service_integration"] = {
                "success": False,
                "error": str(e)
            }
    
    def _test_docker_performance(self):
        """Test performance in Docker environment."""
        print("\n⚡ Testing Docker Performance")
        
        try:
            # Test response times
            request_data = {
                "lat": 40.0,
                "lon": -74.0,
                "date_time": "2025-08-24T19:30:00Z",
                "season": "rut",
                "fast_mode": True
            }
            
            response_times = []
            for i in range(3):
                start_time = time.time()
                response = requests.post(
                    "http://localhost:8000/predict",
                    json=request_data,
                    timeout=30
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    response_times.append(response_time)
            
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                
                print(f"   ✅ Average response time: {avg_time:.2f}s")
                print(f"   ✅ Maximum response time: {max_time:.2f}s")
                
                # Performance should be reasonable in Docker
                performance_success = avg_time < 30.0 and max_time < 45.0
                
                if performance_success:
                    print("   ✅ Performance targets met")
                else:
                    print("   ⚠️  Performance slower than expected")
            else:
                performance_success = False
                avg_time = max_time = None
                print("   ❌ No successful responses for performance test")
            
            self.test_results["docker_performance"] = {
                "success": performance_success,
                "avg_response_time": avg_time,
                "max_response_time": max_time,
                "response_count": len(response_times)
            }
            
        except Exception as e:
            print(f"   ❌ Performance test failed: {e}")
            self.test_results["docker_performance"] = {
                "success": False,
                "error": str(e)
            }
    
    def _run_integration_tests(self):
        """Run integration tests."""
        self._test_service_integration()
        self._test_refactored_architecture()
    
    def _run_e2e_tests(self):
        """Run end-to-end tests."""
        self._test_container_health()
        self._test_api_functionality()
        self._test_frontend_accessibility()
        self._test_service_integration()
    
    def _run_performance_tests(self):
        """Run performance tests."""
        self._test_docker_performance()
    
    def _all_tests_passed(self) -> bool:
        """Check if all tests passed."""
        return all(result.get("success", False) for result in self.test_results.values())
    
    def _print_test_summary(self):
        """Print test summary."""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "=" * 70)
        print("🐳 DOCKER TEST SUMMARY")
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
            print(f"  {status} {test_name}")
            
            # Print additional details for failures
            if not result.get("success", False) and "error" in result:
                print(f"    Error: {result['error']}")
        
        print(f"\n🐳 DOCKER DEPLOYMENT STATUS:")
        print(f"  Architecture: Service-based (refactored)")
        print(f"  Container Health: {'✅ Healthy' if self.test_results.get('container_health', {}).get('success', False) else '❌ Issues'}")
        print(f"  API Functionality: {'✅ Working' if self.test_results.get('api_functionality', {}).get('success', False) else '❌ Issues'}")
        print(f"  Frontend Access: {'✅ Working' if self.test_results.get('frontend_accessibility', {}).get('success', False) else '❌ Issues'}")
        
        if self._all_tests_passed():
            print(f"\n🎉 ALL DOCKER TESTS PASSED! Refactored app ready for deployment.")
        else:
            print(f"\n⚠️  Some Docker tests failed. Review results above.")
    
    def _cleanup_containers(self):
        """Clean up Docker containers."""
        print("\n🧹 Cleaning up Docker containers...")
        
        try:
            subprocess.run(["docker-compose", "down"], cwd=self.project_root, capture_output=True)
            print("   ✅ Containers stopped and removed")
        except Exception as e:
            print(f"   ⚠️  Cleanup error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Docker Test Runner for Deer Prediction App")
    parser.add_argument("--quick", action="store_true", help="Run quick validation tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    parser.add_argument("--build", action="store_true", help="Force rebuild containers")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't clean up containers after tests")
    
    args = parser.parse_args()
    
    # Determine test type
    test_type = "all"  # default
    if args.quick:
        test_type = "quick"
    elif args.integration:
        test_type = "integration"
    elif args.e2e:
        test_type = "e2e"
    elif args.performance:
        test_type = "performance"
    
    # Run tests
    runner = DockerTestRunner()
    success = runner.run_tests(
        test_type=test_type,
        force_build=args.build,
        cleanup=not args.no_cleanup
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
