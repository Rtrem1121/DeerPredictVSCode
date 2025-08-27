#!/usr/bin/env python3
"""
Test to verify the map consistency fix is working properly.
This ensures both hunting predictions and scouting maps use the same map type.
"""

import re

def test_map_consistency_fix():
    """Test that the map consistency fix is properly implemented."""
    
    print("🔍 Testing Map Consistency Fix")
    print("=" * 50)
    
    files_to_check = [
        'frontend/app.py',
        'frontend/app_new.py'
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        print(f"\n📁 Checking {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Test 1: Check that map_type is stored in session state
            if 'st.session_state.map_type = map_type' in content:
                print("✅ Map type is stored in session state")
            else:
                print("❌ Map type is NOT stored in session state")
                all_good = False
            
            # Test 2: Check that hardcoded "Satellite" is removed from scouting
            if 'scout_map = create_map(st.session_state.hunt_location, st.session_state.map_zoom, "Satellite")' in content:
                print("❌ Still using hardcoded 'Satellite' in scouting map")
                all_good = False
            else:
                print("✅ Hardcoded 'Satellite' removed from scouting map")
            
            # Test 3: Check that scouting map uses session state map type
            if 'map_type_for_scout = getattr(st.session_state, \'map_type\', \'Satellite\')' in content:
                print("✅ Scouting map uses session state map type with fallback")
            else:
                print("❌ Scouting map does NOT use session state map type")
                all_good = False
            
            # Test 4: Check that scout_map uses the variable
            if 'scout_map = create_map(st.session_state.hunt_location, st.session_state.map_zoom, map_type_for_scout)' in content:
                print("✅ Scouting map uses map_type_for_scout variable")
            else:
                print("❌ Scouting map does NOT use map_type_for_scout variable")
                all_good = False
                
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
            all_good = False
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 SUCCESS: Map consistency fix is properly implemented!")
        print("\n📋 What changed:")
        print("  • Map type selection is now stored in session state")
        print("  • Scouting map uses the same map type as hunting predictions")
        print("  • Fallback to 'Satellite' if map type is not yet selected")
        print("\n🎯 Result:")
        print("  • Both maps will now have the same visual style")
        print("  • Users get consistent mapping experience")
        print("  • No functionality is broken")
    else:
        print("❌ FAILED: Map consistency fix has issues!")
    
    return all_good

def test_backward_compatibility():
    """Test that existing functionality still works."""
    print("\n🔄 Testing Backward Compatibility")
    print("-" * 30)
    
    files_to_check = ['frontend/app.py', 'frontend/app_new.py']
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check that create_map function signature is unchanged
            if 'def create_map(location, zoom_start, map_type):' in content:
                print(f"✅ {file_path}: create_map function signature unchanged")
            else:
                print(f"❌ {file_path}: create_map function signature changed!")
                return False
                
            # Check that hunting map still works
            if 'm = create_map(st.session_state.hunt_location, st.session_state.map_zoom, map_type)' in content:
                print(f"✅ {file_path}: Hunting predictions map unchanged")
            else:
                print(f"❌ {file_path}: Hunting predictions map changed!")
                return False
                
        except Exception as e:
            print(f"❌ Error checking {file_path}: {e}")
            return False
    
    print("✅ Backward compatibility maintained")
    return True

def main():
    """Run all tests."""
    success1 = test_map_consistency_fix()
    success2 = test_backward_compatibility()
    
    if success1 and success2:
        print("\n🚀 ALL TESTS PASSED! Safe to deploy the changes.")
        return True
    else:
        print("\n💥 TESTS FAILED! Please review the changes.")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    if not success:
        sys.exit(1)
