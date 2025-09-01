#!/usr/bin/env python3
"""
Prediction Analysis Data Collector

Safely collects detailed analysis data during prediction generation without affecting
core prediction functionality. Follows additive design pattern for zero-risk integration.

Author: GitHub Copilot
Version: 1.0.0
Date: September 1, 2025
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class CriteriaAnalysis:
    """Analysis of criteria used for predictions"""
    bedding_criteria: Dict[str, Any]
    stand_criteria: Dict[str, Any] 
    feeding_criteria: Dict[str, Any]
    thresholds_applied: Dict[str, float]
    criteria_met: Dict[str, bool]

@dataclass
class DataSourceAnalysis:
    """Analysis of data sources and their quality"""
    gee_data_quality: Dict[str, Any]
    osm_data_quality: Dict[str, Any]
    weather_data_quality: Dict[str, Any]
    scouting_data_quality: Dict[str, Any]
    fallback_scenarios_used: List[str]

@dataclass
class AlgorithmAnalysis:
    """Analysis of algorithms and decision points"""
    primary_algorithm: str
    algorithm_version: str
    decision_points: List[Dict[str, Any]]
    confidence_calculations: Dict[str, float]
    enhancement_applications: List[str]

@dataclass
class ScoringAnalysis:
    """Detailed scoring breakdown"""
    bedding_scoring: Dict[str, Any]
    stand_scoring: Dict[str, Any]
    feeding_scoring: Dict[str, Any]
    overall_confidence: float
    score_distributions: Dict[str, List[float]]

@dataclass
class WindAnalysisData:
    """Wind analysis results for all locations"""
    overall_wind_conditions: Dict[str, Any]
    location_wind_analyses: List[Dict[str, Any]]
    wind_summary: Dict[str, Any]
    wind_recommendations: List[str]

@dataclass
class ThermalAnalysisData:
    """Thermal analysis results"""
    thermal_conditions: Dict[str, Any]
    thermal_timing: Dict[str, Any]
    thermal_positioning: List[str]
    thermal_recommendations: List[str]

class PredictionAnalyzer:
    """
    Comprehensive prediction analysis data collector
    
    Safely collects detailed analysis data during prediction generation.
    Uses additive design pattern - all functionality is optional and
    does not affect core prediction logic.
    """
    
    def __init__(self):
        """Initialize the analyzer with empty data structures"""
        self.analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.collection_started = datetime.now()
        
        # Core analysis data structures
        self.criteria_analysis: Optional[CriteriaAnalysis] = None
        self.data_source_analysis: Optional[DataSourceAnalysis] = None
        self.algorithm_analysis: Optional[AlgorithmAnalysis] = None
        self.scoring_analysis: Optional[ScoringAnalysis] = None
        self.wind_analysis: Optional[WindAnalysisData] = None
        self.thermal_analysis: Optional[ThermalAnalysisData] = None
        
        # Collection tracking
        self.data_collected = {
            'criteria': False,
            'data_sources': False,
            'algorithms': False,
            'scoring': False,
            'wind': False,
            'thermal': False
        }
        
        logger.info(f"🔍 PredictionAnalyzer initialized: {self.analysis_id}")
    
    def collect_criteria_analysis(self, bedding_criteria: Dict, stand_criteria: Dict,
                                 feeding_criteria: Dict, thresholds: Dict) -> None:
        """
        Collect criteria analysis data
        
        Args:
            bedding_criteria: Bedding zone criteria and values
            stand_criteria: Stand location criteria and values
            feeding_criteria: Feeding area criteria and values
            thresholds: Applied threshold values
        """
        try:
            # Determine which criteria were met
            criteria_met = {
                'bedding_canopy': bedding_criteria.get('canopy_coverage', 0) >= thresholds.get('min_canopy', 0.6),
                'bedding_roads': bedding_criteria.get('road_distance', 0) >= thresholds.get('min_road_distance', 200),
                'bedding_slope': thresholds.get('min_slope', 3) <= bedding_criteria.get('slope', 0) <= thresholds.get('max_slope', 30),
                'thermal_optimal': thresholds.get('optimal_aspect_min', 135) <= bedding_criteria.get('aspect', 0) <= thresholds.get('optimal_aspect_max', 225)
            }
            
            self.criteria_analysis = CriteriaAnalysis(
                bedding_criteria=bedding_criteria,
                stand_criteria=stand_criteria,
                feeding_criteria=feeding_criteria,
                thresholds_applied=thresholds,
                criteria_met=criteria_met
            )
            
            self.data_collected['criteria'] = True
            logger.debug(f"📋 Criteria analysis collected: {sum(criteria_met.values())}/{len(criteria_met)} criteria met")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to collect criteria analysis: {e}")
    
    def collect_data_source_analysis(self, gee_data: Dict, osm_data: Dict, 
                                   weather_data: Dict, scouting_data: Dict) -> None:
        """
        Collect data source quality analysis
        
        Args:
            gee_data: Google Earth Engine data and quality indicators
            osm_data: OpenStreetMap data and quality indicators
            weather_data: Weather data and quality indicators
            scouting_data: Scouting enhancement data and quality indicators
        """
        try:
            # Assess data quality
            gee_quality = {
                'available': bool(gee_data.get('query_success', False)),
                'canopy_valid': 0 <= gee_data.get('canopy_coverage', -1) <= 1,
                'elevation_valid': gee_data.get('elevation', 0) > 0,
                'slope_valid': 0 <= gee_data.get('slope', -1) <= 90,
                'quality_score': self._calculate_gee_quality_score(gee_data)
            }
            
            osm_quality = {
                'available': bool(osm_data.get('roads_found', False)),
                'road_distance_valid': osm_data.get('nearest_road_distance_m', -1) >= 0,
                'infrastructure_complete': bool(osm_data.get('infrastructure_analysis')),
                'quality_score': self._calculate_osm_quality_score(osm_data)
            }
            
            weather_quality = {
                'available': bool(weather_data.get('temperature')),
                'wind_data_complete': all(k in weather_data for k in ['wind_direction', 'wind_speed']),
                'temperature_valid': -50 <= weather_data.get('temperature', -999) <= 120,
                'api_source': weather_data.get('api_source', 'unknown'),
                'quality_score': self._calculate_weather_quality_score(weather_data)
            }
            
            scouting_quality = {
                'observations_found': len(scouting_data.get('enhancements_applied', [])),
                'enhancement_active': scouting_data.get('total_boost_points', 0) > 0,
                'mature_buck_indicators': scouting_data.get('mature_buck_indicators', 0),
                'quality_score': self._calculate_scouting_quality_score(scouting_data)
            }
            
            # Identify fallback scenarios
            fallback_scenarios = []
            if not gee_quality['available']:
                fallback_scenarios.append("GEE → Open-Elevation fallback")
            if weather_quality['api_source'] == 'cached':
                fallback_scenarios.append("Weather → Cached data fallback")
            
            self.data_source_analysis = DataSourceAnalysis(
                gee_data_quality=gee_quality,
                osm_data_quality=osm_quality,
                weather_data_quality=weather_quality,
                scouting_data_quality=scouting_quality,
                fallback_scenarios_used=fallback_scenarios
            )
            
            self.data_collected['data_sources'] = True
            logger.debug(f"📊 Data source analysis collected: {len(fallback_scenarios)} fallbacks used")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to collect data source analysis: {e}")
    
    def collect_algorithm_analysis(self, primary_algorithm: str, algorithm_version: str,
                                 decision_points: List[Dict], confidence_calc: Dict,
                                 enhancements: List[str]) -> None:
        """
        Collect algorithm decision analysis
        
        Args:
            primary_algorithm: Name of primary prediction algorithm
            algorithm_version: Version of the algorithm used
            decision_points: List of key algorithm decision points
            confidence_calc: Confidence calculation breakdown
            enhancements: List of enhancement algorithms applied
        """
        try:
            self.algorithm_analysis = AlgorithmAnalysis(
                primary_algorithm=primary_algorithm,
                algorithm_version=algorithm_version,
                decision_points=decision_points,
                confidence_calculations=confidence_calc,
                enhancement_applications=enhancements
            )
            
            self.data_collected['algorithms'] = True
            logger.debug(f"⚙️ Algorithm analysis collected: {len(decision_points)} decision points")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to collect algorithm analysis: {e}")
    
    def collect_scoring_analysis(self, bedding_scores: Dict, stand_scores: Dict,
                               feeding_scores: Dict, overall_confidence: float) -> None:
        """
        Collect detailed scoring breakdown
        
        Args:
            bedding_scores: Bedding zone scoring details
            stand_scores: Stand location scoring details  
            feeding_scores: Feeding area scoring details
            overall_confidence: Overall prediction confidence
        """
        try:
            # Calculate score distributions
            score_distributions = {
                'bedding': [zone.get('suitability_score', 0) for zone in bedding_scores.get('zones', [])],
                'stands': [stand.get('confidence', 0) for stand in stand_scores.get('stands', [])],
                'feeding': [area.get('score', 0) for area in feeding_scores.get('areas', [])]
            }
            
            self.scoring_analysis = ScoringAnalysis(
                bedding_scoring=bedding_scores,
                stand_scoring=stand_scores,
                feeding_scoring=feeding_scores,
                overall_confidence=overall_confidence,
                score_distributions=score_distributions
            )
            
            self.data_collected['scoring'] = True
            logger.debug(f"🎯 Scoring analysis collected: {overall_confidence:.2f} overall confidence")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to collect scoring analysis: {e}")
    
    def collect_wind_analysis(self, wind_conditions: Dict, location_analyses: List[Dict],
                            wind_summary: Dict) -> None:
        """
        Collect comprehensive wind analysis data
        
        Args:
            wind_conditions: Overall wind conditions
            location_analyses: Wind analysis for each location
            wind_summary: Summary of wind analysis results
        """
        try:
            # Extract wind recommendations
            wind_recommendations = []
            for analysis in location_analyses:
                wind_recommendations.extend(analysis.get('wind_analysis', {}).get('recommendations', []))
            
            self.wind_analysis = WindAnalysisData(
                overall_wind_conditions=wind_conditions,
                location_wind_analyses=location_analyses,
                wind_summary=wind_summary,
                wind_recommendations=list(set(wind_recommendations))  # Remove duplicates
            )
            
            self.data_collected['wind'] = True
            logger.debug(f"🌬️ Wind analysis collected: {len(location_analyses)} locations analyzed")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to collect wind analysis: {e}")
    
    def collect_thermal_analysis(self, thermal_conditions: Dict, thermal_timing: Dict,
                               thermal_positions: List[str]) -> None:
        """
        Collect thermal analysis data
        
        Args:
            thermal_conditions: Thermal wind conditions and strength
            thermal_timing: Optimal timing based on thermal patterns
            thermal_positions: Recommended positions for thermal advantage
        """
        try:
            # Generate thermal recommendations
            thermal_recommendations = []
            if thermal_conditions.get('is_active', False):
                strength = thermal_conditions.get('strength_scale', 0)
                if strength > 6:
                    thermal_recommendations.append("Strong thermal patterns - use for strategic advantage")
                elif strength > 3:
                    thermal_recommendations.append("Moderate thermal activity - beneficial for scent management")
                
                if thermal_conditions.get('timing_advantage') == 'prime_morning_thermal':
                    thermal_recommendations.append("Prime morning thermal window - optimal hunting time")
            
            self.thermal_analysis = ThermalAnalysisData(
                thermal_conditions=thermal_conditions,
                thermal_timing=thermal_timing,
                thermal_positioning=thermal_positions,
                thermal_recommendations=thermal_recommendations
            )
            
            self.data_collected['thermal'] = True
            logger.debug(f"🌡️ Thermal analysis collected: {len(thermal_recommendations)} recommendations")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to collect thermal analysis: {e}")
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        Get complete analysis data in structured format
        
        Returns:
            Dict containing all collected analysis data
        """
        analysis_complete_time = datetime.now()
        collection_duration = (analysis_complete_time - self.collection_started).total_seconds()
        
        # Calculate completion percentage
        completion_percentage = sum(self.data_collected.values()) / len(self.data_collected) * 100
        
        comprehensive_analysis = {
            'analysis_metadata': {
                'analysis_id': self.analysis_id,
                'collection_started': self.collection_started.isoformat(),
                'analysis_completed': analysis_complete_time.isoformat(),
                'collection_duration_seconds': collection_duration,
                'completion_percentage': completion_percentage,
                'analyzer_version': '2.0.0',
                'data_collected': self.data_collected
            },
            'criteria_analysis': asdict(self.criteria_analysis) if self.criteria_analysis else None,
            'data_source_analysis': asdict(self.data_source_analysis) if self.data_source_analysis else None,
            'algorithm_analysis': asdict(self.algorithm_analysis) if self.algorithm_analysis else None,
            'scoring_analysis': asdict(self.scoring_analysis) if self.scoring_analysis else None,
            'wind_analysis': asdict(self.wind_analysis) if self.wind_analysis else None,
            'thermal_analysis': asdict(self.thermal_analysis) if self.thermal_analysis else None
        }
        
        logger.info(f"🔍 Analysis complete: {completion_percentage:.1f}% data collected in {collection_duration:.2f}s")
        
        return comprehensive_analysis
    
    def _calculate_gee_quality_score(self, gee_data: Dict) -> float:
        """Calculate GEE data quality score (0-1)"""
        score = 0.0
        if gee_data.get('query_success'):
            score += 0.3
        if 0 <= gee_data.get('canopy_coverage', -1) <= 1:
            score += 0.3
        if gee_data.get('elevation', 0) > 0:
            score += 0.2
        if 0 <= gee_data.get('slope', -1) <= 90:
            score += 0.2
        return score
    
    def _calculate_osm_quality_score(self, osm_data: Dict) -> float:
        """Calculate OSM data quality score (0-1)"""
        score = 0.0
        if osm_data.get('roads_found'):
            score += 0.4
        if osm_data.get('nearest_road_distance_m', -1) >= 0:
            score += 0.3
        if osm_data.get('infrastructure_analysis'):
            score += 0.3
        return score
    
    def _calculate_weather_quality_score(self, weather_data: Dict) -> float:
        """Calculate weather data quality score (0-1)"""
        score = 0.0
        if weather_data.get('temperature') is not None:
            score += 0.3
        if weather_data.get('wind_direction') is not None:
            score += 0.3
        if weather_data.get('wind_speed') is not None:
            score += 0.2
        if weather_data.get('api_source') != 'cached':
            score += 0.2
        return score
    
    def _calculate_scouting_quality_score(self, scouting_data: Dict) -> float:
        """Calculate scouting data quality score (0-1)"""
        observations = len(scouting_data.get('enhancements_applied', []))
        boost_points = scouting_data.get('total_boost_points', 0)
        
        if observations == 0:
            return 0.0
        elif observations >= 3 and boost_points > 10:
            return 1.0
        elif observations >= 2 and boost_points > 5:
            return 0.7
        elif observations >= 1:
            return 0.4
        else:
            return 0.0

# Global analyzer factory
def create_prediction_analyzer() -> PredictionAnalyzer:
    """Factory function to create a new prediction analyzer instance"""
    return PredictionAnalyzer()
