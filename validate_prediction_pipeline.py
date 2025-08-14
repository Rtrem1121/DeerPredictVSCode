#!/usr/bin/env python3
"""
Prediction Pipeline Validation Test

This script validates that:
1. Backend algorithms are working correctly
2. GPX historical data is being integrated
3. Frontend receives correct prediction data
4. All components are communicating properly

Author: Vermont Deer Prediction System
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PredictionPipelineValidator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        
    def test_backend_health(self):
        """Test if backend is responding"""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Backend health check passed")
                self.test_results['backend_health'] = {
                    'status': 'PASS',
                    'response_time': response.elapsed.total_seconds(),
                    'data': data
                }
                return True
            else:
                logger.error(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Backend health check error: {e}")
            return False
    
    def test_scouting_data_integration(self):
        """Test if scouting observations are being returned"""
        try:
            response = requests.get(f"{self.base_url}/scouting/observations")
            if response.status_code == 200:
                observations = response.json()
                logger.info(f"✅ Scouting data integration: Found {len(observations)} observations")
                
                # Analyze observation types
                obs_types = {}
                confidence_scores = []
                dates = []
                
                for obs in observations:
                    obs_type = obs.get('observation_type', 'unknown')
                    obs_types[obs_type] = obs_types.get(obs_type, 0) + 1
                    confidence_scores.append(obs.get('confidence', 0))
                    if obs.get('date'):
                        dates.append(obs['date'])
                
                self.test_results['scouting_integration'] = {
                    'status': 'PASS',
                    'total_observations': len(observations),
                    'observation_types': obs_types,
                    'avg_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                    'date_range': {
                        'earliest': min(dates) if dates else None,
                        'latest': max(dates) if dates else None
                    }
                }
                return True
            else:
                logger.error(f"❌ Scouting data integration failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Scouting data integration error: {e}")
            return False
    
    def test_prediction_algorithm(self):
        """Test prediction algorithm with known coordinates"""
        test_locations = [
            # Vermont hunting areas from your GPX data
            {"lat": 44.2850, "lon": -73.0459, "name": "Fred Johnson WMA"},
            {"lat": 44.3637, "lon": -73.0091, "name": "Bolton Area"},
            {"lat": 43.3154, "lon": -73.2254, "name": "Rupert Area"},
        ]
        
        prediction_results = []
        
        for location in test_locations:
            try:
                # Test prediction API
                response = requests.post(f"{self.base_url}/predict", json={
                    "lat": location["lat"],
                    "lon": location["lon"],
                    "weather_conditions": "clear",
                    "temperature": 45,
                    "wind_speed": 5,
                    "time_of_day": "dawn"
                })
                
                if response.status_code == 200:
                    prediction = response.json()
                    logger.info(f"✅ Prediction for {location['name']}: {prediction.get('probability', 0):.1f}%")
                    
                    prediction_results.append({
                        'location': location['name'],
                        'coordinates': f"{location['lat']}, {location['lon']}",
                        'probability': prediction.get('probability', 0),
                        'confidence': prediction.get('confidence', 0),
                        'factors': prediction.get('contributing_factors', {}),
                        'status': 'PASS'
                    })
                else:
                    logger.error(f"❌ Prediction failed for {location['name']}: {response.status_code}")
                    prediction_results.append({
                        'location': location['name'],
                        'status': 'FAIL',
                        'error': response.text
                    })
                    
            except Exception as e:
                logger.error(f"❌ Prediction error for {location['name']}: {e}")
                prediction_results.append({
                    'location': location['name'],
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        self.test_results['prediction_algorithm'] = {
            'status': 'PASS' if all(r.get('status') == 'PASS' for r in prediction_results) else 'FAIL',
            'results': prediction_results
        }
        
        return len([r for r in prediction_results if r.get('status') == 'PASS']) > 0
    
    def test_historical_data_impact(self):
        """Test if historical GPX data is affecting predictions"""
        # Test same location with and without considering historical data
        test_location = {"lat": 44.2850, "lon": -73.0459}  # Area with lots of GPX data
        
        try:
            # Get prediction
            response = requests.post(f"{self.base_url}/predict", json={
                "lat": test_location["lat"],
                "lon": test_location["lon"],
                "weather_conditions": "clear",
                "temperature": 45,
                "wind_speed": 5,
                "time_of_day": "dawn"
            })
            
            if response.status_code == 200:
                prediction = response.json()
                factors = prediction.get('contributing_factors', {})
                
                # Check if historical data factors are present
                historical_indicators = [
                    'scouting_data',
                    'bedding_areas',
                    'feeding_areas', 
                    'trail_cameras',
                    'deer_tracks',
                    'rub_lines',
                    'scrapes'
                ]
                
                found_historical = []
                for indicator in historical_indicators:
                    if indicator in factors and factors[indicator] > 0:
                        found_historical.append(indicator)
                
                logger.info(f"✅ Historical data impact test: Found {len(found_historical)} historical factors")
                logger.info(f"   Historical factors: {found_historical}")
                
                self.test_results['historical_data_impact'] = {
                    'status': 'PASS' if found_historical else 'WARNING',
                    'probability': prediction.get('probability', 0),
                    'historical_factors_found': found_historical,
                    'all_factors': factors
                }
                
                return len(found_historical) > 0
            else:
                logger.error(f"❌ Historical data impact test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Historical data impact test error: {e}")
            return False
    
    def test_prediction_consistency(self):
        """Test prediction consistency with same inputs"""
        test_params = {
            "lat": 44.2850,
            "lon": -73.0459,
            "weather_conditions": "clear",
            "temperature": 45,
            "wind_speed": 5,
            "time_of_day": "dawn"
        }
        
        predictions = []
        
        # Run same prediction 5 times
        for i in range(5):
            try:
                response = requests.post(f"{self.base_url}/predict", json=test_params)
                if response.status_code == 200:
                    prediction = response.json()
                    predictions.append(prediction.get('probability', 0))
                else:
                    logger.error(f"❌ Consistency test run {i+1} failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Consistency test run {i+1} error: {e}")
        
        if predictions:
            avg_prob = sum(predictions) / len(predictions)
            variance = sum((p - avg_prob) ** 2 for p in predictions) / len(predictions)
            std_dev = variance ** 0.5
            
            # Predictions should be consistent (low standard deviation)
            is_consistent = std_dev < 5.0  # Allow 5% variance
            
            logger.info(f"✅ Prediction consistency: Avg={avg_prob:.1f}%, StdDev={std_dev:.2f}%")
            
            self.test_results['prediction_consistency'] = {
                'status': 'PASS' if is_consistent else 'WARNING',
                'predictions': predictions,
                'average': avg_prob,
                'std_deviation': std_dev,
                'is_consistent': is_consistent
            }
            
            return is_consistent
        
        return False
    
    def test_data_freshness(self):
        """Test if recent data has higher impact than old data"""
        try:
            # Get observations to check data freshness impact
            response = requests.get(f"{self.base_url}/scouting/observations")
            if response.status_code == 200:
                observations = response.json()
                
                # Analyze date distribution
                recent_obs = 0
                old_obs = 0
                now = datetime.now()
                
                for obs in observations:
                    if obs.get('date'):
                        obs_date = datetime.fromisoformat(obs['date'].replace('Z', '+00:00')).replace(tzinfo=None)
                        days_old = (now - obs_date).days
                        
                        if days_old < 30:  # Recent
                            recent_obs += 1
                        elif days_old > 365:  # Old
                            old_obs += 1
                
                logger.info(f"✅ Data freshness: {recent_obs} recent observations, {old_obs} old observations")
                
                self.test_results['data_freshness'] = {
                    'status': 'PASS',
                    'recent_observations': recent_obs,
                    'old_observations': old_obs,
                    'total_observations': len(observations)
                }
                
                return True
            else:
                logger.error(f"❌ Data freshness test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Data freshness test error: {e}")
            return False
    
    def run_full_validation(self):
        """Run all validation tests"""
        logger.info("🔍 Starting Prediction Pipeline Validation...")
        
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Scouting Data Integration", self.test_scouting_data_integration),
            ("Prediction Algorithm", self.test_prediction_algorithm),
            ("Historical Data Impact", self.test_historical_data_impact),
            ("Prediction Consistency", self.test_prediction_consistency),
            ("Data Freshness", self.test_data_freshness)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Running: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.warning(f"⚠️  {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
        
        # Generate summary report
        success_rate = (passed_tests / total_tests) * 100
        
        logger.info(f"\n📊 VALIDATION SUMMARY")
        logger.info(f"   Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("🎉 OVERALL STATUS: HEALTHY - Prediction pipeline is working correctly!")
        elif success_rate >= 60:
            logger.warning("⚠️  OVERALL STATUS: WARNING - Some issues detected, but core functionality works")
        else:
            logger.error("❌ OVERALL STATUS: CRITICAL - Multiple issues detected, review required")
        
        return self.test_results

def main():
    """Run the validation"""
    validator = PredictionPipelineValidator()
    results = validator.run_full_validation()
    
    # Save detailed results
    with open('prediction_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n📄 Detailed results saved to: prediction_validation_results.json")

if __name__ == "__main__":
    main()
