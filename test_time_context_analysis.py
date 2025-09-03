#!/usr/bin/env python3
"""
Test Time-Context Aware Predictions

Verifies that the prediction system provides contextually appropriate 
recommendations based on current time, rather than generic planning advice.
"""

import requests
from datetime import datetime, time
from backend.hunting_context_analyzer import analyze_hunting_context, HuntingContext, ActionContext

def test_evening_context_analysis():
    """Test the hunting context analysis for 7:19 PM on September 3rd"""
    
    print("🕰️ TESTING TIME-CONTEXT ANALYSIS")
    print("=" * 60)
    
    # Test current time: 7:19 PM on September 3rd, 2025
    test_time = datetime(2025, 9, 3, 19, 19, 0)
    
    print(f"📅 Test Scenario: {test_time.strftime('%B %d, %Y at %I:%M %p')}")
    print(f"🌍 Location: Vermont")
    
    # Analyze hunting context
    context = analyze_hunting_context(test_time)
    
    print(f"\n🎯 CONTEXT ANALYSIS:")
    print(f"   Hunting Context: {context['context'].value}")
    print(f"   Recommended Action: {context['action'].value}")
    print(f"   Legal Light: {context['legal_hours']['earliest']} - {context['legal_hours']['latest']}")
    print(f"   Currently Legal: {context['current_status']['is_legal_light']}")
    print(f"   Time Remaining: {context['current_status']['time_remaining_minutes']:.1f} minutes")
    
    print(f"\n📋 RECOMMENDATIONS:")
    print(f"   Primary: {context['recommendations']['primary']}")
    print(f"   Secondary: {context['recommendations']['secondary']}")
    print(f"   Timing: {context['recommendations']['timing']}")
    
    print(f"\n🎯 SPECIFIC ACTIONS:")
    for i, action in enumerate(context['recommendations']['specific_actions'], 1):
        print(f"   {i}. {action}")
    
    # Verify this is appropriate for the situation
    expected_context = HuntingContext.POST_HUNT
    expected_action = ActionContext.PACK_OUT
    
    print(f"\n✅ VALIDATION:")
    print(f"   Expected Context: {expected_context.value} - {'✅' if context['context'] == expected_context else '❌'}")
    print(f"   Expected Action: {expected_action.value} - {'✅' if context['action'] == expected_action else '❌'}")
    
    return context

def test_api_with_context():
    """Test the API to ensure it provides time-appropriate recommendations"""
    
    print(f"\n🌐 TESTING API INTEGRATION")
    print("=" * 60)
    
    url = "http://localhost:8000/analyze-prediction-detailed"
    payload = {
        "lat": 43.3140,
        "lon": -73.2306,
        "date_time": "2025-09-03T19:19:00",
        "time_of_day": 19,
        "season": "fall",
        "hunting_pressure": "low"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            
            # Check for context information
            if 'prediction' in result and 'hunting_context' in result['prediction']:
                context_data = result['prediction']['hunting_context']
                
                print(f"📊 API CONTEXT RESULTS:")
                print(f"   Situation: {context_data.get('context', 'unknown')}")
                print(f"   Action: {context_data.get('action', 'unknown')}")
                print(f"   Primary Guidance: {context_data['recommendations']['primary']}")
                print(f"   Time Remaining: {context_data['current_status']['time_remaining_minutes']:.1f} min")
                
                # Check if we got appropriate evening recommendations
                primary_guidance = context_data['recommendations']['primary']
                if "HUNT OVER" in primary_guidance or "STAY PUT" in primary_guidance:
                    print(f"   ✅ APPROPRIATE: Evening context correctly detected")
                else:
                    print(f"   ❌ PROBLEM: Generic planning advice when hunt is over")
                    
            else:
                print(f"   ❌ NO CONTEXT: API did not include hunting context analysis")
                
            # Check for context override
            if result['prediction'].get('context_override'):
                print(f"   ✅ CONTEXT OVERRIDE: Time-aware modifications applied")
            else:
                print(f"   ❌ NO OVERRIDE: Generic prediction without time context")
                
        else:
            print(f"   ❌ API ERROR: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ CONNECTION ERROR: {e}")

def test_different_times():
    """Test various times to ensure appropriate context switching"""
    
    print(f"\n⏰ TESTING DIFFERENT TIME SCENARIOS")
    print("=" * 60)
    
    test_scenarios = [
        (datetime(2025, 9, 3, 5, 30), "Dawn Hunt Start", "Should recommend active hunting"),
        (datetime(2025, 9, 3, 12, 0), "Midday", "Should recommend scouting/observation"),
        (datetime(2025, 9, 3, 17, 30), "Evening Hunt", "Should recommend active hunting"),
        (datetime(2025, 9, 3, 19, 15), "Late Evening", "Should recommend staying put"),
        (datetime(2025, 9, 3, 20, 0), "After Dark", "Should recommend packing out"),
        (datetime(2025, 9, 3, 22, 0), "Night", "Should recommend planning tomorrow")
    ]
    
    for test_time, scenario, expected in test_scenarios:
        context = analyze_hunting_context(test_time)
        print(f"🕐 {scenario} ({test_time.strftime('%H:%M')})")
        print(f"   Context: {context['context'].value}")
        print(f"   Action: {context['action'].value}")
        print(f"   Guidance: {context['recommendations']['primary']}")
        print(f"   Expected: {expected}")
        print()

if __name__ == "__main__":
    # Test context analysis
    test_evening_context_analysis()
    
    # Test API integration
    test_api_with_context()
    
    # Test different scenarios
    test_different_times()
    
    print("\n🎯 SUMMARY")
    print("=" * 60)
    print("The system should now provide time-appropriate recommendations:")
    print("• At 7:19 PM: 'HUNT OVER' or 'STAY PUT' guidance")
    print("• Not generic morning planning advice")
    print("• Context-specific actions based on legal light")
    print("• Real-time decision support for hunters in the field")
