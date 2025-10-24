#!/usr/bin/env python3
"""
Quick test to verify prediction coordinates are actually being used.
"""
import asyncio
import sys
from backend.services.prediction_service import PredictionService

async def test_coordinates():
    """Test 3 different locations and check if results differ"""
    service = PredictionService()
    
    test_locations = [
        {"name": "Vermont 1", "lat": 44.5, "lon": -72.5},
        {"name": "Vermont 2 (50mi away)", "lat": 45.0, "lon": -73.0},
        {"name": "Vermont 3 (100mi away)", "lat": 43.5, "lon": -71.5},
    ]
    
    results = []
    
    print("=" * 80)
    print("COORDINATE VARIATION TEST")
    print("=" * 80)
    
    for loc in test_locations:
        print(f"\n🎯 Testing {loc['name']}: ({loc['lat']}, {loc['lon']})")
        
        result = await service.predict(
            lat=loc['lat'],
            lon=loc['lon'],
            time_of_day=6,
            season='fall',
            hunting_pressure='medium'
        )
        
        # Extract first bedding zone coordinates
        bedding_zones = result.get('bedding_zones', {}).get('features', [])
        if bedding_zones:
            first_zone = bedding_zones[0]
            coords = first_zone['geometry']['coordinates']
            print(f"   First bedding zone: [{coords[0]:.4f}, {coords[1]:.4f}]")
            print(f"   Slope: {first_zone['properties'].get('slope', 'N/A')}")
            print(f"   Type: {first_zone['properties'].get('bedding_type', 'N/A')}")
            
            results.append({
                'location': loc['name'],
                'input': (loc['lat'], loc['lon']),
                'bedding_output': (coords[0], coords[1]),
                'slope': first_zone['properties'].get('slope'),
                'type': first_zone['properties'].get('bedding_type')
            })
        else:
            print(f"   ❌ NO BEDDING ZONES RETURNED")
            results.append({
                'location': loc['name'],
                'input': (loc['lat'], loc['lon']),
                'bedding_output': None,
                'slope': None,
                'type': None
            })
    
    # Check if all outputs are identical (the bug!)
    print("\n" + "=" * 80)
    print("RESULTS COMPARISON")
    print("=" * 80)
    
    if len(results) >= 2:
        coords_match = all(
            r['bedding_output'] == results[0]['bedding_output'] 
            for r in results[1:]
        )
        
        if coords_match:
            print("❌ BUG CONFIRMED: All 3 different inputs produced IDENTICAL bedding coordinates!")
            print(f"   All bedding zones at: {results[0]['bedding_output']}")
        else:
            print("✅ WORKING: Different inputs produced different bedding coordinates")
            for r in results:
                print(f"   {r['location']}: {r['bedding_output']}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_coordinates())
