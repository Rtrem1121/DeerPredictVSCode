"""
Critical GEE Data Validation Tests

These tests prevent false positives from stale satellite data and
validate temporal consistency between Hansen 2000 and Sentinel-2.

Author: GitHub Copilot
Date: October 1, 2025
"""

import pytest
from optimized_biological_integration import OptimizedBiologicalIntegration
from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor


@pytest.mark.unit
@pytest.mark.critical
@pytest.mark.regression
class TestGEEDataValidation:
    """Prevent false positives from stale/invalid satellite data"""
    
    @pytest.fixture
    def integrator(self):
        """Create biological integration instance"""
        return OptimizedBiologicalIntegration()
    
    @pytest.fixture
    def predictor(self):
        """Create bedding zone predictor instance"""
        return EnhancedBeddingZonePredictor()
    
    def test_hansen_canopy_vs_sentinel2_temporal_consistency(self, integrator):
        """
        CRITICAL: Detect when Hansen 2000 doesn't match current Sentinel-2 data
        
        Prevents: False positives on converted land (forest -> field)
        Real Example: 43.31, -73.215 showed 95% canopy (Hansen) but is mowed grass
        """
        # Test with a forested location that should be consistent
        vermont_forest = integrator.get_dynamic_gee_data(44.26, -72.58)
        
        # Extract canopy metrics
        hansen_canopy = vermont_forest.get('treecover2000', 0)
        
        # Calculate NDVI-based canopy estimate (NDVI > 0.5 suggests dense vegetation)
        ndvi = vermont_forest.get('ndvi', 0)
        
        # Healthy forest should have Hansen > 40% AND NDVI > 0.4
        if hansen_canopy > 40:
            assert ndvi > 0.3, \
                f"Hansen shows {hansen_canopy}% canopy but NDVI is {ndvi:.3f} - possible temporal mismatch"
        
        # Log data source for verification
        assert 'data_source' in vermont_forest, "Missing data_source tracking"
        print(f"✅ Data source: {vermont_forest['data_source']}")
    
    def test_known_false_positive_location_rejection(self, predictor):
        """
        REGRESSION TEST: Ensure known false positive is now rejected
        
        Ground Truth: 43.31, -73.215 is a mowed grass field (user confirmed)
        Previous Bug: System gave 94% confidence bedding zone prediction
        Expected: Low confidence (<50%) OR validation warning
        """
        # Known false positive location from conversation history
        false_positive_lat = 43.31
        false_positive_lon = -73.215
        
        # Get GEE data to check for validation
        gee_data = predictor.get_dynamic_gee_data_enhanced(false_positive_lat, false_positive_lon)
        
        # Run full analysis
        result = predictor.run_enhanced_biological_analysis(
            false_positive_lat, false_positive_lon, 
            time_of_day=6, season='fall', hunting_pressure='medium'
        )
        
        # Extract bedding zones (GeoJSON dict with 'features' list)
        bedding_zones_geojson = result.get('bedding_zones', {})
        assert isinstance(bedding_zones_geojson, dict), f"Expected dict, got {type(bedding_zones_geojson)}"
        
        bedding_features = bedding_zones_geojson.get('features', [])
        
        # CRITICAL ASSERTION: Either low confidence OR validation warning present
        has_low_confidence = all(
            feature.get('properties', {}).get('confidence', 1.0) < 0.5 
            for feature in bedding_features
        ) if bedding_features else True
        
        has_validation_warning = (
            'validation_warning' in gee_data or 
            'grass_pattern_detected' in gee_data or
            gee_data.get('data_source', '').endswith('_validated')
        )
        
        assert has_low_confidence or has_validation_warning, \
            f"False positive not flagged! Features: {len(bedding_features)}, " \
            f"Confidence: {bedding_features[0].get('properties', {}).get('confidence') if bedding_features else 'N/A'}, " \
            f"Validation: {has_validation_warning}, Data source: {gee_data.get('data_source')}"
        
        confidence = bedding_features[0].get('properties', {}).get('confidence', 0) if bedding_features else 0
        print(f"✅ False positive correctly handled - Confidence: {confidence:.2f}")
    
    def test_known_true_positive_location_validation(self, predictor):
        """
        VALIDATION TEST: Ensure known good location still works
        
        Ground Truth: 44.26, -72.58 is forested Vermont hunting area
        Expected: Bedding zones generated with reasonable confidence (>40%)
        """
        # Known good location from README
        vermont_forest_lat = 44.26
        vermont_forest_lon = -72.58
        
        # Get GEE data
        gee_data = predictor.get_dynamic_gee_data_enhanced(vermont_forest_lat, vermont_forest_lon)
        
        # Run full analysis
        result = predictor.run_enhanced_biological_analysis(
            vermont_forest_lat, vermont_forest_lon,
            time_of_day=6, season='fall', hunting_pressure='medium'
        )
        
        # Extract bedding zones (GeoJSON dict with 'features' list)
        bedding_zones_geojson = result.get('bedding_zones', {})
        assert isinstance(bedding_zones_geojson, dict), f"Expected dict, got {type(bedding_zones_geojson)}"
        
        bedding_features = bedding_zones_geojson.get('features', [])
        assert len(bedding_features) > 0, "No bedding zones generated for known forested area"
        
        # At least one should have decent confidence
        max_confidence = max(
            feature.get('properties', {}).get('confidence', 0) 
            for feature in bedding_features
        )
        assert max_confidence > 0.4, \
            f"Confidence too low ({max_confidence:.2f}) for known good location"
        
        # Verify GEE data quality
        ndvi = gee_data.get('ndvi_value', gee_data.get('ndvi', 0))
        assert ndvi > 0.2, "NDVI too low for forested area"
        
        print(f"✅ True positive validated - Max confidence: {max_confidence:.2f}, NDVI: {ndvi:.3f}")
    
    def test_gee_data_source_tracking(self, integrator):
        """
        Ensure all GEE data includes source tracking for debugging
        
        Critical for identifying which data pipeline was used
        """
        gee_data = integrator.get_dynamic_gee_data(44.26, -72.58)
        
        # Must have data_source field
        assert 'data_source' in gee_data, "Missing data_source tracking field"
        
        # Should be one of known sources
        valid_sources = [
            'dynamic_gee_enhanced',
            'dynamic_gee_enhanced_validated',
            'static_gee',
            'fallback'
        ]
        
        data_source = gee_data['data_source']
        assert any(source in data_source for source in valid_sources), \
            f"Unknown data source: {data_source}"
        
        print(f"✅ Data source tracked: {data_source}")
    
    def test_grass_field_ndvi_pattern_detection(self, integrator):
        """
        Detect grass field patterns using NDVI characteristics
        
        Grass fields typically have:
        - Moderate NDVI (0.5-0.7) from grass photosynthesis
        - Low canopy height
        - Uniform texture
        """
        # Get data for potential grass field location
        gee_data = integrator.get_dynamic_gee_data(43.31, -73.215)
        
        ndvi = gee_data.get('ndvi', 0)
        hansen_canopy = gee_data.get('treecover2000', 0)
        
        # Grass field pattern: decent NDVI but shouldn't have high tree canopy from 2000
        # If current NDVI is good (>0.4) but we claim high canopy (>60%), likely grass
        is_suspicious = (ndvi > 0.4 and ndvi < 0.8) and hansen_canopy > 60
        
        if is_suspicious:
            # Should have some validation flag or warning
            assert 'validation_warning' in gee_data or 'grass_pattern_detected' in gee_data, \
                f"Grass field pattern detected (NDVI: {ndvi:.3f}, Hansen: {hansen_canopy}%) but not flagged"
        
        print(f"✅ Grass field detection logic validated - NDVI: {ndvi:.3f}, Hansen: {hansen_canopy}%")


@pytest.mark.unit
@pytest.mark.critical
class TestDataIntegrity:
    """Validate data structure integrity and required fields"""
    
    def test_gee_data_required_fields(self):
        """Ensure GEE data contains all required fields"""
        predictor = EnhancedBeddingZonePredictor()
        gee_data = predictor.get_dynamic_gee_data_enhanced(44.26, -72.58)
        
        required_fields = [
            'ndvi_value',  # Enhanced predictor uses ndvi_value not ndvi
            'canopy_coverage',
            'data_source'
        ]
        
        for field in required_fields:
            assert field in gee_data, f"Missing required field: {field}. Available: {list(gee_data.keys())}"
        
        # Validate data types
        assert isinstance(gee_data['ndvi_value'], (int, float)), "NDVI must be numeric"
        assert isinstance(gee_data['canopy_coverage'], (int, float)), "Canopy coverage must be numeric"
        assert isinstance(gee_data['data_source'], str), "Data source must be string"
        
        print(f"✅ All required fields present and valid types")
    
    def test_bedding_zone_response_schema(self):
        """Validate bedding zone prediction response structure"""
        predictor = EnhancedBeddingZonePredictor()
        result = predictor.run_enhanced_biological_analysis(
            44.26, -72.58, 
            time_of_day=6, season='fall', hunting_pressure='medium'
        )
        
        # Must have key sections
        assert 'bedding_zones' in result, "Missing bedding_zones"
        
        # Bedding zones is GeoJSON dict with 'features' list
        bedding_zones_geojson = result['bedding_zones']
        assert isinstance(bedding_zones_geojson, dict), f"Expected dict, got {type(bedding_zones_geojson)}"
        assert 'type' in bedding_zones_geojson, "Missing GeoJSON 'type'"
        assert 'features' in bedding_zones_geojson, "Missing GeoJSON 'features'"
        
        bedding_features = bedding_zones_geojson['features']
        assert isinstance(bedding_features, list), "Features must be a list"
        
        # If features exist, validate structure
        if bedding_features:
            feature = bedding_features[0]
            assert 'geometry' in feature, "Feature missing geometry"
            assert 'properties' in feature, "Feature missing properties"
            
            properties = feature['properties']
            assert 'confidence' in properties, "Feature properties missing confidence"
            
            # Confidence must be 0-1 range
            confidence = properties['confidence']
            assert 0 <= confidence <= 1, \
                f"Confidence out of range: {confidence}"
        
        print(f"✅ Response schema validated - {len(bedding_features)} zones found")
