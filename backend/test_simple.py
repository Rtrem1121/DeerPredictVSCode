#!/usr/bin/env python3
"""
Simple test to check what's causing the backend crash
"""
import sys
import traceback

print("Starting simple test...")

try:
    print("1. Testing core import...")
    import core
    print("✅ Core imported successfully")
    
    print("2. Testing core.get_weather_data function...")
    # This should work without making actual API calls if it fails quickly
    result = core.get_weather_data(44.2601, -72.5806)
    print(f"✅ Weather data function works: {type(result)}")
    
except Exception as e:
    print(f"❌ Error in core functions: {e}")
    traceback.print_exc()

try:
    print("3. Testing core.get_vegetation_grid_from_osm function...")
    # This might timeout but shouldn't crash
    result = core.get_vegetation_grid_from_osm(44.2601, -72.5806)
    print(f"✅ Vegetation function works: {result.shape}")
    
except Exception as e:
    print(f"❌ Error in vegetation function: {e}")
    traceback.print_exc()

try:
    print("4. Testing main import...")
    import main
    print("✅ Main imported successfully")
    
except Exception as e:
    print(f"❌ Error in main import: {e}")
    traceback.print_exc()

print("Test complete!")
