#!/usr/bin/env python3
"""
TEST IMPLEMENTATION: AM Movement Direction Fix

This file contains the fixed behavioral analysis logic for proper AM movement direction.
Test this implementation before integrating into the main system.

KEY FIX: AM hours (5:30-8:30) should show deer moving FEEDING→BEDDING (returning from night feeding)

Author: GitHub Copilot
Date: August 26, 2025
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class FixedBehavioralAnalysis:
    """Fixed behavioral analysis with correct AM movement direction logic"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_movement_direction_notes(self, time_of_day: int, season: str) -> List[str]:
        """
        Generate movement direction behavioral notes with FIXED AM logic
        
        Args:
            time_of_day: Hour of day (0-23)
            season: Hunting season (early_season, rut, late_season)
            
        Returns:
            List of behavioral notes with correct movement direction
        """
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
                "Minimal movement - deer are resting",
                "Occasional bedding area shifts in hot weather"
            ])
            
        # MIDDAY: 12:00-15:00 = BEDDED (thermal regulation)
        elif 12 <= time_of_day <= 15:
            notes.extend([
                "Deer bedded in thermal cover",
                "Minimal activity except water trips in hot weather",
                "Using thermal bedding areas for temperature regulation"
            ])
            
        # AFTERNOON: 16:00-17:00 = PRE-FEEDING MOVEMENT 
        elif 16 <= time_of_day <= 17:
            notes.extend([
                "Early pre-feeding movement beginning",
                "Deer starting to leave bedding areas",
                "Movement direction: bedding areas → feeding areas",
                "Cautious movement as deer assess conditions"
            ])
            
        # EVENING: 18:00-20:00 = PRIME FEEDING MOVEMENT
        elif 18 <= time_of_day <= 20:
            notes.extend([
                "Prime feeding movement period",
                "Movement direction: bedding areas → feeding areas",
                "Peak feeding activity hours",
                "Deer moving to primary food sources"
            ])
            
        # NIGHT: 21:00-4:00 = FEEDING ACTIVITY
        elif 21 <= time_of_day <= 23 or 0 <= time_of_day <= 4:
            notes.extend([
                "Primary feeding period - deer on food sources",
                "Multiple feeding areas may be visited",
                "Limited travel between food sources",
                "Preparing for morning return to bedding"
            ])
        
        # Add seasonal modifications
        if season == "early_season":
            notes.append("Early season: Establishing fall feeding patterns")
        elif season == "rut":
            notes.append("Rut season: Breeding activity may override normal feeding schedules")
        elif season == "late_season":
            notes.append("Late season: Energy conservation - reduced movement")
            
        return notes
    
    def get_weather_trigger_notes(self, weather_data: Dict) -> List[str]:
        """
        Generate weather-triggered behavioral notes with FIXED cold front logic
        
        Args:
            weather_data: Weather information dictionary
            
        Returns:
            List of weather-influenced behavioral notes
        """
        notes = []
        
        temperature = weather_data.get('temperature', 50)
        pressure = weather_data.get('pressure', 30.0)
        wind_speed = weather_data.get('wind', {}).get('speed', 5)
        
        # COLD FRONT DETECTION (pressure drop + temperature drop)
        # This should INCREASE movement probability
        if pressure < 29.9 and temperature < 45:
            notes.extend([
                "Cold front conditions detected - increased deer movement expected",
                "Barometric pressure drop triggering feeding activity", 
                "Temperature drop encouraging deer to feed before weather worsens",
                "PRIME HUNTING CONDITIONS - deer will be moving"
            ])
            
        # High pressure system (stable weather)
        elif pressure > 30.2:
            notes.extend([
                "High pressure system - stable weather patterns",
                "Normal movement patterns expected",
                "Good visibility conditions for hunting"
            ])
            
        # High wind conditions
        if wind_speed > 15:
            notes.extend([
                "High wind conditions - deer seeking wind protection",
                "Prefer sheltered bedding areas and travel routes",
                "Movement may be reduced in open areas"
            ])
        elif wind_speed < 5:
            notes.extend([
                "Calm wind conditions - deer may use open travel routes",
                "Good scent management conditions for hunters"
            ])
            
        return notes
    
    def get_pressure_response_notes(self, pressure_level: str, time_of_day: int) -> List[str]:
        """
        Generate hunting pressure response notes with FIXED pressure logic
        
        Args:
            pressure_level: Hunting pressure level (low, moderate, high)
            time_of_day: Hour of day (0-23)
            
        Returns:
            List of pressure-influenced behavioral notes
        """
        notes = []
        
        if pressure_level == "high":
            # High pressure should REDUCE daytime activity
            if 6 <= time_of_day <= 18:  # Daytime hours
                notes.extend([
                    "High hunting pressure - reduced daytime deer activity",
                    "Deer shifting to more nocturnal behavior patterns",
                    "Expect minimal movement during daylight hours",
                    "Deer using thicker cover and avoiding open areas"
                ])
            else:  # Nighttime hours
                notes.extend([
                    "High hunting pressure - increased nocturnal activity",
                    "Deer compensating with more night feeding",
                    "Primary movement shifted to darkness hours"
                ])
                
        elif pressure_level == "moderate":
            notes.extend([
                "Moderate hunting pressure - some behavioral adjustment",
                "Deer may delay movement by 30-60 minutes",
                "Still huntable but require more careful approach"
            ])
            
        elif pressure_level == "low":
            notes.extend([
                "Low hunting pressure - normal deer movement patterns",
                "Deer following natural behavioral rhythms",
                "Good opportunity for predictable movement"
            ])
            
        return notes
    
    def get_time_based_activity_level(self, time_of_day: int) -> str:
        """
        Get activity level with FIXED time-based curve (dawn/dusk peaks)
        
        Args:
            time_of_day: Hour of day (0-23)
            
        Returns:
            Activity level string
        """
        # Create proper activity curve with dawn/dusk peaks
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
    
    def get_seasonal_food_notes(self, season: str) -> List[str]:
        """
        Generate seasonal food source notes with FIXED seasonal logic
        
        Args:
            season: Hunting season (early_season, rut, late_season)
            
        Returns:
            List of seasonal food source notes
        """
        notes = []
        
        if season == "early_season":
            notes.extend([
                "Early season food sources: acorns and mast crops priority",
                "Oak flats and beech groves provide high-energy mast",
                "Soybean fields offer protein-rich forage",
                "Apple orchards attract deer during early fall",
                "Browse and forbs supplement diet in transition areas"
            ])
            
        elif season == "rut":
            notes.extend([
                "Rut season food sources: high-energy requirements",
                "Standing corn provides carbohydrates for breeding activity",
                "Remaining mast crops still highly attractive",
                "High-energy browse in staging areas",
                "Does seeking nutritious food sources to support breeding"
            ])
            
        elif season == "late_season":
            notes.extend([
                "Late season food sources: survival-focused feeding",
                "Corn stubble provides accessible waste grain",
                "Woody browse becomes primary food source",
                "Waste grain from harvested fields concentrated food",
                "Conifer tips and bark for emergency nutrition"
            ])
            
        return notes
    
    def get_mature_buck_specific_notes(self, general_notes: List[str]) -> List[str]:
        """
        Generate mature buck specific behavioral modifications
        
        Args:
            general_notes: General deer behavioral notes
            
        Returns:
            Modified notes for mature buck behavior
        """
        mature_notes = []
        
        # Add mature buck specific modifiers
        mature_notes.extend([
            "Mature buck behavior: 30% more cautious than general deer",
            "Increased pressure sensitivity - avoid hunting pressure areas",
            "Prefer thicker cover and longer escape routes",
            "More likely to delay movement if conditions aren't optimal"
        ])
        
        # Modify existing notes for mature buck caution
        for note in general_notes:
            if "movement" in note.lower():
                mature_notes.append(f"Mature buck: {note} (with increased caution)")
            elif "feeding" in note.lower():
                mature_notes.append(f"Mature buck: {note} (security-focused)")
            else:
                mature_notes.append(note)
                
        return mature_notes

def test_fixed_behavioral_analysis():
    """Test the fixed behavioral analysis implementation"""
    print("🧪 TESTING FIXED BEHAVIORAL ANALYSIS")
    print("=" * 50)
    
    analyzer = FixedBehavioralAnalysis()
    
    # Test AM movement direction (should be feeding→bedding)
    print("\n🌅 Testing AM Movement Direction (6:00 AM):")
    am_notes = analyzer.get_movement_direction_notes(6, "early_season")
    for note in am_notes:
        print(f"  • {note}")
    
    # Check for correct direction
    movement_text = " ".join(am_notes).lower()
    if "feeding areas → bedding areas" in movement_text:
        print("  ✅ CORRECT: Shows feeding→bedding movement")
    else:
        print("  ❌ ERROR: Movement direction unclear or wrong")
    
    # Test cold front logic (should increase movement)
    print("\n🌦️ Testing Cold Front Logic:")
    cold_front_weather = {"temperature": 40, "pressure": 29.7, "wind": {"speed": 8}}
    weather_notes = analyzer.get_weather_trigger_notes(cold_front_weather)
    for note in weather_notes:
        print(f"  • {note}")
    
    # Check for increased movement
    weather_text = " ".join(weather_notes).lower()
    if "increased deer movement" in weather_text:
        print("  ✅ CORRECT: Cold front increases movement")
    else:
        print("  ❌ ERROR: Cold front not triggering movement")
    
    # Test pressure response (high pressure should reduce daytime activity)
    print("\n👥 Testing High Pressure Response (12:00 PM):")
    pressure_notes = analyzer.get_pressure_response_notes("high", 12)
    for note in pressure_notes:
        print(f"  • {note}")
    
    # Check for reduced daytime activity
    pressure_text = " ".join(pressure_notes).lower()
    if "reduced daytime" in pressure_text:
        print("  ✅ CORRECT: High pressure reduces daytime activity")
    else:
        print("  ❌ ERROR: High pressure not reducing daytime activity")
    
    # Test time-based activity curve
    print("\n⏰ Testing Time-Based Activity Levels:")
    test_times = [6, 12, 18, 23]
    expected = ["high", "low", "high", "moderate"]
    
    for i, time in enumerate(test_times):
        activity = analyzer.get_time_based_activity_level(time)
        expected_activity = expected[i]
        status = "✅ CORRECT" if activity == expected_activity else "❌ ERROR"
        print(f"  • {time:02d}:00 - Expected: {expected_activity}, Got: {activity} {status}")
    
    # Test seasonal food logic
    print("\n🍂 Testing Seasonal Food Logic:")
    for season in ["early_season", "rut", "late_season"]:
        food_notes = analyzer.get_seasonal_food_notes(season)
        print(f"  • {season}:")
        for note in food_notes[:2]:  # Show first 2 notes
            print(f"    - {note}")
    
    print("\n✅ Fixed behavioral analysis test completed!")
    return True

if __name__ == "__main__":
    test_fixed_behavioral_analysis()
