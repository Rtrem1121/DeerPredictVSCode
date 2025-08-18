#!/usr/bin/env python3
"""
Google Earth Engine Authorization Test & Real Data Integration

Complete workflow to test GEE authorization and switch from fallback to real satellite data.
"""

import sys
import os
import json
from pathlib import Path

def check_credentials_file():
    """Check if GEE credentials file exists"""
    creds_path = Path("credentials/gee-service-account.json")
    
    print("🔐 Checking GEE Credentials...")
    if creds_path.exists():
        try:
            with open(creds_path, 'r') as f:
                creds = json.load(f)
            
            if creds.get('type') == 'service_account':
                print(f"✅ Valid service account credentials found")
                print(f"   Account: {creds.get('client_email', 'Unknown')}")
                print(f"   Project: {creds.get('project_id', 'Unknown')}")
                return True
            else:
                print("❌ Invalid credentials format")
                return False
                
        except Exception as e:
            print(f"❌ Error reading credentials: {e}")
            return False
    else:
        print("❌ Credentials file not found")
        print(f"   Expected location: {creds_path.absolute()}")
        return False

def test_gee_authentication():
    """Test Google Earth Engine authentication"""
    print("\n🛰️ Testing GEE Authentication...")
    
    try:
        # Set environment variables for this test
        os.environ['GEE_PROJECT_ID'] = 'deer-predict-app'
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(Path("credentials/gee-service-account.json").absolute())
        
        from gee_docker_setup import gee_setup
        
        # Test initialization
        if gee_setup.initialize():
            print("✅ GEE authentication successful!")
            
            # Test basic functionality
            status = gee_setup.get_status()
            print(f"   Project: {status['project_id']}")
            print(f"   Credentials: {'✅' if status['credentials_file_exists'] else '❌'}")
            
            return True
        else:
            print("❌ GEE authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ GEE authentication error: {e}")
        return False

def test_real_vegetation_analysis():
    """Test real vegetation analysis with satellite data"""
    print("\n🌿 Testing Real Vegetation Analysis...")
    
    try:
        from backend.vegetation_analyzer import get_vegetation_analyzer
        
        analyzer = get_vegetation_analyzer()
        
        # Test with Vermont coordinates
        test_lat, test_lon = 44.26, -72.58
        print(f"   Testing location: {test_lat}, {test_lon} (Vermont)")
        
        # Analyze hunting area
        results = analyzer.analyze_hunting_area(test_lat, test_lon, radius_km=1.0)
        
        data_source = results.get('analysis_metadata', {}).get('data_source', 'unknown')
        print(f"   Data source: {data_source}")
        
        if data_source == 'google_earth_engine':
            print("✅ Real satellite data retrieved!")
            
            # Display key metrics
            ndvi = results.get('ndvi_analysis', {})
            if ndvi:
                print(f"   NDVI Mean: {ndvi.get('mean_ndvi', 'N/A'):.3f}")
                print(f"   Vegetation Health: {ndvi.get('health_category', 'N/A')}")
            
            food_sources = results.get('food_sources', {})
            if food_sources:
                print(f"   Food Sources: {len(food_sources.get('features', []))} identified")
            
            return True
        else:
            print("⚠️ Using fallback data - GEE not fully operational")
            return False
            
    except Exception as e:
        print(f"❌ Vegetation analysis test failed: {e}")
        return False

def test_enhanced_predictions():
    """Test enhanced predictions with real satellite data"""
    print("\n🎯 Testing Enhanced Predictions...")
    
    try:
        from backend.enhanced_prediction_engine import EnhancedPredictionEngine
        from datetime import datetime, timezone
        
        engine = EnhancedPredictionEngine()
        
        # Test prediction with real coordinates
        test_lat, test_lon = 44.26, -72.58
        test_date = datetime(2024, 11, 15, 7, 0, tzinfo=timezone.utc)
        
        # Mock weather data for test
        weather_data = {
            'temp': 18,
            'humidity': 65,
            'wind_speed': 8,
            'conditions': 'partly_cloudy'
        }
        
        # Mock terrain data for test
        terrain_features = {
            'elevation_grid': [[100, 110, 120]] * 3,
            'slope_grid': [[5, 10, 15]] * 3
        }
        
        print(f"   Testing enhanced prediction for {test_lat}, {test_lon}")
        
        results = engine.generate_enhanced_prediction(
            test_lat, test_lon, test_date, "rut", weather_data, terrain_features
        )
        
        if 'satellite_enhanced' in results:
            print("✅ Enhanced predictions with satellite data generated!")
            
            # Display enhancement details
            enhancements = results.get('satellite_enhancements', {})
            print(f"   Vegetation accuracy boost: {enhancements.get('vegetation_boost', 0):.1f}%")
            print(f"   Food source confidence: {enhancements.get('food_confidence', 0):.1f}%")
            
            return True
        else:
            print("⚠️ Enhanced predictions generated but without satellite data")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced prediction test failed: {e}")
        return False

def display_integration_status():
    """Display current integration status and next steps"""
    print("\n" + "="*60)
    print("📊 INTEGRATION STATUS SUMMARY")
    print("="*60)
    
    # Run all tests
    tests = [
        ("Credentials File", check_credentials_file),
        ("GEE Authentication", test_gee_authentication),
        ("Real Vegetation Analysis", test_real_vegetation_analysis),
        ("Enhanced Predictions", test_enhanced_predictions)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📈 Overall Status: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 FULL REAL DATA INTEGRATION ACTIVE!")
        print("   Your deer predictions now use live satellite data")
        print("   ✅ Real-time vegetation analysis")
        print("   ✅ Live NDVI calculations") 
        print("   ✅ Current land cover data")
        print("   ✅ Satellite-enhanced accuracy")
    elif passed >= 2:
        print("\n✨ PARTIAL INTEGRATION ACTIVE")
        print("   Some satellite features are working")
        print("   📡 Check failed tests above for issues")
    else:
        print("\n⚠️ FALLBACK MODE ACTIVE")
        print("   Using synthetic data - satellite integration needed")
        
    print("\n🔧 Next Steps:")
    if passed < total:
        print("   1. Complete Google Cloud Setup (see instructions)")
        print("   2. Download service account credentials")
        print("   3. Place credentials in: credentials/gee-service-account.json")
        print("   4. Re-run this test: python test_gee_integration.py")
    else:
        print("   1. ✅ Authorization complete!")
        print("   2. ✅ Real satellite data active!")
        print("   3. 🎯 Ready for enhanced hunting predictions!")

if __name__ == "__main__":
    print("🚀 Google Earth Engine Integration Test")
    print("Testing authorization and real data activation...")
    
    display_integration_status()
