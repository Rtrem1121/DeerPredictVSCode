
import rasterio
import os
import numpy as np

def deep_inspect(filename):
    # Adjusted path for analysis/ folder execution
    path = os.path.join(os.path.dirname(__file__), "..", "data", "lidar", "vermont", filename)
    print(f"Inspecting: {path}")
    
    if not os.path.exists(path):
        print("File not found!")
        return

    try:
        with rasterio.open(path) as src:
            print(f"  CRS: {src.crs}")
            print(f"  Units: {src.units}")
            print(f"  Transform: {src.transform}")
            
            # Read a larger chunk (1000x1000) from the center
            window = rasterio.windows.Window(src.width//2 - 500, src.height//2 - 500, 1000, 1000)
            data = src.read(1, window=window)
            
            # Filter out NoData
            valid_data = data[data != src.nodata]
            
            if valid_data.size == 0:
                print("  No valid data in center window.")
                return

            print(f"  Valid Pixels: {valid_data.size}")
            print(f"  Min: {np.min(valid_data):.2f}")
            print(f"  Max: {np.max(valid_data):.2f}")
            print(f"  Mean: {np.mean(valid_data):.2f}")
            print(f"  Median: {np.median(valid_data):.2f}")
            
            # Percentiles
            p = np.percentile(valid_data, [1, 5, 25, 50, 75, 95, 99])
            print(f"  Percentiles: 1%={p[0]:.2f}, 50%={p[3]:.2f}, 99%={p[6]:.2f}")
            
            # Histogram
            hist, bins = np.histogram(valid_data, bins=10)
            print("  Histogram:")
            for i in range(len(hist)):
                print(f"    {bins[i]:.1f} - {bins[i+1]:.1f}: {hist[i]}")

    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    files = [
        "Central_TopoDiff_70cm_DEMHF.tif"
    ]
    for f in files:
        deep_inspect(f)
