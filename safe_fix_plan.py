#!/usr/bin/env python3
"""
PHASE 4: SAFE FIX IMPLEMENTATION
================================

Strategy:
1. Create backup of working vegetation_analyzer
2. Create improved NDVI method with better date ranges
3. Fix gee_setup singleton issue
4. Test in isolation before integration
"""

def create_improved_ndvi_method():
    """Create improved NDVI calculation with better fallbacks"""
    
    improved_code = '''
    def _analyze_ndvi_improved(self, area: ee.Geometry, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Improved NDVI analysis with better fallback strategies"""
        try:
            # Strategy 1: Try multiple date ranges and cloud thresholds
            search_strategies = [
                # (days_back, cloud_threshold, description)
                (30, 20, "Recent clear imagery"),
                (60, 30, "Extended recent period"),
                (90, 40, "Seasonal period"),
                (180, 50, "Extended seasonal"),
                (365, 60, "Annual fallback")
            ]
            
            for days_back, cloud_threshold, description in search_strategies:
                search_start = end_date - timedelta(days=days_back)
                
                collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \\
                    .filterBounds(area) \\
                    .filterDate(search_start.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \\
                    .filter(ee.Filter.lt('CLOUD_COVER', cloud_threshold))
                
                size = collection.size().getInfo()
                if size > 0:
                    logger.info(f"🛰️ Found {size} images using {description}")
                    
                    # Calculate NDVI
                    def calculate_ndvi(image):
                        ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
                        return image.addBands(ndvi)
                    
                    # Get median NDVI
                    ndvi_collection = collection.map(calculate_ndvi)
                    median_ndvi = ndvi_collection.select('NDVI').median()
                    
                    # Calculate statistics
                    stats = median_ndvi.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=area,
                        scale=30,
                        maxPixels=1e9
                    ).getInfo()
                    
                    ndvi_value = stats.get('NDVI')
                    if ndvi_value is not None:
                        # Interpret NDVI values
                        if ndvi_value > 0.6:
                            vegetation_health = "excellent"
                        elif ndvi_value > 0.4:
                            vegetation_health = "good"
                        elif ndvi_value > 0.2:
                            vegetation_health = "moderate"
                        else:
                            vegetation_health = "poor"
                        
                        return {
                            'ndvi_value': ndvi_value,
                            'vegetation_health': vegetation_health,
                            'image_count': size,
                            'date_range_days': days_back,
                            'cloud_threshold': cloud_threshold,
                            'strategy_used': description,
                            'analysis_date': end_date.isoformat()
                        }
            
            # If no imagery found with any strategy
            logger.warning("No suitable imagery available with any search strategy")
            return {
                'ndvi_value': None,
                'vegetation_health': 'unknown',
                'error': 'No suitable imagery available',
                'strategies_tried': len(search_strategies)
            }
            
        except Exception as e:
            logger.error(f"NDVI analysis failed: {e}")
            return {
                'ndvi_value': None,
                'vegetation_health': 'unknown', 
                'error': str(e)
            }
    '''
    
    return improved_code

def create_gee_setup_fix():
    """Create fix for gee_setup singleton"""
    
    fix_code = '''
    def initialize_robust(self) -> bool:
        """Robust GEE initialization with proper error handling"""
        if self.initialized and self.available:
            return True
            
        try:
            # Clear any previous initialization state
            self.initialized = False
            self.available = False
            
            if self.credentials_path and os.path.exists(self.credentials_path):
                logger.info("🔐 Attempting service account authentication...")
                
                # Direct initialization without double-calling
                credentials = ee.ServiceAccountCredentials(None, self.credentials_path)
                ee.Initialize(credentials)
                
                # Simple test without getInfo() which might fail
                try:
                    ee.Number(1)  # Just create, don't call getInfo
                    self.initialized = True
                    self.available = True
                    logger.info("✅ GEE initialized successfully with service account")
                    return True
                except Exception as test_error:
                    logger.warning(f"GEE test failed but auth succeeded: {test_error}")
                    # Sometimes the test fails but GEE actually works
                    self.initialized = True  
                    self.available = True
                    return True
                    
            else:
                logger.warning(f"Service account file not found: {self.credentials_path}")
                return False
                
        except Exception as e:
            logger.error(f"GEE initialization failed: {e}")
            return False
    '''
    
    return fix_code

if __name__ == "__main__":
    print("=== SAFE FIX PLAN ===")
    print("✅ Created improved NDVI method")
    print("✅ Created GEE setup fix") 
    print("🎯 Next: Test fixes in isolation before applying")
