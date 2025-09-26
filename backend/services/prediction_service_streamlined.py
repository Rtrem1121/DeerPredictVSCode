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

Author: GitHub Copilot  
Version: 3.0.0 - Exclusive Enhanced Bedding Integration
Date: August 28, 2025
"""

from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Streamlined prediction service using EnhancedBeddingZonePredictor exclusively.
    
    This service uses comprehensive biological analysis with real-time data integration:
    - GEE (Google Earth Engine) for canopy and vegetation data
    - Open-Meteo for weather and thermal analysis  
    - Open-Elevation for terrain elevation data
    - OSM (OpenStreetMap) for security and road proximity analysis
    """
    
    def __init__(self):
        """Initialize the prediction service with EnhancedBeddingZonePredictor as primary engine."""
        try:
            self.predictor = EnhancedBeddingZonePredictor()
            logger.info("✅ EnhancedBeddingZonePredictor initialized as exclusive prediction engine")
        except Exception as e:
            logger.error(f"❌ Failed to initialize EnhancedBeddingZonePredictor: {e}")
            raise

    async def predict(
        self,
        lat: float,
        lon: float,
        time_of_day: int,
        season: str,
        hunting_pressure: str,
        target_datetime=None,
    ) -> Dict:
        """
        Generate comprehensive deer movement prediction using EnhancedBeddingZonePredictor exclusively.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            time_of_day: Hour of day (0-23)
            season: Season ('spring', 'summer', 'fall', 'winter')
            hunting_pressure: Pressure level ('low', 'medium', 'high')
            
        Returns:
            Dict: Enhanced prediction results with comprehensive data integration
        """
        try:
            # Use EnhancedBeddingZonePredictor exclusively
            result = self.predictor.run_enhanced_biological_analysis(
                lat,
                lon,
                time_of_day,
                season,
                hunting_pressure,
                target_datetime=target_datetime,
            )
            
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
            gee_data = result.get('gee_data', {})
            osm_data = result.get('osm_data', {})
            weather_data = result.get('weather_data', {})
            
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
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced prediction failed: {e}")
            raise


# Global service instance
_prediction_service = None


def get_prediction_service() -> PredictionService:
    """Get the singleton prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
