#!/usr/bin/env python3

from datetime import datetime, date, time, timedelta

def calculate_legal_hunting_hours(hunt_date: date):
    """
    Calculate legal hunting hours for Vermont based on date.
    Vermont: 30 minutes before sunrise to 30 minutes after sunset.
    """
    # Vermont sunrise/sunset approximations (Montpelier)
    sunrise_times = {
        1: (7, 26), 2: (7, 8), 3: (6, 27), 4: (6, 31), 5: (5, 41), 6: (5, 9),
        7: (5, 10), 8: (5, 38), 9: (6, 13), 10: (6, 48), 11: (7, 28), 12: (7, 6)
    }
    
    sunset_times = {
        1: (16, 22), 2: (17, 0), 3: (17, 39), 4: (19, 18), 5: (19, 54), 6: (20, 27),
        7: (20, 38), 8: (20, 14), 9: (19, 26), 10: (18, 31), 11: (16, 40), 12: (16, 13)
    }
    
    month = hunt_date.month
    sunrise_hour, sunrise_min = sunrise_times.get(month, (6, 30))
    sunset_hour, sunset_min = sunset_times.get(month, (18, 30))
    
    # Create datetime objects for calculation
    sunrise_dt = datetime.combine(hunt_date, time(sunrise_hour, sunrise_min))
    sunset_dt = datetime.combine(hunt_date, time(sunset_hour, sunset_min))
    
    # Calculate legal hours (30 min before sunrise to 30 min after sunset)
    earliest_hunting = (sunrise_dt - timedelta(minutes=30)).time()
    latest_hunting = (sunset_dt + timedelta(minutes=30)).time()
    
    return earliest_hunting, latest_hunting

# Test with current date
test_date = date.today()
print(f"Testing for date: {test_date}")
print(f"Month: {test_date.month}")

earliest, latest = calculate_legal_hunting_hours(test_date)
print(f"Legal hunting hours: {earliest} to {latest}")

# Test with 5:42 PM
test_time = time(17, 42)  # 5:42 PM
print(f"\nTesting time: {test_time}")
print(f"Is {test_time} > {latest}? {test_time > latest}")
print(f"Is {test_time} < {earliest}? {test_time < earliest}")

# Check what the context would be
if test_time < earliest:
    print("Context: PRE_HUNT")
elif test_time > latest:
    print("Context: POST_HUNT")
else:
    print("Context: ACTIVE_HUNT")
