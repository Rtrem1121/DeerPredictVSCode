#!/usr/bin/env python3
"""
Enhanced Prediction API Integration

Integrates the enhanced prediction engine with satellite data
into the existing FastAPI backend system.

Author: GitHub Copilot
Date: August 14, 2025
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import HTTPException

from backend.enhanced_prediction_engine import get_enhanced_prediction_engine
from backend import core

logger = logging.getLogger(__name__)

class EnhancedPredictionAPI:
    """
    API layer for enhanced prediction functionality
    """
    
    def __init__(self):
        self.engine = get_enhanced_prediction_engine()
        self.core = core
    
    async def generate_enhanced_prediction(self, 
                                         lat: float, 
                                         lon: float, 
                                         hunt_date: Optional[str] = None,
                                         season: str = "early_season") -> Dict[str, Any]:
        """
        Generate enhanced prediction with satellite integration
        
        Args:
            lat: Latitude for hunting area
            lon: Longitude for hunting area  
            hunt_date: Target hunt date (ISO format)
            season: Hunting season
            
        Returns:
            Enhanced prediction results
        """
        
        try:
            # Parse hunt date
            if hunt_date:
                hunt_datetime = datetime.fromisoformat(hunt_date.replace('Z', '+00:00'))
            else:
                hunt_datetime = datetime.now(timezone.utc)
            
            logger.info(f"🎯 Starting enhanced prediction for {lat:.4f}, {lon:.4f}")
            
            # Get weather data using existing core functionality
            weather_data = await self._get_weather_data(lat, lon)
            
            # Get terrain features using existing analysis
            terrain_features = await self._get_terrain_features(lat, lon)
            
            # Generate enhanced prediction
            prediction_result = self.engine.generate_enhanced_prediction(
                lat=lat,
                lon=lon,
                date_time=hunt_datetime,
                season=season,
                weather_data=weather_data,
                terrain_features=terrain_features
            )
            
            # Add metadata
            prediction_result.update({
                'request_parameters': {
                    'latitude': lat,
                    'longitude': lon,
                    'hunt_date': hunt_date,
                    'season': season
                },
                'api_version': 'enhanced_v1.0',
                'processing_timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"✅ Enhanced prediction completed with {prediction_result.get('enhancement_level', 'unknown')} enhancement")
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"Enhanced prediction failed: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Enhanced prediction generation failed: {str(e)}"
            )
    
    async def compare_prediction_methods(self, 
                                       lat: float, 
                                       lon: float,
                                       hunt_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Compare standard vs enhanced prediction methods
        
        Args:
            lat: Latitude
            lon: Longitude
            hunt_date: Target hunt date
            
        Returns:
            Comparison of prediction methods
        """
        
        try:
            # Generate both standard and enhanced predictions
            enhanced_result = await self.generate_enhanced_prediction(lat, lon, hunt_date)
            standard_result = await self._generate_standard_prediction(lat, lon, hunt_date)
            
            # Calculate improvement metrics
            improvement_metrics = self._calculate_improvement_metrics(
                standard_result, enhanced_result
            )
            
            return {
                'comparison_type': 'standard_vs_enhanced',
                'standard_prediction': standard_result,
                'enhanced_prediction': enhanced_result,
                'improvement_metrics': improvement_metrics,
                'recommendation': self._generate_method_recommendation(improvement_metrics),
                'comparison_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Prediction comparison failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Prediction comparison failed: {str(e)}"
            )
    
    async def get_vegetation_summary(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get vegetation analysis summary for hunting area
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Vegetation analysis summary
        """
        
        try:
            vegetation_analyzer = self.engine.vegetation_analyzer
            vegetation_data = vegetation_analyzer.analyze_hunting_area(lat, lon, radius_km=2.0)
            
            # Create hunter-friendly summary
            summary = {
                'vegetation_health': vegetation_data.get('vegetation_health', {}),
                'food_sources': vegetation_data.get('food_sources', {}),
                'land_cover_summary': self._summarize_land_cover(
                    vegetation_data.get('land_cover', {})
                ),
                'hunting_suitability': vegetation_data.get('land_cover', {}).get('habitat_suitability', 'moderate'),
                'water_availability': vegetation_data.get('water_proximity', {}),
                'analysis_quality': vegetation_data.get('analysis_metadata', {}),
                'key_insights': self._extract_vegetation_insights(vegetation_data)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Vegetation summary failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Vegetation analysis failed: {str(e)}"
            )
    
    async def _get_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather data using existing core functionality"""
        try:
            # Use existing weather functionality from core
            weather_result = self.core.get_weather_data(lat, lon)
            return weather_result if weather_result else {}
        except Exception as e:
            logger.warning(f"Weather data retrieval failed: {e}")
            return {}
    
    async def _get_terrain_features(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get terrain features using existing analysis"""
        try:
            # Use existing terrain analysis from core
            terrain_result = self.core.analyze_terrain(lat, lon)
            return terrain_result if terrain_result else {}
        except Exception as e:
            logger.warning(f"Terrain analysis failed: {e}")
            return {}
    
    async def _generate_standard_prediction(self, lat: float, lon: float, 
                                          hunt_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate standard prediction for comparison"""
        try:
            # Use existing core prediction functionality
            date_str = hunt_date or datetime.now().isoformat()
            standard_result = self.core.predict_deer_movement(lat, lon, date_str)
            return {
                'prediction_type': 'standard',
                'movement_probability': standard_result.get('probability', 0.5),
                'confidence_level': 'standard',
                'data_sources': ['weather', 'terrain', 'historical']
            }
        except Exception as e:
            logger.warning(f"Standard prediction failed: {e}")
            return {
                'prediction_type': 'standard_fallback',
                'movement_probability': 0.5,
                'confidence_level': 'low'
            }
    
    def _calculate_improvement_metrics(self, standard: Dict[str, Any], 
                                     enhanced: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate improvement metrics between prediction methods"""
        
        standard_prob = standard.get('movement_probability', 0.5)
        enhanced_prob = enhanced.get('movement_predictions', {}).get('movement_probability', 0.5)
        
        confidence_improvement = self._assess_confidence_improvement(standard, enhanced)
        data_richness_improvement = self._assess_data_richness(standard, enhanced)
        
        return {
            'probability_difference': round(enhanced_prob - standard_prob, 3),
            'confidence_improvement': confidence_improvement,
            'data_richness_score': data_richness_improvement,
            'additional_insights_count': len(enhanced.get('hunting_insights', [])),
            'satellite_enhancement_active': enhanced.get('enhancement_level') != 'none',
            'vegetation_analysis_available': 'vegetation_analysis' in enhanced,
            'overall_improvement_score': self._calculate_overall_improvement(
                enhanced_prob - standard_prob, confidence_improvement, data_richness_improvement
            )
        }
    
    def _generate_method_recommendation(self, metrics: Dict[str, Any]) -> str:
        """Generate recommendation on which prediction method to use"""
        
        improvement_score = metrics.get('overall_improvement_score', 0)
        
        if improvement_score > 0.6:
            return "Enhanced prediction strongly recommended - significant improvements in accuracy and insights"
        elif improvement_score > 0.3:
            return "Enhanced prediction recommended - moderate improvements available"
        elif improvement_score > 0:
            return "Enhanced prediction slightly better - marginal improvements"
        else:
            return "Standard prediction sufficient - minimal enhancement benefit"
    
    def _summarize_land_cover(self, land_cover: Dict[str, Any]) -> Dict[str, Any]:
        """Create hunter-friendly land cover summary"""
        
        percentages = land_cover.get('land_cover_percentages', {})
        
        return {
            'forest_coverage': percentages.get('deciduous_forest', 0) + percentages.get('evergreen_forest', 0),
            'agricultural_areas': percentages.get('cultivated_crops', 0) + percentages.get('hay_pasture', 0),
            'water_features': percentages.get('open_water', 0) + percentages.get('woody_wetlands', 0),
            'developed_areas': percentages.get('developed_high', 0) + percentages.get('developed_medium', 0),
            'grassland_openings': percentages.get('grassland_herbaceous', 0),
            'hunting_quality_rating': land_cover.get('habitat_suitability', 'moderate')
        }
    
    def _extract_vegetation_insights(self, vegetation_data: Dict[str, Any]) -> List[str]:
        """Extract key insights from vegetation analysis"""
        
        insights = []
        
        # NDVI insights
        ndvi_analysis = vegetation_data.get('ndvi_analysis', {})
        if ndvi_analysis.get('health_rating') == 'excellent':
            insights.append("Excellent vegetation health - high deer activity expected")
        elif ndvi_analysis.get('health_rating') == 'poor':
            insights.append("Poor vegetation health - deer may be concentrated near food sources")
        
        # Food source insights
        food_sources = vegetation_data.get('food_sources', {})
        food_abundance = food_sources.get('food_abundance', 'moderate')
        if food_abundance == 'high':
            insights.append("High food abundance - increased deer movement likely")
        elif food_abundance == 'low':
            insights.append("Limited food sources - predictable deer patterns expected")
        
        # Land cover insights
        land_cover = vegetation_data.get('land_cover', {})
        habitat_suitability = land_cover.get('habitat_suitability', 'moderate')
        if habitat_suitability == 'excellent':
            insights.append("Excellent habitat suitability for deer populations")
        
        return insights
    
    # Helper methods
    def _assess_confidence_improvement(self, standard: Dict, enhanced: Dict) -> float:
        """Assess confidence improvement from enhanced prediction"""
        enhanced_confidence = enhanced.get('confidence_metrics', {}).get('overall_confidence_score', 0.5)
        standard_confidence = 0.5  # Baseline standard confidence
        return round(enhanced_confidence - standard_confidence, 3)
    
    def _assess_data_richness(self, standard: Dict, enhanced: Dict) -> float:
        """Assess data richness improvement"""
        standard_sources = len(standard.get('data_sources', []))
        enhanced_sources = len([
            'satellite', 'vegetation', 'weather', 'terrain', 'pressure_mapping'
        ])
        return round((enhanced_sources - standard_sources) / enhanced_sources, 3)
    
    def _calculate_overall_improvement(self, prob_diff: float, conf_improve: float, 
                                     data_improve: float) -> float:
        """Calculate overall improvement score"""
        weighted_score = (
            abs(prob_diff) * 0.4 +  # Probability improvement
            conf_improve * 0.4 +    # Confidence improvement  
            data_improve * 0.2      # Data richness improvement
        )
        return round(min(weighted_score, 1.0), 3)


# Global instance
enhanced_prediction_api = EnhancedPredictionAPI()

def get_enhanced_prediction_api() -> EnhancedPredictionAPI:
    """Get singleton enhanced prediction API"""
    return enhanced_prediction_api
