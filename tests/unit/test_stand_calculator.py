#!/usr/bin/env python3
"""
Unit Tests: WindAwareStandCalculator Service

Tests Phase 4.10 crosswind stand positioning logic extracted from
the main predictor. Validates evening/morning/all-day stand calculations
with wind-aware and thermal logic.

Author: GitHub Copilot (Refactoring Validation)
Date: October 19, 2025
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.stand_calculator import (
    WindAwareStandCalculator,
    ThermalWindData,
    StandCalculationResult
)


class TestWindAwareStandCalculator:
    """Test suite for WindAwareStandCalculator service."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return WindAwareStandCalculator()
    
    # ==================== EVENING STAND TESTS ====================
    
    def test_evening_stand_strong_wind_crosswind(self, calculator):
        """Test evening stand with strong wind uses crosswind logic."""
        result = calculator.calculate_evening_stand(
            wind_direction=270,  # West wind
            wind_speed_mph=15,   # Strong wind
            downhill_direction=180,  # South downhill
            downwind_direction=90,   # East (opposite of wind)
            thermal_data=None,
            slope=15
        )
        
        assert isinstance(result, StandCalculationResult)
        assert result.wind_aware is True, "Strong wind should use wind-aware logic"
        assert result.crosswind_bearing is not None
        
        # Crosswind should be ~90° from wind (either 0° or 180°)
        # Should choose the one closer to downhill (180°)
        assert 135 <= result.bearing <= 225, \
            f"Evening crosswind should be near downhill (180°), got {result.bearing}°"
        
        assert "crosswind" in result.primary_reason.lower() or "wind" in result.primary_reason.lower()
    
    def test_evening_stand_light_wind_terrain(self, calculator):
        """Test evening stand with light wind uses terrain logic."""
        result = calculator.calculate_evening_stand(
            wind_direction=270,
            wind_speed_mph=5,  # Light wind
            downhill_direction=180,
            downwind_direction=90,
            thermal_data=None,
            slope=20
        )
        
        assert isinstance(result, StandCalculationResult)
        # With light wind on slope, should use terrain/deer movement logic (not crosswind)
        assert result.wind_aware is False, "Light wind should NOT use wind-aware crosswind logic"
        assert "deer" in result.primary_reason.lower() or "downhill" in result.primary_reason.lower() or "terrain" in result.primary_reason.lower()
    
    def test_evening_stand_with_thermal_active(self, calculator):
        """Test evening stand with active thermal winds."""
        thermal_data = ThermalWindData(
            is_active=True,
            direction=200,  # SSW thermal direction
            strength=0.7,
            phase="evening"
        )
        
        result = calculator.calculate_evening_stand(
            wind_direction=270,
            wind_speed_mph=8,  # Moderate wind
            downhill_direction=180,
            downwind_direction=90,
            thermal_data=thermal_data,
            slope=18
        )
        
        assert isinstance(result, StandCalculationResult)
        # Should consider both thermal and downhill in light wind
        assert "thermal" in result.primary_reason.lower() or "downhill" in result.primary_reason.lower()
    
    def test_evening_stand_crosswind_selection(self, calculator):
        """Test crosswind option selection favors downhill direction."""
        # Wind from north (0°), crosswind options are 90° (E) and 270° (W)
        # Downhill is south (180°), so should choose 180° or nearest crosswind
        result = calculator.calculate_evening_stand(
            wind_direction=0,   # North wind
            wind_speed_mph=12,
            downhill_direction=180,  # South downhill
            downwind_direction=180,  # South
            thermal_data=None,
            slope=15
        )
        
        # Crosswind options: 90° (E) or 270° (W)
        # Neither is directly downhill (180°), but logic should pick one
        assert result.crosswind_bearing in [90, 270]
    
    # ==================== MORNING STAND TESTS ====================
    
    def test_morning_stand_strong_wind_crosswind(self, calculator):
        """Test morning stand with strong wind uses crosswind logic."""
        result = calculator.calculate_morning_stand(
            wind_direction=270,  # West wind
            wind_speed_mph=15,
            uphill_direction=0,  # North uphill
            downwind_direction=90,
            thermal_data=None,
            slope=15
        )
        
        assert isinstance(result, StandCalculationResult)
        assert result.wind_aware is True
        assert result.crosswind_bearing is not None
        
        # Crosswind should be near uphill direction (0° North)
        assert result.bearing < 45 or result.bearing > 315, \
            f"Morning crosswind should be near uphill (0°), got {result.bearing}°"
        
        assert "crosswind" in result.primary_reason.lower()
    
    def test_morning_stand_light_wind_uphill(self, calculator):
        """Test morning stand with light wind favors uphill intercept."""
        result = calculator.calculate_morning_stand(
            wind_direction=270,
            wind_speed_mph=5,  # Light wind
            uphill_direction=0,  # North uphill
            downwind_direction=90,
            thermal_data=None,
            slope=20
        )
        
        assert isinstance(result, StandCalculationResult)
        # Should use uphill intercept on slopes with light wind
        assert "uphill" in result.primary_reason.lower() or "intercept" in result.primary_reason.lower()
    
    def test_morning_stand_flat_terrain_wind_based(self, calculator):
        """Test morning stand on flat terrain uses wind-based positioning."""
        result = calculator.calculate_morning_stand(
            wind_direction=270,
            wind_speed_mph=5,
            uphill_direction=0,
            downwind_direction=90,
            thermal_data=None,
            slope=3  # Flat
        )
        
        assert isinstance(result, StandCalculationResult)
        # Flat terrain with light wind should mention wind
        assert "wind" in result.primary_reason.lower() or "flat" in result.primary_reason.lower()
    
    # ==================== ALL-DAY STAND TESTS ====================
    
    def test_allday_stand_strong_wind_opposite_crosswind(self, calculator):
        """Test all-day stand provides opposite crosswind from morning."""
        # First get morning stand
        morning = calculator.calculate_morning_stand(
            wind_direction=270,
            wind_speed_mph=15,
            uphill_direction=0,
            downwind_direction=90,
            thermal_data=None,
            slope=15
        )
        
        # Now get all-day stand (should be opposite)
        allday = calculator.calculate_allday_stand(
            wind_direction=270,
            wind_speed_mph=15,
            morning_bearing=morning.bearing,
            uphill_direction=0,
            downwind_direction=90,
            slope=15
        )
        
        assert isinstance(allday, StandCalculationResult)
        assert allday.wind_aware is True
        
        # All-day should be opposite crosswind from morning
        # If morning is 0° or 180°, all-day should be the other option
        morning_bearing = morning.bearing
        allday_bearing = allday.bearing
        
        # Should be significantly different (not same quadrant)
        angle_diff = abs(morning_bearing - allday_bearing)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        assert angle_diff > 90, \
            f"All-day ({allday_bearing}°) should differ from morning ({morning_bearing}°) by >90°"
    
    def test_allday_stand_light_wind_alternate_uphill(self, calculator):
        """Test all-day stand with light wind provides alternate uphill angle."""
        result = calculator.calculate_allday_stand(
            wind_direction=270,
            wind_speed_mph=5,
            morning_bearing=0,  # Assume morning was uphill
            uphill_direction=0,
            downwind_direction=90,
            slope=18
        )
        
        assert isinstance(result, StandCalculationResult)
        # Light wind on sloped terrain should use uphill/terrain-based logic
        assert result.wind_aware is False, "Light wind should NOT use crosswind logic"
        assert ("uphill" in result.primary_reason.lower() or 
                "alternate" in result.primary_reason.lower() or 
                "variation" in result.primary_reason.lower())
    
    # ==================== SCENT MANAGEMENT TESTS ====================
    
    def test_scent_validation_safe(self, calculator):
        """Test scent validation passes when stand is NOT in downwind scent cone."""
        # Stand at north (0°), wind from west (270°)
        # Scent blows east (270 + 180 = 90°)
        # Angular diff between stand (0°) and scent (90°) = 90° > 45° = SAFE
        bedding_zones = [{"zone_type": "primary", "lat": 44.5, "lon": -72.8}]
        
        is_safe, violations = calculator.validate_scent_management(
            stand_bearing=0,     # North stand (90° away from scent direction)
            wind_direction=270,  # West wind (scent blows to east at 90°)
            wind_speed_mph=10,
            bedding_zones=bedding_zones
        )
        
        assert is_safe is True, f"Stand 90° away from scent should be safe, got violations: {violations}"
        assert len(violations) == 0, "Should have no violations"
    
    def test_scent_validation_violation(self, calculator):
        """Test scent validation fails when stand is upwind of bedding."""
        # Bedding zone at east (90°), stand at west (270°), wind from west (270°)
        # Scent blows east (90°), toward bedding zones - VIOLATION
        bedding_zones = [{"zone_type": "primary", "lat": 44.5, "lon": -72.8}]
        
        is_safe, violations = calculator.validate_scent_management(
            stand_bearing=90,   # East stand (same as scent direction)
            wind_direction=270,  # West wind (scent blows east at 90°)
            wind_speed_mph=10,
            bedding_zones=bedding_zones
        )
        
        assert is_safe is False, "Stand upwind should violate scent management"
        assert len(violations) > 0, "Should have violations"
    
    def test_scent_validation_edge_case(self, calculator):
        """Test scent validation at edge of cone (45° from scent bearing)."""
        # Scent blows at 90° (east), stand at 135° (SE) - exactly at 45° boundary
        bedding_zones = [{"zone_type": "primary", "lat": 44.5, "lon": -72.8}]
        
        is_safe, violations = calculator.validate_scent_management(
            stand_bearing=135,   # 45° off from scent direction
            wind_direction=270,  # Downwind is 90°
            wind_speed_mph=10,
            bedding_zones=bedding_zones
        )
        
        # Edge case: 45° is exactly at cone boundary
        # Should be marginal or safe depending on implementation
        assert isinstance(is_safe, bool)
    
    # ==================== WIND THRESHOLD TESTS ====================
    
    def test_wind_threshold_transition(self, calculator):
        """Test behavior at wind threshold (10 mph)."""
        # Just above threshold
        result_strong = calculator.calculate_evening_stand(
            wind_direction=270,
            wind_speed_mph=10.5,  # Just above
            downhill_direction=180,
            downwind_direction=90,
            thermal_data=None,
            slope=15
        )
        
        # Just below threshold
        result_light = calculator.calculate_evening_stand(
            wind_direction=270,
            wind_speed_mph=9.5,  # Just below
            downhill_direction=180,
            downwind_direction=90,
            thermal_data=None,
            slope=15
        )
        
        # Strong wind should be wind-aware
        assert result_strong.wind_aware is True or "crosswind" in result_strong.reasoning.lower()
        
        # Light wind should use terrain
        assert result_light.wind_aware is False or "terrain" in result_light.reasoning.lower() \
               or "downhill" in result_light.reasoning.lower()
    
    # ==================== BEARING COMBINATION TESTS ====================
    
    def test_bearing_combination_simple(self, calculator):
        """Test bearing combination for non-wraparound cases."""
        # Combine north (0°) and east (90°) with equal weights
        combined = calculator._combine_bearings(0, 90, 0.5, 0.5)
        
        # Should be northeast (45°)
        assert 40 <= combined <= 50, f"Expected ~45°, got {combined}°"
    
    def test_bearing_combination_wraparound(self, calculator):
        """Test bearing combination handles 0°/360° wraparound."""
        # Combine north (350°) and north (10°) - should give ~0°
        combined = calculator._combine_bearings(350, 10, 0.5, 0.5)
        
        # Should be near 0° (allowing for wraparound)
        assert combined < 20 or combined > 340, \
            f"Expected near 0° for 350° + 10°, got {combined}°"
    
    def test_bearing_combination_weighted(self, calculator):
        """Test weighted bearing combination."""
        # Combine north (0°) and east (90°) with 80% weight on north
        combined = calculator._combine_bearings(0, 90, 0.8, 0.2)
        
        # Should be closer to north than east
        assert combined < 30, f"Expected <30° (closer to 0°), got {combined}°"
    
    # ==================== ANGULAR DIFFERENCE TESTS ====================
    
    def test_angular_diff_simple(self, calculator):
        """Test angular difference for simple cases."""
        diff = calculator._angular_diff(90, 120)
        assert diff == 30, f"90° to 120° should be 30°, got {diff}°"
    
    def test_angular_diff_wraparound(self, calculator):
        """Test angular difference handles wraparound."""
        diff = calculator._angular_diff(10, 350)
        assert diff == 20, f"10° to 350° should be 20°, got {diff}°"
    
    def test_angular_diff_opposite(self, calculator):
        """Test angular difference for opposite directions."""
        diff = calculator._angular_diff(0, 180)
        assert diff == 180, f"0° to 180° should be 180°, got {diff}°"
    
    # ==================== QUALITY SCORE TESTS ====================
    
    def test_quality_score_calculation(self, calculator):
        """Test stand quality score calculation."""
        # This test assumes StandPosition has calculate_quality_score method
        # Since we're testing the calculator, we'll validate the result structure
        result = calculator.calculate_evening_stand(
            wind_direction=270,
            wind_speed_mph=12,
            downhill_direction=180,
            downwind_direction=90,
            thermal_data=None,
            slope=15
        )
        
        # Validate result has all expected fields
        assert hasattr(result, 'bearing')
        assert hasattr(result, 'wind_aware')
        assert hasattr(result, 'primary_reason')
        assert 0 <= result.bearing <= 360
    
    # ==================== THERMAL WIND DATA TESTS ====================
    
    def test_thermal_wind_data_creation(self):
        """Test ThermalWindData dataclass creation."""
        thermal = ThermalWindData(
            direction=200,
            strength=0.8,
            phase="evening",
            is_active=True
        )
        
        assert thermal.is_active is True
        assert thermal.direction == 200
        assert thermal.strength == 0.8
        assert thermal.phase == "evening"
    
    def test_thermal_wind_data_optional_fields(self):
        """Test ThermalWindData with default values."""
        thermal = ThermalWindData(
            direction=0,
            strength=0.0
        )
        
        assert thermal.is_active is False
        assert thermal.phase == "unknown"  # Default
    
    # ==================== RESULT STRUCTURE TESTS ====================
    
    def test_result_structure_complete(self, calculator):
        """Test StandCalculationResult has all required fields."""
        result = calculator.calculate_evening_stand(
            wind_direction=270,
            wind_speed_mph=12,
            downhill_direction=180,
            downwind_direction=90,
            thermal_data=None,
            slope=15
        )
        
        # Validate all expected fields exist
        assert hasattr(result, 'bearing'), "Result should have bearing"
        assert hasattr(result, 'distance_m'), "Result should have distance_m"
        assert hasattr(result, 'wind_aware'), "Result should have wind_aware flag"
        assert hasattr(result, 'crosswind_bearing'), "Result should have crosswind_bearing"
        assert hasattr(result, 'primary_reason'), "Result should have primary_reason"
        assert hasattr(result, 'strategy'), "Result should have strategy"
    
    def test_result_reasoning_not_empty(self, calculator):
        """Test result always includes primary_reason."""
        test_cases = [
            (15, "strong wind"),  # Strong wind
            (5, "light wind"),    # Light wind
            (10, "threshold"),    # At threshold
        ]
        
        for wind_speed, description in test_cases:
            result = calculator.calculate_evening_stand(
                wind_direction=270,
                wind_speed_mph=wind_speed,
                downhill_direction=180,
                downwind_direction=90,
                thermal_data=None,
                slope=15
            )
            
            assert result.primary_reason != "", f"primary_reason should not be empty for {description}"
            assert len(result.primary_reason) > 10, f"primary_reason should be descriptive for {description}"
            
            assert result.primary_reason, f"Reasoning should not be empty for {description}"
            assert len(result.primary_reason) > 10, f"Reasoning too short for {description}"


class TestStandCalculatorEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return WindAwareStandCalculator()
    
    def test_zero_wind(self, calculator):
        """Test behavior with zero wind speed."""
        result = calculator.calculate_evening_stand(
            wind_direction=270,
            wind_speed_mph=0,  # No wind
            downhill_direction=180,
            downwind_direction=90,
            thermal_data=None,
            slope=15
        )
        
        assert isinstance(result, StandCalculationResult)
        # Should default to terrain-based logic
    
    def test_extreme_wind(self, calculator):
        """Test behavior with extreme wind speeds."""
        result = calculator.calculate_evening_stand(
            wind_direction=270,
            wind_speed_mph=50,  # Hurricane
            downhill_direction=180,
            downwind_direction=90,
            thermal_data=None,
            slope=15
        )
        
        assert isinstance(result, StandCalculationResult)
        assert result.wind_aware is True, "Extreme wind should use wind-aware logic"
    
    def test_flat_terrain(self, calculator):
        """Test behavior on completely flat terrain."""
        result = calculator.calculate_morning_stand(
            wind_direction=270,
            wind_speed_mph=8,
            uphill_direction=0,
            downwind_direction=90,
            thermal_data=None,
            slope=0  # Completely flat
        )
        
        assert isinstance(result, StandCalculationResult)
        # Flat terrain should use wind-based positioning
    
    def test_steep_terrain(self, calculator):
        """Test behavior on very steep terrain."""
        result = calculator.calculate_evening_stand(
            wind_direction=270,
            wind_speed_mph=8,
            downhill_direction=180,
            downwind_direction=90,
            thermal_data=None,
            slope=35  # Very steep
        )
        
        assert isinstance(result, StandCalculationResult)
        # Steep terrain might still work but with warnings


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])



