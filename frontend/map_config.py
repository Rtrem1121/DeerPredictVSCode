# Map Configuration for Deer Prediction App
# Add new map types here for easy expansion

MAP_SOURCES = {
    # Topographic Maps - Best for hunting applications
    "Topographic (USGS)": {
        "tiles": "https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}",
        "attr": "USGS",
        "description": "🇺🇸 USGS topographic maps with contour lines and detailed terrain features. Best for US locations.",
        "max_zoom": 16,
        "best_for": ["US hunting areas", "Detailed terrain analysis", "Contour reading"]
    },
    
    "Topographic (OpenTopo)": {
        "tiles": "https://tile.opentopomap.org/{z}/{x}/{y}.png",
        "attr": "OpenTopoMap (CC-BY-SA)",
        "description": "🌍 Global topographic maps with contour lines and terrain shading. Great worldwide coverage.",
        "max_zoom": 17,
        "best_for": ["International locations", "Global coverage", "Contour visualization"]
    },
    
    "Topographic (Esri)": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        "attr": "Esri",
        "description": "🗺️ Professional topographic maps with terrain features and comprehensive land cover data.",
        "max_zoom": 19,
        "best_for": ["Professional use", "Detailed land cover", "High zoom levels"]
    },
    
    # Terrain and Physical Maps
    "Terrain (Stamen)": {
        "tiles": "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png",
        "attr": "Stamen Design (CC BY 3.0)",
        "description": "🏔️ Beautiful terrain maps with hill shading and natural color palette.",
        "max_zoom": 18,
        "best_for": ["Terrain visualization", "Natural features", "Hill shading"]
    },
    
    # Satellite and Aerial Imagery
    "Satellite (Esri)": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Esri",
        "description": "🛰️ High-resolution satellite imagery. Perfect for identifying actual terrain features and vegetation.",
        "max_zoom": 19,
        "best_for": ["Vegetation identification", "Water features", "Actual terrain conditions"]
    },
    
    # Street and Navigation Maps
    "Street Map": {
        "tiles": None,  # Use default OpenStreetMap
        "attr": "OpenStreetMap",
        "description": "🛣️ Standard street map with roads, trails, and labels. Good for navigation and access planning.",
        "max_zoom": 19,
        "best_for": ["Road access", "Trail navigation", "Property boundaries"]
    },
    
    # Specialized Hunting Maps (if available)
    "Hunting (OnX)": {
        "tiles": "https://tile.onxmaps.com/map/tile/{z}/{x}/{y}.png",  # Example - would need API key
        "attr": "onX Maps",
        "description": "🎯 Specialized hunting maps with property boundaries and land ownership data.",
        "max_zoom": 18,
        "best_for": ["Property boundaries", "Land ownership", "Hunting regulations"],
        "requires_auth": True,
        "enabled": False  # Disabled by default - requires subscription
    }
}

# Overlay configurations
OVERLAY_SOURCES = {
    "contours": {
        "name": "Contour Lines",
        "url": "https://basemap.nationalmap.gov/arcgis/services/USGSTopoLarge/MapServer/WMSServer?",
        "layers": "0",
        "description": "Elevation contour lines showing terrain elevation changes"
    },
    
    "hillshade": {
        "name": "Terrain Shading",
        "url": "https://basemap.nationalmap.gov/arcgis/services/USGSImageryOnly/MapServer/WMSServer?",
        "layers": "0",
        "description": "Hill shading to show terrain relief and slope",
        "opacity": 0.6
    },
    
    "land_cover": {
        "name": "Land Cover",
        "url": "https://basemap.nationalmap.gov/arcgis/services/USGSImageryOnly/MapServer/WMSServer?",
        "layers": "1",
        "description": "Land cover classification showing vegetation types",
        "opacity": 0.7
    }
}

# Map recommendations based on use case
USE_CASE_RECOMMENDATIONS = {
    "scouting": ["Topographic (USGS)", "Satellite (Esri)"],
    "stand_placement": ["Topographic (USGS)", "Topographic (Esri)"],
    "access_planning": ["Street Map", "Topographic (USGS)"],
    "terrain_analysis": ["Topographic (OpenTopo)", "Terrain (Stamen)"],
    "vegetation_analysis": ["Satellite (Esri)", "Topographic (Esri)"]
}
