#!/usr/bin/env python3
"""
Test Frontend Implementation of Deer Approach Fix

This creates a small test version to verify the fix works in the frontend context
before implementing it in the main app.
"""

import streamlit as st
import math
from test_deer_approach_fix import enhanced_deer_approach_calculation

def test_streamlit_integration():
    """Test how the fix would work in Streamlit"""
    
    st.title("🧪 Deer Approach Direction Fix Test")
    st.write("Testing the dynamic deer approach calculation vs. hardcoded SE default")
    
    # Simulate different terrain scenarios
    test_scenarios = {
        "Ridge Travel Corridor": {
            'terrain_features': {
                'terrain_type': 'ridge_top',
                'aspect': 180,
                'slope': 20,
                'elevation': 1500
            },
            'coordinates': {'lat': 44.0, 'lon': -72.0},
            'stand_type': 'Travel Corridor',
            'bedding_zones': {'zones': []}
        },
        "Valley Feeding Area": {
            'terrain_features': {
                'terrain_type': 'valley_agricultural',
                'aspect': 90,
                'slope': 5,
                'elevation': 800,
                'forest_edge': True
            },
            'coordinates': {'lat': 44.1, 'lon': -72.1},
            'stand_type': 'Feeding Area',
            'bedding_zones': {'zones': []}
        },
        "Steep North Slope Bedding": {
            'terrain_features': {
                'terrain_type': 'north_slope',
                'aspect': 360,
                'slope': 25,
                'elevation': 1200
            },
            'coordinates': {'lat': 44.2, 'lon': -72.2},
            'stand_type': 'Bedding Area',
            'bedding_zones': {'zones': []}
        },
        "With Bedding Zone Data": {
            'terrain_features': {'terrain_type': 'mixed'},
            'coordinates': {'lat': 44.26, 'lon': -72.58},
            'stand_type': 'Travel Corridor',
            'bedding_zones': {
                'zones': [
                    {'lat': 44.27, 'lon': -72.57, 'confidence': 85}
                ]
            }
        }
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("❌ Current (Broken) Logic")
        st.code("""
# Current broken code:
deer_approach_dir = 'SE'  # Default
deer_approach_bearing = 135  # Default
        """)
        
        st.write("**Result for ALL locations:**")
        st.error("• Deer likely approach from: SE (135°)")
        st.error("• SAME result everywhere!")
        
    with col2:
        st.subheader("✅ Fixed (Dynamic) Logic")
        st.code("""
# New dynamic calculation:
bearing, direction = enhanced_deer_approach_calculation(prediction_data)
        """)
        
        st.write("**Results by terrain type:**")
        for scenario_name, scenario_data in test_scenarios.items():
            bearing, direction = enhanced_deer_approach_calculation(scenario_data)
            
            if scenario_name == "Ridge Travel Corridor":
                st.success(f"• **{scenario_name}:** {direction} ({bearing:.0f}°)")
            elif scenario_name == "Valley Feeding Area":
                st.info(f"• **{scenario_name}:** {direction} ({bearing:.0f}°)")
            elif scenario_name == "Steep North Slope Bedding":
                st.warning(f"• **{scenario_name}:** {direction} ({bearing:.0f}°)")
            else:
                st.success(f"• **{scenario_name}:** {direction} ({bearing:.0f}°)")
    
    st.markdown("---")
    
    # Show wind recommendations would also change
    st.subheader("🌬️ How Wind Recommendations Would Change")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("**Current (Always SE):**")
        st.code("""
Deer approach: SE (135°)
Best wind: NE or SW  
Worst wind: SE
        """)
        
    with col4:
        st.markdown("**Dynamic (Changes by location):**")
        
        # Show how wind advice would change for each scenario
        for scenario_name, scenario_data in list(test_scenarios.items())[:2]:
            bearing, direction = enhanced_deer_approach_calculation(scenario_data)
            
            # Calculate optimal wind directions (perpendicular to approach)
            wind1 = (bearing + 90) % 360
            wind2 = (bearing - 90) % 360
            
            directions_list = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            
            wind_dir1 = directions_list[int((wind1 + 11.25) / 22.5) % 16]
            wind_dir2 = directions_list[int((wind2 + 11.25) / 22.5) % 16]
            
            st.code(f"""
{scenario_name}:
Deer approach: {direction} ({bearing:.0f}°)
Best wind: {wind_dir1} or {wind_dir2}
Worst wind: {direction}
            """)
    
    st.markdown("---")
    st.success("✅ **Fix Ready for Implementation**")
    st.write("The dynamic calculation provides location-specific deer approach directions and wind recommendations!")

if __name__ == "__main__":
    test_streamlit_integration()
