"""
Vermont-specific configuration for white-tailed deer movement prediction.
Based on Vermont Fish & Wildlife data and regional ecological patterns.
"""

# Vermont deer population and habitat characteristics
VERMONT_CONFIG = {
    # Geographic boundaries
    "latitude_range": (42.7, 45.0),  # Vermont's approximate latitude range
    "longitude_range": (-73.5, -71.5),  # Vermont's approximate longitude range
    
    # Elevation zones (meters)
    "elevation_zones": {
        "valley": (0, 305),      # 0-1000 ft - agricultural areas, winter concentration
        "foothill": (305, 610),   # 1000-2000 ft - mixed forest, ideal deer habitat
        "mountain": (610, 1220),  # 2000-4000 ft - higher elevations, summer range
        "alpine": (1220, 1340)    # 4000+ ft - limited deer use, extreme conditions
    },
    
    # Winter severity index thresholds
    "winter_conditions": {
        "mild": {"snow_depth_cm": 25, "temp_threshold": -10},      # <10in snow, >14°F
        "moderate": {"snow_depth_cm": 41, "temp_threshold": -18},  # 10-16in snow, 0-14°F
        "severe": {"snow_depth_cm": 41, "temp_threshold": -18}     # >16in snow, <0°F
    },
    
    # Vermont forest composition (approximate percentages)
    "forest_types": {
        "northern_hardwood": 0.65,    # Maple-beech-birch dominant
        "spruce_fir": 0.15,          # High elevation conifers
        "hemlock_northern_hardwood": 0.10,  # Mixed with hemlock component
        "white_pine": 0.05,          # Pine stands
        "other_conifer": 0.05        # Cedar, other softwoods
    },
    
    # Seasonal deer behavior patterns
    "seasonal_patterns": {
        "early_season": {
            "dates": ("09-01", "10-15"),
            "behavior_focus": "pattern_establishment",
            "primary_foods": ["acorns", "apples", "browse"],
            "movement_distance": "short",  # 0.5-1 mile daily
            "activity_peaks": ["dawn", "dusk"]
        },
        "rut": {
            "dates": ("10-15", "12-15"),
            "behavior_focus": "breeding_activity",
            "primary_foods": ["high_energy_browse", "remaining_mast"],
            "movement_distance": "extended",  # 5-15 miles for bucks
            "activity_peaks": ["dawn", "mid-day", "dusk"]
        },
        "late_season": {
            "dates": ("12-15", "03-31"),
            "behavior_focus": "survival_conservation",
            "primary_foods": ["woody_browse", "conifer_tips"],
            "movement_distance": "minimal",  # Winter yard concentration
            "activity_peaks": ["mid-day"]  # Warmest part of day
        }
    },
    
    # Vermont deer yard characteristics
    "winter_yards": {
        "elevation_preference": "<610m",  # <2000 ft
        "slope_preference": "<15_degrees",
        "aspect_preference": ["south", "southwest", "southeast"],
        "canopy_closure": ">65_percent",
        "dominant_species": ["hemlock", "cedar", "dense_spruce"],
        "snow_depth_trigger": "25.4cm",  # 10 inches
        "migration_distance": "16km"     # Up to 10 miles to yards
    },
    
    # Hunting pressure considerations
    "access_impact": {
        "road_buffer_high": 100,    # meters - high pressure zone
        "road_buffer_moderate": 500, # meters - moderate pressure
        "trail_buffer": 200,        # meters - hiking trail impact
        "pressure_multiplier": 0.8  # Reduction factor for scores
    },
    
    # Vermont-specific weather patterns
    "weather_patterns": {
        "prevailing_winds": {
            "fall": "northwest",
            "winter": "northwest", 
            "spring": "south",
            "summer": "southwest"
        },
        "storm_tracks": "west_to_east",
        "cold_front_frequency": "weekly_fall",
        "snow_season": ("11-15", "04-15")
    },
    
    # Mast crop influence (key Vermont food sources)
    "mast_species": {
        "oak": {"species": ["red_oak", "white_oak"], "elevation_max": 457},  # <1500ft
        "beech": {"distribution": "widespread", "elevation_max": 914},       # <3000ft
        "apple": {"type": "wild_domestic", "elevation_max": 305},           # <1000ft
        "cherry": {"type": "black_cherry", "elevation_max": 610},           # <2000ft
        "mountain_ash": {"elevation_range": (610, 1220)}                    # 2000-4000ft
    },
    
    # Water sources and importance
    "water_features": {
        "importance_by_season": {
            "early_season": "high",
            "rut": "moderate", 
            "late_season": "low"  # Snow provides water
        },
        "buffer_distance": 200,  # meters - deer travel distance to water
        "preferred_types": ["streams", "beaver_ponds", "seeps"]
    }
}

# Validation functions
def validate_vermont_coordinates(lat: float, lon: float) -> bool:
    """Check if coordinates are within Vermont boundaries."""
    lat_range = VERMONT_CONFIG["latitude_range"]
    lon_range = VERMONT_CONFIG["longitude_range"]
    
    return (lat_range[0] <= lat <= lat_range[1] and 
            lon_range[0] <= lon <= lon_range[1])

def get_elevation_zone(elevation_m: float) -> str:
    """Determine elevation zone for Vermont-specific analysis."""
    zones = VERMONT_CONFIG["elevation_zones"]
    
    if elevation_m < zones["valley"][1]:
        return "valley"
    elif elevation_m < zones["foothill"][1]:
        return "foothill"
    elif elevation_m < zones["mountain"][1]:
        return "mountain"
    else:
        return "alpine"

def get_winter_severity(snow_depth_cm: float, temperature_c: float) -> str:
    """Determine winter severity level for deer behavior adjustments."""
    conditions = VERMONT_CONFIG["winter_conditions"]
    
    if (snow_depth_cm > conditions["severe"]["snow_depth_cm"] or 
        temperature_c < conditions["severe"]["temp_threshold"]):
        return "severe"
    elif (snow_depth_cm > conditions["moderate"]["snow_depth_cm"] or 
          temperature_c < conditions["moderate"]["temp_threshold"]):
        return "moderate"
    else:
        return "mild"

def is_winter_yard_elevation(elevation_m: float) -> bool:
    """Check if elevation is suitable for Vermont winter deer yards."""
    return elevation_m < VERMONT_CONFIG["winter_yards"]["elevation_preference"].replace("<", "").replace("m", "")

def get_seasonal_behavior_focus(season: str) -> dict:
    """Get Vermont-specific behavioral focus for the season."""
    return VERMONT_CONFIG["seasonal_patterns"].get(season, {})
