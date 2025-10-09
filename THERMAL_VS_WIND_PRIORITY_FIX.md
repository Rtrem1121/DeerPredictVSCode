# Thermal vs Prevailing Wind Priority - CRITICAL FIX NEEDED
**Date**: October 9, 2025, 6:00 PM  
**User Observation**: "At 6 PM at the actual location, unless there is a 20mph wind or more, right now the wind is moving west-ish [from thermal downslope, not prevailing wind]"

---

## 🎯 **The Problem:**

### **Current Logic** (Lines 1510-1530):
```python
if evening_thermal["strength"] > 0.3:  # 30% threshold
    # Use thermal + deer movement (95% or 80%)
    # Prevailing wind = 5-20%
else:  # Weak thermal
    # Use deer movement (60%) + prevailing wind (40%)
```

### **What's Wrong**:
- ❌ Only checks **thermal strength** (not wind strength!)
- ❌ On north-facing slopes (aspect 0°), thermal strength = **4%** (very weak!)
- ❌ 4% < 30% threshold → Uses **40% prevailing wind** weight
- ❌ **Ignores that prevailing wind is also weak** (< 20 mph)!

---

## 🌡️ **Biological Reality (Your Field Experience):**

### **At 6 PM (Sunset ± 20 min):**

**Thermal Drafts**:
- ✅ **ACTIVE** - Cooling air sinks downslope
- ✅ **OBSERVABLE** - You can feel wind moving "west-ish" (downslope)
- ✅ **DOMINANT** - Unless prevailing wind > 20 mph

**Prevailing Wind**:
- Current: 347° at **4.8 mph** (very light!)
- At 4.8 mph: **Negligible** compared to thermal drafts
- Only dominates at **> 20 mph** (strong sustained wind)

---

## 📊 **Wind Speed Thresholds:**

### **Thermal Dominance by Wind Speed**:

| Prevailing Wind Speed | Thermal Influence | Logic |
|-----------------------|-------------------|-------|
| 0-5 mph | **100% thermal** | No prevailing wind effect |
| 5-10 mph | **95% thermal** | Very weak prevailing wind |
| 10-15 mph | **80% thermal** | Moderate prevailing wind |
| 15-20 mph | **60% thermal** | Strong prevailing wind |
| 20+ mph | **30% thermal** | Very strong prevailing wind OVERRIDES thermals |

### **Your Current Case**:
- Wind speed: **4.8 mph**
- Thermal should be: **100% dominant**
- Current code: **60% deer movement, 40% prevailing wind** ❌

---

## 🔧 **The Fix:**

### **Add Wind Speed Check to Thermal Logic**

**Current** (Lines 1510-1530):
```python
if evening_thermal["strength"] > 0.3:  # Only checks thermal strength!
    # Use thermal-dominant logic
    wind_weight = 0.05 if evening_thermal["strength"] > 0.1 else 0.2
else:  # Weak thermal
    # Use prevailing wind (40% weight)
    evening_bearing = self._combine_bearings(
        downhill_direction,
        downwind_direction,
        0.6, 0.4  # 40% prevailing wind - WRONG when wind is weak!
    )
```

**Fixed**:
```python
# Get current wind speed from weather data
wind_speed_mph = weather_data.get('wind', {}).get('speed', 0)  # mph

# Determine if thermal or prevailing wind dominates
# Thermals dominate unless prevailing wind is STRONG (> 20 mph)
thermal_is_active = (
    evening_thermal["phase"] in ["strong_evening_downslope", "peak_evening_downslope", "post_sunset_maximum"]
    or evening_thermal["strength"] > 0.1  # Any measurable thermal
)

if thermal_is_active and wind_speed_mph < 20:  # THERMAL DOMINATES
    # Combine thermal direction with deer movement (both downhill)
    evening_bearing = self._combine_bearings(
        evening_thermal["direction"],  # Thermal flows downhill
        downhill_direction,  # Deer move downhill
        evening_thermal["strength"] * 0.6,  # Weight by thermal strength
        0.4  # Deer movement weight
    )
    
    # Wind weight based on wind SPEED, not thermal strength
    if wind_speed_mph < 5:
        wind_weight = 0.0  # No prevailing wind effect
    elif wind_speed_mph < 10:
        wind_weight = 0.05  # 5% prevailing wind
    elif wind_speed_mph < 15:
        wind_weight = 0.15  # 15% prevailing wind
    else:  # 15-20 mph
        wind_weight = 0.25  # 25% prevailing wind
    
    evening_bearing = self._combine_bearings(
        evening_bearing,
        downwind_direction,
        1.0 - wind_weight,  # Thermal + movement (75-100%)
        wind_weight         # Prevailing wind (0-25%)
    )
    logger.info(f"🌅 THERMAL DOMINANT: Bearing={evening_bearing:.0f}°, Wind speed={wind_speed_mph:.1f}mph, Wind weight={wind_weight:.0%}")
    
elif wind_speed_mph >= 20:  # STRONG PREVAILING WIND DOMINATES
    # Strong prevailing wind overrides weak thermals
    evening_bearing = self._combine_bearings(
        downhill_direction,  # Deer still move downhill
        downwind_direction,  # Strong prevailing wind
        0.4,  # 40% deer movement
        0.6   # 60% prevailing wind (STRONG wind dominates)
    )
    logger.info(f"💨 WIND DOMINANT: Bearing={evening_bearing:.0f}°, Wind speed={wind_speed_mph:.1f}mph (>20mph), Thermal overridden")
    
else:  # No thermal activity AND weak wind (midday, calm conditions)
    # Use deer movement + moderate prevailing wind influence
    wind_weight = min(0.4, wind_speed_mph / 50)  # Scale with wind speed
    evening_bearing = self._combine_bearings(
        downhill_direction,
        downwind_direction,
        1.0 - wind_weight,
        wind_weight
    )
    logger.info(f"🦌 DEER MOVEMENT: Bearing={evening_bearing:.0f}°, Wind speed={wind_speed_mph:.1f}mph, Wind weight={wind_weight:.0%}")
```

---

## 📊 **Impact on Your Cases:**

### **Case 1: Your Current 6 PM Hunt**
**Conditions**:
- Time: 6:00 PM (20 min before sunset)
- Wind: 347° at **4.8 mph** (very weak!)
- Thermal phase: `peak_evening_downslope` (95% strength on south slopes)
- Thermal phase (north slope): Weak (4% strength) BUT still active!

**Current Code**:
```
thermal_strength = 4% < 30%
→ Use prevailing wind (40% weight)
→ evening_bearing = 60% deer (0°) + 40% wind (167°) = 67° (ENE)
→ WRONG! Wind is only 4.8 mph, shouldn't have 40% influence!
```

**Fixed Code**:
```
wind_speed = 4.8 mph < 5 mph
→ Thermal dominant, wind_weight = 0% (no prevailing wind effect)
→ evening_bearing = 100% thermal + deer (both 0° downhill) = 0° (N)
→ CORRECT! Stand placed straight downhill!
```

---

### **Case 2: 6 PM with Strong North Wind**
**Conditions**:
- Time: 6:00 PM
- Wind: 347° at **25 mph** (STRONG!)
- Thermal: Downslope (trying to flow north)

**Current Code**:
```
thermal_strength = 4% < 30%
→ Use 40% prevailing wind
→ Not enough! Strong wind should be 60%+
```

**Fixed Code**:
```
wind_speed = 25 mph > 20 mph
→ WIND DOMINANT mode
→ evening_bearing = 40% deer (0°) + 60% wind (167°) = 100° (E)
→ CORRECT! Strong wind overrides thermal!
```

---

### **Case 3: Midday (No Thermal)**
**Conditions**:
- Time: 12:00 PM (midday)
- Wind: 347° at **8 mph**
- Thermal: Minimal (10% strength)

**Current Code**:
```
thermal_strength = 10% < 30%
→ Use 40% prevailing wind
→ Reasonable (no thermal to override)
```

**Fixed Code**:
```
thermal_is_active = False (midday lull)
wind_speed = 8 mph
→ DEER MOVEMENT mode
→ wind_weight = 8 / 50 = 16%
→ evening_bearing = 84% deer + 16% wind
→ SIMILAR but more nuanced!
```

---

## 🌡️ **The Wind Speed Curve:**

### **Thermal Influence vs Wind Speed** (At Sunset):

```
Thermal Dominance
    100% ┤██████████████████▓▓▓▓▓▓▒▒▒▒░░░░
         │                  
     75% ┤                  ▓▓▓▓▓▓▒▒▒▒░░░░
         │                        
     50% ┤                        ▒▒▒▒░░░░
         │                              
     25% ┤                              ░░░░
         │                                  
      0% └─────┬─────┬─────┬─────┬─────┬─────
           0-5   5-10  10-15 15-20  20+  25+
                Wind Speed (mph)

Legend:
█ = 100% thermal (no prevailing wind)
▓ = 75-95% thermal (weak prevailing wind)
▒ = 50-75% thermal (moderate prevailing wind)
░ = 25-50% thermal (strong prevailing wind)
  = 0-25% thermal (very strong wind dominates)
```

---

## 🎯 **Summary:**

### **Your Field Observation**:
✅ "At 6 PM, unless there's 20+ mph wind, thermals dominate"

### **Current Code Problem**:
❌ Only checks thermal strength (4% on north slopes = weak)
❌ Doesn't check prevailing wind strength (4.8 mph = also weak!)
❌ Gives 40% weight to 4.8 mph wind = WRONG!

### **The Fix**:
✅ Check **wind speed**, not just thermal strength
✅ Thermal dominates when wind < 20 mph (your observation!)
✅ Wind weight scales with wind speed: 0-5 mph = 0%, 20+ mph = 60%
✅ Even weak thermals (4%) override weak prevailing winds (< 5 mph)

---

## 📝 **Implementation:**

Would you like me to implement this fix? It will:

1. **Get wind speed** from weather data
2. **Check wind speed threshold** (< 20 mph = thermal dominant)
3. **Scale prevailing wind weight** by wind speed (0-60%)
4. **Log the decision** (thermal vs wind dominant)

**Result**: At 6 PM with 4.8 mph wind, stands will be placed **straight downhill** (0° north), matching your field experience that thermal drafts are flowing "west-ish" (downslope direction)! 🌡️🎯
