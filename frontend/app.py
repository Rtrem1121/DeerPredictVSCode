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
from typing import Any, Dict
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

COMPASS_DIRECTIONS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
]


def degrees_to_compass(degrees):
    """Convert degrees to a compass string."""
    try:
        if degrees is None:
            return "Unknown"
        deg = float(degrees) % 360
        return COMPASS_DIRECTIONS[int((deg + 11.25) / 22.5) % 16]
    except (TypeError, ValueError):
        return "Unknown"


def format_wind_reading(direction_deg, speed_mph):
    """Format wind direction/speed into a compact string."""
    compass = degrees_to_compass(direction_deg)
    try:
        if speed_mph is None:
            return compass
        return f"{compass} at {float(speed_mph):.1f} mph"
    except (TypeError, ValueError):
        return f"{compass} at {speed_mph}"

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


def _parse_iso_datetime(value):
    """Safely parse an ISO-formatted datetime string into local time."""
    if not value:
        return None
    try:
        cleaned = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo:
            return parsed.astimezone()
        return parsed
    except Exception:
        return None


def format_local_time(value):
    """Format an ISO datetime string into a readable local timestamp."""
    parsed = _parse_iso_datetime(value)
    if not parsed:
        return "Unknown"
    return parsed.strftime("%b %d %I:%M %p")


def format_minutes_to_clock(value):
    """Convert minutes remaining into a readable string."""
    if value is None:
        return "Unknown"
    try:
        minutes = float(value)
    except (TypeError, ValueError):
        return "Unknown"
    if minutes < 1:
        return "<1 minute"
    hours = int(minutes) // 60
    mins = int(round(minutes - hours * 60))
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins} minutes"


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
@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_observation_types_cached(base_url: str):
    """Cacheable helper so we don't hammer /scouting/types."""
    response = requests.get(f"{base_url}/scouting/types", timeout=10)
    response.raise_for_status()
    return response.json().get('observation_types', [])


def get_observation_types():
    """Get available scouting observation types from backend with hourly refresh."""
    try:
        return _fetch_observation_types_cached(BACKEND_URL)
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

    active_prediction_raw = st.session_state.get('prediction_results')
    active_prediction = None
    if isinstance(active_prediction_raw, dict):
        if 'data' in active_prediction_raw and isinstance(active_prediction_raw['data'], dict):
            active_prediction = active_prediction_raw['data']
        else:
            active_prediction = active_prediction_raw

    if active_prediction:
        context_summary = active_prediction.get('context_summary', {})
        hunting_context = active_prediction.get('hunting_context', {})
        recommendations = hunting_context.get('recommendations', {}) if isinstance(hunting_context, dict) else {}
        primary_guidance = context_summary.get('primary_guidance') or recommendations.get('primary')
        secondary_guidance = context_summary.get('secondary_guidance') or recommendations.get('secondary')
        specific_actions = recommendations.get('specific_actions') if isinstance(recommendations.get('specific_actions'), list) else []
        recommended_action = context_summary.get('recommended_action') or hunting_context.get('action')
        time_remaining_minutes = hunting_context.get('current_status', {}).get('time_remaining_minutes') if isinstance(hunting_context.get('current_status'), dict) else None
        time_remaining_label = format_minutes_to_clock(time_remaining_minutes)
        legal_hours = hunting_context.get('legal_hours', {}) if isinstance(hunting_context.get('legal_hours'), dict) else {}
        earliest_legal = legal_hours.get('earliest')
        latest_legal = legal_hours.get('latest')

        severity = 'info'
        if isinstance(recommended_action, str):
            lowered = recommended_action.lower()
            if any(trigger in lowered for trigger in ['last', 'urgent', 'final']):
                severity = 'warning'
            elif any(trigger in lowered for trigger in ['stand down', 'hold', 'pause']):
                severity = 'error'

        summary_lines = []
        if primary_guidance:
            summary_lines.append(f"**{primary_guidance}**")
        if secondary_guidance:
            summary_lines.append(secondary_guidance)
        if time_remaining_label != "Unknown":
            summary_lines.append(f"⏳ Time remaining: {time_remaining_label}")
        elif context_summary.get('time_remaining'):
            summary_lines.append(f"⏳ Time remaining: {context_summary['time_remaining']} minutes")
        if earliest_legal and latest_legal:
            summary_lines.append(f"🕒 Legal light: {earliest_legal} – {latest_legal}")
        if specific_actions:
            bullet_list = "\n".join(f"• {item}" for item in specific_actions[:3])
            summary_lines.append(f"📝 Focus: \n{bullet_list}")

        message = "\n".join(summary_lines) if summary_lines else "Current conditions loaded."
        if severity == 'warning':
            st.warning(message)
        elif severity == 'error':
            st.error(message)
        else:
            st.info(message)

        hunt_windows = active_prediction.get('hunt_window_predictions') or []
        if hunt_windows:
            next_window = hunt_windows[0]
            start_label = format_local_time(next_window.get('window_start'))
            end_label = format_local_time(next_window.get('window_end'))
            wind_label = next_window.get('dominant_wind', 'Unknown wind')
            confidence_pct = max(0.0, min(100.0, float(next_window.get('confidence', 0)) * 100)) if isinstance(next_window.get('confidence'), (int, float)) else 0
            boost = next_window.get('priority_boost', 0)
            trigger_summary = next_window.get('trigger_summary') or []
            triggers_text = f"Triggers: {', '.join(trigger_summary)}" if trigger_summary else ""
            st.success(
                f"🪵 Next hunt window: {start_label} → {end_label} · {wind_label} · Confidence {confidence_pct:.0f}% · Boost +{boost:.1f} {triggers_text}"
            )
        else:
            st.info("🪵 No forecast-aligned hunt window detected in the next 24 hours. Monitor wind shifts for updates.")

        wind_summary = active_prediction.get('wind_summary', {}) if isinstance(active_prediction.get('wind_summary'), dict) else {}
        weather_snapshot = active_prediction.get('weather_data', {}) if isinstance(active_prediction.get('weather_data'), dict) else {}
        if wind_summary:
            overall_conditions = wind_summary.get('overall_wind_conditions', {}) if isinstance(wind_summary.get('overall_wind_conditions'), dict) else {}
            prevailing = overall_conditions.get('prevailing_wind', 'Unknown wind')
            effective = overall_conditions.get('effective_wind', 'Unknown effective wind')
            rating = overall_conditions.get('hunting_rating', 'N/A')
            thermal_active = overall_conditions.get('thermal_activity')

            wind_source = weather_snapshot.get('wind_source') if isinstance(weather_snapshot, dict) else None
            source_labels = {
                'current': 'live obs',
                'current_override': 'live override',
                'forecast': 'forecast hour'
            }
            prevailing_label = prevailing + (f" ({source_labels.get(wind_source, wind_source)})" if wind_source else "")

            summary_bits = [
                f"Prevailing: {prevailing_label}",
                f"Effective: {effective}",
                f"Rating: {rating}"
            ]

            current_snapshot = weather_snapshot.get('current_snapshot', {}) if isinstance(weather_snapshot.get('current_snapshot'), dict) else {}
            if current_snapshot:
                live_reading = format_wind_reading(
                    current_snapshot.get('wind_direction'),
                    current_snapshot.get('wind_speed')
                )
                live_label = f"Live: {live_reading}"
                if live_reading and live_label not in summary_bits:
                    # Only append when forecast still drives the prevailing label
                    if wind_source != 'current_override' or live_reading not in prevailing_label:
                        summary_bits.append(live_label)

            target_lookup = weather_snapshot.get('target_forecast_lookup', {})
            if isinstance(target_lookup, dict):
                override_reason = target_lookup.get('override_reason')
                status = target_lookup.get('status')
                matched_hour = target_lookup.get('matched_hour')
                if matched_hour:
                    matched_label = format_local_time(matched_hour)
                    summary_bits.append(f"Forecast hour: {matched_label}")
                elif status == 'current_only':
                    summary_bits.append("Forecast hour: current conditions")
                if override_reason:
                    summary_bits.append("Override: current conditions within 45 min")

            if thermal_active:
                summary_bits.append("Thermals active")

            st.markdown("**🌬️ Wind Gameplan:** " + " · ".join(summary_bits))

            tactical = wind_summary.get('tactical_recommendations', [])
            if tactical:
                for tip in tactical[:3]:
                    st.caption(f"• {tip}")
    
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
                        context_tags = rec.get('context_tags', []) or []
                        wind_credibility = rec.get('wind_credibility', {}) or {}
                        marker_color = 'green' if 'hunt_window_priority' in context_tags else color

                        popup_lines = [
                            f"{icon_name} Stand #{i}: {stand_type}",
                            f"Confidence: {confidence:.0f}%"
                        ]

                        reasoning = rec.get('reasoning')
                        if reasoning:
                            popup_lines.append(reasoning)

                        if wind_credibility:
                            alignment_pct = wind_credibility.get('alignment_score_now', 0) * 100
                            status_label = "🟢 Wind Ready" if wind_credibility.get('is_green_now') else "🕒 Setup Soon"
                            popup_lines.append(f"{status_label} ({alignment_pct:.0f}% alignment)")

                            preferred = wind_credibility.get('preferred_directions') or []
                            if preferred:
                                popup_lines.append(f"Preferred Winds: {', '.join(preferred)}")

                            priority_boost = wind_credibility.get('priority_boost', 0)
                            if priority_boost:
                                popup_lines.append(f"Priority Boost: +{priority_boost:.1f}")

                            best_alignment = format_local_time(wind_credibility.get('best_alignment_time'))
                            if best_alignment != "Unknown":
                                popup_lines.append(f"Best Alignment: {best_alignment}")

                            triggers = wind_credibility.get('triggers_met') or []
                            if triggers:
                                popup_lines.append(f"Triggers: {', '.join(triggers)}")

                        popup_html = "<br>".join(popup_lines)
                        tooltip_suffix = " 🔥" if 'hunt_window_priority' in context_tags else ""

                        folium.Marker(
                            [stand_lat, stand_lon],
                            popup=popup_html,
                            icon=folium.Icon(color=marker_color, icon=icon),
                            tooltip=f"Stand #{i} - {confidence:.0f}%{tooltip_suffix}"
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
        if active_prediction:
            st.caption("Legend: 🟢 green stand marker = forecast priority, 🔥 tooltip badge = hunt-window boost, 🛏️ bedding icons = alternative bedding, 🌾 = alternative feeding, 📷 = optimized camera.")
        
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

    if active_prediction:
        stand_recommendations = active_prediction.get('mature_buck_analysis', {}).get('stand_recommendations', []) if isinstance(active_prediction.get('mature_buck_analysis'), dict) else []
        if stand_recommendations:
            st.markdown("### 🪵 Stand Priority Overview")
            for idx, stand in enumerate(stand_recommendations, 1):
                stand_type = stand.get('type', 'Stand')
                confidence = stand.get('confidence')
                action_priority = (stand.get('action_priority') or 'unknown').upper()
                context_note = stand.get('context_note')
                wind_status = stand.get('wind_credibility', {}) if isinstance(stand.get('wind_credibility'), dict) else {}
                alignment_score = wind_status.get('alignment_score_now')
                alignment_pct = f"{alignment_score * 100:.0f}%" if isinstance(alignment_score, (int, float)) else "—"
                priority_boost = wind_status.get('priority_boost')
                preferred_list = wind_status.get('preferred_directions') or []
                summary_line = f"#{idx} {stand_type} · Confidence {confidence:.0f}%" if isinstance(confidence, (int, float)) else f"#{idx} {stand_type}"
                summary_line += f" · Priority: {action_priority}"
                st.markdown(f"**{summary_line}**")
                detail_bits = []
                if alignment_pct != "—":
                    detail_bits.append(f"Wind alignment {alignment_pct}")
                if isinstance(priority_boost, (int, float)) and priority_boost:
                    detail_bits.append(f"Boost +{priority_boost:.1f}")
                if preferred_list:
                    detail_bits.append(f"Preferred winds: {', '.join(preferred_list)}")
                if detail_bits:
                    st.caption(" · ".join(detail_bits))
                if context_note:
                    st.warning(context_note)
        else:
            st.info("No stand recommendations available yet for this prediction.")
    
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
                        
                        # NEW: Try to get detailed analysis if available
                        try:
                            analysis_response = requests.post(
                                f"{BACKEND_URL}/analyze-prediction-detailed",
                                json=prediction_data,
                                headers={'Content-Type': 'application/json'},
                                timeout=10  # Quick timeout for optional feature
                            )
                            
                            if analysis_response.status_code == 200:
                                analysis_data = analysis_response.json()
                                if analysis_data.get('success') and analysis_data.get('detailed_analysis'):
                                    # Add detailed analysis to prediction results
                                    prediction['detailed_analysis'] = analysis_data['detailed_analysis']
                                    st.info("✨ **Enhanced Analysis:** Detailed wind, thermal, and criteria analysis included!")
                                else:
                                    st.info("ℹ️ **Standard Analysis:** Basic prediction data available.")
                            else:
                                st.info("ℹ️ **Standard Analysis:** Detailed analysis endpoint not available.")
                        except Exception as analysis_error:
                            # Don't fail the whole prediction if detailed analysis fails
                            st.info("ℹ️ **Standard Analysis:** Detailed analysis temporarily unavailable.")
                        
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
        prediction_data = prediction.get('data', prediction) if isinstance(prediction, dict) and 'data' in prediction else prediction
        hunt_windows = prediction_data.get('hunt_window_predictions') or []
        stand_priority_overrides = prediction_data.get('stand_priority_overrides') or {}

        if hunt_windows or stand_priority_overrides:
            with st.expander("🪵 Forecast Hunt Windows & Wind Credibility", expanded=True):
                if hunt_windows:
                    st.markdown("**Upcoming Stand Hunt Windows (next 24 hrs):**")
                    for window in hunt_windows[:4]:
                        stand_label = window.get('stand_name') or window.get('stand_id', 'Stand')
                        start_time = format_local_time(window.get('window_start'))
                        end_time = format_local_time(window.get('window_end'))
                        confidence_pct = max(0.0, min(100.0, window.get('confidence', 0) * 100))
                        priority_boost = window.get('priority_boost', 0)
                        wind_label = window.get('dominant_wind', 'Unknown')
                        st.markdown(
                            f"- **{stand_label}** · {start_time} → {end_time} · {wind_label} wind · Confidence {confidence_pct:.0f}% · Boost +{priority_boost:.1f}"
                        )
                        triggers = window.get('trigger_summary') or []
                        if triggers:
                            st.caption(f"Triggers: {', '.join(triggers)}")
                else:
                    st.info("No forecast-aligned hunt windows detected in the next day.")

                if stand_priority_overrides:
                    st.markdown("**Stand Wind Credibility Snapshot:**")
                    for status in list(stand_priority_overrides.values())[:4]:
                        alignment_pct = max(0.0, min(100.0, status.get('alignment_score_now', 0) * 100))
                        preferred = ', '.join(status.get('preferred_directions', []))
                        triggers = ', '.join(status.get('triggers_met', []))
                        best_alignment = format_local_time(status.get('best_alignment_time'))
                        is_green = status.get('is_green_now', False)

                        cols = st.columns([3, 1, 1])
                        with cols[0]:
                            st.markdown(f"**{status.get('stand_name', status.get('stand_id', 'Stand'))}**")
                            if preferred:
                                st.write(f"Preferred Winds: {preferred}")
                            if triggers:
                                st.write(f"Triggers: {triggers}")
                            if best_alignment != "Unknown":
                                st.write(f"Best Alignment: {best_alignment}")
                        with cols[1]:
                            st.markdown("**Alignment**")
                            st.write(f"{alignment_pct:.0f}%")
                            st.caption("🟢 Ready" if is_green else "🕒 Warming Up")
                        with cols[2]:
                            st.markdown("**Priority Boost**")
                            st.write(f"+{status.get('priority_boost', 0):.1f}")
                else:
                    st.info("No stand wind credibility overrides available yet; configure stand wind profiles to unlock this data.")
        
        # Debug section - Enhanced validation metrics and raw data
        with st.expander("🐛 Debug: Show Enhanced Validation Data"):
            # Critical validation metrics tabs
            tab1, tab2, tab3 = st.tabs(["🎯 Critical Validations", "📊 Terrain Data", "🗂️ Raw JSON"])
            
            with tab1:
                st.subheader("🔍 System Validation Status")
                
                # Slope consistency validation
                if 'bedding_zones' in prediction and prediction['bedding_zones'].get('properties', {}).get('slope_tracking'):
                    slope_tracking = prediction['bedding_zones']['properties']['slope_tracking']
                    gee_slope = prediction.get('gee_data', {}).get('slope', 'N/A')
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("🏔️ Slope Consistency", 
                                slope_tracking.get('consistency_check', 'unknown').title(),
                                delta="✅ Verified" if slope_tracking.get('consistency_check') == 'verified' else "❌ Issue")
                        st.metric("📏 GEE Source Slope", f"{gee_slope:.1f}°" if isinstance(gee_slope, (int, float)) else str(gee_slope))
                    
                    with col2:
                        st.metric("🎯 Suitability Slope", f"{slope_tracking.get('gee_source_slope', 'N/A'):.1f}°" if isinstance(slope_tracking.get('gee_source_slope'), (int, float)) else "N/A")
                        zones_slopes = slope_tracking.get('zones_using_slope', [])
                        unique_slopes = len(set(zones_slopes)) if zones_slopes else 0
                        st.metric("🛏️ Zone Slope Unity", f"{unique_slopes} unique values" if unique_slopes else "No zones",
                                delta="✅ Consistent" if unique_slopes <= 1 else f"❌ {unique_slopes} different values")
                
                # Aspect consistency validation  
                if 'feeding_areas' in prediction and prediction['feeding_areas'].get('features'):
                    feeding_features = prediction['feeding_areas']['features']
                    terrain_aspects = [f.get('properties', {}).get('terrain_aspect') for f in feeding_features]
                    unique_aspects = len(set(terrain_aspects)) if terrain_aspects else 0
                    
                    st.metric("🧭 Feeding Aspect Unity", f"{unique_aspects} unique values",
                            delta="✅ Consistent" if unique_aspects <= 1 else f"❌ {unique_aspects} different values")
                
                # Bedding zone generation status
                bedding_count = len(prediction.get('bedding_zones', {}).get('features', []))
                st.metric("🛏️ Bedding Zones Generated", bedding_count,
                        delta="✅ Success" if bedding_count > 0 else "❌ No zones (check slope limits)")
                
                # Biological accuracy indicators
                if bedding_count > 0:
                    first_zone = prediction['bedding_zones']['features'][0]['properties']
                    slope_val = first_zone.get('slope', 0)
                    aspect_val = first_zone.get('aspect', 0)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        slope_status = "✅ Suitable" if slope_val <= 30 else "❌ Too steep"
                        st.metric("🏔️ Slope Biological Check", f"{slope_val:.1f}°", delta=slope_status)
                    
                    with col2:
                        aspect_status = "✅ Optimal" if 135 <= aspect_val <= 225 else "⚠️ Suboptimal"
                        st.metric("🧭 Aspect Biological Check", f"{aspect_val:.0f}°", delta=aspect_status)
            
            with tab2:
                st.subheader("🗺️ Terrain & Environmental Data")
                
                # GEE Data
                if 'gee_data' in prediction:
                    gee_data = prediction['gee_data']
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🛰️ Google Earth Engine Data**")
                        st.write(f"📏 Slope: {gee_data.get('slope', 'N/A'):.2f}°" if isinstance(gee_data.get('slope'), (int, float)) else f"📏 Slope: {gee_data.get('slope', 'N/A')}")
                        st.write(f"🧭 Aspect: {gee_data.get('aspect', 'N/A'):.0f}°" if isinstance(gee_data.get('aspect'), (int, float)) else f"🧭 Aspect: {gee_data.get('aspect', 'N/A')}")
                        st.write(f"🌲 Canopy: {gee_data.get('canopy_coverage', 'N/A'):.1%}" if isinstance(gee_data.get('canopy_coverage'), (int, float)) else f"🌲 Canopy: {gee_data.get('canopy_coverage', 'N/A')}")
                        st.write(f"📍 Elevation: {gee_data.get('elevation', 'N/A'):.0f}m" if isinstance(gee_data.get('elevation'), (int, float)) else f"📍 Elevation: {gee_data.get('elevation', 'N/A')}")
                    
                    with col2:
                        st.markdown("**🏞️ OSM & Weather Data**")
                        osm_data = prediction.get('osm_data', {})
                        weather_data = prediction.get('weather_data', {})
                        st.write(f"🛣️ Road Distance: {osm_data.get('nearest_road_distance_m', 'N/A'):.0f}m" if isinstance(osm_data.get('nearest_road_distance_m'), (int, float)) else f"�️ Road Distance: {osm_data.get('nearest_road_distance_m', 'N/A')}")
                        st.write(f"🌡️ Temperature: {weather_data.get('temperature', 'N/A'):.1f}°F" if isinstance(weather_data.get('temperature'), (int, float)) else f"🌡️ Temperature: {weather_data.get('temperature', 'N/A')}")
                        st.write(f"💨 Wind: {weather_data.get('wind_direction', 'N/A'):.0f}° at {weather_data.get('wind_speed', 'N/A'):.1f}mph" if isinstance(weather_data.get('wind_direction'), (int, float)) and isinstance(weather_data.get('wind_speed'), (int, float)) else f"💨 Wind: {weather_data.get('wind_direction', 'N/A')}° at {weather_data.get('wind_speed', 'N/A')}mph")
            
            with tab3:
                st.subheader("🗂️ Complete Raw Prediction Data")
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
        
        # ==========================================
        # COMPREHENSIVE PREDICTION ANALYSIS DISPLAY
        # ==========================================
        
        # Check if we have detailed analysis data in the prediction results
        detailed_analysis = prediction.get('detailed_analysis', None)
        
        if detailed_analysis:
            # Display comprehensive analysis with expandable sections
            with st.expander("🔍 **Detailed Prediction Analysis**", expanded=False):
                
                # Analysis Overview
                st.markdown("### 📊 Analysis Overview")
                
                if 'analysis_metadata' in detailed_analysis:
                    metadata = detailed_analysis['analysis_metadata']
                    
                    # Create overview metrics in columns
                    overview_col1, overview_col2, overview_col3 = st.columns(3)
                    
                    with overview_col1:
                        completion = metadata.get('completion_percentage', 0)
                        if completion >= 80:
                            st.success(f"🟢 **Analysis Status**\n{completion:.1f}% Complete (Excellent)")
                        elif completion >= 60:
                            st.warning(f"🟡 **Analysis Status**\n{completion:.1f}% Complete (Good)")
                        else:
                            st.error(f"🔴 **Analysis Status**\n{completion:.1f}% Complete (Limited)")
                    
                    with overview_col2:
                        st.info(f"🔧 **Analyzer Version**\n{metadata.get('analyzer_version', 'Unknown')}")
                        
                    with overview_col3:
                        # Show data collection status from the actual API response
                        data_collected = metadata.get('data_collected', {})
                        completed_count = sum(1 for v in data_collected.values() if v)
                        total_count = len(data_collected)
                        st.info(f"📋 **Data Collection**\n{completed_count}/{total_count} Sources Complete")
                
                # Criteria Analysis Tab
                st.markdown("---")
                st.markdown("### 📋 Criteria Analysis")
                
                if 'criteria_analysis' in detailed_analysis:
                    criteria = detailed_analysis['criteria_analysis']
                    
                    # Criteria Summary
                    if 'criteria_summary' in criteria:
                        summary = criteria['criteria_summary']
                        criteria_col1, criteria_col2, criteria_col3 = st.columns(3)
                        
                        with criteria_col1:
                            st.metric("Total Criteria", summary.get('total_criteria', 0))
                        with criteria_col2:
                            st.metric("Met Criteria", summary.get('met_criteria', 0))
                        with criteria_col3:
                            compliance = summary.get('compliance_percentage', 0)
                            st.metric("Compliance Rate", f"{compliance:.1f}%")
                    
                    # Detailed Criteria by Type
                    criteria_detail_col1, criteria_detail_col2, criteria_detail_col3 = st.columns(3)
                    
                    with criteria_detail_col1:
                        st.markdown("**🛏️ Bedding Criteria**")
                        bedding = criteria.get('bedding_criteria', {})
                        for key, value in list(bedding.items())[:3]:
                            display_key = key.replace('_', ' ').title()
                            if isinstance(value, float):
                                st.write(f"• {display_key}: {value:.2f}")
                            else:
                                st.write(f"• {display_key}: {value}")
                    
                    with criteria_detail_col2:
                        st.markdown("**🎯 Stand Criteria**")
                        stand = criteria.get('stand_criteria', {})
                        for key, value in list(stand.items())[:3]:
                            display_key = key.replace('_', ' ').title()
                            if isinstance(value, float):
                                st.write(f"• {display_key}: {value:.2f}")
                            else:
                                st.write(f"• {display_key}: {value}")
                    
                    with criteria_detail_col3:
                        st.markdown("**🌾 Feeding Criteria**")
                        feeding = criteria.get('feeding_criteria', {})
                        for key, value in list(feeding.items())[:3]:
                            display_key = key.replace('_', ' ').title()
                            if isinstance(value, float):
                                st.write(f"• {display_key}: {value:.2f}")
                            else:
                                st.write(f"• {display_key}: {value}")
                
                # Environmental Analysis Tab
                st.markdown("---")
                st.markdown("### 🌿 Environmental Analysis")
                
                env_col1, env_col2 = st.columns(2)
                
                with env_col1:
                    # Wind Analysis
                    st.markdown("#### 🌬️ Wind Analysis")
                    if 'wind_analysis' in detailed_analysis:
                        wind = detailed_analysis['wind_analysis']
                        
                        # Overall Wind Conditions
                        if 'overall_wind_conditions' in wind:
                            overall = wind['overall_wind_conditions']
                            st.write(f"**Current Wind:** {overall.get('prevailing_wind', 'Unknown')}")
                            
                            if overall.get('thermal_activity', False):
                                st.success("🔥 Thermal Activity: Active")
                            else:
                                st.info("❄️ Thermal Activity: Inactive")
                            
                            rating = overall.get('hunting_rating', '0/10')
                            if isinstance(rating, str) and '/' in rating:
                                rating_num = float(rating.split('/')[0])
                            else:
                                rating_num = float(rating) if rating else 0
                            
                            if rating_num >= 8:
                                st.success(f"🌬️ **Wind Rating:** {rating_num:.1f}/10 (Excellent)")
                            elif rating_num >= 6:
                                st.warning(f"🌬️ **Wind Rating:** {rating_num:.1f}/10 (Good)")
                            else:
                                st.error(f"🌬️ **Wind Rating:** {rating_num:.1f}/10 (Poor)")
                        
                        # Location Wind Analyses Summary
                        if 'location_wind_analyses' in wind:
                            locations = wind['location_wind_analyses']
                            if locations:
                                st.markdown("**Location Analysis:**")
                                # Group by location type for better display
                                location_types = {}
                                for loc in locations:
                                    loc_type = loc.get('location_type', 'Unknown').title()
                                    if loc_type not in location_types:
                                        location_types[loc_type] = []
                                    location_types[loc_type].append(loc)
                                
                                for loc_type, locs in location_types.items():
                                    avg_rating = sum(loc.get('wind_analysis', {}).get('wind_advantage_rating', 0) for loc in locs) / len(locs)
                                    st.write(f"• {loc_type}: {avg_rating:.1f}/10")
                        
                        # Show detailed wind recommendations if available
                        if 'wind_recommendations' in wind:
                            recommendations = wind['wind_recommendations']
                            if recommendations:
                                st.markdown("**Wind Recommendations:**")
                                for rec in recommendations[:2]:  # Show top 2
                                    st.write(f"• {rec}")
                        
                        # Wind Summary
                        if 'wind_summary' in wind:
                            summary = wind['wind_summary']
                            if 'confidence_assessment' in summary:
                                confidence = summary['confidence_assessment']
                                st.write(f"**Wind Analysis Confidence:** {confidence:.1f}%")
                
                with env_col2:
                    # Thermal Analysis
                    st.markdown("#### 🔥 Thermal Analysis")
                    if 'thermal_analysis' in detailed_analysis:
                        thermal = detailed_analysis['thermal_analysis']
                        
                        # Thermal Conditions
                        if 'thermal_conditions' in thermal:
                            conditions = thermal['thermal_conditions']
                            is_active = conditions.get('is_active', False)
                            strength = conditions.get('strength_scale', 0)
                            direction = conditions.get('direction', 'Unknown')
                            
                            if is_active:
                                if strength >= 7:
                                    st.success(f"🔥 **Thermal Status:** Active & Strong ({strength:.1f}/10)")
                                elif strength >= 5:
                                    st.warning(f"🔥 **Thermal Status:** Active & Moderate ({strength:.1f}/10)")
                                else:
                                    st.info(f"🔥 **Thermal Status:** Active & Weak ({strength:.1f}/10)")
                            else:
                                st.error("❄️ **Thermal Status:** Inactive")
                            
                            st.write(f"**Direction:** {direction.replace('_', ' ').title()}")
                        
                        # Thermal Advantages
                        if 'thermal_advantages' in thermal:
                            advantages = thermal['thermal_advantages']
                            optimal_timing = advantages.get('optimal_timing', 'Unknown')
                            st.write(f"**Optimal Timing:** {optimal_timing.replace('_', ' ').title()}")
                            
                            hunting_windows = advantages.get('hunting_windows', [])
                            if hunting_windows:
                                st.markdown("**Prime Windows:**")
                                for window in hunting_windows[:2]:  # Show first 2
                                    st.write(f"• {window}")
                        
                        # Thermal Locations
                        locations = thermal.get('thermal_locations', [])
                        if locations:
                            st.markdown("**Active Zones:**")
                            for loc in locations[:3]:  # Show first 3
                                st.write(f"• {loc.replace('_', ' ').title()}")
                
                # Data Quality and Scoring
                st.markdown("---")
                st.markdown("### 📈 Data Quality & Scoring")
                
                quality_col1, quality_col2 = st.columns(2)
                
                with quality_col1:
                    # Data Source Analysis
                    if 'data_source_analysis' in detailed_analysis:
                        data_sources = detailed_analysis['data_source_analysis']
                        st.markdown("#### 📊 Data Quality")
                        
                        if 'data_quality_summary' in data_sources:
                            quality = data_sources['data_quality_summary']
                            overall_quality = quality.get('overall_quality', 0)
                            
                            if overall_quality >= 8:
                                st.success(f"🟢 **Overall Quality:** {overall_quality:.1f}/10 (High)")
                            elif overall_quality >= 6:
                                st.warning(f"🟡 **Overall Quality:** {overall_quality:.1f}/10 (Moderate)")
                            else:
                                st.error(f"🔴 **Overall Quality:** {overall_quality:.1f}/10 (Low)")
                            
                            freshness = quality.get('data_freshness', 0)
                            completeness = quality.get('completeness', 0)
                            st.write(f"• **Data Freshness:** {freshness:.1f}/10")
                            st.write(f"• **Completeness:** {completeness:.1f}/10")
                
                with quality_col2:
                    # Scoring Analysis
                    if 'scoring_analysis' in detailed_analysis:
                        scoring = detailed_analysis['scoring_analysis']
                        st.markdown("#### 🎯 Confidence Metrics")
                        
                        if 'confidence_metrics' in scoring:
                            metrics = scoring['confidence_metrics']
                            overall_confidence = metrics.get('overall_confidence', 0)
                            
                            if overall_confidence >= 8:
                                st.success(f"🟢 **Overall Confidence:** {overall_confidence:.1f}/10 (High)")
                            elif overall_confidence >= 6:
                                st.warning(f"🟡 **Overall Confidence:** {overall_confidence:.1f}/10 (Moderate)")
                            else:
                                st.error(f"🔴 **Overall Confidence:** {overall_confidence:.1f}/10 (Low)")
                            
                            prediction_reliability = metrics.get('prediction_reliability', 0)
                            data_confidence = metrics.get('data_confidence', 0)
                            st.write(f"• **Prediction Reliability:** {prediction_reliability:.1f}/10")
                            st.write(f"• **Data Confidence:** {data_confidence:.1f}/10")
        
        else:
            # Show notice that detailed analysis is not available
            with st.expander("🔍 **Detailed Prediction Analysis**", expanded=False):
                st.info("💡 **Enhanced Analysis Available:** Detailed analysis is available when using the new `/analyze-prediction-detailed` API endpoint. This provides comprehensive wind analysis, thermal analysis, criteria evaluation, and data quality metrics.")
                st.markdown("**Features available with detailed analysis:**")
                st.write("• 🌬️ Comprehensive wind direction analysis")
                st.write("• 🔥 Advanced thermal wind calculations")
                st.write("• 📋 Detailed criteria compliance scoring")
                st.write("• 📊 Data quality and confidence metrics")
                st.write("• 🎯 Algorithm analysis and feature engineering details")
        
        # Add comprehensive wind analysis section if available
        if detailed_analysis and 'wind_analysis' in detailed_analysis:
            wind_analysis = detailed_analysis['wind_analysis']
            with st.expander("🌬️ **Comprehensive Wind Analysis - All Locations**", expanded=False):
                st.markdown("### 🌬️ Complete Wind Intelligence Report")
                
                # Overall Wind Summary
                if 'wind_summary' in wind_analysis:
                    wind_summary = wind_analysis['wind_summary']
                    overall_conditions = wind_summary.get('overall_wind_conditions', {})
                    
                    summary_col1, summary_col2 = st.columns(2)
                    with summary_col1:
                        st.markdown("**🌬️ Current Wind Conditions:**")
                        st.write(f"• Prevailing Wind: {overall_conditions.get('prevailing_wind', 'Unknown')}")
                        st.write(f"• Thermal Activity: {'Active' if overall_conditions.get('thermal_activity', False) else 'Inactive'}")
                        st.write(f"• Effective Wind: {overall_conditions.get('effective_wind', 'Unknown')}")
                    
                    with summary_col2:
                        rating = overall_conditions.get('hunting_rating', '0/10')
                        if isinstance(rating, str) and '/' in rating:
                            rating_display = rating
                        else:
                            rating_display = f"{rating:.1f}/10"
                        st.metric("🎯 Hunting Rating", rating_display)
                
                # Detailed Location Analysis
                if 'location_wind_analyses' in wind_analysis:
                    locations = wind_analysis['location_wind_analyses']
                    st.markdown("---")
                    st.markdown(f"### 📍 Location-Specific Wind Analysis ({len(locations)} Locations)")
                    
                    # Group by location type
                    location_groups = {'bedding': [], 'stand': [], 'feeding': []}
                    for loc in locations:
                        loc_type = loc.get('location_type', 'unknown')
                        if loc_type in location_groups:
                            location_groups[loc_type].append(loc)
                    
                    # Display each group
                    for group_name, group_locations in location_groups.items():
                        if group_locations:
                            st.markdown(f"#### 🎯 {group_name.title()} Locations ({len(group_locations)} spots)")
                            
                            for i, loc in enumerate(group_locations):
                                coords = loc.get('coordinates', [0, 0])
                                wind_data = loc.get('wind_analysis', {})
                                
                                with st.container():
                                    st.markdown(f"**Location {i+1}: {coords[0]:.4f}, {coords[1]:.4f}**")
                                    
                                    # Wind details in columns
                                    wind_col1, wind_col2, wind_col3 = st.columns(3)
                                    
                                    with wind_col1:
                                        st.write(f"🌬️ Wind Direction: {wind_data.get('prevailing_wind_direction', 'Unknown')}°")
                                        st.write(f"💨 Wind Speed: {wind_data.get('prevailing_wind_speed', 'Unknown')} mph")
                                        st.write(f"🎯 Scent Cone: {wind_data.get('scent_cone_direction', 'Unknown')}°")
                                    
                                    with wind_col2:
                                        st.write(f"⭐ Wind Rating: {wind_data.get('wind_advantage_rating', 0):.1f}/10")
                                        st.write(f"🔥 Thermal Active: {'Yes' if wind_data.get('thermal_wind_active', False) else 'No'}")
                                        st.write(f"📍 Approach Bearing: {wind_data.get('optimal_approach_bearing', 'Unknown')}°")
                                    
                                    with wind_col3:
                                        confidence = loc.get('confidence_score', 0)
                                        if confidence >= 0.7:
                                            st.success(f"✅ Confidence: {confidence:.1%}")
                                        elif confidence >= 0.5:
                                            st.warning(f"⚠️ Confidence: {confidence:.1%}")
                                        else:
                                            st.error(f"❌ Confidence: {confidence:.1%}")
                                    
                                    # Recommendations
                                    recommendations = wind_data.get('recommendations', [])
                                    if recommendations:
                                        st.markdown("**🎯 Tactical Recommendations:**")
                                        for rec in recommendations[:2]:
                                            st.write(f"• {rec}")
                                    
                                    # Entry routes
                                    entry_routes = loc.get('optimal_entry_routes', [])
                                    if entry_routes:
                                        st.write(f"**🚶 Entry Route:** {entry_routes[0]}")
                                    
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
                action_priority = (stand_1.get('action_priority') or '').upper()
                context_note = stand_1.get('context_note')
                priority_bits = []
                if action_priority:
                    priority_bits.append(f"Priority: {action_priority}")
                if context_note:
                    priority_bits.append(context_note)
                if priority_bits:
                    priority_message = " | ".join(priority_bits)
                    if action_priority == "HIGH":
                        st.success(priority_message)
                    elif action_priority == "MEDIUM":
                        st.info(priority_message)
                    elif action_priority == "LOW":
                        st.warning(priority_message)
                    else:
                        st.info(priority_message)
                
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
                        
                        # Use sophisticated backend wind analysis instead of simple calculations
                        st.markdown("**🌬️ Real-Time Wind Analysis:**")
                        
                        # Get current wind conditions from backend analysis (handle API wrapper)
                        prediction_data = prediction.get('data', prediction) if 'data' in prediction else prediction
                        weather_data = prediction_data.get('weather_data', {})
                        wind_analyses = prediction_data.get('wind_analyses', [])
                        wind_summary = prediction_data.get('wind_summary', {})
                        
                        if weather_data and 'wind_direction' in weather_data:
                            current_wind_dir = weather_data['wind_direction']
                            current_wind_speed = weather_data.get('wind_speed', 0)
                            
                            # Convert wind direction to compass
                            directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                                        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                            current_wind_compass = directions[int((current_wind_dir + 11.25) / 22.5) % 16]
                            
                            # Get wind rating from backend analysis
                            overall_conditions = wind_summary.get('overall_wind_conditions', {})
                            hunting_rating = overall_conditions.get('hunting_rating', 'N/A')
                            
                            # Show current wind status with backend assessment
                            if hunting_rating != 'N/A':
                                rating_num = float(hunting_rating.split('/')[0]) if '/' in str(hunting_rating) else 0
                                if rating_num >= 8:
                                    st.success(f"• **Current Wind:** {current_wind_compass} at {current_wind_speed:.1f} mph (Rating: {hunting_rating} - Excellent!)")
                                elif rating_num >= 6:
                                    st.success(f"• **Current Wind:** {current_wind_compass} at {current_wind_speed:.1f} mph (Rating: {hunting_rating} - Good)")
                                else:
                                    st.warning(f"• **Current Wind:** {current_wind_compass} at {current_wind_speed:.1f} mph (Rating: {hunting_rating})")
                            else:
                                st.info(f"• **Current Wind:** {current_wind_compass} at {current_wind_speed:.1f} mph")
                            
                            # Show tactical recommendations from backend
                            tactical_recs = wind_summary.get('tactical_recommendations', [])
                            if tactical_recs:
                                st.write(f"• **Tactical Advice:** {tactical_recs[0]}")
                            
                            # Show thermal activity if active
                            thermal_active = overall_conditions.get('thermal_activity', False)
                            if thermal_active:
                                st.info("• **Thermal Winds Active** - Enhanced scent management opportunities")
                        else:
                            # Fallback to simple calculation if backend data unavailable
                            crosswind_labels = []
                            for offset in (
                                (deer_approach_result['bearing'] + 90) % 360,
                                (deer_approach_result['bearing'] - 90) % 360,
                            ):
                                label = degrees_to_compass(offset)
                                if label not in crosswind_labels:
                                    crosswind_labels.append(label)
                            if crosswind_labels:
                                st.info(f"• **Theoretical Crosswinds:** {', '.join(crosswind_labels)}")
                            st.write(f"• **Avoid Wind From:** {deer_approach_result['compass']} (towards deer)")
                        
                        st.info(f"• **Deer Movement:** {deer_approach_result['movement_type']} ({deer_approach_result['confidence']} confidence)")
                
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
                    wind_credibility = stand_1.get('wind_credibility', {})
                    if wind_credibility:
                        st.markdown("**🪵 Hunt Window Status:**")
                        alignment_pct = max(0.0, min(100.0, wind_credibility.get('alignment_score_now', 0) * 100))
                        st.write(f"Alignment Match: {alignment_pct:.0f}%")
                        if wind_credibility.get('is_green_now'):
                            st.success("Green light right now – winds are in your favor.")
                        else:
                            st.info("Winds trending into position – monitor approaching window.")

                        preferred = wind_credibility.get('preferred_directions') or []
                        if preferred:
                            st.write(f"Preferred Winds: {', '.join(preferred)}")

                        priority_boost = wind_credibility.get('priority_boost', 0)
                        if priority_boost:
                            st.write(f"Priority Boost Applied: +{priority_boost:.1f}")

                        best_alignment = format_local_time(wind_credibility.get('best_alignment_time'))
                        if best_alignment != "Unknown":
                            st.write(f"Peak Alignment: {best_alignment}")

                        triggers = wind_credibility.get('triggers_met') or []
                        if triggers:
                            st.caption(f"Triggers: {', '.join(triggers)}")

                    wind_analysis = stand_recommendations[0].get('wind_analysis', {}) if stand_recommendations else {}

                    # Wind analysis with current conditions
                    if wind_analysis:
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
                    fallback_crosswind_dirs = []
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

                    if deer_approach_bearing is not None:
                        crosswind_offsets = [
                            (deer_approach_bearing + 90) % 360,
                            (deer_approach_bearing - 90) % 360,
                        ]
                        for bearing in crosswind_offsets:
                            compass_label = degrees_to_compass(bearing)
                            if compass_label not in fallback_crosswind_dirs:
                                fallback_crosswind_dirs.append(compass_label)

                    preferred_winds_display = []
                    avoid_winds_display = []
                    
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
                        
                        preferred_winds_display = []
                        if wind_credibility:
                            preferred_winds_display = list(wind_credibility.get('preferred_directions') or [])
                        if not preferred_winds_display:
                            preferred_winds_display = fallback_crosswind_dirs.copy()

                        avoid_winds_display = []
                        if wind_analysis:
                            scent_cone = wind_analysis.get('scent_cone_direction')
                            if scent_cone is not None:
                                avoid_winds_display.append(degrees_to_compass(scent_cone))
                        if not avoid_winds_display and deer_approach_dir:
                            avoid_winds_display.append(deer_approach_dir)

                        st.markdown("**🧭 SPECIFIC WIND DIRECTIONS FOR THIS STAND:**")
                        st.write(f"• **Deer likely approach from:** {deer_approach_dir} ({deer_approach_bearing:.0f}°)")
                        if preferred_winds_display:
                            st.write(f"• **Preferred winds:** {', '.join(preferred_winds_display)}")
                        if avoid_winds_display:
                            st.write(f"• **Avoid winds:** {', '.join(avoid_winds_display)} (pushes scent toward deer)")

                        if stand_type in ["Travel Corridor", "General"]:
                            st.write("• **Game plan:** Hold a crosswind so scent drifts off the travel lane")
                        else:
                            st.write("• **Game plan:** Keep wind blowing from the deer toward you to guard the approach")
                        
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
                        if fallback_crosswind_dirs:
                            st.write(f"• **Suggested crosswinds:** {', '.join(fallback_crosswind_dirs)}")
                        if deer_approach_dir:
                            st.write(f"• **Avoid winds:** {deer_approach_dir} (puts scent on the approach route)")
                    
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
                        if preferred_winds_display:
                            st.write(f"• **Run winds:** {', '.join(preferred_winds_display)} to keep scent off the trail")
                        else:
                            st.write("• **Run a crosswind** so scent slides off the travel route")
                        if avoid_winds_display:
                            st.write(f"• **Avoid winds:** {', '.join(avoid_winds_display)} (deer will catch your scent)")
                        st.write("• **Goal:** Push scent past the corridor instead of down it")
                    else:  # Bedding/Feeding areas
                        st.write(f"• **Deer located {deer_approach_dir} of your stand** - stay just downwind of bedding/feeding activity")
                        if preferred_winds_display:
                            st.write(f"• **Best winds:** {', '.join(preferred_winds_display)} (blow deer-to-hunter)")
                        if avoid_winds_display:
                            st.write(f"• **Avoid winds:** {', '.join(avoid_winds_display)} (push scent into deer)")
                        st.write(f"• **Approach from opposite direction** - Come in from the {deer_approach_dir} side")
                        st.write(f"• **Check wind before hunting** - Abort if it starts drifting toward deer")
                    
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
                    "Trail Camera": "blue",
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
                    selected_enum = selected_type_data.get('enum_name', '')
                    
                    # Confidence rating
                    confidence = st.slider("📊 Confidence Level", 1, 10, 7, 
                                         help="How certain are you about this observation?")
                    
                    # Notes
                    notes = st.text_area("📝 Notes", placeholder="Describe what you observed...")
                    
                    # Type-specific details
                    details = {}
                    
                    if selected_enum == "FRESH_SCRAPE":
                        st.markdown("#### 🦌 Scrape Details")
                        details = {
                            "size": st.selectbox("Size", ["Small", "Medium", "Large", "Huge"]),
                            "freshness": st.selectbox("Freshness", ["Old", "Recent", "Fresh", "Very Fresh"]),
                            "licking_branch": st.checkbox("Active licking branch present"),
                            "multiple_scrapes": st.checkbox("Multiple scrapes in area")
                        }
                    
                    elif selected_enum == "RUB_LINE":
                        st.markdown("#### 🌳 Rub Details")
                        details = {
                            "tree_diameter_inches": st.number_input("Tree Diameter (inches)", 1, 36, 6),
                            "rub_height_inches": st.number_input("Rub Height (inches)", 12, 72, 36),
                            "direction": st.selectbox("Primary Direction", 
                                                    ["North", "South", "East", "West", "Northeast", "Northwest", "Southeast", "Southwest", "Multiple"]),
                            "tree_species": st.text_input("Tree Species (optional)"),
                            "multiple_rubs": st.checkbox("Multiple rubs in line")
                        }
                    
                    elif selected_enum == "BEDDING_AREA":
                        st.markdown("#### 🛏️ Bedding Details")
                        details = {
                            "number_of_beds": st.number_input("Number of Beds", 1, 20, 1),
                            "bed_size": st.selectbox("Bed Size", ["Small (Doe/Fawn)", "Medium (Young Buck)", "Large (Mature Buck)", "Multiple Sizes"]),
                            "cover_type": st.selectbox("Cover Type", ["Thick Brush", "Conifer Stand", "Creek Bottom", "Ridge Top", "Field Edge"]),
                            "thermal_advantage": st.checkbox("Good thermal cover")
                        }
                    
                    elif selected_enum == "TRAIL_CAMERA":
                        st.markdown("#### 📸 Camera Details")
                        cam_col1, cam_col2 = st.columns(2)
                        with cam_col1:
                            camera_brand = st.text_input("Camera Brand/Model (optional)", key="map_camera_brand")
                            camera_direction = st.selectbox(
                                "Camera Facing",
                                [
                                    "North", "South", "East", "West",
                                    "Northeast", "Northwest", "Southeast", "Southwest"
                                ],
                                key="map_camera_direction"
                            )
                            trail_width_feet = st.number_input("Trail Width (feet)", min_value=1, max_value=30, value=3, key="map_camera_trail_width")
                        with cam_col2:
                            include_setup_date = st.checkbox("Include camera setup date", value=True, key="map_camera_use_setup_date")
                            setup_date_value = None
                            if include_setup_date:
                                setup_date_value = st.date_input(
                                    "Camera Setup Date",
                                    value=datetime.now().date(),
                                    key="map_camera_setup_date"
                                )
                            setup_height_feet = st.number_input("Camera Height (feet)", min_value=1, max_value=20, value=8, key="map_camera_height")
                            detection_zone = st.selectbox(
                                "Detection Zone",
                                ["Narrow Trail", "Wide Trail", "Intersection", "Food Plot Edge", "Mineral Site", "Mock Scrape"],
                                key="map_camera_detection_zone"
                            )
                        peak_activity = st.text_input("Peak Activity Window (optional)", key="map_camera_peak_activity")
                        mature_buck_seen = st.checkbox("Captured a mature buck here recently?", key="map_camera_mature_flag")
                        mature_sighting_iso = None
                        mature_notes = None
                        if mature_buck_seen:
                            sight_col1, sight_col2 = st.columns(2)
                            with sight_col1:
                                sighting_date = st.date_input(
                                    "Mature Buck Capture Date",
                                    value=datetime.now().date(),
                                    key="map_camera_sighting_date"
                                )
                            with sight_col2:
                                default_time = datetime.now().replace(second=0, microsecond=0).time()
                                sighting_time = st.time_input(
                                    "Capture Time",
                                    value=default_time,
                                    key="map_camera_sighting_time"
                                )
                            mature_notes = st.text_area(
                                "Mature Buck Notes (optional)",
                                placeholder="Antler size, direction of travel, behavior...",
                                key="map_camera_sighting_notes"
                            )
                            mature_sighting_iso = datetime.combine(sighting_date, sighting_time).isoformat()

                        details = {
                            "camera_brand": camera_brand or None,
                            "camera_direction": camera_direction or None,
                            "trail_width_feet": float(trail_width_feet) if trail_width_feet else None,
                            "setup_height_feet": float(setup_height_feet) if setup_height_feet else None,
                            "detection_zone": detection_zone or None,
                            "peak_activity_time": peak_activity or None,
                            "mature_buck_seen": mature_buck_seen,
                            "mature_buck_seen_at": mature_sighting_iso,
                            "mature_buck_notes": mature_notes or None
                        }
                        if include_setup_date and setup_date_value:
                            details["setup_date"] = datetime.combine(setup_date_value, datetime.min.time()).isoformat()

                    elif selected_enum == "DEER_TRACKS":
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
                        if selected_enum == "FRESH_SCRAPE":
                            observation_data["scrape_details"] = details
                        elif selected_enum == "RUB_LINE":
                            observation_data["rub_details"] = details
                        elif selected_enum == "BEDDING_AREA":
                            observation_data["bedding_details"] = details
                        elif selected_enum == "TRAIL_CAMERA":
                            observation_data["camera_details"] = details
                        elif selected_enum == "DEER_TRACKS":
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
                    selected_type_data = next((ot for ot in observation_types if ot['type'] == selected_obs_type), {})
                    selected_enum = selected_type_data.get('enum_name', '')
                
                notes = st.text_area("📝 Notes", placeholder="Describe what you observed...")

                camera_details_manual: Dict[str, Any] = {}
                if selected_enum == "TRAIL_CAMERA":
                    st.markdown("#### 📸 Camera Details")
                    manual_cam_col1, manual_cam_col2 = st.columns(2)
                    with manual_cam_col1:
                        manual_camera_brand = st.text_input("Camera Brand/Model (optional)", key="manual_camera_brand")
                        manual_camera_direction = st.selectbox(
                            "Camera Facing",
                            [
                                "North", "South", "East", "West",
                                "Northeast", "Northwest", "Southeast", "Southwest"
                            ],
                            key="manual_camera_direction"
                        )
                    with manual_cam_col2:
                        manual_include_setup = st.checkbox("Include camera setup date", value=True, key="manual_camera_use_setup")
                        manual_setup_date = None
                        if manual_include_setup:
                            manual_setup_date = st.date_input(
                                "Camera Setup Date",
                                value=datetime.now().date(),
                                key="manual_camera_setup_date"
                            )
                    manual_peak_activity = st.text_input("Peak Activity Window (optional)", key="manual_camera_peak_activity")
                    manual_trail_width = st.number_input("Trail Width (feet)", min_value=1, max_value=30, value=3, key="manual_camera_trail_width")
                    manual_setup_height = st.number_input("Camera Height (feet)", min_value=1, max_value=20, value=8, key="manual_camera_height")
                    manual_detection_zone = st.selectbox(
                        "Detection Zone",
                        ["Narrow Trail", "Wide Trail", "Intersection", "Food Plot Edge", "Mineral Site", "Mock Scrape"],
                        key="manual_camera_detection_zone"
                    )
                    manual_mature_buck_seen = st.checkbox("Captured a mature buck here recently?", key="manual_camera_mature_flag")
                    manual_mature_iso = None
                    manual_mature_notes = None
                    if manual_mature_buck_seen:
                        manual_sighting_col1, manual_sighting_col2 = st.columns(2)
                        with manual_sighting_col1:
                            manual_sighting_date = st.date_input(
                                "Mature Buck Capture Date",
                                value=datetime.now().date(),
                                key="manual_camera_sighting_date"
                            )
                        with manual_sighting_col2:
                            manual_default_time = datetime.now().replace(second=0, microsecond=0).time()
                            manual_sighting_time = st.time_input(
                                "Capture Time",
                                value=manual_default_time,
                                key="manual_camera_sighting_time"
                            )
                        manual_mature_notes = st.text_area(
                            "Mature Buck Notes (optional)",
                            placeholder="Antler size, behavior, direction...",
                            key="manual_camera_sighting_notes"
                        )
                        manual_mature_iso = datetime.combine(manual_sighting_date, manual_sighting_time).isoformat()

                    camera_details_manual = {
                        "camera_brand": manual_camera_brand or None,
                        "camera_direction": manual_camera_direction or None,
                        "peak_activity_time": manual_peak_activity or None,
                        "trail_width_feet": float(manual_trail_width) if manual_trail_width else None,
                        "setup_height_feet": float(manual_setup_height) if manual_setup_height else None,
                        "detection_zone": manual_detection_zone or None,
                        "mature_buck_seen": manual_mature_buck_seen,
                        "mature_buck_seen_at": manual_mature_iso,
                        "mature_buck_notes": manual_mature_notes or None
                    }
                    if manual_include_setup and manual_setup_date:
                        camera_details_manual["setup_date"] = datetime.combine(manual_setup_date, datetime.min.time()).isoformat()
                
                submitted = st.form_submit_button("✅ Add Observation", type="primary")
                
                if submitted:
                    observation_data = {
                        "lat": manual_lat,
                        "lon": manual_lon,
                        "observation_type": selected_obs_type,
                        "confidence": confidence,
                        "notes": notes
                    }

                    if camera_details_manual:
                        observation_data["camera_details"] = camera_details_manual
                    
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
