#!/usr/bin/env python3

from backend.gpx_parser import GPXParser
import json

def test_real_gpx():
    parser = GPXParser()
    
    # Read the GPX file
    with open('hunting-waypoints.gpx', 'r', encoding='utf-8') as f:
        content = f.read()
    
    result = parser.parse_gpx_file(content)
    
    waypoints = result.get('waypoints', [])
    total_waypoints = result.get('total_waypoints', 0)
    
    print(f'Parsed {len(waypoints)} waypoints from GPX file')
    
    # Convert to scouting observations
    observations = parser.convert_to_scouting_observations(waypoints)
    
    print(f'Found {len(observations)} hunting observations')
    print(f'Total waypoints in file: {len(waypoints)}')
    print(f'Skipped: {len(waypoints) - len(observations)}')
    print('\nSample observations:')
    
    for i, obs in enumerate(observations[:10]):
        print(f'  {i+1:2d}. "{obs.notes}" -> Type: {obs.observation_type}, Confidence: {obs.confidence:.2f}')
    
    # Check why some might be skipped
    print(f'\nFiltering details:')
    print(f'Total waypoints in GPX: {len(waypoints)}')
    print(f'Valid hunting observations: {len(observations)}')
    print(f'Success rate: {len(observations)/len(waypoints)*100:.1f}%')
    
    return observations

if __name__ == "__main__":
    test_real_gpx()
