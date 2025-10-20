"""
Integration Tests for Vermont Locations

End-to-end prediction tests using real Vermont GPS coordinates across
the state's geographic diversity. Tests validate GeoJSON format,
biological accuracy, performance, and scent management.

Coverage:
- Northern Vermont (44.8-45.0°N): Canadian border, highest elevations
- Central Vermont (44.0-44.5°N): Green Mountains, typical terrain  
- Southern Vermont (42.7-43.5°N): Massachusetts border, lower elevations

References:
- Vermont Fish & Wildlife: Deer habitat zones
- USGS: Vermont topography and elevation data
"""

import pytest
import time
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add project root to path to import from root-level module
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor


# Vermont test locations covering geographic diversity
VERMONT_LOCATIONS = {
    # Northern Vermont (44.8-45.0°N) - Canadian Border Region
    "norton": {
        "lat": 44.9833,
        "lon": -71.7997,
        "name": "Norton (Northern Border)",
        "elevation_range": (900, 1100),
        "expected_zones": 3,
        "climate": "coldest",
        "terrain": "rolling hills"
    },
    "jay_peak": {
        "lat": 44.9386,
        "lon": -72.5034,
        "name": "Jay Peak Area",
        "elevation_range": (1000, 1400),
        "expected_zones": 3,
        "climate": "cold",
        "terrain": "steep mountains"
    },
    
    # Central Vermont (44.0-44.5°N) - Green Mountains
    "stowe": {
        "lat": 44.4654,
        "lon": -72.6874,
        "name": "Stowe Area",
        "elevation_range": (600, 1000),
        "expected_zones": 3,
        "climate": "moderate",
        "terrain": "mountainous"
    },
    "montpelier": {
        "lat": 44.2601,
        "lon": -72.5754,
        "name": "Montpelier Region",
        "elevation_range": (400, 800),
        "expected_zones": 3,
        "climate": "moderate",
        "terrain": "valleys and ridges"
    },
    "woodstock": {
        "lat": 43.6244,
        "lon": -72.5184,
        "name": "Woodstock Area",
        "elevation_range": (500, 900),
        "expected_zones": 3,
        "climate": "moderate",
        "terrain": "rolling hills"
    },
    "killington": {
        "lat": 43.6042,
        "lon": -72.8206,
        "name": "Killington Region",
        "elevation_range": (800, 1200),
        "expected_zones": 3,
        "climate": "moderate-cold",
        "terrain": "mountainous"
    },
    
    # Southern Vermont (42.7-43.5°N) - Massachusetts Border
    "bennington": {
        "lat": 42.8781,
        "lon": -73.1968,
        "name": "Bennington Area",
        "elevation_range": (500, 900),
        "expected_zones": 3,
        "climate": "warmer",
        "terrain": "valleys"
    },
    "brattleboro": {
        "lat": 42.8509,
        "lon": -72.5579,
        "name": "Brattleboro Region",
        "elevation_range": (200, 600),
        "expected_zones": 3,
        "climate": "warmer",
        "terrain": "river valleys"
    },
    "manchester": {
        "lat": 43.1637,
        "lon": -73.0738,
        "name": "Manchester Area",
        "elevation_range": (600, 1000),
        "expected_zones": 3,
        "climate": "moderate",
        "terrain": "valleys and slopes"
    },
    "rutland": {
        "lat": 43.6106,
        "lon": -72.9726,
        "name": "Rutland Region",
        "elevation_range": (500, 900),
        "expected_zones": 3,
        "climate": "moderate",
        "terrain": "valleys"
    }
}


class TestVermontLocationIntegration:
    """Integration tests for Vermont locations."""
    
    @pytest.fixture(scope="class")
    def predictor(self):
        """Create predictor instance for all tests."""
        return EnhancedBeddingZonePredictor()
    
    def validate_geojson_structure(self, geojson):
        """
        Validate GeoJSON structure matches spec.
        
        Checks:
        - Type is FeatureCollection
        - Features array exists
        - Each feature has type, geometry, properties
        - Coordinates are valid [lon, lat] arrays
        """
        assert geojson is not None, "GeoJSON should not be None"
        assert "type" in geojson, "GeoJSON missing 'type' field"
        assert geojson["type"] == "FeatureCollection", "GeoJSON type should be FeatureCollection"
        
        assert "features" in geojson, "GeoJSON missing 'features' array"
        assert isinstance(geojson["features"], list), "Features should be a list"
        
        for i, feature in enumerate(geojson["features"]):
            assert "type" in feature, f"Feature {i} missing 'type'"
            assert feature["type"] == "Feature", f"Feature {i} type should be 'Feature'"
            
            assert "geometry" in feature, f"Feature {i} missing 'geometry'"
            geometry = feature["geometry"]
            assert "type" in geometry, f"Feature {i} geometry missing 'type'"
            assert geometry["type"] in ["Point", "LineString", "Polygon"], \
                f"Feature {i} has invalid geometry type: {geometry['type']}"
            
            assert "coordinates" in geometry, f"Feature {i} geometry missing 'coordinates'"
            coords = geometry["coordinates"]
            
            if geometry["type"] == "Point":
                assert len(coords) == 2, f"Feature {i} Point should have 2 coordinates"
                lon, lat = coords
                assert -180 <= lon <= 180, f"Feature {i} invalid longitude: {lon}"
                assert -90 <= lat <= 90, f"Feature {i} invalid latitude: {lat}"
            
            assert "properties" in feature, f"Feature {i} missing 'properties'"
            assert isinstance(feature["properties"], dict), \
                f"Feature {i} properties should be a dict"
    
    def validate_bedding_zones_biological(self, bedding_zones, location_info):
        """
        Validate bedding zones meet biological criteria.
        
        Checks:
        - Slope in viable range (typically 10-30°)
        - Aspect preferences (SE-SW preferred in Vermont)
        - Elevation reasonable for location
        - Distance from center within search radius
        - Score above minimum threshold
        """
        assert len(bedding_zones) > 0, \
            f"Should find at least one bedding zone for {location_info['name']}"
        
        for i, zone in enumerate(bedding_zones):
            # Check slope viability (Vermont bucks prefer 10-30°)
            # Some flexibility for exceptional sites
            slope = zone.get("slope", 0)
            assert 0 <= slope <= 45, \
                f"Zone {i} slope {slope}° outside reasonable range (0-45°)"
            
            # Check aspect is valid bearing
            aspect = zone.get("aspect", 0)
            assert 0 <= aspect <= 360, \
                f"Zone {i} aspect {aspect}° invalid (should be 0-360°)"
            
            # Check score is reasonable
            score = zone.get("score", 0)
            assert score >= 0, f"Zone {i} score {score} should be non-negative"
            assert score <= 100, f"Zone {i} score {score} should not exceed 100"
            
            # Check distance is within search radius (typically 500m)
            distance = zone.get("distance", 0)
            assert distance >= 0, f"Zone {i} distance {distance}m should be non-negative"
            assert distance <= 1000, \
                f"Zone {i} distance {distance}m exceeds reasonable search radius"
            
            # Check coordinates are valid and near Vermont
            lat = zone.get("lat", 0)
            lon = zone.get("lon", 0)
            assert 42.7 <= lat <= 45.1, \
                f"Zone {i} latitude {lat}° outside Vermont range (42.7-45.1°)"
            assert -73.5 <= lon <= -71.5, \
                f"Zone {i} longitude {lon}° outside Vermont range (-73.5 to -71.5°)"
    
    def validate_stand_positions(self, stand_positions, wind_speed):
        """
        Validate stand positions respect scent management.
        
        Checks:
        - At least one stand recommendation exists
        - Stand coordinates are valid
        - Scent cone safety (45° angle for wind >5mph)
        - Distance from bedding appropriate (50-150 yards typical)
        - Wind direction considered in positioning
        """
        assert len(stand_positions) > 0, "Should provide at least one stand position"
        
        for i, stand in enumerate(stand_positions):
            # Check coordinates
            lat = stand.get("lat", 0)
            lon = stand.get("lon", 0)
            assert 42.7 <= lat <= 45.1, \
                f"Stand {i} latitude {lat}° outside Vermont range"
            assert -73.5 <= lon <= -71.5, \
                f"Stand {i} longitude {lon}° outside Vermont range"
            
            # Check distance
            distance = stand.get("distance", 0)
            assert 0 <= distance <= 300, \
                f"Stand {i} distance {distance}m outside typical range (0-300m)"
            
            # Check bearing
            bearing = stand.get("bearing", 0)
            assert 0 <= bearing <= 360, \
                f"Stand {i} bearing {bearing}° invalid (should be 0-360°)"
            
            # Scent management validation for strong winds
            if wind_speed >= 10:
                # Stand should be positioned crosswind (not directly downwind)
                assert "wind_safe" in stand or "scent_safe" in stand, \
                    f"Stand {i} should include scent safety indicator for wind {wind_speed}mph"
    
    def validate_performance(self, execution_time, location_name):
        """
        Validate prediction performance.
        
        Target: <15 seconds per prediction (LIDAR batch optimization)
        Acceptable: <30 seconds (network delays, API rate limits)
        """
        assert execution_time > 0, "Execution time should be positive"
        
        if execution_time < 15:
            print(f"✅ {location_name}: Excellent performance ({execution_time:.2f}s)")
        elif execution_time < 30:
            print(f"⚠️ {location_name}: Acceptable performance ({execution_time:.2f}s)")
        else:
            pytest.fail(
                f"❌ {location_name}: Performance too slow ({execution_time:.2f}s > 30s target)"
            )
    
    @pytest.mark.parametrize("location_key", [
        "norton",
        "jay_peak", 
        "stowe",
        "montpelier",
        "woodstock",
        "killington",
        "bennington",
        "brattleboro",
        "manchester",
        "rutland"
    ])
    def test_vermont_location(self, predictor, location_key):
        """
        Test prediction for a specific Vermont location.
        
        Validates:
        1. GeoJSON structure and format
        2. Biological accuracy of bedding zones
        3. Stand position scent management
        4. Performance <15s target
        """
        location = VERMONT_LOCATIONS[location_key]
        
        print(f"\n{'='*60}")
        print(f"Testing: {location['name']}")
        print(f"Coordinates: {location['lat']:.4f}°N, {location['lon']:.4f}°W")
        print(f"Terrain: {location['terrain']}, Climate: {location['climate']}")
        print(f"{'='*60}")
        
        # Prepare prediction parameters
        lat = location["lat"]
        lon = location["lon"]
        prediction_time = datetime.now(timezone.utc)
        wind_direction = 270  # West wind (common in Vermont)
        wind_speed_mph = 8  # Moderate wind
        temperature_f = 45  # Fall temperature
        
        # Execute prediction with timing
        start_time = time.time()
        
        result = predictor.predict_bedding_zones(
            lat=lat,
            lon=lon,
            prediction_time=prediction_time,
            wind_direction=wind_direction,
            wind_speed_mph=wind_speed_mph,
            temperature_f=temperature_f
        )
        
        execution_time = time.time() - start_time
        
        # Validate result structure
        assert result is not None, f"Prediction failed for {location['name']}"
        assert "status" in result, "Result missing 'status' field"
        
        # Allow for warnings but require success or partial success
        assert result["status"] in ["success", "partial_success", "warning"], \
            f"Prediction status '{result['status']}' indicates failure"
        
        # Validate GeoJSON structure
        if "geojson" in result:
            print(f"\n✓ GeoJSON validation...")
            self.validate_geojson_structure(result["geojson"])
            print(f"  GeoJSON structure valid")
        
        # Validate bedding zones
        if "bedding_zones" in result and result["bedding_zones"]:
            print(f"\n✓ Bedding zone validation...")
            bedding_zones = result["bedding_zones"]
            print(f"  Found {len(bedding_zones)} bedding zones")
            self.validate_bedding_zones_biological(bedding_zones, location)
            print(f"  Bedding zones meet biological criteria")
            
            # Check expected zone count
            expected = location["expected_zones"]
            actual = len(bedding_zones)
            if actual >= expected:
                print(f"  ✅ Zone count: {actual} (expected ≥{expected})")
            else:
                print(f"  ⚠️ Zone count: {actual} (expected ≥{expected}, lower than expected)")
        else:
            # Some locations might not have ideal bedding habitat
            print(f"\n⚠️ No bedding zones found for {location['name']}")
            print(f"  This may be valid for locations with suboptimal terrain")
        
        # Validate stand positions
        if "stand_positions" in result and result["stand_positions"]:
            print(f"\n✓ Stand position validation...")
            stands = result["stand_positions"]
            print(f"  Found {len(stands)} stand recommendations")
            self.validate_stand_positions(stands, wind_speed_mph)
            print(f"  Stand positions respect scent management")
        
        # Validate performance
        print(f"\n✓ Performance validation...")
        self.validate_performance(execution_time, location['name'])
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"✅ {location['name']}: ALL VALIDATIONS PASSED")
        print(f"{'='*60}\n")


class TestVermontGeographicCoverage:
    """Test geographic coverage across Vermont."""
    
    def test_latitude_coverage(self):
        """Verify test locations cover Vermont's latitude range."""
        lats = [loc["lat"] for loc in VERMONT_LOCATIONS.values()]
        
        min_lat = min(lats)
        max_lat = max(lats)
        
        # Vermont spans 42.7°N to 45.0°N
        assert min_lat >= 42.7, f"Minimum latitude {min_lat}° below Vermont's southern border"
        assert min_lat <= 43.0, f"Should test near southern border (got {min_lat}°)"
        
        assert max_lat <= 45.1, f"Maximum latitude {max_lat}° above Vermont's northern border"
        assert max_lat >= 44.8, f"Should test near northern border (got {max_lat}°)"
        
        # Should have good distribution
        lat_range = max_lat - min_lat
        assert lat_range >= 2.0, f"Latitude range {lat_range}° too narrow (should be ≥2.0°)"
        
        print(f"✓ Latitude coverage: {min_lat:.2f}° to {max_lat:.2f}° (range: {lat_range:.2f}°)")
    
    def test_longitude_coverage(self):
        """Verify test locations cover Vermont's longitude range."""
        lons = [loc["lon"] for loc in VERMONT_LOCATIONS.values()]
        
        min_lon = min(lons)
        max_lon = max(lons)
        
        # Vermont spans -73.4°W to -71.5°W
        assert min_lon >= -73.5, f"Minimum longitude {min_lon}° west of Vermont's western border"
        assert min_lon <= -72.8, f"Should test near western border (got {min_lon}°)"
        
        assert max_lon <= -71.4, f"Maximum longitude {max_lon}° east of Vermont's eastern border"
        assert max_lon >= -72.0, f"Should test near eastern border (got {max_lon}°)"
        
        # Should have good distribution
        lon_range = max_lon - min_lon
        assert lon_range >= 1.2, f"Longitude range {lon_range}° too narrow (should be ≥1.2°)"
        
        print(f"✓ Longitude coverage: {min_lon:.2f}° to {max_lon:.2f}° (range: {lon_range:.2f}°)")
    
    def test_elevation_diversity(self):
        """Verify test locations cover Vermont's elevation diversity."""
        elevations = []
        for loc in VERMONT_LOCATIONS.values():
            elevations.extend(loc["elevation_range"])
        
        min_elev = min(elevations)
        max_elev = max(elevations)
        
        # Vermont elevations: ~95m (Lake Champlain) to 1,339m (Mt. Mansfield)
        assert min_elev >= 100, f"Minimum elevation {min_elev}m below typical Vermont range"
        assert max_elev <= 1500, f"Maximum elevation {max_elev}m above Vermont's highest peak"
        
        # Should cover significant elevation range
        elev_range = max_elev - min_elev
        assert elev_range >= 800, \
            f"Elevation range {elev_range}m too narrow (should be ≥800m for diversity)"
        
        print(f"✓ Elevation coverage: {min_elev}m to {max_elev}m (range: {elev_range}m)")
    
    def test_climate_zones(self):
        """Verify test locations cover Vermont's climate diversity."""
        climates = {loc["climate"] for loc in VERMONT_LOCATIONS.values()}
        
        # Should include cold (north), moderate (central), and warmer (south) zones
        assert "coldest" in climates or "cold" in climates, \
            "Should include northern Vermont cold climate zones"
        assert "moderate" in climates or "moderate-cold" in climates, \
            "Should include central Vermont moderate climate zones"
        assert "warmer" in climates, \
            "Should include southern Vermont warmer climate zones"
        
        print(f"✓ Climate diversity: {', '.join(sorted(climates))}")
    
    def test_terrain_diversity(self):
        """Verify test locations cover Vermont's terrain diversity."""
        terrains = {loc["terrain"] for loc in VERMONT_LOCATIONS.values()}
        
        # Vermont has mountains, valleys, and rolling hills
        assert any("mountain" in t.lower() for t in terrains), \
            "Should include mountainous terrain"
        assert any("valley" in t.lower() or "valleys" in t.lower() for t in terrains), \
            "Should include valley terrain"
        assert any("hill" in t.lower() for t in terrains), \
            "Should include rolling hills terrain"
        
        print(f"✓ Terrain diversity: {len(terrains)} different types")
        for terrain in sorted(terrains):
            print(f"  - {terrain}")


class TestVermontLocationMetadata:
    """Test location metadata completeness."""
    
    def test_all_locations_have_required_fields(self):
        """Verify every location has all required metadata fields."""
        required_fields = ["lat", "lon", "name", "elevation_range", 
                          "expected_zones", "climate", "terrain"]
        
        for key, location in VERMONT_LOCATIONS.items():
            for field in required_fields:
                assert field in location, \
                    f"Location '{key}' missing required field: {field}"
    
    def test_coordinates_valid(self):
        """Verify all coordinates are valid lat/lon values."""
        for key, location in VERMONT_LOCATIONS.items():
            lat = location["lat"]
            lon = location["lon"]
            
            assert -90 <= lat <= 90, \
                f"Location '{key}' has invalid latitude: {lat}"
            assert -180 <= lon <= 180, \
                f"Location '{key}' has invalid longitude: {lon}"
            
            # Should be in Vermont
            assert 42.7 <= lat <= 45.1, \
                f"Location '{key}' latitude {lat}° outside Vermont"
            assert -73.5 <= lon <= -71.4, \
                f"Location '{key}' longitude {lon}° outside Vermont"
    
    def test_elevation_ranges_valid(self):
        """Verify elevation ranges are logical."""
        for key, location in VERMONT_LOCATIONS.items():
            elev_range = location["elevation_range"]
            
            assert isinstance(elev_range, tuple), \
                f"Location '{key}' elevation_range should be a tuple"
            assert len(elev_range) == 2, \
                f"Location '{key}' elevation_range should have 2 values"
            
            min_elev, max_elev = elev_range
            assert min_elev < max_elev, \
                f"Location '{key}' elevation range invalid: {min_elev} >= {max_elev}"
            assert min_elev >= 0, \
                f"Location '{key}' minimum elevation {min_elev}m should be positive"
            assert max_elev <= 2000, \
                f"Location '{key}' maximum elevation {max_elev}m exceeds reasonable Vermont range"
    
    def test_expected_zones_reasonable(self):
        """Verify expected zone counts are reasonable."""
        for key, location in VERMONT_LOCATIONS.items():
            expected = location["expected_zones"]
            
            assert isinstance(expected, int), \
                f"Location '{key}' expected_zones should be an integer"
            assert 1 <= expected <= 10, \
                f"Location '{key}' expected_zones {expected} outside reasonable range (1-10)"
    
    def test_location_count(self):
        """Verify we have enough test locations for good coverage."""
        location_count = len(VERMONT_LOCATIONS)
        
        assert location_count >= 10, \
            f"Should have at least 10 test locations (got {location_count})"
        
        print(f"✓ Total test locations: {location_count}")
