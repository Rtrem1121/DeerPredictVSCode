#!/usr/bin/env python3

from datetime import datetime
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from hunting_context_analyzer import analyze_hunting_context, create_time_aware_prediction_context

# Test the exact flow that happens in production
print("=== PRODUCTION FLOW TEST ===")

# Simulate exactly what happens in prediction_service.py
current_time = datetime.now()
print(f"Current system time: {current_time}")
print(f"Time only: {current_time.time()}")
print(f"Date: {current_time.date()}")
print(f"Month: {current_time.month}")

# Call the exact function that production uses
context_analysis = analyze_hunting_context(current_time)

print(f"\n=== CONTEXT ANALYSIS RESULT ===")
print(f"Context: {context_analysis['context']}")
print(f"Action: {context_analysis['action']}")
print(f"Primary recommendation: {context_analysis['recommendations']['primary']}")
print(f"Time remaining: {context_analysis['current_status']['time_remaining_minutes']} minutes")

# Test with a specific 5:42 PM time for today
test_time_542pm = datetime.combine(current_time.date(), datetime.strptime("17:42", "%H:%M").time())
print(f"\n=== TESTING 5:42 PM SPECIFICALLY ===")
print(f"Test time: {test_time_542pm}")

context_542 = analyze_hunting_context(test_time_542pm)
print(f"Context for 5:42 PM: {context_542['context']}")
print(f"Action for 5:42 PM: {context_542['action']}")
print(f"Primary recommendation: {context_542['recommendations']['primary']}")

# Test the full create_time_aware_prediction_context flow
dummy_prediction = {
    'timestamp': 'test',
    'mature_buck_analysis': {
        'stand_recommendations': []
    }
}

print(f"\n=== TESTING FULL CONTEXT CREATION ===")
result = create_time_aware_prediction_context(dummy_prediction, test_time_542pm)
print(f"Context summary: {result['context_summary']}")
