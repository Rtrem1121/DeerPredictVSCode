#!/usr/bin/env python3
"""
Prediction Service Module

Centralized service for deer movement prediction logic using EnhancedBeddingZonePredictor.
This module implements comprehensive biological analysis with GEE, Open-Meteo, Open-Elevation, and OSM integration.

Key Responsibilities:
- Use EnhancedBeddingZonePredictor exclusively as primary prediction engine
- Generate bedding zones with comprehensive data integration
- Provide detailed logging of prediction metrics
- Handle error scenarios gracefully
- Integrate wind direction and thermal analysis for all location types

Author: GitHub Copilot  
Version: 3.1.0 - Wind and Thermal Analysis Integration
Date: September 1, 2025
"""

from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor
from dataclasses import asdict
from backend.scouting_prediction_enhancer import get_scouting_enhancer
from backend.advanced_thermal_analysis import AdvancedThermalAnalyzer
from backend.analysis.wind_thermal_analyzer import get_wind_thermal_analyzer
from backend.analysis.prediction_analyzer import PredictionAnalyzer
import logging
import numpy as np
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Streamlined prediction service using EnhancedBeddingZonePredictor exclusively.
    
    This service uses comprehensive biological analysis with real-time data integration:
    - GEE (Google Earth Engine) for canopy and vegetation data
    - Open-Meteo for weather and thermal analysis  
    - Open-Elevation for terrain elevation data
    - OSM (OpenStreetMap) for security and road proximity analysis
    - Advanced thermal wind analysis for all location types
    - Comprehensive wind direction analysis for scent management
    """
    
    def __init__(self):
        """Initialize the prediction service with comprehensive analysis components."""
        try:
            self.predictor = EnhancedBeddingZonePredictor()
            self.scouting_enhancer = get_scouting_enhancer()
            self.thermal_analyzer = AdvancedThermalAnalyzer()
            self.wind_analyzer = get_wind_thermal_analyzer()
            logger.info("✅ EnhancedBeddingZonePredictor initialized as exclusive prediction engine")
            logger.info("✅ ScoutingPredictionEnhancer initialized for field data integration")
            logger.info("✅ AdvancedThermalAnalyzer initialized for thermal wind analysis")
            logger.info("✅ WindThermalAnalyzer initialized for comprehensive wind analysis")
        except Exception as e:
            logger.error(f"❌ Failed to initialize prediction components: {e}")
            raise

    async def predict(self, lat: float, lon: float, time_of_day: int, season: str, hunting_pressure: str) -> Dict:
        """
        Generate comprehensive deer movement prediction using EnhancedBeddingZonePredictor exclusively.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            time_of_day: Hour of day (0-23)
            season: Season ('spring', 'summer', 'fall', 'winter')
            hunting_pressure: Pressure level ('low', 'medium', 'high')
            
        Returns:
            Dict: Enhanced prediction results with comprehensive data integration, wind analysis, and thermal analysis
        """
        return await self.predict_with_analysis(lat, lon, time_of_day, season, hunting_pressure, analyzer=None)
    
    async def predict_with_analysis(self, lat: float, lon: float, time_of_day: int, season: str, 
                                   hunting_pressure: str, analyzer: Optional[PredictionAnalyzer] = None) -> Dict:
        """
        Generate comprehensive prediction with optional detailed analysis collection.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate  
            time_of_day: Hour of day (0-23)
            season: Season ('spring', 'summer', 'fall', 'winter')
            hunting_pressure: Pressure level ('low', 'medium', 'high')
            analyzer: Optional PredictionAnalyzer for detailed analysis collection
            
        Returns:
            Dict: Enhanced prediction results with comprehensive data integration
        """
        try:
            # Use EnhancedBeddingZonePredictor exclusively
            result = self.predictor.run_enhanced_biological_analysis(
                lat, lon, time_of_day, season, hunting_pressure
            )
            
            # Extract environmental data for analysis
            gee_data = result.get('gee_data', {})
            osm_data = result.get('osm_data', {})
            weather_data = result.get('weather_data', {})
            
            # Collect criteria analysis if analyzer provided
            if analyzer:
                try:
                    self._collect_criteria_analysis(analyzer, result, gee_data, osm_data, weather_data)
                except Exception as e:
                    logger.warning(f"⚠️ Criteria analysis collection failed: {e}")
            
            # Perform advanced thermal analysis
            thermal_analysis = None
            try:
                terrain_features = {
                    'elevation': gee_data.get('elevation', 1000),
                    'slope': gee_data.get('slope', 10),
                    'aspect': gee_data.get('aspect', 180),
                    'canopy_coverage': gee_data.get('canopy_coverage', 0.6)
                }
                
                thermal_analysis = self.thermal_analyzer.analyze_thermal_conditions(
                    weather_data, terrain_features, lat, lon, time_of_day
                )
                
                logger.info(f"🌡️ THERMAL ANALYSIS: {thermal_analysis.direction} thermal, "
                           f"strength {thermal_analysis.strength_scale:.1f}/10, "
                           f"timing advantage: {thermal_analysis.timing_advantage}")
                
                # Collect thermal analysis if analyzer provided
                if analyzer:
                    try:
                        analyzer.collect_thermal_analysis(
                            thermal_analysis.__dict__,
                            {'optimal_timing': thermal_analysis.timing_advantage},
                            thermal_analysis.optimal_stand_positions
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ Thermal analysis collection failed: {e}")
                
            except Exception as e:
                logger.warning(f"⚠️ Thermal analysis failed: {e}")
            
            # Perform comprehensive wind analysis for all location types
            wind_analyses = []
            try:
                # Analyze bedding locations
                bedding_zones = result.get("bedding_zones", {})
                if bedding_zones and 'features' in bedding_zones:
                    for zone in bedding_zones['features'][:3]:  # Analyze first 3 zones
                        zone_coords = zone.get('geometry', {}).get('coordinates', [lon, lat])
                        zone_lat, zone_lon = zone_coords[1], zone_coords[0]
                        
                        wind_analysis = self.wind_analyzer.analyze_location_winds(
                            'bedding', zone_lat, zone_lon, weather_data, terrain_features,
                            thermal_analysis.__dict__ if thermal_analysis else None, time_of_day
                        )
                        wind_analyses.append(wind_analysis)
                
                # Analyze stand locations
                stand_recommendations = result.get('mature_buck_analysis', {}).get('stand_recommendations', [])
                for i, stand in enumerate(stand_recommendations[:3]):  # Analyze first 3 stands
                    stand_coords = stand.get('coordinates', {})
                    stand_lat = stand_coords.get('lat', lat)
                    stand_lon = stand_coords.get('lon', lon)
                    
                    wind_analysis = self.wind_analyzer.analyze_location_winds(
                        'stand', stand_lat, stand_lon, weather_data, terrain_features,
                        thermal_analysis.__dict__ if thermal_analysis else None, time_of_day
                    )
                    wind_analyses.append(wind_analysis)
                
                # Analyze feeding locations
                feeding_areas = result.get("feeding_areas", {})
                if feeding_areas and 'features' in feeding_areas:
                    for area in feeding_areas['features'][:3]:  # Analyze first 3 areas
                        area_coords = area.get('geometry', {}).get('coordinates', [lon, lat])
                        area_lat, area_lon = area_coords[1], area_coords[0]
                        
                        wind_analysis = self.wind_analyzer.analyze_location_winds(
                            'feeding', area_lat, area_lon, weather_data, terrain_features,
                            thermal_analysis.__dict__ if thermal_analysis else None, time_of_day
                        )
                        wind_analyses.append(wind_analysis)
                
                # Create comprehensive wind summary
                wind_summary = self.wind_analyzer.create_wind_analysis_summary(wind_analyses)
                
                logger.info(f"🌬️ WIND ANALYSIS: {len(wind_analyses)} locations analyzed, "
                           f"overall rating {wind_summary['overall_wind_conditions'].get('hunting_rating', 'N/A')}")
                
                # Collect wind analysis if analyzer provided
                if analyzer:
                    try:
                        # Properly serialize wind analysis data
                        serialized_analyses = [asdict(analysis) for analysis in wind_analyses]
                        analyzer.collect_wind_analysis(
                            wind_summary.get('overall_wind_conditions', {}),
                            serialized_analyses,
                            wind_summary
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ Wind analysis collection failed: {e}")
                
            except Exception as e:
                logger.warning(f"⚠️ Wind analysis failed: {e}")
                wind_analyses = []
                wind_summary = {}
            
            # Apply scouting data enhancements to boost predictions around real field observations
            scouting_enhancement_result = {}
            try:
                # Create basic score maps from prediction results for enhancement
                score_maps = {
                    "travel": self._extract_travel_scores(result),
                    "bedding": self._extract_bedding_scores(result), 
                    "feeding": self._extract_feeding_scores(result)
                }
                
                # Apply scouting enhancements
                scouting_enhancement_result = self.scouting_enhancer.enhance_predictions(
                    lat, lon, score_maps, span_deg=0.04, grid_size=10
                )
                
                # Log scouting enhancement details
                enhancements = scouting_enhancement_result.get('enhancements_applied', [])
                total_boost = scouting_enhancement_result.get('total_boost_points', 0)
                mature_buck_indicators = scouting_enhancement_result.get('mature_buck_indicators', 0)
                
                if enhancements:
                    logger.info(f"🏹 SCOUTING ENHANCEMENT: {len(enhancements)} observations applied")
                    logger.info(f"   Total boost: {total_boost:.1f} points")
                    logger.info(f"   Mature buck indicators: {mature_buck_indicators}")
                    
                    for enhancement in enhancements[:3]:  # Log first 3
                        obs_type = enhancement.get('observation_type', 'unknown')
                        boost = enhancement.get('boost_applied', 0)
                        age_days = enhancement.get('age_days', 0)
                        logger.info(f"   {obs_type}: +{boost:.1f}% boost ({age_days}d old)")
                else:
                    logger.info("🏹 SCOUTING ENHANCEMENT: No nearby observations found")
                    
            except Exception as e:
                logger.warning(f"⚠️ Scouting enhancement failed, using base predictions: {e}")
            
            # Collect data source and algorithm analysis if analyzer provided
            if analyzer:
                try:
                    self._collect_data_source_analysis(analyzer, gee_data, osm_data, weather_data, scouting_enhancement_result)
                    self._collect_algorithm_analysis(analyzer, result)
                    self._collect_scoring_analysis(analyzer, result)
                except Exception as e:
                    logger.warning(f"⚠️ Additional analysis collection failed: {e}")
            
            # Extract bedding zones for logging
            bedding_zones = result["bedding_zones"]
            num_zones = len(bedding_zones['features']) if bedding_zones and 'features' in bedding_zones else 0
            
            # Extract suitability metrics for comprehensive logging
            suitability_analysis = bedding_zones.get('properties', {}).get('suitability_analysis', {}) if bedding_zones else {}
            overall_suitability = suitability_analysis.get('overall_score', 0)
            confidence = result.get('confidence_score', 0)
            
            # Log comprehensive prediction metrics
            logger.info(f"Prediction: {num_zones} zones, "
                       f"suitability={overall_suitability:.1f}%, "
                       f"confidence={confidence:.2f}")
            
            # Log data integration sources
            if gee_data:
                canopy = gee_data.get('canopy_coverage', 0)
                logger.info(f"🛰️ GEE Integration: Canopy={canopy:.1f}%")
            
            if osm_data:
                road_distance = osm_data.get('min_road_distance', 0)
                logger.info(f"🗺️ OSM Integration: Road distance={road_distance:.0f}m")
            
            if weather_data:
                temp = weather_data.get('temperature', 0)
                logger.info(f"🌤️ Weather Integration: Temperature={temp:.1f}°F")
            
            # Log individual zone details for validation
            if bedding_zones and 'features' in bedding_zones:
                for i, zone in enumerate(bedding_zones['features'][:3], 1):
                    zone_props = zone.get('properties', {})
                    zone_coords = zone.get('geometry', {}).get('coordinates', [0, 0])
                    zone_suitability = zone_props.get('suitability_score', 0)
                    zone_type = zone_props.get('bedding_type', 'unknown')
                    logger.info(f"🛌 Zone {i}: {zone_suitability:.1f}% {zone_type} at {zone_coords[1]:.4f}, {zone_coords[0]:.4f}")
            
            # Add wind and thermal analysis to result
            result['thermal_analysis'] = thermal_analysis.__dict__ if thermal_analysis else None
            result['wind_analyses'] = [analysis.__dict__ for analysis in wind_analyses]
            result['wind_summary'] = wind_summary
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced prediction failed: {e}")
            raise

    def _extract_travel_scores(self, result: Dict) -> np.ndarray:
        """Extract travel corridor scores from prediction results."""
        try:
            # Create a basic score grid based on stand positions
            grid_size = 10
            scores = np.ones((grid_size, grid_size)) * 3.0  # Base travel score
            
            # Boost areas around stand recommendations
            stands = result.get('stand_recommendations', [])
            if stands:
                for stand in stands[:3]:
                    # Add boost around stand positions (simplified)
                    scores += 0.5
                    
            return scores
        except:
            return np.ones((10, 10)) * 3.0

    def _extract_bedding_scores(self, result: Dict) -> np.ndarray:
        """Extract bedding scores from prediction results."""
        try:
            grid_size = 10
            
            # Get suitability score from bedding zones
            bedding_zones = result.get("bedding_zones", {})
            suitability_analysis = bedding_zones.get('properties', {}).get('suitability_analysis', {})
            base_score = suitability_analysis.get('overall_score', 50) / 10.0  # Convert to 0-10 scale
            
            scores = np.ones((grid_size, grid_size)) * base_score
            return scores
        except:
            return np.ones((10, 10)) * 5.0

    def _extract_feeding_scores(self, result: Dict) -> np.ndarray:
        """Extract feeding scores from prediction results."""
        try:
            grid_size = 10
            scores = np.ones((grid_size, grid_size)) * 4.0  # Base feeding score
            
            # Boost areas around feeding recommendations
            feeding_areas = result.get('feeding_areas', [])
            if feeding_areas:
                for area in feeding_areas[:3]:
                    scores += 0.3
                    
            return scores
        except:
            return np.ones((10, 10)) * 4.0
    
    def _collect_criteria_analysis(self, analyzer: PredictionAnalyzer, result: Dict, 
                                 gee_data: Dict, osm_data: Dict, weather_data: Dict) -> None:
        """Collect criteria analysis from prediction results"""
        try:
            # Extract bedding criteria
            bedding_zones = result.get("bedding_zones", {})
            bedding_props = bedding_zones.get('properties', {}) if bedding_zones else {}
            suitability_analysis = bedding_props.get('suitability_analysis', {})
            
            bedding_criteria = {
                'canopy_coverage': gee_data.get('canopy_coverage', 0),
                'road_distance': osm_data.get('nearest_road_distance_m', 0),
                'slope': gee_data.get('slope', 0),
                'aspect': gee_data.get('aspect', 0),
                'suitability_score': suitability_analysis.get('overall_score', 0)
            }
            
            # Extract stand criteria
            stand_recommendations = result.get('mature_buck_analysis', {}).get('stand_recommendations', [])
            stand_criteria = {
                'stand_count': len(stand_recommendations),
                'wind_analysis_available': bool(result.get('wind_analyses')),
                'thermal_analysis_available': bool(result.get('thermal_analysis'))
            }
            
            # Extract feeding criteria
            feeding_areas = result.get("feeding_areas", {})
            feeding_criteria = {
                'feeding_areas_count': len(feeding_areas.get('features', [])) if feeding_areas else 0,
                'food_source_diversity': True  # Simplified
            }
            
            # Define thresholds used
            thresholds = {
                'min_canopy': 0.6,
                'min_road_distance': 200,
                'min_slope': 3,
                'max_slope': 30,
                'optimal_aspect_min': 135,
                'optimal_aspect_max': 225
            }
            
            analyzer.collect_criteria_analysis(bedding_criteria, stand_criteria, feeding_criteria, thresholds)
            
        except Exception as e:
            logger.warning(f"⚠️ Criteria analysis collection failed: {e}")
    
    def _collect_data_source_analysis(self, analyzer: PredictionAnalyzer, gee_data: Dict, 
                                    osm_data: Dict, weather_data: Dict, scouting_data: Dict) -> None:
        """Collect data source analysis"""
        try:
            analyzer.collect_data_source_analysis(gee_data, osm_data, weather_data, scouting_data)
        except Exception as e:
            logger.warning(f"⚠️ Data source analysis collection failed: {e}")
    
    def _collect_algorithm_analysis(self, analyzer: PredictionAnalyzer, result: Dict) -> None:
        """Collect algorithm analysis"""
        try:
            decision_points = [
                {
                    'algorithm': 'EnhancedBeddingZonePredictor',
                    'decision': 'bedding_zone_generation',
                    'factors': ['canopy_coverage', 'road_distance', 'slope', 'aspect'],
                    'result': f"{len(result.get('bedding_zones', {}).get('features', []))} zones generated"
                },
                {
                    'algorithm': 'WindThermalAnalyzer', 
                    'decision': 'wind_direction_analysis',
                    'factors': ['prevailing_wind', 'thermal_wind', 'terrain_interaction'],
                    'result': f"{len(result.get('wind_analyses', []))} locations analyzed"
                }
            ]
            
            confidence_calc = {
                'base_confidence': result.get('confidence_score', 0),
                'wind_factor': 0.1 if result.get('wind_analyses') else 0,
                'thermal_factor': 0.1 if result.get('thermal_analysis') else 0
            }
            
            enhancements = []
            if result.get('wind_analyses'):
                enhancements.append('WindThermalAnalyzer')
            if result.get('thermal_analysis'):
                enhancements.append('AdvancedThermalAnalyzer')
            
            analyzer.collect_algorithm_analysis(
                'EnhancedBeddingZonePredictor',
                'v3.1.0-wind-thermal-integration',
                decision_points,
                confidence_calc,
                enhancements
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Algorithm analysis collection failed: {e}")
    
    def _collect_scoring_analysis(self, analyzer: PredictionAnalyzer, result: Dict) -> None:
        """Collect scoring analysis"""
        try:
            # Extract bedding scoring
            bedding_zones = result.get("bedding_zones", {})
            bedding_scoring = {
                'zones': bedding_zones.get('features', []) if bedding_zones else [],
                'suitability_analysis': bedding_zones.get('properties', {}).get('suitability_analysis', {}) if bedding_zones else {}
            }
            
            # Extract stand scoring
            stand_recommendations = result.get('mature_buck_analysis', {}).get('stand_recommendations', [])
            stand_scoring = {
                'stands': stand_recommendations
            }
            
            # Extract feeding scoring
            feeding_areas = result.get("feeding_areas", {})
            feeding_scoring = {
                'areas': feeding_areas.get('features', []) if feeding_areas else []
            }
            
            overall_confidence = result.get('confidence_score', 0)
            
            analyzer.collect_scoring_analysis(bedding_scoring, stand_scoring, feeding_scoring, overall_confidence)
            
        except Exception as e:
            logger.warning(f"⚠️ Scoring analysis collection failed: {e}")


# Global service instance
_prediction_service = None


def get_prediction_service() -> PredictionService:
    """Get the singleton prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
