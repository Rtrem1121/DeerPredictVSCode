"""
Frontend configuration and constants.
Centralizes all frontend settings and map configurations.
"""

# Map center coordinates for Vermont
VERMONT_CENTER = [44.0459, -72.7107]
DEFAULT_ZOOM = 8
RESULTS_ZOOM = 14

# Map display settings
MAP_HEIGHT = 600
RESULTS_MAP_HEIGHT = 600

# UI Configuration
SEASON_OPTIONS = ["early_season", "rut", "late_season"]
SEASON_DISPLAY_NAMES = {
    "early_season": "Early Season", 
    "rut": "Rut",
    "late_season": "Late Season"
}

# Coordinate validation bounds for Vermont
VERMONT_BOUNDS = {
    'min_lat': 42.730,   # Southern border
    'max_lat': 45.017,   # Northern border  
    'min_lon': -73.438,  # Eastern border
    'max_lon': -71.465   # Western border
}

# Default coordinates (center of Vermont)
DEFAULT_LAT = 44.0459
DEFAULT_LON = -72.7107

# API Configuration
BACKEND_URL = "http://backend:8000"
API_TIMEOUT = 30

# CSS Classes
CSS_STYLES = """
<style>
.main-header {
    background: linear-gradient(45deg, #2E7D32, #4CAF50);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 1rem;
}
.map-container {
    border: 3px solid #2E7D32;
    border-radius: 10px;
    padding: 10px;
    background-color: #f8f9fa;
}
.success-message {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    padding: 0.75rem 1.25rem;
    margin-bottom: 1rem;
    border-radius: 0.25rem;
}
.error-message {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
    padding: 0.75rem 1.25rem;
    margin-bottom: 1rem;
    border-radius: 0.25rem;
}
</style>
"""

# Map Legend HTML
MAP_LEGEND_HTML = '''
<div style="position: fixed; 
            top: 10px; right: 10px; width: 280px; height: auto; 
            background-color: white; border:3px solid #2E7D32; z-index:9999; 
            font-size:12px; padding: 12px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
<p style="margin:0; font-weight:bold; font-size:14px; color:#2E7D32;">🦌 HUNTING MAP</p>
<hr style="margin: 8px 0; border-color:#2E7D32;">

<p style="margin:2px 0;"><span style="color:red">🎯</span> Your Target Location</p>
<p style="margin:2px 0;"><span style="color:darkred">🌳</span> Bedding Areas</p>
<p style="margin:2px 0;"><span style="color:green">🍃</span> Feeding Areas</p>
<p style="margin:2px 0;"><span style="color:blue">👣</span> Travel Corridors</p>
<p style="margin:2px 0;"><span style="color:darkgreen">🎯</span> Best Stands (80%+ confidence)</p>
<p style="margin:2px 0;"><span style="color:orange">🎯</span> Good Stands (70%+ confidence)</p>
<p style="margin:2px 0;"><span style="color:darkblue">🚗</span> Parking/Access</p>
</div>
'''

# Instructions text
INSTRUCTIONS_TEXT = """
## 🎯 How to Use This Tool

**👆 Simply click anywhere on the map above** to get instant hunting analysis!

The system will automatically:
- 🔍 Analyze deer behavior at your clicked location
- 🎯 Find the 5 best hunting stands nearby  
- 🚗 Show parking and access routes
- 📊 Provide detailed setup instructions
"""

DETAILS_TEXT = """
**After clicking, the map will update to show:**
- 🎯 **Red crosshairs**: Your selected target location
- 🌳 **Dark red markers**: Bedding areas (where deer rest)
- 🍃 **Green markers**: Feeding areas (where deer eat)  
- 👣 **Blue markers**: Travel corridors (deer movement paths)
- 🎯 **Hunting stands**: Ranked by confidence level
- 🚗 **Blue car icons**: Parking and access points

**Stand Confidence Colors:**
- **Dark Green** = 80%+ confidence (hunt here first!)
- **Orange** = 70%+ confidence (good backup options)
- **Gray** = Lower confidence (last resort)
"""
