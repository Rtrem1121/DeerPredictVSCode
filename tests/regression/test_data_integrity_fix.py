#!/usr/bin/env python3
"""
Test Data Integrity Fix - Internal Contradictions
"""
import requests
import json

def test_data_integrity_fix():
    """Test that detailed analysis correctly reflects actual analysis performed"""
    
    url = "http://localhost:8000/analyze-prediction-detailed"
    
    payload = {
        "lat": 43.3140,
        "lon": -73.2306,
        "date_time": "2025-09-02T18:00:00",
        "time_of_day": 18,
        "season": "fall",
        "hunting_pressure": "low"
    }
    
    print("🔍 TESTING DATA INTEGRITY FIX")
    print("=" * 60)
    print("🎯 Target: Verify detailed_analysis matches actual analysis performed")
    print("🚨 Previous Issue: 'WindThermalAnalyzer: 0 locations analyzed' vs 9 actual analyses")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract main analysis data
            wind_analyses = data.get("prediction", {}).get("wind_analyses", [])
            main_wind_count = len(wind_analyses)
            
            # Extract detailed analysis data
            detailed_analysis = data.get("detailed_analysis", {})
            algorithm_analysis = detailed_analysis.get("algorithm_analysis", {})
            
            print(f"\n📊 MAIN ANALYSIS RESULTS:")
            print(f"   Wind Analyses Found: {main_wind_count}")
            print(f"   Locations Analyzed: {[a.get('location_type', 'unknown') for a in wind_analyses[:3]]}")
            
            # Check algorithm analysis
            decision_points = algorithm_analysis.get("decision_points", [])
            wind_analyzer_data = None
            
            for point in decision_points:
                if point.get("algorithm") == "WindThermalAnalyzer":
                    wind_analyzer_data = point
                    break
            
            print(f"\n🔍 DETAILED ANALYSIS CLAIMS:")
            if wind_analyzer_data:
                claimed_result = wind_analyzer_data.get("result", "No result")
                print(f"   WindThermalAnalyzer Result: {claimed_result}")
                
                # Extract the number from the result string
                try:
                    claimed_count = int(claimed_result.split()[0])
                    print(f"   Claimed Locations Analyzed: {claimed_count}")
                except:
                    claimed_count = -1
                    print(f"   Claimed Locations Analyzed: Could not parse")
            else:
                print(f"   WindThermalAnalyzer: NOT FOUND in algorithm analysis")
                claimed_count = -1
            
            # Check stand criteria
            criteria_analysis = detailed_analysis.get("criteria_analysis", {})
            stand_criteria = criteria_analysis.get("stand_criteria", {})
            wind_available = stand_criteria.get("wind_analysis_available", False)
            
            print(f"\n🎯 STAND CRITERIA CLAIMS:")
            print(f"   wind_analysis_available: {wind_available}")
            
            # Verify data integrity
            print(f"\n✅ DATA INTEGRITY VERIFICATION:")
            
            # Test 1: Main vs Detailed Analysis
            if main_wind_count > 0 and claimed_count == main_wind_count:
                print(f"   ✅ CONSISTENCY: Main analysis ({main_wind_count}) matches detailed analysis ({claimed_count})")
            elif main_wind_count > 0 and claimed_count == 0:
                print(f"   ❌ CONTRADICTION: Main analysis shows {main_wind_count} analyses, detailed claims 0")
                print(f"   🚨 DATA INTEGRITY FAILURE: Analysis performed but not recorded")
            elif main_wind_count == 0:
                print(f"   ⚠️  NO ANALYSIS: Neither main nor detailed analysis show wind data")
            else:
                print(f"   ❓ MISMATCH: Main={main_wind_count}, Detailed={claimed_count}")
            
            # Test 2: Wind Available Flag
            if main_wind_count > 0 and wind_available:
                print(f"   ✅ FLAG CORRECT: wind_analysis_available=true matches {main_wind_count} analyses")
            elif main_wind_count > 0 and not wind_available:
                print(f"   ❌ FLAG ERROR: wind_analysis_available=false but {main_wind_count} analyses exist")
            elif main_wind_count == 0 and not wind_available:
                print(f"   ✅ FLAG CORRECT: wind_analysis_available=false matches 0 analyses")
            else:
                print(f"   ❓ FLAG UNCLEAR: main={main_wind_count}, flag={wind_available}")
            
            # Test 3: Data Reliability Assessment
            if main_wind_count > 0 and claimed_count == main_wind_count and wind_available:
                print(f"\n🎯 RELIABILITY ASSESSMENT:")
                print(f"   ✅ DATA INTEGRITY: EXCELLENT")
                print(f"   ✅ INTERNAL CONSISTENCY: All systems agree")
                print(f"   ✅ HUNTER CONFIDENCE: Analysis data is trustworthy")
                print(f"   ✅ SAFETY RATING: Wind analysis reliable for hunting decisions")
            else:
                print(f"\n🚨 RELIABILITY ASSESSMENT:")
                print(f"   ❌ DATA INTEGRITY: COMPROMISED")
                print(f"   ❌ INTERNAL CONSISTENCY: Contradictory information")
                print(f"   ❌ HUNTER CONFIDENCE: Cannot trust analysis")
                print(f"   ❌ SAFETY RATING: Unreliable for hunting decisions")
            
            # Show sample wind analysis data
            if wind_analyses:
                print(f"\n🌬️ SAMPLE WIND ANALYSIS DATA:")
                for i, analysis in enumerate(wind_analyses[:2]):
                    loc_type = analysis.get('location_type', 'unknown')
                    coords = analysis.get('coordinates', [0, 0])
                    wind_data = analysis.get('wind_analysis', {})
                    approach = wind_data.get('optimal_approach_bearing', 'N/A')
                    scent = wind_data.get('scent_cone_direction', 'N/A')
                    print(f"     {i+1}. {loc_type.upper()}: {coords[0]:.4f}, {coords[1]:.4f}")
                    print(f"        Approach: {approach}°, Scent: {scent}°")
                    
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_data_integrity_fix()
