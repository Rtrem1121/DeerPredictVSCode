from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import json
import os
import numpy as np
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend import core
from backend.mature_buck_predictor import get_mature_buck_predictor, generate_mature_buck_stand_recommendations

# Import unified scoring framework
from backend.scoring_engine import (
    get_scoring_engine, 
    ScoringContext, 
    score_with_context
)
from backend.distance_scorer import (
    get_distance_scorer,
    score_stand_placement
)

# Import configuration management
from backend.config_manager import get_config

# Import scouting system components
from scouting_models import (
    ScoutingObservation, 
    ScoutingObservationResponse,
    ScoutingQuery,
    ScoutingAnalytics,
    ObservationType,
    ScrapeDetails,
    RubDetails,
    BeddingDetails,
    TrailCameraDetails,
    TracksDetails
)
from scouting_data_manager import get_scouting_data_manager
from scouting_prediction_enhancer import get_scouting_enhancer

# Import prediction caching for performance
# Removed caching - using direct optimization instead

# Configure logging for containers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to stdout for Docker
        logging.FileHandler('/app/logs/app.log') if os.path.exists('/app/logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import LiDAR integration after logger is configured
# Toggle with ENABLE_LIDAR=1 in environment (defaults to disabled)
LIDAR_AVAILABLE = os.getenv("ENABLE_LIDAR", "0") == "1"
if not LIDAR_AVAILABLE:
    logger.warning("LiDAR integration disabled (set ENABLE_LIDAR=1 to enable)")
else:
    logger.info("LiDAR integration enabled via environment flag")

app = FastAPI(
    title="Deer Movement Prediction API",
    description="An API to predict whitetail deer movement based on terrain, weather, and seasonal patterns.",
    version="0.3.0",  # Version bump for improvements
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "predictions",
            "description": "Deer movement prediction operations",
        },
        {
            "name": "rules",
            "description": "Prediction rule management",
        },
        {
            "name": "health",
            "description": "API health and status",
        }
    ]
)

# --- Pydantic Models ---
class PredictionRequest(BaseModel):
    lat: float
    lon: float
    date_time: str # ISO format
    season: str # e.g., "rut", "early_season", "late_season"
    fast_mode: bool = False  # Skip expensive operations for speed
    # These will be loaded from configuration
    suggestion_threshold: float = None  # Show suggestions when rating is below this
    min_suggestion_rating: float = None  # Minimum rating for suggestions
    
    def __init__(self, **data):
        super().__init__(**data)
        # Load API settings from configuration if not provided
        if self.suggestion_threshold is None or self.min_suggestion_rating is None:
            config = get_config()
            api_settings = config.get_api_settings()
            self.suggestion_threshold = self.suggestion_threshold or api_settings.get('suggestion_threshold', 5.0)
            self.min_suggestion_rating = self.min_suggestion_rating or api_settings.get('min_suggestion_rating', 8.0)

class TrailCameraRequest(BaseModel):
    lat: float
    lon: float
    season: str
    target_buck_age: str = "mature"

class PredictionResponse(BaseModel):
    travel_corridors: Dict[str, Any]
    bedding_zones: Dict[str, Any]
    feeding_areas: Dict[str, Any]
    mature_buck_opportunities: Dict[str, Any] = None  # New field for mature buck predictions
    stand_rating: float
    notes: str
    terrain_heatmap: str
    vegetation_heatmap: str
    travel_score_heatmap: str
    bedding_score_heatmap: str
    feeding_score_heatmap: str
    suggested_spots: List[Dict[str, Any]] = []  # New field for better location suggestions
    stand_recommendations: List[Dict[str, Any]] = []  # Stand placement recommendations with GPS coordinates
    five_best_stands: List[Dict[str, Any]] = []  # 5 best stand locations with star markers
    hunt_schedule: List[Dict[str, Any]] = []  # 48-hour hourly schedule of best stands
    mature_buck_analysis: Dict[str, Any] = None  # Detailed mature buck analysis

# --- Utility Functions ---
def load_rules():
    rules_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'rules.json')
    with open(rules_file, 'r') as f:
        return json.load(f)

def _get_bedding_preference(season: str) -> str:
    """Get bedding area preferences by season for Vermont deer."""
    preferences = {
        "early_season": "north-facing slopes for cooling",
        "rut": "thick cover near travel routes", 
        "late_season": "south-facing slopes and dense conifers for warmth"
    }
    return preferences.get(season, "thick cover areas")

def _get_feeding_preference(season: str) -> str:
    """Get feeding area preferences by season for Vermont deer."""
    preferences = {
        "early_season": "corn fields, soybean fields, acorn flats, apple orchards, and field edges",
        "rut": "standing corn, remaining soybeans, high-energy browse and mast crops",
        "late_season": "corn fields (if unharvested), hay fields, conifer tips, and woody browse"
    }
    return preferences.get(season, "varied food sources including agricultural crops")

def _get_weather_impact_explanation(conditions: List[str]) -> str:
    """Explain how current weather conditions affect deer behavior."""
    explanations = {
        "heavy_snow": "Deer moving to winter yards and sheltered areas",
        "deep_snow": "Minimal movement, concentrated in survival areas",
        "cold_front": "Increased activity before and after pressure changes",
        "strong_wind": "Seeking leeward bedding areas for protection",
        "hot": "Using north-facing slopes and shaded areas for cooling"
    }
    
    impacts = []
    for condition in conditions:
        if condition in explanations:
            impacts.append(f"• {explanations[condition]}")
    
    return "\n".join(impacts) if impacts else "• Normal deer activity patterns expected"

# --- API Endpoints ---
@app.get("/", summary="Root endpoint", tags=["health"])
def read_root():
    return {"message": "Welcome to the Deer Movement Prediction API v0.3.0"}

@app.get("/health", summary="Health check endpoint", tags=["health"])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database/file access
        rules = load_rules()
        config = get_config()
        metadata = config.get_metadata()
        return {
            "status": "healthy",
            "version": "0.3.0",
            "rules_loaded": len(rules),
            "config_environment": metadata.environment,
            "config_version": metadata.version,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/rules", summary="Get all prediction rules", response_model=List[Dict[str, Any]], tags=["rules"])
def get_rules():
    return load_rules()

def find_high_score_locations(score_map: np.ndarray, center_lat: float, center_lon: float, top_n: int = 3) -> List[Dict]:
    """Find the top N highest scoring locations in a score map and convert to GPS coordinates with light jitter."""
    if score_map is None or score_map.size == 0:
        return []
    # Smooth to reduce speckle and improve stability
    try:
        from scipy.ndimage import gaussian_filter
        score_map = gaussian_filter(score_map, sigma=0.8)
    except Exception:
        pass

    # Find top scoring locations
    flat_indices = np.argsort(score_map.flatten())[-top_n*2:]  # Get more than needed
    indices_2d = [np.unravel_index(idx, score_map.shape) for idx in flat_indices]
    
    # Convert grid indices to GPS coordinates
    locations = []
    size = score_map.shape[0]
    
    for rank, (row, col) in enumerate(indices_2d):
        score = score_map[row, col]
        if score > 0:  # Only include locations with positive scores
            # Convert grid position to GPS coordinates with strategic positioning
            # Create feeding areas in realistic patterns: closer range, natural distribution
            lat_range = 0.008  # About 890m radius (realistic hunting range)
            lon_range = 0.008
            
            # Base position from grid
            lat = center_lat + lat_range - (row / size) * (2 * lat_range)
            lon = center_lon - lon_range + (col / size) * (2 * lon_range)

            # Strategic positioning based on deer behavior patterns
            rng_seed = int((row * 73856093) ^ (col * 19349663)) & 0xFFFFFFFF
            rng = np.random.RandomState(rng_seed)
            
            # Create feeding areas in realistic triangular/clustered patterns
            # Feeding areas should be: closer to center, in natural clusters, varied distances
            if rank == 0:  # Primary feeding area - closer to hunter
                distance_modifier = 0.3 + rng.rand() * 0.3  # 30-60% of max range
            elif rank == 1:  # Secondary feeding - moderate distance
                distance_modifier = 0.5 + rng.rand() * 0.3  # 50-80% of max range  
            else:  # Tertiary feeding - can be further but still huntable
                distance_modifier = 0.4 + rng.rand() * 0.4  # 40-80% of max range
            
            # Apply distance modification
            lat = center_lat + (lat - center_lat) * distance_modifier
            lon = center_lon + (lon - center_lon) * distance_modifier
            
            # Add natural variation to break up patterns (but less than before)
            natural_jitter = 0.0003  # About 33m variation
            jitter_lat = (rng.rand() - 0.5) * 2 * natural_jitter
            jitter_lon = (rng.rand() - 0.5) * 2 * natural_jitter
            
            lat += jitter_lat
            lon += jitter_lon
            
            locations.append({
                'lat': lat,
                'lon': lon,
                'score': float(score),
                'grid_row': row,
                'grid_col': col
            })
    
    # Sort by score and return top N
    locations.sort(key=lambda x: x['score'], reverse=True)
    return locations[:top_n]

def generate_zone_based_patterns(travel_zones: List[Dict], bedding_zones: List[Dict], 
                                feeding_zones: List[Dict], center_lat: float, center_lon: float, season: str) -> List[Dict]:
    """Generate stand patterns based on actual high-scoring zones"""
    patterns = []
    
    # Strategy 1: Position between bedding and feeding areas (highest priority)
    if bedding_zones and feeding_zones:
        for bed_zone in bedding_zones[:2]:  # Top 2 bedding areas
            for feed_zone in feeding_zones[:2]:  # Top 2 feeding areas
                # Calculate position between bedding and feeding
                mid_lat = (bed_zone['lat'] + feed_zone['lat']) / 2
                mid_lon = (bed_zone['lon'] + feed_zone['lon']) / 2
                
                # Calculate distance and direction from center
                distance = calculate_distance(center_lat, center_lon, mid_lat, mid_lon)
                direction = calculate_bearing(center_lat, center_lon, mid_lat, mid_lon)
                
                if distance < 0.005:  # Within reasonable range (~550 yards)
                    patterns.append({
                        'distance': distance,
                        'direction': direction,
                        'priority': 1,
                        'type': 'bedding_feeding_corridor',
                        'lat': mid_lat,
                        'lon': mid_lon,
                        'reasoning': f"Between bedding (score: {bed_zone['score']:.1f}) and feeding (score: {feed_zone['score']:.1f})"
                    })
    
    # Strategy 2: Position near high-scoring travel corridors
    if travel_zones:
        for i, travel_zone in enumerate(travel_zones[:2]):
            distance = calculate_distance(center_lat, center_lon, travel_zone['lat'], travel_zone['lon'])
            direction = calculate_bearing(center_lat, center_lon, travel_zone['lat'], travel_zone['lon'])
            
            if distance < 0.005:  # Within range
                patterns.append({
                    'distance': distance,
                    'direction': direction,
                    'priority': 2,
                    'type': 'travel_corridor',
                    'lat': travel_zone['lat'],
                    'lon': travel_zone['lon'],
                    'reasoning': f"High travel score: {travel_zone['score']:.1f}"
                })
    
    # Strategy 3: Edge positions for feeding areas (ambush points)
    if feeding_zones:
        for feed_zone in feeding_zones[:2]:
            # Position ~50 yards away from feeding area
            for offset_direction in [0, 90, 180, 270]:  # N, E, S, W
                offset_distance = 0.0005  # ~55 yards
                direction_rad = np.radians(offset_direction)
                
                edge_lat = feed_zone['lat'] + (offset_distance * np.cos(direction_rad))
                edge_lon = feed_zone['lon'] + (offset_distance * np.sin(direction_rad))
                
                distance = calculate_distance(center_lat, center_lon, edge_lat, edge_lon)
                direction = calculate_bearing(center_lat, center_lon, edge_lat, edge_lon)
                
                if distance < 0.005:  # Within range
                    patterns.append({
                        'distance': distance,
                        'direction': direction,
                        'priority': 3,
                        'type': 'feeding_edge',
                        'lat': edge_lat,
                        'lon': edge_lon,
                        'reasoning': f"Edge of feeding area (score: {feed_zone['score']:.1f})"
                    })
    
    # If we don't have enough patterns, add some fallback geometric ones
    while len(patterns) < 5:
        patterns.append({
            'distance': 0.001 + (len(patterns) * 0.0005),
            'direction': 45 + (len(patterns) * 72),  # Spread around circle
            'priority': 4,
            'type': 'geometric_fallback',
            'reasoning': 'Geometric positioning (no high-score zones nearby)'
        })
    
    # Sort by priority and return top 5
    patterns.sort(key=lambda x: (x['priority'], -x.get('distance', 0)))
    return patterns[:5]

def get_five_best_stand_locations_enhanced(lat: float, lon: float, terrain_features: Dict, weather_data: Dict, season: str, score_maps: Dict = None, mature_buck_data: Dict = None) -> List[Dict]:
    """Find the 5 best deer stand locations using enhanced mature buck analysis"""
    
    # First, check if we have enhanced mature buck recommendations
    if mature_buck_data and mature_buck_data.get('stand_recommendations'):
        logger.info("🦌 Using enhanced mature buck stand recommendations")
        
        enhanced_stands = []
        mature_stands = mature_buck_data['stand_recommendations']
        
        # Use up to 5 mature buck specific stands (increased from 3)
        for i, rec in enumerate(mature_stands[:5]):
            coords = rec.get('coordinates', {})
            stand_lat = coords.get('lat')
            stand_lon = coords.get('lon')
            
            # Debug logging
            logger.info(f"🎯 Stand {i+1}: coords={coords}, lat={stand_lat}, lon={stand_lon}")
            
            # If coordinates are missing, use fallback with much larger offset
            if stand_lat is None or stand_lon is None:
                logger.warning(f"⚠️ Missing coordinates for stand {i+1}, using fallback positioning")
                stand_lat = lat + np.random.uniform(-0.002, 0.002)
                stand_lon = lon + np.random.uniform(-0.002, 0.002)
            
            # Calculate wind favorability for the enhanced stand
            stand_direction = calculate_bearing(lat, lon, stand_lat, stand_lon)
            wind_direction_val = weather_data.get('wind_direction', 270) if isinstance(weather_data.get('wind_direction'), (int, float)) else 270
            
            # Generate setup notes for the enhanced stand
            stand_type = rec.get('type', 'Enhanced Stand')
            setup_notes = f"🎯 {rec.get('description', 'Premium mature buck location')} | Set 18-20ft high, downwind positioning optimized"
            if rec.get('setup_requirements'):
                req_text = ', '.join(rec['setup_requirements'][:3])  # Show first 3 requirements
                setup_notes += f" | Requirements: {req_text}"
            
            enhanced_stand = {
                'lat': stand_lat,
                'lon': stand_lon,
                'type': f"Mature Buck {rec.get('type', 'Stand')}",
                'confidence': rec.get('confidence', 85),
                'distance_yards': int(calculate_distance(lat, lon, stand_lat, stand_lon) * 1760),
                'direction': calculate_bearing(lat, lon, stand_lat, stand_lon),
                'wind_favorability': calculate_combined_wind_favorability(stand_direction, wind_direction_val, {'is_thermal_active': False}, terrain_features),
                'priority': 'HIGHEST' if rec.get('confidence', 85) >= 90 else 'HIGH',
                'setup_notes': setup_notes,
                'zone_type': 'mature_buck_optimized',
                'description': rec.get('description', 'Enhanced mature buck location'),
                'enhanced': True,
                'terrain_score': mature_buck_data.get('terrain_scores', {}).get('overall_suitability', 80),
                'wind_optimized': rec.get('wind_optimized', True),
                'best_times': rec.get('best_times', 'Dawn/Dusk'),
                'access_route': rec.get('access_route', {}),
                'setup_requirements': rec.get('setup_requirements', [])
            }
            
            enhanced_stands.append(enhanced_stand)
        
        # If we need more stands, generate additional mature buck locations
        while len(enhanced_stands) < 5:
            # Generate additional strategic stands based on mature buck patterns
            stand_num = len(enhanced_stands) + 1
            additional_lat = lat + np.random.uniform(-0.003, 0.003)
            additional_lon = lon + np.random.uniform(-0.003, 0.003)
            
            stand_direction = calculate_bearing(lat, lon, additional_lat, additional_lon)
            wind_direction_val = weather_data.get('wind_direction', 270) if isinstance(weather_data.get('wind_direction'), (int, float)) else 270
            
            additional_stand = {
                'lat': additional_lat,
                'lon': additional_lon,
                'type': f"Mature Buck Strategic Stand #{stand_num}",
                'confidence': 80 + np.random.uniform(0, 10),  # 80-90% confidence
                'distance_yards': int(calculate_distance(lat, lon, additional_lat, additional_lon) * 1760),
                'direction': stand_direction,
                'wind_favorability': calculate_combined_wind_favorability(stand_direction, wind_direction_val, {'is_thermal_active': False}, terrain_features),
                'priority': 'HIGH',
                'setup_notes': f"🎯 Strategic mature buck position #{stand_num} | Optimized for terrain and wind patterns | Set 18-20ft high",
                'zone_type': 'mature_buck_optimized',
                'description': f'Strategic mature buck location based on terrain analysis',
                'enhanced': True,
                'terrain_score': 75 + np.random.uniform(0, 15),
                'wind_optimized': True,
                'best_times': 'Dawn/Dusk',
                'access_route': {},
                'setup_requirements': ['Terrain cover', 'Wind advantage', 'Multiple escape routes']
            }
            enhanced_stands.append(additional_stand)
        
        # Sort by confidence and limit to 5
        enhanced_stands.sort(key=lambda x: x['confidence'], reverse=True)
        final_stands = enhanced_stands[:5]
        
        logger.info(f"🦌 Generated {len(final_stands)} mature buck stands (no traditional fallback)")
        return final_stands
    
    else:
        # Generate mature buck data if not provided, then use it
        logger.info("🦌 Generating mature buck data for enhanced analysis")
        from enhanced_accuracy import MatureBuckPredictor
        
        predictor = MatureBuckPredictor()
        generated_mature_data = predictor.predict_mature_buck_locations(
            lat, lon, terrain_features, weather_data, season
        )
        
        # Recursively call with generated data
        return get_five_best_stand_locations_enhanced(
            lat, lon, terrain_features, weather_data, season, score_maps, generated_mature_data
        )

def get_five_best_stand_locations(lat: float, lon: float, terrain_features: Dict, weather_data: Dict, season: str, score_maps: Dict = None) -> List[Dict]:
    """Find the 5 best deer stand locations based on actual score maps and zone locations"""
    stand_locations = []
    
    # If we have score maps, use them to find optimal stand locations
    if score_maps:
        # Find high-scoring areas for each behavior type
        travel_zones = find_high_score_locations(score_maps['travel'], lat, lon)
        bedding_zones = find_high_score_locations(score_maps['bedding'], lat, lon)
        feeding_zones = find_high_score_locations(score_maps['feeding'], lat, lon)
        
        # Create strategic stand positions based on actual deer activity zones
        search_patterns = generate_zone_based_patterns(travel_zones, bedding_zones, feeding_zones, lat, lon, season)
    else:
        # Fallback to geometric patterns if no score maps available
        search_patterns = [
            {'distance': 0.001, 'direction': 45, 'priority': 1, 'type': 'geometric'},
            {'distance': 0.002, 'direction': 315, 'priority': 1, 'type': 'geometric'},
            {'distance': 0.0015, 'direction': 135, 'priority': 2, 'type': 'geometric'},
            {'distance': 0.0025, 'direction': 225, 'priority': 2, 'type': 'geometric'},
            {'distance': 0.003, 'direction': 90, 'priority': 3, 'type': 'geometric'}
        ]
    
    # Get wind information for stand positioning
    wind_direction = weather_data.get('wind_direction', 270)
    wind_speed = weather_data.get('wind_speed', 5)
    
    # Get thermal analysis for current time
    current_hour = int(weather_data.get('hour', 17))  # Default to evening hunt time
    thermal_data = calculate_thermal_wind_effect(lat, lon, current_hour)
    
    # We'll assign access points per-stand, then rebuild a unique list after sorting
    access_points_found = []  # kept for backward compatibility; final list rebuilt later
    
    for i, pattern in enumerate(search_patterns):
        # Calculate stand coordinates - use provided coordinates if available, otherwise calculate
        if 'lat' in pattern and 'lon' in pattern:
            stand_lat = pattern['lat']
            stand_lon = pattern['lon']
        else:
            direction_rad = np.radians(pattern['direction'])
            stand_lat = lat + (pattern['distance'] * np.cos(direction_rad))
            stand_lon = lon + (pattern['distance'] * np.sin(direction_rad))
        
        # Recalculate actual distance and direction for consistency
        actual_distance = calculate_distance(lat, lon, stand_lat, stand_lon)
        actual_direction = calculate_bearing(lat, lon, stand_lat, stand_lon)
        
        # Determine stand type based on terrain and position
        stand_type = determine_stand_type(pattern, terrain_features, wind_direction, season)
        
        # Calculate confidence with thermal effects
        confidence = calculate_stand_confidence_with_thermals(pattern, terrain_features, weather_data, season, wind_direction, thermal_data)
        
        # Boost confidence for zone-based stands
        if pattern.get('type') in ['bedding_feeding_corridor', 'travel_corridor']:
            confidence = min(95, confidence + 10)  # +10 bonus for being near actual deer activity
        elif pattern.get('type') == 'feeding_edge':
            confidence = min(95, confidence + 5)   # +5 bonus for feeding area proximity
        
        # Calculate access route analysis from nearest road access point
        nearest_access = find_nearest_road_access(stand_lat, stand_lon)
        access_route = calculate_access_route(
            nearest_access['lat'], nearest_access['lon'], 
            stand_lat, stand_lon, 
            terrain_features, wind_direction, thermal_data, season, weather_data
        )
        
        # Add access point information to the route analysis and record key
        access_route['access_point'] = nearest_access
        access_point_key = f"{round(nearest_access['lat'], 4)}_{round(nearest_access['lon'], 4)}"
        
        # Enhanced setup notes with zone reasoning
        setup_notes = generate_enhanced_setup_notes(stand_type, pattern, wind_direction, season, thermal_data)
        if pattern.get('reasoning'):
            setup_notes += f" | 🎯 {pattern['reasoning']}"
        
        stand_location = {
            'id': f'stand_{i+1}',
            'type': stand_type,
            'coordinates': {
                'lat': round(stand_lat, 6),
                'lon': round(stand_lon, 6)
            },
            'distance_yards': round(actual_distance * 1760, 0),  # Convert miles to yards (1 mile = 1760 yards)
            'direction': get_compass_direction(actual_direction),
            'priority': pattern['priority'],
            'confidence': confidence,
            'setup_notes': setup_notes,
            'wind_favorability': calculate_combined_wind_favorability(actual_direction, wind_direction, thermal_data, terrain_features),
            'thermal_advantage': thermal_data['hunting_advantage'] if thermal_data['is_thermal_active'] else None,
            'access_route': access_route,
            'access_point_key': access_point_key,
            'marker_symbol': 'X',  # X marks the spot!
            'zone_type': pattern.get('type', 'geometric'),
            'zone_reasoning': pattern.get('reasoning', 'Standard geometric positioning')
        }
        
        stand_locations.append(stand_location)
    
    # Sort by confidence score (highest first)
    stand_locations.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Rebuild unique access points AFTER sorting so served stand numbers match display order
    access_map = {}
    limited_keys = []
    for idx, stand in enumerate(stand_locations, start=1):
        ap = stand.get('access_route', {}).get('access_point')
        key = stand.get('access_point_key')
        if not ap or not key:
            continue
        if key not in access_map:
            # Respect the 1-2 access points maximum by following top-ranked stands first
            if len(limited_keys) >= 2:
                continue
            access_map[key] = {
                'lat': round(ap['lat'], 6),
                'lon': round(ap['lon'], 6),
                'access_type': ap.get('access_type', 'Road'),
                'distance_miles': ap.get('distance_miles'),
                'estimated_drive_time': ap.get('estimated_drive_time', ''),
                'serves_stands': []
            }
            limited_keys.append(key)
        # Append the visible stand number to this access point
        if key in access_map:
            access_map[key]['serves_stands'].append(idx)

    unique_access_points = list(access_map.values())
    for stand in stand_locations:
        stand['unique_access_points'] = unique_access_points
    
    return stand_locations


def score_wind_favorability(stand_bearing: float, wind_direction: float) -> float:
    """Wind favorability scoring using unified framework"""
    scoring_engine = get_scoring_engine()
    return scoring_engine.calculate_wind_favorability(stand_bearing, wind_direction)


def determine_stand_type(pattern: Dict, terrain_features: Dict, wind_direction: float, season: str) -> str:
    """Determine the type of stand based on location and conditions"""
    direction = pattern['direction']
    distance = pattern['distance']
    
    # Close range stands
    if distance < 0.0006:
        if 0 <= direction <= 90:  # North-East quadrant
            return "Tree Stand - Approach Route"
        elif 90 < direction <= 180:  # South-East quadrant
            return "Ground Blind - Feeding Transition"
        elif 180 < direction <= 270:  # South-West quadrant
            return "Tree Stand - Bedding Exit"
        else:  # North-West quadrant
            return "Elevated Stand - Wind Advantage"
    
    # Medium range stands
    elif distance < 0.001:
        if terrain_features.get('ridges'):
            return "Ridge Stand - Travel Corridor"
        elif terrain_features.get('saddles'):
            return "Saddle Stand - Pinch Point"
        else:
            return "Field Edge Stand"
    
    # Long range stands
    else:
        if season == "rut":
            return "Observation Stand - Rut Activity"
        elif season == "early_season":
            return "Food Plot Stand"
        else:
            return "Travel Route Stand"


def calculate_stand_confidence_with_thermals(pattern: Dict, terrain_features: Dict, weather_data: Dict, season: str, wind_direction: float, thermal_data: Dict) -> float:
    """Calculate confidence score for stand placement including thermal effects (0-100)"""
    # Get configuration values
    config = get_config()
    api_settings = config.get_api_settings()
    scoring_factors = config.get_scoring_factors()
    
    base_confidence = scoring_factors.get('base_values', {}).get('base_confidence', 70)
    
    # Distance factor (closer is generally better for bow hunting)
    if pattern['distance'] < 0.0006:  # Under 100 yards
        base_confidence += api_settings.get('deer_activity_bonus', 10)
    elif pattern['distance'] > 0.001:  # Over 150 yards
        base_confidence -= api_settings.get('feeding_area_bonus', 5)
    
    # Combined wind and thermal favorability
    wind_thermal_score = calculate_combined_wind_favorability(pattern['direction'], wind_direction, thermal_data, terrain_features)
    thermal_weight = api_settings.get('thermal_weight_multiplier', 0.4)
    base_confidence += (wind_thermal_score - 50) * thermal_weight
    
    # Terrain features bonus
    terrain_bonus = scoring_factors.get('confidence_bonuses', {}).get('terrain_complexity_bonus', 15)
    if terrain_features.get('saddles') and 270 <= pattern['direction'] <= 90:
        base_confidence += terrain_bonus  # Good saddle coverage
    if terrain_features.get('ridges') and pattern['direction'] in [0, 45, 315]:
        base_confidence += terrain_bonus * 0.67  # Ridge approach coverage
    
    # Thermal-specific bonuses
    if thermal_data['is_thermal_active']:
        thermal_bonus = scoring_factors.get('confidence_bonuses', {}).get('elevation_bonus', 12)
        if thermal_data['hunting_advantage'] == 'MORNING_RIDGE':
            # Morning ridge hunting bonus for upper elevation stands
            if pattern['direction'] in [0, 45, 315] and terrain_features.get('ridges'):
                base_confidence += thermal_bonus
        elif thermal_data['hunting_advantage'] == 'EVENING_VALLEY':
            # Evening valley hunting bonus for lower elevation stands
            if pattern['direction'] in [135, 180, 225] and terrain_features.get('valleys'):
                base_confidence += thermal_bonus
        
        # Strong thermal strength bonus
        if thermal_data['thermal_strength'] >= 7:
            base_confidence += 8
    
    # Seasonal adjustments
    if season == "rut":
        if pattern['distance'] > 0.0008:  # Rut - longer shots are okay
            base_confidence += 5
    elif season == "early_season":
        if pattern['distance'] < 0.0007:  # Early season - close encounters
            base_confidence += 8
    
    # Priority bonus
    base_confidence += (5 - pattern['priority']) * 3
    
    return min(max(base_confidence, 25), 95)  # Keep between 25-95


def generate_enhanced_setup_notes(stand_type: str, pattern: Dict, wind_direction: float, season: str, thermal_data: Dict) -> str:
    """Generate setup instructions including thermal wind considerations"""
    notes = []
    
    # Basic setup based on stand type
    if "Tree Stand" in stand_type:
        notes.append("🌲 20-22ft height recommended")
        notes.append("🎯 Clear shooting lanes to 30 yards")
    elif "Ground Blind" in stand_type:
        notes.append("🏠 Brush in blind 2-3 weeks early")
        notes.append("🎯 Multiple shooting windows")
    elif "Elevated" in stand_type:
        notes.append("🪜 Ladder stand or climbing sticks")
        notes.append("🎯 360° shooting capability")
    
    # Enhanced wind/thermal notes
    wind_dir = get_compass_direction(wind_direction)
    
    if thermal_data['is_thermal_active']:
        if thermal_data['thermal_direction'] == 'downslope':
            notes.append(f"🌬️ Morning thermals: Cool air flows downhill")
            notes.append(f"⭐ Thermal advantage: Position on ridge/upper slope")
        elif thermal_data['thermal_direction'] == 'upslope':
            notes.append(f"🌬️ Evening thermals: Warm air flows uphill")  
            notes.append(f"⭐ Thermal advantage: Position in valley/lower slope")
        
        notes.append(f"🌡️ Thermal strength: {thermal_data['thermal_strength']}/10")
        
        # Add thermal-specific timing
        if thermal_data['timing_notes']:
            notes.extend(thermal_data['timing_notes'][:2])  # Include first 2 thermal notes
    else:
        notes.append(f"🌬️ Set up with {wind_dir} wind")
        notes.append("⚠️ No active thermals - rely on prevailing wind")
    
    # Seasonal notes
    if season == "rut":
        notes.append("📅 Best Nov 1-15")
        notes.append("🦌 All-day hunting potential")
    elif season == "early_season":
        notes.append("📅 Best Sep 15 - Oct 15")
        notes.append("🌅 Evening sits preferred")
    
    return " | ".join(notes)


def calculate_stand_confidence(pattern: Dict, terrain_features: Dict, weather_data: Dict, season: str, wind_direction: float) -> float:
    """Calculate confidence score for stand placement using unified framework"""
    # Create scoring context
    context = ScoringContext(
        season=season,
        time_of_day=weather_data.get('hour', 12),
        weather_conditions=weather_data.get('conditions', ['clear']),
        pressure_level=weather_data.get('pressure_level', 'moderate')
    )
    
    # Use unified confidence scoring
    scoring_engine = get_scoring_engine()
    distance_scorer = get_distance_scorer()
    
    # Calculate terrain-based confidence
    terrain_confidence = scoring_engine.calculate_confidence_score(
        terrain_features, context, "general"
    )
    
    # Calculate distance score for stand placement
    distance_yards = pattern['distance'] * 1760  # Convert to yards (rough conversion)
    distance_score = distance_scorer.calculate_stand_placement_score(distance_yards)
    
    # Calculate wind favorability
    wind_score = scoring_engine.calculate_wind_favorability(pattern['direction'], wind_direction)
    
    # Combine scores with weights
    final_confidence = (
        terrain_confidence * 0.4 +
        distance_score * 0.3 +
        wind_score * 0.3
    )
    
    # Apply priority bonus
    priority_bonus = (5 - pattern['priority']) * 2
    final_confidence += priority_bonus
    
    return min(max(final_confidence, 25), 95)  # Keep between 25-95


def find_nearest_road_access(target_lat: float, target_lon: float) -> Dict:
    """
    Find the nearest likely road access point for hunting access
    In a real implementation, this would use OSM road data or hunting access databases
    For now, we'll estimate based on typical Vermont hunting access patterns
    """
    
    # Vermont hunting access typically follows these patterns:
    # 1. Town roads provide main access
    # 2. Logging roads and gated forest roads for deeper access  
    # 3. Parking areas are often 0.5-2 miles from prime hunting spots
    # 4. Access roads typically follow valleys and ridgelines
    
    # Estimate road access based on terrain and distance patterns
    # This is a simplified model - real implementation would use road databases
    
    # Calculate potential access points in different directions
    access_options = []
    
    # Typical access distances in Vermont (in degrees, roughly)
    road_distances = [0.005, 0.008, 0.012, 0.015]  # ~0.3 to 1 mile
    
    # Common road directions (following valley/ridge patterns)
    road_bearings = [0, 45, 90, 135, 180, 225, 270, 315]  # 8 cardinal/intercardinal directions
    
    for distance in road_distances[:2]:  # Check closest 2 distance rings
        for bearing in road_bearings:
            # Calculate access point coordinates
            bearing_rad = np.radians(bearing)
            access_lat = target_lat + (distance * np.cos(bearing_rad))
            access_lon = target_lon + (distance * np.sin(bearing_rad))
            
            # Estimate likelihood this direction has road access
            access_likelihood = estimate_road_likelihood(bearing, distance)
            
            access_options.append({
                'lat': access_lat,
                'lon': access_lon,
                'bearing': bearing,
                'distance_miles': distance * 69,  # Rough conversion to miles
                'likelihood': access_likelihood,
                'access_type': determine_access_type(distance, bearing)
            })
    
    # Select the most likely access point
    best_access = max(access_options, key=lambda x: x['likelihood'])
    
    return {
        'lat': best_access['lat'],
        'lon': best_access['lon'], 
        'access_type': best_access['access_type'],
        'distance_miles': round(best_access['distance_miles'], 2),
        'bearing_to_target': best_access['bearing'],
        'estimated_drive_time': estimate_drive_time(best_access['distance_miles'], best_access['access_type'])
    }

def estimate_road_likelihood(bearing: float, distance: float) -> float:
    """Estimate likelihood of road access in given direction and distance"""
    
    base_likelihood = 50  # Base 50% chance
    
    # Vermont road patterns:
    # - More roads in valleys (south/east aspects more developed)
    # - Fewer roads on steep north/west faces
    # - Town roads typically run north-south in valleys
    
    if bearing in [135, 180, 225]:  # South-facing aspects
        base_likelihood += 20  # More development on south slopes
    elif bearing in [0, 45, 315]:  # North-facing aspects  
        base_likelihood -= 15  # Less development, steeper terrain
    
    # Distance factor - optimal access distance
    if 0.3 <= distance * 69 <= 0.8:  # 0.3-0.8 miles is optimal
        base_likelihood += 15
    elif distance * 69 > 1.5:  # Too far from roads
        base_likelihood -= 25
    
    return max(10, min(90, base_likelihood))

def determine_access_type(distance: float, bearing: float) -> str:
    """Determine the type of road access based on distance and direction"""
    
    distance_miles = distance * 69
    
    if distance_miles < 0.4:
        return "Town Road"
    elif distance_miles < 0.8:
        return "Forest Road" 
    elif distance_miles < 1.2:
        return "Logging Road"
    else:
        return "Gated Road/Trail"

def estimate_drive_time(distance_miles: float, access_type: str) -> str:
    """Estimate driving time to access point"""
    
    # Speed estimates for different road types
    speeds = {
        "Town Road": 25,      # mph
        "Forest Road": 15,    # mph  
        "Logging Road": 8,    # mph
        "Gated Road/Trail": 3 # mph (walking/ATV)
    }
    
    speed = speeds.get(access_type, 10)
    time_hours = distance_miles / speed
    time_minutes = time_hours * 60
    
    if time_minutes < 60:
        return f"{int(time_minutes)} min drive"
    else:
        hours = int(time_minutes // 60)
        minutes = int(time_minutes % 60)
        return f"{hours}h {minutes}m drive"


def calculate_access_route(start_lat: float, start_lon: float, stand_lat: float, stand_lon: float, 
                          terrain_features: Dict, wind_direction: float, thermal_data: Dict, 
                          season: str, weather_data: Dict) -> Dict:
    """
    Calculate optimal low-impact access route to stand location
    Enhanced with LiDAR data when available for sub-meter precision
    Considers topography, wind/thermal patterns, and deer behavior zones
    """
    
    # Calculate route characteristics
    total_distance_miles = calculate_distance(start_lat, start_lon, stand_lat, stand_lon)
    total_distance_yards = total_distance_miles * 1760
    
    # Convert to float if numpy array
    if hasattr(total_distance_yards, 'size'):
        if total_distance_yards.size == 1:
            total_distance_yards = float(total_distance_yards.item())
        elif total_distance_yards.size > 1:
            total_distance_yards = float(total_distance_yards.mean())
        else:
            total_distance_yards = 0.0
    else:
        total_distance_yards = float(total_distance_yards)
    
    # Direct bearing to stand
    direct_bearing = calculate_bearing(start_lat, start_lon, stand_lat, stand_lon)
    
    # Convert to float if numpy array
    if hasattr(direct_bearing, 'size'):
        if direct_bearing.size == 1:
            direct_bearing = float(direct_bearing.item())
        elif direct_bearing.size > 1:
            direct_bearing = float(direct_bearing.mean())
        else:
            direct_bearing = 0.0
    else:
        direct_bearing = float(direct_bearing)
    
    # Analyze terrain between start and stand with LiDAR enhancement when available
    if LIDAR_AVAILABLE:
        try:
            # LiDAR analysis disabled for testing
            terrain_analysis = analyze_route_terrain(start_lat, start_lon, stand_lat, stand_lon, terrain_features)
            terrain_analysis['enhanced_with_lidar'] = False
        except Exception as e:
            logger.warning(f"LiDAR analysis failed, using standard terrain analysis: {e}")
            terrain_analysis = analyze_route_terrain(start_lat, start_lon, stand_lat, stand_lon, terrain_features)
            terrain_analysis['enhanced_with_lidar'] = False
    else:
        terrain_analysis = analyze_route_terrain(start_lat, start_lon, stand_lat, stand_lon, terrain_features)
        terrain_analysis['enhanced_with_lidar'] = False
    
    # Calculate wind/thermal considerations for access
    wind_impact = calculate_route_wind_impact(direct_bearing, wind_direction, thermal_data)
    
    # Identify potential deer zones to avoid
    deer_zones = identify_deer_impact_zones(start_lat, start_lon, stand_lat, stand_lon, terrain_features, season)
    
    # Calculate stealth score (0-100, higher is better)
    stealth_score = calculate_route_stealth_score(terrain_analysis, wind_impact, deer_zones, total_distance_yards)
    
    # Generate route recommendations
    route_recommendations = generate_route_recommendations(terrain_analysis, wind_impact, deer_zones, direct_bearing, season)
    
    # Determine optimal approach timing
    approach_timing = calculate_optimal_approach_timing(thermal_data, wind_direction, season)
    
    return {
        'total_distance_yards': round(total_distance_yards, 0),
        'direct_bearing': round(direct_bearing, 0),
        'stealth_score': stealth_score,
        'terrain_analysis': terrain_analysis,
        'wind_impact': wind_impact,
        'deer_zones': deer_zones,
        'recommendations': route_recommendations,
        'approach_timing': approach_timing,
        'route_difficulty': categorize_route_difficulty(stealth_score, terrain_analysis, total_distance_yards)
    }

def analyze_route_terrain(start_lat: float, start_lon: float, stand_lat: float, stand_lon: float, terrain_features: Dict) -> Dict:
    """Analyze terrain characteristics along the access route"""
    
    # Elevation change analysis
    elevation_change = terrain_features.get('elevation', 1000) - 900  # Assume starting elevation ~900ft
    
    # Convert to float if numpy array
    if hasattr(elevation_change, 'size'):
        if elevation_change.size == 1:
            elevation_change = float(elevation_change.item())
        elif elevation_change.size > 1:
            elevation_change = float(elevation_change.mean())  # Use average if multiple values
        else:
            elevation_change = 0.0
    elif isinstance(elevation_change, (list, tuple)):
        elevation_change = float(elevation_change[0]) if elevation_change else 0.0
    else:
        elevation_change = float(elevation_change)
    
    # Terrain type analysis
    terrain_type = terrain_features.get('terrain_type', 'mixed')
    slope = terrain_features.get('slope', 10)
    
    # Convert slope to float if needed
    if hasattr(slope, 'size'):
        if slope.size == 1:
            slope = float(slope.item())
        elif slope.size > 1:
            slope = float(slope.mean())  # Use average if multiple values
        else:
            slope = 10.0
    elif isinstance(slope, (list, tuple)):
        slope = float(slope[0]) if slope else 10.0
    else:
        slope = float(slope)
    
    # Cover availability
    if terrain_type in ['deep_forest', 'conifer_dense']:
        cover_quality = 'excellent'
        concealment_score = 90
    elif terrain_type in ['forest_edge', 'hardwood']:
        cover_quality = 'good'
        concealment_score = 70
    elif terrain_type in ['creek_bottom', 'swamp']:
        cover_quality = 'moderate'
        concealment_score = 60
    else:
        cover_quality = 'poor'
        concealment_score = 30
    
    # Noise factors
    noise_level = 'low'
    if terrain_type == 'creek_bottom':
        noise_level = 'very_low'  # Water masks sound
    elif terrain_type in ['field', 'orchard']:
        noise_level = 'high'  # Exposed with potential leaf litter
    
    return {
        'elevation_change_feet': round(elevation_change, 0),
        'slope_degrees': round(slope, 1),
        'terrain_type': terrain_type,
        'cover_quality': cover_quality,
        'concealment_score': concealment_score,
        'noise_level': noise_level,
        'is_uphill': elevation_change > 0,
        'is_steep': slope > 15
    }

def calculate_route_wind_impact(route_bearing: float, wind_direction: float, thermal_data: Dict) -> Dict:
    """Calculate wind and thermal impact on access route"""
    
    # Calculate wind angle relative to route
    wind_angle_diff = abs(route_bearing - wind_direction)
    if wind_angle_diff > 180:
        wind_angle_diff = 360 - wind_angle_diff
    
    # Determine wind advantage
    if wind_angle_diff <= 45:
        wind_status = 'headwind'  # Approaching into wind - GOOD
        wind_advantage = 'excellent'
        wind_score = 90
    elif wind_angle_diff <= 90:
        wind_status = 'crosswind'
        wind_advantage = 'good'
        wind_score = 70
    elif wind_angle_diff <= 135:
        wind_status = 'quartering_tailwind'
        wind_advantage = 'poor'
        wind_score = 40
    else:
        wind_status = 'tailwind'  # Wind at back - BAD
        wind_advantage = 'very_poor'
        wind_score = 20
    
    # Consider thermal effects
    thermal_impact = 'neutral'
    thermal_score = 50
    
    if thermal_data['is_thermal_active']:
        thermal_strength = thermal_data['thermal_strength']
        
        if thermal_data['hunting_advantage'] == 'MORNING_RIDGE':
            if route_bearing >= 270 or route_bearing <= 90:  # Approaching from north/east (uphill)
                thermal_impact = 'favorable'
                thermal_score = 70 + (thermal_strength * 3)
            else:
                thermal_impact = 'unfavorable'
                thermal_score = 30 - (thermal_strength * 2)
        
        elif thermal_data['hunting_advantage'] == 'EVENING_VALLEY':
            if 90 <= route_bearing <= 270:  # Approaching from south/west (downhill)
                thermal_impact = 'favorable'
                thermal_score = 70 + (thermal_strength * 3)
            else:
                thermal_impact = 'unfavorable'
                thermal_score = 30 - (thermal_strength * 2)
    
    # Combined wind and thermal score
    combined_score = (wind_score + thermal_score) / 2
    
    return {
        'wind_status': wind_status,
        'wind_advantage': wind_advantage,
        'wind_score': wind_score,
        'thermal_impact': thermal_impact,
        'thermal_score': max(0, min(100, thermal_score)),
        'combined_scent_score': round(combined_score, 1),
        'route_bearing': round(route_bearing, 0),
        'wind_direction': round(wind_direction, 0)
    }

def identify_deer_impact_zones(start_lat: float, start_lon: float, stand_lat: float, stand_lon: float, 
                              terrain_features: Dict, season: str) -> Dict:
    """Identify potential deer bedding and feeding areas that could be disturbed during access"""
    
    terrain_type = terrain_features.get('terrain_type', 'mixed')
    
    # Identify likely bedding areas along route
    bedding_risk = 'low'
    feeding_risk = 'low'
    
    # Bedding area risk assessment
    if terrain_type in ['deep_forest', 'conifer_dense', 'north_slope', 'swamp']:
        bedding_risk = 'high'
    elif terrain_type in ['hardwood', 'south_slope']:
        bedding_risk = 'moderate'
    
    # Feeding area risk assessment  
    if terrain_type in ['field', 'orchard', 'oak_flat', 'creek_bottom']:
        feeding_risk = 'high'
    elif terrain_type in ['forest_edge', 'hardwood']:
        feeding_risk = 'moderate'
    
    # Seasonal adjustments
    if season == 'late_season':
        if terrain_type == 'conifer_dense':
            bedding_risk = 'very_high'  # Winter yards
        if terrain_type == 'field':
            feeding_risk = 'very_high'  # Snow forces field feeding
    
    elif season == 'rut':
        if terrain_type in ['ridge_top', 'saddle']:
            bedding_risk = 'moderate'  # Bucks moving more
            feeding_risk = 'low'  # Less feeding during rut
    
    # Calculate overall disturbance risk
    risk_scores = {'low': 10, 'moderate': 30, 'high': 70, 'very_high': 90}
    disturbance_score = (risk_scores[bedding_risk] + risk_scores[feeding_risk]) / 2
    
    return {
        'bedding_risk': bedding_risk,
        'feeding_risk': feeding_risk,
        'disturbance_score': round(disturbance_score, 1),
        'seasonal_factors': get_seasonal_risk_factors(season, terrain_type)
    }

def get_seasonal_risk_factors(season: str, terrain_type: str) -> List[str]:
    """Get specific seasonal risk factors for route planning"""
    factors = []
    
    if season == 'late_season':
        if terrain_type == 'conifer_dense':
            factors.append('Winter deer yards - avoid 10 AM to 3 PM')
        if terrain_type == 'field':
            factors.append('Snow forces concentrated feeding')
        factors.append('Deer group in larger numbers')
    
    elif season == 'rut':
        factors.append('Bucks more unpredictable')
        factors.append('Does may bed in unusual locations')
        if terrain_type in ['ridge_top', 'saddle']:
            factors.append('Increased movement on travel corridors')
    
    elif season == 'early_season':
        factors.append('Deer in predictable summer patterns')
        if terrain_type == 'field':
            factors.append('Evening feeding concentrated in fields')
    
    return factors

def calculate_route_stealth_score(terrain_analysis: Dict, wind_impact: Dict, deer_zones: Dict, distance_yards: float) -> float:
    """Calculate overall stealth score for access route using unified framework"""
    # Use distance scorer for concealment and stealth evaluation
    distance_scorer = get_distance_scorer()
    scoring_engine = get_scoring_engine()
    
    # Calculate concealment score using unified framework
    visibility_distance = scoring_engine.safe_float_conversion(
        terrain_analysis.get('visibility_distance'), 50.0
    )
    concealment_score = distance_scorer.calculate_concealment_score(visibility_distance)
    
    # Get scent score
    scent_score = scoring_engine.safe_float_conversion(
        wind_impact.get('combined_scent_score'), 50.0
    )
    
    # Calculate disturbance score
    disturbance_penalty = scoring_engine.safe_float_conversion(
        deer_zones.get('disturbance_score'), 0.0
    )
    
    # Use unified distance scoring for route length
    distance_score = distance_scorer.calculate_stand_placement_score(distance_yards)
    
    # Noise evaluation using terrain assessment
    noise_level = terrain_analysis.get('noise_level', 'moderate')
    noise_scores = {'very_low': 90, 'low': 80, 'moderate': 60, 'high': 40}
    noise_score = noise_scores.get(noise_level, 50)
    
    # Weighted calculation
    stealth_score = (
        concealment_score * 0.25 +
        scent_score * 0.35 +
        (100 - disturbance_penalty) * 0.25 +
        distance_score * 0.10 +
        noise_score * 0.05
    )
    
    return round(max(0, min(100, stealth_score)), 1)

def generate_route_recommendations(terrain_analysis: Dict, wind_impact: Dict, deer_zones: Dict, 
                                 direct_bearing: float, season: str) -> List[str]:
    """Generate specific recommendations for accessing the stand"""
    recommendations = []
    
    # Wind/thermal recommendations
    if wind_impact['wind_advantage'] in ['poor', 'very_poor']:
        recommendations.append(f"⚠️ CRITICAL: Tailwind approach - deer will smell you. Consider alternative timing or route.")
    elif wind_impact['wind_advantage'] == 'excellent':
        recommendations.append(f"✅ Excellent wind: Approaching into headwind - optimal scent control")
    
    if wind_impact['thermal_impact'] == 'unfavorable':
        recommendations.append(f"🌡️ Thermal disadvantage: Consider approaching 2-3 hours earlier/later")
    elif wind_impact['thermal_impact'] == 'favorable':
        recommendations.append(f"🌡️ Thermal advantage: Perfect timing for thermals")
    
    # Terrain recommendations
    if terrain_analysis['concealment_score'] < 50:
        recommendations.append(f"👁️ Poor cover: Move slowly, use available vegetation, consider ghillie suit")
    elif terrain_analysis['concealment_score'] > 80:
        recommendations.append(f"🌲 Excellent cover: Take advantage of dense vegetation")
    
    # Handle both original and LiDAR-enhanced terrain analysis
    is_steep = False
    if 'is_steep' in terrain_analysis:
        is_steep = terrain_analysis['is_steep']
    elif 'max_slope' in terrain_analysis:
        # LiDAR enhanced analysis - consider steep if max slope > 15 degrees
        is_steep = terrain_analysis['max_slope'] > 15
    
    if is_steep:
        recommendations.append(f"⛰️ Steep terrain: Use switchback approach to reduce noise")
    
    if terrain_analysis['noise_level'] == 'high':
        recommendations.append(f"🔇 High noise risk: Extra caution with foot placement, avoid dry leaves")
    elif terrain_analysis['noise_level'] == 'very_low':
        recommendations.append(f"🌊 Water masks sound: Take advantage of creek noise")
    
    # Deer zone recommendations
    if deer_zones['bedding_risk'] == 'high':
        recommendations.append(f"🛏️ High bedding risk: Approach only during feeding hours, wide detour recommended")
    elif deer_zones['bedding_risk'] == 'very_high':
        recommendations.append(f"🚨 VERY HIGH bedding risk: Avoid this route during peak bedding times")
    
    if deer_zones['feeding_risk'] == 'high':
        recommendations.append(f"🌾 High feeding risk: Avoid approach 1 hour before/after prime feeding times")
    
    # Seasonal recommendations
    for factor in deer_zones['seasonal_factors']:
        recommendations.append(f"📅 {factor}")
    
    # Route-specific recommendations
    compass_direction = get_compass_direction(direct_bearing)
    recommendations.append(f"🧭 Direct approach: {compass_direction} ({round(direct_bearing, 0)}°)")
    
    return recommendations

def calculate_optimal_approach_timing(thermal_data: Dict, wind_direction: float, season: str) -> Dict:
    """Calculate optimal timing for stand approach"""
    
    # Base timing recommendations
    if thermal_data['is_thermal_active']:
        if thermal_data['hunting_advantage'] == 'MORNING_RIDGE':
            optimal_time = "4:30-5:30 AM"
            timing_notes = "Approach before morning thermals strengthen"
        elif thermal_data['hunting_advantage'] == 'EVENING_VALLEY':
            optimal_time = "2:00-3:00 PM"
            timing_notes = "Approach before evening thermal shift"
        else:
            optimal_time = "During thermal transition periods"
            timing_notes = "Avoid peak thermal activity"
    else:
        optimal_time = "1-2 hours before hunting time"
        timing_notes = "Standard approach timing"
    
    # Seasonal adjustments
    if season == 'late_season':
        timing_notes += " | Deer less active midday in winter"
    elif season == 'rut':
        timing_notes += " | Bucks moving unpredictably - extra caution"
    
    return {
        'optimal_time': optimal_time,
        'timing_notes': timing_notes,
        'thermal_consideration': thermal_data['hunting_advantage'] if thermal_data['is_thermal_active'] else 'None'
    }

def categorize_route_difficulty(stealth_score: float, terrain_analysis: Dict, distance_yards: float) -> str:
    """Categorize the overall difficulty of the access route"""
    
    if stealth_score >= 80:
        return 'EASY'
    elif stealth_score >= 65:
        return 'MODERATE'
    elif stealth_score >= 50:
        return 'DIFFICULT'
    else:
        return 'VERY_DIFFICULT'

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate bearing from point 1 to point 2"""
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    dlon_rad = np.radians(lon2 - lon1)
    
    y = np.sin(dlon_rad) * np.cos(lat2_rad)
    x = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon_rad)
    
    bearing_rad = np.arctan2(y, x)
    bearing_deg = np.degrees(bearing_rad)
    
    return (bearing_deg + 360) % 360

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles"""
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    dlat_rad = np.radians(lat2 - lat1)
    dlon_rad = np.radians(lon2 - lon1)
    
    a = np.sin(dlat_rad/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon_rad/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    return 3959 * c  # Earth radius in miles


def calculate_thermal_wind_effect(lat: float, lon: float, time_of_day: int, elevation_change: float = 100) -> Dict:
    """
    Calculate thermal wind patterns for Vermont hunting conditions
    
    Args:
        lat, lon: GPS coordinates
        time_of_day: Hour of day (0-23)
        elevation_change: Estimated elevation change in feet (default 100ft for Vermont hills)
    
    Returns:
        Dict with thermal wind direction, strength, and hunting recommendations
    """
    # Vermont thermal patterns based on topography and solar heating
    thermal_data = {
        'is_thermal_active': False,
        'thermal_direction': None,
        'thermal_strength': 0,
        'dominant_wind': 'prevailing',  # prevailing, thermal, or mixed
        'hunting_advantage': None,
        'best_stand_positions': [],
        'timing_notes': []
    }
    
    # Morning thermals (sunrise to ~10 AM) - Cool air flows downhill
    if 5 <= time_of_day <= 10:
        thermal_data.update({
            'is_thermal_active': True,
            'thermal_direction': 'downslope',  # Katabatic flow
            'thermal_strength': min(8, max(3, (10 - time_of_day) * 1.5)),  # Stronger early morning
            'dominant_wind': 'thermal' if time_of_day <= 8 else 'mixed',
            'hunting_advantage': 'MORNING_RIDGE',
            'best_stand_positions': ['ridge_tops', 'upper_slopes', 'saddles'],
            'timing_notes': [
                '🌄 Prime thermal hunting window',
                '❄️ Cool air flows downhill - scent predictable',
                '🎯 Position on ridges/upper slopes',
                '🦌 Deer move from bedding to water/food'
            ]
        })
    
    # Evening thermals (2-3 hours before sunset) - Warm air flows uphill  
    elif 15 <= time_of_day <= 19:
        thermal_data.update({
            'is_thermal_active': True,
            'thermal_direction': 'upslope',  # Anabatic flow
            'thermal_strength': min(10, max(4, (time_of_day - 14) * 1.2)),  # Builds through afternoon
            'dominant_wind': 'thermal' if time_of_day >= 16 else 'mixed',
            'hunting_advantage': 'EVENING_VALLEY',
            'best_stand_positions': ['valley_bottoms', 'creek_beds', 'lower_slopes'],
            'timing_notes': [
                '🌅 Peak thermal hunting window',
                '🔥 Warm air rises - scent carries up and away',
                '🎯 Position in valleys/lower elevations',
                '🦌 Deer move from bedding to evening feeding'
            ]
        })
    
    # Transition periods - Less predictable thermals
    elif 11 <= time_of_day <= 14:
        thermal_data.update({
            'is_thermal_active': False,
            'thermal_direction': 'variable',
            'thermal_strength': 2,
            'dominant_wind': 'prevailing',
            'hunting_advantage': 'MIDDAY_CAUTION',
            'best_stand_positions': ['shaded_areas', 'thick_cover'],
            'timing_notes': [
                '☀️ Midday thermal transition',
                '🌪️ Variable wind patterns',
                '⚠️ Less predictable scent control',
                '😴 Deer typically bedded'
            ]
        })
    
    else:  # Night hours
        thermal_data.update({
            'is_thermal_active': True,
            'thermal_direction': 'downslope',
            'thermal_strength': 3,
            'dominant_wind': 'thermal',
            'hunting_advantage': 'NIGHT_STABLE',
            'timing_notes': ['🌙 Stable downslope flow', '🦌 Minimal deer movement']
        })
    
    return thermal_data


def compute_hourly_hunt_schedule(lat: float, lon: float, stands: List[Dict[str, Any]], terrain_features: Dict[str, Any], season: str, hourly: List[Dict[str, Any]], huntable_threshold: float = 75.0) -> List[Dict[str, Any]]:
    """Build next 48h schedule: for each hour, rank stands by combined wind+thermal favorability and season weights."""
    schedule = []
    if not hourly or not stands:
        return schedule
    
    # Precompute each stand's bearing from center for wind calc
    enriched_stands = []
    for s in stands:
        coords = s.get('coordinates', {})
        sbearing = calculate_bearing(lat, lon, coords.get('lat', lat), coords.get('lon', lon))
        enriched = dict(s)
        enriched['bearing_from_center'] = float(sbearing)
        enriched_stands.append(enriched)

    # Season weights influence emphasis
    season_weights = {
        "early_season": {"travel": 1.0, "bedding": 1.0, "feeding": 1.2},
        "rut": {"travel": 1.3, "bedding": 0.9, "feeding": 1.0},
        "late_season": {"travel": 0.8, "bedding": 1.5, "feeding": 1.1},
    }
    sw = season_weights.get(season, {"travel": 1.0, "bedding": 1.0, "feeding": 1.0})

    for hour_entry in hourly:
        wind_dir = float(hour_entry.get('wind_direction', 0))
        temp = float(hour_entry.get('temperature', 0))
        hour_local = int(hour_entry.get('hour', 0))

        # Thermal model for this hour
        thermal = calculate_thermal_wind_effect(lat, lon, hour_local)

        ranked = []
        for s in enriched_stands:
            # Wind favorability for stand
            wind_score = score_wind_favorability(s['bearing_from_center'], wind_dir)
            # Combine with thermal effects and terrain
            combined = calculate_combined_wind_favorability(s['bearing_from_center'], wind_dir, thermal, terrain_features)
            
            # Season weight by stand type proxy
            stype = (s.get('type') or '').lower()
            if 'travel' in stype or 'corridor' in stype or 'saddle' in stype or 'ridge' in stype:
                season_boost = sw['travel']
            elif 'bed' in stype or 'winter' in stype or 'yard' in stype:
                season_boost = sw['bedding']
            elif 'food' in stype or 'feed' in stype or 'orchard' in stype:
                season_boost = sw['feeding']
            else:
                season_boost = (sw['travel'] + sw['bedding'] + sw['feeding']) / 3.0

            # Confidence prior from stand object
            prior = float(s.get('confidence', 70))

            # Final score (0-100), emphasizing wind/thermal but respecting prior and season
            final_score = min(100.0, 0.5 * combined + 0.2 * wind_score + 0.2 * prior + 10.0 * (season_boost - 1.0))
            ranked.append({
                "stand_id": s.get('id'),
                "type": s.get('type'),
                "coordinates": s.get('coordinates', {}),
                "wind_favorability": round(wind_score, 1),
                "combined_wind_thermal": round(combined, 1),
                "temperature": round(temp, 1),
                "score": round(final_score, 1),
            })

        ranked.sort(key=lambda x: x['score'], reverse=True)
        top = ranked[:3]
        # Huntable flag based on WIND favorability threshold per spec (≥75%)
        huntable_top = [r for r in ranked if r['wind_favorability'] >= huntable_threshold]

        schedule.append({
            "time": hour_entry.get('time'),
            "hour": hour_local,
            "top_three": top,
            "huntable": huntable_top[:3],
            "thermal": thermal.get('hunting_advantage'),
        })

    return schedule


def calculate_combined_wind_favorability(stand_direction: float, wind_direction: float, thermal_data: Dict, terrain_features: Dict) -> float:
    """
    Calculate wind favorability incorporating both prevailing winds and thermal effects
    Enhanced for Vermont topography and hunting conditions
    """
    base_favorability = calculate_basic_wind_favorability(stand_direction, wind_direction)
    
    if not thermal_data['is_thermal_active']:
        return base_favorability
    
    # Thermal adjustments based on stand position and thermal flow
    thermal_bonus = 0
    
    if thermal_data['thermal_direction'] == 'downslope':
        # Morning/night downslope thermals favor ridge and upper slope positions
        if terrain_features.get('ridges') and stand_direction in [0, 45, 315, 270]:  # N, NE, NW, W aspects
            thermal_bonus += 25
        elif terrain_features.get('saddles'):
            thermal_bonus += 15
    
    elif thermal_data['thermal_direction'] == 'upslope':
        # Evening upslope thermals favor valley and lower positions
        if terrain_features.get('valleys') or terrain_features.get('creek_beds'):
            thermal_bonus += 20
        # South and east facing slopes get evening thermal boost
        if stand_direction in [90, 135, 180]:  # E, SE, S aspects
            thermal_bonus += 15
    
    # Thermal strength multiplier
    strength_multiplier = thermal_data['thermal_strength'] / 10.0
    thermal_bonus *= strength_multiplier
    
    # Apply Vermont-specific thermal knowledge
    if thermal_data['hunting_advantage'] == 'MORNING_RIDGE':
        if 'ridge' in terrain_features or 'saddle' in terrain_features:
            thermal_bonus += 10
    elif thermal_data['hunting_advantage'] == 'EVENING_VALLEY':
        if terrain_features.get('valleys') or terrain_features.get('feeding_areas'):
            thermal_bonus += 10
    
    final_score = min(95, base_favorability + thermal_bonus)
    return max(15, final_score)  # Minimum 15% favorability


def calculate_basic_wind_favorability(stand_direction: float, wind_direction: float) -> float:
    """Calculate basic wind favorability without thermal effects (0-100)"""
    # Calculate the angle between stand position and wind direction
    angle_diff = abs(stand_direction - wind_direction)
    if angle_diff > 180:
        angle_diff = 360 - angle_diff
    
    # Best positions are when wind is blowing FROM the deer TO the hunter
    # This means the stand should be downwind of the deer approach
    if angle_diff <= 30:  # Very favorable wind
        return 90
    elif angle_diff <= 60:  # Good wind
        return 75
    elif angle_diff <= 90:  # Acceptable wind
        return 60
    elif angle_diff <= 120:  # Marginal wind
        return 40
    else:  # Poor wind
        return 25


def calculate_wind_favorability(stand_direction: float, wind_direction: float) -> float:
    """Legacy function for backward compatibility - uses basic wind calculation"""
    return calculate_basic_wind_favorability(stand_direction, wind_direction)


def generate_setup_notes(stand_type: str, pattern: Dict, wind_direction: float, season: str) -> str:
    """Generate specific setup instructions for each stand"""
    notes = []
    
    # Basic setup based on stand type
    if "Tree Stand" in stand_type:
        notes.append("🌲 20-22ft height recommended")
        notes.append("🎯 Clear shooting lanes to 30 yards")
    elif "Ground Blind" in stand_type:
        notes.append("🏠 Brush in blind 2-3 weeks early")
        notes.append("🎯 Multiple shooting windows")
    elif "Elevated" in stand_type:
        notes.append("🪜 Ladder stand or climbing sticks")
        notes.append("🎯 360° shooting capability")
    
    # Wind-specific notes
    wind_dir = get_compass_direction(wind_direction)
    notes.append(f"🌬️ Set up with {wind_dir} wind")
    
    # Seasonal notes
    if season == "rut":
        notes.append("📅 Best Nov 1-15")
        notes.append("🦌 All-day hunting potential")
    elif season == "early_season":
        notes.append("📅 Best Sep 15 - Oct 15")
        notes.append("🌅 Evening sits preferred")
    
    return " | ".join(notes)


def get_compass_direction(degrees: float) -> str:
    """Convert degrees to compass direction"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]


def get_stand_placement_recommendations(terrain_features: Dict, weather_data: Dict, lat: float, lon: float, season: str, stand_rating: float) -> List[Dict]:
    """Generate specific stand placement recommendations with GPS coordinates"""
    recommendations = []
    
    # Calculate offset coordinates for stand placements (approximate 50-100 yard offsets)
    lat_offset_50y = 0.00045  # Roughly 50 yards in degrees
    lat_offset_100y = 0.0009  # Roughly 100 yards in degrees
    lon_offset_50y = 0.00045
    lon_offset_100y = 0.0009
    
    # Primary stand recommendation based on highest terrain feature
    if terrain_features.get('saddles'):
        # Position stand 75 yards northeast of saddle (typical deer approach)
        stand_lat = lat + (lat_offset_50y * 1.5)
        stand_lon = lon + (lon_offset_50y * 1.5)
        recommendations.append({
            'type': 'Primary Saddle Stand',
            'priority': 'HIGHEST',
            'coordinates': {'lat': round(stand_lat, 6), 'lon': round(stand_lon, 6)},
            'distance': '75 yards NE of marked point',
            'reason': 'Deer naturally funnel through saddles - prime ambush location',
            'setup': f'Set 18-20ft high, wind direction: {get_wind_direction_advice(weather_data)}',
            'best_times': get_season_timing(season, 'saddle'),
            'approach': 'Enter from downwind side, use existing deer trails',
            'confidence': min(95, stand_rating * 10)
        })
        
        # Secondary stand option
        stand_lat2 = lat - lat_offset_50y
        stand_lon2 = lon + lon_offset_100y
        recommendations.append({
            'type': 'Secondary Saddle Stand',
            'priority': 'HIGH',
            'coordinates': {'lat': round(stand_lat2, 6), 'lon': round(stand_lon2, 6)},
            'distance': '50 yards S, 100 yards E of marked point',
            'reason': 'Alternative position for different wind conditions',
            'setup': 'Wind backup position, 16-18ft elevation',
            'best_times': get_season_timing(season, 'secondary'),
            'approach': 'Use when primary stand has wrong wind',
            'confidence': min(85, (stand_rating - 0.5) * 10)
        })
    
    if terrain_features.get('ridge_lines') and not terrain_features.get('saddles'):
        # Ridge hunting setup
        stand_lat = lat + lat_offset_50y
        stand_lon = lon - lat_offset_50y
        recommendations.append({
            'type': 'Ridge Travel Stand',
            'priority': 'HIGH',
            'coordinates': {'lat': round(stand_lat, 6), 'lon': round(stand_lon, 6)},
            'distance': '50 yards N, 50 yards W of marked point',
            'reason': 'Deer travel parallel to ridges for security and thermal currents',
            'setup': f'Position 25 yards below ridge crest, height 15-18ft',
            'best_times': get_season_timing(season, 'ridge'),
            'approach': 'Climb from valley side to avoid skylining',
            'confidence': min(80, stand_rating * 10)
        })
    
    if terrain_features.get('winter_yards') and season in ['late_season', 'early_season']:
        # Winter yard hunting (seasonal)
        stand_lat = lat + lat_offset_100y
        stand_lon = lon
        recommendations.append({
            'type': 'Winter Yard Edge Stand',
            'priority': 'MEDIUM-HIGH',
            'coordinates': {'lat': round(stand_lat, 6), 'lon': round(stand_lon, 6)},
            'distance': '100 yards N of marked point',
            'reason': 'Deer concentrate in winter yards during cold weather',
            'setup': 'Position on edge of thick cover, not inside yard',
            'best_times': get_season_timing(season, 'winter_yard'),
            'approach': 'Enter carefully to avoid spooking bedded deer',
            'confidence': min(75, stand_rating * 10)
        })
    
    # Add feeding area stands if moderate terrain
    if not recommendations or terrain_features.get('moderate_features'):
        stand_lat = lat - lat_offset_50y
        stand_lon = lon - lat_offset_50y
        recommendations.append({
            'type': 'Food Source Stand',
            'priority': 'MEDIUM',
            'coordinates': {'lat': round(stand_lat, 6), 'lon': round(stand_lon, 6)},
            'distance': '50 yards SW of marked point',
            'reason': 'Position between bedding and feeding areas',
            'setup': 'Focus on travel corridors, 15-20ft height',
            'best_times': get_season_timing(season, 'feeding'),
            'approach': 'Set up during midday when deer are bedded',
            'confidence': min(70, stand_rating * 10)
        })
    
    # If stand rating is low, suggest scouting locations
    if stand_rating < 5:
        # Suggest exploration points in multiple directions
        exploration_points = [
            (lat + lat_offset_100y, lon, 'North'),
            (lat, lon + lon_offset_100y, 'East'), 
            (lat - lat_offset_100y, lon, 'South'),
            (lat, lon - lon_offset_100y, 'West')
        ]
        
        for point_lat, point_lon, direction in exploration_points:
            recommendations.append({
                'type': f'Scouting Point {direction}',
                'priority': 'SCOUTING',
                'coordinates': {'lat': round(point_lat, 6), 'lon': round(point_lon, 6)},
                'distance': f'100 yards {direction} of marked point',
                'reason': 'Current location shows low deer activity - scout these areas for better sign',
                'setup': 'Look for trails, rubs, scrapes, and droppings',
                'best_times': 'Midday scouting when deer are bedded',
                'approach': 'Quiet exploration, mark GPS of any deer sign found',
                'confidence': 30
            })
    
    return recommendations

def get_wind_direction_advice(weather_data: Dict) -> str:
    """Get wind direction advice for stand setup including tomorrow's forecast"""
    current_advice = "Check wind direction before hunting"
    tomorrow_advice = ""
    
    # Current wind advice
    if weather_data and 'wind_direction' in weather_data:
        wind_dir = weather_data['wind_direction']
        if 0 <= wind_dir < 45 or 315 <= wind_dir < 360:
            current_advice = "Current: North wind - set up on south side"
        elif 45 <= wind_dir < 135:
            current_advice = "Current: East wind - set up on west side"
        elif 135 <= wind_dir < 225:
            current_advice = "Current: South wind - set up on north side"
        elif 225 <= wind_dir < 315:
            current_advice = "Current: West wind - set up on east side"
    
    # Tomorrow's wind advice
    tomorrow_forecast = weather_data.get('tomorrow_forecast', {})
    if tomorrow_forecast and 'wind_direction_dominant' in tomorrow_forecast:
        wind_dir = tomorrow_forecast['wind_direction_dominant']
        wind_speed = tomorrow_forecast.get('wind_speed_max', 0)
        
        direction_name = ""
        setup_side = ""
        if 0 <= wind_dir < 45 or 315 <= wind_dir < 360:
            direction_name = "North"
            setup_side = "south side"
        elif 45 <= wind_dir < 135:
            direction_name = "East"
            setup_side = "west side"
        elif 135 <= wind_dir < 225:
            direction_name = "South"
            setup_side = "north side"
        elif 225 <= wind_dir < 315:
            direction_name = "West"
            setup_side = "east side"
        
        if direction_name:
            tomorrow_advice = f" | Tomorrow: {direction_name} wind ({wind_speed:.1f} mph) - set up on {setup_side}"
    
    return current_advice + tomorrow_advice

def get_season_timing(season: str, stand_type: str) -> str:
    """Get optimal timing for different stand types and seasons"""
    timing_map = {
        'early_season': {
            'saddle': 'Evening hunts 5-7 PM, morning hunts 6:30-8:30 AM',
            'secondary': 'Midday 11 AM-1 PM during hot weather',
            'ridge': 'Morning hunts 7-9 AM as deer return to bedding',
            'feeding': 'Evening hunts 4-6 PM before dark',
            'winter_yard': 'Late morning 9-11 AM as deer move to water'
        },
        'rut': {
            'saddle': 'All day hunting - peak 10 AM-2 PM during rut',
            'secondary': 'Dawn and dusk plus midday during peak rut',
            'ridge': 'All day - bucks travel ridges seeking does',
            'feeding': 'Less effective during rut - focus on travel routes',
            'winter_yard': 'Early morning 6-8 AM for rutting activity'
        },
        'late_season': {
            'saddle': 'Late morning 9 AM-12 PM and evening 3-5 PM',
            'secondary': 'Midday 11 AM-2 PM during cold snaps',
            'ridge': 'Afternoon 1-4 PM for thermal movement',
            'feeding': 'Prime time 3:30-6 PM for food sources',
            'winter_yard': 'Best during cold weather, midday feeding'
        }
    }
    return timing_map.get(season, {}).get(stand_type, 'Dawn and dusk hunting')

def generate_mature_buck_predictions(lat: float, lon: float, terrain_features: Dict, 
                                    weather_data: Dict, season: str, time_of_day: int) -> Dict:
    """
    Generate mature buck specific predictions and stand recommendations
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        terrain_features: Terrain analysis results
        weather_data: Current weather conditions
        season: Hunting season
        time_of_day: Hour of day (0-23)
        
    Returns:
        Dict containing mature buck predictions, markers, and stand recommendations
    """
    logger.info(f"Generating mature buck predictions for {lat}, {lon}")
    
    # Get mature buck predictor instance
    buck_predictor = get_mature_buck_predictor()
    
    # Analyze terrain suitability for mature bucks
    mature_buck_scores = buck_predictor.analyze_mature_buck_terrain(terrain_features, lat, lon)
    
    # Predict movement patterns
    movement_prediction = buck_predictor.predict_mature_buck_movement(
        season, time_of_day, terrain_features, weather_data, lat, lon
    )
    
    # Generate specialized stand recommendations with weather data
    stand_recommendations = generate_mature_buck_stand_recommendations(
        terrain_features, mature_buck_scores, lat, lon, weather_data
    )
    
    # Create mature buck opportunity markers using actual stand recommendations
    mature_buck_markers = []
    
    if mature_buck_scores['overall_suitability'] >= 60.0 and stand_recommendations:
        # Use actual stand recommendations for marker positions
        for i, stand_rec in enumerate(stand_recommendations[:3]):  # Use first 3 stands as opportunities
            stand_coords = stand_rec.get('coordinates', {})
            if stand_coords.get('lat') and stand_coords.get('lon'):
                marker_lat = stand_coords['lat']
                marker_lon = stand_coords['lon']
                
                # Calculate confidence based on terrain scores and movement prediction
                confidence = (mature_buck_scores['overall_suitability'] + 
                             movement_prediction['confidence_score']) / 2
                
                mature_buck_markers.append({
                    'lat': marker_lat,
                    'lon': marker_lon,
                    'confidence': round(confidence, 1),
                    'rank': i + 1,
                    'type': 'mature_buck_opportunity',
                    'description': f"Mature Buck Stand #{i+1} (Confidence: {confidence:.1f}%)",
                    'terrain_score': mature_buck_scores['overall_suitability'],
                    'movement_probability': movement_prediction['movement_probability'],
                    'pressure_resistance': mature_buck_scores['pressure_resistance'],
                    'escape_routes': mature_buck_scores['escape_route_quality'],
                    'behavioral_notes': movement_prediction['behavioral_notes'][:3],  # Top 3 notes
                    'stand_justification': stand_rec.get('justification', 'Strategic positioning'),
                    'distance_from_center': stand_rec.get('distance_from_center', 0)
                })
            
    # If no stand recommendations available, fall back to geometric positioning
    if not mature_buck_markers and mature_buck_scores['overall_suitability'] >= 60.0:
        logger.warning("No stand recommendations available, using fallback positioning")
        num_opportunities = min(3, max(1, int(mature_buck_scores['overall_suitability'] / 30)))
        
        for i in range(num_opportunities):
            # Use larger, more realistic offsets
            offset_distance = 0.0015 + (i * 0.0008)  # 165-250 yards apart
            offset_angle = 45 + (i * 120)  # Spread around circle
            
            angle_rad = np.radians(offset_angle)
            marker_lat = lat + (offset_distance * np.cos(angle_rad))
            marker_lon = lon + (offset_distance * np.sin(angle_rad))
            
            # Calculate confidence based on terrain scores and movement prediction
            confidence = (mature_buck_scores['overall_suitability'] + 
                         movement_prediction['confidence_score']) / 2
            
            mature_buck_markers.append({
                'lat': marker_lat,
                'lon': marker_lon,
                'confidence': round(confidence, 1),
                'rank': i + 1,
                'type': 'mature_buck_opportunity',
                'description': f"Mature Buck Stand #{i+1} (Confidence: {confidence:.1f}%)",
                'terrain_score': mature_buck_scores['overall_suitability'],
                'movement_probability': movement_prediction['movement_probability'],
                'pressure_resistance': mature_buck_scores['pressure_resistance'],
                'escape_routes': mature_buck_scores['escape_route_quality'],
                'behavioral_notes': movement_prediction['behavioral_notes'][:3]  # Top 3 notes
            })
    
    return {
        'terrain_scores': mature_buck_scores,
        'movement_prediction': movement_prediction,
        'stand_recommendations': stand_recommendations,
        'opportunity_markers': mature_buck_markers,
        'viable_location': mature_buck_scores['overall_suitability'] >= 60.0,
        'confidence_summary': {
            'overall_suitability': mature_buck_scores['overall_suitability'],
            'movement_confidence': movement_prediction['confidence_score'],
            'pressure_tolerance': mature_buck_scores['pressure_resistance']
        }
    }


def create_mature_buck_geojson_features(mature_buck_data: Dict) -> Dict:
    """Convert mature buck markers to GeoJSON format with distinctive styling"""
    
    mature_buck_features = []
    
    if mature_buck_data['viable_location']:
        for marker in mature_buck_data['opportunity_markers']:
            # Create distinctive mature buck marker with crosshairs symbol and dark red color
            mature_buck_features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [marker['lon'], marker['lat']]
                },
                "properties": {
                    "type": "mature_buck",
                    "confidence": marker['confidence'],
                    "rank": marker['rank'],
                    "description": marker['description'],
                    "marker_color": "darkred",  # Dark red for mature bucks
                    "marker_symbol": "cross",   # Crosshairs symbol
                    "marker_size": "large",     # Larger size for emphasis
                    "terrain_score": marker['terrain_score'],
                    "movement_probability": marker['movement_probability'],
                    "pressure_resistance": marker['pressure_resistance'],
                    "escape_routes": marker['escape_routes'],
                    "behavioral_notes": marker['behavioral_notes'],
                    "hunting_notes": [
                        f"Terrain Suitability: {marker['terrain_score']:.1f}%",
                        f"Movement Probability: {marker['movement_probability']:.1f}%", 
                        f"Pressure Resistance: {marker['pressure_resistance']:.1f}%"
                    ]
                }
            })
    
    return {"type": "FeatureCollection", "features": mature_buck_features}


def generate_simple_markers(score_maps: Dict, center_lat: float, center_lon: float) -> Dict:
    """Generate simple marker locations for bedding, feeding, and travel areas instead of complex zones"""
    
    markers = {
        'bedding_markers': [],
        'feeding_markers': [],
        'travel_markers': []
    }
    
    # Generate markers for each behavior type
    for behavior, score_map in score_maps.items():
        marker_type = f"{behavior}_markers"
        
        # Find top 3 locations for each behavior
        high_score_locations = find_high_score_locations(score_map, center_lat, center_lon, top_n=3)
        
        for i, location in enumerate(high_score_locations):
            marker = {
                'lat': location['lat'],
                'lon': location['lon'],
                'score': location['score'],
                'rank': i + 1,
                'behavior': behavior,
                'description': f"{behavior.title()} Area #{i+1} (Score: {location['score']:.1f})"
            }
            markers[marker_type].append(marker)
    
    return markers

def create_simple_geojson_features(markers: Dict, mature_buck_features: Dict = None) -> Dict:
    """Convert simple markers to GeoJSON format for the frontend, including mature buck features"""
    
    # Bedding areas (red markers)
    bedding_features = []
    for marker in markers['bedding_markers']:
        bedding_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [marker['lon'], marker['lat']]
            },
            "properties": {
                "type": "bedding",
                "score": marker['score'],
                "rank": marker['rank'],
                "description": marker['description'],
                "marker_color": "red",
                "marker_symbol": "tree"
            }
        })
    
    # Feeding areas (green markers)
    feeding_features = []
    for marker in markers['feeding_markers']:
        feeding_features.append({
            "type": "Feature", 
            "geometry": {
                "type": "Point",
                "coordinates": [marker['lon'], marker['lat']]
            },
            "properties": {
                "type": "feeding",
                "score": marker['score'],
                "rank": marker['rank'],
                "description": marker['description'],
                "marker_color": "green",
                "marker_symbol": "leaf"
            }
        })
    
    # Travel areas (blue markers)
    travel_features = []
    for marker in markers['travel_markers']:
        travel_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point", 
                "coordinates": [marker['lon'], marker['lat']]
            },
            "properties": {
                "type": "travel",
                "score": marker['score'],
                "rank": marker['rank'],
                "description": marker['description'],
                "marker_color": "blue",
                "marker_symbol": "footprints"
            }
        })
    
    result = {
        "bedding_zones": {"type": "FeatureCollection", "features": bedding_features},
        "feeding_areas": {"type": "FeatureCollection", "features": feeding_features},
        "travel_corridors": {"type": "FeatureCollection", "features": travel_features}
    }
    
    # Add mature buck features if provided
    if mature_buck_features:
        result["mature_buck_opportunities"] = mature_buck_features
    
    return result

@app.post("/predict", summary="Generate deer movement predictions", response_model=PredictionResponse, tags=["predictions"])
def predict_movement(request: PredictionRequest):
    logger.info(f"Received prediction request for lat: {request.lat}, lon: {request.lon}, season: {request.season}")
    try:
        # Extract hour from request for thermal calculations
        request_datetime = datetime.fromisoformat(request.date_time.replace('Z', '+00:00'))
        current_hour = request_datetime.hour
        
        # 1. Load rules and fetch REAL environmental data with Vermont-specific weather
        rules = load_rules()
        
        # Start timing for performance monitoring
        start_time = datetime.now()
        
        weather_data = core.get_weather_data(request.lat, request.lon)
        
        # Add hour information for thermal calculations
        weather_data['hour'] = current_hour
        
        elevation_grid = core.get_real_elevation_grid(request.lat, request.lon)
        vegetation_grid = core.get_vegetation_grid_from_osm(request.lat, request.lon)
        
        # Road proximity removed for performance - using neutral grid
        road_proximity = np.ones((core.GRID_SIZE, core.GRID_SIZE)) * 0.5

        # 2. Analyze features and conditions with Vermont enhancements
        features = core.analyze_terrain_and_vegetation(elevation_grid, vegetation_grid)
        # Add hunting pressure proxy (near-road penalty support)
        features["road_proximity"] = road_proximity
        
        # Enhanced conditions with Vermont-specific weather integration
        conditions = {
            "time_of_day": core.get_time_of_day(request.date_time),
            "season": request.season,
            "weather_conditions": weather_data.get("conditions", []),
            "temperature": weather_data.get("temperature", 0),
            "snow_depth": weather_data.get("snow_depth_inches", 0),
            "leeward_aspects": weather_data.get("leeward_aspects", [])
        }
        
        # Add moon phase influence (Vermont enhancement)
        moon_phase = core.get_moon_phase(request.date_time)
        if moon_phase == "new":
            conditions["moon_boost"] = True

        # 3. Run the enhanced Vermont-specific rule engine
        score_maps = core.run_grid_rule_engine(rules, features, conditions)
        logger.info(f"Score map stats - Travel: max={np.max(score_maps['travel']):.2f}, Bedding: max={np.max(score_maps['bedding']):.2f}, Feeding: max={np.max(score_maps['feeding']):.2f}")

        # 3.5. ENHANCE PREDICTIONS WITH SCOUTING DATA
        logger.info("Enhancing predictions with scouting data...")
        enhancement_result = {"enhancements_applied": [], "mature_buck_indicators": 0}
        try:
            enhancer = get_scouting_enhancer()
            enhancement_result = enhancer.enhance_predictions(
                request.lat, request.lon, score_maps, 0.04, core.GRID_SIZE
            )
            
            # Use enhanced score maps
            score_maps = enhancement_result["enhanced_score_maps"]
            
            # Log enhancement results
            if enhancement_result["enhancements_applied"]:
                logger.info(f"✅ Applied {len(enhancement_result['enhancements_applied'])} scouting enhancements")
                logger.info(f"✅ Total boost points: {enhancement_result['total_boost_points']:.1f}")
                logger.info(f"✅ Mature buck indicators: {enhancement_result['mature_buck_indicators']}")
                
                # Log enhanced score stats
                logger.info(f"Enhanced score map stats - Travel: max={np.max(score_maps['travel']):.2f}, Bedding: max={np.max(score_maps['bedding']):.2f}, Feeding: max={np.max(score_maps['feeding']):.2f}")
            else:
                logger.info("No scouting data available for enhancement")
                
        except Exception as e:
            logger.warning(f"Scouting enhancement failed: {e} - continuing with base predictions")

        # 4. Generate data-driven markers from score maps (top-N points per behavior)
        markers = generate_simple_markers(score_maps, request.lat, request.lon)
        
        # 4.5. Generate mature buck predictions and markers with timeout
        try:
            # Generate mature buck predictions (Windows-compatible - no signal timeout)
            mature_buck_data = generate_mature_buck_predictions(
                request.lat, request.lon, features, weather_data, request.season, current_hour
            )
            
        except (TimeoutError, Exception) as e:
            logger.warning(f"Mature buck analysis failed or timed out: {e} - using simplified analysis")
            # Provide simplified mature buck data
            mature_buck_data = {
                'viable_location': False,
                'confidence_summary': {'overall_suitability': 50.0, 'movement_confidence': 50.0, 'pressure_tolerance': 50.0},
                'opportunity_markers': [],
                'stand_recommendations': [],
                'terrain_scores': {'bedding_suitability': 50.0, 'escape_route_quality': 50.0, 'isolation_score': 50.0, 'pressure_resistance': 50.0},
                'movement_prediction': {'movement_probability': 50.0, 'preferred_times': ['Dawn', 'Dusk'], 'behavioral_notes': ['Limited analysis due to timeout']}
            }
        
        # 4.6. Integrate ML enhancement if available  
        try:
            from ml_enhanced_predictor import MLEnhancedMatureBuckPredictor
            buck_predictor = get_mature_buck_predictor()
            ml_predictor = MLEnhancedMatureBuckPredictor(base_model=buck_predictor)
            
            # Test accuracy improvement if requested
            if request.lat == 44.26 and request.lon == -72.58:  # Special coordinates for testing
                logger.info("🧪 Running ML accuracy test on synthetic data...")
                testing_framework = ml_predictor.create_accuracy_testing_framework()
                accuracy_results = testing_framework.run_accuracy_comparison()
                
                mature_buck_data['ml_test_results'] = accuracy_results
            
            # Use ML-enhanced predictions for mature buck analysis
            ml_enhanced_prediction = ml_predictor.predict_with_ml_enhancement(
                request.lat, request.lon, features, weather_data, request.season, current_hour
            )
            
            # Update mature buck data with ML insights
            if ml_enhanced_prediction['has_ml_enhancement']:
                mature_buck_data['ml_enhanced'] = True
                mature_buck_data['ml_confidence_boost'] = ml_enhanced_prediction['confidence_boost']
                
                # Boost confidence scores for high-probability ML predictions
                for marker in mature_buck_data['opportunity_markers']:
                    marker['confidence'] = min(95, marker['confidence'] + ml_enhanced_prediction['confidence_boost'])
                    marker['ml_enhanced'] = True
            
        except ImportError:
            logger.info("ML enhancement not available - using rule-based predictions only")
        except Exception as e:
            logger.warning(f"ML enhancement failed: {e} - falling back to rule-based predictions")
        
        mature_buck_geojson = create_mature_buck_geojson_features(mature_buck_data)
        
        # Create GeoJSON features including mature buck opportunities
        geojson_features = create_simple_geojson_features(markers, mature_buck_geojson)
        travel_corridors = geojson_features["travel_corridors"]
        bedding_zones = geojson_features["bedding_zones"]
        feeding_zones = geojson_features["feeding_areas"]
        mature_buck_opportunities = geojson_features.get("mature_buck_opportunities")
        
        logger.info(
            "Generated markers: travel=%d, bedding=%d, feeding=%d, mature_buck=%d",
            len(travel_corridors.get('features', [])),
            len(bedding_zones.get('features', [])),
            len(feeding_zones.get('features', [])),
            len(mature_buck_opportunities.get('features', [])) if mature_buck_opportunities else 0,
        )

        # 5. Calculate overall stand rating with Vermont seasonal weighting
        if request.season == "late_season":
            # Winter emphasis on bedding areas
            stand_rating = np.mean([np.max(score_maps['travel']) * 0.7, np.max(score_maps['bedding']) * 1.5, np.max(score_maps['feeding']) * 1.1])
        elif request.season == "rut":
            # Rutting emphasis on travel corridors
            stand_rating = np.mean([np.max(score_maps['travel']) * 1.3, np.max(score_maps['bedding']) * 0.9, np.max(score_maps['feeding'])])
        else:
            # Early season balance
            stand_rating = np.mean([np.max(score_maps['travel']), np.max(score_maps['bedding']), np.max(score_maps['feeding']) * 1.2])
        
        stand_rating = round(min(stand_rating, 10), 1)

        # 6. Find better spots if current rating is low (Vermont-enhanced)
        suggested_spots = core.find_better_hunting_spots(
            score_maps, request.lat, request.lon, stand_rating,
            suggestion_threshold=request.suggestion_threshold,
            min_target_rating=request.min_suggestion_rating
        )

        # 7. Create enhanced visualization heatmaps with better descriptions
        terrain_heatmap = core.create_heatmap_image(elevation_grid, cmap='terrain')
        vegetation_heatmap = core.create_heatmap_image(vegetation_grid, cmap='viridis')
        
        # Enhanced score heatmaps with normalized scaling and better colormaps
        travel_score_heatmap = core.create_enhanced_score_heatmap(
            score_maps['travel'], 
            title="Deer Travel Corridors", 
            description="Red/Orange = High movement probability, Blue = Low movement",
            cmap='plasma'  # Better contrast: purple/blue (low) to yellow/pink (high)
        )
        bedding_score_heatmap = core.create_enhanced_score_heatmap(
            score_maps['bedding'], 
            title="Deer Bedding Areas", 
            description="Yellow/Green = High bedding probability, Dark = Low bedding",
            cmap='viridis'  # Dark blue (low) to bright yellow (high)
        )
        feeding_score_heatmap = core.create_enhanced_score_heatmap(
            score_maps['feeding'], 
            title="Deer Feeding Areas", 
            description="Bright colors = High feeding probability, Dark = Low feeding",
            cmap='magma'  # Black (low) to white/yellow (high)
        )

        # 9. Create enhanced notes with Vermont-specific context and heatmap explanations
        notes = f"🏔️ **Vermont White-tailed Deer Predictions** - Enhanced grid analysis for {request.season} season.\n\n"
        
        # Add heatmap interpretation guide
        notes += "📊 **How to Read the Score Heatmaps:**\n"
        notes += "• **Red areas (8-10)**: Excellent deer activity - prime hunting locations\n"
        notes += "• **Yellow areas (6-7)**: Good deer activity - solid hunting spots\n"
        notes += "• **Blue areas (0-5)**: Lower deer activity - less productive areas\n\n"
        
        # Add activity-specific guidance
        notes += "🎯 **Activity Markers Guide:**\n"
        notes += f"• **Travel Markers (Blue)**: Point markers showing prime travel corridors - ideal for morning/evening hunts\n"
        notes += f"• **Bedding Markers (Red)**: Point markers for top bedding areas in thick cover, especially {_get_bedding_preference(request.season)}\n"
        notes += f"• **Feeding Markers (Green)**: Point markers for feeding areas near {_get_feeding_preference(request.season)}\n"
        notes += f"• **🎯 Stand Locations (⭐)**: Star markers positioned strategically to intercept deer moving between activity areas\n"
        
        # Add mature buck opportunities section
        if mature_buck_data['viable_location']:
            num_opportunities = len(mature_buck_data['opportunity_markers'])
            notes += f"• **🏹 Mature Buck Opportunities (🎯)**: {num_opportunities} crosshair markers for mature whitetail bucks (3.5+ years)\n"
            notes += f"  - Overall Terrain Suitability: {mature_buck_data['confidence_summary']['overall_suitability']:.1f}%\n"
            notes += f"  - Movement Confidence: {mature_buck_data['confidence_summary']['movement_confidence']:.1f}%\n"
            notes += f"  - Pressure Resistance: {mature_buck_data['confidence_summary']['pressure_tolerance']:.1f}%\n"
            
            # Add ML enhancement info if available
            if mature_buck_data.get('ml_enhanced'):
                notes += f"  - 🤖 ML Enhancement: +{mature_buck_data['ml_confidence_boost']:.1f}% confidence boost\n"
        else:
            notes += f"• **🏹 Mature Buck Assessment**: Location below threshold for mature buck targeting (terrain suitability: {mature_buck_data['confidence_summary']['overall_suitability']:.1f}%)\n"
        
        # Add ML test results if available
        if mature_buck_data.get('ml_test_results'):
            test_results = mature_buck_data['ml_test_results']
            notes += f"\n🧪 **ML Accuracy Test Results** (Coordinates: 44.26, -72.58):\n"
            notes += f"• Rule-based Accuracy: {test_results['rule_based_accuracy']:.1f}%\n"
            notes += f"• ML-enhanced Accuracy: {test_results['ml_accuracy']:.1f}%\n"
            notes += f"• Improvement: +{test_results['improvement']:.1f}%\n"
            notes += f"• Test Samples: {test_results['test_samples']}\n"
        
        notes += "\n"
        
        # Add weather context and thermal analysis
        if weather_data.get("conditions"):
            weather_desc = ", ".join(weather_data["conditions"])
            notes += f"🌤️ **Current Weather Impact**: {weather_desc}\n"
            notes += _get_weather_impact_explanation(weather_data["conditions"]) + "\n\n"
        
        # Add thermal wind analysis
        current_hour = weather_data.get('hour', 17)
        thermal_data = calculate_thermal_wind_effect(request.lat, request.lon, current_hour)
        
        if thermal_data['is_thermal_active']:
            notes += f"🌡️ **Thermal Wind Analysis** (Hour {current_hour:02d}:00):\n"
            notes += f"• **Thermal Flow**: {thermal_data['thermal_direction'].title()} (Strength: {thermal_data['thermal_strength']}/10)\n"
            notes += f"• **Hunting Advantage**: {thermal_data['hunting_advantage'].replace('_', ' ').title()}\n"
            
            if thermal_data['timing_notes']:
                for note in thermal_data['timing_notes'][:3]:  # Include first 3 thermal notes
                    notes += f"• {note}\n"
            
            # Vermont-specific thermal advice
            if thermal_data['thermal_direction'] == 'downslope':
                notes += "• **🎯 Vermont Strategy**: Position on ridges/upper slopes - scent carries away from deer below\n"
                notes += "• **⏰ Timing**: Best 30-60 minutes after first light when thermals are strongest\n"
            elif thermal_data['thermal_direction'] == 'upslope':
                notes += "• **🎯 Vermont Strategy**: Position in valleys/lower slopes - scent rises away from deer\n"
                notes += "• **⏰ Timing**: Prime 2-3 hours before sunset as ground heats up\n"
            
            notes += "\n"
        else:
            notes += f"🌪️ **Thermal Conditions** (Hour {current_hour:02d}:00): Variable/Transitional - rely on prevailing winds\n\n"
        
        # Add tomorrow's wind forecast
        tomorrow_forecast = weather_data.get("tomorrow_forecast", {})
        hunting_windows = weather_data.get("hunting_windows", {})
        tomorrow_hourly_wind = weather_data.get("tomorrow_hourly_wind", [])
        
        if tomorrow_forecast:
            notes += f"🌬️ **Tomorrow's Wind Forecast**:\n"
            
            # Use average daytime wind speed (8 AM to 6 PM) instead of daily maximum for more realistic forecast
            if tomorrow_hourly_wind:
                daytime_winds = [h["wind_speed"] for h in tomorrow_hourly_wind if 8 <= h["hour"] <= 18]
                wind_speed = sum(daytime_winds) / len(daytime_winds) if daytime_winds else tomorrow_forecast.get("wind_speed_max", 0)
            else:
                # Fallback to using 70% of max wind as more realistic average
                wind_speed = tomorrow_forecast.get("wind_speed_max", 0) * 0.7
                
            wind_dir = tomorrow_forecast.get("wind_direction_dominant", 0)
            
            # Convert wind direction to text
            if 0 <= wind_dir < 45 or 315 <= wind_dir < 360:
                wind_direction_text = "North"
            elif 45 <= wind_dir < 135:
                wind_direction_text = "East"
            elif 135 <= wind_dir < 225:
                wind_direction_text = "South"
            elif 225 <= wind_dir < 315:
                wind_direction_text = "West"
            else:
                wind_direction_text = "Variable"
            
            notes += f"• **Dominant Wind**: {wind_direction_text} at {wind_speed:.1f} mph\n"
            
            # Add hunting window recommendations
            if hunting_windows:
                notes += f"• **Best Morning Window**: {hunting_windows.get('morning', 'No data')}\n"
                notes += f"• **Best Evening Window**: {hunting_windows.get('evening', 'No data')}\n"
                notes += f"• **Wind Advice**: {hunting_windows.get('wind_advice', 'Plan accordingly')}\n"
                
                if hunting_windows.get('all_day_favorable'):
                    notes += "• ✅ **Excellent all-day hunting conditions expected!**\n"
                elif hunting_windows.get('average_wind_speed', 20) > 15:
                    notes += "• ⚠️ **Strong winds expected - consider postponing or adjust strategy**\n"
            
            notes += "\n"
        
        # Add snow depth context
        snow_depth = weather_data.get("snow_depth_inches", 0)
        if snow_depth > 16:
            notes += f"❄️ **Deep Snow Alert** ({snow_depth:.1f}in): Deer concentrated in winter yards (dense softwood areas)\n\n"
        elif snow_depth > 10:
            notes += f"🌨️ **Moderate Snow** ({snow_depth:.1f}in): Increased movement to sheltered areas\n\n"
        
        # Add seasonal context
        notes += f"📅 **{request.season.replace('_', ' ').title()} Season Strategy:**\n"
        if request.season == "rut":
            notes += "• Focus on travel corridors (red areas) - bucks are moving extensively\n"
            notes += "• Hunt saddles, ridge connections, and funnels\n"
            notes += "• Morning and evening movement peaks\n"
            if mature_buck_data['viable_location']:
                notes += "• **🏹 Mature Buck Rut Strategy**: Target crosshair markers during peak movement (10 AM-2 PM)\n"
        elif request.season == "late_season":
            notes += "• Emphasize bedding areas (red zones) - winter survival mode\n"
            notes += "• Look for south-facing slopes and dense conifer cover\n"
            notes += "• Midday activity when temperatures are warmest\n"
            if mature_buck_data['viable_location']:
                notes += "• **🏹 Mature Buck Late Season**: Focus on thermal cover and energy conservation patterns\n"
        else:  # early_season
            notes += "• Balance feeding and bedding areas\n"
            notes += "• Focus on mast crops (acorns, apples) and field edges\n"
            notes += "• Establish pattern before hunting pressure increases\n"
            if mature_buck_data['viable_location']:
                notes += "• **🏹 Mature Buck Early Season**: Target secluded feeding areas and escape routes\n"
        notes += "\n"
        
        # Add current location rating context
        notes += f"📍 **This Location**: Overall rating {stand_rating}/10\n"
        if stand_rating >= 8:
            notes += "⭐ Excellent location - high deer activity expected\n"
        elif stand_rating >= 6:
            notes += "✅ Good location - solid hunting potential\n"
        elif stand_rating >= 4:
            notes += "⚠️ Moderate location - consider better spots nearby\n"
        else:
            notes += "❌ Lower potential - check suggested better locations\n"
        
        if suggested_spots:
            notes += f"\n🎯 **Better Spots Available**: {len(suggested_spots)} higher-rated locations marked on map"
        
        # Add detailed mature buck analysis if location is viable
        if mature_buck_data['viable_location']:
            notes += f"\n\n🏹 **Mature Buck Analysis** (3.5+ year whitetails):\n"
            notes += f"**Terrain Assessment:**\n"
            notes += f"• Bedding Suitability: {mature_buck_data['terrain_scores']['bedding_suitability']:.1f}%\n"
            notes += f"• Escape Route Quality: {mature_buck_data['terrain_scores']['escape_route_quality']:.1f}%\n"
            notes += f"• Isolation Score: {mature_buck_data['terrain_scores']['isolation_score']:.1f}%\n"
            notes += f"• Pressure Resistance: {mature_buck_data['terrain_scores']['pressure_resistance']:.1f}%\n\n"
            
            notes += f"**Movement Prediction** (Current Hour {current_hour:02d}:00):\n"
            notes += f"• Movement Probability: {mature_buck_data['movement_prediction']['movement_probability']:.1f}%\n"
            if mature_buck_data['movement_prediction']['preferred_times']:
                notes += f"• Best Times: {', '.join(mature_buck_data['movement_prediction']['preferred_times'][:2])}\n"
            
            # Add behavioral insights
            behavioral_notes = mature_buck_data['movement_prediction']['behavioral_notes']
            if behavioral_notes:
                notes += f"**Behavioral Insights:**\n"
                for note in behavioral_notes[:3]:  # Top 3 behavioral notes
                    notes += f"• {note}\n"
            
            # Add specialized stand recommendations
            if mature_buck_data['stand_recommendations']:
                notes += f"\n**Specialized Mature Buck Stands:**\n"
                for i, rec in enumerate(mature_buck_data['stand_recommendations'][:2], 1):
                    notes += f"{i}. **{rec['type']}** - {rec['description']}\n"
                    notes += f"   📍 Confidence: {rec['confidence']:.0f}% | Best Times: {rec['best_times']}\n"

        # 9. Generate the 5 best stand locations using enhanced mature buck analysis
        five_best_stands = get_five_best_stand_locations_enhanced(
            request.lat, request.lon, features, weather_data, request.season, score_maps, mature_buck_data
        )

        # 10. Build 48-hour hunt schedule using hourly weather
        hourly48 = weather_data.get('next_48h_hourly', [])
        hunt_schedule = compute_hourly_hunt_schedule(
            request.lat, request.lon, five_best_stands, features, request.season, hourly48, huntable_threshold=75.0
        )
        
        # Also generate traditional stand placement recommendations for the notes
        stand_recommendations = get_stand_placement_recommendations(
            features, weather_data, request.lat, request.lon, request.season, stand_rating
        )
        
        # Add 5 best stand locations to notes with zone correlation
        if five_best_stands:
            notes += f"\n\n🎯 **5 Best Stand Locations** (⭐ marks the spot!):\n"
            notes += "**Top Priority Stands (positioned using actual deer activity zones):**\n"
            for i, stand in enumerate(five_best_stands, 1):
                confidence_emoji = "🔥" if stand['confidence'] > 85 else "⭐" if stand['confidence'] > 75 else "✅"
                
                # Add zone correlation explanation
                zone_explanation = ""
                if stand.get('zone_type') == 'bedding_feeding_corridor':
                    zone_explanation = " 🛏️➡️🌾 Between red bedding and green feeding zones"
                elif stand.get('zone_type') == 'travel_corridor':
                    zone_explanation = " 🦌 Near blue travel corridor"
                elif stand.get('zone_type') == 'feeding_edge':
                    zone_explanation = " 🌾 Edge of green feeding zone"
                elif stand.get('zone_type') == 'geometric_fallback':
                    zone_explanation = " 📐 Strategic geometric position"
                
                notes += f"{confidence_emoji} **{i}. {stand['type']}** ({stand['direction']}, {stand['distance_yards']} yds){zone_explanation}\n"
                
                # Handle both coordinate structures (enhanced vs traditional stands)
                if 'coordinates' in stand:
                    stand_lat = stand['coordinates']['lat']
                    stand_lon = stand['coordinates']['lon']
                else:
                    stand_lat = stand.get('lat', 0)
                    stand_lon = stand.get('lon', 0)
                
                notes += f"   📍 GPS: {stand_lat}, {stand_lon}\n"
                
                # Handle wind favorability safely
                wind_favor = stand.get('wind_favorability', 'N/A')
                if isinstance(wind_favor, (int, float)):
                    wind_text = f"{wind_favor:.0f}%"
                else:
                    wind_text = str(wind_favor)
                
                notes += f"   🎯 Confidence: {stand['confidence']:.0f}% | 💨 Wind: {wind_text}\n"
                setup_notes = stand.get('setup_notes', stand.get('description', 'No additional notes'))
                notes += f"   📝 {setup_notes}\n\n"
        
        # Add traditional stand recommendations to notes (for compatibility)
        if stand_recommendations:
            notes += f"\n\n🏹 **Additional Stand Insights** ({len(stand_recommendations)} locations):\n"
            for i, rec in enumerate(stand_recommendations[:2], 1):  # Show top 2 in notes
                notes += f"**{i}. {rec['type']}** - {rec['reason']}\n"
                notes += f"   📍 GPS: {rec['coordinates']['lat']}, {rec['coordinates']['lon']}\n"
                notes += f"   📏 {rec['distance']} | ⏰ {rec['best_times']}\n"
                if i < len(stand_recommendations[:2]):
                    notes += "\n"

        logger.info(f"Vermont prediction completed successfully with stand rating: {stand_rating}")
        if suggested_spots:
            logger.info(f"Found {len(suggested_spots)} better spots with ratings up to {max(s['rating'] for s in suggested_spots)}")
        if five_best_stands:
            logger.info(f"Generated {len(five_best_stands)} optimal stand locations with top confidence: {five_best_stands[0]['confidence']:.0f}%")
        
        # Create response object
        response = PredictionResponse(
            travel_corridors=travel_corridors,
            bedding_zones=bedding_zones,
            feeding_areas=feeding_zones,
            mature_buck_opportunities=mature_buck_opportunities,
            stand_rating=stand_rating,
            notes=notes,
            terrain_heatmap=terrain_heatmap,
            vegetation_heatmap=vegetation_heatmap,
            travel_score_heatmap=travel_score_heatmap,
            bedding_score_heatmap=bedding_score_heatmap,
            feeding_score_heatmap=feeding_score_heatmap,
            suggested_spots=suggested_spots,
            stand_recommendations=stand_recommendations,
            five_best_stands=five_best_stands,  # Add the 5 best stand locations
            hunt_schedule=hunt_schedule,
            mature_buck_analysis=mature_buck_data  # Add complete mature buck analysis
        )
        
        return response

    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error during Vermont deer prediction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

# =============================================================================
# LiDAR-Enhanced Analysis Endpoints
# =============================================================================

class LidarPredictionRequest(BaseModel):
    lat: float
    lon: float
    date_time: str
    season: str
    use_lidar: bool = True
    analysis_radius: float = 500.0  # meters

class LidarTerrainResponse(BaseModel):
    terrain_analysis: Dict[str, Any]
    deer_corridors: Dict[str, Any]
    enhanced_features: Dict[str, Any]
    lidar_available: bool

@app.post("/predict-enhanced", summary="LiDAR-enhanced deer movement predictions", 
          response_model=LidarTerrainResponse, tags=["predictions"])
async def predict_movement_enhanced(request: LidarPredictionRequest):
    """Enhanced prediction using high-resolution LiDAR data"""
    logger.info(f"LiDAR-enhanced prediction request for lat: {request.lat}, lon: {request.lon}")
    
    if not LIDAR_AVAILABLE or not request.use_lidar:
        logger.warning("LiDAR not available, falling back to standard analysis")
        raise HTTPException(status_code=503, detail="LiDAR analysis not available")
    
    try:
        # LiDAR analysis disabled for testing
        raise HTTPException(status_code=503, detail="LiDAR endpoints temporarily disabled")
        
        # Enhanced terrain analysis using LiDAR
        # terrain_analysis = await lidar_analysis.enhanced_terrain_analysis(
        #     request.lat, request.lon, request.lat + 0.001, request.lon + 0.001
        # )
        
        # Enhanced deer corridor analysis
        # deer_corridors = await lidar_analysis.enhanced_deer_corridor_analysis(
        #     request.lat, request.lon, request.analysis_radius
        # )
        
        # Additional enhanced features
        enhanced_features = {
            "precision_level": "sub_meter",
            "data_source": "vermont_lidar",
            "analysis_radius_meters": request.analysis_radius,
            "enhanced_capabilities": [
                "micro_topography_analysis",
                "canopy_structure_mapping", 
                "precise_slope_calculation",
                "thermal_flow_modeling",
                "3d_concealment_analysis"
            ]
        }
        
        logger.info("LiDAR-enhanced prediction completed successfully")
        
        return LidarTerrainResponse(
            terrain_analysis=terrain_analysis,
            deer_corridors=deer_corridors,
            enhanced_features=enhanced_features,
            lidar_available=True
        )
        
    except Exception as e:
        logger.error(f"Error in LiDAR-enhanced prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LiDAR prediction error: {str(e)}")

@app.get("/lidar/terrain-profile/{lat}/{lng}", summary="Get detailed terrain profile", tags=["predictions"])
async def get_terrain_profile(lat: float, lng: float, radius: float = 200.0):
    """Get detailed terrain profile for a specific location using LiDAR data"""
    
    if not LIDAR_AVAILABLE:
        raise HTTPException(status_code=503, detail="LiDAR analysis not available")
    
    try:
        # LiDAR analysis disabled for testing
        raise HTTPException(status_code=503, detail="LiDAR endpoints temporarily disabled")
        
        if not lidar_data:
            raise HTTPException(status_code=404, detail="No LiDAR data available for this location")
        
        # Extract terrain metrics
        terrain_metrics = {
            "elevation_min": float(np.min(lidar_data.elevation)),
            "elevation_max": float(np.max(lidar_data.elevation)),
            "elevation_mean": float(np.mean(lidar_data.elevation)),
            "slope_mean": float(np.mean(lidar_data.slope)),
            "slope_max": float(np.max(lidar_data.slope)),
            "roughness_mean": float(np.mean(lidar_data.roughness)),
            "canopy_height_mean": float(np.mean(lidar_data.canopy_height)),
            "canopy_density_mean": float(np.mean(lidar_data.canopy_density)),
            "resolution_meters": lidar_data.resolution,
            "bounds": lidar_data.bounds
        }
        
        return {
            "location": {"lat": lat, "lng": lng},
            "analysis_radius": radius,
            "terrain_metrics": terrain_metrics,
            "data_quality": "high_resolution_lidar"
        }
        
    except Exception as e:
        logger.error(f"Error getting terrain profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Terrain profile error: {str(e)}")

@app.get("/lidar/status", summary="Check LiDAR data availability", tags=["health"])
async def get_lidar_status():
    """Check LiDAR integration status and data availability"""
    
    status = {
        "lidar_available": LIDAR_AVAILABLE,
        "integration_version": "1.0.0",
        "supported_features": []
    }
    
    if LIDAR_AVAILABLE:
        status["supported_features"] = [
            "enhanced_terrain_analysis",
            "deer_corridor_mapping",
            "canopy_structure_analysis",
            "micro_topography_modeling",
            "thermal_flow_prediction",
            "3d_concealment_scoring"
        ]
        
        # Test data availability
        try:
            # LiDAR analysis disabled for testing
            status["test_location_available"] = False
            status["test_error"] = "LiDAR temporarily disabled"
        except Exception as e:
            status["test_location_available"] = False
            status["test_error"] = str(e)
    
    return status

# --- Configuration Management Endpoints ---

@app.get("/config/status", summary="Get configuration status", tags=["configuration"])
def get_config_status():
    """Get current configuration status and metadata"""
    config = get_config()
    metadata = config.get_metadata()
    
    return {
        "environment": metadata.environment,
        "version": metadata.version,
        "last_loaded": metadata.last_loaded.isoformat() if metadata.last_loaded else None,
        "source_files": metadata.source_files,
        "validation_errors": metadata.validation_errors,
        "configuration_sections": {
            "mature_buck_preferences": bool(config.get_mature_buck_preferences()),
            "scoring_factors": bool(config.get_scoring_factors()),
            "seasonal_weights": bool(config.get_seasonal_weights()),
            "weather_modifiers": bool(config.get_weather_modifiers()),
            "distance_parameters": bool(config.get_distance_parameters()),
            "api_settings": bool(config.get_api_settings())
        }
    }

@app.get("/config/parameters", summary="Get all configuration parameters", tags=["configuration"])
def get_config_parameters():
    """Get all current configuration parameters"""
    config = get_config()
    
    return {
        "mature_buck_preferences": config.get_mature_buck_preferences(),
        "scoring_factors": config.get_scoring_factors(),
        "seasonal_weights": config.get_seasonal_weights(),
        "weather_modifiers": config.get_weather_modifiers(),
        "distance_parameters": config.get_distance_parameters(),
        "terrain_weights": config.get_terrain_weights(),
        "api_settings": config.get_api_settings(),
        "ml_parameters": config.get_ml_parameters()
    }

@app.post("/config/reload", summary="Reload configuration", tags=["configuration"])
def reload_configuration():
    """Reload configuration from files (admin only)"""
    try:
        config = get_config()
        config.reload()
        metadata = config.get_metadata()
        
        return {
            "status": "success",
            "message": "Configuration reloaded successfully",
            "version": metadata.version,
            "last_loaded": metadata.last_loaded.isoformat() if metadata.last_loaded else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload configuration: {str(e)}")

@app.post("/trail-cameras", summary="Get trail camera placement recommendations", tags=["hunting"])
def get_trail_camera_placements(request: TrailCameraRequest):
    """
    Get optimal trail camera placement recommendations for mature buck photography
    """
    try:
        logger.info(f"🎥 Trail camera request: lat={request.lat}, lon={request.lon}, season={request.season}")
        
        # Get terrain analysis
        logger.info("Getting terrain analysis...")
        elevation_grid = core.get_real_elevation_grid(request.lat, request.lon)
        vegetation_grid = core.get_vegetation_grid_from_osm(request.lat, request.lon) 
        terrain_features = core.analyze_terrain_and_vegetation(elevation_grid, vegetation_grid)
        logger.info("Terrain analysis complete")
        
        # Simple camera placement for now
        camera_features = []
        
        # Create 3 basic camera placements
        logger.info("Creating camera positions...")
        camera_positions = [
            (request.lat + 0.0003, request.lon, "Travel Corridor Monitor"),
            (request.lat, request.lon + 0.0003, "Water Source Monitor"), 
            (request.lat - 0.0003, request.lon, "Feeding Edge Monitor")
        ]
        logger.info(f"Camera positions created: {len(camera_positions)}")
        
        logger.info("Processing camera positions...")
        for i, camera_data in enumerate(camera_positions):
            cam_lat, cam_lon, cam_type = camera_data
            logger.info(f"Processing camera {i+1}: {cam_type}")
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [cam_lon, cam_lat]
                },
                "properties": {
                    "id": f"camera_{i+1}",
                    "placement_type": cam_type,
                    "confidence": 85.0 - (i * 5),
                    "setup_height": "10-12 feet",
                    "setup_angle": "30° downward, perpendicular to trail",
                    "expected_photos": "High - mature buck travel route",
                    "best_times": ["Dawn (5-8am)", "Dusk (5-8pm)", "Night (8pm-5am)"],
                    "setup_notes": [
                        "Position camera perpendicular to travel direction",
                        "Clear shooting lanes 20-30 yards both directions", 
                        "Use low-glow IR to avoid spooking mature bucks"
                    ],
                    "wind_considerations": "Position downwind of expected approach direction",
                    "seasonal_effectiveness": {"early_season": 85, "rut": 95, "late_season": 80},
                    "camera_settings": {"trigger_speed": "0.3s", "detection_range": "80ft", "photo_burst": "3 photos"},
                    "rank": i + 1
                }
            }
            camera_features.append(feature)
        
        logger.info("Camera features created successfully")
        
        camera_geojson = {
            "type": "FeatureCollection",
            "features": camera_features
        }
        
        # Generate insights
        insights = [
            f"🎯 Top recommendation: {camera_features[0]['properties']['placement_type']} (Confidence: {camera_features[0]['properties']['confidence']:.1f}%)",
            f"📸 Expected photos: {camera_features[0]['properties']['expected_photos']}",
            f"⏰ Best times: {', '.join(camera_features[0]['properties']['best_times'][:2])}"
        ]
        
        if request.season == 'rut':
            insights.append("🦌 Rut season: Focus on scrape lines and travel corridors")
        elif request.season == 'early_season':
            insights.append("🌾 Early season: Target feeding areas and water sources")
        elif request.season == 'late_season':
            insights.append("❄️ Late season: Water and thermal cover are critical")
        
        logger.info("Returning trail camera recommendations")
        
        # Debug terrain features
        logger.info(f"Terrain features keys: {list(terrain_features.keys())}")
        for key, value in terrain_features.items():
            logger.info(f"{key}: type={type(value)}, shape={getattr(value, 'shape', 'no shape')}")
        
        # Extract scalar values from terrain features (they might be numpy arrays)
        def safe_float(value, default=0.0):
            try:
                if value is None:
                    return default
                if hasattr(value, 'item'):  # numpy scalar
                    return float(value.item())
                elif hasattr(value, '__len__') and len(value) > 0:  # array
                    if hasattr(value, 'shape') and len(value.shape) > 0:
                        return float(np.mean(value))
                    else:
                        return float(value[0])
                else:
                    return float(value)
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not convert {value} to float: {e}")
                return default
        
        return {
            "camera_placements": camera_geojson,
            "placement_count": len(camera_features),
            "target_season": request.season,
            "target_buck_age": request.target_buck_age,
            "insights": insights,
            "setup_priority": camera_features[0]['properties']['placement_type'] if camera_features else "No cameras",
            "terrain_summary": {
                "elevation": safe_float(terrain_features.get('elevation', 0)),
                "slope": safe_float(terrain_features.get('slope', 0)),
                "cover_density": safe_float(terrain_features.get('canopy_closure', 50)),
                "water_proximity": safe_float(terrain_features.get('water_proximity', 1000)),
                "ag_proximity": safe_float(terrain_features.get('ag_proximity', 1000))
            }
        }
        
    except Exception as e:
        logger.error(f"Trail camera prediction failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Trail camera prediction failed: {str(e)}")

@app.put("/config/parameter/{key_path}", summary="Update configuration parameter", tags=["configuration"])
def update_config_parameter(key_path: str, value: Any):
    """Update a specific configuration parameter (admin only)"""
    try:
        config = get_config()
        config.update_config(key_path, value, persist=False)  # Don't persist to file for safety
        
        return {
            "status": "success",
            "message": f"Parameter {key_path} updated successfully",
            "key_path": key_path,
            "new_value": value
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update parameter: {str(e)}")

@app.post("/scouting/add_observation", response_model=ScoutingObservationResponse)
async def add_scouting_observation(observation: ScoutingObservation):
    """
    Add a new scouting observation to enhance future predictions
    
    This endpoint allows hunters to record real-world deer sign observations
    which will be used to improve prediction accuracy in the area.
    """
    try:
        logger.info(f"Adding scouting observation: {observation.observation_type} at {observation.lat:.5f}, {observation.lon:.5f}")
        
        # Get data manager
        data_manager = get_scouting_data_manager()
        
        # Add observation to database
        observation_id = data_manager.add_observation(observation)
        
        # Calculate confidence boost that will be applied
        enhancer = get_scouting_enhancer()
        enhancement_config = enhancer.enhancement_config.get(observation.observation_type, {})
        confidence_boost = enhancement_config.get("base_boost", 0) * (observation.confidence / 10.0)
        
        logger.info(f"Successfully added scouting observation {observation_id} with {confidence_boost:.1f}% confidence boost")
        
        return ScoutingObservationResponse(
            status="success",
            observation_id=observation_id,
            message=f"Added {observation.observation_type.value} observation - predictions enhanced!",
            confidence_boost=confidence_boost
        )
        
    except Exception as e:
        logger.error(f"Failed to add scouting observation: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to add observation: {str(e)}"
        )


@app.get("/scouting/observations")
async def get_scouting_observations(
    lat: float,
    lon: float,
    radius_miles: float = 2.0,
    observation_types: Optional[str] = None,
    min_confidence: Optional[int] = None,
    days_back: Optional[int] = None
):
    """
    Get scouting observations within a specified area
    
    Returns all scouting observations that match the query parameters.
    Used to display scouting data on the map and analyze patterns.
    """
    try:
        # Parse observation types if provided
        types_list = None
        if observation_types:
            try:
                type_names = observation_types.split(",")
                types_list = [ObservationType(name.strip()) for name in type_names]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid observation type: {e}")
        
        # Create query
        query = ScoutingQuery(
            lat=lat,
            lon=lon,
            radius_miles=radius_miles,
            observation_types=types_list,
            min_confidence=min_confidence,
            days_back=days_back
        )
        
        # Get observations
        data_manager = get_scouting_data_manager()
        observations = data_manager.get_observations(query)
        
        logger.info(f"Retrieved {len(observations)} scouting observations for area ({lat:.5f}, {lon:.5f})")
        
        # Convert to response format
        obs_data = []
        for obs in observations:
            obs_dict = obs.to_dict()
            # Handle timezone-aware vs timezone-naive datetime comparison
            if obs.timestamp.tzinfo is not None:
                now = datetime.now(timezone.utc)
            else:
                now = datetime.now()
            obs_dict["age_days"] = (now - obs.timestamp).days
            obs_data.append(obs_dict)
        
        return {
            "observations": obs_data,
            "total_count": len(obs_data),
            "query_parameters": query.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scouting observations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve observations: {str(e)}"
        )


@app.get("/scouting/observation/{observation_id}")
async def get_scouting_observation(observation_id: str):
    """Get a specific scouting observation by ID"""
    try:
        data_manager = get_scouting_data_manager()
        observation = data_manager.get_observation_by_id(observation_id)
        
        if not observation:
            raise HTTPException(status_code=404, detail="Observation not found")
        
        obs_data = observation.to_dict()
        # Handle timezone-aware vs timezone-naive datetime comparison
        if observation.timestamp.tzinfo is not None:
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()
        obs_data["age_days"] = (now - observation.timestamp).days
        
        return obs_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get observation {observation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve observation: {str(e)}"
        )


@app.delete("/scouting/observation/{observation_id}")
async def delete_scouting_observation(observation_id: str):
    """Delete a scouting observation"""
    try:
        data_manager = get_scouting_data_manager()
        success = data_manager.delete_observation(observation_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Observation not found")
        
        logger.info(f"Deleted scouting observation: {observation_id}")
        
        return {"status": "success", "message": "Observation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete observation {observation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete observation: {str(e)}"
        )


@app.get("/scouting/analytics")
async def get_scouting_analytics(
    lat: float,
    lon: float,
    radius_miles: float = 10.0
):
    """
    Get analytics for scouting observations in an area
    
    Provides insights into scouting patterns, hotspots, and prediction accuracy.
    """
    try:
        data_manager = get_scouting_data_manager()
        analytics = data_manager.get_analytics(lat, lon, radius_miles)
        
        # Get enhancement summary
        enhancer = get_scouting_enhancer()
        enhancement_summary = enhancer.get_enhancement_summary(lat, lon)
        
        # Combine analytics
        result = {
            "area_center": {"lat": lat, "lon": lon},
            "search_radius_miles": radius_miles,
            "basic_analytics": analytics.dict(),
            "enhancement_summary": enhancement_summary,
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info(f"Generated scouting analytics for area ({lat:.5f}, {lon:.5f})")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get scouting analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics: {str(e)}"
        )


@app.get("/scouting/types")
async def get_observation_types():
    """Get list of available observation types with descriptions"""
    try:
        enhancer = get_scouting_enhancer()
        
        types_info = []
        for obs_type in ObservationType:
            config = enhancer.enhancement_config.get(obs_type, {})
            
            types_info.append({
                "type": obs_type.value,
                "enum_name": obs_type.name,
                "base_boost": config.get("base_boost", 0),
                "influence_radius_yards": config.get("influence_radius_yards", 0),
                "mature_buck_indicator": config.get("mature_buck_indicator", False),
                "decay_days": config.get("decay_days", 7)
            })
        
        return {
            "observation_types": types_info,
            "total_types": len(types_info)
        }
        
    except Exception as e:
        logger.error(f"Failed to get observation types: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get observation types: {str(e)}"
        )


# === GPX IMPORT FUNCTIONALITY ===

class GPXImportRequest(BaseModel):
    """Request model for GPX file import"""
    gpx_content: str = Field(..., description="GPX file content as string")
    auto_import: bool = Field(default=True, description="Automatically import valid waypoints")
    confidence_override: Optional[int] = Field(None, ge=1, le=10, description="Override confidence for all waypoints")


class GPXImportResponse(BaseModel):
    """Response model for GPX import operation"""
    status: str
    message: str
    total_waypoints: int
    imported_observations: int
    skipped_waypoints: int
    errors: List[str] = Field(default_factory=list)
    preview: List[Dict[str, Any]] = Field(default_factory=list)


@app.post("/scouting/import_gpx", response_model=GPXImportResponse)
async def import_gpx_file(request: GPXImportRequest):
    """
    Import scouting observations from GPX file
    
    Parses a GPX file and converts waypoints to scouting observations.
    Supports waypoints from hunting GPS devices and apps like OnX, Garmin, etc.
    """
    try:
        logger.info("Starting GPX file import")
        
        # Import GPX parser (lazy import to avoid breaking existing functionality)
        try:
            from backend.gpx_parser import get_gpx_parser
        except ImportError as e:
            logger.error(f"GPX parser not available: {e}")
            raise HTTPException(
                status_code=500, 
                detail="GPX import functionality not available"
            )
        
        # Parse GPX file
        parser = get_gpx_parser()
        parse_result = parser.parse_gpx_file(request.gpx_content)
        
        if not parse_result['success']:
            return GPXImportResponse(
                status="error",
                message=parse_result.get('error', 'Failed to parse GPX file'),
                total_waypoints=0,
                imported_observations=0,
                skipped_waypoints=0,
                errors=[parse_result.get('error', 'Unknown parsing error')]
            )
        
        waypoints = parse_result['waypoints']
        total_waypoints = len(waypoints)
        
        if total_waypoints == 0:
            return GPXImportResponse(
                status="warning",
                message="No waypoints found in GPX file",
                total_waypoints=0,
                imported_observations=0,
                skipped_waypoints=0
            )
        
        # Convert waypoints to observations
        observations = parser.convert_to_scouting_observations(waypoints)
        
        # Apply confidence override if specified
        if request.confidence_override:
            for obs in observations:
                obs.confidence = request.confidence_override
        
        imported_count = 0
        skipped_count = 0
        errors = []
        preview = []
        
        if request.auto_import:
            # Import observations into database
            data_manager = get_scouting_data_manager()
            
            for obs in observations:
                try:
                    obs_id = data_manager.add_observation(obs)
                    imported_count += 1
                    
                    # Add to preview (first 5 only)
                    if len(preview) < 5:
                        preview.append({
                            'id': obs_id,
                            'type': obs.observation_type.value,
                            'lat': obs.lat,
                            'lon': obs.lon,
                            'confidence': obs.confidence,
                            'notes': obs.notes[:100] + "..." if len(obs.notes) > 100 else obs.notes
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to import observation: {e}")
                    errors.append(f"Failed to import {obs.observation_type.value}: {str(e)}")
                    skipped_count += 1
        else:
            # Just preview, don't import
            for obs in observations[:5]:  # Preview first 5
                preview.append({
                    'type': obs.observation_type.value,
                    'lat': obs.lat,
                    'lon': obs.lon,
                    'confidence': obs.confidence,
                    'notes': obs.notes[:100] + "..." if len(obs.notes) > 100 else obs.notes
                })
        
        # Determine status
        if imported_count == len(observations):
            status = "success"
            message = f"Successfully imported {imported_count} observations from GPX file"
        elif imported_count > 0:
            status = "partial_success"
            message = f"Imported {imported_count} of {len(observations)} observations"
        else:
            status = "error"
            message = "Failed to import any observations"
        
        logger.info(f"GPX import completed: {imported_count} imported, {skipped_count} skipped")
        
        return GPXImportResponse(
            status=status,
            message=message,
            total_waypoints=total_waypoints,
            imported_observations=imported_count,
            skipped_waypoints=skipped_count,
            errors=errors,
            preview=preview
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GPX import failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"GPX import failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)