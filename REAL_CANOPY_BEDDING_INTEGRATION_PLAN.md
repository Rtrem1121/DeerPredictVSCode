# 🌲 **REAL GEE CANOPY + BEDDING ZONE INTEGRATION PLAN**

## 📋 **Implementation Overview**

**Goal**: Integrate real satellite-derived canopy coverage (Sentinel-2/Landsat) into bedding zone predictions with 1000-yard (914m) search radius.

**Expected Impact**:
- Bedding accuracy: 65% → 85%+ (**+20%**)
- Stand placement: 70% → 90%+ (**+20%**)
- Overall confidence: +15%

---

## 🎯 **Phase 1: GEE Canopy Coverage Extraction** ✅ COMPLETE

### **Files Modified**:
- `backend/vegetation_analyzer.py`

### **Features Added**:
1. **`_analyze_canopy_coverage()`** - Main canopy analysis method
   - Center coordinates + 1000-yard radius (914m)
   - Returns canopy percentage (0-1), spatial grid, thermal cover type
   
2. **`_get_sentinel2_canopy()`** - High-resolution canopy (10m)
   - Sentinel-2 Surface Reflectance imagery
   - NDVI-based canopy detection (NDVI > 0.4 = canopy)
   - 30x30 spatial grid for bedding zone search
   
3. **`_get_landsat8_canopy()`** - Fallback canopy (30m)
   - Landsat 8 Collection 2 imagery
   - Extended 6-month search window
   - Same 30x30 grid structure
   
4. **`_create_canopy_grid()`** - Spatial grid generation
   - 30x30 grid covering 1000-yard radius
   - Batch sampling for efficiency
   - Scipy interpolation for smooth coverage
   
5. **`_analyze_thermal_cover()`** - Conifer vs Hardwood detection
   - NLCD Land Cover classification
   - 41 = Deciduous (hardwood), 42 = Evergreen (conifer), 43 = Mixed
   - Critical for winter bedding/thermal yards
   
6. **`_fallback_canopy_coverage()`** - Graceful degradation
   - Vermont-specific defaults (65% canopy)
   - Uniform grid when satellite unavailable

### **Data Flow**:
```
analyze_hunting_area()
  ↓
_analyze_canopy_coverage(lat, lon, radius_m=914)
  ↓
Try: _get_sentinel2_canopy() [10m resolution]
  ↓ (if fails)
Try: _get_landsat8_canopy() [30m resolution]
  ↓ (if fails)
Use: _fallback_canopy_coverage() [Vermont defaults]
  ↓
Returns: {
  canopy_coverage: 0.78,
  canopy_grid: [[0.85, 0.82, ...], ...],  # 30x30
  grid_coordinates: {lat: [...], lon: [...]},
  thermal_cover_type: 'mixed',
  conifer_percentage: 0.35,
  data_source: 'sentinel2'
}
```

---

## 🎯 **Phase 2: Bedding Zone Integration** (NEXT)

### **Files to Modify**:
1. `enhanced_bedding_zone_predictor.py`
2. `backend/services/prediction_service.py`

### **Key Changes**:

#### **A. Update `get_dynamic_gee_data_enhanced()` Method**

**Current**: Gets canopy from generic `get_dynamic_gee_data()` (often returns 0)

**New**: Extract canopy from VegetationAnalyzer

```python
def get_dynamic_gee_data_enhanced(self, lat: float, lon: float, 
                                 vegetation_data: Optional[Dict] = None,
                                 max_retries: int = 5) -> Dict:
    """Enhanced GEE data with REAL canopy coverage from vegetation analyzer"""
    gee_data = self.get_dynamic_gee_data(lat, lon, max_retries)
    
    # Add elevation, slope, aspect
    elevation_data = self.get_elevation_data(lat, lon)
    gee_data.update(elevation_data)
    
    # 🆕 REAL CANOPY INTEGRATION
    if vegetation_data and 'canopy_coverage_analysis' in vegetation_data:
        canopy_analysis = vegetation_data['canopy_coverage_analysis']
        
        # Extract real satellite canopy
        real_canopy = canopy_analysis.get('canopy_coverage', gee_data.get('canopy_coverage', 0))
        
        # Override GEE canopy with REAL satellite data
        gee_data['canopy_coverage'] = real_canopy
        gee_data['canopy_grid'] = canopy_analysis.get('canopy_grid', [])
        gee_data['thermal_cover_type'] = canopy_analysis.get('thermal_cover_type', 'mixed')
        gee_data['conifer_percentage'] = canopy_analysis.get('conifer_percentage', 0.3)
        gee_data['canopy_data_source'] = canopy_analysis.get('data_source', 'fallback')
        
        # Log real vs estimated
        old_canopy = gee_data.get('canopy_coverage_old', 0)
        logger.info(f"🌲 CANOPY UPGRADE: {old_canopy:.1%} (estimated) → "
                   f"{real_canopy:.1%} (satellite: {gee_data['canopy_data_source']})")
        
        # Flag if using fallback
        if canopy_analysis.get('fallback'):
            logger.warning("⚠️ Canopy using FALLBACK mode (no satellite data)")
    else:
        logger.warning("⚠️ No vegetation analysis provided, using estimated canopy")
    
    # Slope validation (existing code)
    if gee_data.get("slope", 0) > 45:
        # ... Vermont terrain correction
        
    return gee_data
```

#### **B. Update `run_enhanced_biological_analysis()` Method**

**Current**: Calls `get_dynamic_gee_data_enhanced(lat, lon)` without vegetation data

**New**: Get vegetation analysis FIRST, pass to GEE data extraction

```python
def run_enhanced_biological_analysis(self, lat: float, lon: float, time_of_day: int,
                                    season: str, hunting_pressure: str,
                                    target_datetime: Optional[datetime] = None) -> Dict:
    """Enhanced biological analysis with REAL canopy coverage"""
    start_time = time.time()
    
    # 🆕 GET VEGETATION ANALYSIS FIRST (includes real canopy!)
    vegetation_data = None
    try:
        from backend.vegetation_analyzer import VegetationAnalyzer
        
        analyzer = VegetationAnalyzer()
        if analyzer.initialize():
            vegetation_data = analyzer.analyze_hunting_area(
                lat, lon, 
                radius_km=0.914,  # 1000 yards = 914m = 0.914km
                season=season
            )
            logger.info("✅ Vegetation analysis complete (includes real canopy coverage)")
        else:
            logger.warning("⚠️ VegetationAnalyzer initialization failed")
    except Exception as e:
        logger.error(f"Vegetation analysis failed: {e}")
    
    # Get enhanced GEE data with REAL canopy from vegetation analysis
    gee_data = self.get_dynamic_gee_data_enhanced(lat, lon, vegetation_data=vegetation_data)
    osm_data = self.get_osm_road_proximity(lat, lon)
    weather_data = self.get_enhanced_weather_with_trends(lat, lon, target_datetime)
    
    # Generate enhanced bedding zones (now using REAL canopy!)
    bedding_zones = self.generate_enhanced_bedding_zones(lat, lon, gee_data, osm_data, weather_data)
    
    # ... rest of analysis
```

#### **C. Enhanced Bedding Zone Search with Canopy Grid**

**Current**: Single-point canopy check

**New**: Search 30x30 canopy grid for optimal bedding locations

```python
def generate_enhanced_bedding_zones(self, lat: float, lon: float, gee_data: Dict, 
                                   osm_data: Dict, weather_data: Dict) -> Dict:
    """Generate bedding zones using REAL canopy grid search"""
    
    # Check if we have real canopy grid
    canopy_grid = gee_data.get('canopy_grid', [])
    
    if canopy_grid:
        # 🆕 GRID-BASED SEARCH (1000-yard radius)
        logger.info(f"🔍 Searching {len(canopy_grid)}x{len(canopy_grid[0])} canopy grid for bedding zones")
        
        # Find cells with >60% canopy
        high_canopy_cells = []
        grid_size = len(canopy_grid)
        
        for i in range(grid_size):
            for j in range(grid_size):
                canopy_val = canopy_grid[i][j]
                if canopy_val > 0.6:  # Min bedding canopy threshold
                    high_canopy_cells.append((i, j, canopy_val))
        
        logger.info(f"✅ Found {len(high_canopy_cells)} high-canopy cells (>60%)")
        
        # Sort by canopy coverage (best first)
        high_canopy_cells.sort(key=lambda x: x[2], reverse=True)
        
        # Generate bedding zones at top canopy locations
        bedding_zones = []
        for idx, (i, j, canopy_val) in enumerate(high_canopy_cells[:5]):  # Top 5
            # Calculate lat/lon for this grid cell
            grid_coords = gee_data.get('grid_coordinates', {})
            cell_idx = i * grid_size + j
            
            if cell_idx < len(grid_coords.get('lat', [])):
                zone_lat = grid_coords['lat'][cell_idx]
                zone_lon = grid_coords['lon'][cell_idx]
                
                # Create bedding zone with REAL canopy
                bedding_zones.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [zone_lon, zone_lat]},
                    "properties": {
                        "id": f"bedding_{idx}",
                        "type": "bedding",
                        "score": canopy_val * 0.95,  # Canopy-based scoring
                        "canopy_coverage": canopy_val,
                        "canopy_source": "real_satellite",
                        "grid_position": {"row": i, "col": j}
                    }
                })
        
        logger.info(f"✅ Generated {len(bedding_zones)} bedding zones from canopy grid")
        return {"type": "FeatureCollection", "features": bedding_zones}
    
    else:
        # Fallback to existing single-point method
        logger.warning("⚠️ No canopy grid available, using single-point method")
        # ... existing code
```

---

## 🎯 **Phase 3: Validation & Testing**

### **Test Script**: `test_real_canopy_bedding.py`

```python
#!/usr/bin/env python3
"""Test real GEE canopy integration with bedding zones"""

import sys
sys.path.insert(0, 'backend')

from vegetation_analyzer import VegetationAnalyzer
from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor

# Test Vermont location
LAT = 43.33150
LON = -73.23574

print("=" * 60)
print("REAL CANOPY + BEDDING ZONE INTEGRATION TEST")
print("=" * 60)

# Phase 1: Get real canopy coverage
print("\n1️⃣ PHASE 1: Real Canopy Coverage")
analyzer = VegetationAnalyzer()
analyzer.initialize()

vegetation_data = analyzer.analyze_hunting_area(
    LAT, LON, 
    radius_km=0.914,  # 1000 yards
    season='early_season'
)

canopy_analysis = vegetation_data.get('canopy_coverage_analysis', {})
print(f"✅ Canopy Coverage: {canopy_analysis['canopy_coverage']:.1%}")
print(f"✅ Data Source: {canopy_analysis['data_source']}")
print(f"✅ Thermal Cover: {canopy_analysis['thermal_cover_type']}")
print(f"✅ Conifer: {canopy_analysis['conifer_percentage']:.1%}")
print(f"✅ Grid Size: {len(canopy_analysis['canopy_grid'])}x{len(canopy_analysis['canopy_grid'][0])}")

# Phase 2: Generate bedding zones with real canopy
print("\n2️⃣ PHASE 2: Bedding Zones with Real Canopy")
predictor = EnhancedBeddingZonePredictor()

result = predictor.run_enhanced_biological_analysis(
    LAT, LON,
    time_of_day=6,
    season='early_season',
    hunting_pressure='low'
)

gee_data = result['gee_data']
bedding_zones = result['bedding_zones']

print(f"✅ GEE Canopy: {gee_data['canopy_coverage']:.1%}")
print(f"✅ Bedding Zones: {len(bedding_zones['features'])}")
print(f"✅ Confidence: {result['confidence_score']:.2f}")

# Phase 3: Validation
print("\n3️⃣ PHASE 3: Validation")

# Check if canopy is real (not fallback)
if canopy_analysis.get('fallback'):
    print("⚠️ WARNING: Using fallback canopy (no satellite data)")
else:
    print(f"✅ REAL SATELLITE DATA: {canopy_analysis['data_source']}")

# Check bedding zones
if bedding_zones['features']:
    for i, zone in enumerate(bedding_zones['features'][:3]):
        props = zone['properties']
        print(f"\n  Bedding Zone {i+1}:")
        print(f"    Canopy: {props.get('canopy_coverage', 0):.1%}")
        print(f"    Score: {props.get('score', 0):.2f}")
        print(f"    Source: {props.get('canopy_source', 'unknown')}")
else:
    print("❌ NO BEDDING ZONES GENERATED")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
```

### **Expected Results**:

**Before** (Estimated Canopy):
```
Canopy Coverage: 60% (estimated)
Bedding Zones: 1-2 (low confidence)
Confidence: 0.65
```

**After** (Real Satellite Canopy):
```
Canopy Coverage: 78% (sentinel2)
Bedding Zones: 4-5 (high confidence)
Confidence: 0.85
Thermal Cover: mixed (35% conifer)
Grid Search: 30x30 cells analyzed
```

---

## 📊 **Success Criteria**

| Metric | Current | Target | Test Method |
|--------|---------|--------|-------------|
| **Canopy Data Source** | Estimated (fallback) | Sentinel-2/Landsat | Check `data_source` field |
| **Canopy Accuracy** | ±20% error | ±5% error | Compare with ground truth |
| **Bedding Zones Generated** | 1-2 zones | 4-5 zones | Count features |
| **Bedding Confidence** | 0.65 | 0.85+ | Check confidence_score |
| **Grid Search** | None | 30x30 cells | Check canopy_grid |
| **Thermal Cover Detection** | None | Conifer % | Check thermal_cover_type |

---

## 🚀 **Implementation Status**

- ✅ Phase 1: GEE Canopy Extraction (COMPLETE)
  - `vegetation_analyzer.py` updated
  - Sentinel-2 + Landsat 8 support
  - 30x30 grid generation
  - Thermal cover detection
  
- 🔄 Phase 2: Bedding Integration (IN PROGRESS)
  - Update `enhanced_bedding_zone_predictor.py`
  - Grid-based bedding zone search
  - Real canopy validation
  
- ⏳ Phase 3: Validation (PENDING)
  - Create test script
  - Vermont location validation
  - Compare before/after

---

## 📝 **Next Steps**

1. ✅ Implement Phase 1 (Canopy Extraction) - **DONE**
2. ⏭️ Implement Phase 2 (Bedding Integration) - **NEXT**
3. Create validation test script
4. Run test at Vermont location (43.33°N, -73.23°W)
5. Compare with previous bedding predictions
6. Document improvements
7. Commit and push to GitHub

---

**Date**: October 2, 2025  
**Status**: Phase 1 Complete, Phase 2 Ready to Implement  
**Expected Completion**: Phase 2 + 3 in ~30 minutes
