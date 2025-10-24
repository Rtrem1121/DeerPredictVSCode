#!/usr/bin/env python3
"""
Test prediction with detailed logging to see where GEE queries fail
"""
import asyncio
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

from backend.services.prediction_service import PredictionService

async def test_single_prediction():
    """Test one prediction with full logging"""
    service = PredictionService()
    
    print("=" * 80)
    print("TESTING PREDICTION WITH FULL LOGGING")
    print("=" * 80)
    
    # Test Vermont location
    lat, lon = 44.5, -72.5
    print(f"\nTesting: ({lat}, {lon})")
    print(f"   Watch for GEE authentication and query messages...\n")
    
    result = await service.predict(
        lat=lat,
        lon=lon,
        time_of_day=6,
        season='fall',
        hunting_pressure='medium'
    )
    
    # Check what data sources were used
    gee_data = result.get('gee_data', {})
    
    print("\n" + "=" * 80)
    print("PREDICTION DATA SOURCES")
    print("=" * 80)
    print(f"GEE Data Source: {gee_data.get('api_source', 'UNKNOWN')}")
    print(f"Canopy Coverage: {gee_data.get('canopy_coverage', 0):.1%}")
    print(f"Canopy Source: {gee_data.get('canopy_data_source', 'UNKNOWN')}")
    print(f"Slope: {gee_data.get('slope', 0):.1f}°")
    print(f"Aspect: {gee_data.get('aspect', 0):.1f}°")
    print(f"Elevation: {gee_data.get('elevation', 0):.0f}m")
    
    # Check if real data was used
    using_real_data = (
        gee_data.get('api_source') != 'fallback' and
        gee_data.get('canopy_data_source') not in ['estimated', 'fallback']
    )
    
    print("\n" + "=" * 80)
    if using_real_data:
        print("SUCCESS: USING REAL SATELLITE/TERRAIN DATA")
    else:
        print("PROBLEM: USING FALLBACK/ESTIMATED DATA (This causes uniform patterns!)")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_single_prediction())
