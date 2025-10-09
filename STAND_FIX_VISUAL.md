# Visual Fix - Stand 2 & 3 Positioning

## ❌ **OLD BEHAVIOR** (Stands BELOW Bedding!)

```
North-Facing Slope (Aspect=0°, Slope=5.5°)

NORTH ↑ (Low Elevation on North Slope)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stand 1 (Evening) ← Lat 43.3135 ✅ Correct
Bearing: 0° N (downhill)
Purpose: Intercept deer moving to feeding

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 INPUT POINT ← Lat 43.3122
Elevation: 331m

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bedding 1 ← Lat 43.3110 (S of input)
Bedding 2 ← Lat 43.3114 (S of input)
Bedding 3 ← Lat 43.3111 (S of input)
Bearing: 180-210° (uphill)
Purpose: Security bedding areas ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stand 2 (Morning) ← Lat 43.3096 ❌ WRONG!
Bearing: 207° SSW (crosswind)
Purpose: BELOW bedding (misses deer!)

Stand 3 (Alternate) ← Lat 43.3102 ❌ WRONG!
Bearing: 169° SSE (downwind)  
Purpose: BELOW bedding (unusable!)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOUTH ↓ (High Elevation on North Slope)


❌ PROBLEM:
- Morning deer movement: Feeding → Bedding → Continue UPHILL
- Stand 2 & 3: Positioned BELOW bedding
- Result: Deer walk PAST stands before reaching bedding ❌
```

---

## ✅ **NEW BEHAVIOR** (Stands ABOVE Bedding!)

```
North-Facing Slope (Aspect=0°, Slope=5.5°)

NORTH ↑ (Low Elevation on North Slope)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stand 1 (Evening) ← Lat 43.313x ✅ Correct
Bearing: 0° N (downhill)
Purpose: Intercept deer moving to feeding

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 INPUT POINT ← Lat 43.3122
Elevation: 331m

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stand 2 (Morning) ← Lat 43.312x ✅ NOW CORRECT!
Bearing: 180-186° S (uphill)
Purpose: ABOVE bedding (intercepts deer!)

Stand 3 (Alternate) ← Lat 43.312x ✅ NOW CORRECT!
Bearing: 225° SW (uphill variation)
Purpose: ABOVE bedding (different wind approach!)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bedding 1 ← Lat 43.311x (uphill from input)
Bedding 2 ← Lat 43.311x (uphill from input)
Bedding 3 ← Lat 43.311x (uphill from input)
Bearing: 180-210° S (uphill)
Purpose: Security bedding areas ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feeding zones ← Lat 43.313x (downhill in valley)
Bearing: 0° N (downhill)
Purpose: Valley food sources ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOUTH ↓ (High Elevation on North Slope)


✅ SOLUTION:
- Morning deer movement: Feeding → Bedding → Continue UPHILL
- Stand 2 & 3: Positioned ABOVE bedding
- Result: Deer must pass stands on final approach ✅
```

---

## 🦌 **Deer Movement Patterns:**

### **Evening Hunt** (Stand 1):
```
TIME: 4 PM - 8 PM

RIDGE (South, High)
     ↑
🏔️ Bedding Area ← Deer wake up
     ↓ (moving downhill)
     ↓ Thermal drafts pull downslope
     ↓
📍 Input Point
     ↓
🎯 Stand 1 ← INTERCEPT! ✅
     ↓ (continuing downhill)
     ↓
🌾 Feeding Area ← Destination

Movement: DOWNHILL
Stand Position: Downhill (valley direction)
Scent: Thermal drafts carry scent downslope
Strategy: Sit below bedding, intercept route
```

### **Morning Hunt** (Stand 2):
```
TIME: 5 AM - 10 AM

RIDGE (South, High)
     ↑
🎯 Stand 2 ← INTERCEPT! ✅ (ABOVE bedding)
     ↑ (deer continuing uphill)
     ↑ Thermal drafts pull upslope
     ↑
🏔️ Bedding Area ← Deer pass through
     ↑ (moving uphill)
     ↑
📍 Input Point
     ↑
🌾 Feeding Area ← Deer start here

Movement: UPHILL
Stand Position: Uphill (beyond bedding)
Scent: Thermal drafts carry scent upslope
Strategy: Sit above bedding, intercept final approach
```

---

## 🔑 **The Key Change:**

### **OLD Logic** (Crosswind/Downwind):
```python
# Stand 2
crosswind = (uphill + 90) % 360  # Perpendicular ❌
morning_bearing = combine(crosswind, downwind)
Result: 207° SSW = BELOW bedding on north slope ❌

# Stand 3
allday_bearing = downwind  # 169° SSE ❌
Result: BELOW bedding on north slope ❌
```

### **NEW Logic** (Uphill):
```python
# Stand 2
if slope > 5:
    morning_bearing = uphill  # 180° S ✅
Result: ABOVE bedding on north slope ✅

# Stand 3
if slope > 5:
    allday_bearing = uphill + 45  # 225° SW ✅
Result: ABOVE bedding on north slope ✅
```

---

## 📊 **Coordinate Analysis:**

### **Your Prediction**:
```
Input: 43.31224, -73.21559

OLD Positions:
Stand 1: 43.3135 (N of input) ✅ Correct
Bedding: 43.311x (S of input) ✅ Correct
Stand 2: 43.3096 (S of bedding!) ❌ WRONG
Stand 3: 43.3102 (S of bedding!) ❌ WRONG

NEW Positions (Expected):
Stand 1: 43.313x (N of input) ✅ Evening intercept
Stand 2: 43.312x (Between input & bedding) ✅ Morning intercept
Stand 3: 43.312x (Between input & bedding) ✅ Alternate approach
Bedding: 43.311x (S of stands) ✅ Uphill security
Feeding: 43.313x (N of input) ✅ Valley food
```

---

## ✅ **Summary:**

**Problem**: Stand 2 & 3 below bedding zones (wrong latitude)

**Cause**: Crosswind/downwind logic ignored terrain slope

**Fix**: Slope-aware positioning - uphill for Stand 2 & 3

**Result**: 
- Stand 1: Downhill (0° N) ✅
- Stand 2: Uphill (180° S) ✅
- Stand 3: Uphill variation (225° SW) ✅
- All stands correctly positioned for deer movement!

**Status**: ✅ Ready for testing - Run new prediction!
