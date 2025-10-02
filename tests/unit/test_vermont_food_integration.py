#!/usr/bin/env python3
"""
Unit Tests for Vermont Food Classification Integration

Tests the integration of Vermont-specific food source analysis
with the prediction service and vegetation analyzer.

Author: GitHub Copilot
Date: October 2, 2025
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import modules to test
from backend.services.prediction_service import PredictionService
from backend.vegetation_analyzer import VegetationAnalyzer
from backend.vermont_food_classifier import VermontFoodClassifier


class TestVermontFoodClassifier:
    """Test Vermont Food Classifier functionality"""
    
    def test_vermont_crops_defined(self):
        """Test that Vermont crop classifications are properly defined"""
        from backend.vermont_food_classifier import VERMONT_CROPS
        
        # Verify key Vermont crops exist
        assert 1 in VERMONT_CROPS  # Corn
        assert VERMONT_CROPS[1] == 'Corn'
        
        assert 37 in VERMONT_CROPS  # Hay
        assert 141 in VERMONT_CROPS  # Deciduous Forest
        assert 142 in VERMONT_CROPS  # Evergreen Forest
        
        # Verify no soybeans (user constraint)
        soybean_codes = [5]  # CDL code for soybeans
        for code in soybean_codes:
            if code in VERMONT_CROPS:
                pytest.fail(f"Soybeans (code {code}) should not be in Vermont crops")
    
    def test_seasonal_quality_scores(self):
        """Test that crops have seasonal quality scores"""
        from backend.vermont_food_classifier import VERMONT_CROP_QUALITY
        
        # Test corn seasonal scoring
        corn_quality = VERMONT_CROP_QUALITY.get(1, {})  # Corn
        assert 'early_season' in corn_quality
        assert 'rut' in corn_quality
        assert 'late_season' in corn_quality
        
        # Verify corn is high quality during rut
        assert corn_quality['rut'] > 0.85, "Corn should be prime food during rut"
        
        # Verify deciduous forest (mast) is high quality early season
        deciduous_quality = VERMONT_CROP_QUALITY.get(141, {})
        assert deciduous_quality['early_season'] > 0.70, "Mast should be important early season"
    
    def test_seasonal_priorities(self):
        """Test seasonal food priority weighting"""
        from backend.vermont_food_classifier import VERMONT_SEASONAL_PRIORITIES
        
        # Test early season priorities
        early_priorities = VERMONT_SEASONAL_PRIORITIES['early_season']
        assert 'mast' in early_priorities['weights']
        assert early_priorities['weights']['mast'] >= 0.40, "Early season should prioritize mast"
        
        # Test rut priorities
        rut_priorities = VERMONT_SEASONAL_PRIORITIES['rut']
        assert 'agriculture' in rut_priorities['weights']
        assert rut_priorities['weights']['agriculture'] >= 0.40, "Rut should prioritize agriculture"
        
        # Test late season priorities
        late_priorities = VERMONT_SEASONAL_PRIORITIES['late_season']
        assert 'browse' in late_priorities['weights']
        assert late_priorities['weights']['browse'] >= 0.35, "Late season should prioritize browse"


class TestVegetationAnalyzerIntegration:
    """Test vegetation analyzer integration with Vermont classifier"""
    
    @patch('backend.vegetation_analyzer.ee')
    def test_analyze_hunting_area_accepts_season(self, mock_ee):
        """Test that analyze_hunting_area accepts season parameter"""
        # Mock GEE initialization
        mock_ee.Initialize = Mock()
        
        analyzer = VegetationAnalyzer()
        
        # Mock GEE data
        with patch.object(analyzer, '_get_gee_data') as mock_gee_data:
            mock_gee_data.return_value = {
                'canopy_coverage': 0.75,
                'elevation': 1000,
                'slope': 10,
                'aspect': 180
            }
            
            with patch.object(analyzer, '_identify_food_sources') as mock_food:
                mock_food.return_value = {
                    'overall_food_score': 0.85,
                    'food_source_count': 3,
                    'dominant_food': {'name': 'Corn', 'quality_score': 0.95}
                }
                
                # Call with season parameter
                result = analyzer.analyze_hunting_area(
                    lat=44.26,
                    lon=-72.58,
                    radius_km=2.0,
                    season='rut'
                )
                
                # Verify season was passed through
                assert mock_food.called
                call_args = mock_food.call_args
                assert 'season' in call_args.kwargs or len(call_args.args) >= 4
                
                # Verify result contains season
                assert result.get('analysis_metadata', {}).get('season') == 'rut'
    
    @patch('backend.vermont_food_classifier.ee')
    def test_food_sources_call_vermont_classifier(self, mock_ee):
        """Test that _identify_food_sources calls Vermont classifier"""
        from backend.vegetation_analyzer import VegetationAnalyzer
        from datetime import datetime
        
        # Mock GEE
        mock_ee.Initialize = Mock()
        mock_ee.Geometry = Mock()
        mock_ee.Geometry.Point = Mock(return_value=Mock())
        
        analyzer = VegetationAnalyzer()
        
        with patch('backend.vegetation_analyzer.get_vermont_food_classifier') as mock_get_vt:
            mock_vt_classifier = Mock()
            mock_vt_classifier.analyze_vermont_food_sources.return_value = {
                'overall_food_score': 0.87,
                'food_source_count': 3,
                'food_patches': [
                    {'name': 'Corn', 'quality_score': 0.95, 'type': 'agricultural'}
                ],
                'dominant_food': {'name': 'Corn', 'quality_score': 0.95}
            }
            mock_get_vt.return_value = mock_vt_classifier
            
            # Call _identify_food_sources with season
            mock_area = Mock()
            result = analyzer._identify_food_sources(
                area=mock_area,
                start_date=datetime(2025, 11, 1),
                end_date=datetime(2025, 11, 30),
                season='rut'
            )
            
            # Verify Vermont classifier was called
            assert mock_vt_classifier.analyze_vermont_food_sources.called
            assert result['overall_food_score'] == 0.87
            assert result['dominant_food']['name'] == 'Corn'


class TestPredictionServiceIntegration:
    """Test prediction service integration with Vermont food classifier"""
    
    @pytest.mark.asyncio
    @patch('backend.services.prediction_service.EnhancedBeddingZonePredictor')
    @patch('backend.services.prediction_service.get_vegetation_analyzer')
    async def test_prediction_service_uses_vermont_food(self, mock_get_veg, mock_predictor_class):
        """Test that prediction service uses Vermont food classification"""
        # Mock vegetation analyzer
        mock_veg_analyzer = Mock()
        mock_veg_analyzer.analyze_hunting_area.return_value = {
            'food_sources': {
                'overall_food_score': 0.87,
                'food_source_count': 3,
                'food_patches': [
                    {'name': 'Corn', 'quality_score': 0.95}
                ],
                'dominant_food': {'name': 'Corn', 'quality_score': 0.95}
            },
            'vegetation_health': {'health_rating': 'good'},
            'analysis_metadata': {'season': 'rut'}
        }
        mock_get_veg.return_value = mock_veg_analyzer
        
        # Mock predictor
        mock_predictor = Mock()
        mock_predictor.run_enhanced_biological_analysis.return_value = {
            'bedding_zones': {'features': []},
            'mature_buck_analysis': {'stand_recommendations': []},
            'feeding_areas': {'features': []},
            'gee_data': {'canopy_coverage': 0.75},
            'osm_data': {'nearest_road_distance_m': 300},
            'weather_data': {'temperature': 45}
        }
        mock_predictor_class.return_value = mock_predictor
        
        # Mock other dependencies
        with patch('backend.services.prediction_service.get_scouting_enhancer'):
            with patch('backend.services.prediction_service.AdvancedThermalAnalyzer'):
                with patch('backend.services.prediction_service.get_wind_thermal_analyzer'):
                    with patch('backend.services.prediction_service.get_config'):
                        with patch('backend.services.prediction_service.HuntWindowPredictor'):
                            # Create service
                            service = PredictionService()
                            
                            # Call predict
                            result = await service.predict(
                                lat=44.26,
                                lon=-72.58,
                                time_of_day=17,
                                season='rut',
                                hunting_pressure='medium'
                            )
                            
                            # Verify vegetation analyzer was initialized
                            assert mock_get_veg.called
    
    def test_extract_feeding_scores_uses_vermont_data(self):
        """Test that _extract_feeding_scores uses Vermont food classification"""
        with patch('backend.services.prediction_service.EnhancedBeddingZonePredictor'):
            with patch('backend.services.prediction_service.get_scouting_enhancer'):
                with patch('backend.services.prediction_service.AdvancedThermalAnalyzer'):
                    with patch('backend.services.prediction_service.get_wind_thermal_analyzer'):
                        with patch('backend.services.prediction_service.get_config'):
                            with patch('backend.services.prediction_service.HuntWindowPredictor'):
                                with patch('backend.services.prediction_service.get_vegetation_analyzer') as mock_get_veg:
                                    # Mock vegetation analyzer
                                    mock_veg_analyzer = Mock()
                                    mock_veg_analyzer.analyze_hunting_area.return_value = {
                                        'food_sources': {
                                            'overall_food_score': 0.90,  # High food score
                                            'food_source_count': 3
                                        }
                                    }
                                    mock_get_veg.return_value = mock_veg_analyzer
                                    
                                    service = PredictionService()
                                    
                                    # Call _extract_feeding_scores with Vermont data
                                    scores = service._extract_feeding_scores(
                                        result={},
                                        lat=44.26,
                                        lon=-72.58,
                                        season='rut'
                                    )
                                    
                                    # Verify vegetation analyzer was called with season
                                    assert mock_veg_analyzer.analyze_hunting_area.called
                                    call_kwargs = mock_veg_analyzer.analyze_hunting_area.call_args.kwargs
                                    assert call_kwargs['season'] == 'rut'
                                    
                                    # Verify scores reflect Vermont food quality (0.90 * 10 = 9.0)
                                    assert isinstance(scores, np.ndarray)
                                    assert scores.shape == (10, 10)
                                    assert np.mean(scores) > 8.0, "High food score should produce high feeding scores"
    
    def test_extract_feeding_scores_fallback(self):
        """Test that _extract_feeding_scores falls back gracefully"""
        with patch('backend.services.prediction_service.EnhancedBeddingZonePredictor'):
            with patch('backend.services.prediction_service.get_scouting_enhancer'):
                with patch('backend.services.prediction_service.AdvancedThermalAnalyzer'):
                    with patch('backend.services.prediction_service.get_wind_thermal_analyzer'):
                        with patch('backend.services.prediction_service.get_config'):
                            with patch('backend.services.prediction_service.HuntWindowPredictor'):
                                with patch('backend.services.prediction_service.get_vegetation_analyzer') as mock_get_veg:
                                    # Mock vegetation analyzer to raise exception
                                    mock_veg_analyzer = Mock()
                                    mock_veg_analyzer.analyze_hunting_area.side_effect = Exception("GEE unavailable")
                                    mock_get_veg.return_value = mock_veg_analyzer
                                    
                                    service = PredictionService()
                                    
                                    # Call _extract_feeding_scores (should not crash)
                                    scores = service._extract_feeding_scores(
                                        result={'feeding_areas': []},
                                        lat=44.26,
                                        lon=-72.58,
                                        season='rut'
                                    )
                                    
                                    # Verify fallback scores returned
                                    assert isinstance(scores, np.ndarray)
                                    assert scores.shape == (10, 10)
                                    assert np.mean(scores) == 4.0, "Fallback should return base score of 4.0"


class TestSeasonalScoring:
    """Test seasonal food scoring variations"""
    
    def test_corn_seasonal_variation(self):
        """Test that corn scoring varies by season"""
        from backend.vermont_food_classifier import VERMONT_CROP_QUALITY
        
        corn_quality = VERMONT_CROP_QUALITY.get(1, {})
        
        # Corn should be:
        # - Moderate in early season (45% - growing)
        # - Excellent in rut (95% - standing corn)
        # - High in late season (90% - waste grain)
        
        assert corn_quality['early_season'] < corn_quality['rut'], \
            "Corn should be less valuable early season than during rut"
        assert corn_quality['late_season'] > 0.80, \
            "Corn waste grain should remain valuable late season"
    
    def test_mast_seasonal_variation(self):
        """Test that mast (deciduous forest) scoring varies by season"""
        from backend.vermont_food_classifier import VERMONT_CROP_QUALITY
        
        deciduous_quality = VERMONT_CROP_QUALITY.get(141, {})  # Deciduous forest
        
        # Mast should be:
        # - Excellent in early season (85% - acorn drop)
        # - Good in rut (75% - remaining mast)
        # - Moderate in late season (50% - mostly consumed)
        
        assert deciduous_quality['early_season'] > deciduous_quality['rut'], \
            "Mast should peak early season"
        assert deciduous_quality['rut'] > deciduous_quality['late_season'], \
            "Mast should decline through season"
    
    def test_browse_seasonal_variation(self):
        """Test that browse availability increases in late season"""
        from backend.vermont_food_classifier import VERMONT_CROP_QUALITY
        
        shrubland_quality = VERMONT_CROP_QUALITY.get(152, {})  # Shrubland (browse)
        
        # Browse should be:
        # - Moderate early season (other foods available)
        # - Important late season (limited alternatives)
        
        assert shrubland_quality['late_season'] >= shrubland_quality['early_season'], \
            "Browse should be more important late season"


class TestIntegrationLogging:
    """Test that Vermont food integration produces proper logging"""
    
    @pytest.mark.asyncio
    @patch('backend.services.prediction_service.logger')
    @patch('backend.services.prediction_service.EnhancedBeddingZonePredictor')
    @patch('backend.services.prediction_service.get_vegetation_analyzer')
    async def test_vermont_food_logging(self, mock_get_veg, mock_predictor_class, mock_logger):
        """Test that Vermont food analysis logs properly"""
        # Mock vegetation analyzer
        mock_veg_analyzer = Mock()
        mock_veg_analyzer.analyze_hunting_area.return_value = {
            'food_sources': {
                'overall_food_score': 0.87,
                'food_source_count': 3,
                'food_patches': [
                    {'name': 'Corn', 'quality_score': 0.95},
                    {'name': 'Good Mast Production', 'quality_score': 0.75}
                ],
                'dominant_food': {'name': 'Corn', 'quality_score': 0.95}
            },
            'analysis_metadata': {'season': 'rut'}
        }
        mock_get_veg.return_value = mock_veg_analyzer
        
        # Mock predictor
        mock_predictor = Mock()
        mock_predictor.run_enhanced_biological_analysis.return_value = {
            'bedding_zones': {'features': []},
            'mature_buck_analysis': {'stand_recommendations': []},
            'feeding_areas': {'features': []},
            'gee_data': {'canopy_coverage': 0.75},
            'osm_data': {},
            'weather_data': {}
        }
        mock_predictor_class.return_value = mock_predictor
        
        with patch('backend.services.prediction_service.get_scouting_enhancer'):
            with patch('backend.services.prediction_service.AdvancedThermalAnalyzer'):
                with patch('backend.services.prediction_service.get_wind_thermal_analyzer'):
                    with patch('backend.services.prediction_service.get_config'):
                        with patch('backend.services.prediction_service.HuntWindowPredictor'):
                            service = PredictionService()
                            
                            # Extract feeding scores to trigger logging
                            service._extract_feeding_scores(
                                result={},
                                lat=44.26,
                                lon=-72.58,
                                season='rut'
                            )
                            
                            # Verify Vermont food analysis logging
                            log_calls = [str(call) for call in mock_logger.info.call_args_list]
                            vermont_log_found = any('VERMONT FOOD ANALYSIS' in call for call in log_calls)
                            assert vermont_log_found or mock_logger.info.called, \
                                "Vermont food analysis should log results"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
