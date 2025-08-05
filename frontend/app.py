
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json
from datetime import datetime
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
BACKEND_URL = "http://backend:8000"

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
    
    � **Vermont Food Sources:**
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
    
    � **Vermont Hunting Tips**:
    - Focus on elevation transitions (1000-2000 ft)
    - Monitor snow depth for winter yard activation
    - Consider prevailing northwest winds for stand placement
    """)

st.write("**Select a Vermont location, date, and season to predict deer activity with enhanced terrain analysis.**")

# --- Input Widgets ---
col1, col2 = st.columns([3, 1])

with col2:
    st.subheader("Inputs")
    
    # Map Type Selection with descriptions
    map_type = st.selectbox("Map Type", list(MAP_CONFIGS.keys()))
    
    # Show map description
    st.info(MAP_CONFIGS[map_type]["description"])
    
    # Map overlay options
    with st.expander("Map Overlays"):
        show_contours = st.checkbox("Show Contour Lines", value=False, help="Add elevation contour lines to any map type")
        show_terrain_shading = st.checkbox("Show Terrain Shading", value=False, help="Add hillshade overlay for terrain visualization")
    
    # Advanced options
    with st.expander("Advanced Options"):
        st.write("**Better Spot Suggestions**")
        suggestion_threshold = st.slider(
            "Show suggestions when rating is below:", 
            min_value=1.0, max_value=10.0, value=5.0, step=0.5,
            help="Show alternative locations when your selected spot has a rating below this threshold"
        )
        min_suggestion_rating = st.slider(
            "Minimum rating for suggestions:", 
            min_value=5.0, max_value=10.0, value=8.0, step=0.5,
            help="Only suggest locations with ratings above this threshold"
        )
    
    season = st.selectbox("Season", ["Early Season", "Rut", "Late Season"])
    date = st.date_input("Date", datetime.now())
    time = st.time_input("Time", datetime.now().time())
    
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

with col1:
    st.subheader("Map")
    map_data = st_folium(m, width=700, height=500)

# --- Prediction Logic ---
if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    
    st.sidebar.subheader("Selected Location")
    st.sidebar.write(f"Lat: {lat:.4f}, Lon: {lon:.4f}")

    # Initialize session state for prediction
    if 'prediction' not in st.session_state:
        st.session_state.prediction = None

    if st.sidebar.button("Get Prediction"):
        with st.spinner("Fetching and analyzing real-world map data..."):
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

            except requests.exceptions.RequestException as e:
                st.sidebar.error(f"Error connecting to backend: {e}")
                st.session_state.prediction = None # Clear previous prediction on error
            except Exception as e:
                st.sidebar.error(f"An unexpected error occurred: {e}")
                st.session_state.prediction = None # Clear previous prediction on error

    # Display the map and results if a prediction is available in the session state
    if st.session_state.prediction:
        prediction = st.session_state.prediction
        st.sidebar.subheader("Prediction Results")
        st.sidebar.metric("Stand Rating", f"{prediction['stand_rating']}/10")
        
        # Add prominent wind forecast section
        with st.sidebar.expander("🌬️ Tomorrow's Wind Forecast", expanded=True):
            # Parse tomorrow's forecast from the notes or try to get it from prediction data
            notes = prediction.get('notes', '')
            
            # Look for tomorrow's wind info in the notes
            import re
            wind_pattern = r"🌬️ \*\*Tomorrow's Wind Forecast\*\*:(.*?)(?=\n\n|\n•|\n\*\*|$)"
            wind_match = re.search(wind_pattern, notes, re.DOTALL)
            
            if wind_match:
                wind_info = wind_match.group(1).strip()
                # Clean up the markdown formatting for display
                wind_lines = [line.strip() for line in wind_info.split('\n') if line.strip()]
                
                for line in wind_lines:
                    if 'Dominant Wind' in line:
                        st.metric("Tomorrow's Wind", line.replace('• **Dominant Wind**: ', ''))
                    elif 'Best Morning Window' in line:
                        st.write(f"🌅 **Morning**: {line.replace('• **Best Morning Window**: ', '')}")
                    elif 'Best Evening Window' in line:
                        st.write(f"🌇 **Evening**: {line.replace('• **Best Evening Window**: ', '')}")
                    elif 'Wind Advice' in line:
                        advice = line.replace('• **Wind Advice**: ', '')
                        if 'excellent' in advice.lower():
                            st.success(f"💨 {advice}")
                        elif 'strong' in advice.lower() or 'postpone' in advice.lower():
                            st.error(f"💨 {advice}")
                        else:
                            st.info(f"💨 {advice}")
                    elif 'Excellent all-day' in line:
                        st.success("✅ Excellent all-day hunting conditions!")
                    elif 'Strong winds expected' in line:
                        st.warning("⚠️ Strong winds expected - adjust strategy!")
            else:
                st.info("Wind forecast data will appear here after making a prediction")
        
        # Add 5 Best Stand Locations section
        if prediction.get('five_best_stands') and len(prediction['five_best_stands']) > 0:
            with st.sidebar.expander("⭐ 5 Best Stand Locations", expanded=True):
                st.markdown("**⭐ marks the spot!** Click star markers on map for details.")
                
                # Show all 5 stands with detailed info
                st.markdown("**🔥 Top 5 Priority Stands:**")
                for i, stand in enumerate(prediction['five_best_stands'], 1):
                    confidence = stand['confidence']
                    if confidence > 85:
                        emoji = "🔥"
                        color = "🔴"
                    elif confidence > 75:
                        emoji = "⭐"
                        color = "🟠"
                    elif confidence > 65:
                        emoji = "✅"
                        color = "🟢"
                    else:
                        emoji = "📍"
                        color = "🔵"
                    
                    st.markdown(f"{emoji} **#{i}. {stand['type']}**")
                    st.markdown(f"   {color} {confidence:.0f}% confidence | {stand['distance_yards']} yds {stand['direction']}")
                    st.markdown(f"   📍 `{stand['coordinates']['lat']}, {stand['coordinates']['lon']}`")
                    
                    # Access route information
                    if 'access_route' in stand:
                        route = stand['access_route']
                        difficulty_colors = {
                            'EASY': '🟢',
                            'MODERATE': '🟡', 
                            'DIFFICULT': '🟠',
                            'VERY_DIFFICULT': '🔴'
                        }
                        color_icon = difficulty_colors.get(route['route_difficulty'], '⚫')
                        st.markdown(f"   🚶 Access: {color_icon} {route['route_difficulty']} ({route['stealth_score']}/100)")
                        
                        # Key access warnings
                        if route['wind_impact']['wind_advantage'] in ['poor', 'very_poor']:
                            st.markdown("   ⚠️ WIND WARNING: Tailwind approach")
                        if route['deer_zones']['bedding_risk'] in ['high', 'very_high']:
                            st.markdown("   🛏️ High bedding risk")
                    
                    st.markdown("---")
                
                st.info("💡 **Tip**: Higher confidence = better deer activity expected")
            
            # Add detailed access route analysis
            with st.sidebar.expander("🚶 Access Route Analysis", expanded=False):
                st.markdown("**Stealth approach planning for each stand**")
                
                for i, stand in enumerate(prediction['five_best_stands'], 1):
                    if 'access_route' in stand:
                        route = stand['access_route']
                        st.markdown(f"**Stand #{i} - {stand['type']}**")
                        
                        # Route summary
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Distance", f"{route['total_distance_yards']} yds")
                            st.metric("Stealth Score", f"{route['stealth_score']}/100")
                        with col2:
                            st.metric("Bearing", f"{route['direct_bearing']}°")
                            st.metric("Difficulty", route['route_difficulty'])
                        
                        # Key recommendations
                        if route['recommendations']:
                            st.markdown("**🎯 Key Recommendations:**")
                            for rec in route['recommendations'][:3]:  # Top 3 recommendations
                                st.markdown(f"• {rec}")
                        
                        # Optimal timing
                        if route['approach_timing']:
                            timing = route['approach_timing']
                            st.markdown(f"**⏰ Best Approach Time:** {timing['optimal_time']}")
                        
                        st.markdown("---")
        
        st.sidebar.info(prediction['notes'])

        st.sidebar.subheader("Score Heatmaps")
        
        # Add score interpretation guide
        with st.sidebar.expander("📖 How to Read These Heatmaps"):
            st.markdown("""
            **🔴 Red = High Activity (8-10)** - HUNT HERE!  
            **🟡 Yellow = Good Activity (6-7)** - Solid spots  
            **🔵 Blue = Low Activity (0-5)** - Avoid these areas
            
            **Quick Tips:**
            - Focus on the RED zones in each map
            - Hunt where travel (red) meets feeding (red)
            - Check all three maps together for best spots
            """)
        
        st.sidebar.image(f"data:image/png;base64,{prediction['travel_score_heatmap']}", caption="🚶 Travel Corridors - Where deer move")
        st.sidebar.image(f"data:image/png;base64,{prediction['bedding_score_heatmap']}", caption="🛏️ Bedding Areas - Where deer rest")
        st.sidebar.image(f"data:image/png;base64,{prediction['feeding_score_heatmap']}", caption="🌾 Feeding Areas - Where deer eat")

        # Show suggested better spots if available
        if prediction.get('suggested_spots') and len(prediction['suggested_spots']) > 0:
            st.sidebar.subheader("🎯 Better Hunting Spots Found!")
            st.sidebar.warning(f"Your selected location has a low rating ({prediction['stand_rating']}/10). Check the map for {len(prediction['suggested_spots'])} better alternatives marked with stars!")
            
            with st.sidebar.expander("View Suggested Spots Details"):
                for i, spot in enumerate(prediction['suggested_spots']):
                    st.write(f"**Spot #{i+1}** - Rating: {spot['rating']}/10")
                    st.write(f"📍 {spot['distance_km']} km away")
                    st.write(f"🎯 {spot['primary_activity']}")
                    
                    # Show score breakdown in small text
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Travel", f"{spot['travel_score']}")
                    with col_b:
                        st.metric("Bedding", f"{spot['bedding_score']}")
                    with col_c:
                        st.metric("Feeding", f"{spot['feeding_score']}")
                    
                    st.write("---")
                    
                st.info("💡 Tip: Click on the star markers on the map to see more details about each suggested location!")

        # --- Score Interpretation Guide ---
        st.markdown("---")
        st.markdown("### 📊 **Understanding Your Deer Activity Predictions**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 🔴 **Excellent (8-10)**
            **HUNT THESE AREAS!**
            - Prime deer activity
            - High success probability
            - Focus your hunting time here
            """)
            
        with col2:
            st.markdown("""
            #### 🟡 **Good (6-7)**
            **Solid Backup Options**
            - Moderate deer activity
            - Worth hunting if reds are busy
            - Good secondary spots
            """)
            
        with col3:
            st.markdown("""
            #### 🔵 **Low (0-5)**
            **Avoid These Areas**
            - Poor deer activity
            - Walk through to reach reds
            - Don't waste hunting time
            """)
        
        # Current location rating with advice
        st.markdown("---")
        current_rating = prediction['stand_rating']
        if current_rating >= 8:
            st.success(f"🎯 **Your Selected Location: {current_rating}/10** - Excellent choice! This is a prime hunting area.")
        elif current_rating >= 6:
            st.info(f"✅ **Your Selected Location: {current_rating}/10** - Good hunting potential. Solid choice for this season.")
        elif current_rating >= 4:
            st.warning(f"⚠️ **Your Selected Location: {current_rating}/10** - Moderate potential. Consider the better spots marked on the map.")
        else:
            st.error(f"❌ **Your Selected Location: {current_rating}/10** - Low potential. Definitely check the better alternatives marked on the map!")

        # --- Access Route Analysis ---
        if prediction.get('five_best_stands') and len(prediction['five_best_stands']) > 0:
            # Check if any stands have access route data
            has_access_routes = any('access_route' in stand for stand in prediction['five_best_stands'])
            
            if has_access_routes:
                st.markdown("---")
                st.markdown("### 🚶 **Access Route Analysis**")
                st.markdown("*Critical stealth approach planning - the most important hunting factor*")
                
                # Overall access difficulty summary
                route_difficulties = []
                critical_warnings = []
                
                for stand in prediction['five_best_stands']:
                    if 'access_route' in stand:
                        route = stand['access_route']
                        route_difficulties.append(route['route_difficulty'])
                        
                        # Collect critical warnings
                        if route['wind_impact']['wind_advantage'] in ['poor', 'very_poor']:
                            critical_warnings.append(f"Stand #{prediction['five_best_stands'].index(stand)+1}: TAILWIND APPROACH")
                        if route['deer_zones']['bedding_risk'] in ['high', 'very_high']:
                            critical_warnings.append(f"Stand #{prediction['five_best_stands'].index(stand)+1}: HIGH BEDDING DISTURBANCE RISK")
                
                # Show critical warnings prominently
                if critical_warnings:
                    st.error("⚠️ **CRITICAL ACCESS WARNINGS:**")
                    for warning in critical_warnings[:3]:  # Show top 3 warnings
                        st.markdown(f"• {warning}")
                    st.markdown("*Review detailed recommendations below*")
                
                # Detailed analysis for each stand
                st.markdown("**🎯 Detailed Access Analysis by Stand:**")
                
                for i, stand in enumerate(prediction['five_best_stands'], 1):
                    if 'access_route' in stand:
                        route = stand['access_route']
                        
                        with st.expander(f"🚶 Stand #{i} Access Route - {stand['type']} ({route['route_difficulty']})", expanded=(i <= 2)):
                            
                            # Route metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("🎯 Stealth Score", f"{route['stealth_score']}/100")
                            with col2:
                                st.metric("📏 Distance", f"{route['total_distance_yards']} yds")
                            with col3:
                                st.metric("🧭 Bearing", f"{route['direct_bearing']}°")
                            with col4:
                                difficulty_colors = {
                                    'EASY': '🟢 EASY',
                                    'MODERATE': '🟡 MODERATE', 
                                    'DIFFICULT': '🟠 DIFFICULT',
                                    'VERY_DIFFICULT': '🔴 VERY DIFFICULT'
                                }
                                st.metric("🚶 Difficulty", difficulty_colors.get(route['route_difficulty'], route['route_difficulty']))
                            
                            # Wind and thermal analysis
                            wind_info = route['wind_impact']
                            st.markdown("**🌬️ Wind & Thermal Analysis:**")
                            
                            wind_color = "🔴" if wind_info['wind_advantage'] in ['poor', 'very_poor'] else "🟢" if wind_info['wind_advantage'] == 'excellent' else "🟡"
                            st.markdown(f"• Wind Status: {wind_color} {wind_info['wind_status'].title()} ({wind_info['wind_advantage']})")
                            
                            if route.get('approach_timing', {}).get('thermal_consideration', 'None') != 'None':
                                thermal_color = "🟢" if wind_info['thermal_impact'] == 'favorable' else "🔴" if wind_info['thermal_impact'] == 'unfavorable' else "🟡"
                                st.markdown(f"• Thermal Impact: {thermal_color} {wind_info['thermal_impact'].title()}")
                            
                            # Terrain and deer zone risks
                            terrain = route['terrain_analysis']
                            deer_zones = route['deer_zones']
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**🏔️ Terrain Factors:**")
                                st.markdown(f"• Cover Quality: {terrain['cover_quality'].title()}")
                                st.markdown(f"• Noise Level: {terrain['noise_level'].title()}")
                                if terrain['is_steep']:
                                    st.markdown("• ⛰️ Steep terrain - extra caution")
                            
                            with col2:
                                st.markdown("**🦌 Deer Disturbance Risk:**")
                                bedding_color = "🔴" if deer_zones['bedding_risk'] in ['high', 'very_high'] else "🟡" if deer_zones['bedding_risk'] == 'moderate' else "🟢"
                                st.markdown(f"• Bedding Risk: {bedding_color} {deer_zones['bedding_risk'].title()}")
                                
                                feeding_color = "🔴" if deer_zones['feeding_risk'] in ['high', 'very_high'] else "🟡" if deer_zones['feeding_risk'] == 'moderate' else "🟢"
                                st.markdown(f"• Feeding Risk: {feeding_color} {deer_zones['feeding_risk'].title()}")
                            
                            # Key recommendations
                            if route['recommendations']:
                                st.markdown("**🎯 Critical Recommendations:**")
                                for rec in route['recommendations']:
                                    st.markdown(f"• {rec}")
                            
                            # Optimal timing
                            if route['approach_timing']:
                                timing = route['approach_timing']
                                st.markdown(f"**⏰ Optimal Approach Time:** {timing['optimal_time']}")
                                st.markdown(f"**💡 Timing Notes:** {timing['timing_notes']}")
                
                # General access tips
                st.info("""
                **🎯 General Access Tips:**
                • Always approach into the wind when possible
                • Use terrain features for concealment
                • Move slowly and deliberately
                • Avoid deer bedding areas during rest periods
                • Time your approach based on thermal patterns
                """)

        # --- Stand Placement Recommendations ---
        if prediction.get('stand_recommendations') and len(prediction['stand_recommendations']) > 0:
            st.markdown("---")
            st.markdown("### 🏹 **Stand Placement Recommendations**")
            st.markdown("*GPS coordinates and setup instructions for optimal stand locations*")
            
            for i, rec in enumerate(prediction['stand_recommendations']):
                with st.expander(f"🎯 {rec['type']} - {rec['priority']} Priority"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**📍 GPS Coordinates:** `{rec['coordinates']['lat']}, {rec['coordinates']['lon']}`")
                        st.markdown(f"**📏 Location:** {rec['distance']}")
                        st.markdown(f"**🎯 Why This Spot:** {rec['reason']}")
                        st.markdown(f"**🪜 Stand Setup:** {rec['setup']}")
                        st.markdown(f"**🕐 Best Times:** {rec['best_times']}")
                        st.markdown(f"**🚶 Approach:** {rec['approach']}")
                    
                    with col2:
                        # Create a confidence meter
                        confidence = rec.get('confidence', 70)
                        if confidence >= 90:
                            st.success(f"🎯 {confidence}% Confidence")
                        elif confidence >= 75:
                            st.info(f"✅ {confidence}% Confidence") 
                        elif confidence >= 60:
                            st.warning(f"⚠️ {confidence}% Confidence")
                        else:
                            st.error(f"🔍 {confidence}% Confidence")
                        
                        # Priority badge
                        priority = rec['priority']
                        if priority == 'HIGHEST':
                            st.markdown("🥇 **TOP CHOICE**")
                        elif priority == 'HIGH':
                            st.markdown("🥈 **EXCELLENT**")
                        elif priority == 'MEDIUM-HIGH':
                            st.markdown("🥉 **VERY GOOD**")
                        elif priority == 'MEDIUM':
                            st.markdown("⭐ **GOOD**")
                        else:
                            st.markdown("🔍 **SCOUTING**")
            
            # Add copy-to-clipboard functionality for GPS coordinates
            st.markdown("#### 📱 GPS Coordinates for Your Device:")
            gps_text = ""
            for i, rec in enumerate(prediction['stand_recommendations'][:3], 1):  # Top 3 only
                gps_text += f"{i}. {rec['type']}: {rec['coordinates']['lat']}, {rec['coordinates']['lon']}\n"
            
            if gps_text:
                st.text_area("Copy these coordinates to your GPS app:", gps_text, height=100)
                st.info("💡 **Tip:** Copy these coordinates and paste them into your hunting GPS app, Google Maps, or OnX Hunt for navigation to your stand locations.")
        
        else:
            st.markdown("---")
            st.info("🔍 No specific stand recommendations available for this location. Try selecting a spot with terrain features like saddles, ridges, or forest edges.")

        # --- Display Predictions on Map ---
        st.markdown("### 🗺️ **Interactive Prediction Map**")
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

        # Add travel corridors
        if prediction.get('travel_corridors') and prediction['travel_corridors'].get('features'):
            folium.GeoJson(
                prediction['travel_corridors'],
                style_function=lambda x: {'color': 'blue', 'weight': 3, 'opacity': 0.7},
                name="Travel Corridors",
                show=True
            ).add_to(pred_map)

        # Add bedding zones
        if prediction.get('bedding_zones') and prediction['bedding_zones'].get('features'):
            folium.GeoJson(
                prediction['bedding_zones'],
                style_function=lambda x: {'fillColor': 'red', 'color': 'red', 'weight': 2, 'fillOpacity': 0.4},
                name="Bedding Zones",
                show=True
            ).add_to(pred_map)

        # Add feeding zones
        if prediction.get('feeding_areas') and prediction['feeding_areas'].get('features'):
            folium.GeoJson(
                prediction['feeding_areas'],
                style_function=lambda x: {'fillColor': 'green', 'color': 'green', 'weight': 2, 'fillOpacity': 0.4},
                name="Feeding Areas",
                show=True
            ).add_to(pred_map)
        
        # Add suggested better spots if rating is low
        if prediction.get('suggested_spots') and len(prediction['suggested_spots']) > 0:
            for i, spot in enumerate(prediction['suggested_spots']):
                # Choose icon color based on primary activity
                if spot['primary_activity'] == "Travel Corridor":
                    icon_color = 'blue'
                elif spot['primary_activity'] == "Bedding Area":
                    icon_color = 'red'
                elif spot['primary_activity'] == "Feeding Area":
                    icon_color = 'green'
                else:
                    icon_color = 'orange'
                
                # Create popup text with detailed information
                popup_text = f"""
                <b>Better Hunting Spot #{i+1}</b><br>
                <b>Rating:</b> {spot['rating']}/10<br>
                <b>Distance:</b> {spot['distance_km']} km<br>
                <b>Primary Activity:</b> {spot['primary_activity']}<br>
                <hr>
                <b>Detailed Scores:</b><br>
                Travel: {spot['travel_score']}/10<br>
                Bedding: {spot['bedding_score']}/10<br>
                Feeding: {spot['feeding_score']}/10<br>
                <hr>
                <small>Click here to center map on this location</small>
                """
                
                # Add marker with custom icon
                folium.Marker(
                    [spot['lat'], spot['lon']],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"Better Spot: {spot['rating']}/10 ({spot['distance_km']}km)",
                    icon=folium.Icon(
                        color=icon_color,
                        icon='star'
                    )
                ).add_to(pred_map)
        
        # Add marker for the original clicked location for reference
        folium.Marker(
            [lat, lon],
            popup=f"Selected Location<br>Rating: {prediction['stand_rating']}/10",
            tooltip=f"Your Selection: {prediction['stand_rating']}/10",
            icon=folium.Icon(color='gray', icon='info-sign')
        ).add_to(pred_map)
        
        # Add stand recommendation markers
        if prediction.get('stand_recommendations') and len(prediction['stand_recommendations']) > 0:
            for i, rec in enumerate(prediction['stand_recommendations']):
                rec_lat = rec['coordinates']['lat']
                rec_lon = rec['coordinates']['lon']
                
                # Choose color based on priority
                if rec['priority'] == 'HIGHEST':
                    color = 'red'
                    icon = 'bullseye'
                elif rec['priority'] == 'HIGH':
                    color = 'orange'
                    icon = 'crosshairs'
                elif rec['priority'] in ['MEDIUM-HIGH', 'MEDIUM']:
                    color = 'green'
                    icon = 'screenshot'
                else:
                    color = 'lightblue'
                    icon = 'search'
                
                popup_text = f"""
                <b>{rec['type']}</b><br>
                <b>Priority:</b> {rec['priority']}<br>
                <b>Distance:</b> {rec['distance']}<br>
                <b>Setup:</b> {rec['setup']}<br>
                <b>Best Times:</b> {rec['best_times']}<br>
                <b>GPS:</b> {rec_lat}, {rec_lon}<br>
                <small>{rec['reason']}</small>
                """
                
                folium.Marker(
                    [rec_lat, rec_lon],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"🏹 {rec['type']} ({rec['priority']})",
                    icon=folium.Icon(
                        color=color,
                        icon=icon
                    )
                ).add_to(pred_map)
        
        # Add 5 Best Stand Locations - ⭐ Marks the Spot!
        if prediction.get('five_best_stands') and len(prediction['five_best_stands']) > 0:
            for i, stand in enumerate(prediction['five_best_stands']):
                stand_lat = stand['coordinates']['lat']
                stand_lon = stand['coordinates']['lon']
                
                # Choose marker style based on confidence and priority
                if stand['confidence'] > 85:
                    color = 'red'  # Highest confidence - bright red X
                    icon_color = 'white'
                elif stand['confidence'] > 75:
                    color = 'orange'  # High confidence - orange X
                    icon_color = 'white'
                elif stand['confidence'] > 65:
                    color = 'green'  # Good confidence - green X
                    icon_color = 'white'
                else:
                    color = 'blue'  # Lower confidence - blue X
                    icon_color = 'white'
                
                # Create detailed popup for stand information
                popup_text = f"""
                <b>🎯 Stand #{i+1}: {stand['type']}</b><br>
                <hr>
                <b>📍 GPS:</b> {stand_lat}, {stand_lon}<br>
                <b>📏 Distance:</b> {stand['distance_yards']} yards {stand['direction']}<br>
                <b>🎯 Confidence:</b> {stand['confidence']:.0f}%<br>
                <b>💨 Wind Favorability:</b> {stand['wind_favorability']:.0f}%<br>
                <b>⭐ Priority:</b> {stand['priority']}<br>
                <hr>
                <b>🪜 Setup Notes:</b><br>
                <small>{stand['setup_notes']}</small><br>
                <hr>
                <small><b>⭐ marks the spot!</b> Click to center map here.</small>
                """
                
                # Add the X marker for each stand location
                folium.Marker(
                    [stand_lat, stand_lon],
                    popup=folium.Popup(popup_text, max_width=350),
                    tooltip=f"⭐ Stand #{i+1}: {stand['type']} ({stand['confidence']:.0f}%)",
                    icon=folium.Icon(
                        color=color,
                        icon='star',  # Use star icon instead of X for better visibility
                        icon_color=icon_color,
                        prefix='fa'
                    )
                ).add_to(pred_map)
        
        # Add comprehensive legend for all map markers
        if (prediction.get('suggested_spots') and len(prediction['suggested_spots']) > 0) or \
           (prediction.get('five_best_stands') and len(prediction['five_best_stands']) > 0):
            legend_html = '''
            <div style="position: fixed; 
                        top: 10px; right: 10px; width: 250px; height: 200px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:12px; padding: 10px; border-radius: 5px;">
            <p><b>🗺️ Map Legend</b></p>
            <hr style="margin: 5px 0;">
            <p><b>🎯 Stand Locations:</b></p>
            <p><i class="fa fa-star" style="color:red"></i> ⭐ Best Stands (85%+ confidence)</p>
            <p><i class="fa fa-star" style="color:orange"></i> ⭐ Good Stands (75-84% confidence)</p>
            <p><i class="fa fa-star" style="color:green"></i> ⭐ Solid Stands (65-74% confidence)</p>
            <p><i class="fa fa-star" style="color:blue"></i> ⭐ Other Stands (<65% confidence)</p>
            <hr style="margin: 5px 0;">
            <p><b>📍 Other Markers:</b></p>
            <p><i class="fa fa-star" style="color:blue"></i> Better Travel Spots</p>
            <p><i class="fa fa-star" style="color:red"></i> Better Bedding Spots</p>
            <p><i class="fa fa-star" style="color:green"></i> Better Feeding Spots</p>
            <p><i class="fa fa-info-circle" style="color:gray"></i> Your Selection</p>
            <small><b>⭐ = Star marks the spot for deer stands!</b></small>
            </div>
            '''
            pred_map.get_root().html.add_child(folium.Element(legend_html))
        
        # Add the layer control to the map
        folium.LayerControl().add_to(pred_map)

        with col1:
            # Use a unique key to ensure the map re-renders when the prediction changes
            st_folium(pred_map, width=700, height=500, key=f"pred_map_{lat}_{lon}")
else:
    st.info("Click on the map to select a location for prediction.")
