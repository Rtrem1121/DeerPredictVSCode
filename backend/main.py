from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Any
from . import core

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
    suggestion_threshold: float = 5.0  # Show suggestions when rating is below this
    min_suggestion_rating: float = 8.0  # Minimum rating for suggestions

class PredictionResponse(BaseModel):
    travel_corridors: Dict[str, Any]
    bedding_zones: Dict[str, Any]
    feeding_areas: Dict[str, Any]
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
        return {
            "status": "healthy",
            "version": "0.3.0",
            "rules_loaded": len(rules),
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
            # Convert grid position to GPS coordinates
            lat = center_lat + 0.02 - (row / size) * 0.04
            lon = center_lon - 0.02 + (col / size) * 0.04

            # Add slight deterministic jitter (~<=50m) to avoid alignments while ensuring repeatability
            # 1 degree lat ~= 111_000m; 50m ~= 0.00045 deg
            rng_seed = int((row * 73856093) ^ (col * 19349663)) & 0xFFFFFFFF
            rng = np.random.RandomState(rng_seed)
            jitter_lat = (rng.rand() - 0.5) * 2 * 0.0003  # ~<=33m
            jitter_lon = (rng.rand() - 0.5) * 2 * 0.0003
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
    
    # Collect unique access points (we want only 1-2 total for the entire hunting area)
    access_points_found = []
    
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
        
        # Add access point information to the route analysis
        access_route['access_point'] = nearest_access
        
        # Collect unique access points (avoid duplicates within ~100 yards)
        access_point_key = f"{round(nearest_access['lat'], 4)}_{round(nearest_access['lon'], 4)}"
        is_duplicate = False
        for existing_access in access_points_found:
            if abs(existing_access['lat'] - nearest_access['lat']) < 0.001 and \
               abs(existing_access['lon'] - nearest_access['lon']) < 0.001:
                is_duplicate = True
                break
        
        if not is_duplicate and len(access_points_found) < 2:  # Limit to max 2 access points
            access_points_found.append({
                'lat': round(nearest_access['lat'], 6),
                'lon': round(nearest_access['lon'], 6),
                'access_type': nearest_access['access_type'],
                'distance_miles': nearest_access['distance_miles'],
                'estimated_drive_time': nearest_access['estimated_drive_time'],
                'serves_stands': [i+1]  # Track which stands this access point serves
            })
        else:
            # Update existing access point to show it serves this stand too
            for existing_access in access_points_found:
                if abs(existing_access['lat'] - nearest_access['lat']) < 0.001 and \
                   abs(existing_access['lon'] - nearest_access['lon']) < 0.001:
                    existing_access['serves_stands'].append(i+1)
                    break
        
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
            'distance_yards': round(actual_distance * 111000 * 1.094, 0),  # Convert to yards
            'direction': get_compass_direction(actual_direction),
            'priority': pattern['priority'],
            'confidence': confidence,
            'setup_notes': setup_notes,
            'wind_favorability': calculate_combined_wind_favorability(actual_direction, wind_direction, thermal_data, terrain_features),
            'thermal_advantage': thermal_data['hunting_advantage'] if thermal_data['is_thermal_active'] else None,
            'access_route': access_route,
            'marker_symbol': 'X',  # X marks the spot!
            'zone_type': pattern.get('type', 'geometric'),
            'zone_reasoning': pattern.get('reasoning', 'Standard geometric positioning')
        }
        
        stand_locations.append(stand_location)
    
    # Sort by confidence score (highest first)
    stand_locations.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Add unique access points to the return data
    for i, stand in enumerate(stand_locations):
        stand['unique_access_points'] = access_points_found
    
    return stand_locations


def score_wind_favorability(stand_bearing: float, wind_direction: float) -> float:
    """Basic wind favorability (0-100) for use in scheduling."""
    angle_diff = abs(stand_bearing - wind_direction)
    if angle_diff > 180:
        angle_diff = 360 - angle_diff
    if angle_diff <= 30:
        return 90
    if angle_diff <= 60:
        return 75
    if angle_diff <= 90:
        return 60
    if angle_diff <= 120:
        return 40
    return 25


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
    base_confidence = 70  # Start with base confidence
    
    # Distance factor (closer is generally better for bow hunting)
    if pattern['distance'] < 0.0006:  # Under 100 yards
        base_confidence += 10
    elif pattern['distance'] > 0.001:  # Over 150 yards
        base_confidence -= 5
    
    # Combined wind and thermal favorability
    wind_thermal_score = calculate_combined_wind_favorability(pattern['direction'], wind_direction, thermal_data, terrain_features)
    base_confidence += (wind_thermal_score - 50) * 0.4  # Enhanced weight for thermal effects
    
    # Terrain features bonus
    if terrain_features.get('saddles') and 270 <= pattern['direction'] <= 90:
        base_confidence += 15  # Good saddle coverage
    if terrain_features.get('ridges') and pattern['direction'] in [0, 45, 315]:
        base_confidence += 10  # Ridge approach coverage
    
    # Thermal-specific bonuses
    if thermal_data['is_thermal_active']:
        if thermal_data['hunting_advantage'] == 'MORNING_RIDGE':
            # Morning ridge hunting bonus for upper elevation stands
            if pattern['direction'] in [0, 45, 315] and terrain_features.get('ridges'):
                base_confidence += 12
        elif thermal_data['hunting_advantage'] == 'EVENING_VALLEY':
            # Evening valley hunting bonus for lower elevation stands
            if pattern['direction'] in [135, 180, 225] and terrain_features.get('valleys'):
                base_confidence += 12
        
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
    """Calculate confidence score for stand placement (0-100)"""
    base_confidence = 70  # Start with base confidence
    
    # Distance factor (closer is generally better for bow hunting)
    if pattern['distance'] < 0.0006:  # Under 100 yards
        base_confidence += 10
    elif pattern['distance'] > 0.001:  # Over 150 yards
        base_confidence -= 5
    
    # Wind favorability
    wind_score = calculate_wind_favorability(pattern['direction'], wind_direction)
    base_confidence += (wind_score - 50) * 0.3  # Adjust based on wind
    
    # Terrain features bonus
    if terrain_features.get('saddles') and 270 <= pattern['direction'] <= 90:
        base_confidence += 15  # Good saddle coverage
    if terrain_features.get('ridges') and pattern['direction'] in [0, 45, 315]:
        base_confidence += 10  # Ridge approach coverage
    
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
    """Calculate overall stealth score for access route (0-100, higher is better)"""
    
    # Base score from concealment
    concealment_score = terrain_analysis['concealment_score']
    
    # Wind/thermal score
    scent_score = wind_impact['combined_scent_score']
    
    # Deer disturbance penalty
    disturbance_penalty = deer_zones['disturbance_score']
    
    # Distance factor (longer routes are riskier)
    if distance_yards <= 200:
        distance_score = 90
    elif distance_yards <= 400:
        distance_score = 80
    elif distance_yards <= 600:
        distance_score = 70
    else:
        distance_score = 60
    
    # Noise factor
    noise_scores = {'very_low': 90, 'low': 80, 'moderate': 60, 'high': 40}
    noise_score = noise_scores.get(terrain_analysis['noise_level'], 50)
    
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

def create_simple_geojson_features(markers: Dict) -> Dict:
    """Convert simple markers to GeoJSON format for the frontend"""
    
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
    
    return {
        "bedding_zones": {"type": "FeatureCollection", "features": bedding_features},
        "feeding_areas": {"type": "FeatureCollection", "features": feeding_features},
        "travel_corridors": {"type": "FeatureCollection", "features": travel_features}
    }

@app.post("/predict", summary="Generate deer movement predictions", response_model=PredictionResponse, tags=["predictions"])
def predict_movement(request: PredictionRequest):
    logger.info(f"Received prediction request for lat: {request.lat}, lon: {request.lon}, season: {request.season}")
    try:
        # Extract hour from request for thermal calculations
        request_datetime = datetime.fromisoformat(request.date_time.replace('Z', '+00:00'))
        current_hour = request_datetime.hour
        
        # 1. Load rules and fetch REAL environmental data with Vermont-specific weather
        rules = load_rules()
        weather_data = core.get_weather_data(request.lat, request.lon)
        
        # Add hour information for thermal calculations
        weather_data['hour'] = current_hour
        
        elevation_grid = core.get_real_elevation_grid(request.lat, request.lon)
        vegetation_grid = core.get_vegetation_grid_from_osm(request.lat, request.lon)
        road_proximity = core.get_road_proximity_grid(request.lat, request.lon)

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

        # 4. Generate data-driven markers from score maps (top-N points per behavior)
        markers = generate_simple_markers(score_maps, request.lat, request.lon)
        geojson_features = create_simple_geojson_features(markers)
        travel_corridors = geojson_features["travel_corridors"]
        bedding_zones = geojson_features["bedding_zones"]
        feeding_zones = geojson_features["feeding_areas"]
        logger.info(
            "Generated data-driven markers: travel=%d, bedding=%d, feeding=%d",
            len(travel_corridors.get('features', [])),
            len(bedding_zones.get('features', [])),
            len(feeding_zones.get('features', [])),
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
            description="Red = High movement probability, Blue = Low movement",
            cmap='RdYlBu_r'
        )
        bedding_score_heatmap = core.create_enhanced_score_heatmap(
            score_maps['bedding'], 
            title="Deer Bedding Areas", 
            description="Red = High bedding probability, Blue = Low bedding",
            cmap='RdYlBu_r'
        )
        feeding_score_heatmap = core.create_enhanced_score_heatmap(
            score_maps['feeding'], 
            title="Deer Feeding Areas", 
            description="Red = High feeding probability, Blue = Low feeding",
            cmap='RdYlBu_r'
        )

        # 8. Create enhanced notes with Vermont-specific context and heatmap explanations
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
        notes += f"• **🎯 Stand Locations (⭐)**: Star markers positioned strategically to intercept deer moving between activity areas\n\n"
        
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
            notes += "• Morning and evening movement peaks\n\n"
        elif request.season == "late_season":
            notes += "• Emphasize bedding areas (red zones) - winter survival mode\n"
            notes += "• Look for south-facing slopes and dense conifer cover\n"
            notes += "• Midday activity when temperatures are warmest\n\n"
        else:  # early_season
            notes += "• Balance feeding and bedding areas\n"
            notes += "• Focus on mast crops (acorns, apples) and field edges\n"
            notes += "• Establish pattern before hunting pressure increases\n\n"
        
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

        # 9. Generate the 5 best stand locations around the prediction point using actual score maps
        five_best_stands = get_five_best_stand_locations(
            request.lat, request.lon, features, weather_data, request.season, score_maps
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
                notes += f"   📍 GPS: {stand['coordinates']['lat']}, {stand['coordinates']['lon']}\n"
                notes += f"   🎯 Confidence: {stand['confidence']:.0f}% | 💨 Wind: {stand['wind_favorability']:.0f}%\n"
                notes += f"   📝 {stand['setup_notes']}\n\n"
        
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
        
        return PredictionResponse(
            travel_corridors=travel_corridors,
            bedding_zones=bedding_zones,
            feeding_areas=feeding_zones,
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
            hunt_schedule=hunt_schedule
        )

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