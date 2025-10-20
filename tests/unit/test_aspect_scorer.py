"""
Unit tests for BiologicalAspectScorer

Tests Phase 4.7 wind-integrated aspect scoring against Vermont deer biology.
Validates leeward shelter prioritization, thermal comfort, and slope adjustments.

Test Scenarios:
1. Strong east wind (83°) with SSW aspect (206°) → 90+ score (leeward shelter)
2. Light wind with cold temps, south aspect → 100 score (thermal optimal)
3. Strong wind with windward aspect → <50 score (poor positioning)
4. Steep slopes (>30°) → Penalty applied

References:
- Phase 4.7 test results: Wind 83° East at 12.8 mph → Zones 206-223° scored 95/100
- Nelson & Mech (1981): Thermal refugia validation
"""

import pytest
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from services.aspect_scorer import BiologicalAspectScorer


class TestBiologicalAspectScorer:
    """Test suite for BiologicalAspectScorer service."""
    
    @pytest.fixture
    def scorer(self):
        """Create scorer instance for tests."""
        return BiologicalAspectScorer()
    
    # ============================================================================
    # LEEWARD SHELTER TESTS (Wind >10 mph)
    # ============================================================================
    
    def test_perfect_leeward_shelter_east_wind(self, scorer):
        """
        Test perfect leeward shelter with east wind.
        
        Phase 4.7 Validation:
        - Wind: 83° East at 12.8 mph
        - Aspect: 206° SSW (downhill direction)
        - Leeward: 263° WSW (wind + 180°)
        - Difference: 57° (within 60° = "good leeward shelter")
        - Expected: 90-95 score
        """
        score, reason = scorer.score_aspect(
            aspect=206,
            wind_direction=83,
            wind_speed=12.8,
            temperature=45,
            slope=16
        )
        
        assert score >= 90, f"Expected leeward shelter score >=90, got {score}"
        assert "leeward" in reason.lower(), "Reasoning should mention leeward shelter"
        assert "263" in reason, "Reasoning should show leeward direction (263°)"
    
    def test_perfect_leeward_shelter_within_30_degrees(self, scorer):
        """Test perfect leeward shelter (within 30° of leeward direction)."""
        # Wind from west (270°), leeward is east (90°)
        # Aspect 100° is 10° from leeward (perfect shelter)
        score, reason = scorer.score_aspect(
            aspect=100,
            wind_direction=270,
            wind_speed=15,
            temperature=50,
            slope=20
        )
        
        assert score == 100, f"Perfect leeward (<30°) should score 100, got {score}"
        assert "perfect leeward" in reason.lower()
    
    def test_good_leeward_shelter_within_60_degrees(self, scorer):
        """Test good leeward shelter (30-60° from leeward direction)."""
        # Wind from north (0°), leeward is south (180°)
        # Aspect 220° is 40° from leeward (good shelter)
        score, reason = scorer.score_aspect(
            aspect=220,
            wind_direction=0,
            wind_speed=12,
            temperature=40,
            slope=15
        )
        
        assert 90 <= score <= 95, f"Good leeward (30-60°) should score 90-95, got {score}"
        assert "good leeward" in reason.lower() or "leeward" in reason.lower()
    
    def test_moderate_shelter_crosswind(self, scorer):
        """Test moderate shelter (60-90° from leeward, crosswind position)."""
        # Wind from east (90°), leeward is west (270°)
        # Aspect 180° is 90° from leeward (crosswind)
        score, reason = scorer.score_aspect(
            aspect=180,
            wind_direction=90,
            wind_speed=14,
            temperature=55,
            slope=18
        )
        
        assert 70 <= score <= 80, f"Moderate shelter (crosswind) should score 70-80, got {score}"
        assert "moderate" in reason.lower() or "crosswind" in reason.lower()
    
    def test_windward_exposure_penalty(self, scorer):
        """Test windward exposure (facing directly into wind)."""
        # Wind from west (270°), aspect 270° faces INTO wind (worst case)
        score, reason = scorer.score_aspect(
            aspect=270,
            wind_direction=270,
            wind_speed=15,
            temperature=50,
            slope=20
        )
        
        assert score <= 50, f"Windward exposure should score <=50, got {score}"
        assert "windward" in reason.lower() or "exposure" in reason.lower()
    
    # ============================================================================
    # THERMAL COMFORT TESTS (Wind <10 mph)
    # ============================================================================
    
    def test_thermal_optimal_cold_south_facing(self, scorer):
        """Test thermal optimal: cold weather with south-facing aspect."""
        # Cold weather (<40°F), south-facing (135-225°) = perfect thermal
        score, reason = scorer.score_aspect(
            aspect=180,  # Due south
            wind_direction=90,
            wind_speed=5,  # Light wind
            temperature=35,  # Cold
            slope=15
        )
        
        assert score == 100, f"Cold + south-facing should score 100, got {score}"
        assert "thermal optimal" in reason.lower() or "south-facing" in reason.lower()
        assert "cold" in reason.lower()
    
    def test_thermal_optimal_hot_north_facing(self, scorer):
        """Test thermal optimal: hot weather with north-facing aspect."""
        # Hot weather (>75°F), north-facing (315-45°) = perfect cooling
        score, reason = scorer.score_aspect(
            aspect=0,  # Due north
            wind_direction=180,
            wind_speed=6,
            temperature=80,  # Hot
            slope=18
        )
        
        assert score == 100, f"Hot + north-facing should score 100, got {score}"
        assert "thermal optimal" in reason.lower() or "north-facing" in reason.lower()
        assert "hot" in reason.lower()
    
    def test_thermal_poor_cold_north_facing(self, scorer):
        """Test thermal poor: cold weather with north-facing aspect."""
        # Cold weather (<40°F), north-facing = poor thermal choice
        score, reason = scorer.score_aspect(
            aspect=0,  # Due north
            wind_direction=90,
            wind_speed=7,
            temperature=30,  # Very cold
            slope=20
        )
        
        assert score <= 60, f"Cold + north-facing should score <=60, got {score}"
        assert "north-facing" in reason.lower()
        assert "cold" in reason.lower()
    
    def test_thermal_moderate_temperature(self, scorer):
        """Test moderate temperature (40-75°F) - all aspects acceptable."""
        # Moderate temperature, south-facing gets slight bonus
        score_south, reason_south = scorer.score_aspect(
            aspect=180,
            wind_direction=270,
            wind_speed=8,
            temperature=60,
            slope=15
        )
        
        score_north, reason_north = scorer.score_aspect(
            aspect=0,
            wind_direction=270,
            wind_speed=8,
            temperature=60,
            slope=15
        )
        
        assert 85 <= score_south <= 95, f"Moderate temp, south aspect should score 85-95, got {score_south}"
        assert 80 <= score_north <= 90, f"Moderate temp, north aspect should score 80-90, got {score_north}"
    
    # ============================================================================
    # SLOPE ADJUSTMENT TESTS
    # ============================================================================
    
    def test_steep_slope_penalty(self, scorer):
        """Test steep slope penalty (>30°)."""
        # Perfect leeward but steep slope
        score_steep, _ = scorer.score_aspect(
            aspect=90,
            wind_direction=270,
            wind_speed=12,
            temperature=50,
            slope=35  # Steep
        )
        
        score_ideal, _ = scorer.score_aspect(
            aspect=90,
            wind_direction=270,
            wind_speed=12,
            temperature=50,
            slope=20  # Ideal
        )
        
        assert score_steep < score_ideal, "Steep slope should reduce score"
        penalty = score_ideal - score_steep
        assert penalty >= 5, f"Steep slope penalty should be >=5 points, got {penalty}"
    
    def test_ideal_slope_bonus(self, scorer):
        """Test ideal slope bonus (10-25°)."""
        score_ideal, reason = scorer.score_aspect(
            aspect=180,
            wind_direction=0,
            wind_speed=5,
            temperature=40,
            slope=15  # Ideal range
        )
        
        score_flat, _ = scorer.score_aspect(
            aspect=180,
            wind_direction=0,
            wind_speed=5,
            temperature=40,
            slope=5  # Below ideal range
        )
        
        # Ideal slope gets +5 bonus (capped at 100)
        assert "ideal slope" in reason.lower(), "Reasoning should mention ideal slope bonus"
    
    # ============================================================================
    # EDGE CASES AND VALIDATION
    # ============================================================================
    
    def test_angular_diff_wraparound(self, scorer):
        """Test angular difference calculation handles 0°/360° wraparound."""
        diff1 = scorer.angular_diff(10, 350)  # Should be 20°, not 340°
        diff2 = scorer.angular_diff(0, 180)   # Should be 180°
        diff3 = scorer.angular_diff(90, 270)  # Should be 180°
        
        assert diff1 == 20, f"Angular diff should handle wraparound, got {diff1}"
        assert diff2 == 180, f"Angular diff 0-180 should be 180, got {diff2}"
        assert diff3 == 180, f"Angular diff 90-270 should be 180, got {diff3}"
    
    def test_score_bounds(self, scorer):
        """Test that scores are always bounded 0-100."""
        # Test extreme conditions
        test_cases = [
            (0, 0, 50, -10, 45),    # Extreme steep slope (negative impossible)
            (180, 90, 5, 100, 3),   # Hot temp, wrong aspect, gentle slope
            (90, 270, 0, 0, 80),    # Perfect leeward but extreme steep
        ]
        
        for aspect, wind_dir, wind_speed, temp, slope in test_cases:
            score, _ = scorer.score_aspect(aspect, wind_dir, wind_speed, temp, slope)
            assert 0 <= score <= 100, f"Score must be 0-100, got {score} for inputs {test_cases}"
    
    def test_validation_method(self, scorer):
        """Test validate_score method for biological validation."""
        validation = scorer.validate_score(
            aspect=206,
            wind_direction=83,
            wind_speed=12.8,
            temperature=45,
            slope=16,
            expected_min_score=90
        )
        
        assert validation["passed"], "Phase 4.7 test case should pass validation"
        assert validation["score"] >= 90
        assert validation["priority_mode"] == "leeward_shelter"  # Wind >10 mph
        assert 260 <= validation["leeward_direction"] <= 265  # ~263°
    
    # ============================================================================
    # BIOLOGICAL SCENARIO TESTS (Vermont Deer Ecology)
    # ============================================================================
    
    def test_phase_4_7_validation_zone1(self, scorer):
        """
        Test Phase 4.7 validation: Zone 1 (aspect 223°, wind 83° East).
        
        Real-world test case from Phase 4.7 deployment:
        - Wind: 83° East at 12.8 mph
        - Zone 1: 223° aspect → 95/100 score
        - Leeward: 263° WSW
        - Difference: 40° (good leeward shelter)
        """
        score, reason = scorer.score_aspect(
            aspect=223,
            wind_direction=83,
            wind_speed=12.8,
            temperature=45,
            slope=18
        )
        
        assert score >= 90, f"Phase 4.7 Zone 1 should score >=90, got {score}"
        assert "leeward" in reason.lower()
    
    def test_phase_4_7_validation_primary_zone(self, scorer):
        """
        Test Phase 4.7 validation: Primary zone (aspect 164°, wind 83° East).
        
        Real-world test case:
        - Wind: 83° East at 12.8 mph
        - Primary: 164° aspect → 55/100 score (partial windward)
        - Leeward: 263° WSW
        - Difference: 99° (partial wind exposure, not optimal)
        """
        score, reason = scorer.score_aspect(
            aspect=164,
            wind_direction=83,
            wind_speed=12.8,
            temperature=45,
            slope=14
        )
        
        assert 50 <= score <= 65, f"Phase 4.7 Primary zone should score 50-65, got {score}"
        # Not perfect leeward, so score should be lower
    
    def test_vermont_winter_bedding(self, scorer):
        """
        Test Vermont winter bedding scenario (Nelson & Mech 1981).
        
        Winter conditions:
        - Cold temperature (<30°F)
        - Light wind (<10 mph) - thermals dominate
        - South-facing aspect (135-225°) - solar warming
        - Moderate slope (10-25°) - drainage + comfort
        """
        score, reason = scorer.score_aspect(
            aspect=180,  # Due south
            wind_direction=270,  # West wind
            wind_speed=8,  # Light wind
            temperature=25,  # Very cold
            slope=18  # Ideal slope
        )
        
        assert score >= 95, f"Vermont winter bedding should score >=95, got {score}"
        assert "thermal" in reason.lower()
        assert "south-facing" in reason.lower()
        assert "cold" in reason.lower()
        assert "ideal slope" in reason.lower()
    
    def test_vermont_fall_windy_bedding(self, scorer):
        """
        Test Vermont fall bedding with strong west wind (Hirth 1977).
        
        Fall conditions:
        - Moderate temperature (40-60°F)
        - Strong west wind (>15 mph) - leeward shelter critical
        - East-facing aspect (leeward from west wind)
        - Moderate slope
        """
        score, reason = scorer.score_aspect(
            aspect=90,  # Due east (leeward from west wind)
            wind_direction=270,  # West wind
            wind_speed=16,  # Strong wind
            temperature=50,  # Moderate
            slope=20  # Ideal
        )
        
        assert score >= 95, f"Fall windy bedding should score >=95, got {score}"
        assert "leeward" in reason.lower()
        assert "ideal slope" in reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
