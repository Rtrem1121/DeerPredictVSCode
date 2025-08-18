import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json
import os
from datetime import datetime, timedelta
from map_config import MAP_SOURCES, OVERLAY_SOURCES

# --- Backend Configuration ---
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

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
        
        # Legal hunting times for Vermont
        legal_times = generate_legal_hunting_times(hunt_date)
        if legal_times:
            earliest_time, latest_time = legal_times[0][1], legal_times[-1][1]
            st.success(f"✅ **Vermont Legal Hours:** {earliest_time} - {latest_time}")
            
            # Time selection
            selected_time_idx = st.selectbox(
                "⏰ Hunt Time (Vermont Legal Hours Only)",
                range(len(legal_times)),
                format_func=lambda x: legal_times[x][1],
                index=0
            )
            selected_time = legal_times[selected_time_idx][0]
        else:
            st.error("Unable to calculate legal hunting times")
            selected_time = datetime.now().time()
        
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
        
        # Display map and capture click events
        map_data = st_folium(m, key="hunt_map", width=700, height=500)
        
        # Update location if map was clicked
        if map_data['last_clicked']:
            new_lat = map_data['last_clicked']['lat']
            new_lng = map_data['last_clicked']['lng']
            st.session_state.hunt_location = [new_lat, new_lng]
            st.rerun()
    
    # Display current coordinates
    # Advanced options
    with st.expander("🎥 Advanced Options"):
        include_camera = st.checkbox(
            "Include Optimal Camera Placement", 
            value=False,
            help="Calculate the single optimal trail camera position using satellite analysis"
        )
    
    st.info(f"📍 **Hunt Coordinates:** {st.session_state.hunt_location[0]:.6f}, {st.session_state.hunt_location[1]:.6f}")
    
    # Prediction button
    if st.button("🎯 Generate Hunting Predictions", type="primary"):
        with st.spinner("🧠 Analyzing deer movement patterns..."):
            # Prepare prediction request
            prediction_data = {
                "lat": st.session_state.hunt_location[0],
                "lon": st.session_state.hunt_location[1],
                "date_time": f"{hunt_date}T{selected_time.strftime('%H:%M:%S')}",
                "season": season,
                "include_camera_placement": include_camera
            }
            
            try:
                # Make prediction request
                response = requests.post(
                    f"{BACKEND_URL}/predict",
                    json=prediction_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    prediction = response.json()
                    st.success("✅ **Prediction Complete!**")
                    
                    # Display prediction results
                    if 'mature_buck_analysis' in prediction:
                        mature_buck_data = prediction['mature_buck_analysis']
                        
                        # === MATURE BUCK MOVEMENT PREDICTION ===
                        movement_data = mature_buck_data.get('movement_prediction', {})
                        if movement_data:
                            st.markdown("## 🦌 **Mature Buck Movement Prediction**")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                movement_prob = movement_data.get('movement_probability', 0)
                                if movement_prob >= 75:
                                    st.success(f"🟢 **HIGH Movement Probability**\n{movement_prob:.0f}%")
                                elif movement_prob >= 50:
                                    st.info(f"🟡 **MODERATE Movement Probability**\n{movement_prob:.0f}%")
                                else:
                                    st.warning(f"🔴 **LOW Movement Probability**\n{movement_prob:.0f}%")
                            
                            with col2:
                                confidence_score = movement_data.get('confidence_score', 0)
                                st.metric("📊 Prediction Confidence", f"{confidence_score:.0f}%")
                            
                            with col3:
                                # Check if scouting data enhanced prediction
                                if 'scouting_enhanced' in prediction:
                                    st.success("🔍 **Enhanced by Scouting Data**")
                                else:
                                    st.info("📝 Add scouting data to improve")
                        
                        # === SPECIALIZED MATURE BUCK STAND RECOMMENDATIONS ===
                        stand_recommendations = mature_buck_data.get('stand_recommendations', [])
                        if stand_recommendations:
                            st.markdown("## 🪜 **Recommended Stand Locations**")
                            
                            for i, rec in enumerate(stand_recommendations, 1):
                                with st.expander(f"🎯 **STAND #{i}: {rec.get('type', 'Unknown')}** - Confidence: {rec.get('confidence', 0):.0f}%", expanded=i==1):
                                    
                                    coords = rec.get('coordinates', {})
                                    stand_lat = coords.get('lat', 0)
                                    stand_lon = coords.get('lon', 0)
                                    
                                    col1, col2 = st.columns([2, 1])
                                    
                                    with col1:
                                        st.markdown(f"**📍 GPS Coordinates:** `{stand_lat:.6f}, {stand_lon:.6f}`")
                                        st.markdown(f"**📝 Strategy:** {rec.get('description', 'N/A')}")
                                        st.markdown(f"**⏰ Best Times:** {rec.get('best_times', 'N/A')}")
                                        
                                        # Wind analysis
                                        if rec.get('wind_optimized'):
                                            wind_notes = rec.get('wind_notes', [])
                                            if wind_notes:
                                                st.markdown("**🌬️ Wind Considerations:**")
                                                for note in wind_notes:
                                                    st.markdown(f"  • {note}")
                                    
                                    with col2:
                                        confidence = rec.get('confidence', 0)
                                        if confidence >= 85:
                                            st.success(f"🎯 {confidence:.0f}% Confidence\n**PRIME LOCATION**")
                                        elif confidence >= 70:
                                            st.info(f"✅ {confidence:.0f}% Confidence\n**SOLID CHOICE**")
                                        else:
                                            st.warning(f"⚠️ {confidence:.0f}% Confidence\n**BACKUP OPTION**")
                    
                    # === OPTIMAL CAMERA PLACEMENT ===
                    if 'optimal_camera_placement' in prediction and prediction['optimal_camera_placement']:
                        camera_data = prediction['optimal_camera_placement']
                        
                        if camera_data.get('enabled', False):
                            st.markdown("## 🎥 **Optimal Camera Placement**")
                            
                            camera_coords = camera_data.get('camera_coordinates', {})
                            target_coords = camera_data.get('target_coordinates', {})
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                confidence = camera_data.get('confidence_score', 0)
                                if confidence >= 85:
                                    st.success(f"🔥 **EXCELLENT Position**\n{confidence:.1f}% confidence")
                                elif confidence >= 75:
                                    st.info(f"⭐ **VERY GOOD Position**\n{confidence:.1f}% confidence")
                                else:
                                    st.info(f"✅ **GOOD Position**\n{confidence:.1f}% confidence")
                            
                            with col2:
                                distance = camera_data.get('distance_meters', 0)
                                st.metric("📏 Distance from Target", f"{distance:.0f} meters")
                            
                            with col3:
                                detection_range = camera_data.get('detection_range', "60-120 meters")
                                st.metric("📡 Detection Range", detection_range)
                            
                            # Camera placement details
                            with st.expander("🎯 **Camera Setup Details**", expanded=True):
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**📍 Camera GPS Coordinates:**")
                                    st.code(f"{camera_coords.get('lat', 0):.6f}, {camera_coords.get('lon', 0):.6f}")
                                    
                                    st.markdown("**🎯 Target Location:**")
                                    st.code(f"{target_coords.get('lat', 0):.6f}, {target_coords.get('lon', 0):.6f}")
                                    
                                    reasoning = camera_data.get('placement_reasoning', 'Optimal positioning')
                                    st.markdown(f"**🧠 Strategy:** {reasoning}")
                                
                                with col2:
                                    optimal_times = camera_data.get('optimal_times', ['dawn', 'dusk'])
                                    st.markdown(f"**⏰ Best Times:** {', '.join(optimal_times)}")
                                    
                                    st.markdown("**🔧 Setup Instructions:**")
                                    integration_notes = camera_data.get('integration_notes', [])
                                    for note in integration_notes:
                                        st.markdown(f"• {note}")
                        
                        elif camera_data.get('error'):
                            st.warning(f"🎥 Camera placement calculation failed: {camera_data.get('error')}")
                
                else:
                    st.error(f"Prediction failed: {response.text}")
                    
            except Exception as e:
                st.error(f"Failed to get prediction: {e}")

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
