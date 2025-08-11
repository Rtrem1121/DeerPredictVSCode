#!/usr/bin/env python3
"""
Test Enhanced Mature Buck Prediction System

This script tests the enhanced spatial analysis capabilities of the mature buck predictor,
including movement corridors, bedding predictions, feeding zones, and terrain-based stand positioning.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from mature_buck_predictor import get_mature_buck_predictor, generate_mature_buck_stand_recommendations
import json

def test_enhanced_spatial_predictions():
    """Test the enhanced spatial prediction capabilities"""
    print("🦌 Testing Enhanced Mature Buck Prediction System")
    print("=" * 60)
    
    # Initialize predictor
    predictor = get_mature_buck_predictor()
    
    # Test coordinates (Vermont location)
    lat = 44.2619
    lon = -72.5806
    
    # Sample terrain features with good mature buck habitat
    terrain_features = {
        'canopy_closure': 85.0,
        'elevation': 320.0,
        'slope': 15.0,
        'aspect': 345.0,  # North-facing
        'understory_density': 75.0,
        'drainage_density': 1.8,
        'ridge_connectivity': 0.75,
        'terrain_roughness': 0.65,
        'cover_type_diversity': 4,
        'thick_cover_patches': 3,
        'escape_cover_density': 80.0,
        'nearest_road_distance': 600.0,
        'nearest_building_distance': 900.0,
        'trail_density': 0.3,
        'agricultural_proximity': 250.0,
        'water_proximity': 180.0,
        'hunter_accessibility': 0.4,
        'wetland_proximity': 150.0,
        'cliff_proximity': 800.0,
        'visibility_limitation': 0.85,
        'edge_density': 0.7
    }
    
    # Sample weather data
    weather_data = {
        'temperature': 8,
        'wind_speed': 6,
        'pressure_trend': 'falling',
        'precipitation': 0.5
    }
    
    print(f"📍 Test Location: {lat:.4f}, {lon:.4f}")
    print(f"🌲 Canopy Closure: {terrain_features['canopy_closure']:.1f}%")
    print(f"⛰️  Elevation: {terrain_features['elevation']:.1f}m")
    print(f"🌊 Drainage Density: {terrain_features['drainage_density']:.1f}")
    print(f"🔗 Ridge Connectivity: {terrain_features['ridge_connectivity']:.2f}")
    print()
    
    # Test terrain analysis
    print("🔍 TERRAIN ANALYSIS")
    print("-" * 40)
    terrain_scores = predictor.analyze_mature_buck_terrain(terrain_features, lat, lon)
    
    for score_type, score_value in terrain_scores.items():
        print(f"{score_type.replace('_', ' ').title()}: {score_value:.1f}%")
    print()
    
    # Test movement predictions for different seasons
    seasons = ['early_season', 'rut', 'late_season']
    
    for season in seasons:
        print(f"🦌 MOVEMENT PREDICTIONS - {season.replace('_', ' ').title()}")
        print("-" * 40)
        
        movement_data = predictor.predict_mature_buck_movement(
            season, 7, terrain_features, weather_data, lat, lon  # 7 AM
        )
        
        print(f"Movement Probability: {movement_data['movement_probability']:.1f}%")
        print(f"Confidence Score: {movement_data['confidence_score']:.1f}%")
        print()
        
        # Display movement corridors
        if movement_data['movement_corridors']:
            print("🛤️  Movement Corridors:")
            for i, corridor in enumerate(movement_data['movement_corridors'], 1):
                print(f"  {i}. {corridor['type'].replace('_', ' ').title()}")
                print(f"     📍 {corridor['lat']:.6f}, {corridor['lon']:.6f}")
                print(f"     🎯 Confidence: {corridor['confidence']:.1f}%")
                print(f"     📝 {corridor['description']}")
                print()
        else:
            print("🛤️  No movement corridors identified")
            print()
        
        # Display bedding predictions
        if movement_data['bedding_predictions']:
            print("🛏️  Bedding Locations:")
            for i, bedding in enumerate(movement_data['bedding_predictions'], 1):
                print(f"  {i}. {bedding['type'].replace('_', ' ').title()}")
                print(f"     📍 {bedding['lat']:.6f}, {bedding['lon']:.6f}")
                print(f"     🎯 Confidence: {bedding['confidence']:.1f}%")
                print(f"     📝 {bedding['description']}")
                factors = bedding.get('suitability_factors', {})
                if factors:
                    print(f"     ✅ Factors: {', '.join([k for k, v in factors.items() if v])}")
                print()
        else:
            print("🛏️  No bedding areas identified")
            print()
        
        # Display feeding predictions
        if movement_data['feeding_predictions']:
            print("🍃 Feeding Zones:")
            for i, feeding in enumerate(movement_data['feeding_predictions'], 1):
                print(f"  {i}. {feeding['type'].replace('_', ' ').title()}")
                print(f"     📍 {feeding['lat']:.6f}, {feeding['lon']:.6f}")
                print(f"     🎯 Confidence: {feeding['confidence']:.1f}%")
                print(f"     📝 {feeding['description']}")
                if 'feeding_characteristics' in feeding:
                    food_quality = feeding['feeding_characteristics'].get('food_quality', 'unknown')
                    print(f"     🥬 Food Quality: {food_quality.replace('_', ' ')}")
                print()
        else:
            print("🍃 No feeding zones identified")
            print()
        
        print("=" * 60)
    
    # Test enhanced stand recommendations
    print("🏹 ENHANCED STAND RECOMMENDATIONS")
    print("-" * 40)
    
    stand_recommendations = generate_mature_buck_stand_recommendations(
        terrain_features, terrain_scores, lat, lon
    )
    
    for i, recommendation in enumerate(stand_recommendations, 1):
        print(f"{i}. {recommendation['type']}")
        coords = recommendation['coordinates']
        print(f"   📍 Position: {coords['lat']:.6f}, {coords['lon']:.6f}")
        print(f"   🎯 Confidence: {recommendation['confidence']:.1f}%")
        print(f"   📝 {recommendation['description']}")
        print(f"   🎯 Terrain Justification: {recommendation.get('terrain_justification', 'N/A')}")
        
        # Display precision factors
        precision_factors = coords.get('precision_factors', {})
        if precision_factors:
            print(f"   🔧 Positioning Method: {precision_factors.get('positioning_method', 'unknown')}")
            if 'distance_from_center' in coords:
                print(f"   📏 Distance from Center: {coords['distance_from_center']:.0f}m")
        
        print(f"   ⏰ Best Times: {recommendation['best_times']}")
        print()
    
    print("✅ Enhanced mature buck prediction testing complete!")

if __name__ == "__main__":
    test_enhanced_spatial_predictions()
