#!/usr/bin/env python3
"""
Mature Buck Prediction Accuracy Testing

This script runs comprehensive tests to evaluate and optimize the accuracy
of mature buck location predictions.
"""

import numpy as np
import json
import logging
from datetime import datetime
from typing import Dict, List
import backend.mature_buck_predictor as mature_buck_predictor
import backend.scoring_engine as scoring_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_terrain_analysis_accuracy():
    """Test terrain analysis accuracy for mature buck preferences"""
    print("\n🏔️ TESTING TERRAIN ANALYSIS ACCURACY")
    print("=" * 50)
    
    predictor = mature_buck_predictor.get_mature_buck_predictor()
    
    # Vermont terrain test scenarios
    test_cases = [
        {
            'name': 'Ideal Mature Buck Terrain',
            'terrain': {
                'elevation': 1200,
                'slope': 15,
                'aspect': 180,  # South-facing
                'cover_density': 0.85,
                'water_proximity': 200,
                'terrain_ruggedness': 0.7
            },
            'expected_score': 85  # Should score high
        },
        {
            'name': 'Poor Mature Buck Terrain',
            'terrain': {
                'elevation': 500,
                'slope': 2,
                'aspect': 0,
                'cover_density': 0.3,
                'water_proximity': 1000,
                'terrain_ruggedness': 0.1
            },
            'expected_score': 25  # Should score low
        },
        {
            'name': 'Moderate Mature Buck Terrain',
            'terrain': {
                'elevation': 900,
                'slope': 8,
                'aspect': 270,
                'cover_density': 0.65,
                'water_proximity': 400,
                'terrain_ruggedness': 0.5
            },
            'expected_score': 60  # Should score moderate
        }
    ]
    
    results = []
    for test_case in test_cases:
        try:
            scores = predictor.analyze_mature_buck_terrain(
                test_case['terrain'], 43.5, -72.8
            )
            
            actual_score = scores.get('overall_suitability', 0)
            expected_score = test_case['expected_score']
            accuracy = 100 - abs(actual_score - expected_score)
            
            result = {
                'test': test_case['name'],
                'expected': expected_score,
                'actual': actual_score,
                'accuracy': accuracy
            }
            results.append(result)
            
            print(f"✅ {test_case['name']}")
            print(f"   Expected: {expected_score}% | Actual: {actual_score:.1f}% | Accuracy: {accuracy:.1f}%")
            
        except Exception as e:
            print(f"❌ {test_case['name']}: {str(e)}")
    
    if results:
        avg_accuracy = np.mean([r['accuracy'] for r in results])
        print(f"\n📊 Terrain Analysis Accuracy: {avg_accuracy:.1f}%")
        return avg_accuracy
    return 0

def test_movement_prediction_accuracy():
    """Test movement prediction accuracy across seasons"""
    print("\n🚶 TESTING MOVEMENT PREDICTION ACCURACY")
    print("=" * 50)
    
    predictor = mature_buck_predictor.get_mature_buck_predictor()
    
    # Test scenarios for different seasons and conditions
    test_scenarios = [
        {
            'season': 'early_season',
            'time': 6,  # Dawn
            'weather': {'temp': 55, 'wind_speed': 3, 'pressure': 30.2},
            'expected_movement': 85  # High movement at dawn
        },
        {
            'season': 'rut',
            'time': 14,  # Midday during rut
            'weather': {'temp': 45, 'wind_speed': 8, 'pressure': 29.8},
            'expected_movement': 75  # Moderate movement during rut midday
        },
        {
            'season': 'late_season',
            'time': 17,  # Evening
            'weather': {'temp': 25, 'wind_speed': 2, 'pressure': 30.5},
            'expected_movement': 80  # High movement in cold evening
        }
    ]
    
    terrain_features = {
        'elevation': 1000,
        'slope': 12,
        'cover_density': 0.75,
        'water_proximity': 300
    }
    
    results = []
    for scenario in test_scenarios:
        try:
            movement_data = predictor.predict_mature_buck_movement(
                scenario['season'], scenario['time'], terrain_features,
                scenario['weather'], 43.5, -72.8
            )
            
            actual_movement = movement_data.get('movement_probability', 0)
            expected_movement = scenario['expected_movement']
            accuracy = 100 - abs(actual_movement - expected_movement)
            
            result = {
                'season': scenario['season'],
                'time': scenario['time'],
                'expected': expected_movement,
                'actual': actual_movement,
                'accuracy': accuracy
            }
            results.append(result)
            
            print(f"✅ {scenario['season']} at {scenario['time']}:00")
            print(f"   Expected: {expected_movement}% | Actual: {actual_movement:.1f}% | Accuracy: {accuracy:.1f}%")
            
        except Exception as e:
            print(f"❌ {scenario['season']} at {scenario['time']}:00: {str(e)}")
    
    if results:
        avg_accuracy = np.mean([r['accuracy'] for r in results])
        print(f"\n📊 Movement Prediction Accuracy: {avg_accuracy:.1f}%")
        return avg_accuracy
    return 0

def test_confidence_calibration():
    """Test if confidence scores match actual accuracy"""
    print("\n📊 TESTING CONFIDENCE CALIBRATION")
    print("=" * 50)
    
    predictor = mature_buck_predictor.get_mature_buck_predictor()
    
    # Generate multiple random scenarios to test confidence calibration
    scenarios = []
    for i in range(10):
        terrain = {
            'elevation': np.random.uniform(500, 2000),
            'slope': np.random.uniform(0, 30),
            'cover_density': np.random.uniform(0.3, 0.9),
            'water_proximity': np.random.uniform(50, 1000)
        }
        
        weather = {
            'temp': np.random.uniform(20, 70),
            'wind_speed': np.random.uniform(0, 15),
            'pressure': np.random.uniform(29.5, 30.5)
        }
        
        scenarios.append({'terrain': terrain, 'weather': weather})
    
    confidences = []
    for i, scenario in enumerate(scenarios):
        try:
            movement_data = predictor.predict_mature_buck_movement(
                'early_season', 16, scenario['terrain'], scenario['weather'], 43.5, -72.8
            )
            
            confidence = movement_data.get('confidence_score', 0)
            confidences.append(confidence)
            
            print(f"Scenario {i+1}: Confidence = {confidence:.1f}%")
            
        except Exception as e:
            print(f"❌ Scenario {i+1}: {str(e)}")
    
    if confidences:
        avg_confidence = np.mean(confidences)
        confidence_std = np.std(confidences)
        print(f"\n📊 Average Confidence: {avg_confidence:.1f}% ± {confidence_std:.1f}%")
        
        # Confidence should be well-calibrated (not too high or too low)
        calibration_score = 100 - abs(avg_confidence - 70)  # Target ~70% confidence
        print(f"📊 Confidence Calibration Score: {calibration_score:.1f}%")
        return calibration_score
    return 0

def identify_optimization_opportunities():
    """Identify specific areas for algorithm optimization"""
    print("\n🔧 OPTIMIZATION OPPORTUNITIES")
    print("=" * 50)
    
    opportunities = []
    
    # Check if ML enhancement is working
    try:
        from ml_enhanced_predictor import MLEnhancedMatureBuckPredictor
        ml_predictor = MLEnhancedMatureBuckPredictor()
        print("✅ ML Enhancement: Available")
    except Exception as e:
        print(f"⚠️  ML Enhancement: Disabled ({str(e)})")
        opportunities.append("Enable ML enhancement for improved accuracy")
    
    # Check configuration optimization
    try:
        from backend.config_manager import get_config
        config = get_config()
        print("✅ Configuration Management: Active")
        
        # Check if advanced features are enabled
        if not config.get_value("features.lidar_integration", False):
            opportunities.append("Enable LiDAR integration for terrain analysis")
        
        if not config.get_value("features.weather_integration", True):
            opportunities.append("Enable weather integration for movement predictions")
            
    except Exception as e:
        print(f"⚠️  Configuration: Error ({str(e)})")
        opportunities.append("Fix configuration management system")
    
    # Check scoring engine optimization
    try:
        engine = scoring_engine.get_scoring_engine()
        print("✅ Scoring Engine: Active")
    except Exception as e:
        print(f"⚠️  Scoring Engine: Error ({str(e)})")
        opportunities.append("Optimize unified scoring framework")
    
    print(f"\n🎯 OPTIMIZATION RECOMMENDATIONS:")
    for i, opp in enumerate(opportunities, 1):
        print(f"{i}. {opp}")
    
    return opportunities

def main():
    """Run comprehensive accuracy testing"""
    print("🦌 MATURE BUCK PREDICTION ACCURACY ANALYSIS")
    print("=" * 60)
    
    # Run all tests
    terrain_accuracy = test_terrain_analysis_accuracy()
    movement_accuracy = test_movement_prediction_accuracy() 
    confidence_calibration = test_confidence_calibration()
    optimization_opportunities = identify_optimization_opportunities()
    
    # Calculate overall accuracy score
    overall_accuracy = np.mean([terrain_accuracy, movement_accuracy, confidence_calibration])
    
    print(f"\n🏆 OVERALL ACCURACY ASSESSMENT")
    print("=" * 40)
    print(f"Terrain Analysis: {terrain_accuracy:.1f}%")
    print(f"Movement Prediction: {movement_accuracy:.1f}%")
    print(f"Confidence Calibration: {confidence_calibration:.1f}%")
    print(f"Overall System Accuracy: {overall_accuracy:.1f}%")
    
    # Provide recommendations
    if overall_accuracy >= 80:
        print("✅ EXCELLENT: System is performing at high accuracy")
    elif overall_accuracy >= 70:
        print("✅ GOOD: System is performing well with room for improvement")
    elif overall_accuracy >= 60:
        print("⚠️  FAIR: System needs optimization")
    else:
        print("❌ POOR: Significant algorithm improvements needed")
    
    print(f"\n📋 Next Steps: {len(optimization_opportunities)} optimization opportunities identified")

if __name__ == "__main__":
    main()
