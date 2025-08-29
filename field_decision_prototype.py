#!/usr/bin/env python3
"""
Field Decision Widget Prototype
Standalone tool for real-time hunting decisions when conditions change

This prototype will be integrated into the main app once fully tested.
"""

import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

def get_original_prediction(lat: float, lon: float, season: str = "early_season") -> Optional[Dict]:
    """Get original prediction from the main API"""
    try:
        payload = {
            "lat": lat,
            "lon": lon,
            "date_time": datetime.now().isoformat(),
            "season": season
        }
        
        response = requests.post(f"{API_BASE_URL}/predict", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters"""
    import math
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat_rad = math.radians(lat2 - lat1)
    dlon_rad = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(dlat_rad/2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(dlon_rad/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Return distance in meters
    return 6371000 * c  # Earth radius in meters

def analyze_wind_impact(stands: List[Dict], current_wind: str, current_lat: float = None, current_lon: float = None, max_distance: int = 200) -> List[Dict]:
    """Analyze how current wind affects each stand, with distance filtering"""
    
    # Wind direction mappings (degrees)
    wind_directions = {
        "N": 0, "NE": 45, "E": 90, "SE": 135,
        "S": 180, "SW": 225, "W": 270, "NW": 315
    }
    
    # Deer approach directions and optimal winds for each approach
    # Key: deer approach direction, Value: winds that work well for that approach
    optimal_winds_for_approach = {
        "N": ["S", "SW", "SE"],     # Deer from north, need wind from south
        "NE": ["SW", "W", "S"],     # Deer from northeast, need wind from southwest  
        "E": ["W", "NW", "SW"],     # Deer from east, need wind from west
        "SE": ["NW", "N", "W"],     # Deer from southeast, need wind from northwest
        "S": ["N", "NE", "NW"],     # Deer from south, need wind from north
        "SW": ["NE", "E", "N"],     # Deer from southwest, need wind from northeast
        "W": ["E", "SE", "NE"],     # Deer from west, need wind from east
        "NW": ["SE", "S", "E"]      # Deer from northwest, need wind from southeast
    }
    
    enhanced_stands = []
    
    for i, stand in enumerate(stands):
        # Calculate distance from current position if provided
        distance_meters = None
        distance_feasible = True
        
        if current_lat is not None and current_lon is not None:
            stand_lat = stand['coordinates']['lat']
            stand_lon = stand['coordinates']['lon']
            distance_meters = calculate_distance_meters(current_lat, current_lon, stand_lat, stand_lon)
            distance_feasible = distance_meters <= max_distance
        
        # Determine likely deer approach based on stand type
        stand_type = stand.get('type', 'Unknown')
        
        # Assign likely deer approach direction based on stand analysis
        if 'Feeding' in stand_type:
            deer_approach = "NE"  # Coming from bedding (typically N/NE) to feeding
        elif 'Bedding' in stand_type:
            deer_approach = "SW"  # Leaving feeding areas (typically S/SW) to bedding
        elif 'Travel' in stand_type or 'Corridor' in stand_type:
            deer_approach = "NW"  # General travel often NW/SE corridors
        elif 'Pinch' in stand_type or 'Funnel' in stand_type:
            deer_approach = "N"   # Funnels often have north-south movement
        else:
            deer_approach = "NE"  # Default assumption - most common movement
        
        # Check if current wind is good for this deer approach
        good_winds = optimal_winds_for_approach.get(deer_approach, [])
        wind_quality = "EXCELLENT" if current_wind in good_winds else "POOR"
        
        # Adjust confidence based on wind
        original_confidence = stand.get('confidence', 50)
        if wind_quality == "EXCELLENT":
            adjusted_confidence = min(95, original_confidence * 1.15)  # 15% boost
            wind_impact = "✅ GOOD"
        else:
            adjusted_confidence = max(20, original_confidence * 0.75)  # 25% penalty
            wind_impact = "❌ BAD"
        
        # Apply distance penalty if too far
        if distance_meters is not None and not distance_feasible:
            adjusted_confidence *= 0.3  # Major penalty for distant stands
            wind_impact += " 🚫 TOO FAR"
        
        enhanced_stand = {
            **stand,
            'original_confidence': original_confidence,
            'adjusted_confidence': adjusted_confidence,
            'deer_approach_direction': deer_approach,
            'wind_quality': wind_quality,
            'wind_impact': wind_impact,
            'wind_recommendation': f"Wind {current_wind} for deer from {deer_approach}: {wind_quality}",
            'distance_meters': distance_meters,
            'distance_feasible': distance_feasible,
            'distance_rating': "REACHABLE" if distance_feasible else "TOO FAR"
        }
        
        enhanced_stands.append(enhanced_stand)
    
    # Re-sort by adjusted confidence (feasible stands will rank higher due to distance penalty)
    enhanced_stands.sort(key=lambda x: x['adjusted_confidence'], reverse=True)
    
    return enhanced_stands

def display_quick_decision(enhanced_stands: List[Dict], current_wind: str):
    """Display the quick decision interface"""
    
    st.subheader(f"🌬️ Field Decision for Wind: {current_wind}")
    
    # Find best reachable stand
    reachable_stands = [s for s in enhanced_stands if s.get('distance_feasible', True)]
    best_stand = reachable_stands[0] if reachable_stands else enhanced_stands[0]
    
    with st.container():
        st.markdown("### 🎯 **RECOMMENDED ACTION**")
        
        # Check if current position is best
        current_position_good = False
        if enhanced_stands[0].get('distance_meters') is not None:
            current_position_good = enhanced_stands[0]['distance_meters'] < 50  # Within 50m = current position
        
        if best_stand['wind_quality'] == "EXCELLENT" and current_position_good:
            st.success(f"✅ **STAY PUT** - Current position works with {current_wind} wind")
            st.info(f"**Confidence:** {best_stand['adjusted_confidence']:.1f}% (+{best_stand['adjusted_confidence'] - best_stand['original_confidence']:.1f}%)")
        elif best_stand.get('distance_feasible', True):
            distance_m = best_stand.get('distance_meters', 0)
            if distance_m and distance_m > 50:
                st.warning(f"🔄 **MOVE {distance_m:.0f}m** to {best_stand['type']}")
                st.info(f"**New Confidence:** {best_stand['adjusted_confidence']:.1f}% | **Distance:** {distance_m:.0f} meters")
            else:
                st.success(f"✅ **USE** {best_stand['type']}")
                st.info(f"**Confidence:** {best_stand['adjusted_confidence']:.1f}%")
        else:
            st.error("⚠️ **ALL STANDS TOO FAR** - Consider staying put or increasing max distance")
    
    # Distance-filtered recommendations
    st.markdown("### 📊 **Reachable Stand Analysis**")
    
    reachable_count = len(reachable_stands)
    if reachable_count > 0:
        st.success(f"✅ {reachable_count} stands within range")
    else:
        st.warning("⚠️ No stands within range - showing all options")
        reachable_stands = enhanced_stands  # Show all if none reachable
    
    for i, stand in enumerate(reachable_stands[:3]):  # Show top 3 reachable
        distance_m = stand.get('distance_meters')
        distance_text = f" - {distance_m:.0f}m away" if distance_m else ""
        feasible_icon = "✅" if stand.get('distance_feasible', True) else "🚫"
        
        with st.expander(f"{feasible_icon} Stand #{i+1}: {stand['type']}{distance_text} - {stand['wind_impact']}", 
                        expanded=(i == 0)):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Confidence", 
                    f"{stand['adjusted_confidence']:.1f}%",
                    f"{stand['adjusted_confidence'] - stand['original_confidence']:.1f}%"
                )
                
                coords = stand['coordinates']
                st.write(f"**Coordinates:** {coords['lat']:.6f}, {coords['lon']:.6f}")
                
                if distance_m:
                    st.write(f"**Distance:** {distance_m:.0f} meters")
                    st.write(f"**Feasible:** {stand['distance_rating']}")
            
            with col2:
                st.write(f"**Wind Quality:** {stand['wind_quality']}")
                st.write(f"**Deer Approach:** {stand['deer_approach_direction']}")
                st.write(f"**Wind Analysis:** {stand['wind_recommendation']}")
            
            st.write(f"**Setup:** {stand.get('reasoning', 'Terrain analysis based')}")

def main():
    st.set_page_config(
        page_title="🦌 Field Decision Widget",
        page_icon="🌬️",
        layout="wide"
    )
    
    st.title("🌬️ Field Decision Widget")
    st.markdown("**Real-time hunting decisions when wind conditions change**")
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("📍 Hunt Location")
        
        # Location input
        lat = st.number_input("Latitude", value=43.3006, format="%.6f", step=0.000001)
        lon = st.number_input("Longitude", value=-73.2247, format="%.6f", step=0.000001)
        
        season = st.selectbox("Season", ["early_season", "rut", "late_season"], index=0)
        
        st.header("📍 Current Position (Optional)")
        st.markdown("*If you're already at a stand location*")
        
        use_current_position = st.checkbox("I'm at a specific location", value=False)
        current_lat = None
        current_lon = None
        
        if use_current_position:
            current_lat = st.number_input("Current Latitude", value=43.296134, format="%.6f", step=0.000001, key="current_lat")
            current_lon = st.number_input("Current Longitude", value=-73.232192, format="%.6f", step=0.000001, key="current_lon")
            
            # Movement range
            max_distance = st.slider("Maximum movement distance (meters)", 50, 500, 200, 25)
            
            st.info(f"📏 Will only show stands within {max_distance}m")
        else:
            max_distance = 1000  # Default large range if no current position
        
        st.header("🌬️ Current Field Conditions")
        
        # Wind direction selector - BIG BUTTONS for field use
        current_wind = st.radio(
            "Current Wind Direction",
            ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
            horizontal=True,
            help="Wind is coming FROM this direction"
        )
        
        # Action button
        analyze_button = st.button("🎯 Get Field Recommendation", type="primary", use_container_width=True)
    
    # Main content area
    if analyze_button or st.session_state.get('show_results', False):
        with st.spinner("Analyzing current conditions..."):
            
            # Get original prediction
            prediction = get_original_prediction(lat, lon, season)
            
            if prediction:
                st.session_state['show_results'] = True
                
                # Extract stand recommendations
                stands = prediction.get('stand_recommendations', [])
                
                if stands:
                    # Analyze wind impact with distance filtering
                    enhanced_stands = analyze_wind_impact(stands, current_wind, current_lat, current_lon, max_distance)
                    
                    # Display recommendations
                    display_quick_decision(enhanced_stands, current_wind)
                    
                    # Quick GPS coordinates for best reachable stand
                    st.markdown("### 📱 **Quick GPS Coordinates**")
                    reachable_stands = [s for s in enhanced_stands if s.get('distance_feasible', True)]
                    if reachable_stands:
                        best_coords = reachable_stands[0]['coordinates']
                        distance_info = ""
                        if reachable_stands[0].get('distance_meters'):
                            distance_info = f" ({reachable_stands[0]['distance_meters']:.0f}m away)"
                        st.code(f"{best_coords['lat']:.6f}, {best_coords['lon']:.6f}{distance_info}")
                    else:
                        st.warning("No stands within range - increase max distance")
                    
                else:
                    st.error("No stand recommendations available")
            else:
                st.error("Could not get prediction data. Check if the main app is running.")
    
    else:
        # Instructions
        st.markdown("""
        ### 🎯 **How to Use in the Field**
        
        1. **Enter your hunting location** coordinates
        2. **Select current wind direction** (where wind is coming FROM)
        3. **Click "Get Field Recommendation"** for instant analysis
        
        ### 🌬️ **Wind Analysis Features**
        
        - ✅ **Instant stand ranking** based on current wind
        - 🎯 **Clear stay/switch recommendations**
        - 📍 **GPS coordinates** for quick navigation
        - 🦌 **Deer approach direction** analysis
        
        ### 📱 **Mobile Optimized**
        
        - Large buttons for field use
        - Quick access to GPS coordinates
        - Minimal data usage
        """)

if __name__ == "__main__":
    main()
