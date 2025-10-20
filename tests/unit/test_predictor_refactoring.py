#!/usr/bin/env python3
"""
Integration Test: Verify Main Predictor Refactoring

Tests that the refactored EnhancedBeddingZonePredictor maintains
identical behavior after integrating BiologicalAspectScorer service.

Author: GitHub Copilot (Refactoring Validation)
Date: October 19, 2025
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor


class TestPredictorRefactoring:
    """Test suite validating main predictor refactoring."""
    
    @pytest.fixture
    def predictor(self):
        """Create predictor instance."""
        return EnhancedBeddingZonePredictor()
    
    def test_aspect_scorer_initialized(self, predictor):
        """Test that BiologicalAspectScorer is properly initialized."""
        assert hasattr(predictor, 'aspect_scorer'), \
            "Predictor should have aspect_scorer attribute"
        
        assert predictor.aspect_scorer is not None, \
            "aspect_scorer should be initialized"
        
        # Verify service has expected methods
        assert hasattr(predictor.aspect_scorer, 'score_aspect'), \
            "aspect_scorer should have score_aspect method"
    
    def test_deprecated_method_delegates_to_service(self, predictor):
        """Test that deprecated _score_aspect_biological delegates to service."""
        # Call the deprecated method
        score, reason = predictor._score_aspect_biological(
            aspect=180,
            wind_direction=270,
            wind_speed=12,
            temperature=40,
            slope=15
        )
        
        # Verify it returns valid results
        assert 0 <= score <= 100, f"Score should be 0-100, got {score}"
        assert isinstance(reason, str), f"Reason should be string, got {type(reason)}"
        assert len(reason) > 0, "Reason should not be empty"
    
    def test_leeward_shelter_scoring_consistency(self, predictor):
        """Test leeward shelter scoring produces expected results."""
        # Perfect leeward shelter (wind from east, aspect west)
        score, reason = predictor._score_aspect_biological(
            aspect=270,  # West-facing slope
            wind_direction=90,  # East wind
            wind_speed=15,  # Strong wind
            temperature=45,
            slope=15
        )
        
        assert score >= 90, \
            f"Perfect leeward shelter should score >=90, got {score}"
        assert "leeward" in reason.lower(), \
            f"Reason should mention leeward, got: {reason}"
    
    def test_thermal_comfort_scoring_consistency(self, predictor):
        """Test thermal comfort scoring produces expected results."""
        # Cold weather, south-facing (thermal optimal)
        score, reason = predictor._score_aspect_biological(
            aspect=180,  # South-facing
            wind_direction=270,
            wind_speed=5,  # Light wind
            temperature=35,  # Cold
            slope=15
        )
        
        assert score >= 95, \
            f"Thermal optimal (cold+south) should score >=95, got {score}"
        assert "thermal" in reason.lower(), \
            f"Reason should mention thermal, got: {reason}"
    
    def test_windward_exposure_penalty(self, predictor):
        """Test windward exposure receives appropriate penalty."""
        # Direct windward exposure
        score, reason = predictor._score_aspect_biological(
            aspect=270,  # West-facing
            wind_direction=270,  # West wind (direct exposure)
            wind_speed=15,
            temperature=45,
            slope=15
        )
        
        assert score <= 50, \
            f"Windward exposure should score <=50, got {score}"
        assert "wind" in reason.lower(), \
            f"Reason should mention wind, got: {reason}"
    
    def test_steep_slope_penalty(self, predictor):
        """Test steep slopes receive appropriate penalty."""
        # Very steep slope (>30°)
        score_steep, reason_steep = predictor._score_aspect_biological(
            aspect=180,
            wind_direction=270,
            wind_speed=8,
            temperature=45,
            slope=35  # Steep
        )
        
        # Moderate slope
        score_moderate, reason_moderate = predictor._score_aspect_biological(
            aspect=180,
            wind_direction=270,
            wind_speed=8,
            temperature=45,
            slope=15  # Ideal
        )
        
        assert score_steep < score_moderate, \
            f"Steep slope ({score_steep}) should score lower than moderate ({score_moderate})"
        assert "slope" in reason_steep.lower() or "steep" in reason_steep.lower(), \
            f"Steep slope reason should mention slope/steep, got: {reason_steep}"
    
    def test_ideal_slope_bonus(self, predictor):
        """Test ideal slopes (10-25°) receive bonus."""
        # Ideal slope
        score, reason = predictor._score_aspect_biological(
            aspect=180,
            wind_direction=270,
            wind_speed=8,
            temperature=45,
            slope=18  # Ideal range
        )
        
        assert "ideal" in reason.lower() or "slope" in reason.lower(), \
            f"Ideal slope should be mentioned in reason: {reason}"
    
    def test_score_bounds(self, predictor):
        """Test all scores are bounded 0-100."""
        test_cases = [
            (0, 0, 0, 0, 0),  # Edge case: all zeros
            (360, 360, 100, 100, 50),  # Edge case: max values
            (180, 90, 20, 30, 35),  # Edge case: extreme steep slope
        ]
        
        for aspect, wind_dir, wind_speed, temp, slope in test_cases:
            score, reason = predictor._score_aspect_biological(
                aspect=aspect,
                wind_direction=wind_dir,
                wind_speed=wind_speed,
                temperature=temp,
                slope=slope
            )
            
            assert 0 <= score <= 100, \
                f"Score must be 0-100, got {score} for inputs: " \
                f"aspect={aspect}, wind_dir={wind_dir}, wind_speed={wind_speed}, " \
                f"temp={temp}, slope={slope}"


class TestRefactoringIntegrity:
    """Test that refactoring maintains system integrity."""
    
    def test_predictor_instantiation(self):
        """Test predictor can be instantiated without errors."""
        try:
            predictor = EnhancedBeddingZonePredictor()
            assert predictor is not None
        except Exception as e:
            pytest.fail(f"Predictor instantiation failed: {e}")
    
    def test_aspect_scorer_service_import(self):
        """Test BiologicalAspectScorer service can be imported."""
        try:
            from backend.services.aspect_scorer import BiologicalAspectScorer
            scorer = BiologicalAspectScorer()
            assert scorer is not None
        except ImportError as e:
            pytest.fail(f"Failed to import BiologicalAspectScorer: {e}")
    
    def test_service_and_predictor_consistency(self):
        """Test direct service call matches predictor method call."""
        from backend.services.aspect_scorer import BiologicalAspectScorer
        
        predictor = EnhancedBeddingZonePredictor()
        scorer = BiologicalAspectScorer()
        
        test_params = {
            'aspect': 206,
            'wind_direction': 83,
            'wind_speed': 12.8,
            'temperature': 45,
            'slope': 16
        }
        
        # Call through predictor (deprecated method)
        predictor_score, predictor_reason = predictor._score_aspect_biological(**test_params)
        
        # Call service directly
        service_score, service_reason = scorer.score_aspect(**test_params)
        
        # Should be identical (deprecated method delegates to service)
        assert predictor_score == service_score, \
            f"Scores should match: predictor={predictor_score}, service={service_score}"
        assert predictor_reason == service_reason, \
            f"Reasons should match: predictor='{predictor_reason}', service='{service_reason}'"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
