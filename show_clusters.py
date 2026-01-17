"""Quick script to show all cluster coordinates from last analysis"""
import sys
sys.path.append('.')

from property_hotspot_analyzer import PropertyHotspotAnalyzer
import json

# Load the last run's property corners
PROPERTY_CORNERS = {
    'NW': (43.3226, -73.21439),
    'NE': (43.32252, -73.20466),
    'SE': (43.31382, -73.20513),
    'SW': (43.31471, -73.21784)
}

# Create analyzer with the corners (it expects a dict, not a list)
analyzer = PropertyHotspotAnalyzer(PROPERTY_CORNERS)

# Load the stands from the report
with open('hotspot_report.json', 'r') as f:
    report = json.load(f)

# We need to extract stands from the predictions
# Let me re-run just the clustering part by loading all stands
print("Loading stand data from predictions...")
print(f"Total stands predicted: {report['total_stands_predicted']}")
print(f"Stands inside property: {report['stands_inside_property']}")

# Actually, we need to look at the HTML map which has all the cluster data
print("\nCluster information is in hotspot_map.html")
print("Let me parse the map data...")

# Read the HTML file
with open('hotspot_map.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Look for cluster marker data
import re

# Find all cluster markers in the HTML
cluster_pattern = r'L\.marker\(\[([0-9.-]+),\s*([0-9.-]+)\].*?Icon.*?cluster'
clusters = re.findall(cluster_pattern, html_content, re.DOTALL)

if clusters:
    print(f"\n✅ Found {len(clusters)} cluster markers:")
    for i, (lat, lon) in enumerate(clusters, 1):
        inside = analyzer.is_inside_property(float(lat), float(lon))
        status = "INSIDE" if inside else "OUTSIDE"
        print(f"\n   Cluster {i}: ({lat}, {lon})")
        print(f"   Status: {status} property boundary")
else:
    print("\n⚠️  No cluster markers found in HTML")
    
# Also check for hotspot cluster markers (different pattern)
hotspot_pattern = r'Hotspot.*?\[([0-9.-]+),\s*([0-9.-]+)\]'
hotspots = re.findall(hotspot_pattern, html_content)

if hotspots:
    print(f"\n✅ Found {len(hotspots)} hotspot markers:")
    for i, (lat, lon) in enumerate(hotspots, 1):
        inside = analyzer.is_inside_property(float(lat), float(lon))
        status = "INSIDE" if inside else "OUTSIDE"
        print(f"\n   Hotspot {i}: ({lat}, {lon})")
        print(f"   Status: {status} property boundary")
