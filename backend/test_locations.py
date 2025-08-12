#!/usr/bin/env python3
"""
Test mature buck analysis across multiple locations
"""

import sys
import logging
from datetime import datetime
from typing import Dict, Any

from mature_buck_predictor import get_mature_buck_predictor
from terrain_analyzer import get_terrain_analyzer
from scoring_engine import get_scoring_engine, ScoringContext
from config_manager import get_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test locations in Vermont
TEST_LOCATIONS = [
    {
        'name': 'Mount Mansfield State Forest',
        'lat': 44.5437,
        'lon': -72.8143,
        'description': 'Mountainous terrain with mixed hardwoods',
        'expected_features': ['ridgelines', 'steep_slopes', 'natural_funnels']
    },
    {
        'name': 'Champlain Valley',
        'lat': 44.3853,
        'lon': -73.2287,
        'description': 'Agricultural area with woodlots',
        'expected_features': ['field_edges', 'woodlots', 'travel_corridors']
    }
]

def analyze_location(location: Dict[str, Any]) -> Dict[str, Any]:
    """Run complete analysis for a single location"""
    
    logger.info(f"\n📍 Analyzing location: {location['name']}")
    logger.info(f"Description: {location['description']}")
    
    try:
        # Get components
        predictor = get_mature_buck_predictor()
        terrain = get_terrain_analyzer()
        scorer = get_scoring_engine()
        
        # Run terrain analysis
        logger.info("\n🗺️ Running terrain analysis...")
        terrain_data = terrain.analyze_terrain_features(location['lat'], location['lon'])
        
        # Validate terrain features
        detected_features = terrain_data.get('detected_features', [])
        logger.info(f"✅ Detected {len(detected_features)} terrain features")
        
        for feature in detected_features[:5]:  # Show first 5 features
            feature_type = feature.get('type', 'unknown')
            confidence = feature.get('confidence', 0)
            logger.info(f"  • {feature_type}: {confidence:.1f}% confidence")
            
        # Calculate scores
        logger.info("\n🎯 Calculating location scores...")
        context = ScoringContext(
            season='rut',
            time_of_day=8,  # Morning hours
            weather_conditions=['clear', 'calm'],
            pressure_level='moderate',
            terrain_type='mixed',
            behavior_type='general'
        )
        scores = scorer.calculate_confidence_score(terrain_data, context)
        
        # Generate prediction
        logger.info("\n🦌 Generating mature buck prediction...")
        prediction = predictor.predict(
            terrain_results=terrain_data,
            scores=scores,
            season='rut',  # Test during rut season
            date_time=datetime.now().isoformat(),
            weather_conditions=['clear', 'calm']
        )
        
        # Extract key metrics
        metrics = {
            'location': location['name'],
            'terrain_score': scores.get('overall_score', 0),
            'buck_suitability': prediction.get('mature_buck_analysis', {}).get('overall_suitability', 0),
            'num_bedding': len(prediction.get('bedding_zones', {}).get('features', [])),
            'num_feeding': len(prediction.get('feeding_areas', {}).get('features', [])),
            'num_travel': len(prediction.get('travel_corridors', {}).get('features', [])),
            'num_stands': len(prediction.get('stand_recommendations', [])),
            'confidence_score': prediction.get('confidence_score', 0)
        }
        
        # Log results
        logger.info("\n📊 Analysis Results:")
        logger.info(f"  • Terrain Score: {metrics['terrain_score']:.1f}/100")
        logger.info(f"  • Buck Suitability: {metrics['buck_suitability']:.1f}/100")
        logger.info(f"  • Bedding Areas: {metrics['num_bedding']}")
        logger.info(f"  • Feeding Areas: {metrics['num_feeding']}")
        logger.info(f"  • Travel Corridors: {metrics['num_travel']}")
        logger.info(f"  • Recommended Stands: {metrics['num_stands']}")
        logger.info(f"  • Confidence Score: {metrics['confidence_score']:.1f}%")
        
        # Validate expected features
        expected_features = location['expected_features']
        found_features = [f['type'] for f in detected_features]
        
        matches = [f for f in expected_features if any(ef in f for ef in found_features)]
        logger.info(f"\n✅ Found {len(matches)}/{len(expected_features)} expected terrain features")
        
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Error analyzing location: {str(e)}")
        raise

def main():
    """Run analysis on all test locations"""
    print("\n🎯 MATURE BUCK LOCATION ANALYSIS TEST")
    print("=" * 60)
    
    results = []
    
    for location in TEST_LOCATIONS:
        try:
            metrics = analyze_location(location)
            results.append(metrics)
        except Exception as e:
            print(f"\n❌ Failed to analyze {location['name']}: {str(e)}")
            continue
    
    if len(results) >= 2:
        # Compare locations
        print("\n📊 LOCATION COMPARISON")
        print("=" * 60)
        
        for r1, r2 in zip(results[:-1], results[1:]):
            print(f"\n{r1['location']} vs {r2['location']}:")
            print(f"Terrain Score: {r1['terrain_score']:.1f} vs {r2['terrain_score']:.1f}")
            print(f"Buck Suitability: {r1['buck_suitability']:.1f} vs {r2['buck_suitability']:.1f}")
            print(f"Total Features: {r1['num_bedding'] + r1['num_feeding'] + r1['num_travel']} vs "
                  f"{r2['num_bedding'] + r2['num_feeding'] + r2['num_travel']}")
            
            # Calculate score differences
            terrain_diff = abs(r1['terrain_score'] - r2['terrain_score'])
            suitability_diff = abs(r1['buck_suitability'] - r2['buck_suitability'])
            
            print(f"\nScore Variations:")
            print(f"• Terrain Score Difference: {terrain_diff:.1f}")
            print(f"• Suitability Score Difference: {suitability_diff:.1f}")
            
            if terrain_diff < 5 and suitability_diff < 5:
                print("\n⚠️ Warning: Locations scoring too similarly, may indicate insufficient differentiation")
            
        print("\n✅ Location comparison complete")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
