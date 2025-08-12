import pytest
import numpy as np
from unittest.mock import Mock, patch
from backend.scouting_prediction_enhancer import ScoutingPredictionEnhancer
from backend.scouting_models import ScoutingObservation, ObservationType, ScoutingQuery

@pytest.fixture
def enhancer():
    """Provides a ScoutingPredictionEnhancer instance."""
    return ScoutingPredictionEnhancer()

@pytest.fixture
def sample_score_maps():
    """Provides sample score maps."""
    return {
        "travel": np.ones((10, 10)),
        "bedding": np.ones((10, 10)),
        "feeding": np.ones((10, 10)),
    }

class TestScoutingPredictionEnhancer:
    def test_get_relevant_observations(self, enhancer):
        """Test that _get_relevant_observations calls the data manager with the correct query."""
        with patch.object(enhancer.data_manager, 'get_observations') as mock_get_observations:
            enhancer._get_relevant_observations(44.0, -72.0)
            mock_get_observations.assert_called_once()
            call_args = mock_get_observations.call_args[0][0]
            assert isinstance(call_args, ScoutingQuery)
            assert call_args.lat == 44.0
            assert call_args.lon == -72.0
            assert call_args.radius_miles == 2.0
            assert call_args.days_back == 60

    def test_prepare_enhanced_maps(self, enhancer, sample_score_maps):
        """Test that _prepare_enhanced_maps creates copies of the score maps."""
        enhanced_maps = enhancer._prepare_enhanced_maps(sample_score_maps)
        assert enhanced_maps is not sample_score_maps
        assert enhanced_maps["travel"] is not sample_score_maps["travel"]
        assert np.array_equal(enhanced_maps["travel"], sample_score_maps["travel"])

    def test_apply_enhancements(self, enhancer, sample_score_maps):
        """Test that _apply_enhancements applies enhancements to the score maps."""
        obs = ScoutingObservation(lat=44.0, lon=-72.0, observation_type=ObservationType.FRESH_SCRAPE, confidence=8.0)
        observations = [obs]
        with patch.object(enhancer, '_apply_observation_enhancement') as mock_apply_enhancement:
            mock_apply_enhancement.return_value = {"boost_applied": 10.0, "mature_buck_indicator": True}
            enhancements_applied, mature_buck_indicators = enhancer._apply_enhancements(observations, sample_score_maps, 44.0, -72.0, 0.04, 10)
            assert len(enhancements_applied) == 1
            assert mature_buck_indicators == 1

    def test_apply_cumulative_bonuses(self, enhancer, sample_score_maps):
        """Test that _apply_cumulative_bonuses applies a cumulative bonus to the score maps."""
        with patch.object(enhancer, '_apply_cumulative_bonus') as mock_apply_cumulative_bonus:
            enhancer._apply_cumulative_bonuses(sample_score_maps, 2)
            mock_apply_cumulative_bonus.assert_called_once()

    def test_apply_scrape_enhancement(self, enhancer, sample_score_maps):
        """Test that _apply_scrape_enhancement applies the correct boost."""
        obs = ScoutingObservation(lat=44.0, lon=-72.0, observation_type=ObservationType.FRESH_SCRAPE, confidence=8.0, scrape_details={'size':'Large', 'freshness':'Fresh', 'licking_branch':True})
        config = enhancer.enhancement_config[ObservationType.FRESH_SCRAPE]
        boost = enhancer._apply_scrape_enhancement(obs, sample_score_maps, 5, 5, 5, config, 1.0, 0.8)
        assert boost > 0

    def test_apply_rub_line_enhancement(self, enhancer, sample_score_maps):
        """Test that _apply_rub_line_enhancement applies the correct boost."""
        obs = ScoutingObservation(lat=44.0, lon=-72.0, observation_type=ObservationType.RUB_LINE, confidence=8.0, rub_details={'tree_diameter_inches':10, 'rub_height_inches':40, 'direction': 'North'})
        config = enhancer.enhancement_config[ObservationType.RUB_LINE]
        boost = enhancer._apply_rub_line_enhancement(obs, sample_score_maps, 5, 5, 5, config, 1.0, 0.8)
        assert boost > 0

    def test_apply_trail_camera_enhancement(self, enhancer, sample_score_maps):
        """Test that _apply_trail_camera_enhancement applies the correct boost."""
        obs = ScoutingObservation(lat=44.0, lon=-72.0, observation_type=ObservationType.TRAIL_CAMERA, confidence=8.0, camera_details={'setup_date': '2023-10-01', 'total_photos': 100, 'deer_photos': 10, 'mature_buck_photos': 2})
        config = enhancer.enhancement_config[ObservationType.TRAIL_CAMERA]
        boost = enhancer._apply_trail_camera_enhancement(obs, sample_score_maps, 5, 5, 5, config, 1.0, 0.8)
        assert boost > 0

    def test_apply_radial_boost(self, enhancer):
        """Test that _apply_radial_boost applies a radial boost to the score map."""
        score_map = np.zeros((10, 10))
        enhancer._apply_radial_boost(score_map, 5, 5, 3, 10)
        assert score_map[5, 5] > 0
        assert score_map[0, 0] == 0
