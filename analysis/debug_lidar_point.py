
import rasterio
from rasterio.warp import transform
import os

def debug_point():
    lat = 43.31255
    lon = -73.21502
    
    # Path to the file we suspect covers this area
    # Based on previous logs, Central_TopoDiff... had bounds that might cover it
    filename = "Central_TopoDiff_70cm_DEMHF.tif"
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "lidar", "vermont", filename)
    
    print(f"Debugging Point: {lat}, {lon}")
    print(f"File: {filepath}")
    
    if not os.path.exists(filepath):
        print("File not found.")
        return

    with rasterio.open(filepath) as src:
        print(f"CRS: {src.crs}")
        print(f"Bounds: {src.bounds}")
        
        # Transform point to raster CRS
        xs, ys = transform('EPSG:4326', src.crs, [lon], [lat])
        x, y = xs[0], ys[0]
        
        print(f"Transformed Coords (EPSG:6589): X={x}, Y={y}")
        
        # Check if inside bounds
        in_bounds = (src.bounds.left <= x <= src.bounds.right and 
                     src.bounds.bottom <= y <= src.bounds.top)
        print(f"Inside Bounds: {in_bounds}")
        
        if in_bounds:
            # Get array index
            row, col = src.index(x, y)
            print(f"Row: {row}, Col: {col}")
            
            # Read value
            # Read a 1x1 window
            window = rasterio.windows.Window(col, row, 1, 1)
            val = src.read(1, window=window)
            print(f"Raw Value at Point: {val[0][0]}")
            
            # Check surrounding 3x3
            window3 = rasterio.windows.Window(col-1, row-1, 3, 3)
            val3 = src.read(1, window=window3)
            print(f"Surrounding 3x3:\n{val3}")
            
            print(f"Number of bands: {src.count}")
            if src.count > 1:
                for i in range(2, src.count + 1):
                    val_band = src.read(i, window=window)
                    print(f"Band {i} Value: {val_band[0][0]}")
        else:
            print("Point is outside this file's bounds.")

if __name__ == "__main__":
    debug_point()
