import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json
import os
from datetime import datetime, timedelta
from map_config import MAP_SOURCES, OVERLAY_SOURCES

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
.metric-row {
    display: flex;
    justify-content: space-between;
}
.vermont-header {
    background: linear-gradient(45deg, #2E7D32, #4CAF50);
    color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}
.season-badge {
    background: #1976D2;
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.8rem;
}
.weather-info {
    background: #f5f5f5;
    padding: 0.5rem;
    border-radius: 0.25rem;
    border-left: 4px solid #2196F3;
}
</style>
""", unsafe_allow_html=True)

# --- Backend API URL ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# --- Main App ---
st.markdown('<div class="vermont-header"><h1>🏔️ Vermont White-tailed Deer Movement Predictor</h1><p>Advanced habitat analysis for Vermont hunting conditions</p></div>', unsafe_allow_html=True)

# Add Vermont-specific information
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    **🏔️ Vermont Features:**
    - Green Mountain terrain analysis
    - Winter yard predictions
    - Seasonal migration patterns
    """)
with col2:
    st.markdown("""
    **❄️ Weather Integration:**
    - Snow depth tracking
    - Cold front detection
    - Barometric pressure
    """)
with col3:
    st.markdown("""
    **🌲 Vermont Habitats:**
    - Northern hardwood forests
    - Hemlock winter yards
    - Apple orchard locations
    """)

# Add helpful information about Vermont deer hunting
with st.expander("🦌 Vermont White-tailed Deer Behavior"):
    st.markdown("""
    **Vermont-Specific Deer Patterns:**
    
    🏔️ **Terrain Preferences:**
    - **Ridges & Saddles**: Travel corridors through Green Mountains
    - **South-facing Slopes**: Critical for winter thermal regulation
    - **Hardwood Benches**: Mast production areas (acorns, beech nuts)
    - **Conifer Stands**: Winter yards when snow >10 inches
    
    ❄️ **Seasonal Behavior:**
    - **Early Season (Sept-Oct)**: Pattern establishment, mast feeding
    - **Rut (Oct-Dec)**: Peak breeding activity, extended movement
    - **Late Season (Dec-Mar)**: Winter yard concentration, survival mode
    
    🌨️ **Winter Adaptations:**
    - Migrate 10-15 miles to winter yards when snow >10"
    - Prefer dense softwoods (hemlock, cedar) with >65% canopy closure
    - Activity peaks during warmest part of day (midday)
    - Rely on woody browse when other foods are buried
    
    🍇 **Vermont Food Sources:**
    - Acorns (red oak, white oak) - fall favorite
    - Wild/domestic apples - high energy during rut
    - Beech nuts - important mast crop
    - Conifer tips - winter survival food
    """)

# Add information about understanding score heatmaps
with st.expander("📊 Understanding Score Heatmaps - The Key to Success"):
    st.markdown("""
    **Score heatmaps are your most important tool!** They show exactly where deer are likely to be found.
    
    ## 🎯 **How to Read the Colors:**
    
    ### 🔴 **Red Zones (Score 8-10): HUNT HERE!**
    - **Excellent deer activity** - These are your prime hunting spots
    - **High probability** of deer presence during the selected season/time
    - **Focus your time** on these areas for best success
    
    ### 🟡 **Yellow Zones (Score 6-7): Good Options**
    - **Solid hunting potential** - backup locations
    - **Moderate to good** deer activity expected
    - **Worth hunting** if red zones are occupied or pressured
    
    ### 🔵 **Blue Zones (Score 0-5): Avoid These**
    - **Low deer activity** - poor hunting locations
    - **Better to walk through** these areas to reach red zones
    - **Don't waste time** hunting in blue areas
    
    ## 📋 **Three Different Heatmaps Explained:**
    
    ### 1. 🚶 **Travel Score Heatmap (Movement)**
    - Shows **deer highways** and corridors
    - **Red areas** = main travel routes between bedding and feeding
    - **Best for** morning/evening hunting when deer are moving
    - **Look for** saddles, ridge lines, creek bottoms, funnels
    
    ### 2. 🛏️ **Bedding Score Heatmap (Resting)**
    - Shows where deer **sleep and rest** during the day
    - **Red areas** = preferred bedding cover
    - **Best for** still-hunting or drives
    - **Look for** thick cover, thermal advantages, security
    
    ### 3. 🌾 **Feeding Score Heatmap (Eating)**
    - Shows where deer **eat and forage**
    - **Red areas** = prime food sources for the season
    - **Best for** evening hunting as deer come to feed
    - **Look for** mast crops, field edges, browse areas
    
    ## 💡 **Pro Hunting Tips:**
    
    ✅ **Hunt the Transitions**: Set up between red travel zones and red feeding zones
    
    ✅ **Wind Direction**: Always hunt with wind blowing from deer areas toward you
    
    ✅ **Multiple Maps**: Use all three heatmaps together - deer need food, water, cover, and travel routes
    
    ✅ **Seasonal Focus**: 
    - **Early Season**: Focus on feeding areas (food plots, mast)
    - **Rut**: Focus on travel corridors (deer moving for breeding)
    - **Late Season**: Focus on bedding areas (thermal cover, shelter)
    
    ⚠️ **Avoid Blue Zones** - They'll waste your hunting time!
    """)

# Add information about topographic maps
with st.expander("🗺️ Topographic Maps for Vermont Hunting"):
    st.markdown("""
    **Why topographic maps are essential for Vermont deer hunting:**
    
    🏔️ **Mountain Terrain**: Vermont's elevation changes create natural deer funnels
    - **Saddles**: Low points between peaks - major travel routes
    - **Benches**: Flat areas on slopes - feeding and bedding areas
    - **Creek Bottoms**: Water sources and travel corridors
    
    🌲 **Forest Edge Detection**: Identify transition zones where deer concentrate
    - Forest-to-field edges
    - Conifer-to-hardwood transitions
    - Elevation-driven vegetation changes
    
    **Map Type Recommendations for Vermont:**
    - **USGS Topo**: Best for detailed Green Mountain contours
    - **Esri Topo**: Excellent for current forest coverage
    - **Satellite**: Perfect for identifying actual land use patterns
    """)

# Add information about the better spots feature
with st.expander("🎯 Vermont-Enhanced Better Hunting Spots"):
    st.markdown("""
    **Vermont-Specific Spot Recommendations:**
    
    ⭐ **Enhanced Analysis**: Uses Vermont deer behavior patterns and terrain preferences
    
    🏔️ **Terrain Features Prioritized**:
    - Saddles and ridge connections
    - South-facing winter bedding areas  
    - Hardwood benches for mast
    - Conifer corridors for winter movement
    
    ❄️ **Weather-Adjusted Suggestions**:
    - Snow depth influences winter yard recommendations
    - Cold front timing affects travel corridor ratings
    - Barometric pressure considered for activity predictions
    
    📍 **Vermont Spot Types**:
    - 🔵 **Blue stars**: Mountain travel routes, saddles
    - 🔴 **Red stars**: Winter yards, thermal bedding areas
    - 🟢 **Green stars**: Mast areas, field edges, orchards
    
    🎯 **Vermont Hunting Tips**:
    - Focus on elevation transitions (1000-2000 ft)
    - Monitor snow depth for winter yard activation
    - Consider prevailing northwest winds for stand placement
    """)

st.write("**Select a Vermont location, date, and legal hunting time to predict deer activity with enhanced terrain analysis.**")

# --- Input Widgets ---
st.subheader("🎯 Hunting Prediction Setup")

# Create input columns for better organization
input_col1, input_col2, input_col3, input_col4 = st.columns(4)

with input_col1:
    season = st.selectbox("Season", ["Early Season", "Rut", "Late Season"])
    date = st.date_input("Date", datetime.now())

with input_col2:
    # Generate legal hunting times for the selected date
    legal_times = generate_legal_hunting_times(date)
    time_options = [time_str for _, time_str in legal_times]
    time_objects = [time_obj for time_obj, _ in legal_times]
    
    # Default to closest current time if within hunting hours, otherwise first available
    current_time = datetime.now().time()
    earliest, latest = get_vermont_legal_hunting_hours(date)
    
    default_index = 0
    if earliest <= current_time <= latest:
        # Find closest legal hunting time
        current_minutes = current_time.hour * 60 + current_time.minute
        closest_index = 0
        closest_diff = float('inf')
        
        for i, (time_obj, _) in enumerate(legal_times):
            time_minutes = time_obj.hour * 60 + time_obj.minute
            diff = abs(time_minutes - current_minutes)
            if diff < closest_diff:
                closest_diff = diff
                closest_index = i
        default_index = closest_index
    
    selected_time_str = st.selectbox(
        "Vermont Legal Hunting Time", 
        time_options, 
        index=default_index,
        help="⚖️ Vermont law: 30 min before sunrise to 30 min after sunset"
    )
    
    # Get the actual time object for the selected time
    selected_index = time_options.index(selected_time_str)
    time = time_objects[selected_index]
    
    map_type = st.selectbox("Map Type", list(MAP_CONFIGS.keys()))

with input_col3:
    # Map overlay options
    show_contours = st.checkbox("Show Contour Lines", value=False, help="Add elevation contour lines to any map type")
    show_terrain_shading = st.checkbox("Show Terrain Shading", value=False, help="Add hillshade overlay for terrain visualization")

with input_col4:
    # Vermont hunting hours information
    st.write("**⚖️ Vermont Hunting Hours**")
    earliest, latest = get_vermont_legal_hunting_hours(date)
    st.write(f"**Legal Hours:** {earliest.strftime('%I:%M %p')} - {latest.strftime('%I:%M %p')}")
    st.write("*30 min before sunrise to 30 min after sunset*")
    st.caption("📅 Times update automatically based on selected date")

# Show map description
st.info(MAP_CONFIGS[map_type]["description"])

# Set default values for suggestion parameters (removed from UI)
suggestion_threshold = 5.0
min_suggestion_rating = 8.0

# Center map on a default location
# Using a central US location as a default
DEFAULT_LOCATION = [39.8283, -98.5795]

# Create map with selected tile layer
m = create_map(DEFAULT_LOCATION, 5, map_type)

# Add overlays if requested
if show_contours:
    # Add USGS contour lines as overlay
    contour_layer = folium.raster_layers.WmsTileLayer(
        url="https://basemap.nationalmap.gov/arcgis/services/USGSTopoLarge/MapServer/WMSServer?",
        layers="0",
        transparent=True,
        format="image/png",
        name="Contour Lines",
        control=True
    )
    contour_layer.add_to(m)

if show_terrain_shading:
    # Add terrain hillshade overlay
    hillshade_layer = folium.raster_layers.WmsTileLayer(
        url="https://basemap.nationalmap.gov/arcgis/services/USGSImageryOnly/MapServer/WMSServer?",
        layers="0",
        transparent=True,
        format="image/png",
        name="Terrain Shading",
        control=True,
        opacity=0.6
    )
    hillshade_layer.add_to(m)

# Add a marker for the user to place
m.add_child(folium.LatLngPopup())

# Add layer control if overlays are present
if show_contours or show_terrain_shading:
    folium.LayerControl().add_to(m)

# Display the map and Get Prediction button side by side
map_col, button_col = st.columns([4, 1])

with map_col:
    st.subheader("📍 Select Your Hunting Location")
    map_data = st_folium(m, width=700, height=500)

with button_col:
    st.subheader("🎯 Action")
    
    # Show selected location info when available
    if map_data and map_data["last_clicked"]:
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        
        st.success("📍 **Location Selected**")
        st.write(f"**Lat:** {lat:.4f}")
        st.write(f"**Lon:** {lon:.4f}")
        
        # Initialize session state for prediction
        if 'prediction' not in st.session_state:
            st.session_state.prediction = None

        if st.button("🎯 Get Prediction", type="primary", use_container_width=True):
            with st.spinner("🔍 Analyzing hunting conditions..."):
                try:
                    iso_datetime = f"{date.isoformat()}T{time.isoformat()}"
                    payload = {
                        "lat": lat,
                        "lon": lon,
                        "date_time": iso_datetime,
                        "season": season.lower().replace(" ", "_"),
                        "suggestion_threshold": suggestion_threshold,
                        "min_suggestion_rating": min_suggestion_rating
                    }
                    
                    response = requests.post(f"{BACKEND_URL}/predict", json=payload, timeout=60)
                    response.raise_for_status()
                    
                    # Store the entire prediction in session state
                    st.session_state.prediction = response.json()
                    st.success("✅ Prediction Complete!")

                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Backend Error: {e}")
                    st.session_state.prediction = None
                except Exception as e:
                    st.error(f"❌ Unexpected Error: {e}")
                    st.session_state.prediction = None
    else:
        st.info("👆 Click on the map to select a hunting location, then click Get Prediction")

# Display prediction results if available
if 'prediction' in st.session_state and st.session_state.prediction:
    prediction = st.session_state.prediction
    
    st.markdown("---")
    st.markdown("## 🎯 **Hunting Prediction Results**")
    
    # Key metrics in columns
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("🏹 Stand Rating", f"{prediction['stand_rating']}/10")
    
    with metric_col2:
        # Show season info
        st.metric("🍂 Season", season)
    
    with metric_col3:
        # Show date/time
        st.metric("📅 Date", date.strftime("%m/%d/%Y"))
    
    with metric_col4:
        # Show time
        st.metric("🕐 Time", time.strftime("%I:%M %p"))

    # --- Interactive Prediction Map (moved up from bottom) ---
    st.markdown("---")
    st.markdown("### 🗺️ **Interactive Prediction Map**")
    st.markdown("*Visual display of all recommended hunting stands, deer activity zones, and access points*")
    
    # Create prediction map with same style as main map
    pred_map = create_map([lat, lon], 14, map_type)
    
    # Add the same overlays to prediction map
    if show_contours:
        contour_layer = folium.raster_layers.WmsTileLayer(
            url="https://basemap.nationalmap.gov/arcgis/services/USGSTopoLarge/MapServer/WMSServer?",
            layers="0",
            transparent=True,
            format="image/png",
            name="Contour Lines",
            control=True
        )
        contour_layer.add_to(pred_map)
    
    if show_terrain_shading:
        hillshade_layer = folium.raster_layers.WmsTileLayer(
            url="https://basemap.nationalmap.gov/arcgis/services/USGSImageryOnly/MapServer/WMSServer?",
            layers="0",
            transparent=True,
            format="image/png",
            name="Terrain Shading",
            control=True,
            opacity=0.6
        )
        hillshade_layer.add_to(pred_map)

    # Add travel corridor markers with walking icons
    if prediction.get('travel_corridors') and prediction['travel_corridors'].get('features'):
        for feature in prediction['travel_corridors']['features']:
            coords = feature['geometry']['coordinates']
            props = feature['properties']
            
            # Use walking/footprint icon for travel corridors
            marker_symbol = 'walking'  # Walking icon for travel areas
            
            folium.Marker(
                [coords[1], coords[0]],  # lat, lon
                popup=folium.Popup(f"🚶 <b>{props.get('description', 'Travel Area')}</b><br>Score: {props.get('score', 'N/A')}<br>Rank: #{props.get('rank', 'N/A')}", max_width=250),
                tooltip=f"🚶 {props.get('description', 'Travel Area')}",
                icon=folium.Icon(
                    color='blue',
                    icon=marker_symbol,
                    prefix='fa'
                )
            ).add_to(pred_map)

    # Add bedding zone markers with correct icons
    if prediction.get('bedding_zones') and prediction['bedding_zones'].get('features'):
        for feature in prediction['bedding_zones']['features']:
            coords = feature['geometry']['coordinates']
            props = feature['properties']
            
            # Use the marker_symbol from backend or fallback to tree
            marker_symbol = props.get('marker_symbol', 'tree')
            
            folium.Marker(
                [coords[1], coords[0]],  # lat, lon
                popup=folium.Popup(f"🛏️ <b>{props.get('description', 'Bedding Area')}</b><br>Score: {props.get('score', 'N/A')}<br>Rank: #{props.get('rank', 'N/A')}", max_width=250),
                tooltip=f"🛏️ {props.get('description', 'Bedding Area')}",
                icon=folium.Icon(
                    color='red',
                    icon=marker_symbol,
                    prefix='fa'
                )
            ).add_to(pred_map)

    # Add feeding zone markers with correct icons
    if prediction.get('feeding_areas') and prediction['feeding_areas'].get('features'):
        for feature in prediction['feeding_areas']['features']:
            coords = feature['geometry']['coordinates']
            props = feature['properties']
            
            # Use the marker_symbol from backend or fallback to leaf
            marker_symbol = props.get('marker_symbol', 'leaf')
            
            folium.Marker(
                [coords[1], coords[0]],  # lat, lon
                popup=folium.Popup(f"🌿 <b>{props.get('description', 'Feeding Area')}</b><br>Score: {props.get('score', 'N/A')}<br>Rank: #{props.get('rank', 'N/A')}", max_width=250),
                tooltip=f"🌿 {props.get('description', 'Feeding Area')}",
                icon=folium.Icon(
                    color='green',
                    icon=marker_symbol,
                    prefix='fa'
                )
            ).add_to(pred_map)
    
    # Add mature buck opportunity markers with crosshair icons
    if prediction.get('mature_buck_opportunities') and prediction['mature_buck_opportunities'].get('features'):
        for feature in prediction['mature_buck_opportunities']['features']:
            coords = feature['geometry']['coordinates']
            props = feature['properties']
            
            # Use crosshair icon for mature buck opportunities
            marker_symbol = 'crosshairs'
            
            # Create detailed popup for mature buck opportunity
            popup_text = f"""
            <b>🏹 {props.get('description', 'Mature Buck Opportunity')}</b><br>
            <b>Confidence:</b> {props.get('confidence', 'N/A')}%<br>
            <b>Rank:</b> #{props.get('rank', 'N/A')}<br>
            <hr>
            <b>🎯 Mature Buck Analysis:</b><br>
            <b>Terrain Score:</b> {props.get('terrain_score', 'N/A'):.1f}%<br>
            <b>Movement Probability:</b> {props.get('movement_probability', 'N/A'):.1f}%<br>
            <b>Pressure Resistance:</b> {props.get('pressure_resistance', 'N/A'):.1f}%<br>
            <b>Escape Routes:</b> {props.get('escape_routes', 'N/A'):.1f}%<br>
            <hr>
            <b>📝 Key Insights:</b><br>
            """
            
            # Add hunting notes if available
            hunting_notes = props.get('hunting_notes', [])
            if hunting_notes:
                for note in hunting_notes:
                    popup_text += f"• {note}<br>"
            
            # Add behavioral notes if available
            behavioral_notes = props.get('behavioral_notes', [])
            if behavioral_notes:
                popup_text += "<b>🦌 Behavior:</b><br>"
                for note in behavioral_notes[:2]:  # Show first 2 behavioral notes
                    popup_text += f"• {note}<br>"
            
            popup_text += "<small><b>🏹 MATURE BUCK TARGET!</b><br>Specialized location for hunting mature whitetails (3.5+ years)</small>"
            
            folium.Marker(
                [coords[1], coords[0]],  # lat, lon
                popup=folium.Popup(popup_text, max_width=400),
                tooltip=f"🏹 {props.get('description', 'Mature Buck Opportunity')}",
                icon=folium.Icon(
                    color='darkred',
                    icon=marker_symbol,
                    prefix='fa'
                )
            ).add_to(pred_map)
    
    # Add high-value scouting points (ONLY show truly exceptional areas worth scouting)
    if prediction.get('suggested_spots') and len(prediction['suggested_spots']) > 0:
        # Filter to only show spots that are worth scouting (7.5+ rating)
        worthy_scouting_spots = [spot for spot in prediction['suggested_spots'] if spot['rating'] >= 7.5]
        
        for i, spot in enumerate(worthy_scouting_spots):
            # These are high-value scouting areas - use binoculars icon
            icon_color = 'purple'  # Distinctive color for scouting
            icon_name = 'binoculars'  # Scouting icon
            activity_emoji = '🔍'  # Scouting emoji
            
            # Create popup text emphasizing this is a high-value scouting area
            popup_text = f"""
            <b>{activity_emoji} HIGH-VALUE SCOUTING AREA #{i+1}</b><br>
            <b>Why Scout Here:</b> {spot['primary_activity']}<br>
            <b>Quality Rating:</b> {spot['rating']}/10 ⭐<br>
            <b>Distance:</b> {spot['distance_km']} km<br>
            <hr>
            <b>Activity Potential:</b><br>
            🚶 Travel: {spot['travel_score']}/10<br>
            🛏️ Bedding: {spot['bedding_score']}/10<br>
            🌿 Feeding: {spot['feeding_score']}/10<br>
            <hr>
            <small><b>🔍 PRIME SCOUTING OPPORTUNITY!</b><br>
            This area shows excellent deer activity potential.<br>
            Worth investigating for future hunts.</small>
            """
            
            # Add marker with scouting icon
            folium.Marker(
                [spot['lat'], spot['lon']],
                popup=folium.Popup(popup_text, max_width=350),
                tooltip=f"{activity_emoji} Prime Scouting: {spot['rating']}/10 ⭐",
                icon=folium.Icon(
                    color=icon_color,
                    icon=icon_name,
                    prefix='fa'
                )
            ).add_to(pred_map)
    
    # Add marker for the original clicked location for reference
    folium.Marker(
        [lat, lon],
        popup=f"📍 Your Selected Location<br>Rating: {prediction['stand_rating']}/10<br><small>Original spot you clicked</small>",
        tooltip=f"📍 Your Selection: {prediction['stand_rating']}/10",
        icon=folium.Icon(color='gray', icon='map-pin', prefix='fa')
    ).add_to(pred_map)
    
    # Add stand recommendation markers
    if prediction.get('stand_recommendations') and len(prediction['stand_recommendations']) > 0:
        for i, rec in enumerate(prediction['stand_recommendations']):
            rec_lat = rec['coordinates']['lat']
            rec_lon = rec['coordinates']['lon']
            
            # Choose hunting-specific colors and icons based on priority
            if rec['priority'] == 'HIGHEST':
                color = 'red'
                icon = 'tree'  # Tree icon for highest priority
                priority_emoji = '�'
            elif rec['priority'] == 'HIGH':
                color = 'orange'
                icon = 'tree'  # Tree icon for high priority
                priority_emoji = '�'
            elif rec['priority'] in ['MEDIUM-HIGH', 'MEDIUM']:
                color = 'green'
                icon = 'tree'  # Good hunting spot in cover
                priority_emoji = '🌲'
            else:
                color = 'lightblue'
                icon = 'tree'  # Tree icon for low priority
                priority_emoji = '�'
            
            popup_text = f"""
            <b>🌲 Hunting Stand Recommendation</b><br>
            <b>Type:</b> {rec['type']}<br>
            <b>Priority:</b> {rec['priority']}<br>
            <b>Distance:</b> {rec['distance']}<br>
            <b>Setup:</b> {rec['setup']}<br>
            <b>Best Times:</b> {rec['best_times']}<br>
            <b>GPS:</b> {rec_lat:.6f}, {rec_lon:.6f}<br>
            <hr>
            <small><b>Strategy:</b> {rec['reason']}</small>
            """
            
            folium.Marker(
                [rec_lat, rec_lon],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{priority_emoji} {rec['type']} Stand ({rec['priority']})",
                icon=folium.Icon(
                    color=color,
                    icon=icon,
                    prefix='fa'
                )
            ).add_to(pred_map)
    
    # Add 5 Best Stand Locations - 🎯 Prime Hunting Spots!
    if prediction.get('five_best_stands') and len(prediction['five_best_stands']) > 0:
        for i, stand in enumerate(prediction['five_best_stands']):
            # Handle both coordinate structures (enhanced vs traditional stands)
            if 'coordinates' in stand:
                stand_lat = stand['coordinates']['lat']
                stand_lon = stand['coordinates']['lon']
            else:
                stand_lat = stand.get('lat', 0)
                stand_lon = stand.get('lon', 0)
            
            # Choose marker style based on confidence and priority with hunting-specific icons
            if stand['confidence'] > 85:
                color = 'red'  # Highest confidence - prime spot
                icon_name = 'bullseye'
                confidence_emoji = '🎯'
            elif stand['confidence'] > 75:
                color = 'orange'  # High confidence - excellent spot
                icon_name = 'crosshairs' 
                confidence_emoji = '🏹'
            elif stand['confidence'] > 65:
                color = 'green'  # Good confidence - solid spot
                icon_name = 'tree'
                confidence_emoji = '🌲'
            else:
                color = 'blue'  # Lower confidence - but still a hunting spot
                icon_name = 'map-marker'  # Simple hunting marker instead of binoculars
                confidence_emoji = '�'
            
            # Create detailed popup for stand information with zone references
            popup_text = f"""
            <b>{confidence_emoji} HUNTING STAND #{i+1}</b><br>
            <b>Type:</b> {stand['type']}<br>
            <hr>
            <b>📍 GPS:</b> {stand_lat:.6f}, {stand_lon:.6f}<br>
            <b>📏 Distance:</b> {stand['distance_yards']} yards {stand['direction']}<br>
            <b>🎯 Confidence:</b> {stand['confidence']:.0f}%<br>
            <b>💨 Wind Favorability:</b> {stand['wind_favorability']:.0f}%<br>
            <b>⭐ Priority:</b> {stand['priority']}<br>
            <hr>
            <b>🎯 Why This Spot:</b><br>
            <small>Look at the map zones around this stand:</small><br>
            <small>🛏️ <b>Red zones</b> = Deer bedding areas</small><br>
            <small>🌿 <b>Green zones</b> = Deer feeding areas</small><br>
            <small>🚶 <b>Blue dashed lines</b> = Travel routes</small><br>
            <hr>
            <b>🪜 Setup Strategy:</b><br>
            <small>{stand['setup_notes']}</small><br>
            <hr>
            <small><b>{confidence_emoji} PRIME HUNTING SPOT!</b> Position between the colored zones you see on the map.</small>
            """
            
            # Add the hunting stand marker for each location
            folium.Marker(
                [stand_lat, stand_lon],
                popup=folium.Popup(popup_text, max_width=350),
                tooltip=f"{confidence_emoji} STAND #{i+1}: {stand['type']} ({stand['confidence']:.0f}%)",
                icon=folium.Icon(
                    color=color,
                    icon=icon_name,
                    prefix='fa'
                )
            ).add_to(pred_map)
    
    # Add unique access point markers (separate from stands)
    if prediction.get('five_best_stands') and len(prediction['five_best_stands']) > 0:
        # Get unique access points from the first stand (all stands share the same unique_access_points)
        unique_access_points = prediction['five_best_stands'][0].get('unique_access_points', [])
        
        for access_point in unique_access_points:
            # Create comprehensive access point popup
            stands_served = ', '.join([f"#{stand_id}" for stand_id in access_point['serves_stands']])
            access_popup_text = f"""
            <b>🚗 PARKING & ACCESS POINT</b><br>
            <b>Road Type:</b> {access_point['access_type']}<br>
            <b>Drive Time:</b> {access_point['estimated_drive_time']}<br>
            <b>Distance to Road:</b> {access_point['distance_miles']} miles<br>
            <hr>
            <b>📍 GPS Coordinates:</b> {access_point['lat']:.6f}, {access_point['lon']:.6f}<br>
            <b>🎯 Serves Stands:</b> {stands_served}<br>
            <hr>
            <small><b>📍 Park here and walk to your hunting stands!</b><br>
            <i>This parking location provides access to multiple stand options</i></small>
            """
            
            # Add unique access point marker
            folium.Marker(
                [access_point['lat'], access_point['lon']],
                popup=folium.Popup(access_popup_text, max_width=350),
                tooltip=f"🚗 PARKING: {access_point['access_type']} (Stands {stands_served})",
                icon=folium.Icon(
                    color='darkblue',
                    icon='car',
                    prefix='fa'
                )
            ).add_to(pred_map)
    
    # Add comprehensive legend for all map markers with enhanced zone explanations
    if (prediction.get('suggested_spots') and len(prediction['suggested_spots']) > 0) or \
       (prediction.get('five_best_stands') and len(prediction['five_best_stands']) > 0) or \
       (prediction.get('bedding_zones') and prediction['bedding_zones'].get('features')) or \
       (prediction.get('feeding_areas') and prediction['feeding_areas'].get('features')) or \
       (prediction.get('mature_buck_opportunities') and prediction['mature_buck_opportunities'].get('features')):
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 320px; height: 450px; 
                    background-color: white; border:3px solid #2E7D32; z-index:9999; 
                    font-size:12px; padding: 12px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
        <p style="margin:0; font-weight:bold; font-size:14px; color:#2E7D32;">🗺️ HUNTING MAP GUIDE</p>
        <hr style="margin: 8px 0; border-color:#2E7D32;">
        
        <p style="margin:5px 0; font-weight:bold; color:#CC0000;">🦌 DEER ACTIVITY ZONES:</p>
        <p style="margin:3px 0;"><span style="color:#FF4444;">🛏️ <b>Red Zones</b></span> = Bedding Areas<br>
        <small>Where deer rest during the day</small></p>
        <p style="margin:3px 0;"><span style="color:#44AA44;">🌿 <b>Green Zones</b></span> = Feeding Areas<br>
        <small>Food sources (crops, mast, browse)</small></p>
        <p style="margin:3px 0;"><span style="color:#0066CC;">🚶 <b>Blue Zones</b></span> = Travel Routes<br>
        <small>Paths between bedding & feeding</small></p>
        
        <hr style="margin: 8px 0;">
        <p style="margin:5px 0; font-weight:bold; color:#8B0000;">🏹 MATURE BUCK TARGETS:</p>
        <p style="margin:3px 0;"><span style="color:#8B0000;">🎯 <b>Dark Red Crosshairs</b></span> = Mature Buck Opportunities<br>
        <small>Specialized locations for 3.5+ year bucks</small></p>
        
        <hr style="margin: 8px 0;">
        <p style="margin:5px 0; font-weight:bold; color:#CC6600;">⭐ HUNTING STANDS:</p>
        <p style="margin:2px 0;"><i class="fa fa-bullseye" style="color:red"></i> 🎯 Prime Spots (85%+ confidence)</p>
        <p style="margin:2px 0;"><i class="fa fa-crosshairs" style="color:orange"></i> 🏹 Excellent Spots (75-84%)</p>
        <p style="margin:2px 0;"><i class="fa fa-tree" style="color:green"></i> 🌲 Good Spots (65-74%)</p>
        <p style="margin:2px 0;"><i class="fa fa-map-marker" style="color:blue"></i> � Basic Spots (<65%)</p>
        
        <hr style="margin: 8px 0;">
        <p style="margin:5px 0; font-weight:bold; color:#1a472a;">🚗 PARKING & ACCESS:</p>
        <p style="margin:2px 0;"><i class="fa fa-car" style="color:darkblue"></i> 🚗 Road Access/Parking (1-2 locations for all stands)</p>
        <p style="margin:2px 0;"><i class="fa fa-map-pin" style="color:gray"></i> 📍 Your Selected Location</p>
        
        <div style="background-color:#E8F5E8; padding:6px; margin-top:8px; border-radius:4px; border-left:3px solid #2E7D32;">
        <small><b>💡 HOW TO USE:</b><br>
        Position your stands between the colored zones! Look for stands near the edges of red bedding zones that have good access to green feeding areas.</small>
        </div>
        </div>
        '''
        pred_map.get_root().html.add_child(folium.Element(legend_html))
    
    # Add the layer control to the map
    folium.LayerControl().add_to(pred_map)

    # Display the interactive map
    st_folium(pred_map, width=700, height=500, key=f"pred_map_{lat}_{lon}")

    # === COMPREHENSIVE MATURE BUCK HUNTING ANALYSIS ===
    st.markdown("---")
    st.markdown("# 🦌 **Mature Buck Hunting Strategy**")
    st.markdown("*Comprehensive analysis focused on targeting trophy-class bucks (3.5+ years)*")
    
    # Get mature buck data from prediction
    mature_buck_data = prediction.get('mature_buck_analysis', {})
    
    if mature_buck_data:
        # === MATURE BUCK TERRAIN ASSESSMENT ===
        terrain_scores = mature_buck_data.get('terrain_scores', {})
        st.markdown("## �️ **Terrain Suitability for Mature Bucks**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            overall_score = terrain_scores.get('overall_suitability', 0)
            if overall_score >= 80:
                st.metric("🎯 Overall Suitability", f"{overall_score:.0f}%", delta="EXCELLENT", delta_color="normal")
            elif overall_score >= 65:
                st.metric("🎯 Overall Suitability", f"{overall_score:.0f}%", delta="GOOD", delta_color="normal")
            elif overall_score >= 50:
                st.metric("🎯 Overall Suitability", f"{overall_score:.0f}%", delta="FAIR", delta_color="normal")
            else:
                st.metric("🎯 Overall Suitability", f"{overall_score:.0f}%", delta="POOR", delta_color="inverse")
        
        with col2:
            pressure_resistance = terrain_scores.get('pressure_resistance', 0)
            st.metric("🛡️ Pressure Resistance", f"{pressure_resistance:.0f}%")
            
        with col3:
            escape_routes = terrain_scores.get('escape_route_quality', 0)
            st.metric("🏃 Escape Routes", f"{escape_routes:.0f}%")
            
        with col4:
            security_cover = terrain_scores.get('security_cover', 0)
            st.metric("🌲 Security Cover", f"{security_cover:.0f}%")
        
        # === MATURE BUCK MOVEMENT PREDICTION ===
        movement_data = mature_buck_data.get('movement_prediction', {})
        if movement_data:
            st.markdown("## 🚶 **Mature Buck Movement Patterns**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                movement_prob = movement_data.get('movement_probability', 0)
                confidence_score = movement_data.get('confidence_score', 0)
                
                if movement_prob >= 75:
                    st.success(f"🟢 **HIGH Movement Probability: {movement_prob:.0f}%**")
                elif movement_prob >= 50:
                    st.info(f"🟡 **MODERATE Movement Probability: {movement_prob:.0f}%**")
                else:
                    st.warning(f"🔴 **LOW Movement Probability: {movement_prob:.0f}%**")
                
                st.metric("📊 Prediction Confidence", f"{confidence_score:.0f}%")
            
            with col2:
                behavioral_notes = movement_data.get('behavioral_notes', [])
                if behavioral_notes:
                    st.markdown("**🧠 Key Behavioral Insights:**")
                    for note in behavioral_notes[:3]:
                        st.markdown(f"• {note}")
        
        # === SPECIALIZED MATURE BUCK STAND RECOMMENDATIONS ===
        stand_recommendations = mature_buck_data.get('stand_recommendations', [])
        if stand_recommendations:
            st.markdown("## � **Specialized Mature Buck Stand Locations**")
            st.markdown("*These stands are optimized specifically for mature buck behavior patterns*")
            
            for i, rec in enumerate(stand_recommendations, 1):
                with st.expander(f"🦌 **STAND #{i}: {rec.get('type', 'Unknown')}** - Confidence: {rec.get('confidence', 0):.0f}%", expanded=i==1):
                    
                    # Stand coordinates and basic info
                    coords = rec.get('coordinates', {})
                    stand_lat = coords.get('lat', 0)
                    stand_lon = coords.get('lon', 0)
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**📍 GPS Coordinates:** `{stand_lat:.6f}, {stand_lon:.6f}`")
                        st.markdown(f"**📝 Strategy:** {rec.get('description', 'N/A')}")
                        st.markdown(f"**⏰ Best Times:** {rec.get('best_times', 'N/A')}")
                        
                        # Wind analysis if available
                        if rec.get('wind_optimized'):
                            wind_notes = rec.get('wind_notes', [])
                            if wind_notes:
                                st.markdown("**🌬️ Wind Considerations:**")
                                for note in wind_notes:
                                    st.markdown(f"  • {note}")
                        
                        # Proximity analysis
                        proximity_analysis = rec.get('proximity_analysis', {})
                        if proximity_analysis:
                            bedding_prox = proximity_analysis.get('bedding_proximity', {})
                            feeding_prox = proximity_analysis.get('feeding_proximity', {})
                            
                            if bedding_prox or feeding_prox:
                                st.markdown("**🎯 Zone Proximity Analysis:**")
                                if bedding_prox:
                                    closest_bedding = bedding_prox.get('closest_distance_yards', 0)
                                    st.markdown(f"  • �️ Closest bedding: {closest_bedding:.0f} yards")
                                if feeding_prox:
                                    closest_feeding = feeding_prox.get('closest_distance_yards', 0)
                                    if closest_feeding is not None:
                                        st.markdown(f"  • 🌾 Closest feeding: {closest_feeding:.0f} yards")
                    
                    with col2:
                        # Confidence visualization
                        confidence = rec.get('confidence', 0)
                        if confidence >= 85:
                            st.success(f"🎯 {confidence:.0f}% Confidence\n**PRIME LOCATION**")
                        elif confidence >= 70:
                            st.info(f"✅ {confidence:.0f}% Confidence\n**SOLID CHOICE**")
                        else:
                            st.warning(f"⚠️ {confidence:.0f}% Confidence\n**BACKUP OPTION**")
                        
                        # Pressure resistance
                        pressure_resistance = rec.get('pressure_resistance', 0)
                        if pressure_resistance >= 70:
                            st.metric("🛡️ Pressure Resistance", f"{pressure_resistance:.0f}%", delta="HIGH")
                        else:
                            st.metric("�️ Pressure Resistance", f"{pressure_resistance:.0f}%")
                    
                    # Setup requirements
                    setup_reqs = rec.get('setup_requirements', [])
                    if setup_reqs:
                        st.markdown("**🪜 Setup Requirements:**")
                        for req in setup_reqs:
                            st.markdown(f"  • {req}")
    
    # === HUNT TIMING RECOMMENDATIONS ===
    st.markdown("## ⏰ **Optimal Hunt Timing**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌅 **Best Hunt Windows**")
        schedule = prediction.get('hunt_schedule', [])
        if schedule:
            # Show top 3 hunt windows
            def best_score(entry):
                stands = entry.get('huntable', [])
                return stands[0]['score'] if stands else 0
            ranked_hours = sorted(schedule, key=best_score, reverse=True)[:3]
            
            for item in ranked_hours[:3]:
                hour = item.get('hour')
                when = item.get('time', f"Hour {hour:02d}")
                stands = item.get('huntable', [])
                if stands:
                    top = stands[0]
                    st.markdown(f"**{when}** - Score: {top['score']} | Wind: {top.get('combined_wind_thermal', 0)}%")
        else:
            st.info("Hunt timing analysis will appear after prediction")
    
    with col2:
        st.markdown("### 🌬️ **Wind Conditions**")
        # Parse wind forecast from notes
        notes = prediction.get('notes', '')
        import re
        wind_pattern = r"🌬️ \*\*Tomorrow's Wind Forecast\*\*:(.*?)(?=\n\n|\n•|\n\*\*|$)"
        wind_match = re.search(wind_pattern, notes, re.DOTALL)
        
        if wind_match:
            wind_info = wind_match.group(1).strip()
            wind_lines = [line.strip() for line in wind_info.split('\n') if line.strip()]
            
            for line in wind_lines[:3]:  # Show top 3 wind details
                if 'Dominant Wind' in line:
                    st.markdown(f"**Primary:** {line.replace('• **Dominant Wind**: ', '')}")
                elif 'Best Morning' in line:
                    st.markdown(f"**🌅 Morning:** {line.replace('• **Best Morning Window**: ', '')}")
                elif 'Best Evening' in line:
                    st.markdown(f"**🌇 Evening:** {line.replace('• **Best Evening Window**: ', '')}")
        else:
            st.info("Wind forecast will appear after prediction")
    
    # === TERRAIN HEATMAPS ===
    st.markdown("## 📊 **Terrain Analysis Heatmaps**")
    
    with st.expander("📖 How to Read These Heatmaps", expanded=False):
        st.markdown("""
        **🔴 Red = High Activity (8-10)** - TARGET THESE AREAS!  
        **🟡 Yellow = Good Activity (6-7)** - Solid backup spots  
        **🔵 Blue = Low Activity (0-5)** - Avoid for mature bucks
        
        **Mature Buck Strategy:**
        - Focus on RED zones in bedding areas (security)
        - Hunt transition zones between bedding and feeding
        - Prioritize escape route corridors (travel map)
        """)
    
    heatmap_col1, heatmap_col2, heatmap_col3 = st.columns(3)
    
    with heatmap_col1:
        st.image(f"data:image/png;base64,{prediction['bedding_score_heatmap']}", caption="�️ Bedding Areas - Primary security zones")
    
    with heatmap_col2:
        st.image(f"data:image/png;base64,{prediction['travel_score_heatmap']}", caption="� Travel Corridors - Escape routes & movement")
    
    with heatmap_col3:
        st.image(f"data:image/png;base64,{prediction['feeding_score_heatmap']}", caption="🌾 Feeding Areas - Secondary targets")

    # === ADDITIONAL NOTES ===
    if prediction.get('notes'):
        st.markdown("## 📝 **Additional Analysis Notes**")
        with st.expander("View Detailed Analysis Notes", expanded=False):
            st.info(prediction['notes'])

    else:
        st.error("Please make a prediction to see mature buck hunting analysis.")
