#!/usr/bin/env python3
"""
SAFE FIX: Test improved NDVI method in isolation
"""

def test_improved_ndvi():
    """Test the improved NDVI method before integration"""
    
    try:
        import ee
        import os
        from datetime import datetime, timedelta
        
        # Manual GEE init
        credentials_path = '/app/credentials/gee-service-account.json'
        credentials = ee.ServiceAccountCredentials(None, credentials_path)
        ee.Initialize(credentials)
        
        print("✅ GEE initialized")
        
        # Test improved NDVI calculation
        lat, lon = 44.26, -72.58
        area = ee.Geometry.Point([lon, lat])
        end_date = datetime.now()
        
        # Improved search strategies
        search_strategies = [
            (30, 20, "Recent clear imagery"),
            (60, 30, "Extended recent period"), 
            (90, 40, "Seasonal period"),
            (180, 50, "Extended seasonal"),
            (365, 60, "Annual fallback")
        ]
        
        print("🛰️ Testing improved NDVI strategies...")
        
        for days_back, cloud_threshold, description in search_strategies:
            search_start = end_date - timedelta(days=days_back)
            
            collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterBounds(area) \
                .filterDate(search_start.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUD_COVER', cloud_threshold))
            
            size = collection.size().getInfo()
            print(f"   {description}: {size} images (cloud < {cloud_threshold}%)")
            
            if size > 0:
                # Calculate NDVI
                def calculate_ndvi(image):
                    ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
                    return image.addBands(ndvi)
                
                ndvi_collection = collection.map(calculate_ndvi)
                median_ndvi = ndvi_collection.select('NDVI').median()
                
                stats = median_ndvi.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=area,
                    scale=30,
                    maxPixels=1e9
                ).getInfo()
                
                ndvi_value = stats.get('NDVI')
                if ndvi_value is not None:
                    print(f"   ✅ SUCCESS: NDVI = {ndvi_value:.4f}")
                    print(f"   Strategy: {description} ({days_back} days, <{cloud_threshold}% clouds)")
                    return True
        
        print("❌ No suitable imagery found with any strategy")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_improved_ndvi()
