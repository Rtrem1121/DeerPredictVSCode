import pytest
from backend.distance_scorer import DistanceScorer, ProximityFactors

@pytest.fixture
def scorer():
    """Provides a DistanceScorer instance."""
    return DistanceScorer()

class TestDistanceScorer:
    def test_calculate_road_impact_score(self, scorer):
        """Test the calculate_road_impact_score method."""
        assert scorer.calculate_road_impact_score(1000) == 95.0
        assert scorer.calculate_road_impact_score(400) > 70.0
        assert scorer.calculate_road_impact_score(200) > 40.0
        assert scorer.calculate_road_impact_score(100) > 10.0
        assert scorer.calculate_road_impact_score(0) == 10.0

    def test_calculate_agricultural_proximity_score(self, scorer):
        """Test the calculate_agricultural_proximity_score method."""
        assert scorer.calculate_agricultural_proximity_score(50) == 95.0
        assert scorer.calculate_agricultural_proximity_score(200) > 75.0
        assert scorer.calculate_agricultural_proximity_score(500) > 50.0
        assert scorer.calculate_agricultural_proximity_score(1000) > 25.0
        assert scorer.calculate_agricultural_proximity_score(2000) == 25.0

    def test_calculate_stand_placement_score(self, scorer):
        """Test the calculate_stand_placement_score method."""
        assert scorer.calculate_stand_placement_score(100) > 85.0
        assert scorer.calculate_stand_placement_score(250) > 40.0
        assert scorer.calculate_stand_placement_score(10) == 25.0
        assert scorer.calculate_stand_placement_score(500) == 25.0

    def test_calculate_escape_route_score(self, scorer):
        """Test the calculate_escape_route_score method."""
        assert scorer.calculate_escape_route_score(25) == 95.0
        assert scorer.calculate_escape_route_score(100) > 75.0
        assert scorer.calculate_escape_route_score(200) > 50.0
        assert scorer.calculate_escape_route_score(400) > 20.0
        assert scorer.calculate_escape_route_score(700) == 20.0

    def test_calculate_concealment_score(self, scorer):
        """Test the calculate_concealment_score method."""
        assert scorer.calculate_concealment_score(20) == 95.0
        assert scorer.calculate_concealment_score(50) > 80.0
        assert scorer.calculate_concealment_score(80) > 60.0
        assert scorer.calculate_concealment_score(150) > 30.0
        assert scorer.calculate_concealment_score(250) == 20.0

    def test_calculate_water_proximity_score(self, scorer):
        """Test the calculate_water_proximity_score method."""
        assert scorer.calculate_water_proximity_score(50) == 90.0
        assert scorer.calculate_water_proximity_score(200) > 70.0
        assert scorer.calculate_water_proximity_score(500) > 45.0
        assert scorer.calculate_water_proximity_score(1000) > 20.0
        assert scorer.calculate_water_proximity_score(2000) == 20.0

    def test_calculate_terrain_edge_score(self, scorer):
        """Test the calculate_terrain_edge_score method."""
        assert scorer.calculate_terrain_edge_score(25) == 90.0
        assert scorer.calculate_terrain_edge_score(100) > 70.0
        assert scorer.calculate_terrain_edge_score(200) > 45.0
        assert scorer.calculate_terrain_edge_score(500) == 30.0
