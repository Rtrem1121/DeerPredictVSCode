#!/usr/bin/env python3
"""
Prediction Service Module

Centralized service for deer movement prediction logic, following the Service Layer pattern.
This module extracts the core prediction business logic from the API layer.

Key Responsibilities:
- Orchestrate prediction workflow
- Coordinate terrain, weather, and scouting data
- Generate prediction results
- Handle error scenarios gracefully

Author: GitHub Copilot  
Version: 1.0.0
Date: August 14, 2025
"""

import logging
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Core domain imports
from backend import core
from backend.mature_buck_predictor import get_mature_buck_predictor, generate_mature_buck_stand_recommendations
from backend.scoring_engine import get_scoring_engine, ScoringContext, score_with_context
from backend.distance_scorer import get_distance_scorer, score_stand_placement
from scouting_prediction_enhancer import get_scouting_enhancer

logger = logging.getLogger(__name__)


@dataclass
class PredictionContext:
    """Context object containing all prediction input parameters"""
    lat: float
    lon: float
    date_time: datetime
    season: str
    fast_mode: bool = False
    suggestion_threshold: float = 5.0
    min_suggestion_rating: float = 8.0


@dataclass
class PredictionResult:
    """Structured result object for predictions"""
    travel_corridors: Dict[str, Any]
    bedding_zones: Dict[str, Any]  
    feeding_areas: Dict[str, Any]
    mature_buck_opportunities: Optional[Dict[str, Any]]
    stand_rating: float
    notes: str
    terrain_heatmap: str
    vegetation_heatmap: str
    travel_score_heatmap: str
    bedding_score_heatmap: str
    feeding_score_heatmap: str
    suggested_spots: List[Dict[str, Any]]
    stand_recommendations: List[Dict[str, Any]]
    five_best_stands: List[Dict[str, Any]]
    hunt_schedule: List[Dict[str, Any]]
    mature_buck_analysis: Optional[Dict[str, Any]]


class PredictionServiceError(Exception):
    """Custom exception for prediction service errors"""
    pass


class TerrainAnalysisError(PredictionServiceError):
    """Error during terrain analysis"""
    pass


class WeatherDataError(PredictionServiceError):
    """Error retrieving weather data"""
    pass


class ScoutingDataError(PredictionServiceError):
    """Error processing scouting data"""
    pass


class PredictionService:
    """
    Core prediction service implementing the business logic for deer movement prediction.
    
    This service orchestrates the entire prediction workflow:
    1. Terrain and vegetation analysis
    2. Weather data integration
    3. Rule engine execution
    4. Scouting data enhancement
    5. Mature buck analysis
    6. Stand recommendations
    7. Hunt schedule generation
    """
    
    def __init__(self):
        self.core = core
        self.scoring_engine = get_scoring_engine()
        self.distance_scorer = get_distance_scorer()
        self.mature_buck_predictor = get_mature_buck_predictor()
        self.scouting_enhancer = get_scouting_enhancer()
        
    def predict(self, context: PredictionContext) -> PredictionResult:
        """
        Generate comprehensive deer movement prediction.
        
        Args:
            context: Prediction parameters and settings
            
        Returns:
            PredictionResult: Complete prediction analysis
            
        Raises:
            PredictionServiceError: If prediction fails
        """
        try:
            logger.info(f"Starting prediction for {context.lat:.4f}, {context.lon:.4f}")
            
            # Step 1: Analyze terrain and vegetation
            terrain_data = self._analyze_terrain(context)
            
            # Step 2: Get weather conditions
            weather_data = self._get_weather_data(context)
            
            # Step 3: Execute rule engine
            score_maps = self._execute_rule_engine(context, terrain_data, weather_data)
            
            # Step 4: Enhance with scouting data
            enhanced_scores = self._enhance_with_scouting_data(context, score_maps)
            
            # Step 5: Generate mature buck analysis
            mature_buck_data = self._analyze_mature_buck_opportunities(context, terrain_data, weather_data)
            
            # Step 6: Generate stand recommendations
            stand_recommendations = self._generate_stand_recommendations(context, enhanced_scores, mature_buck_data)
            
            # Step 7: Create hunt schedule
            hunt_schedule = self._generate_hunt_schedule(context, stand_recommendations, weather_data)
            
            # Step 8: Build final result
            result = self._build_prediction_result(
                context, terrain_data, enhanced_scores, mature_buck_data, 
                stand_recommendations, hunt_schedule
            )
            
            logger.info(f"Prediction completed successfully with rating: {result.stand_rating}")
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise PredictionServiceError(f"Prediction generation failed: {str(e)}") from e
    
    def _analyze_terrain(self, context: PredictionContext) -> Dict[str, Any]:
        """Analyze terrain and vegetation for the prediction area"""
        try:
            logger.debug("Analyzing terrain and vegetation")
            
            # Get terrain features using core analysis
            features = self.core.analyze_terrain_and_vegetation(
                context.lat, context.lon, context.fast_mode
            )
            
            if not features:
                raise TerrainAnalysisError("Failed to retrieve terrain data")
                
            logger.debug(f"Terrain analysis complete: {len(features)} features extracted")
            return features
            
        except Exception as e:
            raise TerrainAnalysisError(f"Terrain analysis failed: {str(e)}") from e
    
    def _get_weather_data(self, context: PredictionContext) -> Dict[str, Any]:
        """Retrieve weather data for prediction"""
        try:
            logger.debug("Retrieving weather data")
            
            weather_data = self.core.get_weather_data(context.lat, context.lon)
            
            if not weather_data:
                logger.warning("Weather data unavailable, using defaults")
                weather_data = self._get_default_weather_data()
                
            logger.debug("Weather data retrieved successfully")
            return weather_data
            
        except Exception as e:
            logger.warning(f"Weather retrieval failed: {e}, using defaults")
            return self._get_default_weather_data()
    
    def _execute_rule_engine(self, context: PredictionContext, terrain_data: Dict[str, Any], 
                           weather_data: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """Execute the deer behavior rule engine"""
        try:
            logger.debug("Executing rule engine")
            
            # Load rules and prepare conditions
            rules = self._load_rules()
            conditions = self._build_conditions(context, weather_data)
            
            # Execute grid-based rule engine
            score_maps = self.core.run_grid_rule_engine(rules, terrain_data, conditions)
            
            # Validate score maps
            if not self._validate_score_maps(score_maps):
                raise PredictionServiceError("Invalid score maps generated")
                
            logger.debug(f"Rule engine complete: Travel max={np.max(score_maps['travel']):.2f}")
            return score_maps
            
        except Exception as e:
            raise PredictionServiceError(f"Rule engine execution failed: {str(e)}") from e
    
    def _enhance_with_scouting_data(self, context: PredictionContext, 
                                  score_maps: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Enhance predictions with historical scouting data"""
        try:
            logger.debug("Enhancing with scouting data")
            
            enhancement_result = self.scouting_enhancer.enhance_predictions(
                context.lat, context.lon, score_maps, 0.04, self.core.GRID_SIZE
            )
            
            enhanced_score_maps = enhancement_result.get("enhanced_score_maps", score_maps)
            
            if enhancement_result.get("enhancements_applied"):
                logger.info(f"Applied {len(enhancement_result['enhancements_applied'])} scouting enhancements")
            else:
                logger.info("No scouting data available for enhancement")
                
            return {
                "score_maps": enhanced_score_maps,
                "enhancement_result": enhancement_result
            }
            
        except Exception as e:
            logger.warning(f"Scouting enhancement failed: {e}, using base predictions")
            return {
                "score_maps": score_maps,
                "enhancement_result": {"enhancements_applied": [], "mature_buck_indicators": 0}
            }
    
    def _analyze_mature_buck_opportunities(self, context: PredictionContext, 
                                         terrain_data: Dict[str, Any], 
                                         weather_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate mature buck movement analysis"""
        try:
            logger.debug("Analyzing mature buck opportunities")
            
            current_hour = context.date_time.hour
            
            mature_buck_data = self.mature_buck_predictor.generate_mature_buck_predictions(
                context.lat, context.lon, terrain_data, weather_data, context.season, current_hour
            )
            
            if mature_buck_data and mature_buck_data.get('viable_location', False):
                logger.info("Mature buck analysis indicates viable location")
            else:
                logger.info("Location not optimal for mature buck hunting")
                
            return mature_buck_data
            
        except Exception as e:
            logger.warning(f"Mature buck analysis failed: {e}, using simplified analysis")
            return self._get_default_mature_buck_data()
    
    def _generate_stand_recommendations(self, context: PredictionContext, 
                                      enhanced_data: Dict[str, Any],
                                      mature_buck_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate optimized stand placement recommendations"""
        try:
            logger.debug("Generating stand recommendations")
            
            from backend.main import get_five_best_stand_locations_enhanced
            
            # Generate five best stand locations
            five_best_stands = get_five_best_stand_locations_enhanced(
                context.lat, context.lon, 
                enhanced_data.get("terrain_features", {}),
                {}, context.season, 
                enhanced_data["score_maps"], 
                mature_buck_data
            )
            
            logger.debug(f"Generated {len(five_best_stands)} stand recommendations")
            return five_best_stands
            
        except Exception as e:
            logger.warning(f"Stand recommendation generation failed: {e}")
            return []
    
    def _generate_hunt_schedule(self, context: PredictionContext, 
                              stand_recommendations: List[Dict[str, Any]],
                              weather_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate 48-hour hunt schedule"""
        try:
            logger.debug("Generating hunt schedule")
            
            from backend.main import compute_hourly_hunt_schedule
            
            hourly48 = weather_data.get('next_48h_hourly', [])
            
            hunt_schedule = compute_hourly_hunt_schedule(
                context.lat, context.lon, stand_recommendations, 
                {}, context.season, hourly48, huntable_threshold=75.0
            )
            
            logger.debug(f"Generated {len(hunt_schedule)} scheduled hunting windows")
            return hunt_schedule
            
        except Exception as e:
            logger.warning(f"Hunt schedule generation failed: {e}")
            return []
    
    def _build_prediction_result(self, context: PredictionContext, terrain_data: Dict[str, Any],
                               enhanced_data: Dict[str, Any], mature_buck_data: Optional[Dict[str, Any]],
                               stand_recommendations: List[Dict[str, Any]], 
                               hunt_schedule: List[Dict[str, Any]]) -> PredictionResult:
        """Build the final prediction result object"""
        try:
            score_maps = enhanced_data["score_maps"]
            
            # Generate zones and corridors from score maps
            travel_corridors = self.core.generate_corridors_from_scores(score_maps['travel'])
            bedding_zones = self.core.generate_zones_from_scores(score_maps['bedding'])
            feeding_zones = self.core.generate_zones_from_scores(score_maps['feeding'])
            
            # Calculate overall stand rating
            stand_rating = self._calculate_stand_rating(score_maps)
            
            # Generate notes
            notes = self._generate_prediction_notes(context, enhanced_data, mature_buck_data)
            
            # Generate heatmaps
            heatmaps = self._generate_heatmaps(terrain_data, score_maps)
            
            return PredictionResult(
                travel_corridors=travel_corridors,
                bedding_zones=bedding_zones,
                feeding_areas=feeding_zones,
                mature_buck_opportunities=mature_buck_data,
                stand_rating=stand_rating,
                notes=notes,
                terrain_heatmap=heatmaps['terrain'],
                vegetation_heatmap=heatmaps['vegetation'],
                travel_score_heatmap=heatmaps['travel_score'],
                bedding_score_heatmap=heatmaps['bedding_score'],
                feeding_score_heatmap=heatmaps['feeding_score'],
                suggested_spots=[],  # TODO: Implement suggestion logic
                stand_recommendations=stand_recommendations,
                five_best_stands=stand_recommendations,
                hunt_schedule=hunt_schedule,
                mature_buck_analysis=mature_buck_data
            )
            
        except Exception as e:
            raise PredictionServiceError(f"Failed to build prediction result: {str(e)}") from e
    
    # Helper methods
    
    def _load_rules(self) -> List[Dict[str, Any]]:
        """Load deer behavior rules"""
        from backend.main import load_rules
        return load_rules()
    
    def _build_conditions(self, context: PredictionContext, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build condition parameters for rule engine"""
        conditions = {
            "season": context.season,
            "time_of_day": self.core.get_time_of_day(context.date_time.hour),
            "weather_favorable": weather_data.get('temp', 20) < 25,
            "moon_boost": self.core.get_moon_phase(context.date_time) == "new"
        }
        return conditions
    
    def _validate_score_maps(self, score_maps: Dict[str, np.ndarray]) -> bool:
        """Validate that score maps are properly formed"""
        required_keys = ['travel', 'bedding', 'feeding']
        for key in required_keys:
            if key not in score_maps:
                return False
            if not isinstance(score_maps[key], np.ndarray):
                return False
            if score_maps[key].size == 0:
                return False
        return True
    
    def _calculate_stand_rating(self, score_maps: Dict[str, np.ndarray]) -> float:
        """Calculate overall stand rating from score maps"""
        travel_max = np.max(score_maps['travel'])
        bedding_max = np.max(score_maps['bedding'])
        feeding_max = np.max(score_maps['feeding'])
        
        # Weighted average with travel corridor emphasis
        rating = (travel_max * 0.4 + bedding_max * 0.3 + feeding_max * 0.3)
        return min(rating, 10.0)  # Cap at 10
    
    def _generate_prediction_notes(self, context: PredictionContext, 
                                 enhanced_data: Dict[str, Any],
                                 mature_buck_data: Optional[Dict[str, Any]]) -> str:
        """Generate comprehensive prediction notes"""
        notes = f"## Deer Movement Prediction - {context.season.title()}\n\n"
        notes += f"**Location**: {context.lat:.4f}, {context.lon:.4f}\n"
        notes += f"**Date/Time**: {context.date_time.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        # Add enhancement summary
        enhancement_result = enhanced_data.get("enhancement_result", {})
        if enhancement_result.get("enhancements_applied"):
            notes += f"**Scouting Data**: {len(enhancement_result['enhancements_applied'])} enhancements applied\n"
        
        # Add mature buck analysis if available
        if mature_buck_data and mature_buck_data.get('viable_location', False):
            notes += f"**Mature Buck Viability**: {mature_buck_data['confidence_summary']['overall_suitability']:.1f}%\n"
        
        return notes
    
    def _generate_heatmaps(self, terrain_data: Dict[str, Any], 
                          score_maps: Dict[str, np.ndarray]) -> Dict[str, str]:
        """Generate base64 encoded heatmap images"""
        # TODO: Implement actual heatmap generation
        return {
            'terrain': '',
            'vegetation': '',
            'travel_score': '',
            'bedding_score': '',
            'feeding_score': ''
        }
    
    def _get_default_weather_data(self) -> Dict[str, Any]:
        """Return default weather data when API fails"""
        return {
            'temp': 20,
            'humidity': 60,
            'wind_speed': 5,
            'conditions': 'partly_cloudy',
            'next_48h_hourly': []
        }
    
    def _get_default_mature_buck_data(self) -> Dict[str, Any]:
        """Return default mature buck data when analysis fails"""
        return {
            'viable_location': False,
            'terrain_scores': {
                'overall_suitability': 0.0,
                'bedding_suitability': 0.0,
                'escape_route_quality': 0.0,
                'isolation_score': 0.0,
                'pressure_resistance': 0.0
            },
            'movement_prediction': {
                'movement_probability': 0.0,
                'confidence_score': 0.0,
                'behavioral_notes': []
            },
            'stand_recommendations': [],
            'opportunity_markers': [],
            'confidence_summary': {
                'overall_suitability': 0.0,
                'movement_confidence': 0.0,
                'pressure_tolerance': 0.0
            }
        }


# Service Factory
_prediction_service_instance = None

def get_prediction_service() -> PredictionService:
    """Get singleton instance of prediction service"""
    global _prediction_service_instance
    if _prediction_service_instance is None:
        _prediction_service_instance = PredictionService()
    return _prediction_service_instance
