#!/usr/bin/env python3
"""
Standalone Camera Placement Demo Server
Runs independently on port 8001 for testing before integration

This is a complete separate instance for testing the camera placement system
without affecting your main deer prediction app.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import uvicorn
import json
import os
from advanced_camera_placement import BuckCameraPlacement

# Create FastAPI app
app = FastAPI(
    title="Trail Camera Placement Demo",
    description="Standalone demo for testing optimal camera placement",
    version="1.0.0"
)

# Initialize camera placement system
camera_system = BuckCameraPlacement("http://localhost:8000")  # Still uses main app for data

@app.get("/")
async def root():
    """Serve the demo interface"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trail Camera Placement Demo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            h1 { color: #2c5530; text-align: center; }
            #map { height: 500px; width: 100%; margin: 20px 0; border: 2px solid #2c5530; }
            .info-panel { 
                background: #f0f8f0; 
                border: 1px solid #2c5530; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 5px; 
            }
            .result { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .loading { color: #666; font-style: italic; }
            button { 
                background: #2c5530; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 5px; 
                cursor: pointer; 
                margin: 5px; 
            }
            button:hover { background: #1a3320; }
        </style>
    </head>
    <body>
        <h1>🎥 Trail Camera Placement Demo</h1>
        <div class="info-panel">
            <strong>Instructions:</strong>
            <ul>
                <li>Click anywhere on the map to set your hunting target location</li>
                <li>The system will calculate the single optimal camera placement</li>
                <li>Red pin = Your target, Green camera = Optimal camera position</li>
                <li>Based on real satellite data and deer movement patterns</li>
            </ul>
        </div>
        
        <div id="map"></div>
        
        <div id="results"></div>
        
        <div class="info-panel">
            <button onclick="testVermont()">Test Central Vermont</button>
            <button onclick="testNorthern()">Test Northern Vermont</button>
            <button onclick="testSouthern()">Test Southern Vermont</button>
            <button onclick="clearMap()">Clear Map</button>
        </div>

        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
        <script>
            // Initialize map centered on Vermont
            const map = L.map('map').setView([44.26, -72.58], 10);
            
            // Add map tiles
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            let targetMarker = null;
            let cameraMarker = null;
            let connectionLine = null;
            
            // Handle map clicks
            map.on('click', function(e) {
                const lat = e.latlng.lat;
                const lon = e.latlng.lng;
                analyzeCameraPlacement(lat, lon);
            });
            
            async function analyzeCameraPlacement(lat, lon) {
                // Clear previous markers
                clearMarkers();
                
                // Add target marker
                targetMarker = L.marker([lat, lon], {
                    icon: L.icon({
                        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
                        iconSize: [25, 41],
                        iconAnchor: [12, 41]
                    })
                }).addTo(map).bindPopup('Target Location');
                
                // Show loading
                document.getElementById('results').innerHTML = '<div class="loading">🔄 Calculating optimal camera placement...</div>';
                
                try {
                    // Call our API
                    const response = await fetch(`/camera-placement?lat=${lat}&lon=${lon}`);
                    const data = await response.json();
                    
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    
                    // Add camera marker
                    const cameraLat = data.camera_placement.lat;
                    const cameraLon = data.camera_placement.lon;
                    
                    cameraMarker = L.marker([cameraLat, cameraLon], {
                        icon: L.icon({
                            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
                            iconSize: [25, 41],
                            iconAnchor: [12, 41]
                        })
                    }).addTo(map).bindPopup(`Camera Position<br>${data.camera_placement.confidence_score.toFixed(1)}% confidence`);
                    
                    // Add connection line
                    connectionLine = L.polyline([
                        [lat, lon],
                        [cameraLat, cameraLon]
                    ], {
                        color: 'blue',
                        weight: 2,
                        dashArray: '5, 10'
                    }).addTo(map);
                    
                    // Display results
                    displayResults(data);
                    
                } catch (error) {
                    document.getElementById('results').innerHTML = `<div class="result" style="background: #ffe8e8;">❌ Error: ${error.message}</div>`;
                }
            }
            
            function displayResults(data) {
                const camera = data.camera_placement;
                const quality = data.analysis_quality;
                const instructions = data.usage_instructions;
                
                const html = `
                    <div class="result">
                        <h3>🎯 Camera Placement Analysis</h3>
                        <p><strong>📍 Target:</strong> (${data.target_location.lat.toFixed(6)}, ${data.target_location.lon.toFixed(6)})</p>
                        <p><strong>📷 Camera:</strong> (${camera.lat.toFixed(6)}, ${camera.lon.toFixed(6)})</p>
                        <p><strong>📏 Distance:</strong> ${camera.distance_meters.toFixed(0)} meters</p>
                        <p><strong>🎯 Confidence:</strong> ${camera.confidence_score.toFixed(1)}%</p>
                        <p><strong>💭 Strategy:</strong> ${camera.reasoning}</p>
                        <p><strong>🛰️ Data Source:</strong> ${quality.data_source}</p>
                        <p><strong>⏰ Best Times:</strong> ${instructions.optimal_times.join(', ')}</p>
                        <p><strong>📡 Detection Range:</strong> ${instructions.detection_range}</p>
                    </div>
                `;
                
                document.getElementById('results').innerHTML = html;
            }
            
            function clearMarkers() {
                if (targetMarker) { map.removeLayer(targetMarker); targetMarker = null; }
                if (cameraMarker) { map.removeLayer(cameraMarker); cameraMarker = null; }
                if (connectionLine) { map.removeLayer(connectionLine); connectionLine = null; }
            }
            
            function clearMap() {
                clearMarkers();
                document.getElementById('results').innerHTML = '';
            }
            
            // Test functions
            function testVermont() { analyzeCameraPlacement(44.26, -72.58); }
            function testNorthern() { analyzeCameraPlacement(44.95, -72.32); }
            function testSouthern() { analyzeCameraPlacement(43.15, -72.88); }
        </script>
    </body>
    </html>
    """)

@app.get("/camera-placement")
async def get_camera_placement(
    lat: float = Query(..., description="Target latitude"),
    lon: float = Query(..., description="Target longitude")
):
    """API endpoint for camera placement calculation"""
    try:
        print(f"🎥 Demo: Calculating camera placement for ({lat:.4f}, {lon:.4f})")
        
        result = camera_system.calculate_optimal_camera_position(lat, lon)
        
        # Format for frontend
        response = {
            "target_location": {"lat": lat, "lon": lon},
            "camera_placement": {
                "lat": result["optimal_camera"]["lat"],
                "lon": result["optimal_camera"]["lon"],
                "confidence_score": result["optimal_camera"]["confidence_score"],
                "distance_meters": result["optimal_camera"]["distance_from_target_meters"],
                "reasoning": result["placement_strategy"]["primary_factors"][0] if result["placement_strategy"]["primary_factors"] else "Optimal positioning"
            },
            "analysis_quality": {
                "data_source": result["satellite_data_quality"].get("data_source", "standard"),
                "confidence_level": "high" if result["optimal_camera"]["confidence_score"] >= 80 else "moderate"
            },
            "usage_instructions": {
                "detection_range": result["placement_strategy"]["expected_detection_range"],
                "optimal_times": result["placement_strategy"]["optimal_times"],
                "placement_type": result["placement_strategy"]["placement_type"]
            }
        }
        
        print(f"✅ Demo: Camera calculated with {result['optimal_camera']['confidence_score']:.1f}% confidence")
        return response
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        return {
            "error": f"Camera placement calculation failed: {str(e)}",
            "target_location": {"lat": lat, "lon": lon}
        }

@app.get("/health")
async def health_check():
    """Health check for the demo server"""
    return {
        "status": "healthy",
        "service": "Camera Placement Demo",
        "version": "1.0.0",
        "main_app_connection": "http://localhost:8000"
    }

def start_demo_server():
    """Start the demo server"""
    print("🚀 Starting Trail Camera Placement Demo Server")
    print("=" * 60)
    print("📍 Demo URL: http://localhost:8001")
    print("🗺️ Interactive map interface available")
    print("🔗 Uses main app data from http://localhost:8000")
    print("⚠️ Make sure your main deer prediction app is running first!")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

if __name__ == "__main__":
    start_demo_server()
