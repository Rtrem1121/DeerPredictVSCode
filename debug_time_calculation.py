#!/usr/bin/env python3

from datetime import datetime, date, time, timedelta
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from hunting_context_analyzer import calculate_legal_hunting_hours, analyze_hunting_context

# Test the exact date/time that's failing
now = datetime.now()
print(f"=== DEBUGGING TIME CALCULATION ===")
print(f"Current datetime: {now}")
print(f"Current date: {now.date()}")
print(f"Current month: {now.month}")

# Check legal hours calculation
earliest, latest = calculate_legal_hunting_hours(now.date())
print(f"Legal hours: {earliest} to {latest}")

# Check what the sunset times table says for September (month 9)
sunset_times = {
    1: (16, 22), 2: (17, 0), 3: (17, 39), 4: (19, 18), 5: (19, 54), 6: (20, 27),
    7: (20, 38), 8: (20, 14), 9: (19, 26), 10: (18, 31), 11: (16, 40), 12: (16, 13)
}

sunset_hour, sunset_min = sunset_times.get(9, (18, 30))  # September
print(f"September sunset from table: {sunset_hour}:{sunset_min:02d}")

# Calculate what latest hunting should be (sunset + 30 min)
sunset_dt = datetime.combine(now.date(), time(sunset_hour, sunset_min))
latest_hunting_calculated = (sunset_dt + timedelta(minutes=30)).time()
print(f"Expected latest hunting time: {latest_hunting_calculated}")

# Check current time comparison
current_time_only = now.time()
print(f"Current time only: {current_time_only}")
print(f"Is current > latest? {current_time_only > latest}")
print(f"Should be: {current_time_only} > {latest_hunting_calculated} = {current_time_only > latest_hunting_calculated}")

# Manual comparison
if current_time_only > latest:
    print("❌ PROBLEM: Code thinks hunt is over")
else:
    print("✅ OK: Code thinks hunt is active")
