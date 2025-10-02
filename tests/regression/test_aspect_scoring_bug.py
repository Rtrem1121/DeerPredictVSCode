#!/usr/bin/env python3
"""
Test script to identify the aspect scoring bug.
This script tests detailed scoring for east-facing slopes to see where high scores are coming from.
"""

import sys
sys.path.append('/app')
from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor

def test_aspect_scoring_bug():
    predictor = EnhancedBeddingZonePredictor()
    
    # Mock data for east-facing slope (55.5°)
    gee_data = {
        'slope': 15.0,
        'aspect': 55.5,  # East-facing - should be heavily penalized
        'canopy_coverage': 0.7,
        'elevation': 400
    }
    
    osm_data = {
        'nearest_road_distance_m': 300
    }
    
    weather_data = {
        'wind_direction': 242,
        'temperature': 67.5,
        'wind_speed': 8
    }
    
    print('DETAILED SCORING TEST FOR EAST-FACING SLOPE:')
    print('=' * 50)
    
    suitability = predictor.evaluate_bedding_suitability(gee_data, osm_data, weather_data)
    
    print(f'ASPECT: {gee_data["aspect"]}° (East-facing)')
    print(f'EXPECTED: Low aspect score due to east-facing orientation')
    print()
    print(f'INDIVIDUAL SCORES:')
    for key, value in suitability['scores'].items():
        print(f'  {key}: {value:.1f}/100')
        
    print()
    print(f'OVERALL SCORE: {suitability["overall_score"]:.1f}/100')
    print(f'MEETS CRITERIA: {suitability["meets_criteria"]}')
    print()
    
    # Test the weights to see overall calculation
    weights = {
        "canopy": 0.25,
        "isolation": 0.25,
        "slope": 0.15,
        "aspect": 0.15,
        "wind_protection": 0.10,
        "thermal": 0.10
    }
    
    print('WEIGHTED SCORE BREAKDOWN:')
    total_weighted = 0
    for key, weight in weights.items():
        if key in suitability['scores']:
            weighted_score = suitability['scores'][key] * weight
            total_weighted += weighted_score
            print(f'  {key}: {suitability["scores"][key]:.1f} × {weight} = {weighted_score:.1f}')
    
    print(f'CALCULATED TOTAL: {total_weighted:.1f}')
    print(f'REPORTED TOTAL: {suitability["overall_score"]:.1f}')
    
    if abs(total_weighted - suitability["overall_score"]) > 0.1:
        print('❌ CALCULATION MISMATCH DETECTED!')
    else:
        print('✅ Calculation matches')

if __name__ == "__main__":
    test_aspect_scoring_bug()
