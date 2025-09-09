#!/usr/bin/env python3

import requests
import json
from datetime import datetime

def test_simple_endpoint():
    """Test the simple GET endpoint"""
    
    # Test with the exact coordinates where user saw the problem
    url = "https://app.deerpredictapp.org/predict"
    lat = 43.3140
    lng = -73.2306
    
    print(f"🚨 TESTING TIME CONTEXT BUG - Simple Endpoint")
    print(f"Coordinates: {lat}, {lng}")
    print(f"Current time: {datetime.now()}")
    
    try:
        response = requests.get(url, params={'lat': lat, 'lng': lng}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check hunting context
            if 'hunting_context' in result:
                context = result['hunting_context']
                print(f"\n🔍 HUNTING CONTEXT:")
                print(f"Context: {context.get('context', 'NOT_FOUND')}")
                print(f"Action: {context.get('action', 'NOT_FOUND')}")
                
                if 'recommendations' in context:
                    rec = context['recommendations']
                    print(f"Primary: {rec.get('primary', 'NOT_FOUND')}")
                    
                    # Check if this shows the bug
                    primary = rec.get('primary', '')
                    if 'HUNT OVER' in primary or 'Quiet exit' in primary:
                        print(f"\n🚨 BUG CONFIRMED: Shows 'HUNT OVER' at {datetime.now().strftime('%H:%M')}")
                    elif 'ACTIVE' in primary or 'EVENING HUNT' in primary:
                        print(f"\n✅ BUG FIXED: Correctly shows active hunting time")
                    else:
                        print(f"\n❓ UNKNOWN STATE: {primary}")
            
            # Check context summary
            if 'context_summary' in result:
                summary = result['context_summary']
                print(f"\n📋 CONTEXT SUMMARY:")
                print(f"Situation: {summary.get('situation', 'NOT_FOUND')}")
                print(f"Primary guidance: {summary.get('primary_guidance', 'NOT_FOUND')}")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_simple_endpoint()
