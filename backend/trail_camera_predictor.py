#!/usr/bin/env python3
"""
Trail Camera Placement Predictor for Mature Buck Hunting

This module predicts optimal trail camera placements to capture mature buck photos
based on movement patterns, terrain analysis, and deer behavior algorithms.

Strategy Focus:
- Pinch points and funnels where bucks naturally travel
- Scrape lines and rub routes during rut season  
- Water sources and feeding edge transitions
- Escape routes from bedding to cover
- Wind-conscious positioning for scent control

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Import existing prediction modules
try:
    from .mature_buck_predictor import get_mature_buck_predictor
    from .core import analyze_terrain_and_vegetation
except ImportError:
    from mature_buck_predictor import get_mature_buck_predictor
    from core import analyze_terrain_and_vegetation

logger = logging.getLogger(__name__)

@dataclass
class CameraPlacement:
    """Trail camera placement recommendation"""
    lat: float
    lon: float
    placement_type: str
    confidence: float
    setup_height: str
    setup_angle: str
    expected_photos: str
    best_times: List[str]
    setup_notes: List[str]
    wind_considerations: str
    seasonal_effectiveness: Dict[str, int]
    camera_settings: Dict[str, str]

class TrailCameraPredictor:
    """Predicts optimal trail camera placements for mature buck photography"""
    
    def __init__(self):
        self.mature_buck_predictor = get_mature_buck_predictor()
        
        # Camera placement strategies with effectiveness ratings
        self.placement_strategies = {
            'travel_funnel': {
                'description': 'Natural travel corridor pinch point',
                'confidence_base': 90.0,
                'photo_potential': 'High - daily travel route',
                'height': '10-12 feet',
                'angle': '30° downward, perpendicular to trail',
                'effectiveness': {'early_season': 85, 'rut': 95, 'late_season': 80}
            },
            'scrape_line': {
                'description': 'Active scrape line during rut',
                'confidence_base': 95.0,
                'photo_potential': 'Excellent - frequent rut visits',
                'height': '8-10 feet',
                'angle': '45° downward, facing scrape',
                'effectiveness': {'early_season': 60, 'rut': 98, 'late_season': 40}
            },
            'water_source': {
                'description': 'Primary water access point',
                'confidence_base': 80.0,
                'photo_potential': 'Good - daily water needs',
                'height': '8-10 feet',
                'angle': '20° downward, covering approach',
                'effectiveness': {'early_season': 90, 'rut': 70, 'late_season': 95}
            },
            'feeding_edge': {
                'description': 'Food plot or crop field edge',
                'confidence_base': 85.0,
                'photo_potential': 'Good - feeding activity',
                'height': '12-15 feet',
                'angle': 'Parallel to field edge',
                'effectiveness': {'early_season': 85, 'rut': 60, 'late_season': 90}
            },
            'escape_route': {
                'description': 'Escape corridor from bedding',
                'confidence_base': 75.0,
                'photo_potential': 'Moderate - pressure response',
                'height': '10-12 feet',
                'angle': '30° downward along escape route',
                'effectiveness': {'early_season': 70, 'rut': 80, 'late_season': 75}
            },
            'saddle_pass': {
                'description': 'Ridge saddle travel route',
                'confidence_base': 88.0,
                'photo_potential': 'High - natural highway',
                'height': '10-12 feet',
                'angle': 'Perpendicular to saddle direction',
                'effectiveness': {'early_season': 80, 'rut': 90, 'late_season': 85}
            }
        }
        
        # Camera settings by situation
        self.camera_settings = {
            'day_photos': {'trigger_speed': '0.3s', 'detection_range': '80ft', 'photo_burst': '3 photos'},
            'night_photos': {'trigger_speed': '0.5s', 'detection_range': '60ft', 'ir_flash': 'Low glow'},
            'video_mode': {'video_length': '30s', 'photo_interval': '5s', 'battery_save': 'On'}
        }

    def predict_camera_placements(self, lat: float, lon: float, terrain_features: Dict, 
                                 season: str, target_buck_age: str = "mature") -> List[CameraPlacement]:
        """
        Predict optimal trail camera placements for buck photography
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate  
            terrain_features: Terrain analysis results
            season: Hunting season (early_season, rut, late_season)
            target_buck_age: mature, young, or any
            
        Returns:
            List of trail camera placement recommendations
        """
        logger.info(f"🎥 Predicting trail camera placements for {target_buck_age} bucks in {season}")
        
        placements = []
        
        try:
            # Get mature buck movement predictions
            movement_data = self.mature_buck_predictor.predict_mature_buck_movement(
                season, 17, terrain_features, {}, lat, lon  # Evening time (17:00)
            )
            logger.info(f"✅ Movement data retrieved successfully")
            
            # Get terrain scores
            terrain_scores = self.mature_buck_predictor.analyze_mature_buck_terrain(terrain_features, lat, lon)
            logger.info(f"✅ Terrain scores calculated successfully")
            
            # 1. Travel corridor cameras
            try:
                travel_placements = self._predict_travel_corridor_cameras(
                    lat, lon, movement_data, terrain_features, season
                )
                placements.extend(travel_placements)
                logger.info(f"✅ Travel corridor cameras: {len(travel_placements)}")
            except Exception as e:
                logger.error(f"❌ Travel corridor prediction failed: {e}")
            
            # 2. Scrape line cameras (rut season priority)
            if season == 'rut':
                try:
                    scrape_placements = self._predict_scrape_line_cameras(
                        lat, lon, terrain_features, season
                    )
                    placements.extend(scrape_placements)
                    logger.info(f"✅ Scrape line cameras: {len(scrape_placements)}")
                except Exception as e:
                    logger.error(f"❌ Scrape line prediction failed: {e}")
            
            # 3. Water source cameras
            try:
                water_placements = self._predict_water_source_cameras(
                    lat, lon, terrain_features, season
                )
                placements.extend(water_placements)
                logger.info(f"✅ Water source cameras: {len(water_placements)}")
            except Exception as e:
                logger.error(f"❌ Water source prediction failed: {e}")
            
            # 4. Feeding edge cameras
            try:
                feeding_placements = self._predict_feeding_edge_cameras(
                    lat, lon, movement_data, terrain_features, season
                )
                placements.extend(feeding_placements)
                logger.info(f"✅ Feeding edge cameras: {len(feeding_placements)}")
            except Exception as e:
                logger.error(f"❌ Feeding edge prediction failed: {e}")
            
            # 5. Escape route cameras
            try:
                escape_placements = self._predict_escape_route_cameras(
                    lat, lon, movement_data, terrain_features, season
                )
                placements.extend(escape_placements)
                logger.info(f"✅ Escape route cameras: {len(escape_placements)}")
            except Exception as e:
                logger.error(f"❌ Escape route prediction failed: {e}")
            
        except Exception as e:
            logger.error(f"❌ Movement prediction failed: {e}")
            # Create basic camera placement even if movement prediction fails
            placements.append(CameraPlacement(
                lat=lat + 0.0003,
                lon=lon,
                placement_type="Basic Trail Camera",
                confidence=60.0,
                setup_height="10-12 feet",
                setup_angle="30° downward",
                expected_photos="Moderate - general deer activity",
                best_times=['Dawn', 'Dusk'],
                setup_notes=["Position along likely deer travel route", "Check for signs and trails"],
                wind_considerations="Position downwind of expected deer movement",
                seasonal_effectiveness={'early_season': 70, 'rut': 70, 'late_season': 70},
                camera_settings=self.camera_settings['day_photos']
            ))
        
        # Sort by confidence and return top 5
        placements.sort(key=lambda x: x.confidence, reverse=True)
        logger.info(f"🎯 Final camera recommendations: {len(placements)}")
        return placements[:5]

    def _calculate_distance_yards(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in yards"""
        # Simple distance calculation for short distances
        lat_diff = lat2 - lat1
        lon_diff = lon2 - lon1
        distance_degrees = np.sqrt(lat_diff**2 + lon_diff**2)
        distance_meters = distance_degrees * 111000  # Approximate meters per degree
        distance_yards = distance_meters * 1.09361  # Convert to yards
        return distance_yards

    def _predict_travel_corridor_cameras(self, lat: float, lon: float, movement_data: Dict, 
                                       terrain_features: Dict, season: str) -> List[CameraPlacement]:
        """Predict cameras along travel corridors and pinch points"""
        placements = []
        strategy = self.placement_strategies['travel_funnel']
        
        # Look for natural funnels in terrain
        slope = terrain_features.get('slope', 0)
        elevation = terrain_features.get('elevation', 0)
        cover_density = terrain_features.get('canopy_closure', 50)
        
        if slope > 10 and cover_density > 60:  # Good funnel conditions
            # Create 2-3 camera positions along likely travel routes
            for i in range(2):
                # Position cameras perpendicular to natural travel direction
                angle = 90 + (i * 180)  # East and West sides
                distance = 0.0004 + (i * 0.0002)  # 44-66 yards from center
                
                angle_rad = np.radians(angle)
                camera_lat = lat + (distance * np.cos(angle_rad))
                camera_lon = lon + (distance * np.sin(angle_rad))
                
                confidence = strategy['confidence_base']
                if slope > 20:
                    confidence += 5  # Steeper = better funnel
                if cover_density > 80:
                    confidence += 3  # More cover = better travel
                
                placements.append(CameraPlacement(
                    lat=camera_lat,
                    lon=camera_lon,
                    placement_type="Travel Corridor",
                    confidence=min(confidence, 100.0),
                    setup_height=strategy['height'],
                    setup_angle=strategy['angle'],
                    expected_photos=strategy['photo_potential'],
                    best_times=['Dawn (5-8am)', 'Dusk (5-8pm)', 'Night (8pm-5am)'],
                    setup_notes=[
                        "Position camera perpendicular to travel direction",
                        "Clear shooting lanes 20-30 yards both directions",
                        "Check for rubs and trails to confirm travel route",
                        "Use low-glow IR to avoid spooking mature bucks"
                    ],
                    wind_considerations="Position downwind of expected approach direction",
                    seasonal_effectiveness=strategy['effectiveness'],
                    camera_settings=self.camera_settings['day_photos']
                ))
        
        return placements

    def _predict_scrape_line_cameras(self, lat: float, lon: float, terrain_features: Dict, 
                                   season: str) -> List[CameraPlacement]:
        """Predict cameras on scrape lines during rut"""
        placements = []
        strategy = self.placement_strategies['scrape_line']
        
        # Scrapes typically occur along ridge lines and field edges
        elevation = terrain_features.get('elevation', 0)
        edge_density = terrain_features.get('edge_density', 0)
        
        if elevation > 400 or edge_density > 0.3:  # Good scrape habitat
            # Position camera to monitor likely scrape locations
            angle = 180  # South-facing for best scrape activity
            distance = 0.0003  # ~33 yards
            
            angle_rad = np.radians(angle)
            camera_lat = lat + (distance * np.cos(angle_rad))
            camera_lon = lon + (distance * np.sin(angle_rad))
            
            confidence = strategy['confidence_base']
            if season == 'rut':
                confidence += 5  # Peak effectiveness
            
            placements.append(CameraPlacement(
                lat=camera_lat,
                lon=camera_lon,
                placement_type="Scrape Line Monitor",
                confidence=confidence,
                setup_height=strategy['height'],
                setup_angle=strategy['angle'],
                expected_photos=strategy['photo_potential'],
                best_times=['Pre-dawn (4-6am)', 'Night (9pm-4am)', 'Overcast days'],
                setup_notes=[
                    "Position 15-20 yards from active scrape",
                    "Face camera toward overhanging licking branch",
                    "Use video mode to capture full behavior sequence",
                    "Mock scrape can increase activity if legal"
                ],
                wind_considerations="Critical - position so buck approaches from downwind",
                seasonal_effectiveness=strategy['effectiveness'],
                camera_settings=self.camera_settings['video_mode']
            ))
            
        return placements

    def _predict_water_source_cameras(self, lat: float, lon: float, terrain_features: Dict, 
                                    season: str) -> List[CameraPlacement]:
        """Predict cameras at water sources"""
        placements = []
        strategy = self.placement_strategies['water_source']
        
        water_proximity = terrain_features.get('water_proximity', 1000)
        
        if water_proximity <= 200:  # Close to water source
            # Position camera to monitor water approach
            angle = 45  # Northeast approach (common deer approach)
            distance = 0.0002  # ~22 yards from water
            
            angle_rad = np.radians(angle)
            camera_lat = lat + (distance * np.cos(angle_rad))
            camera_lon = lon + (distance * np.sin(angle_rad))
            
            confidence = strategy['confidence_base']
            if water_proximity <= 100:
                confidence += 10  # Very close to water
            if season == 'late_season':
                confidence += 5  # Water more critical in cold weather
            
            placements.append(CameraPlacement(
                lat=camera_lat,
                lon=camera_lon,
                placement_type="Water Source Monitor",
                confidence=confidence,
                setup_height=strategy['height'],
                setup_angle=strategy['angle'],
                expected_photos=strategy['photo_potential'],
                best_times=['Midday (10am-2pm)', 'Evening (4-7pm)', 'Hot weather'],
                setup_notes=[
                    "Position to cover main approach trail to water",
                    "Higher placement to avoid moisture damage",
                    "Multiple approach angles if water source is large",
                    "Excellent for inventory of all deer using area"
                ],
                wind_considerations="Position so wind carries scent away from water",
                seasonal_effectiveness=strategy['effectiveness'],
                camera_settings=self.camera_settings['day_photos']
            ))
            
        return placements

    def _predict_feeding_edge_cameras(self, lat: float, lon: float, movement_data: Dict,
                                    terrain_features: Dict, season: str) -> List[CameraPlacement]:
        """Predict cameras at feeding areas and field edges"""
        placements = []
        strategy = self.placement_strategies['feeding_edge']
        
        ag_proximity = terrain_features.get('ag_proximity', 1000)
        edge_density = terrain_features.get('edge_density', 0)
        
        if ag_proximity <= 300 or edge_density > 0.4:  # Near feeding opportunities
            # Position camera along field edge or food plot
            angle = 270  # West side of field (typical position)
            distance = 0.0004  # ~44 yards
            
            angle_rad = np.radians(angle)
            camera_lat = lat + (distance * np.cos(angle_rad))
            camera_lon = lon + (distance * np.sin(angle_rad))
            
            confidence = strategy['confidence_base']
            if ag_proximity <= 150:
                confidence += 8  # Very close to agriculture
            if season in ['early_season', 'late_season']:
                confidence += 5  # Peak feeding seasons
            
            placements.append(CameraPlacement(
                lat=camera_lat,
                lon=camera_lon,
                placement_type="Feeding Edge Monitor",
                confidence=confidence,
                setup_height=strategy['height'],
                setup_angle=strategy['angle'],
                expected_photos=strategy['photo_potential'],
                best_times=['Dawn (30min before sunrise)', 'Dusk (30min after sunset)', 'Moonlit nights'],
                setup_notes=[
                    "Position parallel to field edge for side shots",
                    "Higher mounting for broader field of view",
                    "Look for tracks and trails entering field",
                    "Best photos during feeding activity"
                ],
                wind_considerations="Position so wind blows from field toward woods",
                seasonal_effectiveness=strategy['effectiveness'],
                camera_settings=self.camera_settings['night_photos']
            ))
            
        return placements

    def _predict_escape_route_cameras(self, lat: float, lon: float, movement_data: Dict,
                                    terrain_features: Dict, season: str) -> List[CameraPlacement]:
        """Predict cameras along escape routes from bedding areas"""
        placements = []
        strategy = self.placement_strategies['escape_route']
        
        # Use bedding predictions to identify escape routes
        bedding_areas = movement_data.get('bedding_predictions', [])
        
        if bedding_areas and len(bedding_areas) > 0:
            # Get first bedding area safely
            first_bedding = bedding_areas[0]
            bedding_lat = first_bedding.get('lat', lat)
            bedding_lon = first_bedding.get('lon', lon)
            
            # Calculate escape route direction (away from pressure)
            escape_angle = 135  # Southeast escape (away from typical pressure)
            distance = 0.0003  # ~33 yards from bedding
            
            angle_rad = np.radians(escape_angle)
            camera_lat = bedding_lat + (distance * np.cos(angle_rad))
            camera_lon = bedding_lon + (distance * np.sin(angle_rad))
            
            confidence = strategy['confidence_base']
            cover_density = terrain_features.get('canopy_closure', 50)
            if cover_density > 75:
                confidence += 8  # Better escape cover
            
            placements.append(CameraPlacement(
                lat=camera_lat,
                lon=camera_lon,
                placement_type="Escape Route Monitor",
                confidence=confidence,
                setup_height=strategy['height'],
                setup_angle=strategy['angle'],
                expected_photos=strategy['photo_potential'],
                best_times=['Early morning (during pressure)', 'After hunting activity', 'Weather fronts'],
                setup_notes=[
                    "Position along likely escape corridor from bedding",
                    "Monitor for pressure response patterns",
                    "Check for multiple escape route options",
                    "Low-profile setup to avoid detection"
                ],
                wind_considerations="Critical - bucks will circle to check wind",
                seasonal_effectiveness=strategy['effectiveness'],
                camera_settings=self.camera_settings['day_photos']
            ))
        else:
            # No bedding areas found, create generic escape route camera
            logger.info("No bedding areas found, creating generic escape route camera")
            
            # Position camera along likely escape direction from center point
            escape_angle = 135  # Southeast escape
            distance = 0.0003  # ~33 yards
            
            angle_rad = np.radians(escape_angle)
            camera_lat = lat + (distance * np.cos(angle_rad))
            camera_lon = lon + (distance * np.sin(angle_rad))
            
            confidence = strategy['confidence_base'] - 15  # Lower confidence without bedding data
            
            placements.append(CameraPlacement(
                lat=camera_lat,
                lon=camera_lon,
                placement_type="General Escape Route",
                confidence=confidence,
                setup_height=strategy['height'],
                setup_angle=strategy['angle'],
                expected_photos="Moderate - general pressure escape route",
                best_times=['Early morning', 'After disturbance', 'Weather changes'],
                setup_notes=[
                    "Position along general escape direction",
                    "Monitor for deer movement patterns",
                    "Adjust based on observed deer sign",
                    "Low-profile setup recommended"
                ],
                wind_considerations="Position downwind of expected approach",
                seasonal_effectiveness=strategy['effectiveness'],
                camera_settings=self.camera_settings['day_photos']
            ))
            
        return placements

def get_trail_camera_predictor():
    """Get trail camera predictor instance"""
    return TrailCameraPredictor()

# Example usage for testing
if __name__ == "__main__":
    # Test camera placement prediction
    predictor = TrailCameraPredictor()
    
    # Sample terrain data
    test_terrain = {
        'elevation': 800,
        'slope': 15,
        'canopy_closure': 75,
        'water_proximity': 150,
        'ag_proximity': 250,
        'edge_density': 0.6
    }
    
    placements = predictor.predict_camera_placements(
        44.26, -72.58, test_terrain, 'rut'
    )
    
    print(f"🎥 Generated {len(placements)} trail camera recommendations:")
    for i, placement in enumerate(placements, 1):
        print(f"\n{i}. {placement.placement_type} (Confidence: {placement.confidence:.1f}%)")
        print(f"   📍 Position: {placement.lat:.6f}, {placement.lon:.6f}")
        print(f"   📏 Setup: {placement.setup_height} high, {placement.setup_angle}")
        print(f"   📸 Expected: {placement.expected_photos}")
        print(f"   ⏰ Best times: {', '.join(placement.best_times)}")
