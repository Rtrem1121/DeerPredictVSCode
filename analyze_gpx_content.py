#!/usr/bin/env python3
"""
SAFE GPX Content Analyzer

This reads a GPX file and shows what waypoint names are in it,
without importing anything or modifying any app code.
"""

import xml.etree.ElementTree as ET
from collections import Counter

def analyze_gpx_file_safely(file_path):
    """Safely analyze a GPX file to understand waypoint naming patterns"""
    
    print("🔍 SAFE GPX File Analysis")
    print("=" * 30)
    print(f"📁 Analyzing: {file_path}")
    print("⚠️  This only reads the file - no changes made")
    
    try:
        # Read and parse GPX file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        root = ET.fromstring(content)
        
        # Find all waypoints
        waypoints = []
        for wpt in root.findall('.//{http://www.topografix.com/GPX/1/1}wpt'):
            name_elem = wpt.find('.//{http://www.topografix.com/GPX/1/1}name')
            desc_elem = wpt.find('.//{http://www.topografix.com/GPX/1/1}desc')
            type_elem = wpt.find('.//{http://www.topografix.com/GPX/1/1}type')
            
            waypoint = {
                'name': name_elem.text if name_elem is not None else 'No name',
                'desc': desc_elem.text if desc_elem is not None else '',
                'type': type_elem.text if type_elem is not None else '',
                'lat': wpt.get('lat', ''),
                'lon': wpt.get('lon', '')
            }
            waypoints.append(waypoint)
        
        # Also try without namespace
        if not waypoints:
            for wpt in root.findall('.//wpt'):
                name_elem = wpt.find('.//name')
                desc_elem = wpt.find('.//desc')
                type_elem = wpt.find('.//type')
                
                waypoint = {
                    'name': name_elem.text if name_elem is not None else 'No name',
                    'desc': desc_elem.text if desc_elem is not None else '',
                    'type': type_elem.text if type_elem is not None else '',
                    'lat': wpt.get('lat', ''),
                    'lon': wpt.get('lon', '')
                }
                waypoints.append(waypoint)
        
        print(f"\n📊 Found {len(waypoints)} waypoints")
        
        # Analyze waypoint names
        if waypoints:
            print("\n🏷️ Sample Waypoint Names (first 10):")
            for i, wp in enumerate(waypoints[:10]):
                print(f"   {i+1:2}. '{wp['name']}' - {wp['type']}")
                if wp['desc']:
                    print(f"      Desc: {wp['desc'][:50]}...")
            
            # Count name patterns
            name_words = []
            for wp in waypoints:
                if wp['name'] and wp['name'] != 'No name':
                    words = wp['name'].lower().split()
                    name_words.extend(words)
            
            if name_words:
                print(f"\n🔍 Most Common Words in Names:")
                word_counts = Counter(name_words)
                for word, count in word_counts.most_common(10):
                    print(f"   '{word}': {count} times")
            
            # Check for hunting-related terms
            hunting_terms = [
                'stand', 'deer', 'buck', 'hunt', 'scrape', 'rub', 'bed', 
                'trail', 'camera', 'blind', 'feeding', 'oak', 'ridge'
            ]
            
            hunting_found = []
            for term in hunting_terms:
                count = sum(1 for wp in waypoints if term in wp['name'].lower() or term in wp['desc'].lower())
                if count > 0:
                    hunting_found.append((term, count))
            
            if hunting_found:
                print(f"\n🎯 Hunting-Related Terms Found:")
                for term, count in hunting_found:
                    print(f"   '{term}': {count} waypoints")
            else:
                print(f"\n⚠️ No obvious hunting terms found in waypoint names")
                print("   This might be why import failed - names don't match hunting keywords")
        
        return waypoints
        
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        return []

def suggest_solutions(waypoints):
    """Suggest solutions based on analysis"""
    
    if not waypoints:
        return
    
    print(f"\n💡 Suggested Solutions:")
    print("=" * 25)
    
    # Check if names look generic
    generic_patterns = ['waypoint', 'point', 'location', 'spot', 'place']
    has_generic = any(pattern in wp['name'].lower() for wp in waypoints for pattern in generic_patterns)
    
    if has_generic:
        print("🔧 Option 1: Your waypoints have generic names")
        print("   - The app looks for hunting-specific terms")
        print("   - Try renaming key waypoints with terms like:")
        print("     'Stand', 'Deer Area', 'Hunting Spot', 'Buck Sign'")
    
    # Check for numbered waypoints
    has_numbers = any(any(c.isdigit() for c in wp['name']) for wp in waypoints)
    if has_numbers:
        print("🔧 Option 2: Use descriptions instead of names")
        print("   - Add hunting terms to waypoint descriptions")
        print("   - Example: 'Stand 1' → Add description 'Deer hunting stand'")
    
    print("🔧 Option 3: Modify waypoint names before import")
    print("   - Edit your GPX file in a text editor")
    print("   - Add hunting keywords to important waypoint names")
    
    print("🔧 Option 4: Use confidence override")
    print("   - Set a specific confidence level for all waypoints")
    print("   - This helps even if categorization isn't perfect")

if __name__ == "__main__":
    # Try different possible file locations
    possible_files = [
        "hunting-waypoints.gpx",
        "waypoints.gpx", 
        "scouting.gpx",
        "deer-hunting.gpx"
    ]
    
    file_found = False
    for filename in possible_files:
        try:
            with open(filename, 'r'):
                waypoints = analyze_gpx_file_safely(filename)
                suggest_solutions(waypoints)
                file_found = True
                break
        except FileNotFoundError:
            continue
    
    if not file_found:
        print("🔍 GPX File Analysis Tool")
        print("=" * 30)
        print("📁 No GPX file found in current directory")
        print("\n📋 To use this tool:")
        print("1. Copy your GPX file to the app directory")
        print("2. Name it 'hunting-waypoints.gpx'")
        print("3. Run this script again")
        print("\nOr specify the full path to your GPX file.")
