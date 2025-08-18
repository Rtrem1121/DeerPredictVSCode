#!/usr/bin/env python3
"""
Phase 3: Integration Issue Debugging
"""

def test_current_integration():
    """Test exactly how VegetationAnalyzer fails"""
    
    print("=== INTEGRATION DEBUGGING ===\n")
    
    # Test 1: Check gee_setup singleton
    print("🧪 Test 1: gee_setup singleton status")
    try:
        from gee_docker_setup import gee_setup
        print(f"✅ gee_setup imported successfully")
        print(f"   - initialized: {gee_setup.initialized}")
        print(f"   - available: {gee_setup.available}")
        print(f"   - is_available(): {gee_setup.is_available()}")
    except Exception as e:
        print(f"❌ gee_setup import error: {e}")
        return
    
    # Test 2: Force initialize
    print("\n🧪 Test 2: Force gee_setup.initialize()")
    try:
        result = gee_setup.initialize()
        print(f"   - initialize() result: {result}")
        print(f"   - after init - available: {gee_setup.available}")
    except Exception as e:
        print(f"❌ gee_setup initialize error: {e}")
    
    # Test 3: VegetationAnalyzer with forced GEE
    print("\n🧪 Test 3: VegetationAnalyzer with manual GEE init")
    try:
        import ee
        import os
        
        # Manual init like our working test
        credentials_path = '/app/credentials/gee-service-account.json'
        credentials = ee.ServiceAccountCredentials(None, credentials_path)
        ee.Initialize(credentials)
        
        from backend.vegetation_analyzer import VegetationAnalyzer
        analyzer = VegetationAnalyzer()
        analyzer.available = True  # Force enable
        analyzer.initialized = True
        
        print("   - Starting vegetation analysis...")
        result = analyzer.analyze_hunting_area(44.26, -72.58, 2.0)
        
        print(f"   - Analysis completed")
        print(f"   - Has ndvi_analysis: {'ndvi_analysis' in result}")
        print(f"   - Data source: {result.get('analysis_metadata', {}).get('data_source', 'unknown')}")
        
        if 'ndvi_analysis' in result:
            ndvi_val = result['ndvi_analysis'].get('ndvi_value')
            print(f"   - NDVI value: {ndvi_val}")
        
    except Exception as e:
        print(f"❌ VegetationAnalyzer test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_current_integration()
