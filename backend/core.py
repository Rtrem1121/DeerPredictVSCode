import requests
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
import numpy as np
import networkx as nx
from shapely.geometry import Point, Polygon, LineString, shape
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.spatial import ConvexHull
from scipy.ndimage import convolve, laplace, gaussian_filter

# Configure logging
logger = logging.getLogger(__name__)

# --- Environment & Constants ---
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
GRID_SIZE = 10 # The resolution of our analysis grid

# --- Real Data Fetching ---
def get_weather_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Enhanced weather data fetching with Vermont-specific condition detection.
    Includes snow depth, barometric pressure, wind analysis, and tomorrow's forecast.
    """
    try:
        # Get current weather conditions and tomorrow's forecast
        weather_url = f"https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation,snowfall,snow_depth,pressure_msl,wind_speed_10m,wind_direction_10m",
            "hourly": "pressure_msl,wind_speed_10m,wind_direction_10m,temperature_2m",
            "daily": "wind_speed_10m_max,wind_direction_10m_dominant,temperature_2m_max,temperature_2m_min",
            "forecast_days": 3,  # Current + next 2 days
            "timezone": "America/New_York"  # Vermont timezone
        }
        
        response = requests.get(weather_url, params=params)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            hourly = data.get("hourly", {})
            daily = data.get("daily", {})
            
            # Extract current conditions
            temp = current.get("temperature_2m", 0)
            snow_depth = current.get("snow_depth", 0)
            pressure = current.get("pressure_msl", 1013.25)
            wind_speed = current.get("wind_speed_10m", 0)
            wind_direction = current.get("wind_direction_10m", 0)
            
            # Extract tomorrow's wind forecast
            tomorrow_forecast = {}
            if daily and len(daily.get("wind_speed_10m_max", [])) > 1:
                tomorrow_forecast = {
                    "wind_speed_max": daily["wind_speed_10m_max"][1],  # Tomorrow's max wind
                    "wind_direction_dominant": daily["wind_direction_10m_dominant"][1],  # Tomorrow's dominant direction
                    "temperature_max": daily["temperature_2m_max"][1],
                    "temperature_min": daily["temperature_2m_min"][1]
                }
            
            # Get hourly wind forecast for tomorrow (next 24 hours)
            tomorrow_hourly_wind = []
            if hourly and len(hourly.get("wind_speed_10m", [])) >= 24:
                for i in range(24, min(48, len(hourly["wind_speed_10m"]))):  # Hours 24-47 (tomorrow)
                    tomorrow_hourly_wind.append({
                        "hour": i - 24,  # 0-23 representing tomorrow's hours
                        "wind_speed": hourly["wind_speed_10m"][i],
                        "wind_direction": hourly["wind_direction_10m"][i] if i < len(hourly["wind_direction_10m"]) else 0
                    })
            
            # Calculate best hunting windows based on tomorrow's wind
            hunting_windows = calculate_wind_hunting_windows(tomorrow_hourly_wind)
            
            # Detect Vermont-specific weather patterns
            conditions = []
            
            # Snow conditions
            if snow_depth > 25.4:  # >10 inches
                conditions.append("heavy_snow")
            if snow_depth > 40.6:  # >16 inches
                conditions.append("deep_snow")
            if snow_depth > 10.2:  # >4 inches
                conditions.append("moderate_snow")
            
            # Barometric pressure trends (cold front detection)
            if len(hourly.get("pressure_msl", [])) > 3:
                recent_pressures = hourly["pressure_msl"][:4]
                pressure_drop = recent_pressures[0] - recent_pressures[-1]
                if pressure_drop > 3:  # Significant pressure drop
                    conditions.append("cold_front")
            
            # Wind conditions
            if wind_speed > 20:  # mph
                conditions.append("strong_wind")
            
            # Temperature-based conditions
            if temp > 25:  # Hot for Vermont
                conditions.append("hot")
            
            # Determine prevailing wind direction (northwest is common in Vermont)
            leeward_aspects = []
            if 270 <= wind_direction <= 360 or 0 <= wind_direction <= 90:  # NW winds
                leeward_aspects = ["southeast", "south"]
            
            return {
                "temperature": temp,
                "snow_depth_cm": snow_depth,
                "snow_depth_inches": snow_depth / 2.54,
                "pressure": pressure,
                "wind_speed": wind_speed,
                "wind_direction": wind_direction,
                "conditions": conditions,
                "leeward_aspects": leeward_aspects,
                "tomorrow_forecast": tomorrow_forecast,
                "tomorrow_hourly_wind": tomorrow_hourly_wind,
                "hunting_windows": hunting_windows,
                "raw_data": current
            }
        
        else:
            logger.warning(f"Weather API returned status {response.status_code}")
            return {
                "temperature": 10,
                "snow_depth_cm": 0,
                "snow_depth_inches": 0,
                "pressure": 1013.25,
                "wind_speed": 5,
                "wind_direction": 270,
                "conditions": [],
                "leeward_aspects": ["southeast", "south"],
                "tomorrow_forecast": {},
                "tomorrow_hourly_wind": [],
                "hunting_windows": {"morning": "No data", "evening": "No data", "all_day": "No data"},
                "raw_data": {}
            }
    
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        # Return default Vermont winter conditions
        return {
            "temperature": 10,
            "snow_depth_cm": 0,
            "snow_depth_inches": 0,
            "pressure": 1013.25,
            "wind_speed": 5,
            "wind_direction": 270,
            "conditions": [],
            "leeward_aspects": ["southeast", "south"],
            "tomorrow_forecast": {},
            "tomorrow_hourly_wind": [],
            "hunting_windows": {"morning": "No data", "evening": "No data", "all_day": "No data"},
            "raw_data": {}
        }


def calculate_wind_hunting_windows(hourly_wind: List[Dict]) -> Dict[str, Any]:
    """Calculate optimal hunting windows based on wind conditions"""
    if not hourly_wind:
        return {"morning": "No data", "evening": "No data", "all_day": "No data"}
    
    # Find best morning window (5 AM - 10 AM)
    morning_hours = [h for h in hourly_wind if 5 <= h["hour"] <= 10]
    best_morning = min(morning_hours, key=lambda x: x["wind_speed"]) if morning_hours else None
    
    # Find best evening window (3 PM - 7 PM)  
    evening_hours = [h for h in hourly_wind if 15 <= h["hour"] <= 19]
    best_evening = min(evening_hours, key=lambda x: x["wind_speed"]) if evening_hours else None
    
    # Check for all-day low wind
    avg_wind = sum(h["wind_speed"] for h in hourly_wind) / len(hourly_wind) if hourly_wind else 20
    
    def format_wind_advice(hour_data):
        if not hour_data:
            return "No optimal window"
        
        wind_dir = hour_data["wind_direction"]
        wind_speed = hour_data["wind_speed"]
        
        # Convert wind direction to compass heading
        if 0 <= wind_dir < 45 or 315 <= wind_dir < 360:
            direction = "North"
        elif 45 <= wind_dir < 135:
            direction = "East"
        elif 135 <= wind_dir < 225:
            direction = "South"
        else:
            direction = "West"
        
        return f"{hour_data['hour']}:00 - {direction} wind at {wind_speed:.1f} mph"
    
    return {
        "morning": format_wind_advice(best_morning),
        "evening": format_wind_advice(best_evening),
        "average_wind_speed": round(avg_wind, 1),
        "all_day_favorable": avg_wind < 10,
        "wind_advice": "Light winds all day - excellent hunting conditions!" if avg_wind < 8 else 
                      "Moderate winds - plan stand locations carefully" if avg_wind < 15 else 
                      "Strong winds expected - consider postponing hunt"
    }


import time

def get_real_elevation_grid(lat: float, lon: float, size: int = GRID_SIZE, span_deg: float = 0.04) -> np.ndarray:
    """Fetches a grid of real elevation data from the Open-Meteo API using POST requests to handle bulk data."""
    lats = np.linspace(lat + span_deg / 2, lat - span_deg / 2, size)
    lons = np.linspace(lon - span_deg / 2, lon + span_deg / 2, size)
    all_coords = [ (lat_val, lon_val) for lat_val in lats for lon_val in lons ]

    url = "https://api.open-meteo.com/v1/elevation"
    all_elevations = []
    
    # Process coordinates in chunks of 100
    for i in range(0, len(all_coords), 100):
        chunk = all_coords[i:i+100]
        lat_chunk = [c[0] for c in chunk]
        lon_chunk = [c[1] for c in chunk]
        
        # Format for application/x-www-form-urlencoded
        payload = {
            "latitude": ",".join(map(str, lat_chunk)),
            "longitude": ",".join(map(str, lon_chunk))
        }
        
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        results = response.json()
        all_elevations.extend(results['elevation'])
        time.sleep(2) # Add a 2-second delay
        
    return np.array(all_elevations).reshape(size, size)

def get_vegetation_grid_from_osm(lat: float, lon: float, size: int = GRID_SIZE, span_deg: float = 0.04) -> np.ndarray:
    """Fetches land use data from OpenStreetMap via Overpass API and rasterizes it."""
    bbox = (lat - span_deg / 2, lon - span_deg / 2, lat + span_deg / 2, lon + span_deg / 2)
    query = f"""[out:json];(
        way["landuse"="forest"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        way["natural"="wood"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        way["landuse"="farmland"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        way["natural"="water"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        relation["landuse"="forest"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        relation["natural"="wood"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        relation["landuse"="farmland"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        relation["natural"="water"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
    );(._;>;);out body;"""
    
    response = requests.post(OVERPASS_API_URL, data=query)
    response.raise_for_status()
    osm_data = response.json()

    # Create polygons from OSM data
    polygons = {"forest": [], "field": [], "water": []}
    nodes = {node['id']: (node['lon'], node['lat']) for node in osm_data['elements'] if node['type'] == 'node'}
    for element in osm_data['elements']:
        if element['type'] == 'way' and 'nodes' in element and element['nodes'][0] == element['nodes'][-1]:
            coords = [nodes[node_id] for node_id in element['nodes'] if node_id in nodes]
            if len(coords) < 3: continue
            poly = Polygon(coords)
            tags = element.get('tags', {})
            if tags.get('landuse') == 'forest' or tags.get('natural') == 'wood':
                polygons["forest"].append(poly)
            elif tags.get('landuse') == 'farmland':
                polygons["field"].append(poly)
            elif tags.get('natural') == 'water':
                polygons["water"].append(poly)

    # Rasterize polygons onto the grid
    grid = np.ones((size, size), dtype=int) * 1 # Default to field
    lats = np.linspace(lat + span_deg / 2, lat - span_deg / 2, size)
    lons = np.linspace(lon - span_deg / 2, lon + span_deg / 2, size)

    for i in range(size):
        for j in range(size):
            point = Point(lons[j], lats[i])
            if any(poly.contains(point) for poly in polygons["water"]):
                grid[i, j] = 0
            elif any(poly.contains(point) for poly in polygons["forest"]):
                grid[i, j] = 2
    return grid

# --- All other functions (analysis, rule engine, geometry generation) remain the same ---
# (For brevity, the unchanged functions from the previous version are omitted here,
# but they are still part of this file in the actual implementation.)

def detect_edges_simple(binary_grid):
    """Simple edge detection for forest-field transitions using gradient magnitude."""
    
    # Apply slight smoothing to reduce noise
    smoothed = gaussian_filter(binary_grid.astype(float), sigma=0.5)
    
    # Calculate gradient magnitude
    grad_x, grad_y = np.gradient(smoothed)
    edge_magnitude = np.sqrt(grad_x**2 + grad_y**2)
    
    # Threshold to identify edges
    return edge_magnitude > np.percentile(edge_magnitude, 75)

def analyze_terrain_and_vegetation(elevation_grid, vegetation_grid):
    """
    Enhanced terrain analysis for Vermont white-tailed deer habitat prediction.
    Includes advanced curvature analysis for saddles, winter yard detection,
    and improved ridge identification.
    
    Args:
        elevation_grid: 2D numpy array of elevation data
        vegetation_grid: 2D numpy array of vegetation data
    
    Returns:
        dict: Feature dictionary with terrain and vegetation characteristics
    """
    
    # Basic terrain analysis
    grad_x, grad_y = np.gradient(elevation_grid)
    slope = np.degrees(np.arctan(np.sqrt(grad_x**2 + grad_y**2)))
    aspect = np.degrees(np.arctan2(-grad_y, grad_x))
    
    # Enhanced ridge detection using curvature (better for Vermont's rolling hills)
    curvature = laplace(elevation_grid)
    ridge_top = (curvature < 0) & (slope > 10)  # Negative curvature indicates peaks; lower slope threshold
    
    # Vermont-specific saddle and funnel detection
    smoothed_elev = gaussian_filter(elevation_grid, sigma=1)
    hessian_xx = np.gradient(np.gradient(smoothed_elev, axis=0), axis=0)
    hessian_yy = np.gradient(np.gradient(smoothed_elev, axis=1), axis=1)
    hessian_xy = np.gradient(np.gradient(smoothed_elev, axis=0), axis=1)
    
    # Principal curvatures for saddle detection
    discriminant = np.sqrt((hessian_xx - hessian_yy)**2 + 4*hessian_xy**2)
    curv1 = (hessian_xx + hessian_yy + discriminant) / 2
    curv2 = (hessian_xx + hessian_yy - discriminant) / 2
    saddle = (curv1 > 0) & (curv2 < 0) & (slope < 15)  # One positive, one negative curvature
    
    # Terrain features
    flat_area = (slope < 5)
    south_slope = (aspect >= 135) & (aspect <= 225)
    north_slope = (aspect >= 315) | (aspect <= 45)
    southwest_slope = (aspect >= 180) & (aspect <= 270)  # For hardwood benches
    
    # Bluff and cliff pinch points (steep terrain features)
    bluff_pinch = (slope > 35) & (np.abs(curvature) > np.percentile(np.abs(curvature), 85))
    
    # Enhanced vegetation analysis for Vermont species
    # Detect conifer density for winter yards (assuming vegetation_grid encoding)
    conifer_dense = vegetation_grid > 0.7  # High density conifers (hemlock, cedar, spruce)
    conifer_corridor = (vegetation_grid > 0.4) & (vegetation_grid <= 0.7)  # Moderate conifer cover
    hardwood = (vegetation_grid > 0.2) & (vegetation_grid <= 0.4)  # Deciduous forest
    field = vegetation_grid <= 0.2  # Open areas, fields, agriculture
    
    # Vermont-specific habitat features
    winter_yard_potential = conifer_dense & (elevation_grid < 610)  # <2000ft elevation, dense softwoods
    hardwood_bench = hardwood & southwest_slope & (slope > 5) & (slope < 20)  # Mast-producing benches
    orchard = field & (elevation_grid < 457)  # <1500ft, likely agricultural/orchard areas
    
    # Edge detection for transition zones
    forest_edge = detect_edges_simple(vegetation_grid > 0.3)  # Forest-field transitions
    creek_bottom = (elevation_grid < np.percentile(elevation_grid, 20)) & (slope < 10)  # Low-lying drainages
    swamp = creek_bottom & (vegetation_grid > 0.1) & (vegetation_grid < 0.3)  # Wet areas with sparse canopy
    
    # Oak flats (hardwood areas in relatively flat terrain)
    oak_flat = hardwood & flat_area
    
    return {
        # Basic terrain
        'slope': slope,
        'aspect': aspect,
        'elevation': elevation_grid,
        'curvature': curvature,
        
        # Enhanced terrain features
        'ridge_top': ridge_top,
        'saddle': saddle,
        'flat_area': flat_area,
        'south_slope': south_slope,
        'north_slope': north_slope,
        'southwest_slope': southwest_slope,
        'bluff_pinch': bluff_pinch,
        'creek_bottom': creek_bottom,
        
        # Vegetation features
        'conifer_dense': conifer_dense,
        'conifer_corridor': conifer_corridor,
        'hardwood': hardwood,
        'field': field,
        'deep_forest': vegetation_grid > 0.8,  # Very dense forest
        'forest_edge': forest_edge,
        'swamp': swamp,
        
        # Vermont-specific combined features
        'winter_yard_potential': winter_yard_potential,
        'hardwood_bench': hardwood_bench,
        'orchard': orchard,
        'oak_flat': oak_flat,
        
        # Raw grids for additional analysis
        'vegetation_grid': vegetation_grid
    }

def run_grid_rule_engine(rules: List[Dict[str, Any]], features: Dict[str, np.ndarray], conditions: Dict[str, Any]) -> Dict[str, np.ndarray]:
    """
    Enhanced rule engine for Vermont white-tailed deer predictions.
    Includes weather conditions, seasonal modifiers, and Vermont-specific habitat features.
    """
    grid_shape = features["slope"].shape
    score_maps = {
        "travel": np.zeros(grid_shape),
        "bedding": np.zeros(grid_shape),
        "feeding": np.zeros(grid_shape)
    }

    # Vermont-specific seasonal weightings
    seasonal_weights = {
        "early_season": {"travel": 1.0, "bedding": 1.0, "feeding": 1.2},  # Focus on feeding patterns
        "rut": {"travel": 1.3, "bedding": 0.9, "feeding": 1.0},  # Increased movement
        "late_season": {"travel": 0.8, "bedding": 1.5, "feeding": 1.1}   # Winter yard emphasis
    }
    
    # Weather condition modifiers
    weather_modifiers = {
        "cold_front": {"travel": 1.15, "bedding": 1.0, "feeding": 1.1},
        "heavy_snow": {"travel": 0.7, "bedding": 1.2, "feeding": 0.9},
        "deep_snow": {"travel": 0.6, "bedding": 1.3, "feeding": 0.8},
        "strong_wind": {"travel": 0.8, "bedding": 1.2, "feeding": 0.9}
    }

    for rule in rules:
        # Check time and season conditions
        time_match = rule["time"] == "any" or rule["time"] == conditions.get("time_of_day", "any")
        season_match = rule["season"] == "any" or rule["season"] == conditions.get("season", "any")
        
        # Check weather conditions if specified
        weather_match = True
        if "weather_condition" in rule and rule["weather_condition"] != "any":
            weather_match = rule["weather_condition"] in conditions.get("weather_conditions", [])
        
        if not (time_match and season_match and weather_match):
            continue

        # Map rule terrain/vegetation to feature grids
        terrain_key = rule["terrain"]
        vegetation_key = rule["vegetation"]
        
        # Get terrain feature
        if terrain_key == "any":
            terrain_grid = np.ones(grid_shape, dtype=bool)
        else:
            terrain_grid = features.get(terrain_key, np.zeros(grid_shape, dtype=bool))
        
        # Get vegetation feature
        if vegetation_key == "any":
            vegetation_grid = np.ones(grid_shape, dtype=bool)
        else:
            vegetation_grid = features.get(vegetation_key, np.zeros(grid_shape, dtype=bool))
        
        # Combine terrain and vegetation requirements
        combined_mask = np.logical_and(terrain_grid, vegetation_grid)
        
        # Apply base confidence score
        base_score = rule["confidence"]
        
        # Apply seasonal weighting
        season = conditions.get("season", "early_season")
        if season in seasonal_weights:
            base_score *= seasonal_weights[season].get(rule["behavior"], 1.0)
        
        # Apply weather modifiers
        for weather_cond in conditions.get("weather_conditions", []):
            if weather_cond in weather_modifiers:
                base_score *= weather_modifiers[weather_cond].get(rule["behavior"], 1.0)
        
        # Add score to matching cells
        score_maps[rule["behavior"]][combined_mask] += base_score
    
    # Vermont-specific post-processing
    # Reduce scores near high-access areas (hunting pressure proxy)
    if "road_proximity" in features:
        access_penalty = features["road_proximity"] < 0.5  # Close to roads
        for behavior in score_maps:
            score_maps[behavior][access_penalty] *= 0.8
    
    # Winter severity index (boost winter yard features in harsh conditions)
    if "deep_snow" in conditions.get("weather_conditions", []):
        winter_boost = features.get("winter_yard_potential", np.zeros(grid_shape))
        score_maps["bedding"] += winter_boost * 0.5
    
    # Normalize scores to 0-10 range
    for behavior in score_maps:
        max_score = np.max(score_maps[behavior])
        if max_score > 0:
            score_maps[behavior] = (score_maps[behavior] / max_score) * 10
    
    return score_maps

def generate_corridors_from_scores(score_map: np.ndarray, elevation_grid: np.ndarray, lat: float, lon: float, size: int) -> Dict[str, Any]:
    """Uses A* to find optimal paths through high-scoring travel areas."""
    # Invert scores to use as costs for A*
    cost_map = (np.max(score_map) - score_map) + 1
    graph = nx.grid_2d_graph(size, size)
    for u, v in graph.edges():
        graph.add_edge(u, v, weight=cost_map[v])

    # Find path between two high-score areas
    high_score_nodes = np.argwhere(score_map > np.percentile(score_map, 90))
    if len(high_score_nodes) < 2:
        return {"type": "FeatureCollection", "features": []}
    
    start_node = tuple(high_score_nodes[0])
    end_node = tuple(high_score_nodes[-1])

    try:
        path = nx.astar_path(graph, start_node, end_node, heuristic=dist_heuristic)
    except nx.NetworkXNoPath:
        return {"type": "FeatureCollection", "features": []}

    coordinates = [(lon - 0.02 + (x / size) * 0.04, lat + 0.02 - (y / size) * 0.04) for y, x in path]
    line = LineString(coordinates)
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": line.__geo_interface__}] }

def generate_zones_from_scores(score_map: np.ndarray, lat: float, lon: float, size: int, percentile: int = 85) -> Dict[str, Any]:
    """Creates polygons around high-scoring zones."""
    high_score_indices = np.argwhere(score_map > np.percentile(score_map, percentile))
    if len(high_score_indices) < 3:
        return {"type": "FeatureCollection", "features": []}

    hull = ConvexHull(high_score_indices)
    hull_points = [high_score_indices[i] for i in hull.vertices]
    coordinates = [(lon - 0.02 + (x / size) * 0.04, lat + 0.02 - (y / size) * 0.04) for y, x in hull_points]
    polygon = Polygon(coordinates)
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": polygon.__geo_interface__}]}

def get_moon_phase(date_time_str: str) -> str:
    """
    Calculate moon phase for enhanced deer activity predictions.
    Dark moons (new moon) often increase deer activity.
    """
    try:
        from datetime import datetime
        import math
        
        # Parse the input date
        dt = datetime.fromisoformat(date_time_str.replace('Z', '+00:00'))
        
        # Simple moon phase calculation
        # Based on lunar cycle of ~29.53 days
        # Reference new moon: January 6, 2000
        reference = datetime(2000, 1, 6)
        days_since_reference = (dt - reference).days
        lunar_cycle = 29.53
        
        # Calculate phase (0 = new moon, 0.5 = full moon)
        phase = (days_since_reference % lunar_cycle) / lunar_cycle
        
        if phase < 0.125 or phase > 0.875:
            return "new"  # Dark moon - higher activity
        elif 0.375 < phase < 0.625:
            return "full"  # Bright moon - moderate activity
        else:
            return "quarter"  # Moderate light
            
    except Exception as e:
        logger.warning(f"Error calculating moon phase: {e}")
        return "unknown"

def get_time_of_day(date_time_str: str) -> str:
    hour = datetime.fromisoformat(date_time_str).hour
    if 5 <= hour <= 9: return "dawn"
    if 16 <= hour <= 20: return "dusk"
    if 10 <= hour <= 15: return "mid-day"
    return "night"

def dist_heuristic(a, b): return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

def create_enhanced_score_heatmap(score_grid: np.ndarray, title: str, description: str, cmap: str = 'RdYlBu_r') -> str:
    """
    Create an enhanced score heatmap with clear visual indicators and explanations.
    
    Args:
        score_grid: 2D array of scores (0-10 scale)
        title: Title for the heatmap
        description: Description of what the colors mean
        cmap: Colormap to use
    
    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Normalize scores to 0-10 range for consistency
    normalized_scores = np.clip(score_grid, 0, 10)
    
    # Create the heatmap with custom levels
    levels = np.linspace(0, 10, 11)  # 0, 1, 2, ..., 10
    im = ax.contourf(normalized_scores, levels=levels, cmap=cmap, extend='both')
    
    # Add colorbar with clear labels
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Deer Activity Score (0-10)', fontsize=12, fontweight='bold')
    cbar.set_ticks([0, 2, 4, 6, 8, 10])
    cbar.set_ticklabels(['Very Low\n(0-1)', 'Low\n(2-3)', 'Moderate\n(4-5)', 
                        'Good\n(6-7)', 'High\n(8-9)', 'Excellent\n(10)'])
    
    # Enhance the plot appearance
    ax.set_title(f'{title}\n{description}', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Grid East-West', fontsize=11)
    ax.set_ylabel('Grid North-South', fontsize=11)
    
    # Add score statistics as text
    max_score = np.max(normalized_scores)
    avg_score = np.mean(normalized_scores)
    high_score_percent = np.sum(normalized_scores >= 7) / normalized_scores.size * 100
    
    stats_text = f'Max Score: {max_score:.1f}\nAvg Score: {avg_score:.1f}\nHigh Activity Areas: {high_score_percent:.1f}%'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            verticalalignment='top', fontsize=10)
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3)
    
    # Save to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    return f"data:image/png;base64,{image_base64}"

def create_heatmap_image(grid: np.ndarray, cmap: str = 'viridis') -> str:
    """Generates a base64-encoded heatmap image from a grid."""
    fig, ax = plt.subplots()
    ax.imshow(grid, cmap=cmap)
    ax.axis('off')
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    return base64.b64encode(buf.getbuffer()).decode("ascii")

def find_better_hunting_spots(score_maps: Dict[str, np.ndarray], center_lat: float, center_lon: float, 
                            current_rating: float, size: int = GRID_SIZE, span_deg: float = 0.04,
                            min_target_rating: float = 8.0, max_suggestions: int = 5,
                            suggestion_threshold: float = 5.0) -> List[Dict[str, Any]]:
    """Find better hunting spots in the surrounding area if current rating is below threshold."""
    
    if current_rating >= suggestion_threshold:  # Only suggest spots if current rating is below threshold
        return []
    
    # Calculate combined score for each grid cell
    combined_scores = np.mean([score_maps['travel'], score_maps['bedding'], score_maps['feeding']], axis=0) * 2
    combined_scores = np.clip(combined_scores, 0, 10)  # Clamp to 0-10 range
    
    # Find cells with high scores (8+ preferred, but accept 7+ if not enough 8+)
    high_score_mask = combined_scores >= min_target_rating
    
    # If no spots with target rating, lower the threshold
    if np.sum(high_score_mask) == 0:
        min_target_rating = 7.0
        high_score_mask = combined_scores >= min_target_rating
    
    # If still no good spots, take the best available
    if np.sum(high_score_mask) == 0:
        # Take top 20% of scores
        threshold = np.percentile(combined_scores, 80)
        high_score_mask = combined_scores >= threshold
    
    # Get coordinates of high-scoring cells
    high_score_indices = np.argwhere(high_score_mask)
    
    suggestions = []
    
    # Convert grid indices to lat/lon coordinates
    lats = np.linspace(center_lat + span_deg / 2, center_lat - span_deg / 2, size)
    lons = np.linspace(center_lon - span_deg / 2, center_lon + span_deg / 2, size)
    
    for idx in high_score_indices:
        row, col = idx
        lat = lats[row]
        lon = lons[col]
        score = combined_scores[row, col]
        
        # Calculate distance from center point in meters (approximate)
        lat_diff = lat - center_lat
        lon_diff = lon - center_lon
        distance_km = np.sqrt((lat_diff * 111.32)**2 + (lon_diff * 111.32 * np.cos(np.radians(center_lat)))**2)
        
        # Determine primary reason for high score
        travel_score = score_maps['travel'][row, col] * 2
        bedding_score = score_maps['bedding'][row, col] * 2
        feeding_score = score_maps['feeding'][row, col] * 2
        
        primary_activity = "Mixed"
        if travel_score > bedding_score and travel_score > feeding_score:
            primary_activity = "Travel Corridor"
        elif bedding_score > feeding_score:
            primary_activity = "Bedding Area"
        else:
            primary_activity = "Feeding Area"
        
        suggestions.append({
            "lat": float(lat),
            "lon": float(lon),
            "rating": float(round(score, 1)),
            "distance_km": float(round(distance_km, 2)),
            "primary_activity": primary_activity,
            "travel_score": float(round(travel_score, 1)),
            "bedding_score": float(round(bedding_score, 1)),
            "feeding_score": float(round(feeding_score, 1)),
            "description": f"{primary_activity} - Rating {round(score, 1)}/10 ({round(distance_km, 2)}km away)"
        })
    
    # Sort by score (descending) then by distance (ascending)
    suggestions.sort(key=lambda x: (-x['rating'], x['distance_km']))
    
    # Return top suggestions, avoiding duplicates that are too close together
    filtered_suggestions = []
    min_distance_km = 0.1  # Minimum 100m apart
    
    for suggestion in suggestions:
        too_close = False
        for existing in filtered_suggestions:
            if abs(suggestion['lat'] - existing['lat']) < 0.001 and abs(suggestion['lon'] - existing['lon']) < 0.001:
                too_close = True
                break
        
        if not too_close:
            filtered_suggestions.append(suggestion)
            
        if len(filtered_suggestions) >= max_suggestions:
            break
    
    return filtered_suggestions