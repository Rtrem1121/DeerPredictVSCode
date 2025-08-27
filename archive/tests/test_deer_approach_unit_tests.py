#!/usr/bin/env python3
"""
Unit Tests for Deer Approach Direction Fix

These tests verify the fix works correctly before implementing in production.
"""

import unittest
from test_deer_approach_fix import enhanced_deer_approach_calculation, calculate_terrain_based_deer_approach

class TestDeerApproachFix(unittest.TestCase):
    
    def test_no_more_hardcoded_se_default(self):
        """Test that we don't always get SE (135°) as the default"""
        
        # Different terrain types should give different results
        test_cases = [
            {
                'terrain_features': {'terrain_type': 'ridge_top', 'aspect': 180, 'slope': 20},
                'coordinates': {'lat': 44.0, 'lon': -72.0},
                'stand_type': 'Travel Corridor',
                'bedding_zones': {'zones': []}
            },
            {
                'terrain_features': {'terrain_type': 'valley_agricultural', 'aspect': 90, 'slope': 5, 'forest_edge': True},
                'coordinates': {'lat': 44.1, 'lon': -72.1},
                'stand_type': 'Feeding Area',
                'bedding_zones': {'zones': []}
            },
            {
                'terrain_features': {'terrain_type': 'north_slope', 'aspect': 360, 'slope': 25},
                'coordinates': {'lat': 44.2, 'lon': -72.2},
                'stand_type': 'Bedding Area',
                'bedding_zones': {'zones': []}
            }
        ]
        
        results = []
        for case in test_cases:
            bearing, direction = enhanced_deer_approach_calculation(case)
            results.append((bearing, direction))
            
        # Verify we get different results (not all SE/135°)
        bearings = [r[0] for r in results]
        directions = [r[1] for r in results]
        
        # Should not all be 135° (SE)
        self.assertFalse(all(b == 135.0 for b in bearings), 
                        "All results are still 135° - fix didn't work!")
        
        # Should not all be SE
        self.assertFalse(all(d == 'SE' for d in directions),
                        "All results are still SE - fix didn't work!")
        
        print(f"✅ Results vary by terrain: {directions}")
    
    def test_bedding_zone_calculation_takes_priority(self):
        """Test that bedding zone calculation is used when available"""
        
        # Case with bedding zone data
        case_with_bedding = {
            'terrain_features': {'terrain_type': 'mixed'},
            'coordinates': {'lat': 44.26, 'lon': -72.58},
            'stand_type': 'Travel Corridor',
            'bedding_zones': {
                'zones': [
                    {'lat': 44.27, 'lon': -72.57, 'confidence': 85}
                ]
            }
        }
        
        # Case without bedding zone data (same location)
        case_without_bedding = {
            'terrain_features': {'terrain_type': 'mixed'},
            'coordinates': {'lat': 44.26, 'lon': -72.58},
            'stand_type': 'Travel Corridor',
            'bedding_zones': {'zones': []}
        }
        
        bearing_with, dir_with = enhanced_deer_approach_calculation(case_with_bedding)
        bearing_without, dir_without = enhanced_deer_approach_calculation(case_without_bedding)
        
        print(f"✅ With bedding: {dir_with} ({bearing_with:.0f}°)")
        print(f"✅ Without bedding: {dir_without} ({bearing_without:.0f}°)")
        
        # They should be different (bedding zone gives more precise calculation)
        self.assertNotEqual(bearing_with, bearing_without,
                           "Bedding zone calculation should differ from terrain fallback")
    
    def test_stand_type_affects_calculation(self):
        """Test that different stand types give different approach directions"""
        
        base_case = {
            'terrain_features': {'terrain_type': 'ridge_top', 'aspect': 180, 'slope': 15},
            'coordinates': {'lat': 44.0, 'lon': -72.0},
            'bedding_zones': {'zones': []}
        }
        
        stand_types = ['Travel Corridor', 'Bedding Area', 'Feeding Area', 'General']
        results = {}
        
        for stand_type in stand_types:
            case = base_case.copy()
            case['stand_type'] = stand_type
            bearing, direction = enhanced_deer_approach_calculation(case)
            results[stand_type] = (bearing, direction)
            print(f"✅ {stand_type}: {direction} ({bearing:.0f}°)")
        
        # Should get different results for different stand types
        bearings = [r[0] for r in results.values()]
        unique_bearings = set(bearings)
        
        self.assertGreater(len(unique_bearings), 1,
                          "Different stand types should produce different approach directions")
    
    def test_terrain_type_affects_calculation(self):
        """Test that different terrain types give different results"""
        
        base_case = {
            'coordinates': {'lat': 44.0, 'lon': -72.0},
            'stand_type': 'Travel Corridor',
            'bedding_zones': {'zones': []}
        }
        
        terrain_types = [
            {'terrain_type': 'ridge_top', 'aspect': 180, 'slope': 20},
            {'terrain_type': 'valley_agricultural', 'aspect': 90, 'slope': 5},
            {'terrain_type': 'north_slope', 'aspect': 360, 'slope': 25},
            {'terrain_type': 'saddle', 'aspect': 45, 'slope': 10}
        ]
        
        results = []
        for terrain in terrain_types:
            case = base_case.copy()
            case['terrain_features'] = terrain
            bearing, direction = enhanced_deer_approach_calculation(case)
            results.append((terrain['terrain_type'], bearing, direction))
            print(f"✅ {terrain['terrain_type']}: {direction} ({bearing:.0f}°)")
        
        # Should get varied results
        bearings = [r[1] for r in results]
        unique_bearings = set(bearings)
        
        self.assertGreater(len(unique_bearings), 1,
                          "Different terrain types should produce different approach directions")

if __name__ == '__main__':
    print("🧪 Running Deer Approach Direction Fix Tests\n")
    unittest.main(verbosity=2)
