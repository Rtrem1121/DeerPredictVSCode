import json

with open('test_prediction_response.json') as f:
    data = json.load(f)

print(f"Has 'data': {'data' in data}")
print(f"Has 'optimized_points': {'optimized_points' in data['data']}")

opt = data['data'].get('optimized_points', {})
print(f"Has 'stand_sites': {'stand_sites' in opt}")
print(f"Number of stands: {len(opt.get('stand_sites', []))}")

stands = opt.get('stand_sites', [])
for i, stand in enumerate(stands[:3], 1):
    print(f"\nStand {i}:")
    print(f"  lat: {stand.get('lat')}")
    print(f"  lon: {stand.get('lon')}")
    print(f"  score: {stand.get('score')}")
    print(f"  strategy: {stand.get('strategy')}")
