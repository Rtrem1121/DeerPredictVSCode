#!/usr/bin/env python3

import requests
import json
from datetime import datetime

def test_localhost_time_bug():
    """Test the time context issue on localhost"""
    
    url = "http://localhost:8000/predict"
    lat = 43.3140
    lng = -73.2306
    
    print(f"🚨 TESTING TIME CONTEXT BUG - Localhost")
    print(f"Coordinates: {lat}, {lng}")
    print(f"Current time: {datetime.now()}")
    print(f"Expected: Should show ACTIVE_HUNT at current time ({datetime.now().strftime('%H:%M')})")
    
    try:
        payload = {
            'lat': lat,
            'lon': lng,
            'date_time': datetime.now().isoformat(),
            'season': 'fall'
        }
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'data' in result:
                data = result['data']
            
            # Check hunting context
            if 'hunting_context' in data:
                context = data['hunting_context']
                print(f"\n🔍 HUNTING CONTEXT:")
                print(f"Context: {context.get('context', 'NOT_FOUND')}")
                print(f"Action: {context.get('action', 'NOT_FOUND')}")
                
                if 'recommendations' in context:
                    rec = context['recommendations']
                    primary = rec.get('primary', 'NOT_FOUND')
                    print(f"Primary: {primary}")
                    
                    # Check if this shows the bug
                    if 'HUNT OVER' in primary or 'Quiet exit' in primary:
                        print(f"\n🚨 BUG CONFIRMED: Shows 'HUNT OVER' at {datetime.now().strftime('%H:%M')}")
                        print(f"   This should show ACTIVE_HUNT during legal hours!")
                    elif 'ACTIVE' in primary or 'EVENING HUNT' in primary:
                        print(f"\n✅ WORKING CORRECTLY: Shows active hunting time")
                    else:
                        print(f"\n❓ UNKNOWN STATE: {primary}")
                        
                if 'current_status' in context:
                    status = context['current_status']
                    print(f"Time remaining: {status.get('time_remaining_minutes', 'NOT_FOUND')} minutes")
                    print(f"Legal hours: {status.get('legal_hunting_hours', 'NOT_FOUND')}")
            
            # Check context summary
            if 'context_summary' in data:
                summary = data['context_summary']
                print(f"\n📋 CONTEXT SUMMARY:")
                print(f"Situation: {summary.get('situation', 'NOT_FOUND')}")
                print(f"Primary guidance: {summary.get('primary_guidance', 'NOT_FOUND')}")
                print(f"Time remaining: {summary.get('time_remaining', 'NOT_FOUND')} minutes")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_localhost_time_bug()
