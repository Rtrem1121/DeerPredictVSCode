
import rasterio
from rasterio.warp import transform
import os

def check_all_files():
    lat = 43.31255
    lon = -73.21502
    
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "lidar", "vermont")
    files = [f for f in os.listdir(data_dir) if f.endswith('.tif')]
    
    print(f"Checking coverage for {lat}, {lon} in {len(files)} files...")
    
    for f in files:
        filepath = os.path.join(data_dir, f)
        try:
            with rasterio.open(filepath) as src:
                # Transform point to raster CRS
                xs, ys = transform('EPSG:4326', src.crs, [lon], [lat])
                x, y = xs[0], ys[0]
                
                in_bounds = (src.bounds.left <= x <= src.bounds.right and 
                             src.bounds.bottom <= y <= src.bounds.top)
                
                if in_bounds:
                    print(f"\n✅ FOUND COVERAGE: {f}")
                    print(f"   CRS: {src.crs}")
                    print(f"   Transformed: {x:.2f}, {y:.2f}")
                    
                    # Read value
                    row, col = src.index(x, y)
                    window = rasterio.windows.Window(col, row, 1, 1)
                    val = src.read(1, window=window)
                    print(f"   Value: {val[0][0]}")
                    
                    # Read 5x5 stats
                    w5 = rasterio.windows.Window(col-2, row-2, 5, 5)
                    v5 = src.read(1, window=w5)
                    print(f"   5x5 Mean: {v5.mean():.2f}")
                    print(f"   5x5 Max: {v5.max():.2f}")
                else:
                    # print(f"❌ No coverage: {f}")
                    pass
        except Exception as e:
            print(f"Error checking {f}: {e}")

if __name__ == "__main__":
    check_all_files()
