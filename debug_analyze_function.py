#!/usr/bin/env python3

from datetime import datetime
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from hunting_context_analyzer import analyze_hunting_context

# Test with the exact current time
now = datetime.now()
print(f"=== TESTING analyze_hunting_context DIRECTLY ===")
print(f"Input datetime: {now}")

# Call the exact function that the API calls
result = analyze_hunting_context(now)

print(f"\n🔍 RESULT:")
print(f"Context: {result['context']}")
print(f"Action: {result['action']}")
print(f"Primary recommendation: {result['recommendations']['primary']}")
print(f"Time remaining: {result['current_status']['time_remaining_minutes']} minutes")
print(f"Legal hours: {result['current_status']['legal_hunting_hours']}")

print(f"\n📊 DETAILED STATUS:")
for key, value in result['current_status'].items():
    print(f"  {key}: {value}")

# Check if this matches what the API returned
if result['context'].value == 'post_hunt':
    print(f"\n🚨 BUG CONFIRMED: analyze_hunting_context returns post_hunt")
    print(f"   But time calculation shows this should be active_hunt")
else:
    print(f"\n❓ MYSTERY: analyze_hunting_context works correctly")
    print(f"   But API returns different result - caching issue?")
