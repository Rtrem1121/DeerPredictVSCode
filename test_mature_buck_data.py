#!/usr/bin/env python3

import sys
sys.path.append('./backend')
from main import generate_mature_buck_predictions
import backend.core as core

# Test location
lat, lon = 44.26, -72.58

# Get terrain features
elevation_grid = core.get_real_elevation_grid(lat, lon)
vegetation_grid = core.get_vegetation_grid_from_osm(lat, lon)
terrain_features = core.analyze_terrain_and_vegetation(elevation_grid, vegetation_grid)

# Generate mock weather data
weather_data = {'temperature': 45, 'wind_speed': 8, 'wind_direction': 270, 'pressure': 29.8}

# Generate mature buck predictions
mature_buck_data = generate_mature_buck_predictions(lat, lon, terrain_features, weather_data, 'rut', 7)

print('🦌 MATURE BUCK DATA STRUCTURE:')
print('=' * 50)

for key, value in mature_buck_data.items():
    print(f'{key}: {type(value)}')
    if isinstance(value, dict):
        print(f'  Keys: {list(value.keys())}')
    elif isinstance(value, list):
        print(f'  Length: {len(value)}')
        if len(value) > 0:
            print(f'  First item type: {type(value[0])}')
    print()

# Show stand recommendations details
if 'stand_recommendations' in mature_buck_data:
    print('🏹 STAND RECOMMENDATIONS SAMPLE:')
    stands = mature_buck_data['stand_recommendations']
    for i, stand in enumerate(stands[:2]):
        print(f'Stand {i+1}:')
        print(f'  Type: {stand.get("type", "N/A")}')
        print(f'  Confidence: {stand.get("confidence", "N/A")}')
        print()

# Show movement prediction details
if 'movement_prediction' in mature_buck_data:
    movement = mature_buck_data['movement_prediction']
    print('🚶 MOVEMENT PREDICTION SAMPLE:')
    print(f'  Movement Probability: {movement.get("movement_probability", "N/A")}%')
    print(f'  Confidence Score: {movement.get("confidence_score", "N/A")}%')
    if 'behavioral_notes' in movement:
        print(f'  Behavioral Notes: {len(movement["behavioral_notes"])} notes')
        for note in movement['behavioral_notes'][:3]:
            print(f'    - {note}')
    print()

# Show terrain scores
if 'terrain_scores' in mature_buck_data:
    scores = mature_buck_data['terrain_scores']
    print('⛰️ TERRAIN SCORES:')
    for key, value in scores.items():
        print(f'  {key}: {value}')
    print()
