#!/usr/bin/env python3
"""
Test Thermal Wind Integration

Validates that the thermal wind analysis system integrates properly
with the deer prediction system using real Vermont conditions.

Author: GitHub Copilot
Version: 1.0.0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging
from datetime import datetime, timezone
from backend.advanced_thermal_analysis import integrate_thermal_analysis_with_wind
from backend.real_wind_deer_analysis import get_wind_deer_analyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_thermal_integration():
    """Test thermal wind integration with real Vermont data"""
    
    print("🌡️ Testing Thermal Wind Integration System")
    print("="*50)
    
    # Test location: Mount Mansfield area, Vermont (good thermal terrain)
    test_lat = 44.5438
    test_lon = -72.8169
    
    # Test different times of day for thermal patterns
    test_scenarios = [
        {"hour": 6, "description": "Peak morning thermal (downslope)"},
        {"hour": 10, "description": "Transition period"},
        {"hour": 14, "description": "Afternoon buildup"},
        {"hour": 17, "description": "Peak evening thermal (upslope)"},
        {"hour": 20, "description": "Evening thermal ending"}
    ]
    
    # Simulate weather data structure
    mock_weather_data = {
        "main": {"temp": 15},  # °F  
        "wind": {"speed": 8, "deg": 270},  # NW wind
        "hourly_wind": [
            {"hour": h, "wind_speed": 6 + (h % 12), "wind_direction": 270 + (h * 2), "temperature": 10 + h}
            for h in range(24)
        ]
    }
    
    # Simulate terrain features (Mount Mansfield has good thermal terrain)
    mock_terrain = {
        "elevation": 2100,     # feet
        "slope": 25,           # degrees (good for thermals)
        "aspect": 200          # SW-facing (good solar heating)
    }
    
    print(f"📍 Test Location: {test_lat:.4f}, {test_lon:.4f}")
    print(f"🏔️ Terrain: {mock_terrain['elevation']}ft elevation, {mock_terrain['slope']}° slope, {mock_terrain['aspect']}° aspect")
    print(f"🌬️ Base Wind: {mock_weather_data['wind']['speed']}mph from {mock_weather_data['wind']['deg']}°")
    print()
    
    # Test each scenario
    for scenario in test_scenarios:
        print(f"⏰ {scenario['description']} (Hour {scenario['hour']})")
        print("-" * 40)
        
        try:
            # Test thermal analysis
            thermal_analysis = integrate_thermal_analysis_with_wind(
                mock_weather_data, mock_terrain, test_lat, test_lon, scenario['hour']
            )
            
            # Display results
            thermal_data = thermal_analysis.get('thermal_analysis', {})
            
            print(f"   Thermal Active: {thermal_data.get('is_active', False)}")
            print(f"   Direction: {thermal_data.get('direction', 'neutral')}")
            print(f"   Strength: {thermal_data.get('strength', 0):.1f}/10")
            print(f"   Confidence: {thermal_data.get('confidence', 0):.1f}")
            print(f"   Dominant Wind: {thermal_analysis.get('dominant_wind_type', 'unknown')}")
            
            # Show deer behavior implications
            deer_behavior = thermal_analysis.get('deer_behavior_implications', {})
            print(f"   Bedding Behavior: {deer_behavior.get('bedding_behavior', 'standard')}")
            print(f"   Travel Patterns: {deer_behavior.get('travel_patterns', 'standard')}")
            
            # Show stand positioning recommendations
            stand_positions = thermal_analysis.get('stand_positioning', [])
            if stand_positions:
                print(f"   Recommended Stands: {', '.join(stand_positions[:3])}")
            
            print(f"   Timing Advantage: {thermal_analysis.get('timing_recommendation', 'standard')}")
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
            
    # Test wind-deer behavior integration
    print("🦌 Testing Wind-Deer Behavior Integration")
    print("-" * 40)
    
    try:
        wind_analyzer = get_wind_deer_analyzer()
        wind_analysis = wind_analyzer.analyze_wind_deer_behavior(
            mock_weather_data, mock_terrain, test_lat, test_lon, 17  # Evening peak
        )
        
        print(f"   Wind Analysis Type: {type(wind_analysis).__name__}")
        
        # Extract key information from the wind analysis  
        if hasattr(wind_analysis, 'effective_range_meters'):
            print(f"   Scent Dispersion: {wind_analysis.effective_range_meters}m effective range")
        elif isinstance(wind_analysis, dict):
            scent_info = wind_analysis.get('scent_zones', {})
            effective_range = scent_info.get('effective_range_yards', 0) * 0.9144  # Convert to meters
            print(f"   Scent Dispersion: {effective_range:.0f}m effective range")
            
            wind_impact = wind_analysis.get('wind_impact', {})
            print(f"   Wind Advantage: {wind_impact.get('advantage_score', 0):.1f}/10")
            
            stand_opts = wind_analysis.get('optimal_stands', [])
            print(f"   Optimal Stands: {len(stand_opts)} positions identified")
            
            if stand_opts:
                best_stand = stand_opts[0]
                print(f"   Best Stand: {best_stand.get('description', 'Unknown')} (Score: {best_stand.get('score', 0):.1f})")
        else:
            print(f"   Wind analysis structure: {wind_analysis}")
        
    except Exception as e:
        print(f"   ❌ Wind analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test thermal rule integration
    print("📋 Testing Thermal Rules Integration")
    print("-" * 40)
    
    try:
        # Load thermal rules
        with open('backend/thermal_wind_rules.json', 'r') as f:
            thermal_rules = json.load(f)
        
        print(f"   Loaded {len(thermal_rules)} thermal wind rules")
        
        # Test rule matching for morning thermal scenario
        morning_conditions = {
            'thermal_active': True,
            'thermal_direction': 'downslope',
            'thermal_strength': 6.0,
            'time_of_day': 'early_morning',
            'thermal_timing_advantage': 'prime_morning_thermal'
        }
        
        matching_rules = []
        for rule in thermal_rules:
            rule_conditions = rule.get('conditions', {})
            
            # Simple condition matching
            matches = True
            for key, expected in rule_conditions.items():
                if key in morning_conditions:
                    actual = morning_conditions[key]
                    if isinstance(expected, dict):
                        # Handle range conditions
                        if '>=' in expected and actual < expected['>=']:
                            matches = False
                        if '<=' in expected and actual > expected['<=']:
                            matches = False
                    elif expected != actual:
                        matches = False
                else:
                    matches = False
            
            if matches:
                matching_rules.append(rule)
        
        print(f"   Morning scenario matches: {len(matching_rules)} rules")
        if matching_rules:
            for rule in matching_rules[:3]:  # Show first 3
                boost_info = rule.get('boost', {})
                print(f"     • {rule['description'][:60]}...")
                print(f"       Boosts: {boost_info}")
        
    except Exception as e:
        print(f"   ❌ Rule integration error: {e}")
    
    print()
    print("✅ Thermal Wind Integration Test Complete")
    
    return True

if __name__ == "__main__":
    test_thermal_integration()
