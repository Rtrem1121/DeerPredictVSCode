#!/usr/bin/env python3
"""
Test pressure resistance scoring with default terrain feature values
"""

def calculate_pressure_resistance_score():
    """Test pressure resistance calculation with likely default values"""
    
    print("Testing Pressure Resistance Scoring:")
    print("="*50)
    
    # These are likely the default/fallback values being used
    test_scenarios = [
        {
            "name": "Scenario 1: Default/Empty terrain features",
            "escape_cover_density": 50.0,  # Default from _safe_float_conversion
            "hunter_accessibility": 0.7,   # Default from _safe_float_conversion
            "wetland_proximity": 1000.0,   # Default from _safe_float_conversion
            "cliff_proximity": 1000.0,     # Default from _safe_float_conversion
            "visibility_limitation": 0.5   # Default from _safe_float_conversion
        },
        {
            "name": "Scenario 2: Typical forest terrain",
            "escape_cover_density": 75.0,
            "hunter_accessibility": 0.4,
            "wetland_proximity": 500.0,
            "cliff_proximity": 800.0,
            "visibility_limitation": 0.6
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{scenario['name']}:")
        print("-" * 40)
        
        score = 0.0
        
        # Thick escape cover
        escape_cover = scenario["escape_cover_density"]
        if escape_cover >= 80.0:
            cover_points = 30.0
        elif escape_cover >= 60.0:
            cover_points = 20.0
        else:
            cover_points = 0.0
        score += cover_points
        print(f"  Escape cover ({escape_cover}%): +{cover_points}")
        
        # Hunter accessibility
        accessibility = scenario["hunter_accessibility"]
        if accessibility <= 0.3:
            access_points = 25.0
        elif accessibility <= 0.5:
            access_points = 15.0
        else:
            access_points = 0.0
        score += access_points
        print(f"  Hunter accessibility ({accessibility}): +{access_points}")
        
        # Wetland proximity
        wetland_dist = scenario["wetland_proximity"]
        if wetland_dist <= 100:
            wetland_points = 20.0
        elif wetland_dist <= 300:
            wetland_points = 10.0
        else:
            wetland_points = 0.0
        score += wetland_points
        print(f"  Wetland proximity ({wetland_dist}m): +{wetland_points}")
        
        # Cliff proximity
        cliff_dist = scenario["cliff_proximity"]
        if cliff_dist <= 200:
            cliff_points = 15.0
        else:
            cliff_points = 0.0
        score += cliff_points
        print(f"  Cliff proximity ({cliff_dist}m): +{cliff_points}")
        
        # Visibility limitation
        visibility = scenario["visibility_limitation"]
        if visibility >= 0.8:
            vis_points = 10.0
        else:
            vis_points = 0.0
        score += vis_points
        print(f"  Visibility limitation ({visibility}): +{vis_points}")
        
        final_score = min(score, 100.0)
        print(f"  TOTAL PRESSURE RESISTANCE: {final_score}")

if __name__ == "__main__":
    calculate_pressure_resistance_score()
