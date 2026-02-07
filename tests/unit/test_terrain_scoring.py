"""Tests for backend.utils.terrain_scoring — unified terrain scoring module."""

import pytest
import numpy as np

from backend.utils.terrain_scoring import (
    classify_rut_phase,
    detect_drainages,
    detect_ridgelines,
    ridge_proximity_preference,
    rut_adjusted_activity,
    scent_carry_distance,
    scent_cone_half_width,
    season_canopy_score,
    slope_preference,
)


# ---------------------------------------------------------------------------
# Slope preference
# ---------------------------------------------------------------------------

class TestSlopePreference:
    def test_flat_ground_low_score(self):
        """0° flat ground should score low (exposed)."""
        assert slope_preference(0.0) == pytest.approx(0.2, abs=0.01)

    def test_gentle_ramp(self):
        """3° should be ramping up but not at plateau."""
        score = slope_preference(3.0)
        assert 0.5 < score < 1.0

    def test_plateau_range(self):
        """5–22° should all score 1.0 (prime terrain)."""
        for deg in [5, 8, 10, 12, 15, 18, 20, 22]:
            assert slope_preference(float(deg)) == pytest.approx(1.0), f"Failed at {deg}°"

    def test_old_dead_zone_now_scores_well(self):
        """20° used to score 0.0 in old formula — now it's 1.0 (prime bedding)."""
        assert slope_preference(20.0) == pytest.approx(1.0)

    def test_steep_rampdown(self):
        """25° should score less but still positive."""
        score = slope_preference(25.0)
        assert 0.3 < score < 0.9

    def test_very_steep_zero(self):
        """35°+ should score 0."""
        assert slope_preference(35.0) == pytest.approx(0.0, abs=0.01)
        assert slope_preference(45.0) == 0.0

    def test_negative_slope(self):
        assert slope_preference(-5.0) == 0.0

    def test_always_bounded(self):
        for deg in range(-10, 60):
            score = slope_preference(float(deg))
            assert 0.0 <= score <= 1.0, f"Out of bounds at {deg}°"


# ---------------------------------------------------------------------------
# Ridge proximity preference
# ---------------------------------------------------------------------------

class TestRidgeProximityPreference:
    def test_valley_floor_low(self):
        """Bottom 10% of elevation — poor for bedding."""
        score = ridge_proximity_preference(110.0, 100.0, 200.0)
        assert score < 0.3

    def test_midslope_moderate(self):
        """50th percentile — decent travel terrain."""
        score = ridge_proximity_preference(150.0, 100.0, 200.0)
        assert 0.5 < score < 1.0

    def test_upper_third_high(self):
        """80th percentile — prime bedding zone."""
        score = ridge_proximity_preference(180.0, 100.0, 200.0)
        assert score >= 0.9

    def test_ridgetop_good_but_not_peak(self):
        """100th percentile — exposed ridgetop, still good."""
        score = ridge_proximity_preference(200.0, 100.0, 200.0)
        assert 0.6 < score < 1.0

    def test_old_formula_comparison(self):
        """60th percentile used to be optimal — now it's mid-range."""
        old_optimal = ridge_proximity_preference(160.0, 100.0, 200.0)  # 60th pct
        new_optimal = ridge_proximity_preference(180.0, 100.0, 200.0)  # 80th pct
        assert new_optimal >= old_optimal

    def test_always_bounded(self):
        for e in range(100, 210, 5):
            score = ridge_proximity_preference(float(e), 100.0, 200.0)
            assert 0.0 <= score <= 1.0, f"Out of bounds at elev={e}"


# ---------------------------------------------------------------------------
# Ridgeline detection
# ---------------------------------------------------------------------------

class TestRidgelineDetection:
    def test_ridge_on_peak(self):
        """A peak (high TPI, low slope, real relief) should score high."""
        # 10x10 grid: single peak in center
        tpi_large = np.zeros((10, 10), dtype="float32")
        tpi_large[5, 5] = 5.0
        slope = np.full((10, 10), 5.0, dtype="float32")
        relief = np.full((10, 10), 10.0, dtype="float32")

        result = detect_ridgelines(tpi_large, slope, relief)
        assert result[5, 5] > 0.5

    def test_valley_not_ridge(self):
        """A valley (negative TPI) should not score as ridge."""
        tpi_large = np.full((10, 10), -5.0, dtype="float32")
        slope = np.full((10, 10), 5.0, dtype="float32")
        relief = np.full((10, 10), 10.0, dtype="float32")

        result = detect_ridgelines(tpi_large, slope, relief)
        assert np.max(result) < 0.2

    def test_flat_plain_not_ridge(self):
        """Flat terrain with no relief should not be a ridge."""
        tpi_large = np.full((10, 10), 0.5, dtype="float32")
        slope = np.full((10, 10), 1.0, dtype="float32")
        relief = np.full((10, 10), 0.5, dtype="float32")

        result = detect_ridgelines(tpi_large, slope, relief)
        assert np.max(result) < 0.3

    def test_output_shape_preserved(self):
        result = detect_ridgelines(
            np.zeros((20, 30)), np.zeros((20, 30)), np.ones((20, 30))
        )
        assert result.shape == (20, 30)

    def test_bounded_0_1(self):
        result = detect_ridgelines(
            np.random.randn(20, 20).astype("float32") * 5,
            np.random.rand(20, 20).astype("float32") * 30,
            np.random.rand(20, 20).astype("float32") * 15,
        )
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)


# ---------------------------------------------------------------------------
# Drainage detection
# ---------------------------------------------------------------------------

class TestDrainageDetection:
    def test_valley_scores_high(self):
        """Negative TPI + positive curvature = drainage."""
        tpi_small = np.full((10, 10), -3.0, dtype="float32")
        tpi_large = np.full((10, 10), -2.0, dtype="float32")
        curvature = np.full((10, 10), 0.08, dtype="float32")
        relief = np.full((10, 10), 8.0, dtype="float32")

        result = detect_drainages(tpi_small, tpi_large, curvature, relief)
        assert np.mean(result) > 0.3

    def test_ridge_not_drainage(self):
        """Positive TPI (ridge) should not be drainage."""
        tpi_small = np.full((10, 10), 3.0, dtype="float32")
        tpi_large = np.full((10, 10), 2.0, dtype="float32")
        curvature = np.full((10, 10), 0.0, dtype="float32")
        relief = np.full((10, 10), 8.0, dtype="float32")

        result = detect_drainages(tpi_small, tpi_large, curvature, relief)
        assert np.max(result) < 0.1

    def test_bounded_0_1(self):
        result = detect_drainages(
            np.random.randn(20, 20).astype("float32") * 3,
            np.random.randn(20, 20).astype("float32") * 3,
            np.random.randn(20, 20).astype("float32") * 0.1,
            np.random.rand(20, 20).astype("float32") * 15 + 0.1,
        )
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)


# ---------------------------------------------------------------------------
# Season canopy scoring
# ---------------------------------------------------------------------------

class TestSeasonCanopyScore:
    def test_summer_full_weight(self):
        """July with good canopy should score well."""
        score = season_canopy_score(85.0, 0.7, month=7)
        assert score > 0.4

    def test_october_half_weight(self):
        """October is transitional — half weight."""
        july = season_canopy_score(85.0, 0.7, month=7)
        oct = season_canopy_score(85.0, 0.7, month=10)
        assert oct == pytest.approx(july * 0.5, abs=0.01)

    def test_november_nearly_zero(self):
        """November leaf-off — deciduous canopy is noise."""
        score = season_canopy_score(70.0, 0.5, month=11)
        assert score < 0.1

    def test_november_conifer_bonus(self):
        """High canopy (>80%) in November = conifers, gets partial credit."""
        deciduous = season_canopy_score(70.0, 0.5, month=11)
        conifer = season_canopy_score(90.0, 0.7, month=11)
        assert conifer > deciduous

    def test_low_canopy_always_low(self):
        """Low canopy (<60%) always scores near zero."""
        assert season_canopy_score(30.0, 0.1, month=7) < 0.1

    def test_bounded_0_1(self):
        for month in range(1, 13):
            for canopy in [0, 30, 60, 80, 100]:
                for ndvi in [0, 0.3, 0.5, 0.8]:
                    score = season_canopy_score(float(canopy), ndvi, month)
                    assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Rut phase classification
# ---------------------------------------------------------------------------

class TestRutPhaseClassification:
    def test_early_season(self):
        assert classify_rut_phase(9, 15) == "early_season"
        assert classify_rut_phase(10, 10) == "early_season"
        assert classify_rut_phase(6, 1) == "early_season"

    def test_pre_rut(self):
        assert classify_rut_phase(10, 25) == "pre_rut"
        assert classify_rut_phase(11, 2) == "pre_rut"

    def test_seeking(self):
        assert classify_rut_phase(11, 5) == "seeking"
        assert classify_rut_phase(11, 9) == "seeking"

    def test_peak_rut(self):
        assert classify_rut_phase(11, 10) == "peak_rut"
        assert classify_rut_phase(11, 15) == "peak_rut"
        assert classify_rut_phase(11, 22) == "peak_rut"

    def test_post_rut(self):
        assert classify_rut_phase(11, 25) == "post_rut"
        assert classify_rut_phase(12, 3) == "post_rut"

    def test_late_season(self):
        assert classify_rut_phase(12, 10) == "late_season"
        assert classify_rut_phase(12, 25) == "late_season"

    def test_january_is_early(self):
        assert classify_rut_phase(1, 15) == "early_season"


# ---------------------------------------------------------------------------
# Rut-adjusted activity
# ---------------------------------------------------------------------------

class TestRutAdjustedActivity:
    def test_dawn_always_high(self):
        for phase in ["early_season", "pre_rut", "seeking", "peak_rut", "post_rut"]:
            assert rut_adjusted_activity(7, phase) == "high"

    def test_dusk_always_high(self):
        for phase in ["early_season", "pre_rut", "peak_rut"]:
            assert rut_adjusted_activity(17, phase) == "high"

    def test_midday_early_season_low(self):
        """Standard non-rut midday = low activity."""
        assert rut_adjusted_activity(12, "early_season") == "low"
        assert rut_adjusted_activity(14, "early_season") == "low"

    def test_midday_peak_rut_high(self):
        """THIS IS THE KEY FIX: peak rut midday = high activity."""
        assert rut_adjusted_activity(10, "peak_rut") == "high"
        assert rut_adjusted_activity(12, "peak_rut") == "high"
        assert rut_adjusted_activity(14, "peak_rut") == "high"

    def test_midday_seeking_high(self):
        """Seeking phase bucks are cruising midday."""
        assert rut_adjusted_activity(11, "seeking") == "high"

    def test_midday_pre_rut_moderate(self):
        """Pre-rut has some midday scrape checking."""
        assert rut_adjusted_activity(12, "pre_rut") == "moderate"


# ---------------------------------------------------------------------------
# Scent carry distance
# ---------------------------------------------------------------------------

class TestScentCarryDistance:
    def test_calm_short_carry(self):
        dist = scent_carry_distance(2.0)
        assert 200 < dist < 300

    def test_moderate_wind(self):
        dist = scent_carry_distance(8.0)
        assert 350 < dist < 500

    def test_strong_wind_long_carry(self):
        dist = scent_carry_distance(15.0)
        assert dist > 500

    def test_cap_at_700(self):
        assert scent_carry_distance(30.0) == 700.0

    def test_zero_wind(self):
        assert scent_carry_distance(0.0) == 150.0

    def test_monotonically_increasing(self):
        prev = 0
        for speed in range(0, 25):
            d = scent_carry_distance(float(speed))
            assert d >= prev
            prev = d


# ---------------------------------------------------------------------------
# Scent cone half-width
# ---------------------------------------------------------------------------

class TestScentConeHalfWidth:
    def test_calm_wide_cone(self):
        assert scent_cone_half_width(1.0) == 90.0

    def test_moderate_standard_cone(self):
        assert scent_cone_half_width(8.0) == 60.0

    def test_strong_tight_cone(self):
        assert scent_cone_half_width(12.0) == 45.0

    def test_very_strong_tightest(self):
        assert scent_cone_half_width(20.0) == 35.0

    def test_decreasing_with_speed(self):
        """Cone narrows as wind increases."""
        prev = 180
        for speed in [0, 3, 6, 10, 15, 20]:
            w = scent_cone_half_width(float(speed))
            assert w <= prev
            prev = w
