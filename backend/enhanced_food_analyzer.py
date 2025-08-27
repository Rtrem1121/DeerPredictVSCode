#!/usr/bin/env python3
"""
Enhanced Food Source Analysis for Mature Buck Predictions

Addresses the "quality food sources" characteristic by analyzing mast production,
crop maturity timing, food competition, and seasonal food preferences.

Author: Enhanced Mature Buck System
Version: 1.0.0
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedFoodAnalyzer:
    """Advanced food source analysis for mature buck nutrition needs"""
    
    def __init__(self):
        # Vermont-specific mast production cycles (based on research)
        self.mast_cycles = {
            'white_oak': {'good_years': [2024, 2026, 2028], 'poor_years': [2023, 2025, 2027]},
            'red_oak': {'good_years': [2023, 2025, 2027], 'poor_years': [2024, 2026, 2028]},
            'beech': {'good_years': [2024, 2027], 'poor_years': [2025, 2026]},
            'hickory': {'good_years': [2025, 2028], 'poor_years': [2023, 2024, 2026, 2027]}
        }
        
        # Competition factors
        self.competition_factors = {
            'deer_density_high': 0.8,      # High deer density reduces food availability
            'turkey_present': 0.9,         # Turkeys compete for mast
            'squirrel_density_high': 0.85, # Squirrels consume significant mast
            'bear_present': 0.7,           # Bears heavily impact mast availability
            'livestock_present': 0.6       # Cattle/horses compete for browse
        }
    
    def _analyze_mast_sources(self, food_data: Dict, season: str, current_year: int) -> Dict[str, Any]:
        """Analyze mast production and availability"""
        mast_analysis = {
            'oak_availability': 0.0,
            'beech_availability': 0.0,
            'hickory_availability': 0.0,
            'mast_production_year': 'unknown',
            'seasonal_availability': 0.0,
            'quality_score': 0.0
        }
        
        # Get mast tree densities from satellite data
        oak_density = food_data.get('oak_tree_density', 0.0)
        beech_density = food_data.get('beech_tree_density', 0.0)
        hickory_density = food_data.get('hickory_tree_density', 0.0)
        
        # Assess mast production for current year
        mast_production_scores = {}
        for tree_type, cycle in self.mast_cycles.items():
            if current_year in cycle['good_years']:
                mast_production_scores[tree_type] = 0.9
            elif current_year in cycle['poor_years']:
                mast_production_scores[tree_type] = 0.3
            else:
                mast_production_scores[tree_type] = 0.6  # Average year
        
        # Calculate availability based on density and production
        mast_analysis['oak_availability'] = oak_density * mast_production_scores.get('white_oak', 0.6)
        mast_analysis['beech_availability'] = beech_density * mast_production_scores.get('beech', 0.6)
        mast_analysis['hickory_availability'] = hickory_density * mast_production_scores.get('hickory', 0.6)
        
        # Determine if this is a good or poor mast year
        avg_production = np.mean(list(mast_production_scores.values()))
        if avg_production >= 0.8:
            mast_analysis['mast_production_year'] = 'excellent'
        elif avg_production >= 0.6:
            mast_analysis['mast_production_year'] = 'good'
        elif avg_production >= 0.4:
            mast_analysis['mast_production_year'] = 'poor'
        else:
            mast_analysis['mast_production_year'] = 'very_poor'
        
        # Seasonal availability (mast drops in early season, depletes through winter)
        if season == 'early_season':
            mast_analysis['seasonal_availability'] = 1.0
        elif season == 'rut':
            mast_analysis['seasonal_availability'] = 0.7
        else:  # late_season
            mast_analysis['seasonal_availability'] = 0.3
        
        # Quality score based on total mast availability
        total_mast = (mast_analysis['oak_availability'] + 
                     mast_analysis['beech_availability'] + 
                     mast_analysis['hickory_availability'])
        mast_analysis['quality_score'] = min(total_mast * mast_analysis['seasonal_availability'], 1.0)
        
        return mast_analysis
    
    def _analyze_crop_sources(self, food_data: Dict, season: str) -> Dict[str, Any]:
        """Analyze agricultural crop sources"""
        crop_analysis = {
            'corn_availability': 0.0,
            'soybean_availability': 0.0,
            'alfalfa_availability': 0.0,
            'crop_maturity': 'unknown',
            'distance_to_crops': 9999,
            'quality_score': 0.0
        }
        
        # Get crop densities and distances
        corn_density = food_data.get('corn_field_density', 0.0)
        soybean_density = food_data.get('soybean_field_density', 0.0)
        alfalfa_density = food_data.get('alfalfa_field_density', 0.0)
        crop_distance = food_data.get('nearest_crop_distance', 9999)
        
        crop_analysis['distance_to_crops'] = crop_distance
        
        # Assess crop maturity based on season
        if season == 'early_season':
            crop_analysis['crop_maturity'] = 'green_growing'
            # Green soybeans are premium, corn is developing
            crop_analysis['corn_availability'] = corn_density * 0.6
            crop_analysis['soybean_availability'] = soybean_density * 0.95
            crop_analysis['alfalfa_availability'] = alfalfa_density * 0.8
        elif season == 'rut':
            crop_analysis['crop_maturity'] = 'mature_standing'
            # Mature crops, high energy
            crop_analysis['corn_availability'] = corn_density * 0.9
            crop_analysis['soybean_availability'] = soybean_density * 0.8
            crop_analysis['alfalfa_availability'] = alfalfa_density * 0.6
        else:  # late_season
            crop_analysis['crop_maturity'] = 'harvested_stubble'
            # Harvested fields with waste grain
            crop_analysis['corn_availability'] = corn_density * 0.7
            crop_analysis['soybean_availability'] = soybean_density * 0.4
            crop_analysis['alfalfa_availability'] = alfalfa_density * 0.3
        
        # Distance penalty for crop access
        distance_factor = 1.0
        if crop_distance > 1000:
            distance_factor = 0.5
        elif crop_distance > 500:
            distance_factor = 0.7
        elif crop_distance > 200:
            distance_factor = 0.9
        
        # Calculate quality score
        total_crop_value = (crop_analysis['corn_availability'] * 0.4 + 
                           crop_analysis['soybean_availability'] * 0.4 + 
                           crop_analysis['alfalfa_availability'] * 0.2)
        crop_analysis['quality_score'] = total_crop_value * distance_factor
        
        return crop_analysis
    
    def _analyze_browse_sources(self, food_data: Dict, season: str) -> Dict[str, Any]:
        """Analyze woody browse sources"""
        browse_analysis = {
            'browse_availability': 0.0,
            'browse_diversity': 0.0,
            'thermal_cover_browse': 0.0,
            'quality_score': 0.0
        }
        
        # Get browse data
        forest_density = food_data.get('forest_density', 0.0)
        edge_density = food_data.get('edge_density', 0.0)
        conifer_density = food_data.get('conifer_density', 0.0)
        
        # Browse availability varies by season
        if season == 'early_season':
            # Summer browse - leaves, soft shoots
            browse_analysis['browse_availability'] = forest_density * 0.8 + edge_density * 0.6
        elif season == 'rut':
            # Fall browse - some leaves, apple drops
            browse_analysis['browse_availability'] = forest_density * 0.6 + edge_density * 0.8
        else:  # late_season
            # Winter browse - twigs, evergreen tips, critical nutrition
            browse_analysis['browse_availability'] = forest_density * 0.7 + conifer_density * 0.9
            browse_analysis['thermal_cover_browse'] = conifer_density * 0.8
        
        # Browse diversity (mixed forest types)
        browse_analysis['browse_diversity'] = min(forest_density + edge_density + conifer_density, 1.0)
        
        # Quality score (browse is supplemental except in late season)
        if season == 'late_season':
            browse_analysis['quality_score'] = browse_analysis['browse_availability'] * 0.8
        else:
            browse_analysis['quality_score'] = browse_analysis['browse_availability'] * 0.4
        
        return browse_analysis
    
    def _analyze_water_proximity(self, food_data: Dict) -> Dict[str, Any]:
        """Analyze water source proximity (critical for food processing)"""
        water_analysis = {
            'nearest_water': food_data.get('nearest_water_distance', 9999),
            'water_type': food_data.get('water_type', 'unknown'),
            'water_accessibility': 0.0,
            'quality_score': 0.0
        }
        
        water_distance = water_analysis['nearest_water']
        
        # Water accessibility based on distance (deer need water within 1 mile of food)
        if water_distance <= 200:
            water_analysis['water_accessibility'] = 1.0
        elif water_distance <= 500:
            water_analysis['water_accessibility'] = 0.8
        elif water_distance <= 1000:
            water_analysis['water_accessibility'] = 0.6
        elif water_distance <= 1600:  # 1 mile
            water_analysis['water_accessibility'] = 0.4
        else:
            water_analysis['water_accessibility'] = 0.2
        
        # Quality score impacts all food utilization
        water_analysis['quality_score'] = water_analysis['water_accessibility']
        
        return water_analysis
    
    def _assess_food_competition(self, food_data: Dict) -> Dict[str, Any]:
        """Assess competition for food resources"""
        competition_analysis = {
            'deer_density': food_data.get('deer_density_estimate', 'moderate'),
            'turkey_presence': food_data.get('turkey_sign', False),
            'bear_presence': food_data.get('bear_sign', False),
            'livestock_impact': food_data.get('livestock_present', False),
            'competition_factor': 1.0,
            'quality_impact': 0.0
        }
        
        # Calculate competition factor
        factors = []
        
        if competition_analysis['deer_density'] == 'high':
            factors.append(self.competition_factors['deer_density_high'])
        
        if competition_analysis['turkey_presence']:
            factors.append(self.competition_factors['turkey_present'])
        
        if competition_analysis['bear_presence']:
            factors.append(self.competition_factors['bear_present'])
        
        if competition_analysis['livestock_impact']:
            factors.append(self.competition_factors['livestock_present'])
        
        # Apply competition factors (multiplicative)
        competition_analysis['competition_factor'] = np.prod(factors) if factors else 1.0
        
        # Quality impact (reduction in food availability)
        competition_analysis['quality_impact'] = 1.0 - competition_analysis['competition_factor']
        
        return competition_analysis
    
    def _generate_seasonal_outlook(self, season: str, current_year: int) -> Dict[str, Any]:
        """Generate seasonal food outlook"""
        outlook = {
            'current_season_quality': 'good',
            'next_season_forecast': 'good',
            'annual_trend': 'stable',
            'key_factors': []
        }
        
        # Season-specific outlook
        if season == 'early_season':
            outlook['key_factors'].append("Green soybean fields at peak nutrition")
            outlook['key_factors'].append("Fresh mast drop expected soon")
        elif season == 'rut':
            outlook['key_factors'].append("Standing corn provides high energy")
            outlook['key_factors'].append("Mast availability declining")
        else:  # late_season
            outlook['key_factors'].append("Winter browse becomes primary")
            outlook['key_factors'].append("Waste grain in harvested fields")
        
        return outlook
    
    def _calculate_overall_food_score(self, food_categories: Dict) -> float:
        """Calculate overall food landscape score"""
        mast_score = food_categories.get('mast_analysis', {}).get('quality_score', 0.0)
        crop_score = food_categories.get('crop_analysis', {}).get('quality_score', 0.0)
        browse_score = food_categories.get('browse_analysis', {}).get('quality_score', 0.0)
        water_score = food_categories.get('water_sources', {}).get('quality_score', 0.5)
        
        # Weighted combination
        food_score = (mast_score * 0.4 + crop_score * 0.3 + browse_score * 0.2) * water_score * 100.0
        
        return min(max(food_score, 0.0), 100.0)
    
    def _generate_food_recommendations(self, food_categories: Dict, season: str) -> List[str]:
        """Generate food-based hunting recommendations"""
        recommendations = []
        
        mast = food_categories.get('mast_analysis', {})
        crops = food_categories.get('crop_analysis', {})
        water = food_categories.get('water_sources', {})
        
        # Mast recommendations
        if mast.get('quality_score', 0.0) > 0.7:
            recommendations.append("🌰 Excellent mast year - focus on oak flats and ridges")
        elif mast.get('quality_score', 0.0) < 0.3:
            recommendations.append("🌰 Poor mast year - emphasize agricultural areas")
        
        # Crop recommendations
        if crops.get('quality_score', 0.0) > 0.6:
            recommendations.append("🌾 Strong crop availability - edge hunt food plots")
        
        # Water recommendations
        if water.get('quality_score', 0.0) < 0.5:
            recommendations.append("💧 Limited water access - focus near available sources")
        
        # Seasonal recommendations
        if season == 'early_season':
            recommendations.append("🌱 Early season - target green crop fields and fresh mast")
        elif season == 'rut':
            recommendations.append("🦌 Rut period - focus on high-energy food sources")
        else:
            recommendations.append("❄️ Late season - thermal cover near winter food sources")
        
        return recommendations
    
    def _get_food_source_data(self, lat: float, lon: float) -> Dict:
        """Get food source data (placeholder for GEE/OSM integration)"""
        # This would integrate with satellite data and terrain analysis
        return {
            'oak_tree_density': 0.6,
            'beech_tree_density': 0.3,
            'hickory_tree_density': 0.2,
            'corn_field_density': 0.4,
            'soybean_field_density': 0.3,
            'alfalfa_field_density': 0.1,
            'forest_density': 0.8,
            'edge_density': 0.5,
            'conifer_density': 0.3,
            'nearest_crop_distance': 800,
            'nearest_water_distance': 300,
            'water_type': 'stream',
            'deer_density_estimate': 'moderate',
            'turkey_sign': False,
            'bear_sign': False,
            'livestock_present': False
        }
    
    def _calculate_food_confidence(self, food_data: Dict) -> float:
        """Calculate confidence in food analysis"""
        data_points = len([v for v in food_data.values() if v is not None])
        max_points = len(food_data)
        return min(data_points / max_points, 1.0) * 0.85
    
    def _fallback_food_analysis(self) -> Dict[str, Any]:
        """Fallback food analysis when data unavailable"""
        return {
            'overall_food_score': 60.0,
            'food_categories': {},
            'food_recommendations': ["⚠️ Food analysis unavailable - use general food source patterns"],
            'seasonal_outlook': {'current_season_quality': 'unknown'},
            'competition_assessment': {'competition_factor': 1.0},
            'confidence': 0.3
        }

# Global instance
_food_analyzer = None

def get_food_analyzer() -> EnhancedFoodAnalyzer:
    """Get the global food analyzer instance"""
    global _food_analyzer
    if _food_analyzer is None:
        _food_analyzer = EnhancedFoodAnalyzer()
    return _food_analyzer
