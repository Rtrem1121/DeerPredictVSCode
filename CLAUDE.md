# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

LiDAR-driven mature-buck stand recommender for Vermont whitetail hunting. FastAPI backend + Streamlit frontend. The production code path is the **max-accuracy pipeline** — most other prediction modules in `backend/` (`mature_buck_predictor.py`, `enhanced_prediction_*`, etc.) are legacy/auxiliary.

## Common Commands

```bash
# Stack (preferred — backend needs the 55 GB DEM volume mount)
docker compose up --build -d           # backend:8000, frontend:8501, redis:6379
docker compose logs -f backend
docker compose down

# Local dev (no DEM access — most pipeline runs will fail)
python backend/main.py                 # backend
streamlit run frontend/app.py          # frontend

# Tests (see pytest.ini for markers)
pytest -m unit
pytest -m integration                  # requires `docker compose up -d`
pytest -m e2e                          # requires `docker compose up -d`
pytest -m critical                     # must pass before deployment
pytest tests/unit/test_aspect_scorer.py::TestAspectScorer::test_X   # single test
pytest --cov=backend --cov-report=html # coverage HTML in htmlcov/

# Lint / format (line length 120)
make lint        # flake8 backend/ frontend/
make format      # black backend/ frontend/
```

CI lives in `.github/workflows/` (`test.yml`, `ci-cd.yml`, `frontend-validation.yml`).

## Required Environment

`.env` (copy from `.env.example`) must define:
- `OPENWEATHERMAP_API_KEY` — weather
- `GOOGLE_APPLICATION_CREDENTIALS=credentials/gee-service-account.json` — GEE auth
- `GEE_PROJECT_ID` — Earth Engine project
- DEM file present at `data/lidar/raw/vermont/STATEWIDE_2013-2017_70cm_DEMHF.tif` (55 GB, not in git, volume-mounted read-only into the container)

Optional: `APP_PASSWORD`, `BACKEND_URL`, `MAX_ACCURACY_JOBS_DIR`, `LOG_LEVEL`.

## Architecture

### Two parallel prediction stacks
There are two prediction code paths in this repo. Know which one you're touching:

1. **Max-accuracy pipeline** (current production path). Self-contained in [backend/max_accuracy/](backend/max_accuracy/) and exposed by [backend/routers/max_accuracy_router.py](backend/routers/max_accuracy_router.py). Drives the primary Streamlit tab.
2. **Legacy enhanced predictor** ([enhanced_bedding_zone_predictor.py](enhanced_bedding_zone_predictor.py) at repo root, called via [backend/services/prediction_service.py](backend/services/prediction_service.py) and `EnhancedBeddingZonePredictor`). Still wired into `enhanced_endpoints.py` and the older hotspot router. New work should go through the max-accuracy pipeline unless you are explicitly maintaining the legacy path.

The legacy path is mounted into the Docker container as **read-only individual files** (see `docker-compose.yml` lines 19–24) so root-level Python files like `enhanced_bedding_zone_predictor.py` reload without rebuilding the image.

### Max-accuracy pipeline data flow
`POST /property-hotspots/max-accuracy/run` → [pipeline.py](backend/max_accuracy/pipeline.py) `MaxAccuracyPipeline.run()`:

1. **Dense grid** ([grid.py](backend/max_accuracy/grid.py)) — ~20 m spacing across the property polygon (~12k+ candidates typical).
2. **Terrain metrics** ([terrain_metrics.py](backend/max_accuracy/terrain_metrics.py)) — slope, aspect, roughness, curvature, TPI/bench, saddle, corridor, ridgeline, drainage, shelter. Reads DEM tiles via `backend/services/lidar_processor.py` (`DEMFileManager`). Tiling defaults to 512 px tiles for resilience to corrupted DEM blocks (see `MaxAccuracyConfig.tile_size_px`).
3. **Bedding identification** — strict mature-buck thresholds in `MaxAccuracyConfig` (`bedding_min_shelter=0.58`, `bedding_min_bench=0.65`, slope 7–15°, roughness ≥ 3.0, upper 60% elevation).
4. **GEE enrichment** ([gee.py](backend/max_accuracy/gee.py)) — top `gee_sample_k` candidates only; concurrent requests capped at `_GEE_MAX_WORKERS=8`.
5. **Behavior blend** ([behavior.py](backend/max_accuracy/behavior.py)) — 50/50 terrain + behavior by default (`behavior_weight=0.50`).
6. **Bedding proximity scoring** — 70% distance + 30% bedding quality.
7. **Quadrant diversity** — `min_per_quadrant` enforces spread across the polygon.
8. **Wind huntability** — `_calculate_wind_rotation()` decides which wind directions are huntable per stand based on scent vectors to nearby bedding (`scent_carry_distance` from `backend/utils/terrain_scoring.py`).
9. **Persist** — JSON report under `data/max_accuracy_jobs/{job_id}/` (override with `MAX_ACCURACY_JOBS_DIR`); `_cleanup_old_jobs` deletes job dirs > 7 days old.

The pipeline uses `ThreadPoolExecutor` for both tile metric computation and GEE enrichment.

### Service layer
DI is a hand-rolled container in [backend/services/service_container.py](backend/services/service_container.py) wiring terrain, weather, scouting, async HTTP, Redis cache, and async prediction. The legacy `PredictionService` always runs through `EnhancedBeddingZonePredictor` and applies `convert_numpy_types` before returning JSON.

### Corridor engine
[backend/corridor/](backend/corridor/) provides `CorridorEngine` (cost-surface least-cost-path between bedding and feeding/stand candidates). Imported by the max-accuracy pipeline for travel-corridor reasoning.

### Configuration
- Runtime config: YAML in [config/](config/) (`defaults.yaml` + per-environment overrides), loaded by [backend/config_manager.py](backend/config_manager.py). Optional hot-reload via `watchdog`.
- Pipeline config: [`MaxAccuracyConfig`](backend/max_accuracy/config.py) dataclass, overridable via the `config` field on `POST /property-hotspots/max-accuracy/run` (validated by `MaxAccuracyConfigOverrides` in the router).
- Terrain feature weights live on `MaxAccuracyConfig.weights` — change them there, not in scoring code.

### Frontend
Single-page Streamlit app in [frontend/app.py](frontend/app.py). The "Max Accuracy Analysis" tab calls `POST /property-hotspots/max-accuracy/run`, polls `GET /property-hotspots/max-accuracy/report/{job_id}`, and renders Folium maps + ranked stand cards. `frontend/enhanced_data_validation.py` (`FrontendDataValidator`) handles both legacy and wrapped response shapes — keep response shape stable when modifying responses.

### Logging
`backend/main.py` filters `/health` out of uvicorn access logs and writes to `logs/app.log`. The `logs/` directory is intentionally untracked.

## Conventions

- `date_time` is ISO-8601 with timezone; the legacy `prediction_router.py` normalizes to America/New_York. Max-accuracy router takes the string as-is and passes it to the rut classifier (`classify_rut_phase`).
- Numpy types must be converted before JSON serialization on the legacy path (`convert_numpy_types`); the max-accuracy pipeline returns plain Python via `dataclasses.asdict` and explicit casts.
- Tests are organized by marker, not just folder. Always tag new tests (`@pytest.mark.unit` etc.) — the CI matrix selects by marker.
- Quarantined code lives under `archive/`, `debug_archive/`, and `dead_code_backups/` — `pytest.ini` excludes these from collection. Do not add new code there.
- Code under `backend/` is bind-mounted (`./backend:/app/backend`); edits take effect on backend restart without a rebuild. Root-level `*.py` files are **not** bind-mounted — they are baked in via `COPY` at image build time (see `docker-compose.yml`).

## Where things live

| Need | File |
|---|---|
| API entry / router wiring | [backend/main.py](backend/main.py) |
| Max-accuracy endpoints | [backend/routers/max_accuracy_router.py](backend/routers/max_accuracy_router.py) |
| Max-accuracy orchestration | [backend/max_accuracy/pipeline.py](backend/max_accuracy/pipeline.py) |
| Pipeline tunables | [backend/max_accuracy/config.py](backend/max_accuracy/config.py) |
| DEM I/O | [backend/services/lidar_processor.py](backend/services/lidar_processor.py) |
| Legacy prediction path | [backend/services/prediction_service.py](backend/services/prediction_service.py) + [enhanced_bedding_zone_predictor.py](enhanced_bedding_zone_predictor.py) |

## Known architectural debt

- **`enhanced_bedding_zone_predictor.py` (~4 100 lines, root-level)** — monolith with an inverted import direction (root file imports from `backend/`). No quick fix; decompose incrementally by extracting cohesive sub-modules into `backend/`. Do not add new logic to this file; prefer `backend/max_accuracy/` for new features.
| Frontend | [frontend/app.py](frontend/app.py) |
| Architecture deep-dive | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Test layout | [tests/README.md](tests/README.md) |
