#!/usr/bin/env python3
"""
Google Earth Engine Integration Debugging Plan
==============================================

CURRENT STATUS:
✅ WORKING: Manual GEE calls return real NDVI (0.39)
✅ WORKING: Service account authentication 
✅ WORKING: Core prediction engine
❌ BROKEN: GEE integration in VegetationAnalyzer

DEBUGGING STRATEGY:
1. Isolate GEE functionality from main app
2. Create minimal test cases
3. Fix authentication flow
4. Integrate back safely

ROLLBACK PLAN:
- Keep current working prediction engine intact
- Test GEE fixes in isolation
- Only integrate when confirmed working
"""

import logging
import ee
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GEEDebugger:
    """Isolated Google Earth Engine testing and debugging"""
    
    def __init__(self):
        self.credentials_path = '/app/credentials/gee-service-account.json'
        self.initialized = False
        
    def test_authentication(self):
        """Test 1: Verify GEE authentication works"""
        try:
            if not os.path.exists(self.credentials_path):
                return False, f"Credentials not found: {self.credentials_path}"
                
            credentials = ee.ServiceAccountCredentials(None, self.credentials_path)
            ee.Initialize(credentials)
            
            # Test basic functionality
            test_result = ee.Number(1).getInfo()
            if test_result == 1:
                self.initialized = True
                return True, "Authentication successful"
            else:
                return False, "Test failed"
                
        except Exception as e:
            return False, f"Auth error: {e}"
    
    def test_ndvi_calculation(self, lat=44.26, lon=-72.58):
        """Test 2: Verify NDVI calculation works"""
        if not self.initialized:
            success, msg = self.test_authentication()
            if not success:
                return False, msg
        
        try:
            geometry = ee.Geometry.Point([lon, lat])
            
            # Test with different date ranges
            date_ranges = [
                ('2024-06-01', '2024-08-01'),  # Recent summer
                ('2024-04-01', '2024-10-01'),  # Broader range
                ('2023-06-01', '2023-08-01'),  # Last year
            ]
            
            for start_date, end_date in date_ranges:
                collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
                             .filterBounds(geometry)
                             .filterDate(start_date, end_date)
                             .filter(ee.Filter.lt('CLOUD_COVER', 50)))  # More lenient
                
                size = collection.size().getInfo()
                if size > 0:
                    image = collection.first()
                    ndvi = image.normalizedDifference(['SR_B5', 'SR_B4'])
                    value = ndvi.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=geometry,
                        scale=30,
                        maxPixels=1e9
                    ).getInfo()
                    
                    return True, {
                        'ndvi': value.get('nd'),
                        'date_range': f"{start_date} to {end_date}",
                        'image_count': size
                    }
            
            return False, "No suitable imagery found in any date range"
            
        except Exception as e:
            return False, f"NDVI calculation error: {e}"
    
    def test_vegetation_analyzer_isolation(self):
        """Test 3: Test VegetationAnalyzer components in isolation"""
        # This will be implemented after we identify the specific issue
        pass

def run_isolated_tests():
    """Run all isolation tests"""
    debugger = GEEDebugger()
    
    print("=== GEE ISOLATION TESTS ===")
    
    # Test 1: Authentication
    print("\n🧪 Test 1: Authentication")
    success, msg = debugger.test_authentication()
    print(f"Result: {'✅' if success else '❌'} {msg}")
    
    # Test 2: NDVI Calculation
    print("\n🧪 Test 2: NDVI Calculation")
    success, result = debugger.test_ndvi_calculation()
    print(f"Result: {'✅' if success else '❌'} {result}")
    
    return debugger

if __name__ == "__main__":
    run_isolated_tests()
