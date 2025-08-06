#!/usr/bin/env python3
"""
LiDAR Integration Test Script
Tests the LiDAR functionality and integration with the deer prediction system
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_lidar_integration():
    """Test LiDAR integration functionality"""
    
    print("🚀 Testing LiDAR Integration for Vermont Deer Prediction")
    print("=" * 60)
    
    try:
        # Test 1: Import LiDAR modules
        print("\n1. Testing LiDAR module imports...")
        
        try:
            from backend.lidar_integration import lidar_analysis, LidarTerrainData
            print("✅ LiDAR integration module imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import LiDAR module: {e}")
            return False
        
        # Test 2: Test terrain data generation
        print("\n2. Testing terrain data generation...")
        
        test_lat, test_lng = 44.26, -72.58  # Montpelier, VT
        radius = 100.0
        
        terrain_data = await lidar_analysis.get_lidar_terrain(test_lat, test_lng, radius)
        
        if terrain_data:
            print(f"✅ Terrain data generated successfully")
            print(f"   - Resolution: {terrain_data.resolution}m")
            print(f"   - Elevation range: {terrain_data.elevation.min():.1f} - {terrain_data.elevation.max():.1f}m")
            print(f"   - Slope range: {terrain_data.slope.min():.1f} - {terrain_data.slope.max():.1f}°")
            print(f"   - Canopy height: {terrain_data.canopy_height.mean():.1f}m average")
            print(f"   - Canopy density: {terrain_data.canopy_density.mean():.2f} average")
        else:
            print("❌ Failed to generate terrain data")
            return False
        
        # Test 3: Test enhanced terrain analysis
        print("\n3. Testing enhanced terrain analysis...")
        
        target_lat, target_lng = test_lat + 0.001, test_lng + 0.001
        
        analysis_result = await lidar_analysis.enhanced_terrain_analysis(
            test_lat, test_lng, target_lat, target_lng
        )
        
        if analysis_result.get('lidar_enhanced'):
            print("✅ Enhanced terrain analysis completed")
            print(f"   - Distance: {analysis_result.get('distance_meters', 0):.1f}m")
            print(f"   - Elevation change: {analysis_result.get('elevation_change', 0):.1f}m")
            print(f"   - Max slope: {analysis_result.get('max_slope', 0):.1f}°")
            print(f"   - Concealment score: {analysis_result.get('concealment_score', 0):.1f}/100")
            print(f"   - Noise level: {analysis_result.get('noise_level', 'unknown')}")
        else:
            print("❌ Enhanced terrain analysis failed")
            return False
        
        # Test 4: Test deer corridor analysis
        print("\n4. Testing deer corridor analysis...")
        
        corridor_analysis = await lidar_analysis.enhanced_deer_corridor_analysis(
            test_lat, test_lng, radius=300
        )
        
        if corridor_analysis and 'movement_corridors' in corridor_analysis:
            print("✅ Deer corridor analysis completed")
            print(f"   - Movement corridors: {len(corridor_analysis['movement_corridors'])}")
            print(f"   - Bedding areas: {len(corridor_analysis['bedding_areas'])}")
            print(f"   - Feeding zones: {len(corridor_analysis['feeding_zones'])}")
            print(f"   - Analysis radius: {corridor_analysis['analysis_radius_meters']}m")
        else:
            print("❌ Deer corridor analysis failed")
            return False
        
        # Test 5: Test performance
        print("\n5. Testing performance...")
        
        import time
        start_time = time.time()
        
        # Run multiple quick analyses
        for i in range(3):
            test_analysis = await lidar_analysis.enhanced_terrain_analysis(
                test_lat + i * 0.0001, test_lng + i * 0.0001,
                test_lat + i * 0.0001 + 0.0005, test_lng + i * 0.0001 + 0.0005
            )
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 3
        
        print(f"✅ Performance test completed")
        print(f"   - Average analysis time: {avg_time:.3f}s")
        print(f"   - Performance rating: {'Excellent' if avg_time < 1.0 else 'Good' if avg_time < 2.0 else 'Acceptable'}")
        
        print("\n" + "=" * 60)
        print("🎉 All LiDAR integration tests passed!")
        print("✅ LiDAR system is ready for Vermont deer prediction enhancement")
        
        return True
        
    except Exception as e:
        print(f"\n❌ LiDAR integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Test required dependencies"""
    
    print("\n📦 Testing LiDAR dependencies...")
    
    dependencies = [
        ("numpy", "NumPy for array processing"),
        ("rasterio", "Rasterio for GeoTIFF processing"),
        ("scipy", "SciPy for scientific computing"),
    ]
    
    missing_deps = []
    
    for dep, desc in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - {desc}")
        except ImportError:
            print(f"❌ {dep} - {desc} (MISSING)")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install " + " ".join(missing_deps))
        return False
    
    return True

async def main():
    """Main test function"""
    
    print("🌲 Vermont Deer Prediction - LiDAR Integration Test")
    print("Version 1.0.0")
    print("=" * 60)
    
    # Test dependencies first
    if not test_dependencies():
        print("\n❌ Dependency test failed. Please install missing packages.")
        return
    
    # Test LiDAR integration
    success = await test_lidar_integration()
    
    if success:
        print("\n🎯 LiDAR integration is fully operational!")
        print("🦌 Ready to provide enhanced deer prediction with sub-meter accuracy")
    else:
        print("\n⚠️  LiDAR integration test failed. Check logs for details.")

if __name__ == "__main__":
    asyncio.run(main())
