#!/usr/bin/env python3

import requests
import json

def test_api_import():
    # Read GPX file
    with open('hunting-waypoints.gpx', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Test API import in preview mode
    response = requests.post('http://localhost:8000/scouting/import_gpx', 
                           json={'gpx_content': content, 'preview_mode': True})
    
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        result = response.json()
        print('API Response:')
        print(f'  Status: {result["status"]}')
        print(f'  Message: {result["message"]}')
        print(f'  Total waypoints: {result["total_waypoints"]}')
        print(f'  Imported observations: {result["imported_observations"]}')
        print(f'  Skipped waypoints: {result["skipped_waypoints"]}')
        print(f'  Errors: {result.get("errors", [])}')
        
        if result["imported_observations"] > 0:
            print("✅ SUCCESS: GPX import working!")
        else:
            print("❌ ISSUE: No observations imported")
    else:
        print('❌ API Error:', response.text)

if __name__ == "__main__":
    test_api_import()
