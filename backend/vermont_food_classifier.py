#!/usr/bin/env python3
"""
Vermont-Specific Food Source Classification

Analyzes food sources specific to Vermont deer hunting areas using:
- USDA Cropland Data Layer (CDL) for agricultural areas
- NDVI analysis for mast production in hardwood forests
- Land cover classification for browse availability
- Seasonal scoring based on Vermont deer behavior

Author: Vermont Deer Prediction System
Date: October 2, 2025
"""

import logging
import ee
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VermontFoodClassifier:
    """
    Vermont-specific food source analysis for deer hunting prediction.
    
    Focuses on food sources actually present in Vermont:
    - Corn fields (primary agricultural food)
    - Hay fields and pastures
    - Hardwood forests (oak, beech, maple for mast)
    - Apple orchards
    - Browse areas (edges, young forest)
    - Winter food sources (browse, hemlock)
    """
    
    def __init__(self):
        # Vermont-specific crop classifications (USDA CDL codes)
        # These are the crops ACTUALLY found in Vermont
        self.VERMONT_CROPS = {
            # Agricultural Crops
            1: {
                'name': 'Corn',
                'common_in_vt': True,
                'season_quality': {
                    'early_season': 0.45,  # Standing, not attractive yet
                    'rut': 0.95,           # High energy for breeding
                    'late_season': 0.90    # Waste grain, critical winter food
                },
                'description': 'Standing/harvested corn - prime late season food'
            },
            36: {
                'name': 'Alfalfa',
                'common_in_vt': True,
                'season_quality': {
                    'early_season': 0.70,  # Green, nutritious
                    'rut': 0.55,           # Less attractive during rut
                    'late_season': 0.30    # Dormant, low value
                },
                'description': 'Alfalfa hay fields - good early season protein'
            },
            37: {
                'name': 'Other Hay/Non-Alfalfa',
                'common_in_vt': True,
                'season_quality': {
                    'early_season': 0.55,
                    'rut': 0.45,
                    'late_season': 0.25
                },
                'description': 'Timothy/clover hay - moderate food value'
            },
            176: {
                'name': 'Grass/Pasture',
                'common_in_vt': True,
                'season_quality': {
                    'early_season': 0.50,  # Some grazing
                    'rut': 0.35,           # Less attractive
                    'late_season': 0.20    # Dormant grass
                },
                'description': 'Pastures and grassland - light grazing'
            },
            69: {
                'name': 'Grapes',
                'common_in_vt': False,  # Rare in Vermont
                'season_quality': {'early_season': 0.3, 'rut': 0.2, 'late_season': 0.1},
                'description': 'Uncommon in Vermont hunting areas'
            },
            
            # Forest Types (Vermont-specific)
            141: {
                'name': 'Deciduous Forest',
                'common_in_vt': True,
                'season_quality': {
                    'early_season': 0.85,  # Fresh acorns, beechnuts
                    'rut': 0.75,           # Remaining mast
                    'late_season': 0.50    # Browse only
                },
                'description': 'Oak/beech/maple - primary mast production'
            },
            142: {
                'name': 'Evergreen Forest',
                'common_in_vt': True,
                'season_quality': {
                    'early_season': 0.25,  # Limited food value
                    'rut': 0.25,
                    'late_season': 0.40    # Hemlock/cedar browse, thermal cover
                },
                'description': 'Spruce/fir/hemlock - browse and shelter'
            },
            143: {
                'name': 'Mixed Forest',
                'common_in_vt': True,
                'season_quality': {
                    'early_season': 0.70,  # Some mast, good cover
                    'rut': 0.65,
                    'late_season': 0.45    # Mixed browse
                },
                'description': 'Hardwood/softwood mix - moderate food + cover'
            },
            152: {
                'name': 'Shrubland',
                'common_in_vt': True,
                'season_quality': {
                    'early_season': 0.60,  # Fresh browse, berries
                    'rut': 0.50,
                    'late_season': 0.55    # Critical winter browse
                },
                'description': 'Young forest/edge - excellent browse'
            },
            
            # Other Land Cover
            121: {
                'name': 'Developed/Open Space',
                'common_in_vt': True,
                'season_quality': {'early_season': 0.30, 'rut': 0.25, 'late_season': 0.20},
                'description': 'Rural areas, possible apple trees/gardens'
            },
            87: {
                'name': 'Wetlands',
                'common_in_vt': True,
                'season_quality': {
                    'early_season': 0.50,  # Aquatic plants
                    'rut': 0.40,
                    'late_season': 0.30    # Limited winter value
                },
                'description': 'Wetlands - supplemental food'
            },
        }
        
        # Vermont hardwood mast trees (from NDVI + forest type)
        self.VERMONT_MAST_TREES = {
            'white_oak': {
                'ndvi_range': (0.65, 0.85),  # Healthy oak signature
                'preference': 'high',         # Deer preference
                'production_cycle': 2         # Good years every 2-3 years
            },
            'red_oak': {
                'ndvi_range': (0.60, 0.80),
                'preference': 'high',
                'production_cycle': 2
            },
            'beech': {
                'ndvi_range': (0.70, 0.88),
                'preference': 'very_high',    # Beechnuts highly preferred
                'production_cycle': 3         # More variable
            },
            'sugar_maple': {
                'ndvi_range': (0.60, 0.75),
                'preference': 'low',          # Browse only
                'production_cycle': None      # Not mast producer
            },
            'apple': {
                'ndvi_range': (0.55, 0.75),
                'preference': 'very_high',    # Apples extremely attractive
                'production_cycle': 1         # Annual, but variable yield
            }
        }
        
        # Vermont seasonal food priorities
        self.VERMONT_SEASONAL_PRIORITIES = {
            'early_season': {
                'priorities': ['acorns', 'apples', 'beechnuts', 'browse', 'alfalfa'],
                'weights': {'mast': 0.50, 'agriculture': 0.30, 'browse': 0.20}
            },
            'rut': {
                'priorities': ['corn', 'acorns', 'browse', 'high_energy'],
                'weights': {'agriculture': 0.45, 'mast': 0.35, 'browse': 0.20}
            },
            'late_season': {
                'priorities': ['corn_stubble', 'browse', 'hemlock', 'waste_grain'],
                'weights': {'agriculture': 0.40, 'browse': 0.40, 'mast': 0.20}
            }
        }
    
    def analyze_vermont_food_sources(self, 
                                     area: ee.Geometry, 
                                     season: str,
                                     analysis_year: int = 2024) -> Dict[str, Any]:
        """
        Comprehensive Vermont food source analysis.
        
        Args:
            area: GEE Geometry to analyze
            season: Hunting season (early_season, rut, late_season)
            analysis_year: Year for CDL data
            
        Returns:
            Dict with food patches, scores, and locations
        """
        try:
            logger.info(f"🍂 Analyzing Vermont food sources for {season}")
            
            # 1. Agricultural Classification (CDL)
            ag_results = self._analyze_vermont_agriculture(area, season, analysis_year)
            
            # 2. Hardwood Mast Analysis (NDVI + Forest Type)
            mast_results = self._analyze_vermont_mast_production(area, season)
            
            # 3. Browse Availability (Edge Habitat + Young Forest)
            browse_results = self._analyze_vermont_browse(area, season)
            
            # 4. Combine into unified food source map
            combined_results = self._combine_vermont_food_sources(
                ag_results, mast_results, browse_results, season
            )
            
            logger.info(f"✅ Found {len(combined_results.get('food_patches', []))} Vermont food sources")
            
            return combined_results
            
        except Exception as e:
            logger.error(f"❌ Vermont food analysis failed: {e}")
            return self._fallback_vermont_food_analysis(season)
    
    def _analyze_vermont_agriculture(self, 
                                    area: ee.Geometry, 
                                    season: str,
                                    year: int) -> Dict[str, Any]:
        """
        Analyze agricultural food sources using USDA CDL.
        Focuses on Vermont crops: corn, hay, pastures.
        """
        try:
            # Get USDA Cropland Data Layer
            cdl = ee.ImageCollection("USDA/NASS/CDL") \
                .filter(ee.Filter.date(f'{year}-01-01', f'{year}-12-31')) \
                .first() \
                .select('cropland') \
                .clip(area)
            
            # Calculate crop statistics
            crop_histogram = cdl.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=area,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            crop_stats = crop_histogram.get('cropland', {})
            
            # Analyze Vermont-relevant crops
            ag_patches = []
            total_pixels = sum(int(count) for count in crop_stats.values())
            
            if total_pixels == 0:
                logger.warning("No CDL data found in area")
                return {'ag_patches': [], 'dominant_ag': None}
            
            for crop_code_str, pixel_count in crop_stats.items():
                crop_code = int(crop_code_str)
                
                if crop_code not in self.VERMONT_CROPS:
                    continue
                
                crop_info = self.VERMONT_CROPS[crop_code]
                
                # Skip crops not common in Vermont
                if not crop_info.get('common_in_vt', False):
                    continue
                
                proportion = int(pixel_count) / total_pixels
                
                # Only include significant patches (> 2% of area or important crops)
                if proportion < 0.02 and crop_code not in [1, 141, 142]:  # Always include corn and forests
                    continue
                
                quality_score = crop_info['season_quality'].get(season, 0.5)
                
                ag_patches.append({
                    'crop_type': crop_info['name'],
                    'crop_code': crop_code,
                    'quality_score': quality_score,
                    'proportion': proportion,
                    'area_percent': proportion * 100,
                    'description': crop_info['description']
                })
            
            # Sort by quality score
            ag_patches.sort(key=lambda x: x['quality_score'], reverse=True)
            
            # Calculate dominant agricultural food
            dominant = ag_patches[0] if ag_patches else None
            
            return {
                'ag_patches': ag_patches,
                'dominant_ag': dominant,
                'ag_count': len(ag_patches),
                'analysis_method': 'USDA_CDL'
            }
            
        except Exception as e:
            logger.warning(f"CDL analysis failed: {e}")
            return {'ag_patches': [], 'dominant_ag': None}
    
    def _analyze_vermont_mast_production(self, 
                                        area: ee.Geometry, 
                                        season: str) -> Dict[str, Any]:
        """
        Analyze hardwood mast production using NDVI + forest classification.
        Focuses on oak, beech, and apple trees.
        """
        try:
            # Get current date for imagery
            end_date = datetime.now()
            start_date = end_date - timedelta(days=120)  # Last 4 months for mast assessment
            
            # Get Landsat imagery for NDVI
            collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterBounds(area) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUD_COVER', 30))
            
            if collection.size().getInfo() == 0:
                logger.warning("No recent imagery for mast analysis")
                return {'mast_quality': 'unknown', 'mast_score': 0.5}
            
            # Calculate NDVI
            def calc_ndvi(image):
                return image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
            
            ndvi_collection = collection.map(calc_ndvi)
            median_ndvi = ndvi_collection.median()
            
            # Get land cover to identify deciduous forests
            nlcd = ee.Image("USGS/NLCD_RELEASES/2021_REL/NLCD/2021") \
                .select('landcover') \
                .clip(area)
            
            # Mask for deciduous forest (class 41) and mixed forest (class 43)
            forest_mask = nlcd.eq(41).Or(nlcd.eq(43))
            forest_ndvi = median_ndvi.updateMask(forest_mask)
            
            # Calculate forest NDVI statistics
            forest_stats = forest_ndvi.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev(), '', True
                ).combine(
                    ee.Reducer.min(), '', True
                ).combine(
                    ee.Reducer.max(), '', True
                ),
                geometry=area,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            mean_forest_ndvi = forest_stats.get('NDVI_mean', 0.6)
            
            # Interpret NDVI for mast production
            # Research shows: High NDVI in hardwoods = good mast year
            if mean_forest_ndvi > 0.75:
                mast_quality = 'excellent'
                mast_score = 0.90
                description = 'Very high NDVI indicates excellent mast production'
            elif mean_forest_ndvi > 0.65:
                mast_quality = 'good'
                mast_score = 0.75
                description = 'Good NDVI indicates above-average mast production'
            elif mean_forest_ndvi > 0.55:
                mast_quality = 'moderate'
                mast_score = 0.60
                description = 'Moderate NDVI indicates average mast production'
            else:
                mast_quality = 'poor'
                mast_score = 0.35
                description = 'Low NDVI indicates below-average mast production'
            
            # Seasonal adjustment
            season_multiplier = {
                'early_season': 1.0,   # Peak mast availability
                'rut': 0.85,           # Some mast consumed
                'late_season': 0.60    # Most mast gone
            }.get(season, 0.75)
            
            adjusted_score = mast_score * season_multiplier
            
            return {
                'mast_quality': mast_quality,
                'mast_score': adjusted_score,
                'forest_ndvi': round(mean_forest_ndvi, 3),
                'description': description,
                'season_adjustment': season_multiplier,
                'analysis_method': 'NDVI_forest_classification'
            }
            
        except Exception as e:
            logger.warning(f"Mast analysis failed: {e}")
            return {
                'mast_quality': 'moderate',
                'mast_score': 0.60,
                'description': 'Fallback estimate - moderate mast production'
            }
    
    def _analyze_vermont_browse(self, area: ee.Geometry, season: str) -> Dict[str, Any]:
        """
        Analyze browse availability (woody vegetation, edges, young forest).
        Critical for late-season Vermont hunting.
        """
        try:
            # Get land cover for browse analysis
            nlcd = ee.Image("USGS/NLCD_RELEASES/2021_REL/NLCD/2021") \
                .select('landcover') \
                .clip(area)
            
            # Browse-producing cover types
            # Class 52: Shrub/Scrub (excellent browse)
            # Class 71: Grassland/Herbaceous (edge browse)
            # Class 41: Deciduous Forest (browse + mast)
            # Class 42: Evergreen Forest (winter browse - hemlock/cedar)
            
            browse_mask = nlcd.eq(52).Or(nlcd.eq(71)).Or(nlcd.eq(41)).Or(nlcd.eq(42))
            
            # Calculate browse coverage
            browse_stats = browse_mask.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=area,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            browse_coverage = browse_stats.get('landcover', 0.5)
            
            # Seasonal browse scoring
            if season == 'late_season':
                # Winter browse is CRITICAL in Vermont
                base_score = browse_coverage * 0.8
                importance = 'critical'
            elif season == 'rut':
                # Browse supplemental during rut
                base_score = browse_coverage * 0.5
                importance = 'moderate'
            else:  # early_season
                # Fresh browse good but not primary
                base_score = browse_coverage * 0.6
                importance = 'good'
            
            return {
                'browse_availability': browse_coverage,
                'browse_score': base_score,
                'browse_importance': importance,
                'description': f'{importance.capitalize()} browse for {season}',
                'analysis_method': 'NLCD_cover_classification'
            }
            
        except Exception as e:
            logger.warning(f"Browse analysis failed: {e}")
            return {
                'browse_availability': 0.5,
                'browse_score': 0.5,
                'description': 'Moderate browse availability (estimated)'
            }
    
    def _combine_vermont_food_sources(self,
                                     ag_results: Dict,
                                     mast_results: Dict,
                                     browse_results: Dict,
                                     season: str) -> Dict[str, Any]:
        """
        Combine all Vermont food sources into unified scoring.
        """
        # Get seasonal weights
        weights = self.VERMONT_SEASONAL_PRIORITIES[season]['weights']
        
        # Calculate weighted food score
        ag_score = ag_results.get('dominant_ag', {}).get('quality_score', 0.4)
        mast_score = mast_results.get('mast_score', 0.5)
        browse_score = browse_results.get('browse_score', 0.5)
        
        overall_food_score = (
            ag_score * weights['agriculture'] +
            mast_score * weights['mast'] +
            browse_score * weights['browse']
        )
        
        # Compile food patches
        food_patches = []
        
        # Add agricultural patches
        for ag_patch in ag_results.get('ag_patches', []):
            food_patches.append({
                'type': 'agricultural',
                'name': ag_patch['crop_type'],
                'quality_score': ag_patch['quality_score'],
                'coverage_percent': ag_patch['area_percent'],
                'description': ag_patch['description']
            })
        
        # Add mast production as patch
        if mast_results.get('mast_score', 0) > 0.5:
            food_patches.append({
                'type': 'mast',
                'name': f"{mast_results['mast_quality'].capitalize()} Mast Production",
                'quality_score': mast_results['mast_score'],
                'description': mast_results['description']
            })
        
        # Add browse if significant
        if browse_results.get('browse_score', 0) > 0.4:
            food_patches.append({
                'type': 'browse',
                'name': 'Browse Areas',
                'quality_score': browse_results['browse_score'],
                'description': browse_results['description']
            })
        
        # Sort by quality
        food_patches.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return {
            'overall_food_score': overall_food_score,
            'food_patches': food_patches,
            'dominant_food': food_patches[0] if food_patches else None,
            'ag_analysis': ag_results,
            'mast_analysis': mast_results,
            'browse_analysis': browse_results,
            'season': season,
            'food_source_count': len(food_patches)
        }
    
    def _fallback_vermont_food_analysis(self, season: str) -> Dict[str, Any]:
        """Fallback food analysis when GEE unavailable"""
        return {
            'overall_food_score': 0.55,
            'food_patches': [
                {
                    'type': 'estimated',
                    'name': 'Mixed Vermont Habitat',
                    'quality_score': 0.55,
                    'description': 'Estimated food availability (GEE unavailable)'
                }
            ],
            'dominant_food': {
                'type': 'estimated',
                'name': 'Mixed Vermont Habitat',
                'quality_score': 0.55
            },
            'season': season,
            'food_source_count': 1,
            'fallback': True
        }


# Global instance
_vermont_food_classifier = None

def get_vermont_food_classifier() -> VermontFoodClassifier:
    """Get singleton Vermont food classifier instance"""
    global _vermont_food_classifier
    if _vermont_food_classifier is None:
        _vermont_food_classifier = VermontFoodClassifier()
    return _vermont_food_classifier
