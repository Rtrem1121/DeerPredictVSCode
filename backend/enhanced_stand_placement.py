#!/usr/bin/env python3
"""
Enhanced Stand Placement Algorithm for Mature Bucks

Integrates security, food, bedding, and travel route analysis for optimal stand placement.
Addresses all four key mature buck characteristics in placement decisions.

Author: Enhanced Mature Buck System
Version: 1.0.0
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class EnhancedStandPlacement:
    """Advanced stand placement for mature buck hunting"""
    
    def __init__(self):
        # Stand placement criteria weights for mature bucks
        self.criteria_weights = {
            'security': 0.30,        # Highest priority - security is paramount
            'food_quality': 0.25,    # Quality food sources
            'bedding_proximity': 0.20, # Access to safe bedding
            'travel_routes': 0.15,   # Interception of travel routes
            'wind_advantage': 0.10   # Wind/scent considerations
        }
        
    def _analyze_stand_site(self, site_lat: float, site_lon: float,
                           terrain_analysis: Dict, security_analysis: Dict,
                           food_analysis: Dict, season: str) -> Dict[str, Any]:
        """Comprehensive analysis of a potential stand site"""
        
        analysis = {
            'overall_score': 0.0,
            'security_score': 0.0,
            'food_score': 0.0,
            'bedding_score': 0.0,
            'travel_score': 0.0,
            'wind_favorability': 0.0,
            'confidence': 0.0,
            'primary_advantage': 'unknown',
            'recommendations': [],
            'risk_factors': []
        }
        
        # 1. Security Analysis
        analysis['security_score'] = self._score_site_security(
            site_lat, site_lon, security_analysis
        )
        
        # 2. Food Access Analysis
        analysis['food_score'] = self._score_food_access(
            site_lat, site_lon, food_analysis, season
        )
        
        # 3. Bedding Proximity Analysis
        analysis['bedding_score'] = self._score_bedding_access(
            site_lat, site_lon, terrain_analysis
        )
        
        # 4. Travel Route Analysis
        analysis['travel_score'] = self._score_travel_interception(
            site_lat, site_lon, terrain_analysis
        )
        
        # 5. Wind Favorability
        analysis['wind_favorability'] = self._score_wind_advantage(
            site_lat, site_lon, terrain_analysis
        )
        
        # Calculate overall score using weighted criteria
        analysis['overall_score'] = (
            analysis['security_score'] * self.criteria_weights['security'] +
            analysis['food_score'] * self.criteria_weights['food_quality'] +
            analysis['bedding_score'] * self.criteria_weights['bedding_proximity'] +
            analysis['travel_score'] * self.criteria_weights['travel_routes'] +
            analysis['wind_favorability'] * self.criteria_weights['wind_advantage']
        )
        
        # Determine primary advantage
        scores = {
            'security': analysis['security_score'],
            'food': analysis['food_score'],
            'bedding': analysis['bedding_score'],
            'travel': analysis['travel_score'],
            'wind': analysis['wind_favorability']
        }
        analysis['primary_advantage'] = max(scores, key=scores.get)
        
        # Generate recommendations and risk factors
        analysis['recommendations'] = self._generate_site_recommendations(analysis, season)
        analysis['risk_factors'] = self._identify_risk_factors(analysis)
        
        # Calculate confidence based on data quality
        analysis['confidence'] = min(
            (security_analysis.get('confidence', 0.5) +
             food_analysis.get('confidence', 0.5) +
             terrain_analysis.get('confidence', 0.8)) / 3.0, 1.0
        ) * 100.0
        
        return analysis
    
    def _score_site_security(self, site_lat: float, site_lon: float,
                            security_analysis: Dict) -> float:
        """Score security characteristics of stand site"""
        security_score = security_analysis.get('overall_security_score', 50.0)
        
        # Adjust based on specific threats
        threat_categories = security_analysis.get('threat_categories', {})
        
        # Heavy penalty for high access pressure (critical for mature bucks)
        access_threats = threat_categories.get('access_threats', {})
        if access_threats.get('threat_level') == 'extreme':
            security_score *= 0.3  # Severe penalty
        elif access_threats.get('threat_level') == 'high':
            security_score *= 0.6
        
        # Penalty for hunting pressure
        hunting_pressure = threat_categories.get('hunting_pressure_threats', {})
        if hunting_pressure.get('threat_level') in ['high', 'extreme']:
            security_score *= 0.7
        
        return min(max(security_score, 0.0), 100.0)
    
    def _score_food_access(self, site_lat: float, site_lon: float,
                          food_analysis: Dict, season: str) -> float:
        """Score food source access from stand site"""
        base_food_score = food_analysis.get('overall_food_score', 60.0)
        
        # Seasonal adjustments
        seasonal_multipliers = {
            'early_season': 1.1,  # Food sources critical early
            'rut': 0.9,           # Food less important during rut
            'late_season': 1.2    # Food critical in winter
        }
        
        seasonal_score = base_food_score * seasonal_multipliers.get(season, 1.0)
        
        # Mast year bonus
        mast_analysis = food_analysis.get('food_categories', {}).get('mast_analysis', {})
        if mast_analysis.get('mast_production_year') == 'excellent':
            seasonal_score *= 1.2
        elif mast_analysis.get('mast_production_year') == 'very_poor':
            seasonal_score *= 0.8
        
        return min(max(seasonal_score, 0.0), 100.0)
    
    def _score_bedding_access(self, site_lat: float, site_lon: float,
                             terrain_analysis: Dict) -> float:
        """Score bedding area access from stand site"""
        # This would integrate with actual bedding area predictions
        # For now, use terrain-based scoring
        
        canopy_closure = terrain_analysis.get('canopy_closure', 50.0)
        distance_to_thick_cover = terrain_analysis.get('distance_to_thick_cover', 500)
        
        # Score based on proximity to bedding habitat
        if distance_to_thick_cover <= 150:
            distance_score = 90.0
        elif distance_to_thick_cover <= 250:
            distance_score = 75.0
        elif distance_to_thick_cover <= 400:
            distance_score = 60.0
        else:
            distance_score = 30.0
        
        # Bonus for thick cover nearby
        cover_bonus = min(canopy_closure, 100.0) * 0.3
        
        return min(distance_score + cover_bonus, 100.0)
    
    def _score_travel_interception(self, site_lat: float, site_lon: float,
                                  terrain_analysis: Dict) -> float:
        """Score travel route interception potential"""
        # Travel corridor analysis
        corridor_density = terrain_analysis.get('travel_corridor_density', 0.3)
        funnel_proximity = terrain_analysis.get('funnel_proximity', 1000)
        
        # Score based on travel features
        if funnel_proximity <= 100:
            travel_score = 90.0
        elif funnel_proximity <= 250:
            travel_score = 75.0
        elif funnel_proximity <= 500:
            travel_score = 60.0
        else:
            travel_score = 40.0
        
        # Adjust for corridor density
        travel_score *= min(corridor_density * 2.0, 1.0)
        
        return min(max(travel_score, 0.0), 100.0)
    
    def _score_wind_advantage(self, site_lat: float, site_lon: float,
                             terrain_analysis: Dict) -> float:
        """Score wind advantage for scent control"""
        # This would integrate with actual wind analysis
        # For now, use terrain-based wind assessment
        
        elevation_advantage = terrain_analysis.get('elevation_advantage', 0)
        wind_patterns = terrain_analysis.get('prevailing_wind_advantage', 0.5)
        
        # Score wind advantage
        wind_score = 50.0  # Base score
        
        if elevation_advantage > 20:  # 20+ meters elevation advantage
            wind_score += 20.0
        elif elevation_advantage > 10:
            wind_score += 10.0
        
        # Wind pattern bonus
        wind_score += wind_patterns * 30.0
        
        return min(max(wind_score, 0.0), 100.0)
    
    def _generate_candidate_grid(self, center_lat: float, center_lon: float) -> List[Tuple[float, float]]:
        """Generate candidate stand locations in analysis area"""
        candidates = []
        
        # Create 5x5 grid around center point
        meters_to_degrees = 1.0 / 111000.0
        grid_spacing = 200  # 200 meter spacing
        
        for i in range(-2, 3):
            for j in range(-2, 3):
                if i == 0 and j == 0:  # Skip center point
                    continue
                    
                lat_offset = i * grid_spacing * meters_to_degrees
                lon_offset = j * grid_spacing * meters_to_degrees
                
                candidate_lat = center_lat + lat_offset
                candidate_lon = center_lon + lon_offset
                
                candidates.append((candidate_lat, candidate_lon))
        
        return candidates
    
    def _generate_site_recommendations(self, analysis: Dict, season: str) -> List[str]:
        """Generate hunting recommendations for the stand site"""
        recommendations = []
        
        # Security recommendations
        if analysis['security_score'] > 80:
            recommendations.append("🔒 Excellent security - ideal for mature buck hunting")
        elif analysis['security_score'] < 50:
            recommendations.append("⚠️ Security concerns - approach with extreme caution")
        
        # Food recommendations
        if analysis['food_score'] > 80:
            recommendations.append("🍽️ Prime food sources - expect regular deer activity")
        
        # Bedding recommendations
        if analysis['bedding_score'] > 80:
            recommendations.append("🛏️ Close to bedding - morning hunt potential")
        
        # Travel recommendations
        if analysis['travel_score'] > 80:
            recommendations.append("🛤️ Excellent travel interception - all-day potential")
        
        # Seasonal recommendations
        if season == 'rut':
            recommendations.append("🦌 Rut period - focus on dawn and dusk activity")
        elif season == 'late_season':
            recommendations.append("❄️ Late season - thermal cover and food sources critical")
        
        return recommendations
    
    def _identify_risk_factors(self, analysis: Dict) -> List[str]:
        """Identify potential risk factors for the stand site"""
        risks = []
        
        if analysis['security_score'] < 60:
            risks.append("🚨 Security risk - high pressure area")
        
        if analysis['food_score'] < 40:
            risks.append("🍽️ Limited food sources - unpredictable deer movement")
        
        if analysis['bedding_score'] < 40:
            risks.append("🛏️ Poor bedding access - limited morning opportunities")
        
        if analysis['wind_favorability'] < 50:
            risks.append("🌬️ Wind disadvantage - scent control critical")
        
        return risks

# Global instance
_enhanced_stand_placement = None

def get_enhanced_stand_placement() -> EnhancedStandPlacement:
    """Get the global enhanced stand placement instance"""
    global _enhanced_stand_placement
    if _enhanced_stand_placement is None:
        _enhanced_stand_placement = EnhancedStandPlacement()
    return _enhanced_stand_placement
