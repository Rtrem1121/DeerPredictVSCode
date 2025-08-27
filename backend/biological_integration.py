#!/usr/bin/env python3
"""
INTEGRATION: Add Fixed Biological Logic to Prediction Service

This file contains the integration code to add the fixed biological logic
to the main prediction service.

Author: GitHub Copilot
Date: August 26, 2025
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def add_fixed_biological_analysis(prediction_data: Dict, weather_data: Dict, 
                                time_of_day: int, season: str, 
                                hunting_pressure_level: str = "moderate") -> Dict:
    """
    Add fixed biological analysis to prediction data
    
    Args:
        prediction_data: Existing prediction data
        weather_data: Weather conditions
        time_of_day: Hour of day (0-23)
        season: Hunting season
        hunting_pressure_level: Hunting pressure level (low, moderate, high)
        
    Returns:
        Enhanced prediction data with fixed biological logic
    """
    
    # FIXED BIOLOGICAL ANALYSIS
    biological_analysis = {
        "movement_direction": get_fixed_movement_direction_notes(time_of_day, season),
        "weather_influence": get_fixed_weather_trigger_notes(weather_data),
        "pressure_response": get_fixed_pressure_response_notes(hunting_pressure_level, time_of_day),
        "activity_level": get_fixed_activity_level(time_of_day),
        "seasonal_food": get_fixed_seasonal_food_notes(season),
        "biological_logic_version": "FIXED_v1.0"
    }
    
    # Add to prediction data
    prediction_data["biological_analysis"] = biological_analysis
    
    # Update confidence score based on fixed logic
    original_confidence = prediction_data.get("confidence_score", 0.5)
    weather_boost = get_weather_confidence_boost(weather_data)
    pressure_penalty = get_pressure_confidence_penalty(hunting_pressure_level)
    activity_boost = get_activity_confidence_boost(time_of_day)
    
    enhanced_confidence = min(max(original_confidence + weather_boost - pressure_penalty + activity_boost, 0.0), 1.0)
    prediction_data["enhanced_confidence_score"] = enhanced_confidence
    
    # Add hunting recommendations based on fixed logic
    prediction_data["hunting_recommendations"] = generate_fixed_hunting_recommendations(
        biological_analysis, time_of_day, weather_data, hunting_pressure_level
    )
    
    return prediction_data

def get_fixed_movement_direction_notes(time_of_day: int, season: str) -> List[str]:
    """Get movement direction notes with FIXED AM logic"""
    notes = []
    
    # AM HOURS: 5:30-8:30 = FEEDING→BEDDING (returning from night feeding)
    if 5 <= time_of_day <= 8:
        notes.extend([
            "Deer returning to bedding areas after night feeding",
            "Movement direction: feeding areas → bedding areas",
            "Peak return movement between 6:00-7:30 AM",
            "Last chance to catch deer moving before they bed down"
        ])
    # LATE MORNING: 9:00-11:00 = MINIMAL MOVEMENT (bedded down)
    elif 9 <= time_of_day <= 11:
        notes.extend([
            "Deer settled in bedding areas",
            "Minimal movement - deer are resting"
        ])
    # AFTERNOON: 16:00-17:00 = PRE-FEEDING MOVEMENT
    elif 16 <= time_of_day <= 17:
        notes.extend([
            "Early pre-feeding movement beginning",
            "Movement direction: bedding areas → feeding areas"
        ])
    # EVENING: 18:00-20:00 = PRIME FEEDING MOVEMENT
    elif 18 <= time_of_day <= 20:
        notes.extend([
            "Prime feeding movement period",
            "Movement direction: bedding areas → feeding areas",
            "Peak feeding activity hours"
        ])
    # NIGHT: 21:00-4:00 = FEEDING ACTIVITY
    elif 21 <= time_of_day <= 23 or 0 <= time_of_day <= 4:
        notes.extend([
            "Primary feeding period - deer on food sources",
            "Limited travel between food sources"
        ])
    
    # Add seasonal context
    if season == "early_season":
        notes.append("Early season: Establishing fall feeding patterns")
    elif season == "rut":
        notes.append("Rut season: Breeding activity may override normal feeding schedules")
    elif season == "late_season":
        notes.append("Late season: Energy conservation - reduced movement")
    
    return notes

def get_fixed_weather_trigger_notes(weather_data: Dict) -> List[str]:
    """Get weather trigger notes with FIXED cold front logic"""
    notes = []
    
    temperature = weather_data.get('temperature', 50)
    pressure = weather_data.get('pressure', 30.0)
    wind_speed = weather_data.get('wind_speed', 5)
    
    # COLD FRONT DETECTION (pressure drop + temperature drop)
    if pressure < 29.9 and temperature < 45:
        notes.extend([
            "Cold front conditions detected - increased deer movement expected",
            "Barometric pressure drop triggering feeding activity",
            "Temperature drop encouraging deer to feed before weather worsens",
            "PRIME HUNTING CONDITIONS - deer will be moving"
        ])
    # High pressure system
    elif pressure > 30.2:
        notes.extend([
            "High pressure system - stable weather patterns",
            "Normal movement patterns expected"
        ])
    
    # Wind conditions
    if wind_speed > 15:
        notes.extend([
            "High wind conditions - deer seeking wind protection",
            "Movement may be reduced in open areas"
        ])
    elif wind_speed < 5:
        notes.append("Calm wind conditions - good scent management conditions")
    
    return notes

def get_fixed_pressure_response_notes(pressure_level: str, time_of_day: int) -> List[str]:
    """Get pressure response notes with FIXED pressure logic"""
    notes = []
    
    if pressure_level == "high":
        # High pressure should REDUCE daytime activity
        if 6 <= time_of_day <= 18:  # Daytime hours
            notes.extend([
                "High hunting pressure - reduced daytime deer activity",
                "Deer shifting to more nocturnal behavior patterns",
                "Expect minimal movement during daylight hours"
            ])
        else:  # Nighttime hours
            notes.extend([
                "High hunting pressure - increased nocturnal activity",
                "Primary movement shifted to darkness hours"
            ])
    elif pressure_level == "moderate":
        notes.extend([
            "Moderate hunting pressure - some behavioral adjustment",
            "Deer may delay movement by 30-60 minutes"
        ])
    elif pressure_level == "low":
        notes.extend([
            "Low hunting pressure - normal deer movement patterns",
            "Deer following natural behavioral rhythms"
        ])
    
    return notes

def get_fixed_activity_level(time_of_day: int) -> str:
    """Get activity level with FIXED time-based curve"""
    if 6 <= time_of_day <= 8:  # Dawn peak
        return "high"
    elif 9 <= time_of_day <= 11:  # Morning decline
        return "moderate"
    elif 12 <= time_of_day <= 15:  # Midday low
        return "low"
    elif 16 <= time_of_day <= 19:  # Dusk peak
        return "high"
    elif 20 <= time_of_day <= 23:  # Evening moderate
        return "moderate"
    elif 0 <= time_of_day <= 5:  # Night moderate
        return "moderate"
    else:
        return "moderate"

def get_fixed_seasonal_food_notes(season: str) -> List[str]:
    """Get seasonal food notes with FIXED seasonal logic"""
    if season == "early_season":
        return [
            "Early season food sources: acorns and mast crops priority",
            "Oak flats and beech groves provide high-energy mast",
            "Soybean fields offer protein-rich forage"
        ]
    elif season == "rut":
        return [
            "Rut season food sources: high-energy requirements",
            "Standing corn provides carbohydrates for breeding activity",
            "Remaining mast crops still highly attractive"
        ]
    elif season == "late_season":
        return [
            "Late season food sources: survival-focused feeding",
            "Corn stubble provides accessible waste grain",
            "Woody browse becomes primary food source"
        ]
    else:
        return ["Standard food sources for season"]

def get_weather_confidence_boost(weather_data: Dict) -> float:
    """Calculate weather-based confidence boost"""
    temperature = weather_data.get('temperature', 50)
    pressure = weather_data.get('pressure', 30.0)
    
    # Cold front boost
    if pressure < 29.9 and temperature < 45:
        return 0.3  # Major boost for cold front
    elif pressure > 30.2:
        return 0.1  # Small boost for stable weather
    else:
        return 0.0

def get_pressure_confidence_penalty(pressure_level: str) -> float:
    """Calculate hunting pressure confidence penalty"""
    if pressure_level == "high":
        return 0.2  # Major penalty for high pressure
    elif pressure_level == "moderate":
        return 0.1  # Small penalty for moderate pressure
    else:
        return 0.0  # No penalty for low pressure

def get_activity_confidence_boost(time_of_day: int) -> float:
    """Calculate activity-based confidence boost"""
    activity = get_fixed_activity_level(time_of_day)
    if activity == "high":
        return 0.2
    elif activity == "moderate":
        return 0.1
    else:
        return 0.0

def generate_fixed_hunting_recommendations(biological_analysis: Dict, time_of_day: int, 
                                         weather_data: Dict, pressure_level: str) -> List[str]:
    """Generate hunting recommendations based on fixed biological logic"""
    recommendations = []
    
    # Time-based recommendations
    movement_notes = biological_analysis.get("movement_direction", [])
    movement_text = " ".join(movement_notes).lower()
    
    if "feeding areas → bedding areas" in movement_text:
        recommendations.extend([
            "Position along travel routes from feeding areas to bedding areas",
            "Focus on trails leading away from food sources",
            "Set up between food sources and known bedding areas"
        ])
    elif "bedding areas → feeding areas" in movement_text:
        recommendations.extend([
            "Position along trails from bedding areas to feeding areas",
            "Focus on staging areas near food sources"
        ])
    
    # Weather-based recommendations
    weather_notes = biological_analysis.get("weather_influence", [])
    weather_text = " ".join(weather_notes).lower()
    
    if "cold front" in weather_text and "increased movement" in weather_text:
        recommendations.extend([
            "PRIME CONDITIONS: Cold front triggering movement",
            "All-day hunting recommended - deer will be active"
        ])
    elif "high wind" in weather_text:
        recommendations.append("Hunt sheltered areas and wind breaks")
    
    # Pressure-based recommendations
    if pressure_level == "high":
        recommendations.extend([
            "Focus on thick cover and sanctuary areas",
            "Expect reduced daytime movement"
        ])
    elif pressure_level == "low":
        recommendations.append("Normal hunting patterns apply")
    
    return recommendations

def test_biological_integration():
    """Test the biological integration functions"""
    print("🧪 TESTING BIOLOGICAL INTEGRATION")
    print("=" * 50)
    
    # Test data
    test_weather = {"temperature": 40, "pressure": 29.7, "wind_speed": 8}
    test_prediction = {"confidence_score": 0.5}
    
    # Test AM movement
    enhanced = add_fixed_biological_analysis(
        test_prediction.copy(), test_weather, 7, "early_season", "moderate"
    )
    
    print("🌅 AM Movement Test:")
    for note in enhanced["biological_analysis"]["movement_direction"]:
        if "direction" in note.lower():
            print(f"  • {note}")
    
    # Test cold front
    print("\n🌦️ Cold Front Test:")
    for note in enhanced["biological_analysis"]["weather_influence"]:
        if "cold front" in note.lower():
            print(f"  • {note}")
    
    print(f"\n📊 Enhanced Confidence: {enhanced['enhanced_confidence_score']:.2f}")
    print("✅ Integration test completed!")

if __name__ == "__main__":
    test_biological_integration()
