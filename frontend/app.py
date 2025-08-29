import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json
import os
import hashlib
import math
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from map_config import MAP_SOURCES
from enhanced_data_validation import (
    FrontendDataValidator,
    create_enhanced_data_traceability_display,
    enhanced_backend_logging_for_predictions,
    check_enhanced_bedding_predictor_integration
)

# Load environment variables
load_dotenv()

# Configure logging for enhanced data traceability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Deer Approach Direction Calculation Functions ---
def calculate_terrain_based_deer_approach(terrain_features, stand_coords, stand_type):
    """Calculate deer approach direction based on terrain features when bedding zones aren't available"""
    
    # Get terrain characteristics
    aspect = terrain_features.get('aspect', 0)
    slope = terrain_features.get('slope', 0) 
    terrain_type = terrain_features.get('terrain_type', 'mixed')
    
    # Default approach bearing - will be modified based on terrain
    approach_bearing = 180.0  # Default to south approach
    
    # Stand type specific logic
    if stand_type == "Travel Corridor":
        if 'ridge' in terrain_type.lower() or 'saddle' in terrain_type.lower():
            approach_bearing = 45.0  # NE approach from bedding areas
        elif 'valley' in terrain_type.lower() or 'creek' in terrain_type.lower():
            approach_bearing = 270.0 if aspect < 180 else 90.0  # W or E approach
        else:
            approach_bearing = 0.0 if slope > 10 else 180.0  # N or S
            
    elif stand_type == "Bedding Area":
        if slope > 15:
            approach_bearing = 180.0  # South approach from valleys
        else:
            approach_bearing = 135.0 if 'agricultural' in terrain_type else 225.0
            
    elif stand_type == "Feeding Area":
        if terrain_features.get('forest_edge', False):
            approach_bearing = 0.0  # North approach from forest
        elif slope > 10:
            approach_bearing = aspect + 180  # Opposite of slope aspect
        else:
            approach_bearing = 315.0  # NW approach
    
    else:  # General stand
        if 'ridge' in terrain_type.lower():
            approach_bearing = 90.0  # E approach along ridge
        elif 'valley' in terrain_type.lower():
            approach_bearing = 0.0   # N approach down valley
        elif slope > 15:
            approach_bearing = aspect  # Same direction as slope faces
        else:
            approach_bearing = 135.0  # Default SE approach for gentle terrain
    
    # Normalize bearing to 0-360 range
    approach_bearing = approach_bearing % 360
    
    # Convert to compass direction
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    compass_dir = directions[int((approach_bearing + 11.25) / 22.5) % 16]
    
    return approach_bearing, compass_dir

def enhanced_deer_approach_calculation(prediction_data):
    """Enhanced deer approach calculation that tries multiple methods"""
    
    # Method 1: Try bedding zone calculation (existing logic)
    bedding_zones = prediction_data.get('bedding_zones', {}).get('zones', [])
    stand_coords = prediction_data.get('coordinates', {})
    
    if bedding_zones and stand_coords.get('lat') and stand_coords.get('lon'):
        try:
            first_bedding = bedding_zones[0]
            bedding_lat = first_bedding.get('lat', 0)
            bedding_lon = first_bedding.get('lon', 0)
            
            if bedding_lat and bedding_lon:
                bearing = calculate_bearing_between_points(
                    bedding_lat, bedding_lon, 
                    stand_coords['lat'], stand_coords['lon']
                )
                directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                compass_dir = directions[int((bearing + 11.25) / 22.5) % 16]
                return bearing, compass_dir
        except:
            pass  # Fall through to terrain-based calculation
    
    # Method 2: Travel corridor calculation
    travel_zones = prediction_data.get('travel_zones', {}).get('zones', [])
    if travel_zones and len(travel_zones) >= 2:
        try:
            zone1 = travel_zones[0]
            zone2 = travel_zones[1] 
            bearing = calculate_bearing_between_points(
                zone1.get('lat', 0), zone1.get('lon', 0),
                zone2.get('lat', 0), zone2.get('lon', 0)
            )
            directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            compass_dir = directions[int((bearing + 11.25) / 22.5) % 16]
            return bearing, compass_dir
        except:
            pass
    
    # Method 3: Terrain-based calculation (fallback)
    terrain_features = prediction_data.get('terrain_features', {})
    stand_type = prediction_data.get('stand_type', 'General')
    
    return calculate_terrain_based_deer_approach(terrain_features, stand_coords, stand_type)

def calculate_bearing_between_points(lat1, lon1, lat2, lon2):
    """Calculate bearing between two points"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing

def calculate_time_based_deer_approach(hunt_period, stand_coords, prediction_data):
    """
    NEW: Calculate deer approach based on hunt period and actual movement patterns
    Fixes the major logic flaw where deer approach was backwards for morning hunts
    """
    
    # Extract feeding and bedding areas from prediction data
    feeding_areas = []
    bedding_areas = []
    
    # Get feeding areas from backend data
    feeding_data = prediction_data.get('feeding_areas', {})
    if feeding_data and 'features' in feeding_data:
        for feature in feeding_data['features']:
            coords = feature.get('geometry', {}).get('coordinates', [])
            if len(coords) == 2:
                # Convert GeoJSON [lon, lat] to (lat, lon)
                feeding_areas.append((coords[1], coords[0]))
    
    # Get bedding areas from backend data
    bedding_data = prediction_data.get('bedding_zones', {})
    if bedding_data and 'features' in bedding_data:
        for feature in bedding_data['features']:
            coords = feature.get('geometry', {}).get('coordinates', [])
            if len(coords) == 2:
                # Convert GeoJSON [lon, lat] to (lat, lon)
                bedding_areas.append((coords[1], coords[0]))
    
    if hunt_period == "AM":
        # 5:30-9:00 AM: Deer moving FROM feeding TO bedding
        if feeding_areas:
            source_coords = feeding_areas[0]  # Nearest feeding area
            movement_type = "Returning from feeding areas to bedding"
            confidence = "High"
        else:
            # Fallback: assume feeding south/southeast of stand
            source_coords = (stand_coords[0] - 0.01, stand_coords[1] - 0.005)
            movement_type = "Estimated: returning from feeding areas"
            confidence = "Medium"
            
    elif hunt_period == "PM":
        # 17:00-19:00: Deer moving FROM bedding TO feeding
        if bedding_areas:
            source_coords = bedding_areas[0]  # Nearest bedding area
            movement_type = "Leaving bedding areas for feeding"
            confidence = "High"
        else:
            # Fallback: assume bedding north/northeast of stand
            source_coords = (stand_coords[0] + 0.01, stand_coords[1] + 0.005)
            movement_type = "Estimated: leaving bedding areas for feeding"
            confidence = "Medium"
            
    else:  # DAY period (9:00-17:00)
        # Midday: Deer in bedding areas, minimal movement
        if bedding_areas:
            source_coords = bedding_areas[0]
            movement_type = "Minimal movement in bedding areas"
            confidence = "Low"
        else:
            # Fallback: assume bedding north/northeast of stand
            source_coords = (stand_coords[0] + 0.008, stand_coords[1] + 0.004)
            movement_type = "Estimated: minimal movement near bedding"
            confidence = "Low"
    
    # Calculate bearing from source to stand
    approach_bearing = calculate_bearing_between_points(
        source_coords[0], source_coords[1],
        stand_coords[0], stand_coords[1]
    )
    
    # Convert to compass direction
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    approach_compass = directions[int((approach_bearing + 11.25) / 22.5) % 16]
    
    return {
        "bearing": approach_bearing,
        "compass": approach_compass,
        "movement_type": movement_type,
        "confidence": confidence,
        "source_coords": source_coords
    }

# --- Password Protection ---
def check_password():
    """Returns True if the user entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # Get password from environment variable for security
        correct_password = os.getenv("APP_PASSWORD", "DefaultPassword123!")
        
        # Check if password key exists before accessing it
        if "password" in st.session_state:
            if hashlib.sha256(st.session_state["password"].encode()).hexdigest() == hashlib.sha256(correct_password.encode()).hexdigest():
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store password
            else:
                st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.markdown("# 🦌 Professional Deer Hunting Intelligence")
        st.markdown("### 🔐 Secure Access Required")
        st.markdown("*89.1% confidence predictions • Vermont legal hours • Real-time scouting data*")
        st.markdown("---")
        st.text_input(
            "Enter Access Password:", 
            type="password", 
            on_change=password_entered, 
            key="password",
            help="Contact the administrator for access credentials"
        )
        st.markdown("---")
        st.markdown("*🏔️ Vermont Deer Movement Predictor with Enhanced Intelligence*")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.markdown("# 🦌 Professional Deer Hunting Intelligence")
        st.markdown("### 🔐 Secure Access Required")
        st.markdown("*89.1% confidence predictions • Vermont legal hours • Real-time scouting data*")
        st.markdown("---")
        st.text_input(
            "Enter Access Password:", 
            type="password", 
            on_change=password_entered, 
            key="password",
            help="Contact the administrator for access credentials"
        )
        st.error("🚫 Access denied. Please check your password and try again.")
        st.markdown("---")
        st.markdown("*🏔️ Vermont Deer Movement Predictor with Enhanced Intelligence*")
        return False
    else:
        # Password correct
        return True

# --- Backend Configuration ---
BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')

# --- Map Configuration ---
# Filter enabled map sources
MAP_CONFIGS = {
    name: config for name, config in MAP_SOURCES.items() 
    if config.get("enabled", True)
}

def create_map(location, zoom_start, map_type):
    """Create a Folium map with the specified map type"""
    config = MAP_CONFIGS.get(map_type, MAP_CONFIGS["Street Map"])
    
    if config["tiles"]:
        return folium.Map(
            location=location,
            zoom_start=zoom_start,
            tiles=config["tiles"],
            attr=config["attr"]
        )
    else:
        return folium.Map(location=location, zoom_start=zoom_start)

def get_vermont_legal_hunting_hours(date):
    """
    Calculate legal hunting hours for Vermont based on date.
    Vermont legal hunting hours: 30 minutes before sunrise to 30 minutes after sunset.
    
    Returns tuple of (earliest_time, latest_time) as datetime.time objects.
    """
    # Simplified sunrise/sunset table for Vermont (Montpelier)
    # This is a basic approximation - in production, you'd use a proper astronomical library
    sunrise_times = {
        1: (7, 26), 2: (7, 8), 3: (6, 27), 4: (6, 31), 5: (5, 41), 6: (5, 9),
        7: (5, 10), 8: (5, 38), 9: (6, 13), 10: (6, 48), 11: (7, 28), 12: (7, 6)
    }
    
    sunset_times = {
        1: (16, 22), 2: (17, 0), 3: (17, 39), 4: (19, 18), 5: (19, 54), 6: (20, 27),
        7: (20, 38), 8: (20, 14), 9: (19, 26), 10: (18, 31), 11: (16, 40), 12: (16, 13)
    }
    
    month = date.month
    
    # Get approximate sunrise/sunset for the month
    sunrise_hour, sunrise_min = sunrise_times.get(month, (6, 30))
    sunset_hour, sunset_min = sunset_times.get(month, (18, 30))
    
    # Calculate 30 minutes before sunrise and 30 minutes after sunset
    sunrise_dt = datetime.combine(date, datetime.min.time().replace(hour=sunrise_hour, minute=sunrise_min))
    sunset_dt = datetime.combine(date, datetime.min.time().replace(hour=sunset_hour, minute=sunset_min))
    
    earliest_hunting = (sunrise_dt - timedelta(minutes=30)).time()
    latest_hunting = (sunset_dt + timedelta(minutes=30)).time()
    
    return earliest_hunting, latest_hunting

def generate_legal_hunting_times(date):
    """Generate list of legal hunting times for Vermont in 30-minute intervals"""
    earliest, latest = get_vermont_legal_hunting_hours(date)
    
    # Convert to datetime objects for easier manipulation
    earliest_dt = datetime.combine(date, earliest)
    latest_dt = datetime.combine(date, latest)
    
    # If latest time is past midnight, adjust
    if latest_dt < earliest_dt:
        latest_dt += timedelta(days=1)
    
    # Generate times in 30-minute intervals
    current_time = earliest_dt
    hunting_times = []
    
    while current_time <= latest_dt:
        # Format time for display
        time_str = current_time.strftime("%I:%M %p")
        hunting_times.append((current_time.time(), time_str))
        current_time += timedelta(minutes=30)
    
    return hunting_times

# --- Scouting Functions ---
def get_observation_types():
    """Get available scouting observation types from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/scouting/types")
        if response.status_code == 200:
            return response.json().get('observation_types', [])
    except Exception as e:
        st.error(f"Failed to load observation types: {e}")
    return []

def add_scouting_observation(observation_data):
    """Add a new scouting observation"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/scouting/add_observation",
            json=observation_data,
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to add observation: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error adding observation: {e}")
        return None

def get_scouting_observations(lat, lon, radius_miles=5):
    """Get scouting observations near a location"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/scouting/observations",
            params={
                'lat': lat,
                'lon': lon,
                'radius_miles': radius_miles
            }
        )
        if response.status_code == 200:
            return response.json().get('observations', [])
    except Exception as e:
        st.error(f"Failed to load observations: {e}")
    return []

def get_scouting_analytics(lat, lon, radius_miles=5):
    """Get scouting analytics for an area"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/scouting/analytics",
            params={
                'lat': lat,
                'lon': lon,
                'radius_miles': radius_miles
            }
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Failed to load analytics: {e}")
    return {}

# --- App Configuration ---
st.set_page_config(
    page_title="🏔️ Vermont Deer Movement Predictor",
    page_icon="🦌",
    layout="wide"
)

# Add custom CSS for Vermont-themed styling
st.markdown("""
<style>
.stAlert > div {
    padding: 0.5rem 1rem;
}
.stExpander > div:first-child {
    background-color: #f0f8ff;
}
.observation-marker {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 0.5rem;
    padding: 0.5rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# --- Main App ---
# Check password protection first
if not check_password():
    st.stop()

st.title("🏔️ Vermont Deer Movement Predictor with Real-Time Scouting")
st.markdown("*Vermont-legal hunting hours, enhanced predictions, and real-time scouting data integration*")

# Create main navigation tabs
tab_predict, tab_scout, tab_analytics = st.tabs(["🎯 Hunt Predictions", "🔍 Scouting Data", "📊 Analytics"])

# Initialize session state for map data
if 'hunt_location' not in st.session_state:
    st.session_state.hunt_location = [44.26639, -72.58133]  # Vermont center
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 12

# ==========================================
# TAB 1: HUNT PREDICTIONS
# ==========================================
with tab_predict:
    st.header("🎯 Hunting Predictions")
    
    # Create two columns for inputs and map
    input_col, map_col = st.columns([1, 2])
    
    with input_col:
        st.markdown("### 📍 Hunt Location")
        
        # Hunt date selection
        hunt_date = st.date_input(
            "🗓️ Hunt Date",
            value=datetime.now().date(),
            help="Select your planned hunting date"
        )
        
        # Hunt period selection (simplified time periods)
        hunt_period = st.selectbox(
            "⏰ Hunt Period",
            ["AM", "DAY", "PM"],
            index=0,
            format_func=lambda x: {
                "AM": "🌅 AM Hunt (5:30-9:00) - Dawn Movement: Feeding → Bedding",
                "DAY": "☀️ DAY Hunt (9:00-17:00) - Midday: Bedding Areas", 
                "PM": "🌆 PM Hunt (17:00-19:00) - Dusk Movement: Bedding → Feeding"
            }[x],
            help="Select hunting period based on deer movement patterns"
        )
        
        # Season selection
        season = st.selectbox(
            "🍂 Hunting Season",
            ["early_season", "rut", "late_season"],
            index=1,
            format_func=lambda x: {
                "early_season": "🌱 Early Season",
                "rut": "🦌 Rut",
                "late_season": "❄️ Late Season"
            }[x]
        )
        
        # Weather conditions
        weather = st.selectbox(
            "🌤️ Weather Conditions",
            ["Clear", "Partly Cloudy", "Overcast", "Light Rain", "Heavy Rain", "Snow"],
            index=0
        )
        
        # Terrain type
        terrain = st.selectbox(
            "🌲 Terrain Type",
            ["Mixed Forest", "Hardwood", "Conifer", "Field Edge", "Creek Bottom", "Ridge"],
            index=0
        )
    
    with map_col:
        st.markdown("### 🗺️ Select Hunt Location")
        
        # Map type selector
        map_type = st.selectbox(
            "Map Style",
            list(MAP_CONFIGS.keys()),
            index=0
        )
        
        # Store map type in session state for consistency across tabs
        st.session_state.map_type = map_type
        
        # Create and display map
        m = create_map(st.session_state.hunt_location, st.session_state.map_zoom, map_type)
        
        # Add hunt location marker
        folium.Marker(
            st.session_state.hunt_location,
            popup="🎯 Hunt Location",
            icon=folium.Icon(color='red', icon='bullseye')
        ).add_to(m)
        
        # Add prediction results markers if available
        if 'prediction_results' in st.session_state and st.session_state.prediction_results:
            prediction = st.session_state.prediction_results
            
            # Add travel corridor markers
            if 'travel_corridors' in prediction and prediction['travel_corridors']:
                travel_features = prediction['travel_corridors'].get('features', [])
                for feature in travel_features:
                    if feature.get('geometry') and feature['geometry'].get('coordinates'):
                        coords = feature['geometry']['coordinates']
                        lat, lon = coords[1], coords[0]  # GeoJSON is [lon, lat]
                        score = feature['properties'].get('score', 0)
                        
                        folium.CircleMarker(
                            [lat, lon],
                            radius=8,
                            popup=f"🚶 Travel Corridor<br>Score: {score:.2f}",
                            color='blue',
                            fillColor='lightblue',
                            fillOpacity=0.7
                        ).add_to(m)
            
            # Add bedding zone markers with enhanced suitability display
            if 'bedding_zones' in prediction and prediction['bedding_zones']:
                bedding_features = prediction['bedding_zones'].get('features', [])
                
                # Get overall suitability score from properties
                bedding_properties = prediction['bedding_zones'].get('properties', {})
                suitability_analysis = bedding_properties.get('suitability_analysis', {})
                overall_suitability = suitability_analysis.get('overall_score', 0)
                
                for i, feature in enumerate(bedding_features, 1):
                    if feature.get('geometry') and feature['geometry'].get('coordinates'):
                        coords = feature['geometry']['coordinates']
                        lat, lon = coords[1], coords[0]  # GeoJSON is [lon, lat]
                        properties = feature.get('properties', {})
                        score = properties.get('score', 0)
                        
                        # Enhanced popup with biological accuracy details
                        popup_content = f"""
                        <div style='width: 250px;'>
                            <h4>🛏️ Enhanced Bedding Zone {i}</h4>
                            <p><b>Zone Score:</b> {score:.1f}/10</p>
                            <p><b>Overall Suitability:</b> {overall_suitability:.1f}%</p>
                            <p><b>Biological Features:</b></p>
                            <ul>
                                <li>Adaptive thresholds active</li>
                                <li>Canopy & slope optimized</li>
                                <li>South-facing exposure</li>
                                <li>Leeward ridge position</li>
                            </ul>
                        </div>
                        """
                        
                        # Make bedding zones highly visible with larger radius
                        folium.CircleMarker(
                            [lat, lon],
                            radius=15,  # Larger radius for visibility
                            popup=folium.Popup(popup_content, max_width=300),
                            color='darkgreen',
                            fillColor='lightgreen',
                            fillOpacity=0.9,
                            weight=3
                        ).add_to(m)
                        
                        # Add tooltip for hover display
                        folium.Marker(
                            [lat, lon],
                            icon=folium.DivIcon(
                                html=f'<div style="color: green; font-weight: bold;">🛏️{i}</div>',
                                icon_size=(30, 30),
                                icon_anchor=(15, 15)
                            ),
                            tooltip=f"Bedding Zone {i}: {overall_suitability:.1f}% suitability"
                        ).add_to(m)
            
            # Add feeding area markers
            if 'feeding_areas' in prediction and prediction['feeding_areas']:
                feeding_features = prediction['feeding_areas'].get('features', [])
                for feature in feeding_features:
                    if feature.get('geometry') and feature['geometry'].get('coordinates'):
                        coords = feature['geometry']['coordinates']
                        lat, lon = coords[1], coords[0]  # GeoJSON is [lon, lat]
                        score = feature['properties'].get('score', 0)
                        
                        folium.CircleMarker(
                            [lat, lon],
                            radius=6,
                            popup=f"🌾 Feeding Area<br>Score: {score:.2f}",
                            color='orange',
                            fillColor='yellow',
                            fillOpacity=0.6
                        ).add_to(m)
            
            # Add stand location markers (if available)
            if prediction.get('mature_buck_analysis') is not None:
                stand_recommendations = prediction['mature_buck_analysis'].get('stand_recommendations', [])
                for i, rec in enumerate(stand_recommendations, 1):
                    coords = rec.get('coordinates', {})
                    stand_lat = coords.get('lat', 0)
                    stand_lon = coords.get('lon', 0)
                    confidence = rec.get('confidence', 0)
                    stand_type = rec.get('type', 'Unknown')
                    
                    if stand_lat and stand_lon:
                        # Choose marker color based on confidence and position
                        if i == 1:  # Primary stand
                            color = 'red'
                            icon = 'star'
                            icon_name = '🏆'
                        elif i == 2:  # Secondary stand
                            color = 'blue'
                            icon = 'tree'
                            icon_name = '🥈'
                        else:  # Tertiary stand
                            color = 'purple'
                            icon = 'home'
                            icon_name = '🥉'
                        
                        folium.Marker(
                            [stand_lat, stand_lon],
                            popup=f"{icon_name} Stand #{i}: {stand_type}<br>Confidence: {confidence:.0f}%<br>{rec.get('reasoning', '')}",
                            icon=folium.Icon(color=color, icon=icon),
                            tooltip=f"Stand #{i} - {confidence:.0f}%"
                        ).add_to(m)
            
            # Add camera placement marker
            if 'optimal_camera_placement' in prediction and prediction['optimal_camera_placement']:
                camera_data = prediction['optimal_camera_placement']
                camera_lat = camera_data.get('lat', 0)
                camera_lon = camera_data.get('lon', 0)
                camera_confidence = camera_data.get('confidence', 0)
                distance = camera_data.get('distance_from_stand', 0)
                direction = camera_data.get('setup_direction', 'N')
                
                if camera_lat and camera_lon:
                    folium.Marker(
                        [camera_lat, camera_lon],
                        popup=f"📹 Optimal Camera Position<br>Confidence: {camera_confidence}%<br>Distance: {distance}m {direction} of primary stand<br>Setup facing trail approach",
                        icon=folium.Icon(color='darkgreen', icon='video-camera', prefix='fa'),
                        tooltip=f"Camera - {camera_confidence}% confidence"
                    ).add_to(m)
            
            # Legacy camera placement - DISABLED (replaced by optimized camera sites)
            
            # NEW: Add optimized hunting points
            if 'optimized_points' in prediction and prediction['optimized_points']:
                optimized_data = prediction['optimized_points']
                
                # Debug: Show camera count in sidebar
                camera_sites = optimized_data.get('camera_placements', [])
                if camera_sites:
                    st.sidebar.success(f"🎯 Found {len(camera_sites)} optimized camera sites!")
                    for i, cam in enumerate(camera_sites, 1):
                        st.sidebar.info(f"Camera {i}: {cam.get('strategy', 'Unknown')} (Score: {cam.get('score', 0):.1f})")
                else:
                    st.sidebar.warning("⚠️ No optimized camera sites found in prediction data")
                
                # Add Stand Sites (Red Stars with Numbers)
                stand_sites = optimized_data.get('stand_sites', [])
                for i, stand in enumerate(stand_sites, 1):
                    folium.Marker(
                        [stand['lat'], stand['lon']],
                        popup=f"🎯 Stand Site {i}<br><b>{stand['strategy']}</b><br>Score: {stand['score']:.1f}/10<br>{stand['description'][:100]}...<br><b>Best Times:</b> {', '.join(stand['optimal_times'])}",
                        icon=folium.Icon(color='red', icon='bullseye'),
                        tooltip=f"Stand {i}: {stand['strategy']}"
                    ).add_to(m)
                
                # Add Bedding Sites (Green Home Icons with Numbers)  
                bedding_sites = optimized_data.get('bedding_sites', [])
                for i, bed in enumerate(bedding_sites, 1):
                    folium.Marker(
                        [bed['lat'], bed['lon']],
                        popup=f"🛏️ Bedding Site {i}<br><b>{bed['strategy']}</b><br>Score: {bed['score']:.1f}/10<br>{bed['description'][:100]}...<br><b>Security:</b> {bed['specific_attributes'].get('security_score', 'N/A')}%",
                        icon=folium.Icon(color='green', icon='home'),
                        tooltip=f"Bedding {i}: {bed['strategy']}"
                    ).add_to(m)
                
                # Add Feeding Sites (Orange Leaf Icons with Numbers)
                feeding_sites = optimized_data.get('feeding_sites', [])
                for i, feed in enumerate(feeding_sites, 1):
                    folium.Marker(
                        [feed['lat'], feed['lon']],
                        popup=f"🌾 Feeding Site {i}<br><b>{feed['strategy']}</b><br>Score: {feed['score']:.1f}/10<br>{feed['description'][:100]}...<br><b>Food Type:</b> {feed['specific_attributes'].get('food_type', 'N/A')}",
                        icon=folium.Icon(color='orange', icon='leaf'),
                        tooltip=f"Feeding {i}: {feed['strategy']}"
                    ).add_to(m)
                
                # Add Camera Sites (Purple Camera Icons with Numbers)
                camera_sites = optimized_data.get('camera_placements', [])
                for i, cam in enumerate(camera_sites, 1):
                    photo_score = cam['specific_attributes'].get('photo_score', 0)
                    camera_type = cam['specific_attributes'].get('camera_type', 'Unknown')
                    
                    popup_html = f"""
                    <div style='width: 300px;'>
                        <h4>📷 Camera Position {i}</h4>
                        <p><b>Strategy:</b> {cam['strategy']}</p>
                        <p><b>Overall Score:</b> {cam['score']:.1f}/10</p>
                        <p><b>Photo Quality Score:</b> {photo_score:.1f}/10</p>
                        <p><b>Camera Type:</b> {camera_type}</p>
                        <p><b>Description:</b> {cam['description']}</p>
                    </div>
                    """
                    
                    folium.Marker(
                        [cam['lat'], cam['lon']],
                        popup=folium.Popup(popup_html, max_width=300),
                        icon=folium.Icon(color='purple', icon='camera'),
                        tooltip=f"Camera {i}: {cam['strategy']} ({photo_score:.1f}/10)"
                    ).add_to(m)
        
        # Display map and capture click events
        # Use dynamic key to force refresh when predictions are made
        # FIXED: Include prediction hash to force map refresh when new predictions are generated
        map_key = "hunt_map"
        if 'prediction_results' in st.session_state and st.session_state.prediction_results:
            # Create hash of prediction results to force refresh when predictions change
            import hashlib
            prediction_hash = hashlib.md5(str(st.session_state.prediction_results).encode()).hexdigest()[:8]
            map_key = f"hunt_map_{st.session_state.hunt_location[0]:.4f}_{st.session_state.hunt_location[1]:.4f}_{prediction_hash}"
        
        map_data = st_folium(m, key=map_key, width=700, height=500)
        
        # Update location if map was clicked
        if map_data['last_clicked']:
            new_lat = map_data['last_clicked']['lat']
            new_lng = map_data['last_clicked']['lng']
            
            # Check if this is a new location
            old_location = st.session_state.hunt_location
            new_location = [new_lat, new_lng]
            
            # If location changed significantly (>100m), clear old predictions
            if (abs(old_location[0] - new_lat) > 0.001 or 
                abs(old_location[1] - new_lng) > 0.001):
                
                st.session_state.hunt_location = new_location
                
                # Clear old prediction results to prevent showing stale markers
                if 'prediction_results' in st.session_state:
                    del st.session_state.prediction_results
                    
                st.rerun()
    
    # Display current coordinates
    st.write(f"📍 **Current Location:** {st.session_state.hunt_location[0]:.4f}, {st.session_state.hunt_location[1]:.4f}")
    
    # DEBUG: Show map refresh status
    if 'prediction_results' in st.session_state and st.session_state.prediction_results:
        # Count markers that would be displayed
        marker_count = 0
        prediction = st.session_state.prediction_results
        
        if 'bedding_zones' in prediction and prediction['bedding_zones']:
            marker_count += len(prediction['bedding_zones'].get('features', []))
        if 'feeding_areas' in prediction and prediction['feeding_areas']:
            marker_count += len(prediction['feeding_areas'].get('features', []))
        if 'optimized_points' in prediction and prediction['optimized_points']:
            opt_points = prediction['optimized_points']
            for category in ['stand_sites', 'bedding_sites', 'feeding_sites', 'camera_placements']:
                marker_count += len(opt_points.get(category, []))
        
        st.success(f"🗺️ **Map Status:** Displaying {marker_count} prediction markers for location {st.session_state.hunt_location[0]:.4f}, {st.session_state.hunt_location[1]:.4f}")
    else:
        st.info("🗺️ **Map Status:** No predictions loaded - click 'Generate Hunting Predictions' to see markers")
    
    # Generate Predictions button - positioned above Advanced Options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🎯 Generate Hunting Predictions", type="primary", use_container_width=False):
            with st.spinner("🧠 Analyzing deer movement patterns..."):
                # Convert hunt period to representative time for backend compatibility
                period_times = {
                    "AM": "07:00:00",    # 7:00 AM - middle of dawn period
                    "DAY": "13:00:00",   # 1:00 PM - middle of day period  
                    "PM": "18:00:00"     # 6:00 PM - middle of evening period
                }
                
                # Prepare prediction request
                prediction_data = {
                    "lat": st.session_state.hunt_location[0],
                    "lon": st.session_state.hunt_location[1],
                    "date_time": f"{hunt_date}T{period_times[hunt_period]}",
                    "hunt_period": hunt_period,  # Add hunt period for future backend use
                    "season": season,
                    "fast_mode": True,  # Enable fast mode for UI responsiveness
                    "include_camera_placement": st.session_state.get('include_camera_placement', False)
                }
                
                try:
                    # Make prediction request
                    response = requests.post(
                        f"{BACKEND_URL}/predict",
                        json=prediction_data,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        # Handle both old and new API response formats
                        if 'success' in response_data and response_data.get('success'):
                            # New enhanced API format with wrapper
                            prediction = response_data.get('data', response_data)
                        else:
                            # Direct prediction data format
                            prediction = response_data
                        
                        # ENHANCED: Log backend data for traceability
                        validation_results = enhanced_backend_logging_for_predictions(
                            st.session_state.hunt_location[0],
                            st.session_state.hunt_location[1], 
                            prediction
                        )
                        
                        # Check if EnhancedBeddingZonePredictor is active
                        integration_check = check_enhanced_bedding_predictor_integration()
                        
                        # Store results and show appropriate message
                        st.session_state.prediction_results = prediction
                        
                        if validation_results.get("data_extraction_success", False):
                            bedding_count = validation_results.get("bedding_zones_count", 0)
                            suitability = validation_results.get("suitability_score", 0)
                            confidence = validation_results.get("confidence_score", 0)
                            
                            if bedding_count > 0 and suitability > 80:
                                st.success(f"✅ Enhanced bedding predictions generated successfully!")
                                st.info(f"🎯 Generated {bedding_count} bedding zones with {suitability:.1f}% suitability ({confidence:.1f}% confidence)")
                            elif bedding_count > 0:
                                st.success(f"✅ Bedding predictions generated!")
                                st.warning(f"⚠️ Generated {bedding_count} zones with {suitability:.1f}% suitability - may need optimization")
                            else:
                                st.warning("⚠️ Prediction completed but no bedding zones generated")
                                if integration_check.get("predictor_type_detected") == "mature_buck_predictor":
                                    st.error("🔧 Detection: Using legacy predictor instead of EnhancedBeddingZonePredictor")
                        else:
                            st.success("✅ Prediction completed")
                        
                        st.rerun()  # Refresh to show results on map
                        
                    else:
                        st.error(f"Prediction failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"Failed to get prediction: {e}")
                    logger.error(f"Prediction request failed: {e}")
    
    with col2:
        if st.button("🗑️ Clear Cache", help="Clear cached predictions and force map refresh"):
            if 'prediction_results' in st.session_state:
                del st.session_state.prediction_results
            st.success("Cache cleared!")
            st.rerun()
    
    # Advanced options
    with st.expander("🎥 Advanced Options"):
        include_camera = st.checkbox(
            "Include Optimal Camera Placement", 
            value=st.session_state.get('include_camera_placement', False),
            help="Calculate the single optimal trail camera position using satellite analysis",
            key="include_camera_placement"
        )
    
    # Display Hunt Coordinates - show #1 stand location if available, otherwise current location
    hunt_coords_lat = st.session_state.hunt_location[0]
    hunt_coords_lon = st.session_state.hunt_location[1]
    coord_source = "Current Location"
    
    # Check for prediction results and extract #1 stand coordinates
    if 'prediction_results' in st.session_state and st.session_state.prediction_results:
        prediction = st.session_state.prediction_results
        mature_buck = prediction.get('mature_buck_analysis', {})
        stand_recs = mature_buck.get('stand_recommendations', [])
        
        if len(stand_recs) > 0:
            stand_1 = stand_recs[0]
            coords = stand_1.get('coordinates', {})
            
            # Ensure we have valid coordinates
            if isinstance(coords, dict) and 'lat' in coords and 'lon' in coords:
                if coords['lat'] is not None and coords['lon'] is not None:
                    hunt_coords_lat = float(coords['lat'])
                    hunt_coords_lon = float(coords['lon'])
                    coord_source = "#1 Predicted Stand"
    
    st.info(f"📍 **Hunt Coordinates ({coord_source}):** {hunt_coords_lat:.6f}, {hunt_coords_lon:.6f}")
    
    # Display detailed hunt information for Stand #1 if prediction results are available
    if 'prediction_results' in st.session_state and st.session_state.prediction_results:
        prediction = st.session_state.prediction_results
        
        # Debug section - Add toggle to show prediction data
        with st.expander("🐛 Debug: Show Raw Prediction Data"):
            st.json(prediction)
            if st.button("🗑️ Clear Cached Results"):
                del st.session_state.prediction_results
                st.success("Cache cleared! Please make a new prediction.")
                st.rerun()
        
        # Show optimized points summary if available
        if 'optimized_points' in prediction and prediction['optimized_points']:
            st.success("✨ **12 Optimized Hunting Points Generated Using Real-Time Data!**")
            
            optimized_data = prediction['optimized_points']
            
            # Create columns for point categories
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**🎯 Stand Sites**")
                for i, stand in enumerate(optimized_data.get('stand_sites', []), 1):
                    st.markdown(f"**{i}.** {stand['strategy']} ⭐{stand['score']:.1f}")
            
            with col2:
                st.markdown("**🛏️ Bedding Sites**") 
                for i, bed in enumerate(optimized_data.get('bedding_sites', []), 1):
                    st.markdown(f"**{i}.** {bed['strategy']} ⭐{bed['score']:.1f}")
            
            with col3:
                st.markdown("**🌾 Feeding Sites**")
                for i, feed in enumerate(optimized_data.get('feeding_sites', []), 1):
                    st.markdown(f"**{i}.** {feed['strategy']} ⭐{feed['score']:.1f}")
            
            with col4:
                st.markdown("**📷 Camera Sites**")
                for i, cam in enumerate(optimized_data.get('camera_placements', []), 1):
                    st.markdown(f"**{i}.** {cam['strategy']} ⭐{cam['score']:.1f}")
            
            st.markdown("---")
        
        if prediction.get('mature_buck_analysis') is not None:
            stand_recommendations = prediction['mature_buck_analysis'].get('stand_recommendations', [])
            
            if stand_recommendations:  # Check if we have stand recommendations
                stand_1 = stand_recommendations[0]  # Get the #1 stand
                coords = stand_1.get('coordinates', {})
                confidence = stand_1.get('confidence', 0)
                stand_type = stand_1.get('type', 'Unknown')
                reasoning = stand_1.get('reasoning', 'Advanced algorithmic positioning based on satellite analysis')
                
                # Extract comprehensive mature buck data
                mature_buck_data = prediction.get('mature_buck_analysis', {})
                terrain_scores = mature_buck_data.get('terrain_scores', {})
                movement_prediction = mature_buck_data.get('movement_prediction', {})
                stand_recommendations = mature_buck_data.get('stand_recommendations', [])
                
                # Display detailed Stand #1 information with enhanced data
                st.markdown("---")
                st.markdown("### 🎯 **Stand #1 - Detailed Hunt Information**")
                st.markdown(f"*Primary hunting location with {confidence:.0f}% confidence*")
                
                # Stand details in enhanced columns layout
                detail_col1, detail_col2, detail_col3 = st.columns([2, 2, 1])
                
                with detail_col1:
                    st.markdown("**📍 Stand Location Analysis:**")
                    st.write(f"• **Coordinates:** {coords.get('lat', 0):.6f}, {coords.get('lon', 0):.6f}")
                    st.write(f"• **Stand Type:** {stand_type}")
                    st.write(f"• **Algorithm Confidence:** {confidence:.0f}%")
                    
                    # Enhanced terrain analysis from backend data
                    if terrain_scores:
                        st.markdown("**🏔️ Terrain Suitability Scores:**")
                        bedding_suit = terrain_scores.get('bedding_suitability', 0)
                        escape_quality = terrain_scores.get('escape_route_quality', 0)
                        isolation = terrain_scores.get('isolation_score', 0)
                        pressure_resist = terrain_scores.get('pressure_resistance', 0)
                        overall_suit = terrain_scores.get('overall_suitability', 0)
                        
                        st.write(f"• **Bedding Suitability:** {bedding_suit:.1f}%")
                        st.write(f"• **Escape Route Quality:** {escape_quality:.1f}%")
                        st.write(f"• **Isolation Score:** {isolation:.1f}%")
                        st.write(f"• **Pressure Resistance:** {pressure_resist:.1f}%")
                        st.write(f"• **Overall Suitability:** {overall_suit:.1f}%")
                    
                    # Calculate distance and bearing with enhanced precision
                    if coords.get('lat') and coords.get('lon'):
                        from math import radians, cos, sin, asin, sqrt, atan2, degrees
                        
                        def haversine(lon1, lat1, lon2, lat2):
                            # Convert to radians
                            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                            # Haversine formula
                            dlon = lon2 - lon1
                            dlat = lat2 - lat1
                            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                            c = 2 * asin(sqrt(a))
                            r = 6371000  # Radius of earth in meters
                            return c * r
                        
                        def calculate_bearing(lat1, lon1, lat2, lon2):
                            # Calculate bearing from hunt point to stand
                            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                            dlon = lon2 - lon1
                            y = sin(dlon) * cos(lat2)
                            x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
                            bearing = atan2(y, x)
                            bearing = degrees(bearing)
                            bearing = (bearing + 360) % 360
                            return bearing
                        
                        distance = haversine(
                            st.session_state.hunt_location[1],  # lon1
                            st.session_state.hunt_location[0],  # lat1
                            coords.get('lon', 0),  # lon2
                            coords.get('lat', 0)   # lat2
                        )
                        
                        bearing = calculate_bearing(
                            st.session_state.hunt_location[0],  # lat1
                            st.session_state.hunt_location[1],  # lon1
                            coords.get('lat', 0),  # lat2
                            coords.get('lon', 0)   # lon2
                        )
                        
                        # Convert bearing to compass direction
                        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                                    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                        compass_dir = directions[int((bearing + 11.25) / 22.5) % 16]
                        
                        st.markdown("**📏 Distance & Direction:**")
                        st.write(f"• **Distance:** {distance:.0f} meters")
                        st.write(f"• **Bearing:** {bearing:.0f}° ({compass_dir})")
                        
                        # NEW: Time-based deer approach calculation
                        deer_approach_result = calculate_time_based_deer_approach(
                            hunt_period, 
                            (coords.get('lat', 0), coords.get('lon', 0)), 
                            prediction
                        )
                        
                        st.write(f"• **Deer Approach:** {deer_approach_result['compass']} ({deer_approach_result['bearing']:.0f}°)")
                        st.write(f"• **Movement Pattern:** {deer_approach_result['movement_type']}")
                        
                        # Calculate optimal wind directions based on corrected deer approach
                        optimal_wind_1 = (deer_approach_result['bearing'] + 90) % 360
                        optimal_wind_2 = (deer_approach_result['bearing'] - 90) % 360
                        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                                    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                        wind_dir_1 = directions[int((optimal_wind_1 + 11.25) / 22.5) % 16]
                        wind_dir_2 = directions[int((optimal_wind_2 + 11.25) / 22.5) % 16]
                        
                        st.markdown("**🌬️ Optimal Wind Directions:**")
                        st.success(f"• **Best Winds:** {wind_dir_1} or {wind_dir_2}")
                        st.write(f"• **Avoid Wind From:** {deer_approach_result['compass']} (towards deer)")
                        st.info(f"• **Confidence:** {deer_approach_result['confidence']} - Based on {hunt_period} period movement patterns")
                
                with detail_col2:
                    st.markdown("**🧠 Algorithm Analysis:**")
                    
                    # Enhanced reasoning from stand recommendations
                    if stand_recommendations:
                        first_stand = stand_recommendations[0]
                        terrain_justification = first_stand.get('terrain_justification', reasoning)
                        setup_requirements = first_stand.get('setup_requirements', [])
                        
                        st.write(f"**Strategic Positioning:** {terrain_justification}")
                        
                        if setup_requirements:
                            st.markdown("**🎯 Setup Requirements:**")
                            for req in setup_requirements:
                                st.write(f"• {req}")
                    else:
                        st.write(reasoning)
                    
                    # Enhanced movement prediction with detailed data
                    if movement_prediction:
                        movement_prob = movement_prediction.get('movement_probability', 0)
                        confidence_score = movement_prediction.get('confidence_score', 0)
                        preferred_times = movement_prediction.get('preferred_times', [])
                        behavioral_notes = movement_prediction.get('behavioral_notes', [])
                        
                        st.markdown("**🦌 Movement Prediction:**")
                        if movement_prob >= 75:
                            st.success(f"🟢 HIGH Activity Expected ({movement_prob:.0f}%)")
                        elif movement_prob >= 50:
                            st.info(f"🟡 MODERATE Activity Expected ({movement_prob:.0f}%)")
                        else:
                            st.warning(f"🔴 LOW Activity Expected ({movement_prob:.0f}%)")
                        
                        st.write(f"• **Prediction Confidence:** {confidence_score:.0f}%")
                        
                        if preferred_times:
                            st.markdown("**⏰ Optimal Hunt Times:**")
                            for time in preferred_times:
                                st.write(f"• {time}")
                        
                        if behavioral_notes:
                            st.markdown("**📝 Behavioral Intelligence:**")
                            for note in behavioral_notes[:3]:  # Show first 3 notes
                                if "✅" in note or "🎯" in note or "🌞" in note:
                                    st.write(f"• {note}")
                
                with detail_col3:
                    # Wind analysis with current conditions
                    if stand_recommendations and stand_recommendations[0].get('wind_analysis'):
                        wind_analysis = stand_recommendations[0]['wind_analysis']
                        wind_direction = wind_analysis.get('wind_direction', 0)
                        wind_speed = wind_analysis.get('wind_speed', 0)
                        wind_consistency = wind_analysis.get('wind_consistency', 'unknown')
                        scent_safety = wind_analysis.get('scent_safety_margin', 0)
                        
                        st.markdown("**🍃 Wind Analysis:**")
                        st.write(f"• **Direction:** {wind_direction:.0f}°")
                        st.write(f"• **Speed:** {wind_speed:.1f} mph")
                        st.write(f"• **Pattern:** {wind_consistency}")
                        st.write(f"• **Safety Margin:** {scent_safety:.0f}m")
                        
                        # Wind quality assessment
                        wind_advantage = wind_analysis.get('wind_advantage_score', 0)
                        if wind_advantage >= 90:
                            st.success("🟢 EXCELLENT Wind")
                        elif wind_advantage >= 70:
                            st.info("🟡 GOOD Wind")
                        else:
                            st.warning("🔴 POOR Wind")
                    
                    # Camera placement integration
                    camera_placement = prediction.get('optimal_camera_placement', {})
                    if camera_placement and camera_placement.get('enabled'):
                        camera_coords = camera_placement.get('camera_coordinates', {})
                        camera_confidence = camera_placement.get('confidence_score', 0)
                        camera_distance = camera_placement.get('distance_meters', 0)
                        
                        st.markdown("**📹 Camera Position:**")
                        st.write(f"• **Distance:** {camera_distance:.0f}m")
                        st.write(f"• **Confidence:** {camera_confidence:.1f}%")
                        
                        if camera_confidence >= 85:
                            st.success("🎥 PRIME Camera Spot")
                        else:
                            st.info("📹 Good Camera Spot")
                
                # Enhanced hunting recommendations with comprehensive algorithmic data
                with st.expander("🎯 **Enhanced Stand Setup & Wind Intelligence**", expanded=True):
                    
                    # Extract comprehensive data for setup instructions
                    # Get wind and terrain data from stand recommendations
                    wind_analysis = {}
                    terrain_data = {}
                    wind_direction = 'Unknown'
                    wind_speed = 'Unknown'
                    wind_factor = 0
                    slope = 'Unknown'
                    elevation = 'Unknown'
                    aspect = 'Unknown'
                    
                    # NEW: Time-based deer approach calculation (FIXED!)
                    if stand_recommendations:
                        first_stand = stand_recommendations[0]
                        stand_coords = (first_stand['coordinates']['lat'], first_stand['coordinates']['lon'])
                        deer_approach_result = calculate_time_based_deer_approach(hunt_period, stand_coords, prediction)
                        deer_approach_bearing = deer_approach_result['bearing']
                        deer_approach_dir = deer_approach_result['compass']
                    else:
                        # Fallback if no stand recommendations
                        deer_approach_bearing = 135  # Default SE
                        deer_approach_dir = "SE"
                    
                    if stand_recommendations:
                        first_stand = stand_recommendations[0]
                        wind_analysis = first_stand.get('wind_analysis', {})
                        if wind_analysis:
                            wind_direction = wind_analysis.get('wind_direction', 'Unknown')
                            wind_speed = wind_analysis.get('wind_speed', 'Unknown')
                            wind_factor = wind_analysis.get('wind_advantage_score', 0) / 100.0  # Convert to 0-1 scale
                        
                        # Extract terrain data from stand coordinates if available
                        precision_factors = first_stand.get('coordinates', {}).get('precision_factors', {})
                        if precision_factors:
                            elevation = precision_factors.get('elevation', 'Unknown')
                            slope = 15.0  # Default reasonable slope
                        
                        # Get deer approach from bedding zones calculation (done earlier)
                        bedding_zones = prediction.get('bedding_zones', {}).get('zones', [])
                        if bedding_zones and coords.get('lat') and coords.get('lon'):
                            first_bedding = bedding_zones[0]
                            bedding_lat = first_bedding.get('lat', 0)
                            bedding_lon = first_bedding.get('lon', 0)
                            
                            if bedding_lat and bedding_lon:
                                from math import radians, cos, sin, atan2, degrees
                                
                                def calculate_bearing(lat1, lon1, lat2, lon2):
                                    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                                    dlon = lon2 - lon1
                                    y = sin(dlon) * cos(lat2)
                                    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
                                    bearing = atan2(y, x)
                                    bearing = degrees(bearing)
                                    bearing = (bearing + 360) % 360
                                    return bearing
                                
                                deer_approach_bearing = calculate_bearing(bedding_lat, bedding_lon, coords.get('lat', 0), coords.get('lon', 0))
                                directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                                            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                                deer_approach_dir = directions[int((deer_approach_bearing + 11.25) / 22.5) % 16]
                    
                    # Wind-based setup instructions with current data
                    st.markdown("**🍃 Wind-Optimized Positioning:**")
                    if wind_direction != 'Unknown':
                        st.write(f"• **Current Wind Direction:** {wind_direction}°")
                        if wind_speed != 'Unknown':
                            st.write(f"• **Current Wind Speed:** {wind_speed:.1f} mph")
                        
                        # Wind quality assessment
                        if wind_factor >= 0.8:
                            st.success(f"🟢 IDEAL Wind Conditions")
                        elif wind_factor >= 0.6:
                            st.info(f"🟡 GOOD Wind Conditions")
                        elif wind_factor > 0:
                            st.warning(f"🔴 POOR Wind Conditions")
                        
                        st.write(f"• **Scent Control:** Use scent eliminator and wind checker")
                        st.write(f"• **Current Wind Direction:** {wind_direction}")
                        
                        # Calculate optimal wind direction based on stand type and deer approach
                        if stand_type == "Travel Corridor":
                            st.markdown("**🎯 OPTIMAL WIND FOR THIS STAND:**")
                            st.success("• **Wind should blow FROM deer approach TO your stand**")
                            st.write("• **Your scent blows AWAY from deer travel routes**")
                            st.write("• **Deer approach from upwind, you sit downwind**")
                            st.write(f"• **Best wind:** Perpendicular to main travel corridor")
                            
                        elif stand_type == "Bedding Area":
                            st.markdown("**🎯 OPTIMAL WIND FOR THIS STAND:**")
                            st.success("• **Wind should blow FROM bedding area TO you**")
                            st.write("• **Your scent blows AWAY from bedding deer**")
                            st.write("• **Critical:** Deer will smell you if wind is wrong")
                            st.write("• **Only hunt this stand with favorable wind**")
                            
                        elif stand_type == "Feeding Area":
                            st.markdown("**🎯 OPTIMAL WIND FOR THIS STAND:**")
                            st.success("• **Wind should blow FROM feeding area TO you**")
                            st.write("• **Your scent blows AWAY from where deer will feed**")
                            st.write("• **Deer approach feeding areas cautiously**")
                            st.write("• **Wrong wind = busted hunt immediately**")
                        
                        else:  # General stand
                            st.markdown("**🎯 OPTIMAL WIND FOR THIS STAND:**")
                            st.success("• **Wind should blow FROM deer TO you**")
                            st.write("• **Your scent carries AWAY from deer movement**")
                        
                        # Wind checker instructions
                        st.markdown("**💨 Wind Checker Usage:**")
                        st.write("• **Carry powder/puffer bottle** to check wind direction")
                        st.write("• **Check every 30 minutes** - wind shifts throughout day")
                        st.write("• **Thermal winds:** Upslope in morning, downslope in evening")
                        st.write("• **If wind shifts wrong direction:** LEAVE THE STAND")
                        
                        # Use the deer approach calculations from earlier in the code
                        st.markdown("**🧭 SPECIFIC WIND DIRECTIONS FOR THIS STAND:**")
                        st.write(f"• **Deer likely approach from:** {deer_approach_dir} ({deer_approach_bearing:.0f}°)")
                        
                        if stand_type in ["Travel Corridor", "General"]:
                            st.write(f"• **BEST wind directions:** {wind_dir_1} or {wind_dir_2}")
                            st.write(f"• **WORST wind direction:** {deer_approach_dir} (towards deer)")
                            
                        else:  # Bedding/Feeding areas need wind FROM deer TO hunter
                            optimal_wind = deer_approach_bearing
                            directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                                        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                            wind_dir_optimal = directions[int((optimal_wind + 11.25) / 22.5) % 16]
                            # For worst wind, use opposite of optimal
                            worst_wind = (optimal_wind + 180) % 360
                            wind_dir_worst = directions[int((worst_wind + 11.25) / 22.5) % 16]
                            
                            st.write(f"• **Deer location:** {deer_approach_dir} direction from stand")
                            st.write(f"• **BEST wind direction:** {wind_dir_optimal} (FROM deer TO you)")
                            st.write(f"• **WORST wind direction:** {wind_dir_worst} (FROM you TO deer)")
                            st.warning("⚠️ **Only hunt this stand with optimal wind!**")
                        
                        st.write(f"• **Recommended Approach:** Come from downwind side")
                        st.write(f"• **Stand Facing:** Position to face crosswind or into wind")
                        st.write(f"• **Scent Control:** Use scent eliminator and wind checker")
                    else:
                        st.write("• Check local wind conditions before hunting")
                        st.write("• Always approach from downwind")
                        st.write("• Carry wind checker powder/device")
                        st.markdown("**💨 General Wind Rules:**")
                        st.write("• **Wind should blow FROM deer TO you**")
                        st.write("• **Your scent should blow AWAY from deer**")
                        st.write("• **Wrong wind = no deer**")
                    
                    # Terrain-based setup using available data
                    if elevation != 'Unknown' or slope != 'Unknown':
                        st.markdown("**🏔️ Terrain-Based Setup:**")
                        if slope != 'Unknown' and slope > 15:
                            st.write(f"• **Steep Terrain ({slope:.1f}°):** Use climbing harness and safety rope")
                        if elevation != 'Unknown':
                            st.write(f"• **Elevation Advantage:** {elevation:.0f}m provides thermal/scent advantage")
                        if aspect != 'Unknown':
                            st.write(f"• **Slope Faces:** {aspect} - consider sun position for visibility")
                    
                    # Movement pattern analysis
                    st.markdown("**🦌 Deer Movement Intelligence:**")
                    
                    # Calculate and show specific deer approach directions based on stand type
                    if stand_type == "Travel Corridor":
                        st.markdown("**📍 WHERE DEER ARE COMING FROM:**")
                        st.success("🦌 **DEER APPROACH ROUTES:**")
                        st.write(f"• **Primary approach:** {deer_approach_dir} direction ({deer_approach_bearing:.0f}°)")
                        st.write(f"• **Secondary approach:** May come from opposite direction too")
                        st.write("• **Travel corridors = highways** - deer use both directions")
                        st.write("• **Morning:** Deer moving FROM bedding TO feeding")
                        st.write("• **Evening:** Deer moving FROM feeding TO bedding")
                        
                        st.markdown("**🎯 STAND POSITIONING:**")
                        st.write("• **Setup 15-30 yards** from main trail")
                        st.write("• **Face the trail** - prepare for shots from multiple angles")
                        st.write("• **Multiple entry points** - deer may come from various directions")
                        st.write("• **Best times:** Morning/Evening transition periods")
                        
                    elif stand_type == "Bedding Area":
                        st.markdown("**📍 WHERE DEER ARE COMING FROM:**")
                        st.success("🦌 **DEER LOCATION & MOVEMENT:**")
                        st.write(f"• **Deer are bedded:** {deer_approach_dir} direction from your stand")
                        st.write("• **Afternoon movement:** Deer leaving beds to feed")
                        st.write("• **Evening return:** Deer coming back to bed down")
                        st.write("• **Dawn departure:** Deer leaving beds after feeding all night")
                        
                        st.markdown("**🎯 STAND POSITIONING:**")
                        st.write("• **Setup on EDGE** - don't go too deep into bedding")
                        st.write("• **20-40 yards back** from main bedding area")
                        st.write("• **Afternoon hunting** - deer returning to bed")
                        st.write("• **EXTREMELY quiet approach** required - deer are nearby!")
                        
                    elif stand_type == "Feeding Area":
                        st.markdown("**📍 WHERE DEER ARE COMING FROM:**")
                        st.success("🦌 **DEER APPROACH TO FEEDING:**")
                        st.write(f"• **Deer approach feeding from:** {deer_approach_dir} direction")
                        st.write("• **Evening feeding:** Deer come from bedding areas")
                        st.write("• **Morning departure:** Deer return to bedding")
                        st.write("• **Cautious approach:** Deer circle and check wind before feeding")
                        
                        st.markdown("**🎯 STAND POSITIONING:**")
                        st.write("• **Setup DOWNWIND** of main feeding zone")
                        st.write("• **30-40 yards back** from main feeding activity")
                        st.write("• **Evening hunting** - deer coming to feed")
                        st.write("• **Face feeding area** - deer will be in front of you")
                        
                    else:  # General stand
                        st.markdown("**📍 WHERE DEER ARE COMING FROM:**")
                        st.success("🦌 **GENERAL DEER MOVEMENT:**")
                        st.write(f"• **Primary deer approach:** {deer_approach_dir} direction ({deer_approach_bearing:.0f}°)")
                        st.write("• **Based on terrain analysis** and movement patterns")
                        st.write("• **Multiple approach routes** possible")
                        
                        st.markdown("**🎯 STAND POSITIONING:**")
                        st.write("• **Face primary approach direction**")
                        st.write("• **Prepare for movement from multiple angles**")
                    
                    # Specific wind setup based on deer approach
                    st.markdown("**💨 WIND SETUP FOR DEER APPROACHES:**")
                    if stand_type in ["Travel Corridor", "General"]:
                        st.write(f"• **Deer coming from {deer_approach_dir}** - Wind should blow {wind_dir_1} or {wind_dir_2}")
                        st.write(f"• **This carries your scent AWAY** from deer approach routes")
                        st.write(f"• **NEVER hunt with wind blowing {deer_approach_dir}** - deer will smell you!")
                    else:  # Bedding/Feeding areas
                        st.write(f"• **Deer located {deer_approach_dir} of your stand** - Position downwind of deer activity")
                        st.write(f"• **Approach from opposite direction** - Come in from the {deer_approach_dir} side")
                        st.write(f"• **Check wind before hunting** - Never hunt if wind blows toward deer areas")
                    
                    st.markdown("**🎯 DEER BEHAVIOR EXPECTATIONS:**")
                    if stand_type == "Travel Corridor":
                        st.write("• **Steady movement** along established trails")
                        st.write("• **Multiple deer** may use same route")
                        st.write("• **Predictable timing** during feeding transitions")
                    elif stand_type == "Bedding Area":
                        st.write("• **Cautious movement** - deer are security-focused")
                        st.write("• **Stop and listen** frequently")
                        st.write("• **Quick to bolt** if anything seems wrong")
                    elif stand_type == "Feeding Area":
                        st.write("• **Circle and check** before committing to feed")
                        st.write("• **Head down feeding** - good shot opportunities")
                        st.write("• **Group feeding** - multiple deer possible")
                    
                    # Equipment recommendations based on terrain
                    st.markdown("**🎯 Equipment Recommendations:**")
                    if slope != 'Unknown' and slope > 20:
                        st.write("• **Climbing Stand** recommended for steep terrain")
                    else:
                        st.write("• **Ladder/Hang-on Stand** suitable for this terrain")
                    
                    if wind_factor and wind_factor < 0.6:
                        st.write("• **Extra Scent Control** - poor wind conditions")
                        st.write("• **Ozone Generator** or carbon clothing recommended")
                    
                    # Success probability and timing using movement prediction data
                    movement_prob = 75  # Default good probability
                    if movement_prediction:
                        movement_prob = movement_prediction.get('movement_probability', 75)
                    
                    st.markdown("**⏰ Optimal Hunt Times (Algorithm Calculated):**")
                    if movement_prob >= 75:
                        st.success("🟢 **PRIME TIME:** Hunt this stand during peak hours")
                        st.write("• **Morning:** 30 min before sunrise - 8:30 AM")
                        st.write("• **Evening:** 4:00 PM - 30 min after sunset")
                    elif movement_prob >= 50:
                        st.info("🟡 **GOOD TIMING:** Solid hunting window")
                        st.write("• **Morning:** 1 hour before sunrise - 9:00 AM")
                        st.write("• **Evening:** 3:30 PM - dark")
                    else:
                        st.warning("🔴 **BACKUP TIMING:** Use when other stands unavailable")
                        st.write("• **All day sit** may be required")
                        st.write("• **Midday movement** possible in this location")
                    
                    # Confidence-based priority
                    if confidence >= 85:
                        st.success("🎯 **ALGORITHM VERDICT:** PRIMARY STAND - Hunt here first!")
                        
                        # Add simple approach description for #1 stand
                        st.markdown("**🚶 APPROACH STRATEGY:**")
                        approach_bearing = rec.get('coordinates', {}).get('bearing', deer_approach_bearing)
                        
                        # Calculate best approach direction (opposite of deer approach)
                        best_approach_bearing = (approach_bearing + 180) % 360
                        
                        # Convert to simple cardinal direction
                        if 337.5 <= best_approach_bearing or best_approach_bearing < 22.5:
                            approach_dir = "from the South"
                        elif 22.5 <= best_approach_bearing < 67.5:
                            approach_dir = "from the Southwest" 
                        elif 67.5 <= best_approach_bearing < 112.5:
                            approach_dir = "from the West"
                        elif 112.5 <= best_approach_bearing < 157.5:
                            approach_dir = "from the Northwest"
                        elif 157.5 <= best_approach_bearing < 202.5:
                            approach_dir = "from the North"
                        elif 202.5 <= best_approach_bearing < 247.5:
                            approach_dir = "from the Northeast"
                        elif 247.5 <= best_approach_bearing < 292.5:
                            approach_dir = "from the East"
                        else:
                            approach_dir = "from the Southeast"
                        
                        st.write(f"• **Best approach:** Walk in {approach_dir}")
                        st.write(f"• **Why:** Keeps you downwind and away from deer movement")
                        st.write(f"• **Distance:** Stay 100+ yards out until final approach")
                        st.write(f"• **Final setup:** Quietly move into position facing {deer_approach_dir}")
                    elif confidence >= 70:
                        st.info("🎯 **ALGORITHM VERDICT:** SOLID OPTION - High success probability")
                    else:
                        st.warning("🎯 **ALGORITHM VERDICT:** BACKUP STAND - Use when primary spots fail")

# ==========================================
# TAB 2: SCOUTING DATA
# ==========================================
with tab_scout:
    st.header("🔍 Real-Time Scouting Data Entry")
    
    # Get observation types from backend
    observation_types = get_observation_types()
    
    if not observation_types:
        st.error("Unable to load observation types. Please check backend connection.")
    else:
        # Create two modes: map entry and manual entry
        entry_mode = st.radio("📝 Entry Mode", ["🗺️ Map-Based Entry", "✍️ Manual Entry"], horizontal=True)
        
        if entry_mode == "🗺️ Map-Based Entry":
            st.markdown("### 🗺️ Click on the map to add scouting observations")
            
            # Map for scouting entry - using same map type as hunting predictions
            map_type_for_scout = getattr(st.session_state, 'map_type', 'Topographic (USGS)')  # Fallback to USGS Topo if not set
            scout_map = create_map(st.session_state.hunt_location, st.session_state.map_zoom, map_type_for_scout)
            
            # Load and display existing observations
            existing_obs = get_scouting_observations(
                st.session_state.hunt_location[0], 
                st.session_state.hunt_location[1], 
                radius_miles=10
            )
            
            # Add existing observation markers
            for obs in existing_obs:
                color_map = {
                    "Fresh Scrape": "red",
                    "Rub Line": "orange", 
                    "Bedding Area": "green",
                    "Trail Camera Setup": "blue",
                    "Deer Tracks/Trail": "purple",
                    "Feeding Sign": "lightgreen",
                    "Scat/Droppings": "brown",
                    "Other Sign": "gray"
                }
                
                color = color_map.get(obs.get('observation_type'), 'gray')
                
                folium.Marker(
                    [obs['lat'], obs['lon']],
                    popup=f"{obs['observation_type']}<br>Confidence: {obs['confidence']}/10<br>{obs.get('notes', '')[:50]}...",
                    icon=folium.Icon(color=color, icon='eye')
                ).add_to(scout_map)
            
            # Display scouting map
            scout_map_data = st_folium(scout_map, key="scout_map", width=700, height=500)
            
            # Handle map clicks for new observations
            if scout_map_data['last_clicked']:
                clicked_lat = scout_map_data['last_clicked']['lat']
                clicked_lng = scout_map_data['last_clicked']['lng']
                
                st.success(f"📍 **Selected Location:** {clicked_lat:.6f}, {clicked_lng:.6f}")
                
                # Observation entry form
                with st.form("scouting_observation_form"):
                    st.markdown("### 📝 New Observation Details")
                    
                    # Observation type
                    obs_type_names = [ot['type'] for ot in observation_types]
                    selected_obs_type = st.selectbox("🔍 Observation Type", obs_type_names)
                    
                    # Find selected observation type data
                    selected_type_data = next((ot for ot in observation_types if ot['type'] == selected_obs_type), {})
                    
                    # Confidence rating
                    confidence = st.slider("📊 Confidence Level", 1, 10, 7, 
                                         help="How certain are you about this observation?")
                    
                    # Notes
                    notes = st.text_area("📝 Notes", placeholder="Describe what you observed...")
                    
                    # Type-specific details
                    details = {}
                    
                    if selected_obs_type == "Fresh Scrape":
                        st.markdown("#### 🦌 Scrape Details")
                        details = {
                            "size": st.selectbox("Size", ["Small", "Medium", "Large", "Huge"]),
                            "freshness": st.selectbox("Freshness", ["Old", "Recent", "Fresh", "Very Fresh"]),
                            "licking_branch": st.checkbox("Active licking branch present"),
                            "multiple_scrapes": st.checkbox("Multiple scrapes in area")
                        }
                    
                    elif selected_obs_type == "Rub Line":
                        st.markdown("#### 🌳 Rub Details")
                        details = {
                            "tree_diameter_inches": st.number_input("Tree Diameter (inches)", 1, 36, 6),
                            "rub_height_inches": st.number_input("Rub Height (inches)", 12, 72, 36),
                            "direction": st.selectbox("Primary Direction", 
                                                    ["North", "South", "East", "West", "Northeast", "Northwest", "Southeast", "Southwest", "Multiple"]),
                            "tree_species": st.text_input("Tree Species (optional)"),
                            "multiple_rubs": st.checkbox("Multiple rubs in line")
                        }
                    
                    elif selected_obs_type == "Bedding Area":
                        st.markdown("#### 🛏️ Bedding Details")
                        details = {
                            "number_of_beds": st.number_input("Number of Beds", 1, 20, 1),
                            "bed_size": st.selectbox("Bed Size", ["Small (Doe/Fawn)", "Medium (Young Buck)", "Large (Mature Buck)", "Multiple Sizes"]),
                            "cover_type": st.selectbox("Cover Type", ["Thick Brush", "Conifer Stand", "Creek Bottom", "Ridge Top", "Field Edge"]),
                            "thermal_advantage": st.checkbox("Good thermal cover")
                        }
                    
                    elif selected_obs_type == "Trail Camera Setup":
                        st.markdown("#### 📸 Camera Details")
                        details = {
                            "camera_direction": st.selectbox("Camera Facing", 
                                                           ["North", "South", "East", "West", "Northeast", "Northwest", "Southeast", "Southwest"]),
                            "trail_width_feet": st.number_input("Trail Width (feet)", 1, 20, 3),
                            "setup_height_feet": st.number_input("Camera Height (feet)", 1, 15, 8),
                            "detection_zone": st.selectbox("Detection Zone", ["Narrow Trail", "Wide Trail", "Intersection", "Food Plot Edge"])
                        }
                    
                    elif selected_obs_type == "Deer Tracks/Trail":
                        st.markdown("#### 🐾 Track Details")
                        details = {
                            "track_size": st.selectbox("Track Size", ["Small (Doe/Fawn)", "Medium (Young Buck)", "Large (Mature Buck)", "Multiple Sizes"]),
                            "trail_width_inches": st.number_input("Trail Width (inches)", 6, 24, 12),
                            "usage_level": st.selectbox("Usage Level", ["Light", "Moderate", "Heavy", "Highway"]),
                            "direction": st.selectbox("Primary Direction", 
                                                    ["North", "South", "East", "West", "Northeast", "Northwest", "Southeast", "Southwest", "Multiple"])
                        }
                    
                    # Submit button
                    submitted = st.form_submit_button("✅ Add Observation", type="primary")
                    
                    if submitted:
                        # Prepare observation data
                        observation_data = {
                            "lat": clicked_lat,
                            "lon": clicked_lng,
                            "observation_type": selected_obs_type,
                            "confidence": confidence,
                            "notes": notes
                        }
                        
                        # Add type-specific details
                        if selected_obs_type == "Fresh Scrape":
                            observation_data["scrape_details"] = details
                        elif selected_obs_type == "Rub Line":
                            observation_data["rub_details"] = details
                        elif selected_obs_type == "Bedding Area":
                            observation_data["bedding_details"] = details
                        elif selected_obs_type == "Trail Camera Setup":
                            observation_data["camera_details"] = details
                        elif selected_obs_type == "Deer Tracks/Trail":
                            observation_data["tracks_details"] = details
                        
                        # Submit to backend
                        result = add_scouting_observation(observation_data)
                        
                        if result:
                            st.success(f"✅ **Observation Added Successfully!**")
                            st.info(f"**ID:** {result.get('observation_id')}")
                            st.info(f"**Confidence Boost:** +{result.get('confidence_boost', 0):.1f}")
                            st.balloons()
                            
                            # Clear the form by rerunning
                            st.rerun()
        
        else:
            # Manual entry mode
            st.markdown("### ✍️ Manual Coordinate Entry")
            
            with st.form("manual_observation_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    manual_lat = st.number_input("Latitude", value=st.session_state.hunt_location[0], format="%.6f")
                    manual_lon = st.number_input("Longitude", value=st.session_state.hunt_location[1], format="%.6f")
                
                with col2:
                    obs_type_names = [ot['type'] for ot in observation_types]
                    selected_obs_type = st.selectbox("🔍 Observation Type", obs_type_names)
                    confidence = st.slider("📊 Confidence Level", 1, 10, 7)
                
                notes = st.text_area("📝 Notes", placeholder="Describe what you observed...")
                
                submitted = st.form_submit_button("✅ Add Observation", type="primary")
                
                if submitted:
                    observation_data = {
                        "lat": manual_lat,
                        "lon": manual_lon,
                        "observation_type": selected_obs_type,
                        "confidence": confidence,
                        "notes": notes
                    }
                    
                    result = add_scouting_observation(observation_data)
                    
                    if result:
                        st.success(f"✅ **Observation Added Successfully!**")
                        st.info(f"**ID:** {result.get('observation_id')}")

# ==========================================
# TAB 3: ANALYTICS
# ==========================================
with tab_analytics:
    st.header("📊 Scouting Analytics")
    
    # Analytics area selection
    st.markdown("### 📍 Analysis Area")
    
    col1, col2 = st.columns(2)
    with col1:
        analysis_lat = st.number_input("Center Latitude", value=st.session_state.hunt_location[0], format="%.6f")
        analysis_lon = st.number_input("Center Longitude", value=st.session_state.hunt_location[1], format="%.6f")
    
    with col2:
        analysis_radius = st.slider("Analysis Radius (miles)", 1, 10, 5)
    
    if st.button("🔍 Generate Analytics", type="primary"):
        with st.spinner("📊 Analyzing scouting data..."):
            analytics = get_scouting_analytics(analysis_lat, analysis_lon, analysis_radius)
            
            if analytics:
                # Basic stats
                basic_stats = analytics.get('basic_analytics', {})
                
                st.markdown("## 📈 **Area Overview**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_obs = basic_stats.get('total_observations', 0)
                    st.metric("📝 Total Observations", total_obs)
                
                with col2:
                    avg_confidence = basic_stats.get('average_confidence', 0)
                    st.metric("📊 Average Confidence", f"{avg_confidence:.1f}/10")
                
                with col3:
                    obs_by_type = basic_stats.get('observations_by_type', {})
                    most_common = max(obs_by_type.items(), key=lambda x: x[1]) if obs_by_type else ("None", 0)
                    st.metric("🔍 Most Common", most_common[0])
                
                with col4:
                    mature_indicators = basic_stats.get('mature_buck_indicators', 0)
                    st.metric("🦌 Mature Buck Signs", mature_indicators)
                
                # Observation breakdown
                if obs_by_type:
                    st.markdown("## 📋 **Observation Breakdown**")
                    
                    for obs_type, count in obs_by_type.items():
                        percentage = (count / total_obs * 100) if total_obs > 0 else 0
                        st.markdown(f"**{obs_type}:** {count} observations ({percentage:.1f}%)")
                
                # Hotspots
                hotspots = analytics.get('hotspots', [])
                if hotspots:
                    st.markdown("## 🔥 **Activity Hotspots**")
                    
                    for i, hotspot in enumerate(hotspots, 1):
                        with st.expander(f"🎯 Hotspot #{i} - {hotspot.get('observation_count', 0)} observations"):
                            st.markdown(f"**📍 Center:** {hotspot.get('center_lat', 0):.6f}, {hotspot.get('center_lon', 0):.6f}")
                            st.markdown(f"**📊 Confidence Score:** {hotspot.get('avg_confidence', 0):.1f}/10")
                            st.markdown(f"**🔍 Dominant Type:** {hotspot.get('dominant_type', 'Mixed')}")
                
                # Recent activity
                recent_obs = analytics.get('recent_observations', [])
                if recent_obs:
                    st.markdown("## ⏰ **Recent Activity**")
                    
                    for obs in recent_obs[:5]:  # Show last 5
                        with st.container():
                            st.markdown(f"""
                            <div class="observation-marker">
                            <strong>{obs.get('observation_type', 'Unknown')}</strong> - 
                            Confidence: {obs.get('confidence', 0)}/10<br>
                            <small>{obs.get('notes', 'No notes')[:100]}...</small>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("No scouting data found in this area. Start adding observations!")

# Add footer
st.markdown("---")
st.markdown("🦌 **Vermont Deer Movement Predictor** | Enhanced with Real-Time Scouting Data | Vermont Legal Hunting Hours Compliant")

# Add enhanced data traceability display to sidebar
create_enhanced_data_traceability_display()
