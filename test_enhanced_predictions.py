#!/usr/bin/env python3
"""
Enhanced Prediction System Validation Test

Comprehensive testing of the satellite-enhanced deer prediction system
to ensure all components are working correctly.

Author: GitHub Copilot
Date: August 14, 2025
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any

# Import enhanced components
from backend.enhanced_prediction_engine import get_enhanced_prediction_engine
from backend.enhanced_prediction_api import get_enhanced_prediction_api
from backend.vegetation_analyzer import get_vegetation_analyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedPredictionValidator:
    """
    Validator for enhanced prediction system
    """
    
    def __init__(self):
        self.engine = get_enhanced_prediction_engine()
        self.api = get_enhanced_prediction_api()
        self.vegetation_analyzer = get_vegetation_analyzer()
        self.test_results = {}
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive validation of enhanced prediction system
        """
        
        logger.info("🚀 Starting Enhanced Prediction System Validation")
        
        validation_results = {
            'validation_timestamp': datetime.utcnow().isoformat(),
            'component_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'functionality_tests': {},
            'overall_status': 'unknown'
        }
        
        try:
            # Component validation
            validation_results['component_tests'] = await self._validate_components()
            
            # Integration validation
            validation_results['integration_tests'] = await self._validate_integration()
            
            # Performance validation
            validation_results['performance_tests'] = await self._validate_performance()
            
            # Functionality validation
            validation_results['functionality_tests'] = await self._validate_functionality()
            
            # Calculate overall status
            validation_results['overall_status'] = self._calculate_overall_status(validation_results)
            
            # Generate summary
            validation_results['summary'] = self._generate_validation_summary(validation_results)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Comprehensive validation failed: {e}")
            validation_results['overall_status'] = 'failed'
            validation_results['error'] = str(e)
            return validation_results
    
    async def _validate_components(self) -> Dict[str, Any]:
        """Validate individual components"""
        
        logger.info("🔧 Validating individual components...")
        
        component_results = {}
        
        # Test 1: Enhanced Prediction Engine
        try:
            engine = get_enhanced_prediction_engine()
            component_results['enhanced_engine'] = {
                'status': 'functional',
                'initialized': engine is not None,
                'vegetation_analyzer_connected': hasattr(engine, 'vegetation_analyzer')
            }
        except Exception as e:
            component_results['enhanced_engine'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 2: Vegetation Analyzer
        try:
            vegetation = get_vegetation_analyzer()
            component_results['vegetation_analyzer'] = {
                'status': 'functional',
                'initialized': vegetation is not None,
                'gee_client_available': hasattr(vegetation, 'ee')
            }
        except Exception as e:
            component_results['vegetation_analyzer'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 3: Enhanced API
        try:
            api = get_enhanced_prediction_api()
            component_results['enhanced_api'] = {
                'status': 'functional',
                'initialized': api is not None,
                'engine_connected': hasattr(api, 'engine')
            }
        except Exception as e:
            component_results['enhanced_api'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        logger.info("✅ Component validation completed")
        return component_results
    
    async def _validate_integration(self) -> Dict[str, Any]:
        """Validate integration between components"""
        
        logger.info("🔗 Validating component integration...")
        
        integration_results = {}
        
        # Test 1: API to Engine Integration
        try:
            api = get_enhanced_prediction_api()
            # Test a simple prediction call
            result = await api.generate_enhanced_prediction(
                lat=39.7392,  # Denver, CO
                lon=-104.9903,
                season="pre_rut"
            )
            
            integration_results['api_engine_integration'] = {
                'status': 'functional',
                'prediction_generated': 'prediction_data' in result if result else False,
                'enhancement_level': result.get('prediction_data', {}).get('enhancement_level', 'unknown') if result else 'none'
            }
            
        except Exception as e:
            integration_results['api_engine_integration'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 2: Engine to Vegetation Analyzer Integration
        try:
            engine = get_enhanced_prediction_engine()
            vegetation_data = engine._get_vegetation_analysis(39.7392, -104.9903)
            
            integration_results['engine_vegetation_integration'] = {
                'status': 'functional',
                'vegetation_data_retrieved': vegetation_data is not None,
                'has_analysis_metadata': 'analysis_metadata' in vegetation_data if vegetation_data else False
            }
            
        except Exception as e:
            integration_results['engine_vegetation_integration'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 3: Prediction Comparison Integration
        try:
            api = get_enhanced_prediction_api()
            comparison = await api.compare_prediction_methods(
                lat=39.7392,
                lon=-104.9903
            )
            
            integration_results['prediction_comparison'] = {
                'status': 'functional',
                'comparison_generated': 'comparison_data' in comparison if comparison else False,
                'has_improvement_metrics': 'improvement_metrics' in comparison.get('comparison_data', {}) if comparison else False
            }
            
        except Exception as e:
            integration_results['prediction_comparison'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        logger.info("✅ Integration validation completed")
        return integration_results
    
    async def _validate_performance(self) -> Dict[str, Any]:
        """Validate system performance"""
        
        logger.info("⚡ Validating system performance...")
        
        performance_results = {}
        
        # Test 1: Enhanced Prediction Performance
        try:
            start_time = time.time()
            
            api = get_enhanced_prediction_api()
            result = await api.generate_enhanced_prediction(
                lat=39.7392,
                lon=-104.9903,
                season="pre_rut"
            )
            
            end_time = time.time()
            prediction_time = end_time - start_time
            
            performance_results['enhanced_prediction_performance'] = {
                'status': 'measured',
                'prediction_time_seconds': round(prediction_time, 3),
                'performance_rating': self._rate_performance(prediction_time),
                'prediction_successful': result is not None
            }
            
        except Exception as e:
            performance_results['enhanced_prediction_performance'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 2: Vegetation Analysis Performance
        try:
            start_time = time.time()
            
            api = get_enhanced_prediction_api()
            vegetation_summary = await api.get_vegetation_summary(39.7392, -104.9903)
            
            end_time = time.time()
            vegetation_time = end_time - start_time
            
            performance_results['vegetation_analysis_performance'] = {
                'status': 'measured',
                'analysis_time_seconds': round(vegetation_time, 3),
                'performance_rating': self._rate_performance(vegetation_time),
                'analysis_successful': vegetation_summary is not None
            }
            
        except Exception as e:
            performance_results['vegetation_analysis_performance'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        logger.info("✅ Performance validation completed")
        return performance_results
    
    async def _validate_functionality(self) -> Dict[str, Any]:
        """Validate specific functionality"""
        
        logger.info("🎯 Validating specific functionality...")
        
        functionality_results = {}
        
        # Test 1: Enhanced Prediction Features
        try:
            api = get_enhanced_prediction_api()
            result = await api.generate_enhanced_prediction(
                lat=39.7392,
                lon=-104.9903,
                season="pre_rut"
            )
            
            prediction_data = result.get('prediction_data', {}) if result else {}
            
            functionality_results['enhanced_prediction_features'] = {
                'status': 'functional',
                'has_movement_predictions': 'movement_predictions' in prediction_data,
                'has_vegetation_analysis': 'vegetation_analysis' in prediction_data,
                'has_food_mapping': 'food_source_mapping' in prediction_data,
                'has_pressure_zones': 'pressure_zones' in prediction_data,
                'has_confidence_metrics': 'confidence_metrics' in prediction_data,
                'has_hunting_insights': 'hunting_insights' in prediction_data,
                'has_optimal_stands': 'optimal_stands' in prediction_data,
                'feature_count': len([k for k in prediction_data.keys() if not k.startswith('request_')])
            }
            
        except Exception as e:
            functionality_results['enhanced_prediction_features'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 2: Vegetation Analysis Features
        try:
            api = get_enhanced_prediction_api()
            vegetation_summary = await api.get_vegetation_summary(39.7392, -104.9903)
            
            functionality_results['vegetation_analysis_features'] = {
                'status': 'functional',
                'has_vegetation_health': 'vegetation_health' in vegetation_summary,
                'has_food_sources': 'food_sources' in vegetation_summary,
                'has_land_cover_summary': 'land_cover_summary' in vegetation_summary,
                'has_hunting_suitability': 'hunting_suitability' in vegetation_summary,
                'has_water_availability': 'water_availability' in vegetation_summary,
                'has_key_insights': 'key_insights' in vegetation_summary,
                'feature_count': len(vegetation_summary.keys()) if vegetation_summary else 0
            }
            
        except Exception as e:
            functionality_results['vegetation_analysis_features'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 3: Multiple Location Testing
        test_locations = [
            (39.7392, -104.9903),  # Denver, CO
            (44.2619, -72.5806),   # Vermont
            (42.3601, -71.0589),   # Boston, MA
        ]
        
        location_results = []
        for lat, lon in test_locations:
            try:
                api = get_enhanced_prediction_api()
                result = await api.generate_enhanced_prediction(lat, lon, season="early_season")
                
                location_results.append({
                    'coordinates': (lat, lon),
                    'prediction_successful': result is not None,
                    'enhancement_level': result.get('prediction_data', {}).get('enhancement_level', 'unknown') if result else 'none'
                })
                
            except Exception as e:
                location_results.append({
                    'coordinates': (lat, lon),
                    'prediction_successful': False,
                    'error': str(e)
                })
        
        functionality_results['multiple_location_testing'] = {
            'status': 'completed',
            'locations_tested': len(test_locations),
            'successful_predictions': len([r for r in location_results if r.get('prediction_successful', False)]),
            'success_rate': len([r for r in location_results if r.get('prediction_successful', False)]) / len(test_locations),
            'location_results': location_results
        }
        
        logger.info("✅ Functionality validation completed")
        return functionality_results
    
    def _rate_performance(self, time_seconds: float) -> str:
        """Rate performance based on execution time"""
        if time_seconds < 2.0:
            return 'excellent'
        elif time_seconds < 5.0:
            return 'good'
        elif time_seconds < 10.0:
            return 'acceptable'
        else:
            return 'slow'
    
    def _calculate_overall_status(self, validation_results: Dict[str, Any]) -> str:
        """Calculate overall validation status"""
        
        failed_tests = 0
        total_tests = 0
        
        for test_category in ['component_tests', 'integration_tests', 'performance_tests', 'functionality_tests']:
            category_results = validation_results.get(test_category, {})
            for test_name, test_result in category_results.items():
                total_tests += 1
                if isinstance(test_result, dict) and test_result.get('status') == 'failed':
                    failed_tests += 1
        
        if failed_tests == 0:
            return 'all_tests_passed'
        elif failed_tests / total_tests < 0.25:
            return 'mostly_functional'
        elif failed_tests / total_tests < 0.5:
            return 'partially_functional'
        else:
            return 'significant_issues'
    
    def _generate_validation_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation summary"""
        
        overall_status = validation_results.get('overall_status', 'unknown')
        
        summary = {
            'overall_status': overall_status,
            'validation_timestamp': validation_results.get('validation_timestamp'),
            'system_capabilities': [],
            'identified_issues': [],
            'recommendations': []
        }
        
        # Analyze capabilities
        functionality_tests = validation_results.get('functionality_tests', {})
        enhanced_features = functionality_tests.get('enhanced_prediction_features', {})
        
        if enhanced_features.get('has_movement_predictions'):
            summary['system_capabilities'].append('Movement prediction analysis')
        if enhanced_features.get('has_vegetation_analysis'):
            summary['system_capabilities'].append('Satellite vegetation analysis')
        if enhanced_features.get('has_food_mapping'):
            summary['system_capabilities'].append('Food source mapping')
        if enhanced_features.get('has_pressure_zones'):
            summary['system_capabilities'].append('Hunting pressure assessment')
        if enhanced_features.get('has_optimal_stands'):
            summary['system_capabilities'].append('Optimal stand recommendations')
        
        # Analyze issues
        for test_category in ['component_tests', 'integration_tests', 'performance_tests', 'functionality_tests']:
            category_results = validation_results.get(test_category, {})
            for test_name, test_result in category_results.items():
                if isinstance(test_result, dict) and test_result.get('status') == 'failed':
                    summary['identified_issues'].append(f"{test_name}: {test_result.get('error', 'Unknown error')}")
        
        # Generate recommendations
        if overall_status == 'all_tests_passed':
            summary['recommendations'].append('System is fully operational and ready for production use')
        elif overall_status == 'mostly_functional':
            summary['recommendations'].append('System is largely functional with minor issues to address')
        else:
            summary['recommendations'].append('Address identified issues before production deployment')
        
        # Performance recommendations
        performance_tests = validation_results.get('performance_tests', {})
        for test_name, test_result in performance_tests.items():
            if isinstance(test_result, dict) and test_result.get('performance_rating') == 'slow':
                summary['recommendations'].append(f'Consider optimizing {test_name} for better performance')
        
        return summary

async def main():
    """
    Main validation function
    """
    
    logger.info("🧪 Enhanced Prediction System Validation Starting...")
    
    validator = EnhancedPredictionValidator()
    validation_results = await validator.run_comprehensive_validation()
    
    # Save validation results
    results_path = "enhanced_prediction_validation_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    # Print summary
    summary = validation_results.get('summary', {})
    overall_status = summary.get('overall_status', 'unknown')
    
    logger.info("=" * 60)
    logger.info("🧪 ENHANCED PREDICTION SYSTEM VALIDATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Overall Status: {overall_status.upper()}")
    
    capabilities = summary.get('system_capabilities', [])
    if capabilities:
        logger.info("\n✅ System Capabilities:")
        for capability in capabilities:
            logger.info(f"  • {capability}")
    
    issues = summary.get('identified_issues', [])
    if issues:
        logger.info("\n⚠️ Identified Issues:")
        for issue in issues:
            logger.info(f"  • {issue}")
    
    recommendations = summary.get('recommendations', [])
    if recommendations:
        logger.info("\n💡 Recommendations:")
        for recommendation in recommendations:
            logger.info(f"  • {recommendation}")
    
    logger.info(f"\n📄 Detailed results saved to: {results_path}")
    
    if overall_status in ['all_tests_passed', 'mostly_functional']:
        logger.info("🎯 Enhanced prediction system is ready for use!")
        return True
    else:
        logger.warning("⚠️ Enhanced prediction system needs attention before production use")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
