#!/usr/bin/env python3
"""
Real OSM Security Data Integration

Uses actual OpenStreetMap data for security threat analysis.
NO PLACEHOLDERS - only real data from OSM Overpass API.

Author: Real Data Implementation
Version: 1.0.0
"""

import requests
import json
import logging
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OSMFeature:
    """Represents a real OSM feature"""
    feature_type: str
    distance: float
    lat: float
    lon: float
    tags: Dict[str, str]
    osm_id: str

class RealOSMSecurityData:
    """Get real security data from OpenStreetMap - NO PLACEHOLDERS"""
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.timeout = 30
        
    def get_comprehensive_security_data(self, lat: float, lon: float, 
                                      radius: int = 2000) -> Dict[str, Any]:
        """
        Get comprehensive real security data from OSM
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius: Search radius in meters
            
        Returns:
            Dictionary with REAL security threat data from OSM
        """
        try:
            logger.info(f"🔍 Querying real OSM data for {lat:.4f}, {lon:.4f} within {radius}m")
            
            # Get real data from OSM
            security_data = {
                'parking_areas': self.get_real_parking_areas(lat, lon, radius),
                'trail_networks': self.get_real_trail_networks(lat, lon, radius),
                'road_network': self.get_real_road_network(lat, lon, radius),
                'buildings': self.get_real_buildings(lat, lon, radius),
                'access_points': self.get_real_access_points(lat, lon, radius),
                'analysis_center': {'lat': lat, 'lon': lon},
                'search_radius': radius,
                'data_source': 'openstreetmap_overpass_api'
            }
            
            # Calculate real derived metrics
            security_data['road_density_per_km2'] = self._calculate_real_road_density(
                security_data['road_network'], radius
            )
            security_data['access_density_per_km2'] = self._calculate_real_access_density(
                security_data['parking_areas'] + security_data['access_points'], radius
            )
            security_data['nearest_threats'] = self._find_real_nearest_threats(security_data)
            security_data['threat_summary'] = self._summarize_real_threats(security_data)
            
            logger.info(f"✅ Real OSM data retrieved: {len(security_data['parking_areas'])} parking, "
                       f"{len(security_data['trail_networks'])} trails, "
                       f"{len(security_data['road_network'])} roads, "
                       f"{len(security_data['buildings'])} buildings")
            
            return security_data
            
        except Exception as e:
            logger.error(f"Real OSM security data retrieval failed: {e}")
            # Return empty real data structure (no fake placeholders)
            return self._empty_real_data_structure()
    
    def get_real_parking_areas(self, lat: float, lon: float, radius: int) -> List[OSMFeature]:
        """Get REAL parking areas from OSM"""
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          way["amenity"="parking"](around:{radius},{lat},{lon});
          node["amenity"="parking"](around:{radius},{lat},{lon});
          way["highway"="service"]["service"="parking_aisle"](around:{radius},{lat},{lon});
          way["leisure"="fishing"]["parking"](around:{radius},{lat},{lon});
          way["tourism"="camp_site"](around:{radius},{lat},{lon});
          node["tourism"="camp_site"](around:{radius},{lat},{lon});
          way["amenity"="parking_space"](around:{radius},{lat},{lon});
          node["amenity"="parking_space"](around:{radius},{lat},{lon});
        );
        out geom;
        """
        
        features = self._execute_real_overpass_query(query, lat, lon, 'parking')
        logger.debug(f"Found {len(features)} real parking areas from OSM")
        return features
    
    def get_real_trail_networks(self, lat: float, lon: float, radius: int) -> List[OSMFeature]:
        """Get REAL trail networks from OSM"""
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          way["highway"="path"](around:{radius},{lat},{lon});
          way["highway"="track"](around:{radius},{lat},{lon});
          way["highway"="footway"](around:{radius},{lat},{lon});
          way["highway"="cycleway"](around:{radius},{lat},{lon});
          way["highway"="bridleway"](around:{radius},{lat},{lon});
          way["route"="hiking"](around:{radius},{lat},{lon});
          way["trail_visibility"](around:{radius},{lat},{lon});
          relation["route"="hiking"](around:{radius},{lat},{lon});
          way["highway"="service"]["access"="forestry"](around:{radius},{lat},{lon});
          way["highway"="service"]["access"="private"](around:{radius},{lat},{lon});
        );
        out geom;
        """
        
        features = self._execute_real_overpass_query(query, lat, lon, 'trail')
        logger.debug(f"Found {len(features)} real trails from OSM")
        return features
    
    def get_real_road_network(self, lat: float, lon: float, radius: int) -> List[OSMFeature]:
        """Get REAL road network from OSM"""
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          way["highway"="motorway"](around:{radius},{lat},{lon});
          way["highway"="trunk"](around:{radius},{lat},{lon});
          way["highway"="primary"](around:{radius},{lat},{lon});
          way["highway"="secondary"](around:{radius},{lat},{lon});
          way["highway"="tertiary"](around:{radius},{lat},{lon});
          way["highway"="residential"](around:{radius},{lat},{lon});
          way["highway"="unclassified"](around:{radius},{lat},{lon});
          way["highway"="service"](around:{radius},{lat},{lon});
          way["highway"="track"]["access"!="private"](around:{radius},{lat},{lon});
        );
        out geom;
        """
        
        features = self._execute_real_overpass_query(query, lat, lon, 'road')
        logger.debug(f"Found {len(features)} real roads from OSM")
        return features
    
    def get_real_buildings(self, lat: float, lon: float, radius: int) -> List[OSMFeature]:
        """Get REAL buildings from OSM"""
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          way["building"](around:{radius},{lat},{lon});
          node["building"](around:{radius},{lat},{lon});
          way["amenity"="restaurant"](around:{radius},{lat},{lon});
          way["amenity"="cafe"](around:{radius},{lat},{lon});
          way["amenity"="shop"](around:{radius},{lat},{lon});
          way["amenity"="fuel"](around:{radius},{lat},{lon});
          node["amenity"="restaurant"](around:{radius},{lat},{lon});
          node["amenity"="cafe"](around:{radius},{lat},{lon});
          node["amenity"="shop"](around:{radius},{lat},{lon});
          node["amenity"="fuel"](around:{radius},{lat},{lon});
          way["tourism"="hotel"](around:{radius},{lat},{lon});
          way["tourism"="motel"](around:{radius},{lat},{lon});
          way["tourism"="guest_house"](around:{radius},{lat},{lon});
        );
        out geom;
        """
        
        features = self._execute_real_overpass_query(query, lat, lon, 'building')
        logger.debug(f"Found {len(features)} real buildings from OSM")
        return features
    
    def get_real_access_points(self, lat: float, lon: float, radius: int) -> List[OSMFeature]:
        """Get REAL access points (gates, trailheads, boat launches) from OSM"""
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          node["barrier"="gate"](around:{radius},{lat},{lon});
          way["barrier"="gate"](around:{radius},{lat},{lon});
          node["information"="trailhead"](around:{radius},{lat},{lon});
          way["information"="trailhead"](around:{radius},{lat},{lon});
          way["leisure"="slipway"](around:{radius},{lat},{lon});
          node["leisure"="slipway"](around:{radius},{lat},{lon});
          way["amenity"="boat_rental"](around:{radius},{lat},{lon});
          node["amenity"="boat_rental"](around:{radius},{lat},{lon});
          node["highway"="trailhead"](around:{radius},{lat},{lon});
          way["access"="destination"](around:{radius},{lat},{lon});
        );
        out geom;
        """
        
        features = self._execute_real_overpass_query(query, lat, lon, 'access_point')
        logger.debug(f"Found {len(features)} real access points from OSM")
        return features
    
    def _execute_real_overpass_query(self, query: str, center_lat: float, center_lon: float, 
                                   feature_type: str) -> List[OSMFeature]:
        """Execute real Overpass API query and return actual OSM features"""
        try:
            logger.debug(f"Executing real OSM query for {feature_type}")
            
            response = requests.post(self.overpass_url, data=query, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            features = []
            
            for element in data.get('elements', []):
                feature = self._parse_real_osm_element(element, center_lat, center_lon, feature_type)
                if feature:
                    features.append(feature)
            
            return features
            
        except requests.exceptions.Timeout:
            logger.warning(f"OSM query timeout for {feature_type} - no fake data returned")
            return []
        except requests.exceptions.RequestException as e:
            logger.warning(f"OSM query failed for {feature_type}: {e} - no fake data returned")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in OSM query for {feature_type}: {e}")
            return []
    
    def _parse_real_osm_element(self, element: Dict, center_lat: float, center_lon: float, 
                              feature_type: str) -> Optional[OSMFeature]:
        """Parse real OSM element into OSMFeature"""
        try:
            # Get real coordinates based on element type
            if element['type'] == 'node':
                feat_lat, feat_lon = element['lat'], element['lon']
            elif element['type'] == 'way' and 'geometry' in element and element['geometry']:
                # Use center point of way geometry
                geometry = element['geometry']
                if geometry:
                    # Calculate centroid of way
                    lats = [pt['lat'] for pt in geometry]
                    lons = [pt['lon'] for pt in geometry]
                    feat_lat = sum(lats) / len(lats)
                    feat_lon = sum(lons) / len(lons)
                else:
                    return None
            else:
                return None
            
            # Calculate real distance from center
            distance = self._calculate_real_distance(center_lat, center_lon, feat_lat, feat_lon)
            
            # Get real OSM tags
            tags = element.get('tags', {})
            osm_id = f"{element['type']}/{element['id']}"
            
            return OSMFeature(
                feature_type=feature_type,
                distance=distance,
                lat=feat_lat,
                lon=feat_lon,
                tags=tags,
                osm_id=osm_id
            )
            
        except Exception as e:
            logger.debug(f"Error parsing real OSM element: {e}")
            return None
    
    def _calculate_real_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate real distance between two points in meters using Haversine formula"""
        # Earth's radius in meters
        R = 6371000
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _calculate_real_road_density(self, roads: List[OSMFeature], radius: int) -> float:
        """Calculate real road density per km² from actual OSM road data"""
        if not roads:
            return 0.0
        
        # Calculate actual search area in km²
        area_km2 = (math.pi * radius * radius) / 1000000
        
        # Count unique roads (avoid double counting)
        unique_roads = len(set(road.osm_id for road in roads))
        
        return unique_roads / area_km2
    
    def _calculate_real_access_density(self, access_points: List[OSMFeature], radius: int) -> float:
        """Calculate real access point density per km² from actual OSM data"""
        if not access_points:
            return 0.0
        
        area_km2 = (math.pi * radius * radius) / 1000000
        unique_access = len(set(ap.osm_id for ap in access_points))
        
        return unique_access / area_km2
    
    def _find_real_nearest_threats(self, security_data: Dict) -> Dict[str, float]:
        """Find real distances to nearest security threats from actual OSM data"""
        nearest = {
            'nearest_parking': None,
            'nearest_trail': None,
            'nearest_road': None,
            'nearest_building': None,
            'nearest_access': None
        }
        
        # Find actual nearest of each type from real OSM data
        for category, key in [
            ('parking_areas', 'nearest_parking'),
            ('trail_networks', 'nearest_trail'),
            ('road_network', 'nearest_road'),
            ('buildings', 'nearest_building'),
            ('access_points', 'nearest_access')
        ]:
            features = security_data.get(category, [])
            if features:
                nearest_feature = min(features, key=lambda f: f.distance)
                nearest[key] = {
                    'distance': nearest_feature.distance,
                    'osm_id': nearest_feature.osm_id,
                    'tags': nearest_feature.tags,
                    'coordinates': {'lat': nearest_feature.lat, 'lon': nearest_feature.lon}
                }
        
        return nearest
    
    def _summarize_real_threats(self, security_data: Dict) -> Dict[str, Any]:
        """Summarize real threat levels based on actual OSM data"""
        threats = security_data['nearest_threats']
        
        summary = {
            'overall_threat_level': 'low',
            'primary_threats': [],
            'threat_count': {
                'parking': len(security_data['parking_areas']),
                'trails': len(security_data['trail_networks']),
                'roads': len(security_data['road_network']),
                'buildings': len(security_data['buildings']),
                'access_points': len(security_data['access_points'])
            },
            'densities': {
                'road_density': security_data['road_density_per_km2'],
                'access_density': security_data['access_density_per_km2']
            }
        }
        
        # Determine threat level based on actual data
        threat_factors = []
        
        # Check parking proximity (critical for mature bucks)
        if threats['nearest_parking'] and threats['nearest_parking']['distance'] < 500:
            threat_factors.append('close_parking')
            summary['primary_threats'].append(f"Parking {threats['nearest_parking']['distance']:.0f}m away")
        
        # Check trail density
        if security_data['trail_networks'] and len(security_data['trail_networks']) > 5:
            threat_factors.append('high_trail_density')
            summary['primary_threats'].append(f"High trail density ({len(security_data['trail_networks'])} trails)")
        
        # Check road density
        if security_data['road_density_per_km2'] > 3.0:
            threat_factors.append('high_road_density')
            summary['primary_threats'].append(f"High road density ({security_data['road_density_per_km2']:.1f}/km²)")
        
        # Check building proximity
        if threats['nearest_building'] and threats['nearest_building']['distance'] < 300:
            threat_factors.append('close_buildings')
            summary['primary_threats'].append(f"Building {threats['nearest_building']['distance']:.0f}m away")
        
        # Determine overall threat level
        if len(threat_factors) >= 3:
            summary['overall_threat_level'] = 'extreme'
        elif len(threat_factors) >= 2:
            summary['overall_threat_level'] = 'high'
        elif len(threat_factors) >= 1:
            summary['overall_threat_level'] = 'moderate'
        else:
            summary['overall_threat_level'] = 'low'
        
        return summary
    
    def _empty_real_data_structure(self) -> Dict[str, Any]:
        """Return empty real data structure when OSM query fails (NO FAKE DATA)"""
        return {
            'parking_areas': [],
            'trail_networks': [],
            'road_network': [],
            'buildings': [],
            'access_points': [],
            'road_density_per_km2': 0.0,
            'access_density_per_km2': 0.0,
            'nearest_threats': {
                'nearest_parking': None,
                'nearest_trail': None,
                'nearest_road': None,
                'nearest_building': None,
                'nearest_access': None
            },
            'threat_summary': {
                'overall_threat_level': 'unknown',
                'primary_threats': ['OSM data unavailable'],
                'threat_count': {
                    'parking': 0,
                    'trails': 0,
                    'roads': 0,
                    'buildings': 0,
                    'access_points': 0
                },
                'densities': {
                    'road_density': 0.0,
                    'access_density': 0.0
                }
            },
            'data_source': 'osm_query_failed'
        }

# Global instance
_real_osm_security = None

def get_real_osm_security() -> RealOSMSecurityData:
    """Get the global real OSM security data instance"""
    global _real_osm_security
    if _real_osm_security is None:
        _real_osm_security = RealOSMSecurityData()
    return _real_osm_security
