#!/usr/bin/env python3

import sys
from datetime import datetime, time
import pytz

def test_time_logic():
    """Test the time logic that's causing the hunting context bug"""
    
    print("🔍 DEBUGGING TIME CONTEXT BUG")
    print("=" * 50)
    
    # Test scenario: 5:42 PM on September 8, 2025
    test_time = time(17, 42)  # 5:42 PM
    earliest_hunt = time(5, 43)  # 5:43 AM 
    latest_hunt = time(19, 56)  # 7:56 PM
    
    print(f"📅 Test Scenario:")
    print(f"   Current Time: {test_time} (5:42 PM)")
    print(f"   Legal Hours: {earliest_hunt} - {latest_hunt}")
    print()
    
    print(f"🔍 Time Comparisons:")
    print(f"   current_time < earliest_hunt: {test_time < earliest_hunt}")
    print(f"   current_time > latest_hunt: {test_time > latest_hunt}")
    print(f"   In legal hours: {earliest_hunt <= test_time <= latest_hunt}")
    print()
    
    # Show what the bug logic would produce
    if test_time < earliest_hunt:
        context = "PRE_HUNT"
        verdict = "❌ WRONG: Should be ACTIVE_HUNT"
    elif test_time > latest_hunt:
        context = "POST_HUNT" 
        verdict = "❌ CRITICAL BUG: This is the problem!"
    else:
        context = "ACTIVE_HUNT"
        verdict = "✅ CORRECT"
        
    print(f"🎯 Context Logic Result:")
    print(f"   Calculated Context: {context}")
    print(f"   Verdict: {verdict}")
    print()
    
    # Show time remaining calculation
    from datetime import datetime, timedelta
    current_dt = datetime.combine(datetime.now().date(), test_time)
    latest_dt = datetime.combine(datetime.now().date(), latest_hunt)
    time_remaining = (latest_dt - current_dt).total_seconds() / 60
    
    print(f"⏰ Time Calculations:")
    print(f"   Time remaining: {time_remaining:.1f} minutes")
    print(f"   Hours remaining: {time_remaining/60:.2f} hours")
    print()
    
    print("🚨 THE PROBLEM:")
    print("   5:42 PM is CLEARLY within legal hours (5:43 AM - 7:56 PM)")
    print("   System should show 'ACTIVE_HUNT' not 'POST_HUNT'")
    print("   This is prime evening hunting time!")

if __name__ == "__main__":
    test_time_logic()
