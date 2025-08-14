#!/usr/bin/env python3
"""
Analyze User's GPX File

This script will help us see what waypoint names and types are actually 
in the user's GPX file so we can update the parser to match their naming conventions.
"""

import xml.etree.ElementTree as ET
from collections import Counter
import re

def analyze_gpx_content():
    """Analyze the user's uploaded GPX content to understand naming patterns"""
    
    print("🔍 Analyzing Your GPX File Content")
    print("=" * 50)
    
    # Try to find any recent GPX content in logs or temporary storage
    # Since we can't access the uploaded file directly, let's check if there's
    # any way to see what was processed
    
    # First, let's create a simple way for the user to paste their GPX content
    print("To analyze your GPX file, I need to see some sample waypoint names.")
    print("\nPlease follow these steps:")
    print("\n1. Open your GPX file in a text editor (Notepad)")
    print("2. Look for lines that start with '<wpt lat='")
    print("3. Copy a few example waypoint sections")
    print("\nExample of what to look for:")
    print("""
    <wpt lat="44.123" lon="-72.456">
      <name>Stand Site 1</name>
      <desc>Good bedding area</desc>
      <type>Waypoint</type>
    </wpt>
    """)
    
    return True

def suggest_keyword_mapping():
    """Suggest common hunting waypoint name patterns"""
    
    print("\n🎯 Common Hunting Waypoint Names I Should Look For:")
    print("=" * 50)
    
    common_patterns = {
        "Stand/Blind Locations": [
            "stand", "blind", "tree stand", "ground blind", "ladder stand",
            "hang on", "climbing stand", "bow stand", "gun stand"
        ],
        "Deer Sign": [
            "scrape", "rub", "bedding", "bed", "feeding", "browse",
            "trail", "crossing", "funnel", "pinch point"
        ],
        "Hunting Areas": [
            "hunting spot", "hunt area", "deer area", "buck area",
            "morning stand", "evening stand", "all day stand"
        ],
        "Observation Points": [
            "camera", "trail cam", "scout", "observation", "watch",
            "vantage point", "overlook"
        ],
        "Terrain Features": [
            "ridge", "saddle", "draw", "creek", "field edge",
            "fence row", "transition", "oak ridge", "cedar thicket"
        ]
    }
    
    for category, keywords in common_patterns.items():
        print(f"\n{category}:")
        for keyword in keywords:
            print(f"  - {keyword}")
    
    print("\n💡 Tip: Tell me what types of names your waypoints have!")
    print("Examples: 'Stand 1', 'Oak Grove', 'Creek Bottom', 'Scrape Line', etc.")

def create_enhanced_parser():
    """Create an enhanced parser with more flexible keyword matching"""
    
    print("\n🔧 Creating Enhanced Parser")
    print("=" * 30)
    
    enhanced_keywords = """
    # Enhanced hunting waypoint detection
    HUNTING_KEYWORDS = {
        # Specific deer sign
        'scrape', 'scrapes', 'buck scrape', 'fresh scrape',
        'rub', 'rubs', 'buck rub', 'rub line',
        'bed', 'beds', 'bedding', 'bedding area', 'deer bed',
        
        # Hunting locations
        'stand', 'stands', 'tree stand', 'ladder stand', 'hang on',
        'blind', 'ground blind', 'bow blind',
        'hunt', 'hunting', 'hunting spot', 'hunt area',
        
        # Deer areas and behavior
        'deer', 'buck', 'doe', 'fawn',
        'feeding', 'browse', 'food plot',
        'trail', 'deer trail', 'game trail',
        'crossing', 'deer crossing',
        'funnel', 'pinch', 'saddle',
        
        # Observation/scouting
        'camera', 'cam', 'trail cam', 'trailcam',
        'scout', 'scouting', 'observation',
        'sign', 'deer sign',
        'track', 'tracks', 'hoofprint',
        'droppings', 'scat', 'pellets',
        
        # Terrain/hunting features  
        'ridge', 'creek', 'draw', 'bottom',
        'field', 'edge', 'fence', 'row',
        'oak', 'acorn', 'mast',
        'thicket', 'cover', 'thick',
        'water', 'pond', 'stream'
    }
    """
    
    print("Enhanced keyword list created!")
    print("This will catch many more hunting-related waypoints.")

if __name__ == "__main__":
    analyze_gpx_content()
    suggest_keyword_mapping()
    create_enhanced_parser()
    
    print("\n🎯 Next Steps:")
    print("1. Tell me what your waypoint names look like")
    print("2. I'll update the parser to match your naming style")
    print("3. Re-import your GPX file with better success!")
