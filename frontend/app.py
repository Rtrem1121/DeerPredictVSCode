import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json
from datetime import datetime
from map_config import MAP_SOURCES, OVERLAY_SOURCES

# --- Map Configuration ---
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

# --- App Configuration ---
st.set_page_config(
    page_title="🏔️ Vermont Deer Hunter",
    page_icon="🦌",
    layout="wide"
)

# Custom CSS for clean styling
st.markdown("""
<style>
.main-header {
    background: linear-gradient(45deg, #2E7D32, #4CAF50);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 1rem;
}
.map-container {
    border: 3px solid #2E7D32;
    border-radius: 10px;
    padding: 10px;
    background-color: #f8f9fa;
}
</style>
""", unsafe_allow_html=True)

# Simple Header
st.markdown("""
<div class="main-header">
    <h1>🏔️ Vermont Deer Hunter 🦌</h1>
    <p><b>Click anywhere on the map to find the best hunting spots</b></p>
</div>
""", unsafe_allow_html=True)

# Simple controls in one row
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
with col1:
    map_type = st.selectbox("Map Type", list(MAP_CONFIGS.keys()))
with col2:
    season = st.selectbox("Season", ["early_season", "rut", "late_season"], 
                         format_func=lambda x: x.replace("_", " ").title())
with col3:
    date = st.date_input("Date", datetime.now())
with col4:
    time = st.time_input("Time", datetime.now().time())

# Manual coordinate input as backup option
st.markdown("### 🎯 Click on the map below, or enter coordinates manually:")

coord_col1, coord_col2, coord_col3 = st.columns([3, 3, 2])
with coord_col1:
    manual_lat = st.number_input("Latitude", value=44.0459, format="%.6f", step=0.000001)
with coord_col2:
    manual_lon = st.number_input("Longitude", value=-72.7107, format="%.6f", step=0.000001)
with coord_col3:
    manual_predict = st.button("🎯 ANALYZE HERE", type="primary")

# Initialize session state
if 'last_prediction_coords' not in st.session_state:
    st.session_state.last_prediction_coords = None
if 'prediction_result' not in st.session_state:
    st.session_state.prediction_result = None
if 'last_processed_click' not in st.session_state:
    st.session_state.last_processed_click = None

# Check for manual prediction first
prediction_triggered = False
clicked_lat = None
clicked_lon = None

if manual_predict:
    clicked_lat = manual_lat
    clicked_lon = manual_lon
    current_coords = f"{clicked_lat:.6f},{clicked_lon:.6f}"
    
    # Only trigger if coordinates are different from last prediction
    if st.session_state.last_prediction_coords != current_coords:
        prediction_triggered = True
        st.session_state.last_prediction_coords = current_coords

# Center map on Vermont
VERMONT_CENTER = [44.0459, -72.7107]

# Create the main map
main_map = create_map(VERMONT_CENTER, 8, map_type)

# Get map click data
st.markdown('<div class="map-container">', unsafe_allow_html=True)
map_data = st_folium(main_map, width=None, height=600, returned_objects=["last_object_clicked", "last_clicked"])
st.markdown('</div>', unsafe_allow_html=True)

# Debug info (remove this later)
if st.checkbox("Show debug info"):
    st.write("Map data:", map_data)

# Process click data - trigger prediction on any map click (if no manual prediction)
if not prediction_triggered and map_data.get('last_clicked'):
    clicked_lat = map_data['last_clicked']['lat']
    clicked_lon = map_data['last_clicked']['lng']
    current_coords = f"{clicked_lat:.6f},{clicked_lon:.6f}"
    
    # Only trigger if this is a NEW click (different from last processed click)
    last_click_key = f"{clicked_lat:.6f},{clicked_lon:.6f}"
    if st.session_state.last_processed_click != last_click_key:
        st.session_state.last_processed_click = last_click_key
        
        # Only trigger prediction if coordinates are different from last prediction
        if st.session_state.last_prediction_coords != current_coords:
            prediction_triggered = True
            st.session_state.last_prediction_coords = current_coords

# Process prediction if triggered by either method
if prediction_triggered:
    
    st.success(f"📍 Analyzing location: {clicked_lat:.6f}, {clicked_lon:.6f}")
    
    # Prepare prediction request
    datetime_str = f"{date}T{time}"
    
    prediction_data = {
        "lat": clicked_lat,
        "lon": clicked_lon,
        "date_time": datetime_str,
        "season": season
    }
    
    # Make API call
    try:
        with st.spinner("🔍 Analyzing deer activity and finding best hunting spots..."):
            response = requests.post("http://backend:8000/predict", json=prediction_data)
        
        if response.status_code == 200:
            prediction = response.json()
            
            # Store the prediction result in session state
            st.session_state.prediction_result = {
                'prediction': prediction,
                'clicked_lat': clicked_lat,
                'clicked_lon': clicked_lon,
                'map_type': map_type
            }
        
        else:
            st.error(f"API Error: {response.status_code}")
            st.session_state.prediction_result = None
            
    except Exception as e:
        st.error(f"Error making prediction: {str(e)}")
        st.session_state.prediction_result = None

# Display results if we have them
if st.session_state.prediction_result:
    result = st.session_state.prediction_result
    prediction = result['prediction']
    clicked_lat = result['clicked_lat'] 
    clicked_lon = result['clicked_lon']
    
    # Create ONE results map that replaces the main map
    st.markdown("## 🎯 Your Hunting Analysis Results")
    results_map = create_map([clicked_lat, clicked_lon], 14, map_type)
    
    # Add clicked location marker with VERY prominent styling (your initial click point)
    folium.Marker(
        [clicked_lat, clicked_lon],
        popup=f"📍 YOUR INITIAL CLICK POINT<br>Lat: {clicked_lat:.6f}<br>Lon: {clicked_lon:.6f}<br><br>This is where you clicked to start the analysis",
        tooltip=f"📍 Initial Click: {clicked_lat:.6f}, {clicked_lon:.6f}",
        icon=folium.Icon(color='red', icon='bullseye', prefix='fa', icon_size=(40, 40))
    ).add_to(results_map)
    
    # Add an additional circle marker to make it even more visible
    folium.CircleMarker(
        [clicked_lat, clicked_lon],
        radius=15,
        popup=f"📍 YOUR CLICK POINT<br>{clicked_lat:.6f}, {clicked_lon:.6f}",
        color='red',
        weight=4,
        fillColor='yellow',
        fillOpacity=0.7
    ).add_to(results_map)
    
    # Add deer activity markers
    if prediction.get('bedding_zones', {}).get('features'):
        for feature in prediction['bedding_zones']['features']:
            if feature['geometry']['type'] == 'Point':
                coords = feature['geometry']['coordinates']
                folium.Marker(
                    [coords[1], coords[0]],
                    popup=f"🛏️ Bedding Zone<br>Score: {feature['properties'].get('score', 'N/A')}",
                    icon=folium.Icon(color='darkred', icon='tree', prefix='fa')
                ).add_to(results_map)
    
    if prediction.get('feeding_areas', {}).get('features'):
        for feature in prediction['feeding_areas']['features']:
            if feature['geometry']['type'] == 'Point':
                coords = feature['geometry']['coordinates']
                folium.Marker(
                    [coords[1], coords[0]],
                    popup=f"🌾 Feeding Area<br>Score: {feature['properties'].get('score', 'N/A')}",
                    icon=folium.Icon(color='green', icon='leaf', prefix='fa')
                ).add_to(results_map)
    
    if prediction.get('travel_corridors', {}).get('features'):
        for feature in prediction['travel_corridors']['features']:
            if feature['geometry']['type'] == 'Point':
                coords = feature['geometry']['coordinates']
                folium.Marker(
                    [coords[1], coords[0]],
                    popup=f"🚶 Travel Corridor<br>Score: {feature['properties'].get('score', 'N/A')}",
                    icon=folium.Icon(color='blue', icon='shoe-prints', prefix='fa')
                ).add_to(results_map)
    
    # Add best hunting stands
    if prediction.get('five_best_stands'):
        for i, stand in enumerate(prediction['five_best_stands']):
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
            ).add_to(results_map)
    
    # Add unique access point markers
    if prediction.get('five_best_stands') and len(prediction['five_best_stands']) > 0:
        unique_access_points = prediction['five_best_stands'][0].get('unique_access_points', [])
        
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
            ).add_to(results_map)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 280px; height: auto; 
                background-color: white; border:3px solid #2E7D32; z-index:9999; 
                font-size:12px; padding: 12px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
    <p style="margin:0; font-weight:bold; font-size:14px; color:#2E7D32;">🦌 HUNTING MAP</p>
    <hr style="margin: 8px 0; border-color:#2E7D32;">
    
    <p style="margin:2px 0;"><span style="color:red; font-weight:bold;">🎯⭕</span> <strong>Your Initial Click Point</strong></p>
    <p style="margin:2px 0;"><span style="color:darkred">🌳</span> Bedding Areas</p>
    <p style="margin:2px 0;"><span style="color:green">🍃</span> Feeding Areas</p>
    <p style="margin:2px 0;"><span style="color:blue">👣</span> Travel Corridors</p>
    <p style="margin:2px 0;"><span style="color:darkgreen">🎯</span> Best Stands (80%+ confidence)</p>
    <p style="margin:2px 0;"><span style="color:orange">🎯</span> Good Stands (70%+ confidence)</p>
    <p style="margin:2px 0;"><span style="color:darkblue">🚗</span> Parking/Access</p>
    </div>
    '''
    results_map.get_root().html.add_child(folium.Element(legend_html))
    
    # Display the single results map
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st_folium(results_map, width=None, height=600, key=f"results_{clicked_lat}_{clicked_lon}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show access information for the #1 best stand
    if prediction.get('five_best_stands') and len(prediction['five_best_stands']) > 0:
        best_stand = prediction['five_best_stands'][0]
        
        st.markdown("## 🚗 Access Information to Best Stand (#1)")
        
        # Access route information
        if 'access_route' in best_stand:
            route = best_stand['access_route']
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📍 Parking & Approach")
                st.write(f"**🚗 Parking Location:** {route.get('parking_description', 'See map for parking points')}")
                st.write(f"**🚶 Walking Distance:** {route['total_distance_yards']} yards")
                st.write(f"**⛰️ Route Difficulty:** {route['route_difficulty']}")
                st.write(f"**⏱️ Estimated Walk Time:** {route.get('estimated_walk_time', 'N/A')}")
            
            with col2:
                st.markdown("### 🧭 Route Details")
                st.write(f"**🎯 Stand Type:** {best_stand['type']}")
                st.write(f"**📊 Confidence:** {best_stand['confidence']:.1f}%")
                st.write(f"**🌬️ Wind Favorability:** {best_stand['wind_favorability']:.1f}%")
                st.write(f"**📐 Distance from Click:** {best_stand['distance_yards']} yards {best_stand['direction']}")
        
        # Show unique access points if available
        if 'unique_access_points' in best_stand and best_stand['unique_access_points']:
            st.markdown("### 🗺️ Available Parking Options")
            for i, access_point in enumerate(best_stand['unique_access_points']):
                if access_point['serves_stands'] and 1 in access_point['serves_stands']:
                    with st.expander(f"🚗 Parking Option #{i+1} - {access_point['access_type']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Road Type:** {access_point['access_type']}")
                            st.write(f"**Drive Time:** {access_point['estimated_drive_time']}")
                            st.write(f"**GPS Coordinates:** {access_point['lat']:.6f}, {access_point['lon']:.6f}")
                        with col2:
                            st.write(f"**Distance to Parking:** {access_point['distance_miles']} miles")
                            st.write(f"**Serves Stands:** #{', #'.join(map(str, access_point['serves_stands']))}")
        
        st.markdown("---")
    
    # Show stand details in a simple table
    if prediction.get('five_best_stands'):
        st.markdown("## 📊 Stand Details")
        for i, stand in enumerate(prediction['five_best_stands']):
            with st.expander(f"🎯 Stand #{i+1} - {stand['confidence']:.1f}% Confidence"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Type:** {stand['type']}")
                    st.write(f"**Distance:** {stand['distance_yards']} yards {stand['direction']}")
                    st.write(f"**GPS:** {stand['coordinates']['lat']:.6f}, {stand['coordinates']['lon']:.6f}")
                with col2:
                    st.write(f"**Wind Favorability:** {stand['wind_favorability']:.1f}%")
                    if 'access_route' in stand:
                        route = stand['access_route']
                        st.write(f"**Walk from parking:** {route['total_distance_yards']} yards")
                        st.write(f"**Route difficulty:** {route['route_difficulty']}")
                
                st.write(f"**Setup Notes:** {stand['setup_notes']}")
    
    # Add button to clear results and start new analysis
    st.markdown("---")
    if st.button("🔄 Analyze New Location", type="secondary"):
        st.session_state.prediction_result = None
        st.session_state.last_prediction_coords = None
        st.session_state.last_processed_click = None
        st.experimental_rerun()

else:
    # Clean instructions for users
    st.markdown("""
    ## 🎯 How to Use This Tool
    
    **👆 Simply click anywhere on the map above** to get instant hunting analysis!
    
    The system will automatically:
    - 🔍 Analyze deer behavior at your clicked location
    - 🎯 Find the 5 best hunting stands nearby  
    - 🚗 Show parking and access routes
    - 📊 Provide detailed setup instructions
    """)
    
    st.info("💡 **It's that simple** - just click any spot on the map and get your hunting analysis!")
    
    with st.expander("📋 What You'll See in the Results"):
        st.markdown("""
        **After clicking, the map will update to show:**
        - 🎯 **Red crosshairs**: Your selected target location
        - 🌳 **Dark red markers**: Bedding areas (where deer rest)
        - 🍃 **Green markers**: Feeding areas (where deer eat)  
        - 👣 **Blue markers**: Travel corridors (deer movement paths)
        - 🎯 **Hunting stands**: Ranked by confidence level
        - 🚗 **Blue car icons**: Parking and access points
        
        **Stand Confidence Colors:**
        - **Dark Green** = 80%+ confidence (hunt here first!)
        - **Orange** = 70%+ confidence (good backup options)
        - **Gray** = Lower confidence (last resort)
        """)
