"""
Test fixtures and sample data for deer prediction app testing.

This module provides consistent test data to validate that refactoring
preserves the current excellent functionality.
"""

from typing import Dict, Any, List
from datetime import datetime
import json

# Test location that currently yields 95% camera confidence
GOLDEN_TEST_LOCATION = {
    "latitude": 44.262462,
    "longitude": -72.579816,
    "name": "Vermont Test Location - 95% Confidence"
}

# Expected camera placement results (preserve these!)
EXPECTED_CAMERA_PLACEMENT = {
    "confidence": 95.0,  # Updated from observed performance
    "distance_from_target": 75.0,  # Updated from observed performance  
    "reasoning": "optimal distance balancing detail and coverage",
    "coordinates": {
        "latitude": 44.262462,
        "longitude": -72.579816
    }
}

# Expected mature buck analysis results
EXPECTED_MATURE_BUCK_RESULTS = {
    "movement_probability": 0.80,  # 80% during rut
    "confidence_score": 0.59,     # 59% algorithmic confidence
    "prime_times": ["06:00"],     # Prime morning movement
    "stand_recommendations": 4,    # 4 specialized positions
    "stand_confidence": 0.95      # 95% confidence each
}

# Test locations for various scenarios
TEST_LOCATIONS = [
    {
        "name": "Golden Test Location",
        "latitude": 44.262462,
        "longitude": -72.579816,
        "expected_confidence": 89.1,
        "description": "Primary test location with known 89.1% confidence"
    },
    {
        "name": "Alternative Vermont Location",
        "latitude": 44.3,
        "longitude": -72.6,
        "expected_confidence": 75.0,  # Will establish baseline
        "description": "Secondary test location"
    },
    {
        "name": "Edge Case Location",
        "latitude": 44.1,
        "longitude": -72.4,
        "expected_confidence": 50.0,  # Will establish baseline
        "description": "Edge case for validation"
    }
]

# API request templates
def get_prediction_request_template(
    latitude: float = GOLDEN_TEST_LOCATION["latitude"],
    longitude: float = GOLDEN_TEST_LOCATION["longitude"],
    include_camera: bool = True,
    hunt_date: str = None,
    season: str = "rut"
) -> Dict[str, Any]:
    """Generate a prediction request template for testing."""
    request = {
        "lat": latitude,  # API uses 'lat' not 'latitude'
        "lon": longitude, # API uses 'lon' not 'longitude'
        "date_time": hunt_date or "2025-11-15T06:00:00",  # Default to rut season morning
        "season": season
    }
    if include_camera:
        request["include_camera_placement"] = include_camera
    return request

def get_rut_season_request() -> Dict[str, Any]:
    """Get a request template for rut season testing."""
    return get_prediction_request_template(
        hunt_date="2025-11-15T06:00:00",  # Peak rut season morning
        season="rut"
    )

def get_early_season_request() -> Dict[str, Any]:
    """Get a request template for early season testing."""
    return get_prediction_request_template(
        hunt_date="2025-10-01T06:00:00",  # Early season morning
        season="early_season"
    )

# Expected API response structure (preserve this!)
EXPECTED_API_RESPONSE_STRUCTURE = {
    "required_fields": [
        "travel_corridors",
        "bedding_zones", 
        "feeding_areas",
        "mature_buck_opportunities",
        "stand_rating",
        "notes"
    ],
    "camera_placement_fields": [
        # Camera placement info is in the notes field, not a separate object
        # This will be checked differently in validation
    ],
    "mature_buck_fields": [
        # Mature buck info is in the mature_buck_opportunities GeoJSON
        # This will be checked differently in validation
    ]
}

# Performance benchmarks (maintain these!)
PERFORMANCE_BENCHMARKS = {
    "api_response_time_max": 30.0,  # seconds
    "frontend_load_time_max": 3.0,  # seconds
    "prediction_confidence_min": 85.0,  # percentage
    "camera_confidence_target": 95.0,  # percentage (updated from observed performance)
    "camera_confidence_acceptable_range": (75.0, 100.0),  # acceptable range
    "error_rate_max": 1.0  # percentage
}

def load_sample_responses():
    """Load sample API responses for testing."""
    # This will be populated with actual responses during baseline establishment
    return {
        "golden_location_response": None,  # To be captured
        "rut_season_response": None,       # To be captured
        "early_season_response": None      # To be captured
    }

def validate_response_structure(response: Dict[str, Any]) -> List[str]:
    """Validate that API response maintains expected structure."""
    errors = []
    
    # Check required fields
    for field in EXPECTED_API_RESPONSE_STRUCTURE["required_fields"]:
        if field not in response:
            errors.append(f"Missing required field: {field}")
    
    # Check that GeoJSON structures are valid
    geojson_fields = ["travel_corridors", "bedding_zones", "feeding_areas", "mature_buck_opportunities"]
    for field in geojson_fields:
        if field in response:
            geojson_data = response[field]
            if not isinstance(geojson_data, dict):
                errors.append(f"{field} should be a GeoJSON object")
            elif "type" not in geojson_data or geojson_data["type"] != "FeatureCollection":
                errors.append(f"{field} should be a FeatureCollection")
            elif "features" not in geojson_data:
                errors.append(f"{field} should have features array")
    
    # Validate stand_rating is present and numeric
    if "stand_rating" in response:
        if not isinstance(response["stand_rating"], (int, float)):
            errors.append("stand_rating should be numeric")
    
    # Check that notes contain camera placement info
    if "notes" in response:
        notes = response["notes"]
        if "Confidence" not in notes or "GPS" not in notes:
            errors.append("Notes should contain camera placement information")
    
    return errors

def save_baseline_response(location_name: str, response: Dict[str, Any]):
    """Save a baseline response for future comparison."""
    filename = f"baseline_{location_name.lower().replace(' ', '_')}_response.json"
    filepath = f"tests/fixtures/{filename}"
    
    with open(filepath, 'w') as f:
        json.dump(response, f, indent=2)
    
    return filepath
