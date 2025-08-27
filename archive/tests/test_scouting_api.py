#!/usr/bin/env python3
"""
Test script for scouting API endpoints
"""

import requests
import json
from datetime import datetime

def test_scouting_api():
    print('✅ Testing scouting API endpoints...')

    # Test adding a scouting observation
    obs_data = {
        'lat': 44.26639,
        'lon': -72.58133,
        'observation_type': 'Fresh Scrape',
        'scrape_details': {
            'size': 'Large',
            'freshness': 'Very Fresh', 
            'licking_branch': True,
            'multiple_scrapes': False
        },
        'notes': 'Large scrape with very active licking branch, multiple deer tracks around area',
        'confidence': 9,
        'timestamp': datetime.now().isoformat()
    }

    try:
        print('Testing add observation endpoint...')
        response = requests.post('http://localhost:8000/scouting/add_observation', json=obs_data)
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Added observation: {result["observation_id"]}')
            print(f'✅ Confidence boost: {result["confidence_boost"]}%')
            observation_id = result["observation_id"]
        else:
            print(f'❌ Error adding observation: {response.status_code} - {response.text}')
            return
            
        # Test getting observations
        print('\nTesting get observations endpoint...')
        response = requests.get(f'http://localhost:8000/scouting/observations?lat=44.26639&lon=-72.58133&radius_miles=1.0')
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Retrieved {result["total_count"]} observations')
        else:
            print(f'❌ Error getting observations: {response.status_code} - {response.text}')
            
        # Test getting observation types
        print('\nTesting get observation types endpoint...')
        response = requests.get('http://localhost:8000/scouting/types')
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Available observation types: {result["total_types"]}')
            for obs_type in result["observation_types"][:3]:  # Show first 3
                print(f'  - {obs_type["type"]}: {obs_type["base_boost"]}% boost, {obs_type["influence_radius_yards"]} yard radius')
        else:
            print(f'❌ Error getting types: {response.status_code} - {response.text}')
            
        # Test getting analytics
        print('\nTesting analytics endpoint...')
        response = requests.get(f'http://localhost:8000/scouting/analytics?lat=44.26639&lon=-72.58133&radius_miles=5.0')
        if response.status_code == 200:
            result = response.json()
            analytics = result["basic_analytics"]
            print(f'✅ Analytics: {analytics["total_observations"]} total observations')
            print(f'✅ Average confidence: {analytics["average_confidence"]:.1f}/10')
            if analytics["observations_by_type"]:
                print(f'✅ By type: {analytics["observations_by_type"]}')
        else:
            print(f'❌ Error getting analytics: {response.status_code} - {response.text}')
        
        print('\n🎯 All scouting API endpoints working correctly!')
        
    except Exception as e:
        print(f'❌ Connection error: {e}')
        print('Make sure the backend is running on http://localhost:8000')

if __name__ == "__main__":
    test_scouting_api()
