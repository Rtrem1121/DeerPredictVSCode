#!/usr/bin/env python3
"""Check the structure of wind analyses in API response"""

import requests
import json

# Test API call
resp = requests.post('http://localhost:8000/analyze-prediction-detailed', json={
    "lat": 43.3140,
    "lon": -73.2306,
    "date_time": "2025-09-02T18:00:00",
    "time_of_day": 18,
    "season": "fall",
    "hunting_pressure": "low"
})

if resp.status_code == 200:
    result = resp.json()
    print('=== TOP LEVEL KEYS ===')
    for key in result.keys():
        print(f'{key}: {type(result[key])}')
    
    print('\n=== PREDICTION STRUCTURE ===')
    prediction = result.get('prediction', {})
    for key in prediction.keys():
        print(f'prediction.{key}: {type(prediction[key])}')
        if 'wind' in key.lower() and isinstance(prediction[key], list):
            print(f'    Count: {len(prediction[key])}')
    
    print('\n=== MATURE BUCK ANALYSIS ===')
    mba = prediction.get('mature_buck_analysis', {})
    print(f'Type: {type(mba)}')
    if isinstance(mba, dict):
        for key in mba.keys():
            print(f'  mba.{key}: {type(mba[key])}')
            if isinstance(mba[key], list):
                print(f'    Count: {len(mba[key])}')
                if len(mba[key]) > 0 and 'wind' in str(mba[key][0]).lower():
                    print(f'    Sample: {str(mba[key][0])[:100]}...')
                
else:
    print(f'Error: {resp.status_code}')
