#!/usr/bin/env python3
"""
Test script to verify map consistency between hunting predictions and scouting data input.
This ensures we don't break the existing functionality when making the change.
"""

import sys
import os
sys.path.append('.')

def test_map_creation():
    """Test that map creation works with different map types."""
    try:
        # Import the map creation function
        from frontend.enhanced_ui import create_map
        
        # Test coordinates (using a known good location)
        test_lat, test_lon = 44.2619, -72.5806  # Vermont coordinates
        test_zoom = 13
        
        # Test different map types
        map_types = ["OpenStreetMap", "Satellite", "Terrain"]
        
        print("🗺️  Testing map creation with different types...")
        
        for map_type in map_types:
            try:
                test_map = create_map([test_lat, test_lon], test_zoom, map_type)
                print(f"✅ {map_type} map created successfully")
            except Exception as e:
                print(f"❌ {map_type} map failed: {e}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import create_map function: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_current_implementation():
    """Verify the current map implementation in the frontend."""
    try:
        from frontend.enhanced_ui import st
        print("🔍 Checking current map implementation...")
        
        # Read the current frontend file to verify structure
        with open('frontend/enhanced_ui.py', 'r') as f:
            content = f.read()
            
        # Check for map-related code
        if 'create_map' in content:
            print("✅ create_map function found")
        else:
            print("❌ create_map function not found")
            return False
            
        if 'map_type' in content:
            print("✅ map_type parameter usage found")
        else:
            print("❌ map_type parameter not found")
            return False
            
        # Check for scouting map section
        if '"Satellite"' in content and 'scout_map' in content:
            print("✅ Current scouting map (hardcoded Satellite) found")
        else:
            print("❌ Current scouting map implementation not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error verifying implementation: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Starting Map Consistency Test")
    print("=" * 50)
    
    # Test 1: Verify current implementation
    print("\n📋 Test 1: Verifying current implementation...")
    if not verify_current_implementation():
        print("❌ Current implementation verification failed")
        return False
    
    # Test 2: Test map creation
    print("\n🗺️  Test 2: Testing map creation...")
    if not test_map_creation():
        print("❌ Map creation test failed")
        return False
    
    print("\n✅ All tests passed! Safe to proceed with map consistency change.")
    print("\n📝 Recommended change:")
    print("   Replace hardcoded 'Satellite' in scouting map with st.session_state.map_type")
    print("   This will make scouting map use the same type as hunting predictions map.")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
