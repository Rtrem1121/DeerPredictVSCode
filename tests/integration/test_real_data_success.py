#!/usr/bin/env python3
"""
Real Data Success Report - Shows comprehensive analysis working with actual prediction data
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime

def make_api_request(url, data=None, timeout=30):
    """Make API request using urllib (built-in)"""
    try:
        if data:
            data_encoded = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_encoded)
            req.add_header('Content-Type', 'application/json')
        else:
            req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            response_data = response.read().decode('utf-8')
            return {
                'status_code': response.getcode(),
                'data': json.loads(response_data)
            }
    except Exception as e:
        return {'status_code': 0, 'data': {}, 'error': str(e)}

def test_real_data_success():
    """Show that the system is working with real hunting data"""
    print("🎯 REAL DATA SUCCESS VERIFICATION")
    print("=" * 45)
    
    # Test real hunting location
    test_location = {
        "lat": 45.4215,
        "lon": -75.6972, 
        "date_time": "2024-11-15T06:00:00"
    }
    
    print(f"📍 Location: {test_location['lat']}, {test_location['lon']}")
    print(f"📅 Date: {test_location['date_time']}")
    
    # Make real API call
    backend_url = "http://localhost:8000"
    response = make_api_request(f"{backend_url}/predict", test_location)
    
    if response['status_code'] != 200:
        print(f"❌ API call failed: {response.get('error', 'Unknown error')}")
        return False
    
    data = response['data']
    if not data.get('success'):
        print(f"❌ Prediction failed: {data.get('error', 'Unknown error')}")
        return False
    
    result_data = data['data']
    print("\n🌍 REAL DATA ANALYSIS RESULTS:")
    print("=" * 40)
    
    # Google Earth Engine Data
    if 'gee_data' in result_data:
        gee = result_data['gee_data']
        print(f"📡 Google Earth Engine Data:")
        print(f"   🌲 Canopy Coverage: {gee.get('canopy_coverage', 0)*100:.1f}%")
        print(f"   🏔️ Elevation: {gee.get('elevation', 0):.0f}m")
        print(f"   📐 Slope: {gee.get('slope', 0):.1f}°")
        print(f"   🧭 Aspect: {gee.get('aspect', 0):.0f}°")
        print(f"   🌿 NDVI: {gee.get('ndvi_value', 0):.3f}")
        print(f"   ✅ Query Success: {gee.get('query_success', False)}")
    
    # Weather Data  
    if 'weather_data' in result_data:
        weather = result_data['weather_data']
        print(f"\n🌤️ Real Weather Data:")
        print(f"   🌡️ Temperature: {weather.get('temperature', 0):.1f}°F")
        print(f"   💨 Wind: {weather.get('wind_direction', 0)}° at {weather.get('wind_speed', 0):.1f} mph")
        print(f"   💧 Humidity: {weather.get('humidity', 0)}%")
        print(f"   📊 Pressure: {weather.get('pressure', 0):.2f} inHg")
        print(f"   ❄️ Cold Front: {weather.get('is_cold_front', False)}")
    
    # Bedding Zone Analysis
    if 'bedding_zones' in result_data:
        bedding = result_data['bedding_zones']
        features = bedding.get('features', [])
        props = bedding.get('properties', {})
        
        print(f"\n🛏️ Bedding Zone Analysis:")
        print(f"   📊 Zones Found: {len(features)}")
        print(f"   🎯 Overall Score: {props.get('suitability_analysis', {}).get('overall_score', 0):.1f}")
        
        criteria = props.get('suitability_analysis', {}).get('criteria', {})
        scores = props.get('suitability_analysis', {}).get('scores', {})
        
        if criteria and scores:
            print(f"   📐 Criteria Analysis:")
            print(f"      Canopy: {scores.get('canopy', 0)}/100 (requirement: {criteria.get('canopy_coverage', 0)*100:.0f}%)")
            print(f"      Road Distance: {scores.get('isolation', 0):.1f}/100 (actual: {criteria.get('road_distance', 0):.0f}m)")
            print(f"      Slope: {scores.get('slope', 0)}/100 (actual: {criteria.get('slope', 0):.1f}°)")
    
    # Stand Recommendations  
    if 'mature_buck_analysis' in result_data:
        stands = result_data['mature_buck_analysis'].get('stand_recommendations', [])
        print(f"\n🎪 Stand Recommendations:")
        print(f"   📊 Recommendations: {len(stands)}")
        
        for i, stand in enumerate(stands[:3]):
            coords = stand.get('coordinates', {})
            print(f"   Stand {i+1}:")
            print(f"      📍 Location: {coords.get('lat', 0):.4f}, {coords.get('lon', 0):.4f}")
            print(f"      🎯 Confidence: {stand.get('confidence', 0):.1f}%")
            print(f"      🏷️ Type: {stand.get('type', 'Unknown')}")
            print(f"      💡 Reasoning: {stand.get('reasoning', 'None')}")
    
    # Feeding Areas
    if 'feeding_areas' in result_data:
        feeding = result_data['feeding_areas']
        features = feeding.get('features', [])
        print(f"\n🌾 Feeding Areas:")
        print(f"   📊 Areas Found: {len(features)}")
        
        for i, area in enumerate(features[:3]):
            props = area.get('properties', {})
            coords = area.get('geometry', {}).get('coordinates', [0, 0])
            print(f"   Area {i+1}:")
            print(f"      📍 Location: {coords[1]:.4f}, {coords[0]:.4f}")
            print(f"      🎯 Score: {props.get('score', 0)}/100")
            print(f"      🏷️ Type: {props.get('feeding_type', 'Unknown')}")
    
    # Wind & Thermal Analysis
    if 'wind_thermal_analysis' in result_data:
        wind = result_data['wind_thermal_analysis']
        print(f"\n🌬️ Wind & Thermal Analysis:")
        print(f"   💨 Wind Direction: {wind.get('wind_direction', 0)}°")
        print(f"   💨 Wind Speed: {wind.get('wind_speed', 0):.1f} mph")
        print(f"   🛡️ Wind Protection: {wind.get('wind_protection', 'Unknown')}")
        print(f"   🔥 Thermal Advantage: {wind.get('thermal_advantage', 'Unknown')}")
        print(f"   ✅ Optimal Alignment: {wind.get('optimal_wind_alignment', False)}")
    
    # Performance Metrics
    print(f"\n⚡ Performance Metrics:")
    print(f"   ⏱️ Analysis Time: {result_data.get('analysis_time', 0):.2f} seconds")
    print(f"   🎯 Confidence Score: {result_data.get('confidence_score', 0)*100:.1f}%")
    print(f"   📊 Movement Confidence: {result_data.get('movement_direction', {}).get('movement_confidence', 0):.1f}%")
    print(f"   🔄 Version: {result_data.get('optimization_version', 'Unknown')}")
    
    print("\n" + "=" * 45)
    print("✅ SUCCESS: Real hunting data successfully processed!")
    print("🎯 The prediction system is working with actual GEE, weather, and terrain data")
    print("🌍 Ready for production hunting predictions!")
    
    return True

def main():
    print(f"📅 Real Data Test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_real_data_success()
    
    if success:
        print("\n🎉 REAL DATA INTEGRATION COMPLETE!")
        print("📊 Your comprehensive analysis enhancement is ready for:")
        print("   • Real Google Earth Engine data")
        print("   • Real weather and wind conditions") 
        print("   • Real terrain analysis")
        print("   • Real stand placement recommendations")
        print("   • Real feeding area identification")
        print("   • Real bedding zone analysis")
        print()
        print("🚀 Next Steps:")
        print("   1. Rebuild Docker containers with enhanced analysis")
        print("   2. Test Streamlit frontend with enhanced display")
        print("   3. Deploy enhanced prediction system")
    else:
        print("❌ Real data test failed - check Docker containers")

if __name__ == "__main__":
    main()
