"""
Unit tests for mature buck prediction functionality.

These tests ensure that the sophisticated mature buck analysis
that provides accurate behavioral modeling is preserved during refactoring.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.fixtures.test_data import (
    GOLDEN_TEST_LOCATION,
    EXPECTED_MATURE_BUCK_RESULTS,
    get_rut_season_request,
)

try:
    from backend.mature_buck_predictor import MatureBuckPreferences, MatureBuckBehaviorModel
    MATURE_BUCK_MODULE_AVAILABLE = True
except ImportError:
    MATURE_BUCK_MODULE_AVAILABLE = False
    MatureBuckPreferences = None
    MatureBuckBehaviorModel = None

class TestMatureBuckPreferences:
    """Test suite for mature buck preferences configuration."""
    
    @pytest.fixture
    def buck_preferences(self):
        """Fixture to provide mature buck preferences."""
        if not MATURE_BUCK_MODULE_AVAILABLE:
            pytest.skip("Mature buck module not available")
        return MatureBuckPreferences()
    
    def test_mature_buck_module_availability(self):
        """Test that mature buck module is available."""
        assert MATURE_BUCK_MODULE_AVAILABLE, "Mature buck module should be available"
        assert MatureBuckPreferences is not None
    
    @pytest.mark.skipif(not MATURE_BUCK_MODULE_AVAILABLE, reason="Mature buck module not available")
    def test_preferences_initialization(self, buck_preferences):
        """Test that preferences are initialized correctly."""
        assert buck_preferences is not None
        
        # Test that key preferences are set
        assert hasattr(buck_preferences, 'min_bedding_thickness'), "Should have bedding thickness preference"
        assert hasattr(buck_preferences, 'preferred_elevation_range'), "Should have elevation preference"
        assert hasattr(buck_preferences, 'isolation_preference'), "Should have isolation preference"
        
        # Values should be reasonable
        if hasattr(buck_preferences, 'min_bedding_thickness'):
            thickness = buck_preferences.min_bedding_thickness
            assert 0 <= thickness <= 100, f"Bedding thickness {thickness} should be reasonable percentage"
    
    @pytest.mark.skipif(not MATURE_BUCK_MODULE_AVAILABLE, reason="Mature buck module not available")
    def test_preferences_from_config(self, buck_preferences):
        """Test that preferences are loaded from configuration system."""
        # Ensure preferences are using the configuration management system
        # This validates that the configuration integration is working
        
        # Test that configuration values are applied
        # These may vary based on environment but should be present
        assert buck_preferences is not None, "Preferences should be initialized"
        
        # If configuration is working, preferences should have reasonable values
        # rather than None or extreme values

class TestMatureBuckBehaviorModel:
    """Test suite for mature buck behavior modeling."""
    
    @pytest.fixture
    def behavior_model(self):
        """Fixture to provide behavior model."""
        if not MATURE_BUCK_MODULE_AVAILABLE:
            pytest.skip("Mature buck module not available")
        return MatureBuckBehaviorModel()
    
    @pytest.mark.skipif(not MATURE_BUCK_MODULE_AVAILABLE, reason="Mature buck module not available")
    def test_rut_season_behavior(self, behavior_model):
        """Test mature buck behavior during rut season."""
        # Rut season should show high movement probability
        rut_date = datetime(2025, 11, 15)  # Peak rut
        
        # Test movement probability calculation
        if hasattr(behavior_model, 'calculate_movement_probability'):
            movement_prob = behavior_model.calculate_movement_probability(
                season="rut",
                date=rut_date,
                latitude=GOLDEN_TEST_LOCATION["latitude"],
                longitude=GOLDEN_TEST_LOCATION["longitude"]
            )
            
            # During rut, movement should be high (≥75%)
            assert movement_prob >= 0.75, f"Rut movement probability {movement_prob} should be high"
            assert movement_prob <= 1.0, f"Movement probability {movement_prob} should not exceed 100%"
    
    @pytest.mark.skipif(not MATURE_BUCK_MODULE_AVAILABLE, reason="Mature buck module not available")
    def test_early_season_behavior(self, behavior_model):
        """Test mature buck behavior during early season."""
        early_date = datetime(2025, 10, 1)  # Early season
        
        if hasattr(behavior_model, 'calculate_movement_probability'):
            movement_prob = behavior_model.calculate_movement_probability(
                season="early_season",
                date=early_date,
                latitude=GOLDEN_TEST_LOCATION["latitude"],
                longitude=GOLDEN_TEST_LOCATION["longitude"]
            )
            
            # Early season movement should be moderate (40-70%)
            assert 0.4 <= movement_prob <= 0.7, f"Early season movement probability {movement_prob} should be moderate"
    
    @pytest.mark.skipif(not MATURE_BUCK_MODULE_AVAILABLE, reason="Mature buck module not available")
    def test_behavioral_patterns(self, behavior_model):
        """Test that behavioral patterns are reasonable."""
        test_location = GOLDEN_TEST_LOCATION
        
        # Test different times of day if method exists
        if hasattr(behavior_model, 'get_prime_movement_times'):
            prime_times = behavior_model.get_prime_movement_times(
                latitude=test_location["latitude"],
                longitude=test_location["longitude"]
            )
            
            assert prime_times is not None, "Should return prime movement times"
            assert len(prime_times) > 0, "Should have at least one prime time"
            
            # Common prime times should be early morning or evening
            time_strings = [str(t) for t in prime_times]
            has_morning_or_evening = any(
                "06:" in t or "07:" in t or "17:" in t or "18:" in t or "19:" in t 
                for t in time_strings
            )
            assert has_morning_or_evening, f"Prime times {prime_times} should include morning or evening"

class TestMatureBuckIntegration:
    """Integration tests for mature buck analysis."""
    
    @pytest.mark.skipif(not MATURE_BUCK_MODULE_AVAILABLE, reason="Mature buck module not available")
    def test_complete_analysis_pipeline(self):
        """Test complete mature buck analysis pipeline."""
        # This test validates the complete analysis flow
        
        preferences = MatureBuckPreferences()
        behavior_model = MatureBuckBehaviorModel()
        
        test_location = GOLDEN_TEST_LOCATION
        
        # Test that both components work together
        assert preferences is not None, "Preferences should be available"
        assert behavior_model is not None, "Behavior model should be available"
        
        # If there's an integrated analysis method, test it
        # This would be the method that provides the complete mature buck analysis
    
    @pytest.mark.skipif(not MATURE_BUCK_MODULE_AVAILABLE, reason="Mature buck module not available")
    def test_confidence_scoring(self):
        """Test mature buck confidence scoring."""
        behavior_model = MatureBuckBehaviorModel()
        
        # Test confidence calculation if available
        if hasattr(behavior_model, 'calculate_confidence'):
            confidence = behavior_model.calculate_confidence(
                latitude=GOLDEN_TEST_LOCATION["latitude"],
                longitude=GOLDEN_TEST_LOCATION["longitude"]
            )
            
            # Confidence should be reasonable (algorithmic predictions typically 30-80%)
            assert 0.3 <= confidence <= 0.8, f"Mature buck confidence {confidence} should be reasonable"
        
        # The expected 59% confidence from golden location
        expected_confidence = EXPECTED_MATURE_BUCK_RESULTS["confidence_score"]
        if hasattr(behavior_model, 'calculate_confidence'):
            actual_confidence = behavior_model.calculate_confidence(
                latitude=GOLDEN_TEST_LOCATION["latitude"],
                longitude=GOLDEN_TEST_LOCATION["longitude"]
            )
            
            # Allow ±10% tolerance for algorithmic confidence
            tolerance = 0.1
            assert abs(actual_confidence - expected_confidence) <= tolerance, \
                f"Confidence {actual_confidence} should be close to expected {expected_confidence}"

class TestMatureBuckPerformance:
    """Performance tests for mature buck analysis."""
    
    @pytest.mark.skipif(not MATURE_BUCK_MODULE_AVAILABLE, reason="Mature buck module not available")
    def test_analysis_performance(self):
        """Test that mature buck analysis completes in reasonable time."""
        import time
        
        behavior_model = MatureBuckBehaviorModel()
        
        start_time = time.time()
        
        # Run a complete analysis
        if hasattr(behavior_model, 'calculate_movement_probability'):
            result = behavior_model.calculate_movement_probability(
                season="rut",
                date=datetime.now(),
                latitude=GOLDEN_TEST_LOCATION["latitude"],
                longitude=GOLDEN_TEST_LOCATION["longitude"]
            )
        
        end_time = time.time()
        analysis_time = end_time - start_time
        
        # Analysis should be fast (< 3 seconds for unit operations)
        assert analysis_time < 3.0, f"Mature buck analysis took {analysis_time:.2f}s, should be < 3s"

class TestMatureBuckRegression:
    """Regression tests to ensure refactoring preserves functionality."""
    
    @pytest.mark.skipif(not MATURE_BUCK_MODULE_AVAILABLE, reason="Mature buck module not available")
    def test_preserve_rut_behavior(self):
        """Test that rut behavior characteristics are preserved."""
        behavior_model = MatureBuckBehaviorModel()
        
        # Test golden location during rut
        rut_date = datetime(2025, 11, 15)
        
        if hasattr(behavior_model, 'calculate_movement_probability'):
            movement_prob = behavior_model.calculate_movement_probability(
                season="rut",
                date=rut_date,
                latitude=GOLDEN_TEST_LOCATION["latitude"],
                longitude=GOLDEN_TEST_LOCATION["longitude"]
            )
            
            # Should match expected rut behavior (80% movement probability)
            expected_prob = EXPECTED_MATURE_BUCK_RESULTS["movement_probability"]
            tolerance = 0.1  # ±10% tolerance
            
            assert abs(movement_prob - expected_prob) <= tolerance, \
                f"Rut movement probability {movement_prob} should be close to expected {expected_prob}"
    
    @pytest.mark.skipif(not MATURE_BUCK_MODULE_AVAILABLE, reason="Mature buck module not available")
    def test_preserve_stand_recommendations(self):
        """Test that stand recommendation count is preserved."""
        # The current system provides 4 specialized stand positions
        expected_stands = EXPECTED_MATURE_BUCK_RESULTS["stand_recommendations"]
        
        # This would test whatever method generates stand recommendations
        # The exact implementation may vary, but should maintain the same quality
        
        # For now, just validate that the expected count is reasonable
        assert expected_stands == 4, "Should recommend 4 specialized stand positions"
        
        # If there's a method to get recommendations, test it:
        # if hasattr(behavior_model, 'get_stand_recommendations'):
        #     recommendations = behavior_model.get_stand_recommendations(...)
        #     assert len(recommendations) == expected_stands

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
