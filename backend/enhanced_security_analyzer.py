#!/usr/bin/env python3
"""
Enhanced Security Analysis for Mature Buck Predictions

Addresses the critical "seeking security" characteristic by analyzing
human pressure indicators, trail camera density, and access points.
USES REAL OPENSTREETMAP DATA - NO PLACEHOLDERS.

Author: Real Data Implementation Team
Version: 2.0.0 - Real OSM Integration
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from .real_osm_security import get_real_osm_security, OSMFeature

logger = logging.getLogger(__name__)

class EnhancedSecurityAnalyzer:
    """Advanced security analysis for pressure-sensitive mature bucks"""
    
    def __init__(self):
        pass
        
    def analyze_security_threats(self, lat: float, lon: float, radius_km: float = 2.0) -> Dict[str, Any]:
        """
        Comprehensive security threat analysis for mature buck habitat using REAL OSM data.
        
        Args:
            lat: Center latitude
            lon: Center longitude  
            radius_km: Analysis radius in kilometers
            
        Returns:
            Security analysis results with REAL threat assessments from OSM
        """
        try:
            logger.info(f"🔍 Starting REAL OSM security analysis for {lat:.4f}, {lon:.4f}")
            
            # Get REAL security data from OpenStreetMap
            radius_meters = int(radius_km * 1000)
            osm_security = get_real_osm_security()
            real_security_data = osm_security.get_comprehensive_security_data(lat, lon, radius_meters)
            
            # Analyze different threat categories using REAL data
            security_analysis = {
                'overall_security_score': 0.0,
                'threat_categories': {
                    'road_threats': self._analyze_real_road_threats(real_security_data),
                    'structure_threats': self._analyze_real_structure_threats(real_security_data),
                    'access_threats': self._analyze_real_access_threats(real_security_data),
                    'trail_threats': self._analyze_real_trail_threats(real_security_data)
                },
                'security_recommendations': [],
                'pressure_level': 'unknown',
                'confidence': 0.0,
                'real_osm_data': real_security_data,  # Include raw OSM data for transparency
                'data_source': 'openstreetmap_overpass_api'
            }
            
            # Calculate overall security score based on REAL data
            security_analysis['overall_security_score'] = self._calculate_real_security_score(
                security_analysis['threat_categories'], real_security_data
            )
            
            # Determine pressure level from REAL threats
            security_analysis['pressure_level'] = self._determine_pressure_level(
                security_analysis['overall_security_score']
            )
            
            # Generate recommendations based on REAL OSM threats
            security_analysis['security_recommendations'] = self._generate_real_security_recommendations(
                security_analysis['threat_categories'], real_security_data
            )
            
            # Calculate confidence based on REAL data quality
            security_analysis['confidence'] = self._calculate_real_data_confidence(real_security_data)
            
            logger.info(f"✅ REAL OSM security analysis complete - Score: {security_analysis['overall_security_score']:.1f}, "
                       f"Pressure: {security_analysis['pressure_level']}, "
                       f"OSM Features: {len(real_security_data.get('parking_areas', []))}P "
                       f"{len(real_security_data.get('trail_networks', []))}T "
                       f"{len(real_security_data.get('road_network', []))}R "
                       f"{len(real_security_data.get('buildings', []))}B")
            
            return security_analysis
            
        except Exception as e:
            logger.error(f"REAL OSM security analysis failed: {e}")
            return self._fallback_security_analysis()
    
    def _analyze_real_road_threats(self, real_security_data: Dict) -> Dict[str, Any]:
        """Analyze road-based security threats using REAL OSM road data"""
        road_network = real_security_data.get('road_network', [])
        road_density = real_security_data.get('road_density_per_km2', 0.0)
        
        road_threats = {
            'road_count': len(road_network),
            'road_density_per_km2': road_density,
            'nearest_road_distance': None,
            'nearest_road_type': None,
            'road_types': {},
            'threat_level': 'low'
        }
        
        if road_network:
            # Find nearest road from REAL OSM data
            nearest_road = min(road_network, key=lambda r: r.distance)
            road_threats['nearest_road_distance'] = nearest_road.distance
            road_threats['nearest_road_type'] = nearest_road.tags.get('highway', 'unknown')
            
            # Count road types from REAL OSM tags
            for road in road_network:
                highway_type = road.tags.get('highway', 'unknown')
                road_threats['road_types'][highway_type] = road_threats['road_types'].get(highway_type, 0) + 1
        
        # Determine threat level based on REAL data
        nearest_distance = road_threats['nearest_road_distance'] or 9999
        
        # Major roads (highways, primary, secondary) are more threatening
        major_road_types = ['motorway', 'trunk', 'primary', 'secondary']
        has_major_roads = any(rt in road_threats['road_types'] for rt in major_road_types)
        
        if nearest_distance < 300 or (has_major_roads and nearest_distance < 800) or road_density > 8.0:
            road_threats['threat_level'] = 'extreme'
        elif nearest_distance < 600 or (has_major_roads and nearest_distance < 1200) or road_density > 5.0:
            road_threats['threat_level'] = 'high'
        elif nearest_distance < 1000 or road_density > 2.0:
            road_threats['threat_level'] = 'moderate'
        else:
            road_threats['threat_level'] = 'low'
            
        return road_threats
    
    def _analyze_real_structure_threats(self, real_security_data: Dict) -> Dict[str, Any]:
        """Analyze building and structure threats using REAL OSM building data"""
        buildings = real_security_data.get('buildings', [])
        
        structure_threats = {
            'building_count': len(buildings),
            'nearest_building_distance': None,
            'building_types': {},
            'commercial_presence': False,
            'residential_presence': False,
            'threat_level': 'low'
        }
        
        if buildings:
            # Find nearest building from REAL OSM data
            nearest_building = min(buildings, key=lambda b: b.distance)
            structure_threats['nearest_building_distance'] = nearest_building.distance
            
            # Analyze building types from REAL OSM tags
            for building in buildings:
                building_type = building.tags.get('building', 'unknown')
                amenity = building.tags.get('amenity', '')
                
                structure_threats['building_types'][building_type] = structure_threats['building_types'].get(building_type, 0) + 1
                
                # Check for commercial/residential from REAL tags
                if amenity in ['restaurant', 'cafe', 'shop', 'fuel', 'hotel', 'motel']:
                    structure_threats['commercial_presence'] = True
                if building_type in ['house', 'residential', 'apartments']:
                    structure_threats['residential_presence'] = True
        
        # Determine threat level based on REAL data
        nearest_distance = structure_threats['nearest_building_distance'] or 9999
        building_count = structure_threats['building_count']
        
        if (nearest_distance < 200 or 
            building_count > 15 or 
            structure_threats['commercial_presence']):
            structure_threats['threat_level'] = 'extreme'
        elif (nearest_distance < 500 or 
              building_count > 8 or 
              structure_threats['residential_presence']):
            structure_threats['threat_level'] = 'high'
        elif nearest_distance < 1000 or building_count > 3:
            structure_threats['threat_level'] = 'moderate'
        else:
            structure_threats['threat_level'] = 'low'
            
        return structure_threats
    
    def _analyze_real_access_threats(self, real_security_data: Dict) -> Dict[str, Any]:
        """Analyze access point threats using REAL OSM parking and access data"""
        parking_areas = real_security_data.get('parking_areas', [])
        access_points = real_security_data.get('access_points', [])
        access_density = real_security_data.get('access_density_per_km2', 0.0)
        
        access_threats = {
            'parking_count': len(parking_areas),
            'access_point_count': len(access_points),
            'total_access_count': len(parking_areas) + len(access_points),
            'access_density_per_km2': access_density,
            'nearest_parking_distance': None,
            'nearest_access_distance': None,
            'parking_types': {},
            'access_types': {},
            'threat_level': 'low'
        }
        
        # Analyze REAL parking areas
        if parking_areas:
            nearest_parking = min(parking_areas, key=lambda p: p.distance)
            access_threats['nearest_parking_distance'] = nearest_parking.distance
            
            for parking in parking_areas:
                parking_type = parking.tags.get('amenity', 'parking')
                access_threats['parking_types'][parking_type] = access_threats['parking_types'].get(parking_type, 0) + 1
        
        # Analyze REAL access points
        if access_points:
            nearest_access = min(access_points, key=lambda a: a.distance)
            access_threats['nearest_access_distance'] = nearest_access.distance
            
            for access in access_points:
                access_type = access.tags.get('barrier', access.tags.get('information', 'access'))
                access_threats['access_types'][access_type] = access_threats['access_types'].get(access_type, 0) + 1
        
        # Determine threat level based on REAL access data (critical for mature bucks)
        nearest_parking = access_threats['nearest_parking_distance'] or 9999
        nearest_access = access_threats['nearest_access_distance'] or 9999
        nearest_overall = min(nearest_parking, nearest_access)
        
        if nearest_overall < 400 or access_density > 4.0 or len(parking_areas) > 8:
            access_threats['threat_level'] = 'extreme'
        elif nearest_overall < 800 or access_density > 2.5 or len(parking_areas) > 4:
            access_threats['threat_level'] = 'high'
        elif nearest_overall < 1500 or access_density > 1.0 or len(parking_areas) > 1:
            access_threats['threat_level'] = 'moderate'
        else:
            access_threats['threat_level'] = 'low'
            
        return access_threats
    
    def _analyze_real_trail_threats(self, real_security_data: Dict) -> Dict[str, Any]:
        """Analyze trail network threats using REAL OSM trail data"""
        trail_networks = real_security_data.get('trail_networks', [])
        
        trail_threats = {
            'trail_count': len(trail_networks),
            'nearest_trail_distance': None,
            'trail_types': {},
            'established_trails': 0,
            'informal_paths': 0,
            'threat_level': 'low'
        }
        
        if trail_networks:
            # Find nearest trail from REAL OSM data
            nearest_trail = min(trail_networks, key=lambda t: t.distance)
            trail_threats['nearest_trail_distance'] = nearest_trail.distance
            
            # Analyze trail types from REAL OSM tags
            for trail in trail_networks:
                highway_type = trail.tags.get('highway', 'unknown')
                trail_threats['trail_types'][highway_type] = trail_threats['trail_types'].get(highway_type, 0) + 1
                
                # Categorize by establishment level
                if highway_type in ['track', 'bridleway', 'cycleway']:
                    trail_threats['established_trails'] += 1
                elif highway_type in ['path', 'footway']:
                    trail_threats['informal_paths'] += 1
        
        # Determine threat level based on REAL trail data
        nearest_distance = trail_threats['nearest_trail_distance'] or 9999
        trail_count = trail_threats['trail_count']
        established_count = trail_threats['established_trails']
        
        if nearest_distance < 100 or trail_count > 12 or established_count > 6:
            trail_threats['threat_level'] = 'extreme'
        elif nearest_distance < 250 or trail_count > 8 or established_count > 3:
            trail_threats['threat_level'] = 'high'
        elif nearest_distance < 500 or trail_count > 4:
            trail_threats['threat_level'] = 'moderate'
        else:
            trail_threats['threat_level'] = 'low'
            
        return trail_threats
    
    def _calculate_real_security_score(self, threat_categories: Dict, real_security_data: Dict) -> float:
        """Calculate overall security score based on REAL OSM data (0-100, higher = more secure)"""
        threat_scores = {}
        
        # Convert threat levels to numeric scores (0-100)
        threat_level_scores = {
            'low': 85.0,
            'moderate': 65.0, 
            'high': 40.0,
            'extreme': 15.0
        }
        
        for category, threats in threat_categories.items():
            threat_level = threats.get('threat_level', 'moderate')
            threat_scores[category] = threat_level_scores.get(threat_level, 50.0)
        
        # Weighted average based on threat importance for mature bucks
        weights = {
            'road_threats': 0.25,        # Important - vehicle access
            'structure_threats': 0.20,   # Important - human presence
            'access_threats': 0.35,      # CRITICAL for mature bucks - parking/access
            'trail_threats': 0.20        # Important - foot traffic
        }
        
        weighted_score = sum(
            threat_scores.get(category, 50.0) * weights.get(category, 0.25)
            for category in threat_categories.keys()
        )
        
        # Bonus for extremely remote areas (no OSM features found)
        total_features = (len(real_security_data.get('parking_areas', [])) + 
                         len(real_security_data.get('trail_networks', [])) + 
                         len(real_security_data.get('road_network', [])) + 
                         len(real_security_data.get('buildings', [])))
        
        if total_features == 0:
            weighted_score = min(weighted_score + 10.0, 100.0)  # Bonus for truly remote areas
        
        return min(max(weighted_score, 0.0), 100.0)
    
    def _generate_real_security_recommendations(self, threat_categories: Dict, real_security_data: Dict) -> List[str]:
        """Generate security-based recommendations using REAL OSM data"""
        recommendations = []
        
        # Check each threat category and provide specific REAL data insights
        for category, threats in threat_categories.items():
            threat_level = threats.get('threat_level', 'moderate')
            
            if threat_level in ['high', 'extreme']:
                if category == 'road_threats':
                    road_count = threats.get('road_count', 0)
                    nearest_distance = threats.get('nearest_road_distance')
                    if nearest_distance:
                        recommendations.append(f"⚠️ Road pressure: {road_count} roads found, nearest {nearest_distance:.0f}m away")
                    else:
                        recommendations.append(f"⚠️ High road density: {road_count} roads in area")
                        
                elif category == 'structure_threats':
                    building_count = threats.get('building_count', 0)
                    nearest_distance = threats.get('nearest_building_distance')
                    if nearest_distance:
                        recommendations.append(f"🏠 Building pressure: {building_count} buildings, nearest {nearest_distance:.0f}m away")
                    else:
                        recommendations.append(f"🏠 Building density: {building_count} structures detected")
                        
                elif category == 'access_threats':
                    parking_count = threats.get('parking_count', 0)
                    access_count = threats.get('access_point_count', 0)
                    nearest_parking = threats.get('nearest_parking_distance')
                    if parking_count > 0:
                        if nearest_parking:
                            recommendations.append(f"🚗 CRITICAL: {parking_count} parking areas, nearest {nearest_parking:.0f}m (mature bucks avoid)")
                        else:
                            recommendations.append(f"🚗 CRITICAL: {parking_count} parking areas detected (major mature buck deterrent)")
                    if access_count > 0:
                        recommendations.append(f"🚪 Access pressure: {access_count} gates/trailheads found")
                        
                elif category == 'trail_threats':
                    trail_count = threats.get('trail_count', 0)
                    established = threats.get('established_trails', 0)
                    nearest_distance = threats.get('nearest_trail_distance')
                    if nearest_distance:
                        recommendations.append(f"🥾 Trail pressure: {trail_count} trails ({established} established), nearest {nearest_distance:.0f}m")
                    else:
                        recommendations.append(f"🥾 High trail density: {trail_count} trails found")
        
        # Add positive recommendations for secure areas
        total_threats = sum(1 for cat in threat_categories.values() if cat.get('threat_level') in ['high', 'extreme'])
        
        if total_threats == 0:
            total_features = (len(real_security_data.get('parking_areas', [])) + 
                            len(real_security_data.get('trail_networks', [])) + 
                            len(real_security_data.get('road_network', [])) + 
                            len(real_security_data.get('buildings', [])))
            
            if total_features == 0:
                recommendations.append("✅ EXCELLENT: Truly remote area - no infrastructure detected")
            elif total_features < 5:
                recommendations.append("✅ GOOD: Low infrastructure density - suitable for mature bucks")
            else:
                recommendations.append("✅ MODERATE: Some infrastructure but manageable security profile")
        
        # Add specific mature buck insights
        if len(real_security_data.get('parking_areas', [])) == 0:
            recommendations.append("🎯 Mature buck advantage: No parking areas detected in 2km radius")
        
        if not recommendations:
            recommendations.append("⚠️ OSM data analysis completed - review threat summary")
        
        return recommendations
    
    def _calculate_real_data_confidence(self, real_security_data: Dict) -> float:
        """Calculate confidence in the security analysis based on REAL OSM data quality"""
        # Check if we successfully got data from OSM
        data_source = real_security_data.get('data_source', 'unknown')
        
        if data_source == 'osm_query_failed':
            return 0.3  # Low confidence when OSM failed
        
        # Count successful data categories
        feature_categories = ['parking_areas', 'trail_networks', 'road_network', 'buildings', 'access_points']
        successful_categories = 0
        total_features = 0
        
        for category in feature_categories:
            features = real_security_data.get(category, [])
            if isinstance(features, list):
                successful_categories += 1
                total_features += len(features)
        
        # Base confidence on successful API calls
        base_confidence = successful_categories / len(feature_categories)
        
        # Boost confidence if we found actual features (indicates good data coverage)
        if total_features > 0:
            feature_boost = min(total_features / 20.0, 0.2)  # Up to 20% boost
            base_confidence += feature_boost
        
        # OSM is generally high quality, so reasonable confidence
        return min(base_confidence, 0.9)  # Max 90% confidence
    
    def _determine_pressure_level(self, security_score: float) -> str:
        """Determine pressure level based on security score"""
        if security_score >= 80.0:
            return 'minimal'
        elif security_score >= 60.0:
            return 'moderate'
        elif security_score >= 35.0:
            return 'high'
        else:
            return 'extreme'
    
    def _fallback_security_analysis(self) -> Dict[str, Any]:
        """Fallback security analysis when REAL OSM data is unavailable"""
        return {
            'overall_security_score': 50.0,
            'threat_categories': {
                'road_threats': {'threat_level': 'unknown', 'road_count': 0},
                'structure_threats': {'threat_level': 'unknown', 'building_count': 0},
                'access_threats': {'threat_level': 'unknown', 'parking_count': 0, 'access_point_count': 0},
                'trail_threats': {'threat_level': 'unknown', 'trail_count': 0}
            },
            'security_recommendations': ["⚠️ OSM security analysis unavailable - use conservative approach"],
            'pressure_level': 'unknown',
            'confidence': 0.2,
            'data_source': 'fallback_no_real_data',
            'real_osm_data': None
        }

# Global instance
_security_analyzer = None

def get_security_analyzer() -> EnhancedSecurityAnalyzer:
    """Get the global security analyzer instance"""
    global _security_analyzer
    if _security_analyzer is None:
        _security_analyzer = EnhancedSecurityAnalyzer()
    return _security_analyzer
