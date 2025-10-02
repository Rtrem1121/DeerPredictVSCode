#!/usr/bin/env python3
"""
Test for PredictionAnalyzer - Step 1.1 Verification

Tests that the PredictionAnalyzer correctly collects analysis data
without affecting prediction functionality.
"""

import sys
import os

# Add the specific path for the analyzer module
sys.path.insert(0, '/Users/richardtremblay/DeerPredictVSCode/backend/analysis')

from backend.analysis.prediction_analyzer import PredictionAnalyzer, create_prediction_analyzer

def test_analyzer_initialization():
    """Test that analyzer initializes correctly"""
    print("🧪 Testing analyzer initialization...")
    
    analyzer = create_prediction_analyzer()
    assert analyzer is not None
    assert analyzer.analysis_id.startswith("analysis_")
    assert all(not collected for collected in analyzer.data_collected.values())
    
    print("✅ Analyzer initialization test passed")

def test_criteria_collection():
    """Test criteria analysis collection"""
    print("🧪 Testing criteria collection...")
    
    analyzer = create_prediction_analyzer()
    
    # Mock criteria data
    bedding_criteria = {
        'canopy_coverage': 0.85,
        'road_distance': 450,
        'slope': 15,
        'aspect': 195
    }
    
    stand_criteria = {
        'wind_advantage': True,
        'thermal_position': 'ridge_top'
    }
    
    feeding_criteria = {
        'edge_habitat': True,
        'water_access': True
    }
    
    thresholds = {
        'min_canopy': 0.6,
        'min_road_distance': 200,
        'min_slope': 3,
        'max_slope': 30,
        'optimal_aspect_min': 135,
        'optimal_aspect_max': 225
    }
    
    # Collect criteria
    analyzer.collect_criteria_analysis(bedding_criteria, stand_criteria, feeding_criteria, thresholds)
    
    # Verify collection
    assert analyzer.data_collected['criteria'] == True
    assert analyzer.criteria_analysis is not None
    assert analyzer.criteria_analysis.bedding_criteria['canopy_coverage'] == 0.85
    
    print("✅ Criteria collection test passed")

def test_data_source_collection():
    """Test data source analysis collection"""
    print("🧪 Testing data source collection...")
    
    analyzer = create_prediction_analyzer()
    
    # Mock data source data
    gee_data = {'query_success': True, 'canopy_coverage': 0.85, 'elevation': 1200}
    osm_data = {'roads_found': True, 'nearest_road_distance_m': 450}
    weather_data = {'temperature': 38.5, 'wind_direction': 240, 'wind_speed': 5.2}
    scouting_data = {'enhancements_applied': [{'type': 'RUB_LINE'}], 'total_boost_points': 18}
    
    # Collect data sources
    analyzer.collect_data_source_analysis(gee_data, osm_data, weather_data, scouting_data)
    
    # Verify collection
    assert analyzer.data_collected['data_sources'] == True
    assert analyzer.data_source_analysis is not None
    assert analyzer.data_source_analysis.gee_data_quality['available'] == True
    
    print("✅ Data source collection test passed")

def test_comprehensive_analysis():
    """Test complete analysis generation"""
    print("🧪 Testing comprehensive analysis generation...")
    
    analyzer = create_prediction_analyzer()
    
    # Collect some mock data
    analyzer.collect_criteria_analysis(
        {'canopy_coverage': 0.85}, {}, {}, {'min_canopy': 0.6}
    )
    
    # Get comprehensive analysis
    analysis = analyzer.get_comprehensive_analysis()
    
    # Verify structure
    assert 'analysis_metadata' in analysis
    assert 'criteria_analysis' in analysis
    assert analysis['analysis_metadata']['completion_percentage'] > 0
    
    print("✅ Comprehensive analysis test passed")

def test_error_handling():
    """Test that analyzer handles errors gracefully"""
    print("🧪 Testing error handling...")
    
    analyzer = create_prediction_analyzer()
    
    # Try to collect with invalid data
    try:
        analyzer.collect_criteria_analysis(None, None, None, None)
        # Should not crash, should log warning
        assert analyzer.data_collected['criteria'] == False
        print("✅ Error handling test passed")
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        raise

if __name__ == "__main__":
    print("🔍 Running PredictionAnalyzer Tests (Step 1.1)")
    print("=" * 50)
    
    try:
        test_analyzer_initialization()
        test_criteria_collection()
        test_data_source_collection()
        test_comprehensive_analysis()
        test_error_handling()
        
        print("=" * 50)
        print("✅ All Step 1.1 tests passed! PredictionAnalyzer is working correctly.")
        print("🚀 Ready to proceed to Step 1.2: Enhance Prediction Service Integration")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
