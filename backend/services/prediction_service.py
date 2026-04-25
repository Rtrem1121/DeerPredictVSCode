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
- Apply real-time hunting context for actionable recommendations

Author: GitHub Copilot  
Version: 3.2.0 - Real-Time Context Integration
Date: September 3, 2025
"""

from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor
from dataclasses import asdict
from datetime import datetime
from backend.hunting_context_analyzer import analyze_hunting_context, create_time_aware_prediction_context
from backend.scouting_prediction_enhancer import get_scouting_enhancer
from backend.advanced_thermal_analysis import AdvancedThermalAnalyzer
from backend.analysis.wind_thermal_analyzer import get_wind_thermal_analyzer
from backend.analysis.prediction_analyzer import PredictionAnalyzer
from backend.config_manager import get_config
from backend.hunt_window.hunt_window_predictor import HuntWindowPredictor
from backend.utils.geo import haversine
from backend.vegetation_analyzer import get_vegetation_analyzer
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


def convert_numpy_types(obj):
    """
    Recursively convert numpy types to Python native types for JSON serialization.
    
    Args:
        obj: Object to convert
        
    Returns:
        Converted object with Python native types
    """
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    return obj


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
            self.vegetation_analyzer = get_vegetation_analyzer()
            self.config = get_config()
            self.hunt_window_predictor = HuntWindowPredictor.from_config(self.config)
            logger.info("[INIT] EnhancedBeddingZonePredictor initialized as exclusive prediction engine")
            logger.info("[INIT] ScoutingPredictionEnhancer initialized for field data integration")
            logger.info("[INIT] AdvancedThermalAnalyzer initialized for thermal wind analysis")
            logger.info("[INIT] WindThermalAnalyzer initialized for comprehensive wind analysis")
            logger.info("[INIT] VegetationAnalyzer initialized for Vermont food classification")
            logger.info("[INIT] HuntWindowPredictor initialized for forecast-triggered stand prioritization")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize prediction components: {e}")
            raise

    async def predict(
        self,
        lat: float,
        lon: float,
        time_of_day: int,
        season: str,
        hunting_pressure: str,
        target_datetime: Optional[datetime] = None,
    ) -> Dict:
        """
        Generate comprehensive deer movement prediction using EnhancedBeddingZonePredictor exclusively.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            time_of_day: Hour of day (0-23)
            season: Season ('spring', 'summer', 'fall', 'winter')
            hunting_pressure: Pressure level ('low', 'medium', 'high')
            target_datetime: Optional future datetime to align forecast data with
            
        Returns:
            Dict: Enhanced prediction results with comprehensive data integration, wind analysis, and thermal analysis
        """
        return await self.predict_with_analysis(
            lat,
            lon,
            time_of_day,
            season,
            hunting_pressure,
            analyzer=None,
            target_datetime=target_datetime,
        )
    
    async def predict_with_analysis(
        self,
        lat: float,
        lon: float,
        time_of_day: int,
        season: str,
        hunting_pressure: str,
        analyzer: Optional[PredictionAnalyzer] = None,
        target_datetime: Optional[datetime] = None,
    ) -> Dict:
        """
        Generate comprehensive prediction with optional detailed analysis collection.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate  
            time_of_day: Hour of day (0-23)
            season: Season ('spring', 'summer', 'fall', 'winter')
            hunting_pressure: Pressure level ('low', 'medium', 'high')
            analyzer: Optional PredictionAnalyzer for detailed analysis collection
            target_datetime: Optional future datetime to align forecast data and context
            
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
            
            # Extract environmental data for analysis
            gee_data = result.get('gee_data', {})
            osm_data = result.get('osm_data', {})
            weather_data = result.get('weather_data', {})
            
            # Collect criteria analysis if analyzer provided
            if analyzer:
                try:
                    self._collect_criteria_analysis(analyzer, result, gee_data, osm_data, weather_data)
                except Exception as e:
                    logger.warning(f"[WARN] Criteria analysis collection failed: {e}")
            
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
                
                logger.info(f"[THERMAL] THERMAL ANALYSIS: {thermal_analysis.direction} thermal, "
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
                        logger.warning(f"[WARN] Thermal analysis collection failed: {e}")
                
            except Exception as e:
                logger.warning(f"[WARN] Thermal analysis failed: {e}")
            
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
                
                logger.info(f"[WIND] WIND ANALYSIS: {len(wind_analyses)} locations analyzed, "
                           f"overall rating {wind_summary['overall_wind_conditions'].get('hunting_rating', 'N/A')}")
                
                # Collect wind analysis if analyzer provided
                if analyzer:
                    try:
                        # Properly serialize wind analysis data - convert numpy types
                        serialized_analyses = []
                        for analysis in wind_analyses:
                            analysis_dict = asdict(analysis)
                            analysis_dict = convert_numpy_types(analysis_dict)
                            serialized_analyses.append(analysis_dict)
                        
                        # Convert wind summary
                        wind_summary_clean = convert_numpy_types(wind_summary)
                        
                        analyzer.collect_wind_analysis(
                            wind_summary_clean.get('overall_wind_conditions', {}),
                            serialized_analyses,
                            wind_summary_clean
                        )
                    except Exception as e:
                        logger.warning(f"[WARN] Wind analysis collection failed: {e}", exc_info=True)
                
            except Exception as e:
                logger.error(f"[WARN] Wind analysis failed: {e}", exc_info=True)
                wind_analyses = []
                wind_summary = {}
            
            # Forecast-driven hunt window evaluation with stand wind credibility
            result['hunt_window_predictions'] = []
            result['stand_priority_overrides'] = {}
            try:
                thermal_payload = thermal_analysis.__dict__ if thermal_analysis else None
                hunt_window_eval = self.hunt_window_predictor.evaluate(
                    weather_data,
                    stand_recommendations,
                    thermal_payload,
                    current_time=target_datetime,
                ) if hasattr(self, 'hunt_window_predictor') else None

                if hunt_window_eval:
                    result['hunt_window_predictions'] = hunt_window_eval.windows_as_dict()
                    result['stand_priority_overrides'] = hunt_window_eval.stand_status_as_dict()

                    if hunt_window_eval.windows:
                        primary_window = hunt_window_eval.windows[0]
                        logger.info(
                            "[HUNT_WINDOW] HUNT WINDOW: %s aligned for %s (boost +%.1f)",
                            primary_window.stand_name,
                            primary_window.window_start.strftime('%Y-%m-%d %H:%M'),
                            primary_window.priority_boost,
                        )
                else:
                    logger.info("[HUNT_WINDOW] Hunt window predictor unavailable; skipping forecast-triggered prioritization")
            except Exception as e:
                logger.warning(f"[WARN] Hunt window predictor failed: {e}")

            # Apply scouting data enhancements to boost predictions around real field observations
            scouting_enhancement_result = {}
            try:
                # Create basic score maps from prediction results for enhancement
                # Use Vermont food classification for feeding scores
                score_maps = {
                    "travel": self._extract_travel_scores(result, lat, lon),
                    "bedding": self._extract_bedding_scores(result, lat, lon), 
                    "feeding": self._extract_feeding_scores(result, lat, lon, season)
                }
                
                # Store score_maps in result for optimized points generation
                result['score_maps'] = score_maps
                
                # Apply scouting enhancements
                scouting_enhancement_result = self.scouting_enhancer.enhance_predictions(
                    lat, lon, score_maps, span_deg=0.04, grid_size=10
                )
                
                # Log scouting enhancement details
                enhancements = scouting_enhancement_result.get('enhancements_applied', [])
                total_boost = scouting_enhancement_result.get('total_boost_points', 0)
                mature_buck_indicators = scouting_enhancement_result.get('mature_buck_indicators', 0)
                
                if enhancements:
                    logger.info(f"[SCOUTING] SCOUTING ENHANCEMENT: {len(enhancements)} observations applied")
                    logger.info(f"   Total boost: {total_boost:.1f} points")
                    logger.info(f"   Mature buck indicators: {mature_buck_indicators}")
                    
                    for enhancement in enhancements[:3]:  # Log first 3
                        obs_type = enhancement.get('observation_type', 'unknown')
                        boost = enhancement.get('boost_applied', 0)
                        age_days = enhancement.get('age_days', 0)
                        logger.info(f"   {obs_type}: +{boost:.1f}% boost ({age_days}d old)")
                else:
                    logger.info("[SCOUTING] SCOUTING ENHANCEMENT: No nearby observations found")
                    
            except Exception as e:
                logger.warning(f"[WARN] Scouting enhancement failed, using base predictions: {e}")
            
            # Collect data source and algorithm analysis if analyzer provided
            if analyzer:
                try:
                    self._collect_data_source_analysis(analyzer, gee_data, osm_data, weather_data, scouting_enhancement_result)
                    # NOTE: Algorithm analysis moved to after wind analyses are added
                    self._collect_scoring_analysis(analyzer, result)
                except Exception as e:
                    logger.warning(f"[WARN] Additional analysis collection failed: {e}")
            
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
                logger.info(f"[GEE] GEE Integration: Canopy={canopy:.1f}%")
            
            if osm_data:
                road_distance = osm_data.get('min_road_distance', 0)
                logger.info(f"[OSM] OSM Integration: Road distance={road_distance:.0f}m")
            
            if weather_data:
                temp = weather_data.get('temperature', 0)
                logger.info(f"[WEATHER] Weather Integration: Temperature={temp:.1f}┬░F")
            
            # Log individual zone details for validation
            if bedding_zones and 'features' in bedding_zones:
                for i, zone in enumerate(bedding_zones['features'][:3], 1):
                    zone_props = zone.get('properties', {})
                    zone_coords = zone.get('geometry', {}).get('coordinates', [0, 0])
                    zone_suitability = zone_props.get('suitability_score', 0)
                    zone_type = zone_props.get('bedding_type', 'unknown')
                    logger.info(f"[ZONE] Zone {i}: {zone_suitability:.1f}% {zone_type} at {zone_coords[1]:.4f}, {zone_coords[0]:.4f}")
            
            # Add wind and thermal analysis to result
            result['thermal_analysis'] = thermal_analysis.__dict__ if thermal_analysis else None
            result['wind_analyses'] = [analysis.__dict__ for analysis in wind_analyses]
            result['wind_summary'] = wind_summary
            
            # CRITICAL FIX: Collect algorithm analysis AFTER wind analyses are added to result
            if analyzer:
                try:
                    self._collect_algorithm_analysis(analyzer, result)
                    # Update wind analysis availability flag now that wind data exists
                    if hasattr(analyzer, 'criteria_analysis') and analyzer.criteria_analysis:
                        analyzer.criteria_analysis.stand_criteria['wind_analysis_available'] = bool(result.get('wind_analyses'))
                except Exception as e:
                    logger.warning(f"[WARN] Algorithm analysis collection failed: {e}")
            
            # Apply real-time hunting context analysis
            try:
                effective_time = target_datetime or datetime.now()
                # Ensure timezone-naive datetime for context analysis
                if effective_time.tzinfo is not None:
                    effective_time = effective_time.replace(tzinfo=None)
                logger.info(
                    "[CONTEXT] Applying real-time context analysis for %s on %s",
                    effective_time.strftime('%H:%M'),
                    effective_time.strftime('%B %d'),
                )
                result = create_time_aware_prediction_context(result, effective_time)
                logger.info(f"[INIT] Context applied: {result.get('context_summary', {}).get('situation', 'unknown')}")
            except Exception as e:
                logger.warning(f"[WARN] Context analysis failed: {e}")
            
            # Generate optimized points for frontend map display
            try:
                logger.info("[POINTS] Generating optimized points for frontend map display")
                from backend.mature_buck_points_generator import get_points_generator
                
                points_generator = get_points_generator()
                
                # Prepare prediction data for points generation
                prediction_data = {
                    'terrain_features': terrain_features,
                    'score_maps': result.get('score_maps', {}),
                    'security_analysis': getattr(self, '_cached_security_analysis', {}),
                    'mature_buck_analysis': result.get('mature_buck_analysis', {}),
                    'bedding_zones': result.get('bedding_zones', {}),  # Include real bedding zones from predictor
                    'gee_data': result.get('gee_data', {}),
                    'season': season,
                }
                
                # Generate all optimized points
                optimized_points = points_generator.generate_optimized_points(
                    prediction_data, lat, lon, weather_data, season=season
                )
                
                # Convert OptimizedPoint objects to dictionaries for JSON serialization
                if optimized_points:
                    serialized_points = {}
                    for category, points in optimized_points.items():
                        serialized_points[category] = []
                        for point in points:
                            serialized_points[category].append({
                                'lat': point.lat,
                                'lon': point.lon,
                                'score': point.score,
                                'description': point.description,
                                'strategy': point.strategy,
                                'optimal_times': point.optimal_times,
                                'confidence': point.confidence,
                                'real_data_sources': point.real_data_sources,
                                'specific_attributes': point.specific_attributes
                            })
                        logger.info(f"[SERIALIZE] Serialized {len(serialized_points[category])} {category} for frontend")
                    
                    result['optimized_points'] = serialized_points
                    logger.info(f"[INIT] Generated {sum(len(points) for points in serialized_points.values())} optimized points for frontend")
                else:
                    logger.warning("[WARN] No optimized points generated")
                    
            except Exception as e:
                logger.warning(f"[WARN] Optimized points generation failed: {e}")
            
            # Convert any numpy types to Python native types before returning
            result = convert_numpy_types(result)
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Enhanced prediction failed: {e}")
            raise

    def _generate_score_grid(self, center_lat: float, center_lon: float, grid_size: int = 10, span_deg: float = 0.04) -> Tuple[np.ndarray, np.ndarray]:
        """Generate lat/lon grids that match MatureBuckPointsGenerator."""
        lats = np.linspace(center_lat + span_deg/2, center_lat - span_deg/2, grid_size)
        lons = np.linspace(center_lon - span_deg/2, center_lon + span_deg/2, grid_size)
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        return lat_grid, lon_grid

    @staticmethod
    def _extract_geojson_points(feature_collection: Dict, max_features: int = 5) -> List[Tuple[float, float, float]]:
        """Extract (lat, lon, weight) from a GeoJSON FeatureCollection."""
        if not isinstance(feature_collection, dict):
            return []
        features = feature_collection.get('features', [])
        if not isinstance(features, list) or not features:
            return []

        points: List[Tuple[float, float, float]] = []
        for feat in features[:max_features]:
            try:
                geom = feat.get('geometry', {}) if isinstance(feat, dict) else {}
                coords = geom.get('coordinates')
                if not coords or len(coords) < 2:
                    continue
                lon, lat = float(coords[0]), float(coords[1])  # GeoJSON order
                props = feat.get('properties', {}) if isinstance(feat, dict) else {}
                raw = props.get('suitability_score', props.get('score', 50))
                weight = float(raw) / 100.0 if float(raw) > 1.0 else float(raw)
                weight = max(0.1, min(weight, 1.0))
                points.append((lat, lon, weight))
            except Exception:
                continue
        return points

    def _extract_travel_scores(self, result: Dict, center_lat: float, center_lon: float) -> np.ndarray:
        """Extract travel corridor scores using real bedding/feed geometry when available."""
        logger.info("[DEBUG] _extract_travel_scores CALLED")
        try:
            grid_size = 10
            base_score = 3.0

            lat_grid, lon_grid = self._generate_score_grid(center_lat, center_lon, grid_size=grid_size, span_deg=0.04)

            bedding_fc = result.get('bedding_zones', {})
            feeding_fc = result.get('feeding_areas', {})
            bedding_pts = self._extract_geojson_points(bedding_fc, max_features=3)
            feeding_pts = self._extract_geojson_points(feeding_fc, max_features=3)

            # If we have Vermont food patches, treat the best patch as the feeding anchor
            vt_food = result.get('vermont_food_grid', {}) if isinstance(result, dict) else {}
            food_patches = vt_food.get('food_patch_locations', []) if isinstance(vt_food, dict) else []
            if food_patches and not feeding_pts:
                try:
                    best = food_patches[0]
                    feeding_pts = [(float(best['lat']), float(best['lon']), float(best.get('quality', 1.0)))][:1]
                except Exception:
                    logger.debug("Failed to use vermont_food_grid fallback patch", exc_info=True)

            # Fallback: keep previous synthetic pattern if we lack anchors
            if not bedding_pts or not feeding_pts:
                scores = np.ones((grid_size, grid_size)) * base_score
                for i in range(grid_size):
                    for j in range(grid_size):
                        corridor_score = base_score
                        if abs(i - j) < 3:
                            corridor_score += 1.5
                        if 3 <= j <= 6:
                            corridor_score += 1.0
                        if 3 <= i <= 6:
                            corridor_score += 0.8
                        if i < 2 or i > grid_size - 3 or j < 2 or j > grid_size - 3:
                            corridor_score += 0.5
                        scores[i, j] = corridor_score
                return np.clip(scores, base_score, base_score + 3.0)

            bed_lat = float(np.mean([p[0] for p in bedding_pts]))
            bed_lon = float(np.mean([p[1] for p in bedding_pts]))
            feed_lat = float(np.mean([p[0] for p in feeding_pts]))
            feed_lon = float(np.mean([p[1] for p in feeding_pts]))

            # Local projection helpers (meters) around the center latitude
            meters_per_deg_lat = 111000.0
            meters_per_deg_lon = 111000.0 * float(np.cos(np.radians(center_lat)))

            def to_xy(lat: float, lon: float) -> Tuple[float, float]:
                return ((lon - center_lon) * meters_per_deg_lon, (lat - center_lat) * meters_per_deg_lat)

            ax, ay = to_xy(bed_lat, bed_lon)
            bx, by = to_xy(feed_lat, feed_lon)
            abx, aby = (bx - ax), (by - ay)
            ab_len2 = (abx * abx + aby * aby) or 1.0

            scores = np.ones((grid_size, grid_size)) * base_score
            for i in range(grid_size):
                for j in range(grid_size):
                    px, py = to_xy(float(lat_grid[i, j]), float(lon_grid[i, j]))
                    apx, apy = (px - ax), (py - ay)

                    t = (apx * abx + apy * aby) / ab_len2
                    t_clamped = min(1.0, max(0.0, t))
                    cx = ax + t_clamped * abx
                    cy = ay + t_clamped * aby

                    dist_to_corridor = float(np.hypot(px - cx, py - cy))
                    # Influence decays with distance from the bed→feed corridor
                    influence = float(np.exp(-((dist_to_corridor / 200.0) ** 2)))

                    # Slight penalty if outside the segment bounds (still allow some value)
                    segment_bonus = 1.0 if 0.0 <= t <= 1.0 else 0.65

                    corridor_score = base_score + 3.0 * influence * segment_bonus
                    # Edge travel: small bonus near edges (kept from prior behavior)
                    if i < 2 or i > grid_size - 3 or j < 2 or j > grid_size - 3:
                        corridor_score += 0.3

                    scores[i, j] = corridor_score

            scores = np.clip(scores, base_score, base_score + 3.0)
            logger.info("   Returning travel scores (real): min=%.2f, max=%.2f, mean=%.2f", scores.min(), scores.max(), scores.mean())
            return scores
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            logger.error(f"   ERROR in _extract_travel_scores: {e}")
            return np.ones((10, 10)) * 3.0

    def _extract_bedding_scores(self, result: Dict, center_lat: float, center_lon: float) -> np.ndarray:
        """Extract bedding scores using real bedding zone geometry when available."""
        try:
            grid_size = 10
            
            # Get suitability score from bedding zones
            bedding_zones = result.get("bedding_zones", {})
            suitability_analysis = bedding_zones.get('properties', {}).get('suitability_analysis', {})
            base_score = suitability_analysis.get('overall_score', 50) / 10.0  # Convert to 0-10 scale
            
            bedding_pts = self._extract_geojson_points(bedding_zones, max_features=5)
            if not bedding_pts:
                # Fallback: preserve existing gradient behavior when no zones are available
                scores = np.ones((grid_size, grid_size)) * base_score
                for i in range(grid_size):
                    for j in range(grid_size):
                        center_i, center_j = grid_size / 2, grid_size / 2
                        dist_from_center = np.sqrt((i - center_i)**2 + (j - center_j)**2)
                        max_dist = np.sqrt(2 * (grid_size / 2)**2)
                        center_bonus = 1.0 + (0.3 * (1 - dist_from_center / max_dist))
                        if i < grid_size / 3:
                            center_bonus *= 1.2
                        scores[i, j] *= center_bonus
                return np.clip(scores, base_score * 0.7, base_score * 1.5)

            lat_grid, lon_grid = self._generate_score_grid(center_lat, center_lon, grid_size=grid_size, span_deg=0.04)
            scores = np.ones((grid_size, grid_size)) * (base_score * 0.75)

            # Real bedding influence: stronger closer to actual bedding zones
            for i in range(grid_size):
                for j in range(grid_size):
                    cell_lat = float(lat_grid[i, j])
                    cell_lon = float(lon_grid[i, j])
                    best_cell = scores[i, j]
                    for zlat, zlon, weight in bedding_pts:
                        dist_m = haversine(cell_lat, cell_lon, float(zlat), float(zlon))
                        influence = float(np.exp(-((dist_m / 250.0) ** 2)))  # ~250m decay
                        candidate = base_score * (0.75 + 0.65 * influence * float(weight))
                        if candidate > best_cell:
                            best_cell = candidate
                    scores[i, j] = best_cell

            return np.clip(scores, base_score * 0.6, base_score * 1.4)
        except (KeyError, TypeError, AttributeError):
            return np.ones((10, 10)) * 5.0

    def _extract_feeding_scores(self, result: Dict, lat: float = None, lon: float = None, season: str = 'early_season') -> np.ndarray:
        """
        Extract feeding scores from prediction results with Vermont food classification.
        
        Uses spatial food grid mapping to create precise food quality distribution
        across the prediction area based on real Vermont food sources.
        
        If lat/lon/season provided, uses Vermont food classifier for real food source analysis.
        Otherwise falls back to generic feeding area scoring.
        """
        try:
            grid_size = 10
            
            # Try to use Vermont spatial food grid if coordinates available
            if lat is not None and lon is not None:
                try:
                    from backend.vermont_food_classifier import get_vermont_food_classifier
                    
                    vt_classifier = get_vermont_food_classifier()
                    
                    # Get spatial food grid with GPS-mapped food sources
                    spatial_result = vt_classifier.create_spatial_food_grid(
                        center_lat=lat,
                        center_lon=lon,
                        season=season,
                        grid_size=grid_size,
                        span_deg=0.04,
                        radius_m=2000
                    )
                    
                    # Extract food grid (0-1 scale)
                    food_grid = spatial_result['food_grid']
                    
                    # Convert to 0-10 scale for scoring
                    scores = food_grid * 10.0
                    
                    # Log spatial food grid results
                    grid_metadata = spatial_result.get('grid_metadata', {})
                    food_patches = spatial_result.get('food_patch_locations', [])
                    
                    logger.info(f"[OSM] SPATIAL FOOD GRID: {len(food_patches)} high-quality patches identified")
                    logger.info(f"   Mean quality: {grid_metadata.get('mean_grid_quality', 0):.2f}, "
                               f"Range: {food_grid.min():.2f}-{food_grid.max():.2f}")
                    
                    # Log top food patch locations
                    if food_patches:
                        top_patch = food_patches[0]
                        logger.info(f"   [FOOD] Best food: {top_patch['lat']:.4f}, {top_patch['lon']:.4f} "
                                   f"(quality: {top_patch['quality']:.2f})")
                    
                    # Store spatial data in result for stand placement
                    result['vermont_food_grid'] = {
                        'food_grid': food_grid.tolist(),
                        'food_patch_locations': food_patches,
                        'grid_coordinates': spatial_result.get('grid_coordinates', {}),
                        'metadata': grid_metadata
                    }
                    
                    return scores
                    
                except Exception as e:
                    logger.warning(f"[WARN] Spatial food grid creation failed, using fallback: {e}")
            
            # Fallback to generic feeding area scoring
            scores = np.ones((grid_size, grid_size)) * 4.0  # Base feeding score

            feeding_fc = result.get('feeding_areas', {})
            feeding_pts = self._extract_geojson_points(feeding_fc, max_features=5)
            if feeding_pts and lat is not None and lon is not None:
                lat_grid, lon_grid = self._generate_score_grid(lat, lon, grid_size=grid_size, span_deg=0.04)
                for i in range(grid_size):
                    for j in range(grid_size):
                        cell_lat = float(lat_grid[i, j])
                        cell_lon = float(lon_grid[i, j])
                        best = 0.0
                        for flat, flon, weight in feeding_pts:
                            dist_m = haversine(cell_lat, cell_lon, float(flat), float(flon))
                            influence = float(np.exp(-((dist_m / 350.0) ** 2)))  # wider decay for feeding
                            best = max(best, influence * float(weight))
                        scores[i, j] = 4.0 + 4.0 * best
                scores = np.clip(scores, 0.0, 10.0)

            return scores
        except Exception as e:
            logger.warning(f"[WARN] Feeding score extraction failed: {e}")
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
            logger.warning(f"[WARN] Criteria analysis collection failed: {e}")
    
    def _collect_data_source_analysis(self, analyzer: PredictionAnalyzer, gee_data: Dict, 
                                    osm_data: Dict, weather_data: Dict, scouting_data: Dict) -> None:
        """Collect data source analysis"""
        try:
            analyzer.collect_data_source_analysis(gee_data, osm_data, weather_data, scouting_data)
        except Exception as e:
            logger.warning(f"[WARN] Data source analysis collection failed: {e}")
    
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
            logger.warning(f"[WARN] Algorithm analysis collection failed: {e}")
    
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
            logger.warning(f"[WARN] Scoring analysis collection failed: {e}")


# Global service instance
_prediction_service = None


def get_prediction_service() -> PredictionService:
    """Get the singleton prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service

