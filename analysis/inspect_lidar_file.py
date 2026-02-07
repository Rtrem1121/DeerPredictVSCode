
import rasterio
import os
import numpy as np

def inspect_file(filename):
    # Adjusted path to look in parent directory's data folder
    path = os.path.join(os.path.dirname(__file__), "..", "data", "lidar", "vermont", filename)
    print(f"Inspecting: {path}")
    
    try:
        with rasterio.open(path) as src:
            print(f"  Driver: {src.driver}")
            print(f"  Size: {src.width} x {src.height}")
            print(f"  CRS: {src.crs}")
            print(f"  Bounds: {src.bounds}")
            print(f"  Count: {src.count} bands")
            print(f"  NoData: {src.nodata}")
            
            # Read a sample
            data = src.read(1)
            print(f"  Min Value: {np.nanmin(data)}")
            print(f"  Max Value: {np.nanmax(data)}")
            print(f"  Mean Value: {np.nanmean(data)}")
            
            # Check center
            center_val = data[src.height//2, src.width//2]
            print(f"  Center Value: {center_val}")
            
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    files = [
        "Central_TopoDiff_70cm_DEMHF.tif",
        "Northern_TopoDiff_70cm_DEMHF.tif",
        "Southern_TopoDiff_70cm_DEMHF.tif"
    ]
    for f in files:
        inspect_file(f)
