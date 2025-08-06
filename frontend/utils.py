"""
Frontend utility functions for the deer hunting prediction app.
Provides reusable functions for map creation, API calls, and UI components.
"""
import streamlit as st
import folium
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from .config import (
    VERMONT_CENTER, DEFAULT_ZOOM, RESULTS_ZOOM, 
    BACKEND_URL, API_TIMEOUT, MAP_LEGEND_HTML,
    VERMONT_BOUNDS
)
from .map_config import MAP_SOURCES

logger = logging.getLogger(__name__)

# Map configuration
MAP_CONFIGS = {
    name: config for name, config in MAP_SOURCES.items() 
    if config.get("enabled", True)
}


def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """
    Validate that coordinates are within Vermont boundaries.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        lat = float(lat)
        lon = float(lon)
        
        if not (VERMONT_BOUNDS['min_lat'] <= lat <= VERMONT_BOUNDS['max_lat']):
            return False, f"Latitude {lat:.6f} is outside Vermont boundaries"
            
        if not (VERMONT_BOUNDS['min_lon'] <= lon <= VERMONT_BOUNDS['max_lon']):
            return False, f"Longitude {lon:.6f} is outside Vermont boundaries"
            
        return True, ""
        
    except (ValueError, TypeError):
        return False, "Invalid coordinate format"


def create_map(location: list, zoom_start: int, map_type: str) -> folium.Map:
    """
    Create a Folium map with the specified configuration.
    
    Args:
        location: [lat, lon] coordinates for map center
        zoom_start: Initial zoom level
        map_type: Type of map tiles to use
        
    Returns:
        folium.Map: Configured map object
    """
    try:
        config = MAP_CONFIGS.get(map_type, MAP_CONFIGS.get("Street Map", {}))
        
        if config.get("tiles"):
            return folium.Map(
                location=location,
                zoom_start=zoom_start,
                tiles=config["tiles"],
                attr=config.get("attr", "")
            )
        else:
            return folium.Map(location=location, zoom_start=zoom_start)
            
    except Exception as e:
        logger.warning(f"Failed to create map with type {map_type}: {e}")
        # Fallback to default map
        return folium.Map(location=location, zoom_start=zoom_start)


def add_target_marker(map_obj: folium.Map, lat: float, lon: float) -> None:
    """
    Add target location marker to map.
    
    Args:
        map_obj: Folium map object
        lat: Latitude coordinate
        lon: Longitude coordinate
    """
    folium.Marker(
        [lat, lon],
        popup=f"🎯 YOUR TARGET LOCATION<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}",
        tooltip=f"Target: {lat:.6f}, {lon:.6f}",
        icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')
    ).add_to(map_obj)


def add_prediction_markers(map_obj: folium.Map, prediction_data: Dict[str, Any]) -> None:
    """
    Add all prediction markers to the map.
    
    Args:
        map_obj: Folium map object
        prediction_data: Prediction response data
    """
    try:
        # Add bedding zone markers
        if prediction_data.get('bedding_zones', {}).get('features'):
            for feature in prediction_data['bedding_zones']['features']:
                if feature['geometry']['type'] == 'Point':
                    coords = feature['geometry']['coordinates']
                    folium.Marker(
                        [coords[1], coords[0]],
                        popup=f"🛏️ Bedding Zone<br>Score: {feature['properties'].get('score', 'N/A')}",
                        icon=folium.Icon(color='darkred', icon='tree', prefix='fa')
                    ).add_to(map_obj)
        
        # Add feeding area markers
        if prediction_data.get('feeding_areas', {}).get('features'):
            for feature in prediction_data['feeding_areas']['features']:
                if feature['geometry']['type'] == 'Point':
                    coords = feature['geometry']['coordinates']
                    folium.Marker(
                        [coords[1], coords[0]],
                        popup=f"🌾 Feeding Area<br>Score: {feature['properties'].get('score', 'N/A')}",
                        icon=folium.Icon(color='green', icon='leaf', prefix='fa')
                    ).add_to(map_obj)
        
        # Add travel corridor markers
        if prediction_data.get('travel_corridors', {}).get('features'):
            for feature in prediction_data['travel_corridors']['features']:
                if feature['geometry']['type'] == 'Point':
                    coords = feature['geometry']['coordinates']
                    folium.Marker(
                        [coords[1], coords[0]],
                        popup=f"🚶 Travel Corridor<br>Score: {feature['properties'].get('score', 'N/A')}",
                        icon=folium.Icon(color='blue', icon='shoe-prints', prefix='fa')
                    ).add_to(map_obj)
        
        # Add hunting stand markers
        if prediction_data.get('five_best_stands'):
            for i, stand in enumerate(prediction_data['five_best_stands']):
                coords = stand['coordinates']
                confidence = stand['confidence']
                
                # Color code by confidence
                if confidence >= 80:
                    color = 'darkgreen'
                    icon = 'bullseye'
                elif confidence >= 70:
                    color = 'orange'
                    icon = 'crosshairs'
                else:
                    color = 'gray'
                    icon = 'dot-circle'
                
                popup_text = f"""
                <b>🎯 Stand #{i+1}</b><br>
                <b>Type:</b> {stand['type']}<br>
                <b>Confidence:</b> {confidence:.1f}%<br>
                <b>Distance:</b> {stand['distance_yards']} yards {stand['direction']}<br>
                <b>Setup:</b> {stand['setup_notes'][:100]}...
                """
                
                folium.Marker(
                    [coords['lat'], coords['lon']],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"🎯 Stand #{i+1} - {confidence:.1f}% confidence",
                    icon=folium.Icon(color=color, icon=icon, prefix='fa')
                ).add_to(map_obj)
        
        # Add access point markers
        if prediction_data.get('five_best_stands') and len(prediction_data['five_best_stands']) > 0:
            unique_access_points = prediction_data['five_best_stands'][0].get('unique_access_points', [])
            
            for access_point in unique_access_points:
                stands_served = ', '.join([f"#{stand_id}" for stand_id in access_point['serves_stands']])
                access_popup_text = f"""
                <b>🚗 PARKING & ACCESS</b><br>
                <b>Road Type:</b> {access_point['access_type']}<br>
                <b>Drive Time:</b> {access_point['estimated_drive_time']}<br>
                <b>Distance:</b> {access_point['distance_miles']} miles<br>
                <b>Serves Stands:</b> {stands_served}
                """
                
                folium.Marker(
                    [access_point['lat'], access_point['lon']],
                    popup=folium.Popup(access_popup_text, max_width=300),
                    tooltip=f"🚗 PARKING: {access_point['access_type']}",
                    icon=folium.Icon(color='darkblue', icon='car', prefix='fa')
                ).add_to(map_obj)
                
    except Exception as e:
        logger.error(f"Error adding prediction markers: {e}")


def add_map_legend(map_obj: folium.Map) -> None:
    """
    Add legend to the map.
    
    Args:
        map_obj: Folium map object
    """
    map_obj.get_root().html.add_child(folium.Element(MAP_LEGEND_HTML))


def make_prediction_request(
    lat: float, 
    lon: float, 
    date_time: str, 
    season: str
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Make prediction API request.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        date_time: ISO format datetime string
        season: Hunting season
        
    Returns:
        Tuple of (success, response_data, error_message)
    """
    try:
        prediction_data = {
            "lat": lat,
            "lon": lon,
            "date_time": date_time,
            "season": season
        }
        
        response = requests.post(
            f"{BACKEND_URL}/predict",
            json=prediction_data,
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            return True, response.json(), ""
        else:
            error_msg = f"API Error: {response.status_code}"
            if response.status_code == 400:
                try:
                    error_detail = response.json().get('detail', 'Bad request')
                    error_msg = f"Invalid input: {error_detail}"
                except:
                    pass
            elif response.status_code == 429:
                error_msg = "Rate limit exceeded. Please wait and try again."
            elif response.status_code >= 500:
                error_msg = "Server error. Please try again later."
                
            return False, {}, error_msg
            
    except requests.exceptions.Timeout:
        return False, {}, "Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return False, {}, "Unable to connect to prediction service."
    except Exception as e:
        logger.error(f"Prediction request failed: {e}")
        return False, {}, f"Prediction failed: {str(e)}"


def display_error_message(message: str) -> None:
    """
    Display error message with consistent styling.
    
    Args:
        message: Error message to display
    """
    st.error(f"❌ {message}")


def display_success_message(message: str) -> None:
    """
    Display success message with consistent styling.
    
    Args:
        message: Success message to display
    """
    st.success(f"✅ {message}")


def display_info_message(message: str) -> None:
    """
    Display info message with consistent styling.
    
    Args:
        message: Info message to display
    """
    st.info(f"💡 {message}")


def format_season_name(season: str) -> str:
    """
    Format season name for display.
    
    Args:
        season: Season identifier
        
    Returns:
        Formatted season name
    """
    return season.replace("_", " ").title()


def validate_datetime_input(date_input, time_input) -> Tuple[bool, str, str]:
    """
    Validate and format datetime inputs.
    
    Args:
        date_input: Date input from Streamlit
        time_input: Time input from Streamlit
        
    Returns:
        Tuple of (is_valid, datetime_string, error_message)
    """
    try:
        datetime_str = f"{date_input}T{time_input}"
        # Validate by parsing
        datetime.fromisoformat(datetime_str)
        return True, datetime_str, ""
    except Exception as e:
        return False, "", f"Invalid date/time format: {e}"
