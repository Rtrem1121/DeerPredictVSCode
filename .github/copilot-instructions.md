# Copilot Instructions (deer_pred_app)

## Big picture architecture
- Backend is a FastAPI app in `backend/main.py`, composed of routers (e.g., `backend/routers/prediction_router.py`) that call service-layer logic.
- Service layer uses a lightweight DI container (`backend/services/service_container.py`), with singletons for terrain, weather, scouting, async HTTP, Redis cache, and async prediction.
- The prediction pipeline runs through `backend/services/prediction_service.py`, which **always** uses `EnhancedBeddingZonePredictor` (see `enhanced_bedding_zone_predictor.py`) and converts numpy types via `convert_numpy_types` before returning JSON.
- Frontend is Streamlit (`frontend/app.py`) and calls backend `/predict` and `/analyze-prediction-detailed`; it also performs backend↔frontend data validation via `frontend/enhanced_data_validation.py`.
- Configuration is YAML-based: `config/defaults.yaml` + `config/{development,testing,production}.yaml`, loaded/validated by `backend/config_manager.py` with optional hot-reload (watchdog).

## Key workflows (actual commands)
- Local backend: `python backend/main.py`
- Local frontend: `streamlit run frontend/app.py`
- Docker stack: `docker compose up --build` (backend 8000, frontend 8501, optional Redis 6379)
- Tests: `pytest` (markers: `unit`, `integration`, `e2e`, `critical`; see `pytest.ini` and `tests/README.md`)
  - Integration/e2e require Docker running (`docker compose up -d`)

## Project-specific conventions
- Prediction API parses `date_time` and normalizes to America/New_York timezone (see `prediction_router.py`).
- Backend logs suppress `/health` noise and writes to `logs/app.log` (see `backend/main.py`).
- Frontend expects both legacy and wrapped response formats; keep response shape stable (see `FrontendDataValidator` in `frontend/enhanced_data_validation.py`).

## External integrations & data
- GEE credentials must live at `credentials/gee-service-account.json` and are mounted read-only in Docker; set `GOOGLE_APPLICATION_CREDENTIALS` and `GEE_PROJECT_ID` (see `credentials/README.md` and `docker-compose.yml`).
- Weather uses OpenWeatherMap API key in `.env` (`OPENWEATHERMAP_API_KEY`).
- Data files and fixtures live under `data/`, `backend/data/`, and `tests/fixtures/`.

## Where to look first
- API entry: `backend/main.py` and routers in `backend/routers/`.
- Core prediction logic: `backend/services/prediction_service.py` and `enhanced_bedding_zone_predictor.py`.
- Frontend map/presentation logic: `frontend/app.py`.
