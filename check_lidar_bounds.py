#!/usr/bin/env python3
"""
Check the geographic bounds of all LiDAR TIF files
"""

import rasterio
import os

lidar_dir = r"c:\Users\Rich\deer_pred_app\data\lidar\vermont"

print("🗺️  Vermont LiDAR Coverage Areas\n" + "="*80)

for file in os.listdir(lidar_dir):
    if file.lower().endswith(('.tif', '.tiff')):
        filepath = os.path.join(lidar_dir, file)
        
        try:
            with rasterio.open(filepath) as src:
                bounds = src.bounds
                print(f"\n📂 {file}")
                print(f"   Latitude:  {bounds.bottom:.5f}°N to {bounds.top:.5f}°N")
                print(f"   Longitude: {bounds.left:.5f}°W to {bounds.right:.5f}°W")
                print(f"   Resolution: {src.res[0]:.2f}m x {src.res[1]:.2f}m")
                print(f"   Size: {src.width} x {src.height} pixels")
                print(f"   CRS: {src.crs}")
        except Exception as e:
            print(f"\n❌ Error reading {file}: {e}")

print("\n" + "="*80)
print("\n🎯 Test Locations:")
print(f"   Recent hunting: 43.31181°N, -73.21624°W")
print(f"   Original test:  43.31270°N, -73.21680°W")
