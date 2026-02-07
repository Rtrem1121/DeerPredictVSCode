# Max Accuracy Pipeline — GEE/Wind Data Access

This pipeline does **not** call GEE or wind directly. It relies on the same core services used by the hotspot analyzer.

## GEE (Vegetation + Canopy)
Call path used by hotspot analyzer:
- Hotspot job calls `PredictionService.predict(...)`
- `PredictionService` calls `EnhancedBeddingZonePredictor.run_enhanced_biological_analysis(...)`
- That function initializes `VegetationAnalyzer` and calls:
  - `VegetationAnalyzer.analyze_hunting_area(...)`
  - then merges data into `get_dynamic_gee_data_enhanced(...)`

Key locations:
- `backend/services/hotspot_job_service.py` → `PredictionService.predict(...)`
- `backend/services/prediction_service.py`
- `enhanced_bedding_zone_predictor.py` → `run_enhanced_biological_analysis(...)` → `get_dynamic_gee_data_enhanced(...)`

## Wind/Thermals
Call path used by hotspot analyzer:
- `run_enhanced_biological_analysis(...)` calls:
  - `get_enhanced_weather_with_trends(...)`
  - `get_wind_thermal_analysis(...)`

Key locations:
- `backend/services/prediction_service.py`
- `enhanced_bedding_zone_predictor.py`

## Usage in max-accuracy
The max-accuracy pipeline uses **LiDAR + behavior + optional GEE** (`backend/max_accuracy/gee.py`) and **optional wind offsets** (`backend/max_accuracy/wind.py`).
- To use the shared hotspot-style GEE + wind path, run the standard hotspot analyzer, which already routes through `PredictionService`.
