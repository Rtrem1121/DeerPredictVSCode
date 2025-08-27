#!/usr/bin/env python3
"""
Debug script to examine bedding score calculations
"""

import numpy as np
import requests
import json
from backend import core

def test_bedding_scores():
    """Test bedding score calculation and examine why no bedding zones are found"""
    
    # Test coordinates
    lat, lon = 44.5, -89.5
    season = "early"
    
    print("=== Debugging Bedding Score Calculation ===")
    
    # 1. Load rules and get terrain data (mimic what main.py does)
    print("Loading rules and terrain data...")
    rules = core.load_rules()
    
    # Get terrain data
    elevation_grid = core.get_real_elevation_grid(lat, lon)
    vegetation_grid = core.get_vegetation_grid_from_osm(lat, lon)
    road_proximity = core.get_road_proximity_grid(lat, lon)
    
    # Analyze terrain features
    features = core.analyze_terrain_and_vegetation(elevation_grid, vegetation_grid)
    features["road_proximity"] = road_proximity
    
    print(f"Terrain features available: {list(features.keys())}")
    
    # Check bedding-relevant features
    bedding_features = ['south_slope', 'north_slope', 'swamp', 'conifer_dense', 'forest', 'deep_forest']
    for feature in bedding_features:
        if feature in features:
            feature_grid = features[feature]
            if hasattr(feature_grid, 'sum'):
                count = np.sum(feature_grid)
                print(f"  {feature}: {count} cells")
            else:
                print(f"  {feature}: not a grid")
        else:
            print(f"  {feature}: NOT FOUND")
    
    # 2. Get bedding rules specifically
    bedding_rules = [rule for rule in rules if rule.get('behavior') == 'bedding']
    print(f"\nFound {len(bedding_rules)} bedding rules")
    
    # 3. Setup conditions
    conditions = {
        "time_of_day": "afternoon",  # Matches mid-day rules
        "season": season,
        "weather_conditions": [],
        "temperature": 70,
        "snow_depth": 0,
        "leeward_aspects": []
    }
    
    print(f"Conditions: {conditions}")
    
    # 4. Run rule engine and examine bedding scores
    print("\nRunning rule engine...")
    score_maps = core.run_grid_rule_engine(rules, features, conditions)
    
    bedding_scores = score_maps['bedding']
    print(f"Bedding score map shape: {bedding_scores.shape}")
    print(f"Bedding score stats:")
    print(f"  Min: {np.min(bedding_scores):.3f}")
    print(f"  Max: {np.max(bedding_scores):.3f}")
    print(f"  Mean: {np.mean(bedding_scores):.3f}")
    print(f"  Cells > 0: {np.sum(bedding_scores > 0)}")
    print(f"  Cells > 0.1: {np.sum(bedding_scores > 0.1)}")
    print(f"  Cells > 0.5: {np.sum(bedding_scores > 0.5)}")
    
    # 5. Check which rules actually matched
    print(f"\nChecking individual rule matches...")
    for i, rule in enumerate(bedding_rules):
        # Simulate the rule matching logic from core.py
        terrain_key = rule.get("terrain", "any")
        vegetation_key = rule.get("vegetation", "any")
        
        # Get terrain feature
        if terrain_key == "any":
            terrain_grid = np.ones(bedding_scores.shape, dtype=bool)
        else:
            terrain_grid = features.get(terrain_key, np.zeros(bedding_scores.shape, dtype=bool))
        
        # Get vegetation feature
        if vegetation_key == "any":
            vegetation_grid = np.ones(bedding_scores.shape, dtype=bool)
        else:
            vegetation_grid = features.get(vegetation_key, np.zeros(bedding_scores.shape, dtype=bool))
        
        # Combine requirements
        combined_mask = np.logical_and(terrain_grid, vegetation_grid)
        matches = np.sum(combined_mask)
        
        confidence = rule.get("confidence", 0)
        print(f"  Rule {i+1}: terrain={terrain_key}, vegetation={vegetation_key}, confidence={confidence}, matches={matches}")
        
        if matches > 0:
            print(f"    ✓ This rule should contribute {confidence} points to {matches} cells")
        
    return bedding_scores

if __name__ == "__main__":
    test_bedding_scores()
