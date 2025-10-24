"""
Simple test to check what the predictor actually returns
"""
import sys
sys.path.insert(0, 'c:/Users/Rich/deer_pred_app')

from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor

predictor = EnhancedBeddingZonePredictor()
result = predictor.run_enhanced_biological_analysis(
    lat=44.5,
    lon=-72.5,
    time_of_day=6,
    season='fall',
    hunting_pressure='medium'
)

bedding_zones = result.get('bedding_zones', {})
features = bedding_zones.get('features', [])
properties = bedding_zones.get('properties', {})

print(f"\nBedding Zones Structure:")
print(f"  Type: {bedding_zones.get('type')}")
print(f"  Feature count: {len(features)}")
print(f"  Properties keys: {list(properties.keys())}")

if 'search_method' in properties:
    print(f"  Search method: {properties['search_method']}")
if 'enhancement_version' in properties:
    print(f"  Version: {properties['enhancement_version']}")
    
print(f"\nFeatures:")
for i, feature in enumerate(features[:3]):
    coords = feature['geometry']['coordinates']
    props = feature['properties']
    print(f"\n  Zone {i+1}:")
    print(f"    Coords: {coords}")
    print(f"    ID: {props.get('id', 'N/A')}")
    print(f"    Type: {props.get('type', 'N/A')}")
    print(f"    Bedding type: {props.get('bedding_type', 'N/A')}")
