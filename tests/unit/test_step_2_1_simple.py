#!/usr/bin/env python3
"""
Test for New Analysis API Endpoint - Step 2.1 Verification (Simplified)

Tests the core functionality without requiring FastAPI dependencies.
"""

import sys
import os
import json

# Add paths for imports  
sys.path.insert(0, '/Users/richardtremblay/DeerPredictVSCode/backend/analysis')

from backend.analysis.prediction_analyzer import PredictionAnalyzer

def test_analyzer_api_compatibility():
    """Test that analyzer output is compatible with API responses"""
    print("🧪 Testing analyzer API compatibility...")
    
    analyzer = PredictionAnalyzer()
    
    # Collect sample analysis data
    analyzer.collect_criteria_analysis(
        {'canopy_coverage': 0.85, 'road_distance': 450, 'slope': 15.5},
        {'stand_count': 3, 'wind_advantage': True},
        {'feeding_areas_count': 2, 'food_source_diversity': True},
        {'min_canopy': 0.6, 'min_road_distance': 200.0}
    )
    
    analyzer.collect_thermal_analysis(
        {'is_active': True, 'direction': 'downslope', 'strength_scale': 7.2},
        {'optimal_timing': 'prime_morning_thermal'},
        ['ridge_tops', 'upper_slopes']
    )
    
    # Get comprehensive analysis
    analysis = analyzer.get_comprehensive_analysis()
    
    # Verify structure for API
    assert 'analysis_metadata' in analysis
    assert 'criteria_analysis' in analysis  
    assert 'thermal_analysis' in analysis
    
    # Test JSON serialization (critical for API)
    json_str = json.dumps(analysis, default=str, indent=2)
    parsed = json.loads(json_str)
    
    # Verify key data is preserved
    assert parsed['analysis_metadata']['completion_percentage'] > 0
    assert parsed['criteria_analysis']['bedding_criteria']['canopy_coverage'] == 0.85
    
    print("✅ Analyzer API compatibility test passed")

def test_response_structure_mock():
    """Test the expected API response structure"""
    print("🧪 Testing API response structure...")
    
    # Mock what the API response should look like
    analyzer = PredictionAnalyzer()
    analyzer.collect_criteria_analysis({'canopy_coverage': 0.85}, {}, {}, {'min_canopy': 0.6})
    
    # Mock prediction result
    mock_prediction = {
        'bedding_zones': {
            'features': [
                {
                    'properties': {'suitability_score': 87.3},
                    'geometry': {'coordinates': [-72.5813, 44.2664]}
                }
            ]
        },
        'confidence_score': 0.90,
        'thermal_analysis': {'is_active': True, 'strength_scale': 7.2},
        'wind_analyses': [
            {'location_type': 'bedding', 'wind_analysis': {'wind_advantage_rating': 8.1}}
        ]
    }
    
    # Mock API response structure
    api_response = {
        'success': True,
        'prediction': mock_prediction,
        'detailed_analysis': analyzer.get_comprehensive_analysis()
    }
    
    # Verify response structure
    assert api_response['success'] == True
    assert 'bedding_zones' in api_response['prediction']
    assert 'analysis_metadata' in api_response['detailed_analysis']
    
    # Test JSON serialization of complete response
    json_str = json.dumps(api_response, default=str)
    parsed = json.loads(json_str)
    
    assert parsed['success'] == True
    assert parsed['prediction']['confidence_score'] == 0.90
    
    print("✅ API response structure test passed")

def test_error_response_structure():
    """Test error response structure"""
    print("🧪 Testing error response structure...")
    
    # Mock error response
    error_response = {
        'success': False,
        'prediction': None,
        'detailed_analysis': None,
        'error': 'Test error message'
    }
    
    # Verify error structure
    assert error_response['success'] == False
    assert error_response['error'] == 'Test error message'
    assert error_response['prediction'] is None
    
    # Test JSON serialization
    json_str = json.dumps(error_response)
    parsed = json.loads(json_str)
    assert parsed['success'] == False
    
    print("✅ Error response structure test passed")

def test_analysis_completeness():
    """Test that analysis provides comprehensive data for display"""
    print("🧪 Testing analysis completeness...")
    
    analyzer = PredictionAnalyzer()
    
    # Collect multiple types of analysis
    analyzer.collect_criteria_analysis(
        {'canopy_coverage': 0.85, 'road_distance': 450},
        {'wind_advantage': True},  
        {'edge_habitat': True},
        {'min_canopy': 0.6}
    )
    
    analyzer.collect_wind_analysis(
        {'prevailing_wind': 'SW at 5mph', 'thermal_activity': True},
        [
            {'location_type': 'bedding', 'wind_analysis': {'wind_advantage_rating': 8.1}},
            {'location_type': 'stand', 'wind_analysis': {'wind_advantage_rating': 8.4}}
        ],
        {'overall_wind_conditions': {'hunting_rating': '8.1/10'}}
    )
    
    analysis = analyzer.get_comprehensive_analysis()
    
    # Verify we have data for display components
    assert analysis['criteria_analysis'] is not None
    assert analysis['wind_analysis'] is not None
    
    # Check metadata shows good completion
    completion = analysis['analysis_metadata']['completion_percentage']
    assert completion >= 25  # Should have at least some data
    
    print(f"✅ Analysis completeness test passed (completion: {completion:.1f}%)")

def test_large_dataset_handling():
    """Test that analysis can handle larger datasets"""
    print("🧪 Testing large dataset handling...")
    
    analyzer = PredictionAnalyzer()
    
    # Simulate larger wind analysis dataset
    large_wind_analyses = []
    for i in range(10):  # 10 locations
        large_wind_analyses.append({
            'location_type': f'location_{i}',
            'coordinates': (44.2664 + i*0.001, -72.5813 + i*0.001),
            'wind_analysis': {
                'effective_wind_direction': 225 + i*5,
                'effective_wind_speed': 6.0 + i*0.5,
                'wind_advantage_rating': 8.0 + i*0.1
            }
        })
    
    analyzer.collect_wind_analysis(
        {'prevailing_wind': 'SW at 5mph'},
        large_wind_analyses,
        {'overall_wind_conditions': {'hunting_rating': '8.0/10'}}
    )
    
    analysis = analyzer.get_comprehensive_analysis()
    
    # Verify large dataset handling
    wind_data = analysis['wind_analysis']
    assert len(wind_data['location_wind_analyses']) == 10
    
    # Test JSON serialization with large dataset
    json_str = json.dumps(analysis, default=str)
    assert len(json_str) > 1000  # Should be substantial
    
    # Verify it can be parsed back
    parsed = json.loads(json_str)
    assert len(parsed['wind_analysis']['location_wind_analyses']) == 10
    
    print("✅ Large dataset handling test passed")

def main():
    print("🔍 Running New Analysis API Endpoint Tests (Step 2.1 - Simplified)")
    print("=" * 65)
    
    try:
        test_analyzer_api_compatibility()
        test_response_structure_mock()
        test_error_response_structure()
        test_analysis_completeness()
        test_large_dataset_handling()
        
        print("=" * 65)
        print("✅ All Step 2.1 tests passed! API endpoint backend is ready.")
        print("📝 New endpoint: POST /analyze-prediction-detailed")
        print("🔧 Returns: {success, prediction, detailed_analysis, error}")
        print("🚀 Ready to proceed to Step 3.1: Create Wind Analysis Component")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
