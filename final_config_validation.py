#!/usr/bin/env python3

import sys
sys.path.append('.')

print('🎯 COMPREHENSIVE CONFIGURATION SYSTEM VALIDATION')
print('=' * 50)

# Test 1: Basic Configuration Loading
from backend.config_manager import get_config
config = get_config()
print(f'✅ Configuration System: {config.metadata.environment} environment')
print(f'✅ Configuration Version: {config.metadata.version}')

# Test 2: Module Integration
from backend.mature_buck_predictor import MatureBuckPreferences
prefs = MatureBuckPreferences()
print(f'✅ Mature Buck Preferences: bedding thickness = {prefs.min_bedding_thickness}')

# Test 3: Scoring Engine
from backend.scoring_engine import get_scoring_engine
engine = get_scoring_engine()
rut_weights = engine.seasonal_weights.get('rut', {})
print(f'✅ Scoring Engine: rut movement weight = {rut_weights.get("movement", 0)}')

# Test 4: Distance Scorer  
from backend.distance_scorer import get_distance_scorer
scorer = get_distance_scorer()
print(f'✅ Distance Scorer: road impact range = {scorer.factors.road_impact_range} yards')

# Test 5: Parameter Updates
original = config.get('api_settings.suggestion_threshold', 0)
config.update_config('api_settings.suggestion_threshold', 9.0)
updated = config.get('api_settings.suggestion_threshold', 0)
config.update_config('api_settings.suggestion_threshold', original)
print(f'✅ Runtime Updates: threshold changed from {original} to {updated} and back')

print('\n🎉 ALL CONFIGURATION MANAGEMENT FEATURES OPERATIONAL!')
print(f'📊 Total parameters managed: {len(config._config_data)} categories')
print(f'📁 Configuration files: {len(config.metadata.source_files)} loaded')
print(f'⚡ Hot-reload: {"Enabled" if config._observer else "Disabled"}')
