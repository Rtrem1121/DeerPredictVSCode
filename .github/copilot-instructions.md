# Copilot Instructions (deer_pred_app)

## Big picture architecture
- Backend is FastAPI (`backend/main.py`) with routers (notably `backend/routers/prediction_router.py`) calling service-layer logic.
- Max-accuracy stand pipeline lives in `backend/max_accuracy/` and is exposed via `backend/routers/max_accuracy_router.py`.
- Services are wired through a lightweight DI container (`backend/services/service_container.py`) for terrain, weather, scouting, async HTTP, Redis cache, and async prediction.
- Prediction pipeline always runs through `backend/services/prediction_service.py` using `EnhancedBeddingZonePredictor` (`enhanced_bedding_zone_predictor.py`) and `convert_numpy_types` before JSON return.
- Data flow: LiDAR terrain scoring → declustering/shortlist → GEE canopy/NDVI refinement → bedding + stand logic → frontend display (see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)).
- Max-accuracy flow: dense LiDAR grid → terrain metrics (bench/saddle/corridor) → optional GEE canopy/NDVI → behavior blend → quadrant diversity → wind offsets.
- Frontend is Streamlit (`frontend/app.py`) calling `/predict` and `/analyze-prediction-detailed`, with response validation in `frontend/enhanced_data_validation.py`.
- Configuration is YAML-based: `config/defaults.yaml` + `config/{development,testing,production}.yaml`, loaded/validated by `backend/config_manager.py` (optional hot-reload via watchdog).

## Key workflows (actual commands)
- Local backend: `python backend/main.py`
- Local frontend: `streamlit run frontend/app.py`
- Docker stack: `docker compose up --build` (backend 8000, frontend 8501, optional Redis 6379)
- Tests: `pytest` (markers: `unit`, `integration`, `e2e`, `critical`; see `pytest.ini` and [tests/README.md](tests/README.md))
  - Integration/e2e require Docker running (`docker compose up -d`)
- Debug/health checks: `python debug_tool.py` (and subcommands in [debug_archive/README.md](debug_archive/README.md))

## Project-specific conventions
- `date_time` is parsed and normalized to America/New_York in `prediction_router.py`.
- Backend logs suppress `/health` noise and write to `logs/app.log` (`backend/main.py`).
- Frontend expects both legacy and wrapped response formats; keep response shape stable (`FrontendDataValidator` in `frontend/enhanced_data_validation.py`).
- Dense LiDAR pre-scan, declustering, and NDVI trend features are first-class; keep shortlist + refinement outputs in the prediction payload (see [README.md](README.md)).
- RUT stand logic prioritizes bedding proximity + wind/thermal alignment + corridor concentration (pinch points/saddles/benches/funnels) over feeding-only signals.
- Max-accuracy UI is in Property Hotspots: check “Use Max Accuracy pipeline” to run `/property-hotspots/max-accuracy/run`, then refresh to fetch `/property-hotspots/max-accuracy/report/{job_id}`.
- Max-accuracy report persistence lives under `data/max_accuracy_jobs/` (override with `MAX_ACCURACY_JOBS_DIR`).

## External integrations & data
- GEE credentials must live at `credentials/gee-service-account.json` and are mounted read-only in Docker; set `GOOGLE_APPLICATION_CREDENTIALS` and `GEE_PROJECT_ID` (see [credentials/README.md](credentials/README.md)).
- Weather uses OpenWeatherMap API key in `.env` (`OPENWEATHERMAP_API_KEY`).
- Local LiDAR files live under `data/lidar/raw/vermont/` (legacy `data/lidar/vermont/`).
- Test data/fixtures live in `tests/fixtures/`.

## Where to look first
- API entry: `backend/main.py` and routers in `backend/routers/`.
- Core prediction logic: `backend/services/prediction_service.py` and `enhanced_bedding_zone_predictor.py`.
- Frontend map/presentation: `frontend/app.py`.
