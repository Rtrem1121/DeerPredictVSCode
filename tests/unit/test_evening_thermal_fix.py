#!/usr/bin/env python3
"""
Test Evening Thermal Direction Fix
"""
import requests
import json

def test_evening_thermal_fix():
    """Test the corrected evening thermal direction logic"""
    
    url = "http://localhost:8000/analyze-prediction-detailed"
    
    # Test coordinates for Vermont terrain
    payload = {
        "lat": 43.3140,
        "lon": -73.2306,
        "date_time": "2025-09-02T18:00:00",  # 6:00 PM - evening hunt
        "time_of_day": 18,
        "season": "fall",
        "hunting_pressure": "low"
    }
    
    print("🌄 TESTING EVENING THERMAL DIRECTION FIX")
    print("=" * 60)
    print("🕕 Test Time: 6:00 PM (Hour 18) - Prime evening hunt time")
    print("🍂 Season: Fall in Vermont")
    print("📍 Terrain: Hilly terrain with thermal potential")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract thermal analysis
            thermal_analysis = data.get("prediction", {}).get("thermal_analysis", {})
            
            print(f"\n🌡️ THERMAL ANALYSIS RESULTS:")
            print(f"   Is Active: {thermal_analysis.get('is_active', 'N/A')}")
            print(f"   Direction: {thermal_analysis.get('direction', 'N/A')}")
            print(f"   Strength: {thermal_analysis.get('strength_scale', 'N/A')}/10")
            print(f"   Timing Advantage: {thermal_analysis.get('timing_advantage', 'N/A')}")
            
            # Check the physics
            direction = thermal_analysis.get('direction', 'unknown')
            is_active = thermal_analysis.get('is_active', False)
            
            print(f"\n🔬 THERMAL PHYSICS VERIFICATION:")
            print(f"   Time: 6:00 PM (Hour 18)")
            print(f"   Sun Status: Setting (slopes cooling)")
            print(f"   Expected Direction: DOWNSLOPE (air sinks as it cools)")
            print(f"   Actual Direction: {direction.upper()}")
            
            if direction == 'downslope' and is_active:
                print(f"   ✅ PHYSICS CORRECT: Cooling slopes create downslope thermal flow")
                print(f"   ✅ SCENT FLOW: Hunter scent will flow downhill - position accordingly!")
                print(f"   ✅ HUNTING STRATEGY: Stay low, deer approach from uphill")
            elif direction == 'upslope':
                print(f"   ❌ PHYSICS ERROR: Upslope thermal at 6 PM is impossible")
                print(f"   ❌ SCENT DANGER: False confidence about scent rising away")
                print(f"   ❌ HUNT FAILURE: Will position hunter incorrectly")
            elif not is_active:
                print(f"   ⚠️  THERMAL INACTIVE: No thermal wind detected")
                print(f"   📝 NOTE: Check terrain and weather conditions")
            else:
                print(f"   ❓ UNKNOWN DIRECTION: {direction}")
            
            # Show impact on hunting strategy
            print(f"\n🏹 HUNTING STRATEGY IMPLICATIONS:")
            if direction == 'downslope':
                print(f"   📍 STAND PLACEMENT: Position BELOW deer travel routes")
                print(f"   🧭 APPROACH: Come from downhill (below the deer)")
                print(f"   💨 SCENT MANAGEMENT: Your scent flows away from deer uphill")
                print(f"   🦌 DEER MOVEMENT: Expect deer to approach from uphill")
            elif direction == 'upslope':
                print(f"   ⚠️  DANGEROUS STRATEGY: Would position hunter uphill")
                print(f"   ⚠️  SCENT ISSUE: Scent would flow down onto deer")
                print(f"   ⚠️  HUNT FAILURE: Deer would smell hunter before shot opportunity")
            
            # Test multiple evening times
            print(f"\n⏰ TESTING OTHER EVENING TIMES:")
            evening_times = [17, 18, 19, 20]  # 5 PM to 8 PM
            
            for hour in evening_times:
                test_payload = payload.copy()
                test_payload["time_of_day"] = hour
                test_payload["date_time"] = f"2025-09-02T{hour:02d}:00:00"
                
                try:
                    test_response = requests.post(url, json=test_payload, timeout=15)
                    if test_response.status_code == 200:
                        test_data = test_response.json()
                        test_thermal = test_data.get("prediction", {}).get("thermal_analysis", {})
                        test_direction = test_thermal.get('direction', 'unknown')
                        test_active = test_thermal.get('is_active', False)
                        
                        status = "✅ CORRECT" if test_direction == 'downslope' and test_active else "❌ WRONG"
                        print(f"     {hour}:00 ({hour:2d}h): {test_direction.upper()} - {status}")
                    else:
                        print(f"     {hour}:00 ({hour:2d}h): API Error")
                except:
                    print(f"     {hour}:00 ({hour:2d}h): Timeout")
                    
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_evening_thermal_fix()
