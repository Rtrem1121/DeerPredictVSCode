"""
Unit Tests for Bedding Site Domain Models

Tests BeddingZone, BeddingZoneCandidate, and BeddingScoreBreakdown
with focus on Vermont whitetail deer ecology and biological accuracy.

References:
- Nelson & Mech (1981): Bedding site selection
- Marchinton & Hirth (1984): Mature buck patterns
"""

import pytest
from backend.models.bedding_site import (
    BeddingZone,
    BeddingZoneCandidate,
    BeddingScoreBreakdown,
    BeddingZoneType
)


class TestBeddingZoneType:
    """Test bedding zone categorization enum."""
    
    def test_zone_type_values(self):
        """Verify zone type enum values match expected strings."""
        assert BeddingZoneType.PRIMARY.value == "primary"
        assert BeddingZoneType.SECONDARY.value == "secondary"
        assert BeddingZoneType.ESCAPE.value == "escape"
    
    def test_zone_type_iteration(self):
        """Verify all zone types are accessible."""
        zone_types = list(BeddingZoneType)
        assert len(zone_types) == 3
        assert BeddingZoneType.PRIMARY in zone_types
        assert BeddingZoneType.SECONDARY in zone_types
        assert BeddingZoneType.ESCAPE in zone_types


class TestBeddingScoreBreakdown:
    """Test bedding score breakdown model."""
    
    def test_default_initialization(self):
        """Test score breakdown initializes with zero scores."""
        breakdown = BeddingScoreBreakdown()
        
        assert breakdown.slope_score == 0.0
        assert breakdown.aspect_score == 0.0
        assert breakdown.elevation_score == 0.0
        assert breakdown.canopy_score == 0.0
        assert breakdown.food_score == 0.0
        assert breakdown.road_distance_score == 0.0
        assert breakdown.escape_routes_score == 0.0
        assert breakdown.thermal_wind_score == 0.0
        assert breakdown.scent_management_score == 0.0
        assert breakdown.terrain_composite == 0.0
        assert breakdown.habitat_composite == 0.0
        assert breakdown.security_composite == 0.0
        assert breakdown.total_score == 0.0
        assert breakdown.primary_factors == []
        assert breakdown.limiting_factors == []
    
    def test_custom_initialization(self):
        """Test score breakdown with custom values."""
        breakdown = BeddingScoreBreakdown(
            slope_score=85.0,
            aspect_score=90.0,
            canopy_score=95.0,
            terrain_composite=87.5,
            habitat_composite=92.0,
            total_score=88.5,
            primary_factors=["Perfect leeward shelter", "Dense canopy"],
            limiting_factors=["Low food availability"]
        )
        
        assert breakdown.slope_score == 85.0
        assert breakdown.aspect_score == 90.0
        assert breakdown.canopy_score == 95.0
        assert breakdown.terrain_composite == 87.5
        assert breakdown.habitat_composite == 92.0
        assert breakdown.total_score == 88.5
        assert len(breakdown.primary_factors) == 2
        assert len(breakdown.limiting_factors) == 1
    
    def test_get_summary_format(self):
        """Test summary string formatting."""
        breakdown = BeddingScoreBreakdown(
            slope_score=85.0,
            aspect_score=90.0,
            canopy_score=95.0,
            food_score=70.0,
            road_distance_score=80.0,
            scent_management_score=75.0,
            terrain_composite=87.5,
            habitat_composite=82.5,
            security_composite=77.5,
            total_score=82.5,
            primary_factors=["Leeward shelter", "Dense canopy"],
            limiting_factors=["Low food"]
        )
        
        summary = breakdown.get_summary()
        
        # Check total score line
        assert "Total Score: 82.5/100" in summary
        
        # Check composite scores
        assert "Terrain: 87.5" in summary
        assert "slope=85" in summary
        assert "aspect=90" in summary
        
        assert "Habitat: 82.5" in summary
        assert "canopy=95" in summary
        assert "food=70" in summary
        
        assert "Security: 77.5" in summary
        assert "road=80" in summary
        assert "scent=75" in summary
        
        # Check factors
        assert "✅ Strengths: Leeward shelter, Dense canopy" in summary
        assert "⚠️ Limitations: Low food" in summary
    
    def test_get_summary_no_factors(self):
        """Test summary when no factors are provided."""
        breakdown = BeddingScoreBreakdown(total_score=65.0)
        summary = breakdown.get_summary()
        
        assert "Total Score: 65.0/100" in summary
        assert "✅ Strengths" not in summary
        assert "⚠️ Limitations" not in summary


class TestBeddingZoneCandidate:
    """Test bedding zone candidate model."""
    
    def test_basic_initialization(self):
        """Test candidate initialization with required fields."""
        candidate = BeddingZoneCandidate(
            lat=44.5,
            lon=-72.7,
            distance_from_center_m=75.0,
            elevation_m=450.0,
            slope_degrees=18.0,
            aspect_degrees=180.0,
            canopy_coverage=0.75,
            food_availability=0.65,
            road_distance_m=350.0
        )
        
        assert candidate.lat == 44.5
        assert candidate.lon == -72.7
        assert candidate.distance_from_center_m == 75.0
        assert candidate.elevation_m == 450.0
        assert candidate.slope_degrees == 18.0
        assert candidate.aspect_degrees == 180.0
        assert candidate.canopy_coverage == 0.75
        assert candidate.food_availability == 0.65
        assert candidate.road_distance_m == 350.0
        assert candidate.escape_routes == 0  # Default
        assert candidate.final_score == 0.0  # Default
    
    def test_categorize_zone_type_primary(self):
        """Test zone categorization for primary bedding (0-100m)."""
        # Close distance - primary zone
        candidate = BeddingZoneCandidate(
            lat=44.5, lon=-72.7,
            distance_from_center_m=50.0,
            elevation_m=450.0, slope_degrees=18.0, aspect_degrees=180.0,
            canopy_coverage=0.75, food_availability=0.65, road_distance_m=350.0
        )
        
        zone_type = candidate.categorize_zone_type()
        assert zone_type == BeddingZoneType.PRIMARY
        
        # Boundary case - exactly 100m
        candidate.distance_from_center_m = 100.0
        zone_type = candidate.categorize_zone_type()
        assert zone_type == BeddingZoneType.PRIMARY
    
    def test_categorize_zone_type_secondary(self):
        """Test zone categorization for secondary bedding (100-250m)."""
        # Mid-range - secondary zone
        candidate = BeddingZoneCandidate(
            lat=44.5, lon=-72.7,
            distance_from_center_m=175.0,
            elevation_m=450.0, slope_degrees=18.0, aspect_degrees=180.0,
            canopy_coverage=0.75, food_availability=0.65, road_distance_m=350.0
        )
        
        zone_type = candidate.categorize_zone_type()
        assert zone_type == BeddingZoneType.SECONDARY
        
        # Just over 100m boundary
        candidate.distance_from_center_m = 101.0
        zone_type = candidate.categorize_zone_type()
        assert zone_type == BeddingZoneType.SECONDARY
        
        # Exactly at 250m boundary
        candidate.distance_from_center_m = 250.0
        zone_type = candidate.categorize_zone_type()
        assert zone_type == BeddingZoneType.SECONDARY
    
    def test_categorize_zone_type_escape(self):
        """Test zone categorization for escape zones (>250m)."""
        # Far distance - escape zone
        candidate = BeddingZoneCandidate(
            lat=44.5, lon=-72.7,
            distance_from_center_m=350.0,
            elevation_m=450.0, slope_degrees=18.0, aspect_degrees=180.0,
            canopy_coverage=0.75, food_availability=0.65, road_distance_m=350.0
        )
        
        zone_type = candidate.categorize_zone_type()
        assert zone_type == BeddingZoneType.ESCAPE
        
        # Just over 250m boundary
        candidate.distance_from_center_m = 251.0
        zone_type = candidate.categorize_zone_type()
        assert zone_type == BeddingZoneType.ESCAPE
    
    def test_meets_minimum_requirements_all_criteria(self):
        """Test candidate that meets all minimum requirements."""
        candidate = BeddingZoneCandidate(
            lat=44.5, lon=-72.7,
            distance_from_center_m=75.0,
            elevation_m=450.0,
            slope_degrees=18.0,  # ✅ 10-30° range
            aspect_degrees=180.0,
            canopy_coverage=0.75,  # ✅ >60%
            food_availability=0.65,
            road_distance_m=350.0,  # ✅ >200m
            final_score=75.0  # ✅ >60
        )
        
        assert candidate.meets_minimum_requirements() is True
    
    def test_meets_minimum_requirements_slope_too_flat(self):
        """Test candidate fails with slope too flat (<10°)."""
        candidate = BeddingZoneCandidate(
            lat=44.5, lon=-72.7,
            distance_from_center_m=75.0,
            elevation_m=450.0,
            slope_degrees=8.0,  # ❌ Too flat
            aspect_degrees=180.0,
            canopy_coverage=0.75,
            food_availability=0.65,
            road_distance_m=350.0,
            final_score=75.0
        )
        
        assert candidate.meets_minimum_requirements() is False
    
    def test_meets_minimum_requirements_slope_too_steep(self):
        """Test candidate fails with slope too steep (>30°)."""
        candidate = BeddingZoneCandidate(
            lat=44.5, lon=-72.7,
            distance_from_center_m=75.0,
            elevation_m=450.0,
            slope_degrees=35.0,  # ❌ Too steep
            aspect_degrees=180.0,
            canopy_coverage=0.75,
            food_availability=0.65,
            road_distance_m=350.0,
            final_score=75.0
        )
        
        assert candidate.meets_minimum_requirements() is False
    
    def test_meets_minimum_requirements_canopy_too_low(self):
        """Test candidate fails with insufficient canopy (<60%)."""
        candidate = BeddingZoneCandidate(
            lat=44.5, lon=-72.7,
            distance_from_center_m=75.0,
            elevation_m=450.0,
            slope_degrees=18.0,
            aspect_degrees=180.0,
            canopy_coverage=0.55,  # ❌ <60%
            food_availability=0.65,
            road_distance_m=350.0,
            final_score=75.0
        )
        
        assert candidate.meets_minimum_requirements() is False
    
    def test_meets_minimum_requirements_road_too_close(self):
        """Test candidate fails with road too close (<200m)."""
        candidate = BeddingZoneCandidate(
            lat=44.5, lon=-72.7,
            distance_from_center_m=75.0,
            elevation_m=450.0,
            slope_degrees=18.0,
            aspect_degrees=180.0,
            canopy_coverage=0.75,
            food_availability=0.65,
            road_distance_m=150.0,  # ❌ <200m
            final_score=75.0
        )
        
        assert candidate.meets_minimum_requirements() is False
    
    def test_meets_minimum_requirements_score_too_low(self):
        """Test candidate fails with score below threshold (<60)."""
        candidate = BeddingZoneCandidate(
            lat=44.5, lon=-72.7,
            distance_from_center_m=75.0,
            elevation_m=450.0,
            slope_degrees=18.0,
            aspect_degrees=180.0,
            canopy_coverage=0.75,
            food_availability=0.65,
            road_distance_m=350.0,
            final_score=55.0  # ❌ <60
        )
        
        assert candidate.meets_minimum_requirements() is False
    
    def test_meets_minimum_requirements_boundary_cases(self):
        """Test boundary cases for minimum requirements."""
        # Exactly at boundaries - should pass
        candidate = BeddingZoneCandidate(
            lat=44.5, lon=-72.7,
            distance_from_center_m=75.0,
            elevation_m=450.0,
            slope_degrees=10.0,  # Exactly 10° - lower bound
            aspect_degrees=180.0,
            canopy_coverage=0.6000001,  # Just above 60%
            food_availability=0.65,
            road_distance_m=200.0001,  # Just above 200m
            final_score=60.0001  # Just above 60
        )
        
        assert candidate.meets_minimum_requirements() is True
        
        # Upper slope boundary
        candidate.slope_degrees = 30.0
        assert candidate.meets_minimum_requirements() is True


class TestBeddingZone:
    """Test bedding zone model."""
    
    def test_basic_initialization(self):
        """Test bedding zone initialization with required fields."""
        zone = BeddingZone(
            lat=44.5,
            lon=-72.7,
            zone_type=BeddingZoneType.PRIMARY,
            rank=1,
            elevation_m=450.0,
            slope_degrees=18.0,
            aspect_degrees=180.0,
            uphill_direction=0.0,
            canopy_coverage=0.75,
            food_availability=0.65,
            road_distance_m=350.0
        )
        
        assert zone.lat == 44.5
        assert zone.lon == -72.7
        assert zone.zone_type == BeddingZoneType.PRIMARY
        assert zone.rank == 1
        assert zone.elevation_m == 450.0
        assert zone.slope_degrees == 18.0
        assert zone.aspect_degrees == 180.0
        assert zone.uphill_direction == 0.0
        assert zone.canopy_coverage == 0.75
        assert zone.food_availability == 0.65
        assert zone.road_distance_m == 350.0
        
        # Check defaults
        assert zone.dominant_vegetation is None
        assert zone.escape_routes == []
        assert zone.visibility_score == 0.0
        assert zone.thermal_wind_direction is None
        assert zone.thermal_wind_strength == 0.0
        assert zone.scent_cone_safe is True
        assert zone.final_score == 0.0
        assert zone.distance_from_center_m == 0.0
    
    def test_to_geojson_feature_complete(self):
        """Test GeoJSON export with all fields populated."""
        zone = BeddingZone(
            lat=44.5,
            lon=-72.7,
            zone_type=BeddingZoneType.PRIMARY,
            rank=1,
            elevation_m=450.0,
            slope_degrees=18.5,
            aspect_degrees=180.0,
            uphill_direction=0.0,
            canopy_coverage=0.75,
            food_availability=0.65,
            road_distance_m=350.0,
            distance_from_center_m=75.0,
            thermal_wind_direction=270.0,
            final_score=85.5,
            primary_reason="Perfect leeward shelter",
            ecological_context="Dense hemlock-hardwood mix"
        )
        
        geojson = zone.to_geojson_feature()
        
        # Check structure
        assert geojson["type"] == "Feature"
        assert geojson["geometry"]["type"] == "Point"
        assert geojson["geometry"]["coordinates"] == [-72.7, 44.5]  # [lon, lat]
        
        # Check properties
        props = geojson["properties"]
        assert props["zone_type"] == "primary"
        assert props["rank"] == 1
        assert props["score"] == 85.5
        assert props["elevation_m"] == 450.0
        assert props["slope_deg"] == 18.5
        assert props["aspect_deg"] == 180
        assert props["uphill_direction"] == 0
        assert props["canopy_coverage"] == 75.0  # Converted to %
        assert props["food_availability"] == 65.0  # Converted to %
        assert props["road_distance_m"] == 350
        assert props["distance_m"] == 75
        assert props["thermal_direction"] == 270
        assert props["primary_reason"] == "Perfect leeward shelter"
        assert props["ecological_context"] == "Dense hemlock-hardwood mix"
    
    def test_to_geojson_feature_minimal(self):
        """Test GeoJSON export with minimal required fields."""
        zone = BeddingZone(
            lat=44.5,
            lon=-72.7,
            zone_type=BeddingZoneType.SECONDARY,
            rank=2,
            elevation_m=450.0,
            slope_degrees=18.0,
            aspect_degrees=180.0,
            uphill_direction=0.0,
            canopy_coverage=0.65,
            food_availability=0.55,
            road_distance_m=250.0
        )
        
        geojson = zone.to_geojson_feature()
        
        # Check required fields
        assert geojson["type"] == "Feature"
        assert geojson["geometry"]["coordinates"] == [-72.7, 44.5]
        
        props = geojson["properties"]
        assert props["zone_type"] == "secondary"
        assert props["rank"] == 2
        assert props["thermal_direction"] is None  # Not set
        assert props["primary_reason"] == ""
        assert props["ecological_context"] == ""
    
    def test_get_aspect_classification_north(self):
        """Test north-facing aspect classification (315-45°)."""
        zone = BeddingZone(
            lat=44.5, lon=-72.7, zone_type=BeddingZoneType.PRIMARY, rank=1,
            elevation_m=450.0, slope_degrees=18.0, aspect_degrees=0.0,
            uphill_direction=180.0, canopy_coverage=0.75,
            food_availability=0.65, road_distance_m=350.0
        )
        
        # True north
        zone.aspect_degrees = 0.0
        assert zone.get_aspect_classification() == 'north'
        
        # Northeast boundary
        zone.aspect_degrees = 45.0
        assert zone.get_aspect_classification() == 'north'
        
        # Northwest boundary
        zone.aspect_degrees = 315.0
        assert zone.get_aspect_classification() == 'north'
        
        # Just inside north range
        zone.aspect_degrees = 350.0
        assert zone.get_aspect_classification() == 'north'
    
    def test_get_aspect_classification_east(self):
        """Test east-facing aspect classification (45-135°)."""
        zone = BeddingZone(
            lat=44.5, lon=-72.7, zone_type=BeddingZoneType.PRIMARY, rank=1,
            elevation_m=450.0, slope_degrees=18.0, aspect_degrees=90.0,
            uphill_direction=270.0, canopy_coverage=0.75,
            food_availability=0.65, road_distance_m=350.0
        )
        
        # Due east
        zone.aspect_degrees = 90.0
        assert zone.get_aspect_classification() == 'east'
        
        # Just inside east range
        zone.aspect_degrees = 46.0
        assert zone.get_aspect_classification() == 'east'
        
        # Southeast boundary
        zone.aspect_degrees = 135.0
        assert zone.get_aspect_classification() == 'east'
    
    def test_get_aspect_classification_south(self):
        """Test south-facing aspect classification (135-225°)."""
        zone = BeddingZone(
            lat=44.5, lon=-72.7, zone_type=BeddingZoneType.PRIMARY, rank=1,
            elevation_m=450.0, slope_degrees=18.0, aspect_degrees=180.0,
            uphill_direction=0.0, canopy_coverage=0.75,
            food_availability=0.65, road_distance_m=350.0
        )
        
        # Due south
        zone.aspect_degrees = 180.0
        assert zone.get_aspect_classification() == 'south'
        
        # Just inside south range
        zone.aspect_degrees = 136.0
        assert zone.get_aspect_classification() == 'south'
        
        # Southwest boundary
        zone.aspect_degrees = 225.0
        assert zone.get_aspect_classification() == 'south'
    
    def test_get_aspect_classification_west(self):
        """Test west-facing aspect classification (225-315°)."""
        zone = BeddingZone(
            lat=44.5, lon=-72.7, zone_type=BeddingZoneType.PRIMARY, rank=1,
            elevation_m=450.0, slope_degrees=18.0, aspect_degrees=270.0,
            uphill_direction=90.0, canopy_coverage=0.75,
            food_availability=0.65, road_distance_m=350.0
        )
        
        # Due west
        zone.aspect_degrees = 270.0
        assert zone.get_aspect_classification() == 'west'
        
        # Just inside west range
        zone.aspect_degrees = 226.0
        assert zone.get_aspect_classification() == 'west'
        
        # Just before north boundary
        zone.aspect_degrees = 314.0
        assert zone.get_aspect_classification() == 'west'
    
    def test_score_canopy_excellent(self):
        """Test canopy scoring for excellent coverage (≥60%)."""
        zone = BeddingZone(
            lat=44.5, lon=-72.7, zone_type=BeddingZoneType.PRIMARY, rank=1,
            elevation_m=450.0, slope_degrees=18.0, aspect_degrees=180.0,
            uphill_direction=0.0, canopy_coverage=0.75,
            food_availability=0.65, road_distance_m=350.0
        )
        
        # Excellent coverage
        assert zone.score_canopy(0.75) == 100
        assert zone.score_canopy(0.60) == 100
        assert zone.score_canopy(0.85) == 100
    
    def test_score_canopy_good(self):
        """Test canopy scoring for good coverage (50-60%)."""
        zone = BeddingZone(
            lat=44.5, lon=-72.7, zone_type=BeddingZoneType.PRIMARY, rank=1,
            elevation_m=450.0, slope_degrees=18.0, aspect_degrees=180.0,
            uphill_direction=0.0, canopy_coverage=0.75,
            food_availability=0.65, road_distance_m=350.0
        )
        
        # Good coverage
        assert zone.score_canopy(0.55) == 80
        assert zone.score_canopy(0.50) == 80
        assert zone.score_canopy(0.59) == 80
    
    def test_score_canopy_moderate(self):
        """Test canopy scoring for moderate coverage (40-50%)."""
        zone = BeddingZone(
            lat=44.5, lon=-72.7, zone_type=BeddingZoneType.PRIMARY, rank=1,
            elevation_m=450.0, slope_degrees=18.0, aspect_degrees=180.0,
            uphill_direction=0.0, canopy_coverage=0.75,
            food_availability=0.65, road_distance_m=350.0
        )
        
        # Moderate coverage
        assert zone.score_canopy(0.45) == 60
        assert zone.score_canopy(0.40) == 60
        assert zone.score_canopy(0.49) == 60
    
    def test_score_canopy_poor(self):
        """Test canopy scoring for poor coverage (<40%)."""
        zone = BeddingZone(
            lat=44.5, lon=-72.7, zone_type=BeddingZoneType.PRIMARY, rank=1,
            elevation_m=450.0, slope_degrees=18.0, aspect_degrees=180.0,
            uphill_direction=0.0, canopy_coverage=0.75,
            food_availability=0.65, road_distance_m=350.0
        )
        
        # Poor coverage
        assert zone.score_canopy(0.30) == 40
        assert zone.score_canopy(0.20) == 40
        assert zone.score_canopy(0.10) == 40
        assert zone.score_canopy(0.00) == 40


class TestBeddingZoneIntegration:
    """Integration tests for bedding zone models working together."""
    
    def test_candidate_to_zone_conversion(self):
        """Test converting candidate to final zone."""
        # Create high-quality candidate
        candidate = BeddingZoneCandidate(
            lat=44.5,
            lon=-72.7,
            distance_from_center_m=75.0,
            elevation_m=450.0,
            slope_degrees=18.0,
            aspect_degrees=180.0,
            canopy_coverage=0.75,
            food_availability=0.65,
            road_distance_m=350.0,
            escape_routes=3,
            final_score=85.0
        )
        
        # Verify candidate meets requirements
        assert candidate.meets_minimum_requirements() is True
        zone_type = candidate.categorize_zone_type()
        assert zone_type == BeddingZoneType.PRIMARY
        
        # Convert to bedding zone
        zone = BeddingZone(
            lat=candidate.lat,
            lon=candidate.lon,
            zone_type=zone_type,
            rank=1,
            elevation_m=candidate.elevation_m,
            slope_degrees=candidate.slope_degrees,
            aspect_degrees=candidate.aspect_degrees,
            uphill_direction=(candidate.aspect_degrees + 180) % 360,
            canopy_coverage=candidate.canopy_coverage,
            food_availability=candidate.food_availability,
            road_distance_m=candidate.road_distance_m,
            distance_from_center_m=candidate.distance_from_center_m,
            final_score=candidate.final_score
        )
        
        # Verify zone properties
        assert zone.lat == 44.5
        assert zone.zone_type == BeddingZoneType.PRIMARY
        assert zone.final_score == 85.0
        assert zone.get_aspect_classification() == 'south'
        
        # Test GeoJSON export
        geojson = zone.to_geojson_feature()
        assert geojson["properties"]["zone_type"] == "primary"
        assert geojson["properties"]["distance_m"] == 75
    
    def test_multiple_candidates_ranking(self):
        """Test ranking multiple candidates by score."""
        candidates = [
            BeddingZoneCandidate(
                lat=44.5, lon=-72.7, distance_from_center_m=50.0,
                elevation_m=450.0, slope_degrees=18.0, aspect_degrees=180.0,
                canopy_coverage=0.75, food_availability=0.65,
                road_distance_m=350.0, final_score=85.0
            ),
            BeddingZoneCandidate(
                lat=44.51, lon=-72.71, distance_from_center_m=150.0,
                elevation_m=455.0, slope_degrees=20.0, aspect_degrees=170.0,
                canopy_coverage=0.70, food_availability=0.60,
                road_distance_m=300.0, final_score=78.0
            ),
            BeddingZoneCandidate(
                lat=44.49, lon=-72.69, distance_from_center_m=280.0,
                elevation_m=445.0, slope_degrees=22.0, aspect_degrees=190.0,
                canopy_coverage=0.68, food_availability=0.58,
                road_distance_m=280.0, final_score=72.0
            )
        ]
        
        # Sort by score descending
        sorted_candidates = sorted(candidates, key=lambda c: c.final_score, reverse=True)
        
        # Verify ranking
        assert sorted_candidates[0].final_score == 85.0
        assert sorted_candidates[1].final_score == 78.0
        assert sorted_candidates[2].final_score == 72.0
        
        # Verify zone types
        assert sorted_candidates[0].categorize_zone_type() == BeddingZoneType.PRIMARY
        assert sorted_candidates[1].categorize_zone_type() == BeddingZoneType.SECONDARY
        assert sorted_candidates[2].categorize_zone_type() == BeddingZoneType.ESCAPE
        
        # All should meet minimum requirements
        assert all(c.meets_minimum_requirements() for c in sorted_candidates)
