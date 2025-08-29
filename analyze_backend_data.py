"""
Comprehensive Backend Data Analysis
Check what the backend is currently generating for all site types
"""

import requests
import json
from datetime import datetime

def analyze_backend_data():
    """Analyze complete backend response to see all generated sites"""
    
    print("🔍 COMPREHENSIVE BACKEND DATA ANALYSIS")
    print("=" * 60)
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/predict",
            json={
                "lat": 43.3145,
                "lon": -73.2175,
                "date_time": f"{datetime.now().date()}T07:00:00",
                "season": "early_season",
                "fast_mode": True,
                "include_camera_placement": True  # Ensure camera placement is requested
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle both API formats
            if 'success' in data and data.get('success'):
                prediction = data.get('data', data)
            else:
                prediction = data
            
            print("📊 COMPLETE BACKEND RESPONSE ANALYSIS:")
            print("=" * 40)
            
            # 1. Bedding Zones
            bedding_zones = prediction.get('bedding_zones', {})
            if 'features' in bedding_zones:
                bedding_count = len(bedding_zones['features'])
                print(f"🛏️ BEDDING ZONES: {bedding_count}")
                for i, feature in enumerate(bedding_zones['features'], 1):
                    coords = feature['geometry']['coordinates']
                    lat, lon = coords[1], coords[0]
                    score = feature['properties'].get('score', 0)
                    print(f"   Zone {i}: {lat:.6f}, {lon:.6f} (Score: {score:.1f})")
            else:
                print("🛏️ BEDDING ZONES: 0 (missing 'features')")
            
            # 2. Stand Recommendations (from mature_buck_analysis)
            mature_buck = prediction.get('mature_buck_analysis', {})
            stand_recs = mature_buck.get('stand_recommendations', [])
            print(f"\n🎯 STAND SITES (mature_buck_analysis): {len(stand_recs)}")
            for i, stand in enumerate(stand_recs, 1):
                coords = stand.get('coordinates', {})
                if 'lat' in coords and 'lon' in coords:
                    confidence = stand.get('confidence', 0)
                    stand_type = stand.get('type', 'Unknown')
                    print(f"   Stand {i}: {coords['lat']:.6f}, {coords['lon']:.6f} ({stand_type}, {confidence:.0f}%)")
            
            # 3. Optimized Points (newer structure)
            optimized = prediction.get('optimized_points', {})
            if optimized:
                print(f"\n📍 OPTIMIZED POINTS STRUCTURE:")
                
                # Stand sites from optimized points
                opt_stands = optimized.get('stand_sites', [])
                print(f"🎯 OPTIMIZED STAND SITES: {len(opt_stands)}")
                for i, stand in enumerate(opt_stands, 1):
                    lat, lon = stand.get('lat', 0), stand.get('lon', 0)
                    strategy = stand.get('strategy', 'Unknown')
                    score = stand.get('score', 0)
                    print(f"   Stand {i}: {lat:.6f}, {lon:.6f} ({strategy}, Score: {score:.1f})")
                
                # Bedding sites from optimized points
                opt_bedding = optimized.get('bedding_sites', [])
                print(f"🛏️ OPTIMIZED BEDDING SITES: {len(opt_bedding)}")
                for i, bed in enumerate(opt_bedding, 1):
                    lat, lon = bed.get('lat', 0), bed.get('lon', 0)
                    strategy = bed.get('strategy', 'Unknown')
                    score = bed.get('score', 0)
                    print(f"   Bedding {i}: {lat:.6f}, {lon:.6f} ({strategy}, Score: {score:.1f})")
                
                # Feeding sites from optimized points
                opt_feeding = optimized.get('feeding_sites', [])
                print(f"🌾 OPTIMIZED FEEDING SITES: {len(opt_feeding)}")
                for i, feed in enumerate(opt_feeding, 1):
                    lat, lon = feed.get('lat', 0), feed.get('lon', 0)
                    strategy = feed.get('strategy', 'Unknown')
                    score = feed.get('score', 0)
                    print(f"   Feeding {i}: {lat:.6f}, {lon:.6f} ({strategy}, Score: {score:.1f})")
                
                # Camera placements from optimized points
                opt_cameras = optimized.get('camera_placements', [])
                print(f"📷 OPTIMIZED CAMERA SITES: {len(opt_cameras)}")
                for i, cam in enumerate(opt_cameras, 1):
                    lat, lon = cam.get('lat', 0), cam.get('lon', 0)
                    strategy = cam.get('strategy', 'Unknown')
                    score = cam.get('score', 0)
                    print(f"   Camera {i}: {lat:.6f}, {lon:.6f} ({strategy}, Score: {score:.1f})")
            
            # 4. Feeding Areas (legacy structure)
            feeding_areas = prediction.get('feeding_areas', {})
            if 'features' in feeding_areas:
                feeding_count = len(feeding_areas['features'])
                print(f"\n🌾 FEEDING AREAS (legacy): {feeding_count}")
                for i, feature in enumerate(feeding_areas['features'], 1):
                    coords = feature['geometry']['coordinates']
                    lat, lon = coords[1], coords[0]
                    score = feature['properties'].get('score', 0)
                    print(f"   Feeding {i}: {lat:.6f}, {lon:.6f} (Score: {score:.1f})")
            
            # 5. Camera Placement (legacy structure)
            camera_placement = prediction.get('optimal_camera_placement', {})
            if camera_placement:
                cam_lat = camera_placement.get('lat', 0)
                cam_lon = camera_placement.get('lon', 0)
                cam_confidence = camera_placement.get('confidence', 0)
                print(f"\n📷 CAMERA PLACEMENT (legacy): 1")
                print(f"   Camera: {cam_lat:.6f}, {cam_lon:.6f} (Confidence: {cam_confidence:.0f}%)")
            
            # Summary for frontend planning
            print("\n" + "=" * 60)
            print("📋 FRONTEND DISPLAY PLANNING SUMMARY:")
            print("=" * 60)
            
            total_bedding = bedding_count if 'bedding_count' in locals() else 0
            total_bedding += len(optimized.get('bedding_sites', []))
            
            total_stands = len(stand_recs)
            total_stands += len(optimized.get('stand_sites', []))
            
            total_feeding = feeding_count if 'feeding_count' in locals() else 0
            total_feeding += len(optimized.get('feeding_sites', []))
            
            total_cameras = len(optimized.get('camera_placements', []))
            if camera_placement:
                total_cameras += 1
            
            print(f"🛏️ Total Bedding Sites Available: {total_bedding}")
            print(f"🎯 Total Stand Sites Available: {total_stands}")
            print(f"🌾 Total Feeding Sites Available: {total_feeding}")
            print(f"📷 Total Camera Sites Available: {total_cameras}")
            
            print("\n🎯 USER REQUIREMENTS:")
            print(f"   Needed: 3 bedding, 3 stands, 3 feeding, 1 camera")
            print(f"   Current: {total_bedding} bedding, {total_stands} stands, {total_feeding} feeding, {total_cameras} cameras")
            
            # Identify gaps
            gaps = []
            if total_bedding < 3:
                gaps.append(f"Need {3 - total_bedding} more bedding sites")
            if total_stands < 3:
                gaps.append(f"Need {3 - total_stands} more stand sites")
            if total_feeding < 3:
                gaps.append(f"Need {3 - total_feeding} more feeding sites")
            if total_cameras < 1:
                gaps.append(f"Need {1 - total_cameras} more camera sites")
            
            if gaps:
                print(f"\n⚠️ GAPS TO ADDRESS:")
                for gap in gaps:
                    print(f"   • {gap}")
            else:
                print(f"\n✅ ALL REQUIREMENTS MET!")
            
            return {
                'bedding': total_bedding,
                'stands': total_stands,
                'feeding': total_feeding,
                'cameras': total_cameras,
                'gaps': gaps,
                'prediction_data': prediction
            }
        
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

if __name__ == "__main__":
    result = analyze_backend_data()
    
    if result:
        if not result['gaps']:
            print("\n🎉 Ready to implement frontend display for all required sites!")
        else:
            print("\n🔧 Backend modifications needed to meet requirements.")
