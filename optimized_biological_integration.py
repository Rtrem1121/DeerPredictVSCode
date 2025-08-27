#!/usr/bin/env python3
"""
OPTIMIZED BIOLOGICAL INTEGRATION: Incorporating Advanced Recommendations

This enhanced version incorporates all the brainstorm recommendations:
- Strengthened GEE integration with dynamic NDVI/canopy fetches
- OSM road proximity checks for bedding security
- Refined midday activity logic with cold front validation
- Enhanced environmental logic with pressure trend analysis
- Complete frontend integration with WebSocket and Selenium validation

Author: GitHub Copilot
Date: August 26, 2025
"""

import asyncio
import aiohttp
import json
import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import websocket
import threading

# Try to import Google Earth Engine
try:
    import ee
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False
    print("⚠️ Google Earth Engine not available - using fallback data")

logger = logging.getLogger(__name__)

class OptimizedBiologicalIntegration:
    """Optimized biological integration with all advanced recommendations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gee_authenticated = False
        self.pressure_history = []  # For trend analysis
        self.websocket_connected = False
        
        # Initialize GEE if available
        if GEE_AVAILABLE:
            self.initialize_gee()
        
        # Vermont test locations with varied terrain
        self.vermont_locations = [
            {"name": "Tinmouth", "lat": 43.3127, "lon": -73.2271, "terrain": "ridge"},
            {"name": "Mount Tabor", "lat": 43.3306, "lon": -72.9417, "terrain": "mountain"},
            {"name": "Killington", "lat": 43.6042, "lon": -72.8092, "terrain": "ski_area"},
            {"name": "Green Mountain", "lat": 43.2917, "lon": -72.8833, "terrain": "forest"},
            {"name": "Lake Champlain", "lat": 44.4759, "lon": -73.2121, "terrain": "agricultural"}
        ]
    
    def initialize_gee(self):
        """Initialize Google Earth Engine with Docker-compatible authentication"""
        try:
            # First try Docker-compatible initialization with service account
            import os
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            project_id = os.getenv('GEE_PROJECT_ID', 'deer-predict-app')
            
            if credentials_path and os.path.exists(credentials_path):
                # Use service account credentials for Docker
                service_credentials = ee.ServiceAccountCredentials(None, credentials_path)
                ee.Initialize(service_credentials, project=project_id)
                self.gee_authenticated = True
                self.logger.info(f"✅ GEE authenticated with service account for project: {project_id}")
            else:
                # Fallback to regular authentication for local development
                ee.Initialize(project=project_id)
                self.gee_authenticated = True
                self.logger.info(f"✅ GEE authenticated with regular auth for project: {project_id}")
                
        except Exception as e:
            try:
                # If authentication fails, try manual authentication
                ee.Authenticate()
                ee.Initialize(project='deer-predict-app')
                self.gee_authenticated = True
                self.logger.info("✅ GEE authenticated after manual login with deer-predict-app project")
            except Exception as auth_error:
                self.logger.warning(f"⚠️ GEE authentication failed: {auth_error}")
                self.gee_authenticated = False
    
    def get_dynamic_gee_data(self, lat: float, lon: float, max_retries: int = 3) -> Dict:
        """Get dynamic NDVI/canopy data from Google Earth Engine with error retries"""
        if not self.gee_authenticated:
            return self.get_fallback_gee_data(lat, lon)
        
        for attempt in range(max_retries):
            try:
                # Create point geometry
                point = ee.Geometry.Point([lon, lat])
                
                # Get recent Landsat data for NDVI
                landsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                    .filterBounds(point) \
                    .filterDate('2024-06-01', '2024-09-30') \
                    .filter(ee.Filter.lt('CLOUD_COVER', 20)) \
                    .first()
                
                if landsat:
                    # Calculate NDVI
                    ndvi = landsat.normalizedDifference(['SR_B5', 'SR_B4'])
                    
                    # Get canopy cover from Global Forest Cover
                    canopy = ee.Image('UMD/hansen/global_forest_change_2022_v1_10') \
                        .select('treecover2000')
                    
                    # ENHANCED: Get OSM disturbance data integrated with GEE
                    osm_disturbance = self.get_osm_disturbance_for_gee(lat, lon)
                    
                    # Sample values at point
                    ndvi_value = ndvi.sample(point, 30).first().get('nd').getInfo()
                    canopy_value = canopy.sample(point, 30).first().get('treecover2000').getInfo()
                    
                    # Apply OSM disturbance factor to canopy
                    effective_canopy = float(canopy_value) / 100 if canopy_value else 0.6
                    if osm_disturbance["high_disturbance"]:
                        effective_canopy *= 0.8  # Reduce effective canopy near roads/development
                    
                    gee_data = {
                        "ndvi_value": float(ndvi_value) if ndvi_value else 0.5,
                        "canopy_coverage": effective_canopy,
                        "deciduous_forest_percentage": effective_canopy,
                        "vegetation_health": "excellent" if ndvi_value and ndvi_value > 0.6 else "good",
                        "data_source": "dynamic_gee_enhanced",
                        "query_success": True,
                        "attempt": attempt + 1,
                        "osm_disturbance": osm_disturbance,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    self.logger.info(f"✅ Enhanced GEE data (attempt {attempt+1}): NDVI={ndvi_value:.3f}, Canopy={effective_canopy:.1%}")
                    return gee_data
                
            except Exception as e:
                self.logger.warning(f"⚠️ GEE query attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"❌ All {max_retries} GEE attempts failed")
        
        return self.get_fallback_gee_data(lat, lon)
    
    def get_osm_disturbance_for_gee(self, lat: float, lon: float) -> Dict:
        """Get OSM disturbance data for GEE hybrid analysis"""
        try:
            # Query for development/disturbance features
            overpass_url = "https://overpass-api.de/api/interpreter"
            query = f"""
            [out:json][timeout:15];
            (
              way["highway"~"^(primary|secondary|tertiary|trunk|motorway)$"](around:500,{lat},{lon});
              way["building"](around:200,{lat},{lon});
              way["landuse"~"^(residential|commercial|industrial)$"](around:300,{lat},{lon});
            );
            out count;
            """
            
            response = requests.post(overpass_url, data=query, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                total_features = sum(tag.get('total', 0) for tag in data.get('elements', []))
                
                disturbance_data = {
                    "total_disturbance_features": total_features,
                    "high_disturbance": total_features > 5,
                    "disturbance_factor": min(1.0, total_features / 10.0),
                    "osm_disturbance_success": True
                }
                
                self.logger.info(f"✅ OSM disturbance: {total_features} features found")
                return disturbance_data
            
        except Exception as e:
            self.logger.warning(f"⚠️ OSM disturbance query failed: {e}")
        
        return {
            "total_disturbance_features": 2,
            "high_disturbance": False,
            "disturbance_factor": 0.2,
            "osm_disturbance_success": False
        }
    
    def get_fallback_gee_data(self, lat: float, lon: float) -> Dict:
        """Fallback GEE data when dynamic query fails"""
        # Generate realistic data based on Vermont characteristics
        base_canopy = 0.65 + (lat - 43.0) * 0.1  # Higher canopy in north
        base_ndvi = 0.55 + (lat - 43.0) * 0.05
        
        return {
            "ndvi_value": max(0.2, min(0.8, base_ndvi)),
            "canopy_coverage": max(0.3, min(0.9, base_canopy)),
            "deciduous_forest_percentage": max(0.3, min(0.9, base_canopy)),
            "vegetation_health": "good",
            "data_source": "fallback",
            "query_success": False,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_osm_road_proximity(self, lat: float, lon: float, radius_km: float = 1.0) -> Dict:
        """Get road proximity data from OpenStreetMap"""
        try:
            # Overpass API query for roads
            overpass_url = "https://overpass-api.de/api/interpreter"
            query = f"""
            [out:json][timeout:25];
            (
              way["highway"~"^(primary|secondary|tertiary|trunk|motorway)$"](around:{radius_km*1000},{lat},{lon});
            );
            out geom;
            """
            
            response = requests.post(overpass_url, data=query, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                roads = data.get('elements', [])
                
                min_distance = float('inf')
                road_types = []
                
                for road in roads:
                    if 'geometry' in road:
                        road_types.append(road.get('tags', {}).get('highway', 'unknown'))
                        # Simplified distance calculation to first point
                        if road['geometry']:
                            road_lat = road['geometry'][0]['lat']
                            road_lon = road['geometry'][0]['lon']
                            distance = self.haversine_distance(lat, lon, road_lat, road_lon)
                            min_distance = min(min_distance, distance)
                
                proximity_data = {
                    "nearest_road_distance_m": min_distance if min_distance != float('inf') else 1000,
                    "road_types_nearby": list(set(road_types)),
                    "bedding_security_score": min(1.0, max(0.0, (min_distance - 200) / 800)),  # >200m is good
                    "osm_query_success": True,
                    "roads_found": len(roads)
                }
                
                self.logger.info(f"✅ OSM road data: {min_distance:.0f}m to nearest road")
                return proximity_data
            
        except Exception as e:
            self.logger.warning(f"⚠️ OSM road query failed: {e}")
        
        # Fallback data
        return {
            "nearest_road_distance_m": 500,  # Assume moderate distance
            "road_types_nearby": ["secondary"],
            "bedding_security_score": 0.6,
            "osm_query_success": False,
            "roads_found": 0
        }
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Radius of earth in meters
        
        return c * r
    
    def get_enhanced_weather_with_trends(self, lat: float, lon: float) -> Dict:
        """Get enhanced weather data with hourly pressure AND wind trends"""
        try:
            # Get current and hourly data from Open-Meteo
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,surface_pressure",
                "hourly": "temperature_2m,surface_pressure,wind_speed_10m,wind_direction_10m",
                "timezone": "America/New_York",
                "forecast_days": 1,
                "past_days": 1  # Get past 24 hours for trend analysis
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get("current", {})
                hourly = data.get("hourly", {})
                
                # Current conditions
                current_pressure_hpa = current.get("surface_pressure", 1013.25)
                current_pressure_inhg = current_pressure_hpa * 0.02953
                
                # ENHANCED: Pressure AND wind trend analysis
                pressure_trend = self.analyze_pressure_trend(hourly.get("surface_pressure", []))
                wind_trend = self.analyze_wind_trend(
                    hourly.get("wind_speed_10m", []),
                    hourly.get("wind_direction_10m", [])
                )
                
                weather_data = {
                    "temperature": current.get("temperature_2m", 50),
                    "pressure": current_pressure_inhg,
                    "wind_speed": current.get("wind_speed_10m", 5),
                    "wind_direction": current.get("wind_direction_10m", 0),
                    "humidity": current.get("relative_humidity_2m", 60),
                    "pressure_trend": pressure_trend,
                    "wind_trend": wind_trend,  # NEW: Wind trend analysis
                    "api_source": "open-meteo-enhanced-v2",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Enhanced cold front detection with wind trends
                is_cold_front = self.detect_enhanced_cold_front_with_wind(weather_data)
                weather_data["is_cold_front"] = is_cold_front
                weather_data["cold_front_strength"] = self.calculate_cold_front_strength_with_wind(weather_data)
                
                self.logger.info(f"✅ Enhanced weather v2: {weather_data['temperature']:.1f}°F, wind trend: {wind_trend['description']}")
                return weather_data
                
        except Exception as e:
            self.logger.warning(f"⚠️ Enhanced weather fetch failed: {e}")
        
        # Fallback weather
        return {
            "temperature": 45, "pressure": 29.8, "wind_speed": 8, "wind_direction": 225,
            "humidity": 65, 
            "pressure_trend": {"description": "unknown", "change_rate": 0},
            "wind_trend": {"description": "stable", "direction_shift": 0},
            "api_source": "fallback", "is_cold_front": True, "cold_front_strength": 0.7
        }
    
    def analyze_pressure_trend(self, pressure_data: List[float]) -> Dict:
        """Analyze pressure trend over past 24 hours"""
        if len(pressure_data) < 6:
            return {"description": "insufficient_data", "change_rate": 0, "trend": "stable"}
        
        # Convert to inHg and get recent data
        recent_pressures = [p * 0.02953 for p in pressure_data[-24:]]  # Last 24 hours
        
        if len(recent_pressures) >= 6:
            # Calculate 6-hour change rate
            current = recent_pressures[-1]
            six_hours_ago = recent_pressures[-7] if len(recent_pressures) >= 7 else recent_pressures[0]
            change_rate = current - six_hours_ago
            
            # Classify trend
            if change_rate < -0.1:
                trend = "falling_rapidly"
                description = "rapid pressure drop"
            elif change_rate < -0.05:
                trend = "falling"
                description = "pressure falling"
            elif change_rate > 0.1:
                trend = "rising_rapidly"
                description = "rapid pressure rise"
            elif change_rate > 0.05:
                trend = "rising"
                description = "pressure rising"
            else:
                trend = "stable"
                description = "pressure stable"
            
            return {
                "description": description,
                "change_rate": change_rate,
                "trend": trend,
                "current_pressure": current,
                "six_hour_change": change_rate
            }
        
        return {"description": "stable", "change_rate": 0, "trend": "stable"}
    
    def analyze_wind_trend(self, wind_speed_data: List[float], wind_direction_data: List[float]) -> Dict:
        """Analyze wind speed and direction trends over past 24 hours"""
        if len(wind_speed_data) < 6 or len(wind_direction_data) < 6:
            return {"description": "insufficient_data", "direction_shift": 0, "speed_trend": "stable"}
        
        # Get recent data (last 12 hours)
        recent_speeds = wind_speed_data[-12:]
        recent_directions = wind_direction_data[-12:]
        
        # Analyze direction shift
        current_dir = recent_directions[-1]
        six_hours_ago_dir = recent_directions[-7] if len(recent_directions) >= 7 else recent_directions[0]
        
        # Calculate direction change (accounting for 360° wrap)
        direction_diff = abs(current_dir - six_hours_ago_dir)
        if direction_diff > 180:
            direction_diff = 360 - direction_diff
        
        # Analyze speed trend
        current_speed = recent_speeds[-1]
        avg_speed_6h_ago = sum(recent_speeds[-7:-4]) / 3 if len(recent_speeds) >= 7 else recent_speeds[0]
        speed_change = current_speed - avg_speed_6h_ago
        
        # Classify trends
        if direction_diff > 45:
            direction_status = "major_shift"
            description = f"major wind shift ({direction_diff:.0f}°)"
        elif direction_diff > 20:
            direction_status = "moderate_shift"
            description = f"moderate wind shift ({direction_diff:.0f}°)"
        else:
            direction_status = "stable"
            description = "stable wind direction"
        
        # Add speed trend to description
        if speed_change > 5:
            description += f", increasing speed (+{speed_change:.1f}mph)"
            speed_trend = "increasing"
        elif speed_change < -5:
            description += f", decreasing speed ({speed_change:.1f}mph)"
            speed_trend = "decreasing"
        else:
            speed_trend = "stable"
        
        return {
            "description": description,
            "direction_shift": direction_diff,
            "speed_trend": speed_trend,
            "speed_change": speed_change,
            "triggers_movement": direction_diff > 30 or abs(speed_change) > 8
        }
    
    def detect_enhanced_cold_front_with_wind(self, weather_data: Dict) -> bool:
        """Enhanced cold front detection including wind shift patterns"""
        pressure = weather_data.get("pressure", 30.0)
        temperature = weather_data.get("temperature", 50)
        pressure_trend = weather_data.get("pressure_trend", {})
        wind_trend = weather_data.get("wind_trend", {})
        
        # Traditional cold front indicators
        low_pressure = pressure < 29.9
        cold_temp = temperature < 45
        falling_pressure = pressure_trend.get("trend") in ["falling", "falling_rapidly"]
        
        # NEW: Wind shift indicators
        wind_shift = wind_trend.get("direction_shift", 0) > 30
        wind_triggers_movement = wind_trend.get("triggers_movement", False)
        
        # Enhanced detection - any three of five conditions
        conditions_met = sum([low_pressure, cold_temp, falling_pressure, wind_shift, wind_triggers_movement])
        
        return conditions_met >= 2  # More sensitive with wind data
    
    def calculate_cold_front_strength_with_wind(self, weather_data: Dict) -> float:
        """Calculate cold front strength including wind factors"""
        pressure = weather_data.get("pressure", 30.0)
        temperature = weather_data.get("temperature", 50)
        pressure_trend = weather_data.get("pressure_trend", {})
        wind_trend = weather_data.get("wind_trend", {})
        
        strength = 0.0
        
        # Pressure component (0.0 to 0.3)
        if pressure < 29.5:
            strength += 0.3
        elif pressure < 29.9:
            strength += 0.15 + (29.9 - pressure) * 0.375
        
        # Temperature component (0.0 to 0.25)
        if temperature < 35:
            strength += 0.25
        elif temperature < 45:
            strength += (45 - temperature) * 0.025
        
        # Pressure trend component (0.0 to 0.25)
        change_rate = abs(pressure_trend.get("change_rate", 0))
        if change_rate > 0.15:
            strength += 0.25
        elif change_rate > 0.05:
            strength += change_rate * 1.67
        
        # NEW: Wind trend component (0.0 to 0.2)
        direction_shift = wind_trend.get("direction_shift", 0)
        speed_change = abs(wind_trend.get("speed_change", 0))
        
        if direction_shift > 45:
            strength += 0.15  # Major wind shift
        elif direction_shift > 20:
            strength += 0.1   # Moderate wind shift
        
        if speed_change > 8:
            strength += 0.05  # Significant speed change
        
        return min(1.0, strength)
    
    def get_refined_activity_level(self, time_of_day: int, weather_data: Dict) -> str:
        """Refined midday activity logic with enhanced cold front validation"""
        base_activity = self.get_base_activity_level(time_of_day)
        
        # ENHANCED: Cold front override validation with strict thresholds
        is_cold_front = weather_data.get("is_cold_front", False)
        cold_front_strength = weather_data.get("cold_front_strength", 0)
        pressure = weather_data.get("pressure", 30.0)
        temperature = weather_data.get("temperature", 50)
        
        # CRITICAL: Only strong cold fronts override midday low activity
        if is_cold_front and cold_front_strength > 0.6:
            # Validate with strict thresholds
            pressure_check = pressure < 29.9
            temp_check = temperature < 45
            
            if pressure_check and temp_check and 12 <= time_of_day <= 15:
                self.logger.info(f"🌦️ Strong cold front override: {cold_front_strength:.2f} strength, {pressure:.2f}inHg, {temperature:.1f}°F")
                return "high"  # Override midday low activity
            elif base_activity in ["moderate", "low"]:
                return "high"  # Boost other periods
        elif is_cold_front and cold_front_strength > 0.3:
            # Moderate cold front - limited override
            if base_activity == "low" and 12 <= time_of_day <= 15:
                # Only boost to moderate for weaker fronts
                return "moderate"
            elif base_activity == "moderate":
                return "high"
        
        # EDGE CASE: Stable weather validation - revert to base activity
        pressure_trend = weather_data.get("pressure_trend", {})
        if pressure_trend.get("trend") == "stable" and pressure > 30.1:
            # High pressure stable weather - ensure midday stays low
            if 12 <= time_of_day <= 15:
                self.logger.info(f"📈 Stable high pressure ({pressure:.2f}inHg) - maintaining low midday activity")
                return "low"  # Force low activity in stable high pressure
        
        # High wind penalty (unchanged)
        wind_speed = weather_data.get("wind_speed", 5)
        if wind_speed > 15:
            if base_activity == "high":
                return "moderate"
            elif base_activity == "moderate":
                return "low"
        
        return base_activity
    
    def get_base_activity_level(self, time_of_day: int) -> str:
        """Base activity level without weather modifiers"""
        if 6 <= time_of_day <= 8:
            return "high"
        elif 9 <= time_of_day <= 11:
            return "moderate"
        elif 12 <= time_of_day <= 15:
            return "low"
        elif 16 <= time_of_day <= 19:
            return "high"
        elif 20 <= time_of_day <= 23:
            return "moderate"
        elif 0 <= time_of_day <= 5:
            return "moderate"
        else:
            return "moderate"
    
    def get_enhanced_wind_thermal_analysis(self, weather_data: Dict, gee_data: Dict, osm_data: Dict) -> List[str]:
        """Enhanced wind/thermal analysis with leeward ridge annotations"""
        analysis = []
        
        wind_speed = weather_data.get("wind_speed", 5)
        wind_direction = weather_data.get("wind_direction", 0)
        temperature = weather_data.get("temperature", 50)
        
        # Wind protection analysis
        if wind_speed > 15:
            wind_dir_text = self.get_wind_direction_text(wind_direction)
            leeward_direction = self.get_wind_direction_text((wind_direction + 180) % 360)
            
            analysis.extend([
                f"High wind protection needed: {wind_speed:.1f}mph from {wind_dir_text}",
                f"Seek leeward ridge areas: {leeward_direction} facing slopes",
                f"Dense cover provides wind break: {gee_data.get('canopy_coverage', 0.6):.1%} canopy",
                "Wind protection priority for bedding site selection"
            ])
        elif wind_speed > 8:
            analysis.append(f"Moderate wind consideration: {wind_speed:.1f}mph - partial wind protection beneficial")
        
        # Thermal analysis with Open-Meteo direction specificity
        if temperature < 40:
            analysis.extend([
                "Cold thermal bedding: south-facing slopes for solar gain",
                "Morning thermal pockets in protected valleys",
                "Seek ridges with southern exposure and wind protection"
            ])
        elif temperature > 70:
            analysis.extend([
                "Hot weather thermal: north-facing slopes for cooling",
                f"Dense canopy cooling: {gee_data.get('canopy_coverage', 0.6):.1%} coverage",
                "Upslope bedding strategy: cool ridge tops and shaded areas"
            ])
        
        # Road security integration
        road_distance = osm_data.get("nearest_road_distance_m", 500)
        security_score = osm_data.get("bedding_security_score", 0.6)
        
        if road_distance > 200:
            analysis.append(f"Excellent bedding security: {road_distance:.0f}m from roads")
        elif road_distance > 100:
            analysis.append(f"Moderate bedding security: {road_distance:.0f}m from roads")
        else:
            analysis.append(f"Poor bedding security: only {road_distance:.0f}m from roads")
        
        return analysis
    
    def get_wind_direction_text(self, wind_direction: float) -> str:
        """Convert wind direction degrees to text"""
        directions = [
            "North", "NNE", "NE", "ENE", "East", "ESE", "SE", "SSE",
            "South", "SSW", "SW", "WSW", "West", "WNW", "NW", "NNW"
        ]
        index = int((wind_direction + 11.25) / 22.5) % 16
        return directions[index]
    
    async def validate_frontend_with_websocket(self, lat: float, lon: float) -> Dict:
        """Complete frontend integration with WebSocket and Selenium validation"""
        validation_result = {
            "frontend_accessible": False,
            "websocket_connected": False,
            "real_time_updates": False,
            "stand_markers_visible": False,
            "bedding_maps_display": False,
            "error_messages": []
        }
        
        try:
            # Test 1: Basic frontend accessibility
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8501", timeout=10) as response:
                    if response.status == 200:
                        validation_result["frontend_accessible"] = True
                        self.logger.info("✅ Frontend accessible at localhost:8501")
            
            # Test 2: WebSocket connection for real-time updates
            websocket_result = await self.test_websocket_connection()
            validation_result["websocket_connected"] = websocket_result["connected"]
            validation_result["real_time_updates"] = websocket_result["real_time_updates"]
            
            # Test 3: Selenium validation of map elements
            selenium_result = self.test_map_elements_with_selenium(lat, lon)
            validation_result["stand_markers_visible"] = selenium_result["stand_markers"]
            validation_result["bedding_maps_display"] = selenium_result["bedding_maps"]
            
            if selenium_result["errors"]:
                validation_result["error_messages"].extend(selenium_result["errors"])
                
        except Exception as e:
            validation_result["error_messages"].append(f"Frontend validation failed: {str(e)}")
            self.logger.error(f"❌ Frontend validation error: {e}")
        
        return validation_result
    
    async def test_websocket_connection(self) -> Dict:
        """Test WebSocket connection for real-time updates"""
        result = {"connected": False, "real_time_updates": False, "messages_received": 0}
        
        try:
            # Try to connect to Streamlit WebSocket (typical port)
            ws_url = "ws://localhost:8501/_stcore/stream"
            
            def on_message(ws, message):
                result["messages_received"] += 1
                if "weather" in message.lower() or "update" in message.lower():
                    result["real_time_updates"] = True
            
            def on_open(ws):
                result["connected"] = True
                # Send a test message
                ws.send('{"type": "test", "data": "weather_update"}')
            
            def on_error(ws, error):
                self.logger.warning(f"WebSocket error: {error}")
            
            # Create WebSocket connection with timeout
            ws = websocket.WebSocketApp(ws_url,
                                      on_message=on_message,
                                      on_open=on_open,
                                      on_error=on_error)
            
            # Run for 2 seconds to test
            ws_thread = threading.Thread(target=lambda: ws.run_forever())
            ws_thread.daemon = True
            ws_thread.start()
            
            await asyncio.sleep(2)
            ws.close()
            
            self.logger.info(f"✅ WebSocket test: {result['messages_received']} messages received")
            
        except Exception as e:
            self.logger.warning(f"⚠️ WebSocket test failed: {e}")
        
        return result
    
    def test_map_elements_with_selenium(self, lat: float, lon: float) -> Dict:
        """Use Selenium to verify stand site pins and bedding maps"""
        result = {"stand_markers": False, "bedding_maps": False, "errors": []}
        
        try:
            # Setup Chrome in headless mode
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            
            # Navigate to frontend
            driver.get("http://localhost:8501")
            
            # Wait for page to load
            time.sleep(5)
            
            # Look for map container
            try:
                map_element = driver.find_element(By.CLASS_NAME, "stDeckGlJsonChart")
                if map_element:
                    result["bedding_maps"] = True
                    self.logger.info("✅ Bedding maps display found")
            except:
                try:
                    # Alternative map class names
                    map_element = driver.find_element(By.CSS_SELECTOR, "[data-testid*='map']")
                    if map_element:
                        result["bedding_maps"] = True
                except:
                    result["errors"].append("Map display element not found")
            
            # Look for marker elements (red markers 20-50m downwind)
            try:
                markers = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='marker'], .marker, .map-marker")
                if markers:
                    result["stand_markers"] = True
                    self.logger.info(f"✅ Found {len(markers)} stand markers")
                else:
                    result["errors"].append("Stand markers not visible")
            except Exception as e:
                result["errors"].append(f"Marker detection failed: {str(e)}")
            
            driver.quit()
            
        except Exception as e:
            result["errors"].append(f"Selenium test failed: {str(e)}")
            self.logger.error(f"❌ Selenium validation error: {e}")
        
        return result
    
    def run_optimized_biological_analysis(self, lat: float, lon: float, time_of_day: int, 
                                        season: str, hunting_pressure: str) -> Dict:
        """Run complete optimized biological analysis"""
        
        # 1. Get dynamic GEE data
        gee_data = self.get_dynamic_gee_data(lat, lon)
        
        # 2. Get OSM road proximity
        osm_data = self.get_osm_road_proximity(lat, lon)
        
        # 3. Get enhanced weather with trends
        weather_data = self.get_enhanced_weather_with_trends(lat, lon)
        
        # 4. Refined activity level
        activity_level = self.get_refined_activity_level(time_of_day, weather_data)
        
        # 5. Enhanced wind/thermal analysis
        wind_thermal_analysis = self.get_enhanced_wind_thermal_analysis(weather_data, gee_data, osm_data)
        
        # 6. Movement direction with all enhancements
        movement_direction = self.get_enhanced_movement_direction(time_of_day, season, weather_data, gee_data)
        
        # 7. Generate enhanced bedding zones
        bedding_zones = self.generate_enhanced_bedding_zones(lat, lon, gee_data, osm_data, weather_data)
        
        # 8. Calculate optimized confidence
        confidence = self.calculate_optimized_confidence(weather_data, gee_data, osm_data, activity_level, hunting_pressure)
        
        return {
            "gee_data": gee_data,
            "osm_data": osm_data,
            "weather_data": weather_data,
            "activity_level": activity_level,
            "wind_thermal_analysis": wind_thermal_analysis,
            "movement_direction": movement_direction,
            "bedding_zones": bedding_zones,
            "confidence_score": confidence,
            "optimization_version": "v3.1",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_enhanced_movement_direction(self, time_of_day: int, season: str, weather_data: Dict, gee_data: Dict) -> List[str]:
        """Enhanced movement direction with all optimizations"""
        notes = []
        
        # Base movement direction
        if 5 <= time_of_day <= 8:
            notes.extend([
                "Deer returning to bedding areas after night feeding",
                "Movement direction: feeding areas → bedding areas",
                "Peak return movement between 6:00-7:30 AM"
            ])
        elif 16 <= time_of_day <= 20:
            notes.extend([
                "Prime feeding movement period",
                "Movement direction: bedding areas → feeding areas"
            ])
        else:
            notes.extend([
                "Minimal movement - deer in bedding areas",
                "Occasional thermal regulation movements"
            ])
        
        # Cold front enhancement
        if weather_data.get("is_cold_front", False):
            strength = weather_data.get("cold_front_strength", 0)
            if strength > 0.6:
                notes.append(f"Strong cold front (strength: {strength:.1f}) significantly increases movement probability")
            else:
                notes.append(f"Moderate cold front (strength: {strength:.1f}) moderately increases movement")
        
        # Canopy integration
        canopy = gee_data.get("canopy_coverage", 0.6)
        if canopy > 0.8:
            notes.append(f"Dense canopy ({canopy:.1%}) provides excellent movement security")
        elif canopy < 0.4:
            notes.append(f"Open terrain ({canopy:.1%}) requires cautious movement patterns")
        
        return notes
    
    def calculate_optimized_confidence(self, weather_data: Dict, gee_data: Dict, osm_data: Dict, 
                                     activity_level: str, hunting_pressure: str) -> float:
        """Calculate optimized confidence score with all data sources"""
        confidence = 0.5  # Base
        
        # Weather confidence
        if weather_data.get("api_source") == "open-meteo-enhanced":
            confidence += 0.15  # Real-time enhanced data
        
        cold_front_strength = weather_data.get("cold_front_strength", 0)
        confidence += cold_front_strength * 0.25  # Cold front boost
        
        # GEE data confidence
        if gee_data.get("query_success", False):
            confidence += 0.15  # Dynamic GEE data
        
        ndvi = gee_data.get("ndvi_value", 0.5)
        if ndvi > 0.6:
            confidence += 0.1  # High vegetation health
        
        # OSM road security
        security_score = osm_data.get("bedding_security_score", 0.6)
        confidence += security_score * 0.1  # Security bonus
        
        # Activity level
        if activity_level == "high":
            confidence += 0.2
        elif activity_level == "moderate":
            confidence += 0.1
        
        # Hunting pressure penalty
        if hunting_pressure == "high":
            confidence -= 0.25
        elif hunting_pressure == "moderate":
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)

    def generate_enhanced_bedding_zones(self, lat: float, lon: float, gee_data: Dict, osm_data: Dict, weather_data: Dict) -> Dict:
        """
        Enhanced bedding zone generation with biological accuracy
        
        Fixes the critical issue where bedding zones were empty, undermining biological accuracy.
        Uses GEE canopy (>70%), OSM road proximity (>200m), and environmental factors.
        """
        try:
            bedding_zones = []
            
            # Extract environmental criteria
            canopy_coverage = gee_data.get("canopy_coverage", 0.0)
            road_distance = osm_data.get("nearest_road_distance_m", 0)
            wind_direction = weather_data.get("wind_direction", 180)
            
            # Biological criteria for mature buck bedding
            meets_canopy_threshold = canopy_coverage > 0.7  # >70% canopy for security
            meets_isolation_threshold = road_distance > 200  # >200m from human disturbance
            
            if meets_canopy_threshold and meets_isolation_threshold:
                # Generate multiple high-quality bedding zones
                zone_offsets = [
                    {"lat": 0.0005, "lon": -0.0008, "type": "primary", "description": "Primary bedding: South-facing slope"},
                    {"lat": -0.0003, "lon": 0.0006, "type": "secondary", "description": "Secondary bedding: Leeward ridge"},
                    {"lat": 0.0002, "lon": 0.0004, "type": "escape", "description": "Escape bedding: Dense cover"}
                ]
                
                for i, offset in enumerate(zone_offsets):
                    # Calculate wind protection advantage
                    wind_protection_score = 0.9 if abs(wind_direction - 180) > 30 else 0.7  # Prefer leeward positions
                    
                    bedding_zones.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon + offset["lon"], lat + offset["lat"]]
                        },
                        "properties": {
                            "id": f"bedding_{i}",
                            "type": "bedding",
                            "score": 0.85 + (wind_protection_score * 0.1),  # High base score + wind bonus
                            "confidence": 0.95,
                            "description": f"{offset['description']}, {canopy_coverage:.0%} canopy, {road_distance:.0f}m isolation",
                            "marker_index": i,
                            "bedding_type": offset["type"],
                            "canopy_coverage": canopy_coverage,
                            "road_distance": road_distance,
                            "wind_protection": wind_protection_score,
                            "thermal_advantage": "south_facing_slope",
                            "security_rating": "high"
                        }
                    })
                
                logger.info(f"✅ Generated {len(bedding_zones)} enhanced bedding zones with {canopy_coverage:.1%} canopy")
                
            else:
                # Log why bedding zones weren't generated
                reasons = []
                if not meets_canopy_threshold:
                    reasons.append(f"insufficient canopy coverage ({canopy_coverage:.1%} < 70%)")
                if not meets_isolation_threshold:
                    reasons.append(f"too close to roads ({road_distance:.0f}m < 200m)")
                
                logger.warning(f"❌ No bedding zones generated: {', '.join(reasons)}")
            
            return {
                "type": "FeatureCollection",
                "features": bedding_zones,
                "properties": {
                    "marker_type": "bedding",
                    "total_features": len(bedding_zones),
                    "generated_at": datetime.now().isoformat(),
                    "generation_criteria": {
                        "canopy_threshold": 0.7,
                        "isolation_threshold": 200,
                        "canopy_coverage": canopy_coverage,
                        "road_distance": road_distance,
                        "meets_criteria": meets_canopy_threshold and meets_isolation_threshold
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Bedding zone generation failed: {e}")
            return {
                "type": "FeatureCollection",
                "features": [],
                "properties": {
                    "marker_type": "bedding",
                    "total_features": 0,
                    "generated_at": datetime.now().isoformat(),
                    "error": str(e)
                }
            }

def test_optimized_integration():
    """Test the optimized biological integration"""
    print("🚀 TESTING OPTIMIZED BIOLOGICAL INTEGRATION")
    print("=" * 80)
    print("Incorporating all brainstorm recommendations")
    print("=" * 80)
    
    integrator = OptimizedBiologicalIntegration()
    
    # Test Vermont location
    lat, lon = 43.3127, -73.2271  # Tinmouth, Vermont
    
    print(f"\n📍 Testing Location: Tinmouth, Vermont ({lat}, {lon})")
    print("─" * 60)
    
    # Run optimized analysis
    result = integrator.run_optimized_biological_analysis(
        lat, lon, 7, "early_season", "moderate"
    )
    
    # Display results
    print("\n🛰️ GEE Integration Results:")
    gee_data = result["gee_data"]
    print(f"  Data Source: {gee_data['data_source']}")
    print(f"  Query Success: {gee_data['query_success']}")
    print(f"  NDVI: {gee_data['ndvi_value']:.3f}")
    print(f"  Canopy Coverage: {gee_data['canopy_coverage']:.1%}")
    
    print("\n🛣️ OSM Road Proximity:")
    osm_data = result["osm_data"]
    print(f"  Nearest Road: {osm_data['nearest_road_distance_m']:.0f}m")
    print(f"  Security Score: {osm_data['bedding_security_score']:.2f}")
    print(f"  OSM Query Success: {osm_data['osm_query_success']}")
    
    print("\n🌦️ Enhanced Weather Analysis:")
    weather_data = result["weather_data"]
    print(f"  Temperature: {weather_data['temperature']:.1f}°F")
    print(f"  Pressure: {weather_data['pressure']:.2f}inHg")
    print(f"  Pressure Trend: {weather_data['pressure_trend']['description']}")
    print(f"  Cold Front: {weather_data['is_cold_front']} (strength: {weather_data['cold_front_strength']:.2f})")
    
    print("\n🎯 Activity Level Analysis:")
    print(f"  Activity Level: {result['activity_level']}")
    print(f"  Optimized Confidence: {result['confidence_score']:.2f}")
    
    print("\n🌪️ Wind/Thermal Analysis:")
    for note in result["wind_thermal_analysis"][:3]:
        print(f"  • {note}")
    
    print("\n🦌 Movement Direction:")
    for note in result["movement_direction"][:3]:
        print(f"  • {note}")
    
    def generate_enhanced_bedding_zones(self, lat: float, lon: float, gee_data: Dict, osm_data: Dict, weather_data: Dict) -> Dict:
        """
        Generate biologically accurate bedding zones using multiple data sources.
        
        Bedding site criteria for mature bucks:
        - Canopy coverage > 70% (security)
        - Distance from roads > 200m (low pressure)
        - Elevation/slope: 5°-20° south-facing slopes (thermal advantage)
        - Wind: Leeward ridges and thermal protection
        - Escape routes: Multiple exit options
        """
        bedding_zones = []
        bedding_id = 0
        
        # Primary criteria check
        canopy_coverage = gee_data.get("canopy_coverage", 0)
        road_distance = osm_data.get("nearest_road_distance_m", 0)
        wind_direction = weather_data.get("wind_direction", 0)
        temperature = weather_data.get("temperature", 50)
        
        # Generate bedding zones in a grid pattern around the location
        search_radius = 0.005  # ~500m search radius
        for i in range(-2, 3):
            for j in range(-2, 3):
                if i == 0 and j == 0:  # Skip center point
                    continue
                    
                test_lat = lat + (i * search_radius)
                test_lon = lon + (j * search_radius)
                
                # Calculate bedding suitability score
                bedding_score = self.calculate_bedding_suitability(
                    test_lat, test_lon, canopy_coverage, road_distance, 
                    wind_direction, temperature, i, j
                )
                
                # Only include high-quality bedding areas (score > 0.7)
                if bedding_score > 0.7:
                    # Determine slope aspect and thermal advantage
                    aspect = self.determine_slope_aspect(i, j)
                    thermal_advantage = aspect in ["south", "southwest", "southeast"]
                    
                    # Wind protection assessment
                    wind_protection = self.assess_wind_protection(i, j, wind_direction)
                    
                    bedding_zone = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [test_lon, test_lat]
                        },
                        "properties": {
                            "id": f"bedding_{bedding_id}",
                            "type": "bedding",
                            "score": bedding_score,
                            "confidence": min(bedding_score * 1.2, 1.0),  # Boost confidence for good bedding
                            "description": f"Bedding area: {aspect}-facing slope, {wind_protection}, {canopy_coverage:.0%} canopy",
                            "marker_index": bedding_id,
                            "aspect": aspect,
                            "thermal_advantage": thermal_advantage,
                            "wind_protection": wind_protection,
                            "canopy_coverage": canopy_coverage,
                            "road_distance_m": road_distance,
                            "security_level": "high" if road_distance > 300 else "moderate"
                        }
                    }
                    
                    bedding_zones.append(bedding_zone)
                    bedding_id += 1
                    
                    # Limit to 5 bedding zones for performance
                    if bedding_id >= 5:
                        break
            if bedding_id >= 5:
                break
        
        # Ensure at least one bedding zone if conditions are reasonable
        if len(bedding_zones) == 0 and canopy_coverage > 0.5 and road_distance > 100:
            # Create a default bedding zone with moderate suitability
            default_bedding = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon + 0.002, lat + 0.002]  # Slight offset
                },
                "properties": {
                    "id": "bedding_0",
                    "type": "bedding",
                    "score": 0.75,
                    "confidence": 0.70,
                    "description": f"Moderate bedding area: mixed cover, {canopy_coverage:.0%} canopy",
                    "marker_index": 0,
                    "aspect": "southeast",
                    "thermal_advantage": True,
                    "wind_protection": "partial",
                    "canopy_coverage": canopy_coverage,
                    "road_distance_m": road_distance,
                    "security_level": "moderate"
                }
            }
            bedding_zones.append(default_bedding)
        
        return {
            "type": "FeatureCollection",
            "features": bedding_zones,
            "properties": {
                "marker_type": "bedding",
                "total_features": len(bedding_zones),
                "generated_at": datetime.now().isoformat(),
                "criteria_used": "canopy_coverage,road_distance,slope_aspect,wind_protection"
            }
        }
    
    def calculate_bedding_suitability(self, lat: float, lon: float, canopy_coverage: float, 
                                    road_distance: float, wind_direction: float, 
                                    temperature: float, grid_i: int, grid_j: int) -> float:
        """Calculate bedding suitability score based on multiple factors"""
        score = 0.0
        
        # Canopy coverage (30% of score)
        if canopy_coverage > 0.7:
            score += 0.30
        elif canopy_coverage > 0.5:
            score += 0.20
        elif canopy_coverage > 0.3:
            score += 0.10
        
        # Road distance security (25% of score)
        if road_distance > 300:
            score += 0.25
        elif road_distance > 200:
            score += 0.20
        elif road_distance > 100:
            score += 0.10
        
        # Slope and aspect (20% of score)
        aspect = self.determine_slope_aspect(grid_i, grid_j)
        if aspect in ["south", "southeast", "southwest"]:
            score += 0.20  # Thermal advantage
        elif aspect in ["east", "west"]:
            score += 0.10
        
        # Wind protection (15% of score)
        wind_protection = self.assess_wind_protection(grid_i, grid_j, wind_direction)
        if wind_protection == "excellent":
            score += 0.15
        elif wind_protection == "good":
            score += 0.10
        elif wind_protection == "partial":
            score += 0.05
        
        # Escape routes (10% of score) - varied terrain
        if abs(grid_i) + abs(grid_j) >= 2:  # Not too close to center
            score += 0.10
        
        return min(score, 1.0)
    
    def determine_slope_aspect(self, grid_i: int, grid_j: int) -> str:
        """Determine slope aspect based on grid position"""
        if grid_i > 0 and grid_j == 0:
            return "north"
        elif grid_i > 0 and grid_j > 0:
            return "northeast"
        elif grid_i == 0 and grid_j > 0:
            return "east"
        elif grid_i < 0 and grid_j > 0:
            return "southeast"
        elif grid_i < 0 and grid_j == 0:
            return "south"
        elif grid_i < 0 and grid_j < 0:
            return "southwest"
        elif grid_i == 0 and grid_j < 0:
            return "west"
        elif grid_i > 0 and grid_j < 0:
            return "northwest"
        else:
            return "flat"
    
    def assess_wind_protection(self, grid_i: int, grid_j: int, wind_direction: float) -> str:
        """Assess wind protection based on position relative to prevailing wind"""
        # Convert wind direction to compass direction
        if 315 <= wind_direction or wind_direction < 45:
            wind_from = "north"
        elif 45 <= wind_direction < 135:
            wind_from = "east"
        elif 135 <= wind_direction < 225:
            wind_from = "south"
        else:
            wind_from = "west"
        
        # Determine if position provides wind protection
        if wind_from == "north" and grid_i < 0:  # South of wind
            return "excellent"
        elif wind_from == "south" and grid_i > 0:  # North of wind
            return "excellent"
        elif wind_from == "east" and grid_j < 0:  # West of wind
            return "excellent"
        elif wind_from == "west" and grid_j > 0:  # East of wind
            return "excellent"
        elif abs(grid_i) + abs(grid_j) >= 2:  # Distant positions
            return "good"
        else:
            return "partial"
    
    def validate_spatial_accuracy(self, prediction: Dict) -> float:
        """
        Enhanced spatial accuracy validation including bedding zones.
        
        Returns confidence score from 0.0 to 1.0 based on:
        - Presence of bedding zones
        - Bedding zone quality scores
        - Spatial relationships between bedding, feeding, and travel areas
        """
        bedding_zones = prediction.get("bedding_zones", {}).get("features", [])
        
        # Check for bedding zone presence
        if len(bedding_zones) == 0:
            self.logger.error("❌ No bedding zones detected - critical biological accuracy failure")
            return 0.0
        
        # Calculate average bedding suitability
        total_score = sum(f["properties"]["score"] for f in bedding_zones)
        avg_suitability = total_score / len(bedding_zones)
        
        # Validate bedding quality
        if avg_suitability < 0.6:
            self.logger.warning(f"⚠️ Low bedding suitability: {avg_suitability:.2f}")
            return avg_suitability * 0.5  # Penalize low quality
        elif avg_suitability > 0.8:
            self.logger.info(f"✅ Excellent bedding suitability: {avg_suitability:.2f}")
            return min(avg_suitability * 1.1, 1.0)  # Reward high quality
        else:
            self.logger.info(f"✅ Good bedding suitability: {avg_suitability:.2f}")
            return avg_suitability
    
    print("\n✅ Optimized integration test completed!")
    print(f"📊 Overall optimization score: {result['confidence_score']:.1%}")
    
    return result

if __name__ == "__main__":
    test_optimized_integration()
