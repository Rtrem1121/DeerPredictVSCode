#!/usr/bin/env python3
"""Simplified trail camera predictor to test basic functionality"""

from typing import Dict, List
import logging
import numpy as np

logger = logging.getLogger(__name__)

def test_trail_camera_basic(lat: float, lon: float, terrain_features: Dict, season: str) -> Dict:
    """Basic trail camera recommendation"""
    logger.info(f"🎥 Basic trail camera test for {lat}, {lon} in {season}")
    
    # Create a simple camera placement
    camera = {
        'lat': lat + 0.0003,  # ~33 yards north
        'lon': lon,
        'type': 'Travel Corridor Camera',
        'confidence': 85.0,
        'setup_height': '10-12 feet',
        'setup_angle': '30° downward, perpendicular to trail',
        'expected_photos': 'High - daily travel route',
        'best_times': ['Dawn (5-8am)', 'Dusk (5-8pm)'],
        'setup_notes': [
            'Position camera perpendicular to travel direction',
            'Clear shooting lanes 20-30 yards both directions',
            'Use low-glow IR to avoid spooking mature bucks'
        ],
        'wind_considerations': 'Position downwind of expected approach direction'
    }
    
    return {
        'cameras': [camera],
        'count': 1,
        'status': 'success'
    }
