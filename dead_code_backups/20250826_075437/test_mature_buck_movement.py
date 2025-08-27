#!/usr/bin/env python3
"""
Test suite for mature buck movement prediction functionality.
"""

import pytest
from backend.mature_buck_predictor import MatureBuckPreferences, MatureBuckBehaviorModel
from datetime import datetime

# Test data fixtures
@pytest.fixture

@pytest.fixture
def sample_weather_data():
    return {
        'temperature': 45.0,  # Fahrenheit
        'wind_speed': 8.0,    # mph
        'wind_direction': 180.0,
        'pressure_trend': 'falling',
        'precipitation': 0.0,
        'cloud_cover': 50.0,
        'conditions': ['clear']
    }

def test_movement_prediction_initialization():
    """Test basic movement prediction initialization"""
    model = MatureBuckBehaviorModel()
    assert model is not None
    assert model.preferences is not None
    assert model.confidence_factors is not None

def test_early_season_patterns(sample_terrain_features, sample_weather_data):
    """Test early season movement pattern predictions"""
    model = MatureBuckBehaviorModel()
    
    # Test morning movement (6am)
    morning_patterns = model._early_season_patterns(6, sample_terrain_features, sample_weather_data)
    assert 'movement_probability' in morning_patterns
    assert morning_patterns['movement_probability'] > 0
    assert len(morning_patterns['preferred_times']) > 0
    
    # Test midday movement (12pm)
    midday_patterns = model._early_season_patterns(12, sample_terrain_features, sample_weather_data)
    assert midday_patterns['movement_probability'] < morning_patterns['movement_probability']

def test_rut_season_patterns(sample_terrain_features, sample_weather_data):
    """Test rut season movement pattern predictions"""
    model = MatureBuckBehaviorModel()
    
    # Test prime morning movement (8am)
    morning_patterns = model._rut_season_patterns(8, sample_terrain_features, sample_weather_data)
    assert morning_patterns['movement_probability'] >= 70.0
    
    # Test midday movement (12pm)
    midday_patterns = model._rut_season_patterns(12, sample_terrain_features, sample_weather_data)
    assert midday_patterns['movement_probability'] > 0

def test_pressure_adjustments(sample_terrain_features):
    """Test pressure-based movement adjustments"""
    model = MatureBuckBehaviorModel()
    
    # Create test movement data
    movement_data = {
        'movement_probability': 80.0,
        'behavioral_notes': []
    }
    
    # Test high pressure scenario
    high_pressure_features = sample_terrain_features.copy()
    high_pressure_features['trail_density'] = 2.5
    high_pressure_features['hunter_accessibility'] = 0.8
    
    adjusted_data = model._apply_pressure_adjustments(movement_data, high_pressure_features)
    assert adjusted_data['movement_probability'] < movement_data['movement_probability']
    assert len(adjusted_data['behavioral_notes']) > 0
    
    # Test low pressure scenario
    low_pressure_features = sample_terrain_features.copy()
    low_pressure_features['trail_density'] = 0.2
    low_pressure_features['hunter_accessibility'] = 0.2
    
    adjusted_data = model._apply_pressure_adjustments(movement_data, low_pressure_features)
    assert adjusted_data['movement_probability'] >= movement_data['movement_probability']

def test_movement_confidence_calculation(sample_terrain_features, sample_weather_data):
    """Test movement confidence score calculations"""
    model = MatureBuckBehaviorModel()
    
    # Create test movement data
    movement_data = {
        'movement_probability': 75.0,
        'behavioral_notes': []
    }
    
    # Calculate confidence score
    confidence = model._calculate_movement_confidence(
        movement_data, sample_terrain_features, sample_weather_data
    )
    
    assert 0 <= confidence <= 100
    assert isinstance(confidence, float)

def test_spatial_predictions(sample_terrain_features):
    """Test spatial movement predictions"""
    model = MatureBuckBehaviorModel()
    lat, lon = 44.5, -72.8
    
    # Test movement corridor identification
    corridors = model._identify_movement_corridors(sample_terrain_features, lat, lon)
    assert isinstance(corridors, list)
    assert len(corridors) > 0
    assert all('lat' in corridor and 'lon' in corridor for corridor in corridors)
    
    # Test bedding location prediction
    bedding = model._predict_bedding_locations(sample_terrain_features, lat, lon)
    assert isinstance(bedding, list)
    assert len(bedding) > 0
    assert all('type' in location and 'confidence' in location for location in bedding)
    
    # Test feeding zone prediction
    feeding = model._predict_feeding_zones(sample_terrain_features, lat, lon, 'early_season')
    assert isinstance(feeding, list)
    assert len(feeding) > 0
    assert all('type' in zone and 'confidence' in zone for zone in feeding)

def test_full_movement_prediction(sample_terrain_features, sample_weather_data):
    """Test complete movement prediction workflow"""
    model = MatureBuckBehaviorModel()
    lat, lon = 44.5, -72.8
    
    # Test early season prediction
    early_prediction = model.predict_mature_buck_movement(
        'early_season', 8, sample_terrain_features, sample_weather_data, lat, lon
    )
    
    assert 'movement_probability' in early_prediction
    assert 'confidence_score' in early_prediction
    assert 'movement_corridors' in early_prediction
    assert 'bedding_predictions' in early_prediction
    assert 'feeding_predictions' in early_prediction
    assert 'behavioral_notes' in early_prediction
    
    # Test rut prediction
    rut_prediction = model.predict_mature_buck_movement(
        'rut', 8, sample_terrain_features, sample_weather_data, lat, lon
    )
    
    assert rut_prediction['movement_probability'] > early_prediction['movement_probability']
    
    # Test environmental impact
    cold_weather = sample_weather_data.copy()
    cold_weather['temperature'] = 25.0
    cold_prediction = model.predict_mature_buck_movement(
        'late_season', 8, sample_terrain_features, cold_weather, lat, lon
    )
    
    assert 'behavioral_notes' in cold_prediction
    assert any('energy conservation' in note.lower() for note in cold_prediction['behavioral_notes'])

if __name__ == '__main__':
    pytest.main([__file__])
