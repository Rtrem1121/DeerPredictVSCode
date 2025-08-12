import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from backend.scouting_data_manager import ScoutingDataManager
from backend.scouting_models import ScoutingObservation, ScoutingQuery, ObservationType

@pytest.fixture
def data_manager(tmp_path):
    """Provides a ScoutingDataManager instance with a temporary data file."""
    data_file = tmp_path / "scouting_observations.json"
    return ScoutingDataManager(data_file=str(data_file))

@pytest.fixture
def sample_observation():
    """Provides a sample ScoutingObservation."""
    return ScoutingObservation(
        id="obs1",
        lat=44.2601,
        lon=-72.5754,
        timestamp=datetime.now(),
        observation_type=ObservationType.FRESH_SCRAPE,
        confidence=8.0
    )

class TestScoutingDataManager:
    def test_matches_distance_true(self, data_manager, sample_observation):
        """Test that _matches_distance returns True when within radius."""
        query = ScoutingQuery(lat=44.2601, lon=-72.5754, radius_miles=1.0)
        assert data_manager._matches_distance(sample_observation, query) is True

    def test_matches_distance_false(self, data_manager, sample_observation):
        """Test that _matches_distance returns False when outside radius."""
        query = ScoutingQuery(lat=45.0, lon=-73.0, radius_miles=1.0)
        assert data_manager._matches_distance(sample_observation, query) is False

    def test_matches_type_true(self, data_manager, sample_observation):
        """Test that _matches_type returns True for matching type."""
        query = ScoutingQuery(lat=44.2601, lon=-72.5754, observation_types=[ObservationType.FRESH_SCRAPE])
        assert data_manager._matches_type(sample_observation, query) is True

    def test_matches_type_false(self, data_manager, sample_observation):
        """Test that _matches_type returns False for non-matching type."""
        query = ScoutingQuery(lat=44.2601, lon=-72.5754, observation_types=[ObservationType.RUB_LINE])
        assert data_manager._matches_type(sample_observation, query) is False

    def test_matches_confidence_true(self, data_manager, sample_observation):
        """Test that _matches_confidence returns True for sufficient confidence."""
        query = ScoutingQuery(lat=44.2601, lon=-72.5754, min_confidence=7.0)
        assert data_manager._matches_confidence(sample_observation, query) is True

    def test_matches_confidence_false(self, data_manager, sample_observation):
        """Test that _matches_confidence returns False for insufficient confidence."""
        query = ScoutingQuery(lat=44.2601, lon=-72.5754, min_confidence=9.0)
        assert data_manager._matches_confidence(sample_observation, query) is False

    def test_matches_date_true(self, data_manager, sample_observation):
        """Test that _matches_date returns True for recent observation."""
        query = ScoutingQuery(lat=44.2601, lon=-72.5754, days_back=7)
        assert data_manager._matches_date(sample_observation, query) is True

    def test_matches_date_false(self, data_manager, sample_observation):
        """Test that _matches_date returns False for old observation."""
        sample_observation.timestamp = datetime.now() - timedelta(days=10)
        query = ScoutingQuery(lat=44.2601, lon=-72.5754, days_back=7)
        assert data_manager._matches_date(sample_observation, query) is False

    def test_group_observations(self, data_manager):
        """Test that _group_observations correctly groups observations by proximity."""
        obs1 = ScoutingObservation(lat=44.0, lon=-72.0, timestamp=datetime.now(), observation_type=ObservationType.FRESH_SCRAPE, confidence=8.0)
        obs2 = ScoutingObservation(lat=44.001, lon=-72.001, timestamp=datetime.now(), observation_type=ObservationType.RUB_LINE, confidence=7.0)
        obs3 = ScoutingObservation(lat=45.0, lon=-73.0, timestamp=datetime.now(), observation_type=ObservationType.BEDDING_AREA, confidence=9.0)
        observations = [obs1, obs2, obs3]
        groups = data_manager._group_observations(observations)
        assert len(groups) == 2
        assert len(groups[0]) == 2
        assert len(groups[1]) == 1

    def test_calculate_hot_area(self, data_manager):
        """Test that _calculate_hot_area correctly calculates the details of a hot area."""
        obs1 = ScoutingObservation(lat=44.0, lon=-72.0, timestamp=datetime.now(), observation_type=ObservationType.FRESH_SCRAPE, confidence=8.0)
        obs2 = ScoutingObservation(lat=44.001, lon=-72.001, timestamp=datetime.now(), observation_type=ObservationType.RUB_LINE, confidence=7.0)
        group = [obs1, obs2]
        hot_area = data_manager._calculate_hot_area(group)
        assert hot_area["observation_count"] == 2
        assert hot_area["average_confidence"] == 7.5
        assert set(hot_area["types"]) == {ObservationType.FRESH_SCRAPE.value, ObservationType.RUB_LINE.value}

    def test_calculate_analytics_metrics(self, data_manager):
        """Test that _calculate_analytics_metrics correctly calculates analytics."""
        obs1 = ScoutingObservation(lat=44.0, lon=-72.0, timestamp=datetime.now(), observation_type=ObservationType.FRESH_SCRAPE, confidence=8.0)
        obs2 = ScoutingObservation(lat=44.001, lon=-72.001, timestamp=datetime.now(), observation_type=ObservationType.RUB_LINE, confidence=7.0)
        observations = [obs1, obs2]
        analytics = data_manager._calculate_analytics_metrics(observations)
        assert analytics.total_observations == 2
        assert analytics.average_confidence == 7.5
        assert analytics.observations_by_type == {ObservationType.FRESH_SCRAPE.value: 1, ObservationType.RUB_LINE.value: 1}

    def test_add_observation(self, data_manager, sample_observation):
        """Test adding an observation."""
        obs_id = data_manager.add_observation(sample_observation)
        assert obs_id is not None
        retrieved_obs = data_manager.get_observation_by_id(obs_id)
        assert retrieved_obs.id == obs_id

    def test_get_observations(self, data_manager, sample_observation):
        """Test retrieving observations."""
        data_manager.add_observation(sample_observation)
        query = ScoutingQuery(lat=44.2601, lon=-72.5754, radius_miles=1.0)
        observations = data_manager.get_observations(query)
        assert len(observations) == 1
        assert observations[0].id == sample_observation.id

    def test_update_observation(self, data_manager, sample_observation):
        """Test updating an observation."""
        obs_id = data_manager.add_observation(sample_observation)
        sample_observation.confidence = 9.0
        update_successful = data_manager.update_observation(sample_observation)
        assert update_successful is True
        retrieved_obs = data_manager.get_observation_by_id(obs_id)
        assert retrieved_obs.confidence == 9.0

    def test_delete_observation(self, data_manager, sample_observation):
        """Test deleting an observation."""
        obs_id = data_manager.add_observation(sample_observation)
        delete_successful = data_manager.delete_observation(obs_id)
        assert delete_successful is True
        retrieved_obs = data_manager.get_observation_by_id(obs_id)
        assert retrieved_obs is None
