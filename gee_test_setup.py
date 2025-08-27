import ee

# --- Authentication Step ---
# This function will prompt you to authenticate with your Google account.
# It will typically open a browser window for you to log in and grant permissions.
# You only need to run this once per environment/machine, or when your credentials expire.
print("Starting Earth Engine Authentication...")
ee.Authenticate()
print("Authentication complete.")

# Initialize with your project
ee.Initialize(project='deer-predict-app')
print("Earth Engine initialized with deer-predict-app project.")

# Simple test to verify everything works
try:
    # Test basic functionality
    test_image = ee.Image('LANDSAT/LC08/C02/T1_L2/LC08_013030_20240701')
    print("✅ Basic Earth Engine access confirmed!")
    
    # Test your area (Vermont coordinates)
    point = ee.Geometry.Point(-72.58, 44.26)
    print("✅ Vermont coordinate access confirmed!")
    
    print("🎉 Google Earth Engine setup successful!")
    
except Exception as e:
    print(f"❌ Setup error: {e}")
    print("Check your project permissions and API status.")
