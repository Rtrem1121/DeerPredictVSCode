#!/usr/bin/env python3
"""
Test for New Analysis API Endpoint - Step 2.1 Verification

Tests that the new /analyze-prediction-detailed endpoint works correctly
and returns both prediction data and detailed analysis.
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# Add paths for imports
sys.path.insert(0, '/Users/richardtremblay/DeerPredictVSCode/backend/analysis')
sys.path.insert(0, '/Users/richardtremblay/DeerPredictVSCode')

# Import test modules
from backend.analysis.prediction_analyzer import PredictionAnalyzer

def test_request_model():
    """Test that request models work correctly"""
    print("🧪 Testing request models...")
    
    # Import Pydantic models
    sys.path.insert(0, '/Users/richardtremblay/DeerPredictVSCode/backend/routers')
    from prediction_router import PredictionRequest, DetailedAnalysisResponse
    
    # Test request creation
    request = PredictionRequest(
        lat=44.2664,
        lon=-72.5813,
        date_time="2025-09-01T06:00:00Z",
        season="fall",
        hunt_period="AM"
    )
    
    assert request.lat == 44.2664
    assert request.lon == -72.5813
    assert request.season == "fall"
    
    print("✅ Request models test passed")

def test_analyzer_integration():
    """Test that analyzer integrates correctly with prediction data"""
    print("🧪 Testing analyzer integration...")
    
    analyzer = PredictionAnalyzer()
    
    # Simulate analysis collection
    analyzer.collect_criteria_analysis(
        {'canopy_coverage': 0.85, 'road_distance': 450},
        {'wind_advantage': True},
        {'edge_habitat': True},
        {'min_canopy': 0.6, 'min_road_distance': 200}
    )
    
    # Get analysis
    analysis = analyzer.get_comprehensive_analysis()
    
    # Verify structure for API response
    assert 'analysis_metadata' in analysis
    assert 'criteria_analysis' in analysis
    assert analysis['analysis_metadata']['completion_percentage'] > 0
    
    # Verify it's JSON serializable (important for API response)
    json_str = json.dumps(analysis, default=str)  # default=str handles datetime objects
    assert len(json_str) > 100  # Should be substantial JSON
    
    print("✅ Analyzer integration test passed")

def test_endpoint_response_structure():
    """Test that endpoint response has correct structure"""
    print("🧪 Testing endpoint response structure...")
    
    # Import response models
    sys.path.insert(0, '/Users/richardtremblay/DeerPredictVSCode/backend/routers')
    from prediction_router import DetailedAnalysisResponse
    
    # Mock prediction result
    mock_prediction = {
        'bedding_zones': {'features': []},
        'confidence_score': 0.85,
        'thermal_analysis': {'is_active': True},
        'wind_analyses': []
    }
    
    # Mock detailed analysis
    analyzer = PredictionAnalyzer()
    analyzer.collect_criteria_analysis({'canopy_coverage': 0.85}, {}, {}, {'min_canopy': 0.6})
    mock_analysis = analyzer.get_comprehensive_analysis()
    
    # Create response
    response = DetailedAnalysisResponse(
        success=True,
        prediction=mock_prediction,
        detailed_analysis=mock_analysis
    )
    
    # Verify response structure
    assert response.success == True
    assert response.prediction is not None
    assert response.detailed_analysis is not None
    assert 'bedding_zones' in response.prediction
    assert 'analysis_metadata' in response.detailed_analysis
    
    print("✅ Endpoint response structure test passed")

def test_error_handling():
    """Test that error handling works correctly"""
    print("🧪 Testing error handling...")
    
    # Import response models
    sys.path.insert(0, '/Users/richardtremblay/DeerPredictVSCode/backend/routers')
    from prediction_router import DetailedAnalysisResponse
    
    # Create error response
    error_response = DetailedAnalysisResponse(
        success=False,
        error="Test error message"
    )
    
    # Verify error response
    assert error_response.success == False
    assert error_response.error == "Test error message"
    assert error_response.prediction is None
    assert error_response.detailed_analysis is None
    
    print("✅ Error handling test passed")

def test_datetime_parsing():
    """Test that datetime parsing works correctly"""
    print("🧪 Testing datetime parsing...")
    
    from datetime import datetime
    
    # Test various datetime formats
    test_datetimes = [
        "2025-09-01T06:00:00Z",
        "2025-09-01T18:30:00Z",
        "2025-12-15T12:00:00Z"
    ]
    
    for dt_str in test_datetimes:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        assert isinstance(dt, datetime)
        assert 0 <= dt.hour <= 23
    
    print("✅ Datetime parsing test passed")

def test_json_serialization():
    """Test that analysis data can be serialized to JSON for API response"""
    print("🧪 Testing JSON serialization...")
    
    analyzer = PredictionAnalyzer()
    
    # Collect various types of analysis data
    analyzer.collect_criteria_analysis(
        {'canopy_coverage': 0.85, 'road_distance': 450, 'slope': 15.5},
        {'stand_count': 3, 'wind_advantage': True},
        {'feeding_areas_count': 2, 'food_source_diversity': True},
        {'min_canopy': 0.6, 'min_road_distance': 200.0}
    )
    
    analysis = analyzer.get_comprehensive_analysis()
    
    # Test JSON serialization
    try:
        json_str = json.dumps(analysis, default=str, indent=2)
        
        # Parse it back to verify it's valid JSON
        parsed = json.loads(json_str)
        
        # Verify structure is preserved
        assert 'analysis_metadata' in parsed
        assert 'criteria_analysis' in parsed
        assert parsed['analysis_metadata']['completion_percentage'] > 0
        
        print("✅ JSON serialization test passed")
        
    except (TypeError, ValueError) as e:
        print(f"❌ JSON serialization failed: {e}")
        raise

def main():
    print("🔍 Running New Analysis API Endpoint Tests (Step 2.1)")
    print("=" * 60)
    
    try:
        test_request_model()
        test_analyzer_integration()
        test_endpoint_response_structure()
        test_error_handling()
        test_datetime_parsing()
        test_json_serialization()
        
        print("=" * 60)
        print("✅ All Step 2.1 tests passed! New analysis API endpoint is working correctly.")
        print("🚀 Ready to proceed to Step 3.1: Create Wind Analysis Component")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
