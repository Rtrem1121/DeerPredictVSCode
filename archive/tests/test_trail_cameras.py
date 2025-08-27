#!/usr/bin/env python3
"""Test trail camera placement recommendations"""

import requests
import json

# Test trail camera placement for mature buck during rut season
response = requests.post('http://localhost:8000/trail-cameras', 
                        json={'lat': 44.26, 'lon': -72.58, 'season': 'rut', 'target_buck_age': 'mature'})

if response.status_code == 200:
    data = response.json()
    camera_count = data.get('placement_count', 0)
    top_placement = data.get('setup_priority', 'Unknown')
    insights = data.get('insights', [])
    
    print('🎥 TRAIL CAMERA RECOMMENDATIONS for MATURE BUCK')
    print('📍 Location: Vermont (Forested Area)')
    print(f'📹 Camera placements: {camera_count}')
    print(f'🎯 Top recommendation: {top_placement}')
    print('💡 Key insights:')
    for insight in insights[:3]:
        print(f'   - {insight}')
        
    # Get details of first camera placement
    if 'camera_placements' in data and data['camera_placements']['features']:
        camera = data['camera_placements']['features'][0]['properties']
        print('🔧 Setup details:')
        print(f'   - Height: {camera.get("setup_height", "Unknown")}')
        print(f'   - Angle: {camera.get("setup_angle", "Unknown")}')
        print(f'   - Expected: {camera.get("expected_photos", "Unknown")}')
        print(f'   - Confidence: {camera.get("confidence", 0):.1f}%')
        
        print('⏰ Best times:')
        best_times = camera.get("best_times", [])
        for time in best_times[:2]:
            print(f'   - {time}')
            
        print('📝 Setup notes:')
        setup_notes = camera.get("setup_notes", [])
        for note in setup_notes[:2]:
            print(f'   - {note}')
else:
    print(f'Error: {response.status_code} - {response.text}')
