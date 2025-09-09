#!/usr/bin/env python3

import requests
import json
from datetime import datetime

def test_time_context_issue():
    """Test the specific time context issue the user reported"""
    
    # Test with the exact coordinates where user saw the problem
    url = "https://app.deerpredictapp.org/analyze-prediction-detailed"
    lat = 43.3140
    lng = -73.2306
    
    print(f"🚨 TESTING TIME CONTEXT BUG")
    print(f"Coordinates: {lat}, {lng}")
    print(f"Current time: {datetime.now()}")
    print(f"Expected: Should show ACTIVE_HUNT at 5:42 PM")
    print(f"Problem: User reported shows 'HUNT OVER' instead")
    
    payload = {
        'lat': lat,
        'lon': lng,
        'date_time': datetime.now().isoformat(),
        'time_of_day': 17,  # 5 PM hour
        'season': 'fall',
        'hunting_pressure': 'low'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'prediction' in result:
                pred = result['prediction']
                
                # Check hunting context
                if 'hunting_context' in pred:
                    context = pred['hunting_context']
                    print(f"\n🔍 HUNTING CONTEXT ANALYSIS:")
                    print(f"Context: {context.get('context', 'NOT_FOUND')}")
                    print(f"Action: {context.get('action', 'NOT_FOUND')}")
                    
                    if 'recommendations' in context:
                        rec = context['recommendations']
                        print(f"Primary: {rec.get('primary', 'NOT_FOUND')}")
                        print(f"Secondary: {rec.get('secondary', 'NOT_FOUND')}")
                    
                    if 'current_status' in context:
                        status = context['current_status']
                        print(f"Time remaining: {status.get('time_remaining_minutes', 'NOT_FOUND')} minutes")
                        print(f"Legal hours: {status.get('legal_hunting_hours', 'NOT_FOUND')}")
                
                # Check context summary
                if 'context_summary' in pred:
                    summary = pred['context_summary']
                    print(f"\n📋 CONTEXT SUMMARY:")
                    print(f"Situation: {summary.get('situation', 'NOT_FOUND')}")
                    print(f"Recommended action: {summary.get('recommended_action', 'NOT_FOUND')}")
                    print(f"Primary guidance: {summary.get('primary_guidance', 'NOT_FOUND')}")
                    print(f"Time remaining: {summary.get('time_remaining', 'NOT_FOUND')} minutes")
                    
                    # Check if this shows the bug
                    if 'HUNT OVER' in summary.get('primary_guidance', ''):
                        print(f"\n🚨 BUG CONFIRMED: Shows 'HUNT OVER' when should be ACTIVE_HUNT")
                    elif 'ACTIVE' in summary.get('primary_guidance', ''):
                        print(f"\n✅ BUG FIXED: Correctly shows active hunting time")
                    else:
                        print(f"\n❓ UNKNOWN STATE: {summary.get('primary_guidance', '')}")
                
                # Show timestamp info
                print(f"\n⏰ TIMESTAMP INFO:")
                print(f"Original timestamp: {pred.get('original_timestamp', 'NOT_FOUND')}")
                print(f"Context timestamp: {pred.get('context_timestamp', 'NOT_FOUND')}")
                
            else:
                print("❌ No prediction data in response")
                print(f"Response keys: {list(result.keys())}")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_time_context_issue()
