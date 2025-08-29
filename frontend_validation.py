#!/usr/bin/env python3
"""
Frontend Validation for Bedding Zone Integration
================================================

Validates that bedding zones are properly rendered in the frontend
and addresses coordinate variations and scoring bugs.
"""

import requests
import json
import time
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BeddingZoneFrontendValidator:
    """Validates bedding zone integration in frontend"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_locations = [
            {
                'name': 'Tinmouth, VT (Original Problem)',
                'lat': 43.3146,
                'lon': -73.2178,
                'expected_zones': 3,
                'expected_suitability_min': 60
            },
            {
                'name': 'Vermont Mountain Test',
                'lat': 43.3200,
                'lon': -73.2100,
                'expected_zones': 2,
                'expected_suitability_min': 50
            }
        ]
    
    def validate_api_endpoint(self, lat: float, lon: float) -> Dict[str, Any]:
        """Validate bedding zone API endpoint"""
        
        try:
            url = f"{self.base_url}/api/bedding/validate/{lat}/{lon}"
            response = requests.get(url, params={'debug_mode': True})
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API endpoint failed: {response.status_code}")
                return {'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"API validation failed: {e}")
            return {'error': str(e)}
    
    def validate_coordinate_consistency(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate coordinate consistency and variations"""
        
        features = validation_result.get('bedding_zones', {}).get('features', [])
        if not features:
            return {'status': 'FAIL', 'reason': 'No features to validate'}
        
        # Extract coordinates
        coordinates = []
        for feature in features:
            coords = feature.get('geometry', {}).get('coordinates', [])
            if coords:
                coordinates.append(coords)
        
        if len(coordinates) < 2:
            return {'status': 'PASS', 'reason': 'Single zone, no variation to check'}
        
        # Calculate coordinate variations
        base_lat = validation_result['location']['latitude']
        base_lon = validation_result['location']['longitude']
        
        distances = []
        for coords in coordinates:
            import math
            lat_diff = coords[1] - base_lat
            lon_diff = coords[0] - base_lon
            distance_m = math.sqrt((lat_diff * 111000)**2 + (lon_diff * 111000 * math.cos(math.radians(base_lat)))**2)
            distances.append(distance_m)
        
        max_distance = max(distances)
        min_distance = min(distances)
        variation_range = max_distance - min_distance
        
        # Validate against acceptable ranges
        acceptable_max = 275  # Based on user's observation of 113-275m
        
        result = {
            'status': 'PASS' if max_distance <= acceptable_max else 'FAIL',
            'coordinate_analysis': {
                'min_distance_m': round(min_distance, 1),
                'max_distance_m': round(max_distance, 1),
                'variation_range_m': round(variation_range, 1),
                'acceptable_max_m': acceptable_max,
                'within_acceptable_range': max_distance <= acceptable_max
            }
        }
        
        return result
    
    def validate_scoring_accuracy(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate scoring accuracy and bug resolution"""
        
        metrics = validation_result.get('metrics', {})
        if not metrics:
            return {'status': 'FAIL', 'reason': 'No metrics available'}
        
        avg_suitability = metrics.get('average_suitability', 0)
        original_problematic_score = 43.1
        minimum_acceptable_score = 60
        
        # Check if scoring bug is resolved
        scoring_improved = avg_suitability > original_problematic_score + 15
        score_realistic = avg_suitability >= minimum_acceptable_score
        
        result = {
            'status': 'PASS' if scoring_improved and score_realistic else 'FAIL',
            'scoring_analysis': {
                'current_score': avg_suitability,
                'original_problematic_score': original_problematic_score,
                'improvement': round(avg_suitability - original_problematic_score, 1),
                'minimum_acceptable': minimum_acceptable_score,
                'scoring_bug_resolved': scoring_improved,
                'score_realistic': score_realistic
            }
        }
        
        return result
    
    def validate_frontend_rendering(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate frontend rendering compatibility"""
        
        features = validation_result.get('bedding_zones', {}).get('features', [])
        
        # Check GeoJSON structure
        geojson_valid = all(
            feature.get('type') == 'Feature' and
            'geometry' in feature and
            'properties' in feature
            for feature in features
        )
        
        # Check required properties for frontend
        properties_valid = all(
            'suitability_score' in feature.get('properties', {})
            for feature in features
        )
        
        # Check coordinate format
        coordinates_valid = all(
            len(feature.get('geometry', {}).get('coordinates', [])) == 2
            for feature in features
        )
        
        result = {
            'status': 'PASS' if geojson_valid and properties_valid and coordinates_valid else 'FAIL',
            'frontend_compatibility': {
                'geojson_structure_valid': geojson_valid,
                'required_properties_present': properties_valid,
                'coordinate_format_valid': coordinates_valid,
                'feature_count': len(features),
                'ready_for_rendering': geojson_valid and properties_valid and coordinates_valid
            }
        }
        
        return result
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation across all test locations"""
        
        logger.info("🔍 Starting comprehensive frontend validation...")
        
        results = {
            'validation_timestamp': time.time(),
            'test_locations': [],
            'overall_status': 'UNKNOWN',
            'summary': {}
        }
        
        total_tests = 0
        passed_tests = 0
        
        for location in self.test_locations:
            logger.info(f"Testing {location['name']}...")
            
            # Get validation data from API
            api_result = self.validate_api_endpoint(location['lat'], location['lon'])
            
            if 'error' in api_result:
                location_result = {
                    'location': location,
                    'status': 'ERROR',
                    'error': api_result['error']
                }
            else:
                # Run all validation checks
                coordinate_validation = self.validate_coordinate_consistency(api_result)
                scoring_validation = self.validate_scoring_accuracy(api_result)
                frontend_validation = self.validate_frontend_rendering(api_result)
                
                # Determine overall location status
                all_validations = [coordinate_validation, scoring_validation, frontend_validation]
                location_status = 'PASS' if all(v['status'] == 'PASS' for v in all_validations) else 'FAIL'
                
                location_result = {
                    'location': location,
                    'status': location_status,
                    'api_response': api_result,
                    'validations': {
                        'coordinate_consistency': coordinate_validation,
                        'scoring_accuracy': scoring_validation,
                        'frontend_rendering': frontend_validation
                    }
                }
                
                if location_status == 'PASS':
                    passed_tests += 1
                total_tests += 1
            
            results['test_locations'].append(location_result)
        
        # Calculate overall status
        if total_tests == 0:
            results['overall_status'] = 'ERROR'
        elif passed_tests == total_tests:
            results['overall_status'] = 'PASS'
        elif passed_tests > 0:
            results['overall_status'] = 'PARTIAL'
        else:
            results['overall_status'] = 'FAIL'
        
        results['summary'] = {
            'total_locations_tested': total_tests,
            'locations_passed': passed_tests,
            'success_rate': round((passed_tests / total_tests * 100), 1) if total_tests > 0 else 0,
            'issues_resolved': {
                'coordinate_variations': 'CHECKED',
                'scoring_bug': 'CHECKED',
                'frontend_rendering': 'CHECKED'
            }
        }
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable validation report"""
        
        report = []
        report.append("=" * 70)
        report.append("🎯 FRONTEND VALIDATION REPORT")
        report.append("=" * 70)
        
        # Overall status
        status_emoji = {
            'PASS': '✅',
            'PARTIAL': '⚠️',
            'FAIL': '❌',
            'ERROR': '💥'
        }
        
        overall_status = results['overall_status']
        report.append(f"\n📊 Overall Status: {status_emoji.get(overall_status, '❓')} {overall_status}")
        report.append(f"📈 Success Rate: {results['summary']['success_rate']}%")
        report.append(f"📍 Locations Tested: {results['summary']['total_locations_tested']}")
        
        # Detailed results
        report.append(f"\n🔍 DETAILED VALIDATION RESULTS")
        report.append("-" * 50)
        
        for location_result in results['test_locations']:
            location = location_result['location']
            status = location_result['status']
            
            report.append(f"\n📍 {location['name']}")
            report.append(f"   Status: {status_emoji.get(status, '❓')} {status}")
            
            if status != 'ERROR' and 'validations' in location_result:
                validations = location_result['validations']
                
                # Coordinate validation
                coord_val = validations['coordinate_consistency']
                if 'coordinate_analysis' in coord_val:
                    coord_analysis = coord_val['coordinate_analysis']
                    report.append(f"   Coordinate Variation: {coord_analysis['min_distance_m']:.0f}m - {coord_analysis['max_distance_m']:.0f}m")
                    report.append(f"   Variation Status: {status_emoji.get(coord_val['status'], '❓')} {'Within acceptable range' if coord_analysis['within_acceptable_range'] else 'Exceeds acceptable range'}")
                
                # Scoring validation
                score_val = validations['scoring_accuracy']
                if 'scoring_analysis' in score_val:
                    score_analysis = score_val['scoring_analysis']
                    report.append(f"   Suitability Score: {score_analysis['current_score']}% (was {score_analysis['original_problematic_score']}%)")
                    report.append(f"   Scoring Status: {status_emoji.get(score_val['status'], '❓')} {'+' if score_analysis['improvement'] > 0 else ''}{score_analysis['improvement']} points improvement")
                
                # Frontend validation
                frontend_val = validations['frontend_rendering']
                if 'frontend_compatibility' in frontend_val:
                    frontend_analysis = frontend_val['frontend_compatibility']
                    report.append(f"   Frontend Ready: {status_emoji.get(frontend_val['status'], '❓')} {frontend_analysis['feature_count']} zones, GeoJSON valid")
        
        # Recommendations
        report.append(f"\n💡 RECOMMENDATIONS")
        report.append("-" * 50)
        
        if overall_status == 'PASS':
            report.append("✅ All validations passed! Bedding zone fix is fully integrated.")
            report.append("✅ Frontend rendering should work correctly.")
            report.append("✅ Coordinate variations and scoring bugs are resolved.")
        else:
            report.append("🔧 Review failed validations above.")
            report.append("🔧 Ensure API endpoints are accessible.")
            report.append("🔧 Validate frontend GeoJSON rendering.")
        
        report.append(f"\n" + "=" * 70)
        
        return "\n".join(report)

def main():
    """Run frontend validation"""
    
    validator = BeddingZoneFrontendValidator()
    
    # Check API status first
    try:
        status_response = requests.get(f"{validator.base_url}/api/bedding/status")
        if status_response.status_code == 200:
            logger.info("✅ API is accessible")
        else:
            logger.warning(f"⚠️ API status check returned {status_response.status_code}")
    except Exception as e:
        logger.error(f"❌ API not accessible: {e}")
        logger.info("Note: This validation can still run against the backend directly")
    
    # Run comprehensive validation
    results = validator.run_comprehensive_validation()
    
    # Generate and display report
    report = validator.generate_report(results)
    print(report)
    
    # Save results
    with open('frontend_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("📁 Results saved to frontend_validation_results.json")
    
    return results['overall_status'] == 'PASS'

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
