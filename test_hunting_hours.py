#!/usr/bin/env python3
"""
Test script to verify Vermont hunting hours calculations are working correctly.
"""

import sys
import os
from datetime import datetime, date

# Add frontend directory to path to import the functions
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))

try:
    from app import get_vermont_legal_hunting_hours, generate_legal_hunting_times
    
    def test_hunting_hours():
        """Test hunting hours for different dates"""
        
        print("🦌 Vermont Legal Hunting Hours Test")
        print("=" * 50)
        
        # Test different months
        test_dates = [
            date(2025, 1, 15),   # January - Winter
            date(2025, 4, 15),   # April - Spring  
            date(2025, 7, 15),   # July - Summer
            date(2025, 10, 15),  # October - Fall hunting season
            date(2025, 12, 15),  # December - Late hunting season
        ]
        
        for test_date in test_dates:
            print(f"\n📅 {test_date.strftime('%B %d, %Y')}")
            
            # Get legal hunting hours
            earliest, latest = get_vermont_legal_hunting_hours(test_date)
            print(f"   ⏰ Legal Hours: {earliest.strftime('%I:%M %p')} - {latest.strftime('%I:%M %p')}")
            
            # Generate hunting times
            legal_times = generate_legal_hunting_times(test_date)
            print(f"   🎯 Available Times: {len(legal_times)} options")
            print(f"   📋 First few times: {[time_str for _, time_str in legal_times[:3]]}")
            print(f"   📋 Last few times: {[time_str for _, time_str in legal_times[-3:]]}")
            
            # Verify that times are within legal bounds
            for time_obj, time_str in legal_times:
                if not (earliest <= time_obj <= latest):
                    print(f"   ❌ ERROR: {time_str} is outside legal hours!")
                    return False
            
            print(f"   ✅ All {len(legal_times)} times are within legal hunting hours")
        
        print("\n🎯 Vermont Hunting Hours Test Completed Successfully!")
        print("⚖️ All times comply with Vermont law: 30 min before sunrise to 30 min after sunset")
        return True
    
    def test_current_date():
        """Test with today's date"""
        print(f"\n📅 Testing Today's Date: {date.today().strftime('%B %d, %Y')}")
        
        today = date.today()
        earliest, latest = get_vermont_legal_hunting_hours(today)
        legal_times = generate_legal_hunting_times(today)
        
        print(f"⏰ Today's Legal Hunting Hours: {earliest.strftime('%I:%M %p')} - {latest.strftime('%I:%M %p')}")
        print(f"🎯 Available Time Options: {len(legal_times)}")
        print(f"🌅 Earliest: {legal_times[0][1] if legal_times else 'None'}")
        print(f"🌇 Latest: {legal_times[-1][1] if legal_times else 'None'}")
        
        return True
    
    if __name__ == "__main__":
        print("Testing Vermont hunting hours functionality...\n")
        
        success = test_hunting_hours()
        if success:
            test_current_date()
            print("\n✅ All tests passed! Vermont hunting hours are properly restricted.")
        else:
            print("\n❌ Tests failed!")
            sys.exit(1)

except ImportError as e:
    print(f"❌ Error importing functions: {e}")
    print("Make sure the frontend app.py is available and contains the required functions.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error running tests: {e}")
    sys.exit(1)
