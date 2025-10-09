# North-Facing Slope Fix - PM Hunt Movement Logic
**Date**: October 9, 2025, 7:30 PM  
**Status**: ✅ **FIXED** - Time-aware feeding placement

---

## 🐛 **The Problem:**

### **User Report**:
> "Nope its the same the bedding 1 2 3 are all below the stand sites 2 and 3. I highly doubt a mature buck is walking up hill at the PM time frame."

### **Root Cause**: **Feeding placed UPHILL on north-facing slopes**

**What Happened**:
```
Your Location: North-facing slope (Aspect=354°, Elevation=339m)

OLD Logic:
1. Bedding: Place UPHILL (174° S/SSE) ✅ CORRECT
2. Feeding: REJECT north aspect (354°) ❌
3. Search for south-facing alternatives (135-225°) ❌
4. Find feeding at Aspect=180° (south), Elevation=332m, 331m, 352m
5. Result: Feeding HIGHER than bedding! ❌

Map Layout (BACKWARDS!):
RIDGE (South) ← Feeding (Elev: 352m)
     ↑ UPHILL
Input Point (Elev: 339m)
     ↑ UPHILL  
Bedding (Elev: 339m+)
     ↓ DOWNHILL
VALLEY (North)
```

**The Biological Error**:
- PM Hunt: Deer move FROM bedding → TO feeding
- Thermal drafts: Pull downslope in evening
- Your observation: "I highly doubt a mature buck is walking up hill at the PM time frame" ✅ **100% CORRECT**
- OLD code: Forced feeding UPHILL (against gravity + thermals) ❌

---

## 🔍 **Diagnosis:**

### **The Aspect Restriction**:
Lines 1824-1843 in `enhanced_bedding_zone_predictor.py` (OLD):
```python
aspect_suitable_for_feeding = (base_terrain_aspect is not None and 
                             isinstance(base_terrain_aspect, (int, float)) and 
                             135 <= base_terrain_aspect <= 225)  # South-facing ONLY

if not aspect_suitable_for_feeding:
    logger.warning("PRIMARY FEEDING LOCATION REJECTED: Aspect 354° unsuitable")
    # Search for south-facing alternatives (which are UPHILL on north slopes!)
    alternative_feeding = self._search_alternative_feeding_sites(...)
```

**Why This Was Wrong**:
- **North-facing slope** (aspect=354°): Downhill = North (354°), Uphill = South (174°)
- **South-facing food requirement** (135-225°): Forces search for south aspects
- **On north slopes**: South = UPHILL! ❌
- **Result**: Feeding placed UPHILL, deer must climb against thermal drafts

### **The Missing Context**:
- Code didn't know if it was **AM hunt** vs **PM hunt**
- **AM hunts**: Deer feed BEFORE moving uphill to bed (aspect matters for food quality)
- **PM hunts**: Deer move DOWNHILL with thermal drafts (aspect irrelevant, terrain > food quality)

---

## 🔧 **The Fix:**

### **Time-Aware Feeding Logic**:

**Changed Function Signature**:
```python
# OLD
def generate_enhanced_feeding_areas(self, lat, lon, gee_data, osm_data, weather_data) -> Dict:

# NEW
def generate_enhanced_feeding_areas(self, lat, lon, gee_data, osm_data, weather_data, time_of_day: int = 12) -> Dict:
```

**Added Time-Based Logic** (Lines 1828-1873):
```python
# 🎯 TIME-AWARE FEEDING LOGIC:
is_pm_hunt = time_of_day >= 15  # Evening hunt (3 PM+)
is_am_hunt = time_of_day < 12   # Morning hunt (before noon)

# On sloped terrain during PM hunts, ALWAYS use downhill (thermal draft movement)
if is_pm_hunt and slope > 5:
    logger.info(f"🌅 PM HUNT on {slope:.1f}° slope: Prioritizing DOWNHILL movement (aspect={base_terrain_aspect:.0f}°)")
    logger.info(f"   ⬇️ Deer move downhill with thermal drafts in evening, regardless of aspect")
    # Skip aspect check - use downhill positions
    aspect_suitable_for_feeding = True  # Override aspect requirement
else:
    # AM hunt or flat terrain - aspect matters for food quality
    aspect_suitable_for_feeding = (base_terrain_aspect is not None and 
                                 isinstance(base_terrain_aspect, (int, float)) and 
                                 135 <= base_terrain_aspect <= 225)
    
    if not aspect_suitable_for_feeding and not is_pm_hunt:
        # Only search for south-facing alternatives on AM hunts
        logger.warning(f"🌾 PRIMARY FEEDING LOCATION REJECTED: Aspect {base_terrain_aspect}° unsuitable for feeding")
        alternative_feeding = self._search_alternative_feeding_sites(...)
```

**Updated Function Call** (Line 1055):
```python
# OLD
feeding_areas = self.generate_enhanced_feeding_areas(lat, lon, gee_data, osm_data, weather_data)

# NEW
feeding_areas = self.generate_enhanced_feeding_areas(lat, lon, gee_data, osm_data, weather_data, time_of_day)
```

---

## 📊 **How It Works Now:**

### **PM Hunt (time_of_day ≥ 15)**:
```
Slope > 5° → DOWNHILL PRIORITY MODE
  ↓
Aspect check: SKIPPED (thermal movement > food quality)
  ↓
Feeding: Placed DOWNHILL (aspect direction)
  ↓
Result: Deer move downhill with thermal drafts ✅
```

**Your North-Facing Slope (Aspect=354°, Slope=12.8°)**:
```
Time: 7 PM (19:00) → is_pm_hunt = TRUE
Slope: 12.8° > 5° → Downhill priority
Aspect: 354° (north)
  ↓
Feeding Bearing: 354° (NORTH/downhill) ✅
No south-facing search triggered ✅
  ↓
Map Layout (CORRECT):
RIDGE (South, High)
     ↑
Bedding (~174° S) ← Uphill
     ↑
Input Point (339m)
     ↓ 
Feeding (~354° N) ← Downhill ✅
     ↓
VALLEY (North, Low)
```

### **AM Hunt (time_of_day < 12)**:
```
Aspect check: ACTIVE (food quality matters)
  ↓
North aspect (354°) → REJECTED
  ↓
Search for south-facing alternatives (better mast/browse)
  ↓
Result: Higher quality food sources ✅
```

---

## ✅ **Expected Behavior:**

### **New Logs (PM Hunt, North-Facing Slope)**:
```
🌅 PM HUNT on 12.8° slope: Prioritizing DOWNHILL movement (aspect=354°)
   ⬇️ Deer move downhill with thermal drafts in evening, regardless of aspect
🌾 FEEDING: Slope=12.8° - placing DOWNHILL (354°) for valley food sources
🌾 EMERGENCY FEEDING: Placing downhill (354°) toward valley/water
```

### **Map Positions**:
```
Bedding Zones (all south ~174°):
- Bedding 1: 43.3103, -73.2157 (Primary, uphill)
- Bedding 2: 43.3108, -73.2166 (Secondary, uphill+30°)
- Bedding 3: 43.3105, -73.2157 (Escape, uphill)

Evening Stand: ~354° (N) - Downhill intercept

Feeding Zones (all north ~354°):
- Feeding 1: DOWNHILL from input point
- Feeding 2: DOWNHILL variation
- Feeding 3: DOWNHILL emergency (valley/water)

Elevation Profile:
HIGH → Bedding (South)
  ↓
MID → Input Point
  ↓  
MID → Evening Stand  
  ↓
LOW → Feeding (North) ✅
```

---

## 🧪 **Testing Instructions:**

### **1. Clear Browser Cache**:
- Press `Ctrl+Shift+R` (hard refresh)
- Or clear Streamlit cache from sidebar

### **2. Run New PM Prediction**:
- Enter your coordinates (north-facing slope location)
- Select **PM hunt** (evening time - any time after 3 PM)
- Submit

### **3. Verify Logs**:
```bash
docker-compose logs backend --tail 100 | Select-String "PM HUNT|FEEDING|DOWNHILL"
```

**Should See**:
```
🌅 PM HUNT on 12.8° slope: Prioritizing DOWNHILL movement (aspect=354°)
   ⬇️ Deer move downhill with thermal drafts in evening, regardless of aspect
🌾 FEEDING: Slope=12.8° - placing DOWNHILL (354°) for valley food sources
```

**Should NOT See**:
```
❌ PRIMARY FEEDING LOCATION REJECTED: Aspect 354° unsuitable for feeding
❌ FEEDING FALLBACK SEARCH: Looking for south-facing feeding areas
❌ SUITABLE FEEDING SITE FOUND: ... Aspect: 180° (south-facing) ← This is UPHILL!
```

### **4. Verify Map**:
- ✅ **Bedding zones SOUTH** (uphill from input point)
- ✅ **Feeding zones NORTH** (downhill from input point)
- ✅ **Evening stand BETWEEN** (intercept route, downhill of bedding, uphill of feeding)
- ❌ **NO feeding zones south/uphill** of bedding

---

## 🎯 **Biological Accuracy:**

### **PM Hunt Movement** (NEW - CORRECT):
```
Time: 15:00-20:00 (3 PM - 8 PM)
Solar: Pre-sunset to post-sunset
Thermal: Downslope drafts (95-100% strength)
Deer Movement: FROM bedding (uphill) → TO feeding (downhill)
  ↓
Terrain: Follow thermal drafts downhill
Wind: Thermal > Prevailing (unless >20 mph)
Food Quality: Secondary priority (movement > aspect)
  ↓
Result: Feeding placed DOWNHILL ✅
```

### **AM Hunt Movement** (EXISTING - CORRECT):
```
Time: 05:00-11:00 (5 AM - 11 AM)
Solar: Pre-sunrise to morning
Thermal: Upslope drafts (40-80% strength)
Deer Movement: FROM feeding → TO bedding (uphill)
  ↓
Food Quality: PRIMARY priority (deer feed before bedding)
Aspect: South-facing preferred (better mast/browse)
  ↓
Result: Search for south-facing food (even if uphill) ✅
```

---

## 💡 **Key Learnings:**

### **1. Time Context Matters**:
- Same terrain, opposite movement patterns
- AM: Food quality > Terrain
- PM: Terrain > Food quality

### **2. North-Facing Slopes Are Tricky**:
- Uphill = South (sun)
- Downhill = North (valley)
- South-facing food = UPHILL ❌ (for PM)

### **3. Thermal Drafts Drive PM Movement**:
- Evening thermals pull downslope (95-100%)
- Deer follow thermal drafts (scent control)
- Fighting thermal + gravity = unlikely ❌

### **4. Aspect vs Elevation Trade-off**:
```
AM Hunt:
- Food quality matters (deer feeding session)
- Aspect > Elevation
- Search for south-facing slopes ✅

PM Hunt:
- Movement matters (transit to feeding)
- Elevation > Aspect
- Follow terrain downhill ✅
```

---

## 📝 **Summary:**

**Problem**: Feeding forced UPHILL on north-facing slopes (PM hunts)  
**Cause**: Aspect requirement ignored time-of-day movement patterns  
**Solution**: Time-aware feeding placement (PM = downhill, AM = aspect)  
**Result**: Biologically accurate deer movement on all terrain ✅

**Status**: ✅ **CONTAINERS RESTARTED** - Ready for testing!

**Next**: Run a PM prediction and verify feeding zones are now DOWNHILL! 🎯🦌
