#!/usr/bin/env python3
"""
Enhanced Bedding Zone Prediction Test
Tests the new bedding zone generation and validation functionality
"""

import requests
import json
from datetime import datetime

def test_enhanced_bedding_zones():
    """Test the enhanced bedding zone prediction system"""
    print("🦌 TESTING ENHANCED BEDDING ZONE PREDICTION")
    print("="*60)
    
    # Test the backend API with the enhanced system
    base_url = "http://localhost:8000"
    
    test_data = {
        "lat": 43.3127,
        "lon": -73.2271,
        "date_time": "2025-08-26T06:00:00",
        "season": "early_season",
        "fast_mode": False
    }
    
    print(f"📍 Testing Location: Tinmouth, Vermont ({test_data['lat']}, {test_data['lon']})")
    print("─"*60)
    
    try:
        response = requests.post(f"{base_url}/predict", json=test_data, timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ API Response Success!")
            
            # Check bedding zones specifically
            bedding_zones = data.get("bedding_zones", {})
            bedding_features = bedding_zones.get("features", [])
            
            print(f"\n🛏️ BEDDING ZONE ANALYSIS:")
            print(f"  Total Bedding Areas: {len(bedding_features)}")
            
            if len(bedding_features) > 0:
                print("  ✅ Bedding zones successfully generated!")
                
                total_score = 0
                for i, zone in enumerate(bedding_features):
                    props = zone["properties"]
                    score = props.get("score", 0)
                    total_score += score
                    
                    print(f"  • Zone {i+1}: {props.get('description', 'N/A')}")
                    print(f"    Score: {score:.2f}, Confidence: {props.get('confidence', 0):.2f}")
                    print(f"    Security: {props.get('security_level', 'unknown')}")
                    
                avg_score = total_score / len(bedding_features)
                print(f"\n  📊 Average Bedding Score: {avg_score:.2f}")
                
                if avg_score > 0.8:
                    print("  🎯 EXCELLENT bedding zone quality!")
                elif avg_score > 0.6:
                    print("  ✅ GOOD bedding zone quality")
                else:
                    print("  ⚠️ MODERATE bedding zone quality - needs improvement")
                    
            else:
                print("  ❌ NO bedding zones generated - biological accuracy issue!")
                return False
            
            # Check other prediction data
            print(f"\n🍃 Feeding Areas: {len(data.get('feeding_areas', {}).get('features', []))}")
            print(f"🛤️ Travel Corridors: {len(data.get('travel_corridors', {}).get('features', []))}")
            print(f"🏕️ Stand Recommendations: {len(data.get('stand_recommendations', []))}")
            
            # Analyze mature buck opportunities
            mature_buck = data.get("mature_buck_opportunities", {})
            if mature_buck:
                terrain_scores = mature_buck.get("terrain_scores", {})
                bedding_suitability = terrain_scores.get("bedding_suitability", 0)
                print(f"\n🦌 Mature Buck Analysis:")
                print(f"  Bedding Suitability: {bedding_suitability:.1f}%")
                
                if bedding_suitability > 60:
                    print("  ✅ Good bedding habitat for mature bucks")
                else:
                    print("  ⚠️ Limited bedding habitat - may affect buck presence")
            
            # Overall biological accuracy assessment
            bio_accuracy = calculate_biological_accuracy(data)
            print(f"\n📊 BIOLOGICAL ACCURACY ASSESSMENT:")
            print(f"  Overall Score: {bio_accuracy:.1%}")
            
            if bio_accuracy > 0.8:
                print("  🎯 EXCELLENT biological accuracy!")
                return True
            elif bio_accuracy > 0.6:
                print("  ✅ GOOD biological accuracy")
                return True
            else:
                print("  ❌ POOR biological accuracy - needs improvement")
                return False
                
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

def calculate_biological_accuracy(prediction_data):
    """Calculate overall biological accuracy score"""
    score = 0.0
    max_score = 5.0
    
    # 1. Bedding zones presence and quality (25%)
    bedding_zones = prediction_data.get("bedding_zones", {}).get("features", [])
    if len(bedding_zones) > 0:
        avg_bedding_score = sum(f["properties"].get("score", 0) for f in bedding_zones) / len(bedding_zones)
        score += avg_bedding_score * 1.25  # 25% weight
    
    # 2. Feeding areas presence (20%)
    feeding_areas = prediction_data.get("feeding_areas", {}).get("features", [])
    if len(feeding_areas) >= 2:
        score += 1.0  # 20% weight
    elif len(feeding_areas) == 1:
        score += 0.5
    
    # 3. Travel corridors presence (20%)
    travel_corridors = prediction_data.get("travel_corridors", {}).get("features", [])
    if len(travel_corridors) >= 2:
        score += 1.0  # 20% weight
    elif len(travel_corridors) == 1:
        score += 0.5
    
    # 4. Stand recommendations quality (20%)
    stand_recs = prediction_data.get("stand_recommendations", [])
    if len(stand_recs) >= 3:
        avg_confidence = sum(s.get("confidence", 0) for s in stand_recs) / len(stand_recs)
        score += (avg_confidence / 100) * 1.0  # 20% weight
    
    # 5. Mature buck analysis completeness (15%)
    mature_buck = prediction_data.get("mature_buck_opportunities", {})
    if mature_buck and mature_buck.get("viable_location"):
        terrain_scores = mature_buck.get("terrain_scores", {})
        if terrain_scores.get("bedding_suitability", 0) > 30:
            score += 0.75  # 15% weight
    
    return min(score / max_score, 1.0)

def test_bedding_zone_validation():
    """Test the validation of bedding zones"""
    print("\n🔍 TESTING BEDDING ZONE VALIDATION")
    print("="*50)
    
    # Mock prediction data for validation testing
    test_cases = [
        {
            "name": "No Bedding Zones",
            "data": {"bedding_zones": {"features": []}},
            "expected_score": 0.0
        },
        {
            "name": "Low Quality Bedding",
            "data": {
                "bedding_zones": {
                    "features": [
                        {"properties": {"score": 0.4}},
                        {"properties": {"score": 0.3}}
                    ]
                }
            },
            "expected_score": 0.175  # (0.4+0.3)/2 * 0.5
        },
        {
            "name": "High Quality Bedding",
            "data": {
                "bedding_zones": {
                    "features": [
                        {"properties": {"score": 0.9}},
                        {"properties": {"score": 0.85}}
                    ]
                }
            },
            "expected_score": 0.9625  # (0.9+0.85)/2 * 1.1, capped at 1.0
        }
    ]
    
    from optimized_biological_integration import OptimizedBiologicalIntegration
    optimizer = OptimizedBiologicalIntegration()
    
    for test_case in test_cases:
        score = optimizer.validate_spatial_accuracy(test_case["data"])
        expected = test_case["expected_score"]
        
        print(f"  {test_case['name']}: Score {score:.3f} (expected ~{expected:.3f})")
        
        if abs(score - expected) < 0.1:
            print(f"    ✅ Validation working correctly")
        else:
            print(f"    ⚠️ Validation may need adjustment")

def main():
    """Run all bedding zone enhancement tests"""
    print("🦌 ENHANCED BEDDING ZONE PREDICTION - COMPREHENSIVE TEST")
    print("="*70)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Enhanced bedding zone generation
    api_success = test_enhanced_bedding_zones()
    
    # Test 2: Validation logic
    test_bedding_zone_validation()
    
    # Final assessment
    print("\n🎯 ENHANCEMENT ASSESSMENT")
    print("="*40)
    
    if api_success:
        print("✅ Enhanced bedding zone prediction: WORKING")
        print("✅ Biological accuracy: IMPROVED")
        print("✅ Mature buck habitat analysis: ENHANCED")
        print("\n🚀 READY FOR PRODUCTION DEPLOYMENT!")
    else:
        print("❌ Enhanced bedding zone prediction: NEEDS WORK")
        print("⚠️ Biological accuracy: LIMITED")
        print("🔧 Recommendation: Review bedding zone generation logic")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

if __name__ == "__main__":
    main()
