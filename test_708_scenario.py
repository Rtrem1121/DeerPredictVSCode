#!/usr/bin/env python3
"""
Test the specific scenario: Hunt at 7:08 AM with your exact coordinates
This should show deer moving FROM feeding TO bedding (opposite of current app)
"""

import math

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing between two GPS coordinates"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing

def bearing_to_compass(bearing):
    """Convert bearing to compass direction"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return directions[int((bearing + 11.25) / 22.5) % 16]

def determine_hunt_period(time_str):
    """Determine hunt period from time string"""
    hour = int(time_str.split(':')[0])
    minute = int(time_str.split(':')[1])
    time_minutes = hour * 60 + minute
    
    # Convert time periods to minutes for comparison
    am_start = 5 * 60 + 30  # 5:30 AM = 330 minutes
    am_end = 9 * 60         # 9:00 AM = 540 minutes
    day_end = 17 * 60       # 17:00 (5 PM) = 1020 minutes
    pm_end = 19 * 60        # 19:00 (7 PM) = 1140 minutes
    
    if am_start <= time_minutes < am_end:
        return "AM"
    elif am_end <= time_minutes < day_end:
        return "DAY"
    elif day_end <= time_minutes < pm_end:
        return "PM"
    else:
        return "OUTSIDE_HUNTING_HOURS"

def test_708_am_scenario():
    """Test your specific 7:08 AM hunting scenario"""
    
    print("🎯 TESTING YOUR 7:08 AM HUNT SCENARIO")
    print("=" * 50)
    
    # Your exact coordinates
    hunt_coords = (43.3111, -73.2201)
    stand_coords = (43.309065, -73.225100)
    
    # Mock feeding area (south of stand - common pattern)
    feeding_coords = (43.300628, -73.220358)  # From your backend data
    
    # Mock bedding area (north/thick cover - common pattern)  
    bedding_coords = (43.315, -73.228)
    
    hunt_time = "07:08"
    period = determine_hunt_period(hunt_time)
    
    print(f"Hunt Time: {hunt_time}")
    print(f"Hunt Period: {period}")
    print(f"Hunt Coordinates: {hunt_coords}")
    print(f"Stand Coordinates: {stand_coords}")
    print()
    
    # Current app logic (WRONG for 7:08 AM)
    print("🚫 CURRENT APP LOGIC (INCORRECT):")
    print("-" * 30)
    hunt_to_stand_bearing = calculate_bearing(hunt_coords[0], hunt_coords[1], stand_coords[0], stand_coords[1])
    current_deer_approach = (hunt_to_stand_bearing + 180) % 360
    current_compass = bearing_to_compass(current_deer_approach)
    print(f"Hunt→Stand Bearing: {hunt_to_stand_bearing:.0f}°")
    print(f"Current App Shows: {current_compass} ({current_deer_approach:.0f}°)")
    print(f"Assumes: Deer moving bedding → feeding (WRONG at 7:08 AM)")
    print()
    
    # New corrected logic for 7:08 AM
    print("✅ NEW CORRECTED LOGIC (AM PERIOD):")
    print("-" * 30)
    feeding_to_stand_bearing = calculate_bearing(feeding_coords[0], feeding_coords[1], stand_coords[0], stand_coords[1])
    correct_compass = bearing_to_compass(feeding_to_stand_bearing)
    print(f"Feeding→Stand Bearing: {feeding_to_stand_bearing:.0f}°")
    print(f"Correct Deer Approach: {correct_compass} ({feeding_to_stand_bearing:.0f}°)")
    print(f"Logic: Deer moving feeding → bedding (CORRECT at 7:08 AM)")
    print()
    
    # Compare the difference
    print("📊 COMPARISON:")
    print("-" * 30)
    difference = abs(current_deer_approach - feeding_to_stand_bearing)
    if difference > 180:
        difference = 360 - difference
    
    print(f"Current App: {current_compass} ({current_deer_approach:.0f}°)")
    print(f"Should Be:   {correct_compass} ({feeding_to_stand_bearing:.0f}°)")
    print(f"Difference:  {difference:.0f}° off!")
    print()
    
    # Wind recommendations
    print("💨 WIND STRATEGY DIFFERENCES:")
    print("-" * 30)
    print("Current App Wind Strategy:")
    print(f"  - Assumes deer from {current_compass}")
    print(f"  - Wind should blow FROM deer TO hunter")
    print(f"  - Bad logic for 7:08 AM")
    print()
    print("Corrected Wind Strategy:")
    print(f"  - Deer approaching from {correct_compass} (feeding area)")
    print(f"  - Wind should blow FROM {correct_compass} TO hunter")
    print(f"  - Blocks scent from reaching deer on feeding→bedding route")

def test_all_time_periods():
    """Test how different times affect deer approach"""
    
    print("\n" + "=" * 50)
    print("🕐 TESTING ALL TIME PERIODS")
    print("=" * 50)
    
    test_times = [
        ("06:00", "AM - Early Dawn"),
        ("07:08", "AM - Your Hunt Time"), 
        ("08:30", "AM - Late Dawn"),
        ("12:00", "DAY - Midday"),
        ("15:30", "DAY - Afternoon"),
        ("17:30", "PM - Early Evening"),
        ("18:30", "PM - Peak Evening")
    ]
    
    hunt_coords = (43.3111, -73.2201)
    stand_coords = (43.309065, -73.225100)
    feeding_coords = (43.300628, -73.220358)
    bedding_coords = (43.315, -73.228)
    
    for time_str, description in test_times:
        period = determine_hunt_period(time_str)
        
        if period == "AM":
            # Dawn: deer moving feeding → bedding
            source_coords = feeding_coords
            movement = "Feeding → Bedding"
        elif period == "PM":
            # Dusk: deer moving bedding → feeding
            source_coords = bedding_coords
            movement = "Bedding → Feeding"
        else:
            # Day: deer in bedding
            source_coords = bedding_coords
            movement = "In Bedding Areas"
        
        approach_bearing = calculate_bearing(source_coords[0], source_coords[1], stand_coords[0], stand_coords[1])
        approach_compass = bearing_to_compass(approach_bearing)
        
        print(f"{time_str} ({description}): {approach_compass} ({approach_bearing:.0f}°) - {movement}")

if __name__ == "__main__":
    test_708_am_scenario()
    test_all_time_periods()
