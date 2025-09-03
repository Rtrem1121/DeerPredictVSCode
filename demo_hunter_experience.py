#!/usr/bin/env python3
"""
Real-Time Hunter Decision Demo

Shows what a hunter at 7:19 PM on September 3rd would actually see 
with the time-context aware system vs. generic planning advice.
"""

import requests
from datetime import datetime
from backend.hunting_context_analyzer import analyze_hunting_context

def demonstrate_hunter_experience():
    """Show the difference between generic planning and contextual guidance"""
    
    print("🏹 REAL-TIME HUNTER DECISION DEMO")
    print("=" * 80)
    
    # Current scenario: 7:19 PM on September 3rd in Vermont
    current_time = datetime(2025, 9, 3, 19, 19, 0)
    
    print(f"📍 SCENARIO: Hunter in Vermont at {current_time.strftime('%I:%M %p')}")
    print(f"🌄 Legal shooting light ends at approximately 7:56 PM")
    print(f"⏰ Time remaining: ~37 minutes")
    print()
    
    # Show the time-context analysis
    context = analyze_hunting_context(current_time)
    
    print("🎯 CONTEXT-AWARE GUIDANCE:")
    print("-" * 40)
    print(f"📊 Situation: {context['context'].value.replace('_', ' ').title()}")
    print(f"🎬 Action: {context['action'].value.replace('_', ' ').title()}")
    print(f"📋 Primary: {context['recommendations']['primary']}")
    print(f"📝 Details: {context['recommendations']['secondary']}")
    print()
    
    print("🎯 IMMEDIATE ACTIONS:")
    for i, action in enumerate(context['recommendations']['specific_actions'], 1):
        print(f"   {i}. {action}")
    print()
    
    # Show what the API provides
    print("🌐 FULL API RESPONSE (what hunter actually receives):")
    print("-" * 40)
    
    try:
        # Make API call
        url = "http://localhost:8000/analyze-prediction-detailed"
        payload = {
            "lat": 43.3140,
            "lon": -73.2306,
            "date_time": current_time.isoformat(),
            "season": "fall",
            "hunting_pressure": "low"
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            
            if 'prediction' in result and 'hunting_context' in result['prediction']:
                hunt_context = result['prediction']['hunting_context']
                
                print(f"🔍 Detection: {hunt_context['recommendations']['primary']}")
                print(f"📋 Guidance: {hunt_context['recommendations']['secondary']}")
                print(f"⏰ Timing: {hunt_context['recommendations']['timing']}")
                print()
                
                print("📱 HUNTER'S SMARTPHONE DISPLAY:")
                print("┌" + "─" * 50 + "┐")
                print(f"│ 🦌 Deer Prediction - {current_time.strftime('%I:%M %p')}           │")
                print("├" + "─" * 50 + "┤")
                
                if hunt_context['current_status']['time_remaining_minutes'] > 10:
                    print(f"│ ⚡ ACTIVE HUNT - {hunt_context['current_status']['time_remaining_minutes']:.0f} min remaining    │")
                    print("│ 🦌 EVENING MOVEMENT EXPECTED                   │")
                    print("│                                                │")
                    print("│ ACTIONS:                                       │")
                    print("│ • Watch travel corridors                      │")
                    print("│ • Focus on field edges                        │")
                    print("│ • Stay alert for feeding activity             │")
                elif hunt_context['current_status']['time_remaining_minutes'] > 0:
                    print(f"│ 🛑 STAY PUT - {hunt_context['current_status']['time_remaining_minutes']:.0f} min until dark          │")
                    print("│ ⚠️  Movement will spook deer now               │")
                    print("│                                                │")
                    print("│ ACTIONS:                                       │")
                    print("│ • Remain completely still                     │")
                    print("│ • Observe movement patterns                   │")
                    print("│ • Wait 30+ min after dark to move             │")
                else:
                    print("│ 🌙 HUNT OVER - Quiet exit mode                │")
                    print("│ ⚠️  Legal light has ended                      │")
                    print("│                                                │")
                    print("│ ACTIONS:                                       │")
                    print("│ • Wait 30+ minutes before moving              │")
                    print("│ • Use red headlamp for navigation             │")
                    print("│ • Plan tomorrow's strategy                     │")
                
                print("└" + "─" * 50 + "┘")
                print()
                
                print("✅ SUCCESS: Hunter receives actionable, time-appropriate guidance!")
                
            else:
                print("❌ No context information - would show generic planning advice")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
    
    print()
    print("🔄 COMPARISON: Before vs After")
    print("-" * 40)
    print("❌ BEFORE: 'Morning thermal period (5:30-8:00 AM)' recommendations")
    print("   ↳ Useless when hunt ends in 37 minutes")
    print()
    print("✅ AFTER: Real-time context with immediate actions")
    print("   ↳ Tells hunter exactly what to do RIGHT NOW")
    print()
    print("🎯 IMPACT: GPS-style real-time decision support for hunters!")

if __name__ == "__main__":
    demonstrate_hunter_experience()
