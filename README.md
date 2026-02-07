# 🦌 Deer Prediction App

**LiDAR-powered mature buck stand placement for Vermont whitetail hunting.**

A Streamlit + FastAPI application that uses high-resolution LiDAR terrain data, Google Earth Engine vegetation analysis, and deer behavior modeling to recommend optimal treestand locations across your hunting property.

---

## How It Works

The **Max Accuracy pipeline** scans your entire property boundary using Vermont's statewide 0.7m DEM:

1. **Dense LiDAR grid** — samples terrain every 20m across the property (~12,000+ candidates)
2. **Terrain scoring** — slopes, benches, saddles, ridgelines, corridors, shelter, aspect, roughness, drainage
3. **Bedding zone identification** — strict mature buck criteria (shelter ≥ 0.58, bench ≥ 0.65, slope 7–15°, roughness ≥ 3.0, upper 60% elevation)
4. **GEE canopy/NDVI enrichment** — top candidates get satellite vegetation data from Google Earth Engine
5. **Behavior blending** — 50/50 terrain + behavior score (saddle/bench/corridor/ridgeline features)
6. **Bedding proximity scoring** — 70% distance + 30% bedding quality blend
7. **Quadrant diversity** — ensures stands are spread across the property
8. **Final ranking** — top 20 stand recommendations with coordinates, scores, and terrain feature badges

Typical run: **~75–80 seconds** for a full property scan.

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Vermont statewide DEM file (`STATEWIDE_2013-2017_70cm_DEMHF.tif`) mounted at `data/lidar/raw/vermont/`
- Google Earth Engine service account credentials (see [credentials/README.md](credentials/README.md))
- OpenWeatherMap API key

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your keys:
#   OPENWEATHERMAP_API_KEY=your_key
#   GOOGLE_APPLICATION_CREDENTIALS=credentials/gee-service-account.json
#   GEE_PROJECT_ID=your_project_id
#   APP_PASSWORD=your_password
```

### Docker (Recommended)

```bash
docker compose up --build -d
```

- **Frontend:** http://localhost:8501
- **API docs:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

### Local Development

```bash
# Terminal 1 — backend
python backend/main.py

# Terminal 2 — frontend
streamlit run frontend/app.py
```

---

## Project Structure

```
deer_pred_app/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── max_accuracy/              # Max accuracy pipeline
│   │   ├── pipeline.py            # Pipeline orchestrator
│   │   ├── config.py              # MaxAccuracyConfig dataclass
│   │   ├── terrain_metrics.py     # Bench/saddle/corridor/ridgeline detection
│   │   ├── grid.py                # Dense LiDAR grid generation
│   │   ├── gee.py                 # Google Earth Engine canopy/NDVI
│   │   ├── behavior.py            # Deer behavior scoring
│   │   └── wind.py                # Wind offset calculations
│   ├── routers/
│   │   ├── max_accuracy_router.py # /property-hotspots/max-accuracy/* endpoints
│   │   ├── scouting_router.py     # Field observation CRUD
│   │   ├── config_router.py       # Runtime config
│   │   └── camera_router.py       # Trail camera recommendations
│   ├── services/
│   │   ├── lidar/                 # LiDAR processor (DEM tile reading)
│   │   └── gee/                   # GEE authentication & data
│   └── config_manager.py          # YAML config loader
├── frontend/
│   └── app.py                     # Streamlit UI
├── config/
│   ├── defaults.yaml              # Default configuration
│   ├── development.yaml
│   ├── testing.yaml
│   └── production.yaml
├── credentials/
│   ├── README.md
│   └── gee-service-account.json.template
├── data/
│   ├── lidar/raw/vermont/         # DEM file (not in git — 55 GB)
│   └── max_accuracy_jobs/         # Persisted job reports
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Frontend Tabs

| Tab | Purpose |
|-----|---------|
| **🎯 Max Accuracy Analysis** | Primary tab — run property scans, view stand rankings, interactive map |
| **🔍 Scouting Data** | Log field observations (rubs, scrapes, trails, sightings) |
| **📊 Analytics** | Scouting data trends and patterns |

### Max Accuracy UI Features

- **Rut phase banner** — color-coded header showing current rut phase with date context
- **Top stand hero card** — 5-column metrics (score/terrain/behavior/slope/elevation), terrain feature badges, bedding proximity
- **Stand comparison table** — top 10 ranked with score bars and feature badges
- **Stand detail inspector** — full terrain score breakdown with bars, metrics, and canopy/NDVI data
- **Interactive map** — color-coded rank markers, stand-to-bedding dashed lines, bedding zone circles with hover coordinates, layer toggle, legend overlay
- **Bedding zone summary** — sortable list with quality scores and coordinates
- **Configurable settings** — grid spacing, max candidates, GEE sample K, behavior weight, TPI windows, top K stands, wind offset, min per quadrant

---

## API Endpoints

### Max Accuracy Pipeline

```bash
# Start a property scan (returns job_id)
POST /property-hotspots/max-accuracy/run
{
  "corners": [
    {"lat": 43.319, "lon": -73.231},
    {"lat": 43.322, "lon": -73.204},
    {"lat": 43.299, "lon": -73.211},
    {"lat": 43.300, "lon": -73.240}
  ],
  "date_time": "2025-10-15T10:30:00Z",
  "season": "rut",
  "hunting_pressure": "high",
  "config": {
    "grid_spacing_m": 20,
    "max_candidates": 20000,
    "top_k_stands": 20
  }
}

# Get report
GET /property-hotspots/max-accuracy/report/{job_id}
```

### Scouting

```bash
POST /scouting/add_observation    # Log a field observation
GET  /scouting/observations       # List observations
GET  /scouting/analytics          # Scouting trends
GET  /scouting/types              # Observation type definitions
```

### System

```bash
GET  /health                      # Health check
GET  /config                      # Current runtime config
```

---

## Configuration

### Pipeline Defaults

| Setting | Default | Description |
|---------|---------|-------------|
| `grid_spacing_m` | 20 | LiDAR sample spacing (meters) |
| `max_candidates` | 20,000 | Candidate pool size |
| `top_k_stands` | 20 | Number of stand recommendations |
| `gee_sample_k` | 100 | Candidates enriched with GEE data |
| `behavior_weight` | 0.50 | Terrain vs behavior blend |
| `tile_size_px` | 512 | DEM tile size (resilient to corrupted blocks) |
| `min_per_quadrant` | 1 | Minimum stands per property quadrant |
| `bedding_min_bench` | 0.65 | Bench score threshold for bedding |
| `bedding_min_shelter` | 0.58 | Shelter score threshold for bedding |
| `bedding_slope_min/max` | 7–15° | Slope range for bedding zones |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENWEATHERMAP_API_KEY` | Yes | Weather data API key |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | Path to GEE service account JSON |
| `GEE_PROJECT_ID` | Yes | Google Earth Engine project ID |
| `APP_PASSWORD` | No | Frontend password protection |
| `BACKEND_URL` | No | Backend URL for frontend (default: `http://backend:8000`) |
| `MAX_ACCURACY_JOBS_DIR` | No | Report persistence directory |
| `LOG_LEVEL` | No | Logging level (default: `INFO`) |

---

## Docker

Three containers:

| Container | Port | Purpose |
|-----------|------|---------|
| `backend` | 8000 | FastAPI + LiDAR + GEE |
| `frontend` | 8501 | Streamlit UI |
| `redis` | 6379 | Response caching |

The 55 GB DEM file is volume-mounted read-only from the host (not copied into the image):
```yaml
volumes:
  - ./data/lidar/raw/vermont:/app/data/lidar/raw/vermont:ro
```

---

## Terrain Scoring Weights

| Feature | Weight | What it detects |
|---------|--------|-----------------|
| Slope preference | 18% | 5–22° plateau scoring |
| Bench | 14% | Sidehill benches — prime bedding |
| Saddle | 14% | Terrain funnels — proven travel corridors |
| Elevation preference | 12% | Ridge proximity (upper third) |
| Corridor | 8% | General travel corridor |
| Shelter | 8% | Wind/thermal protection |
| Aspect | 8% | South/SE facing thermal advantage |
| Roughness | 6% | Terrain texture (not flat field) |
| Curvature | 4% | Terrain shape |
| Ridgeline | 4% | Ridge spine travel |
| Drainage | 4% | Drainage funnel travel |

---

## Tests

```bash
pytest -m unit           # Unit tests
pytest -m integration    # Integration tests (requires Docker)
pytest -m e2e            # End-to-end tests (requires Docker)
```

See [pytest.ini](pytest.ini) for markers and configuration.

---

## Security

- `.env` is in `.gitignore` — API keys never committed
- GEE credentials directory ignores all JSON except templates
- Frontend supports optional password protection via `APP_PASSWORD`
- No secrets are hardcoded in source code

---

## Tech Stack

- **Backend:** Python 3.10, FastAPI, Uvicorn
- **Frontend:** Streamlit, Folium (interactive maps)
- **Terrain:** Rasterio, NumPy, SciPy (LiDAR DEM processing)
- **Vegetation:** Google Earth Engine (Sentinel-2 canopy/NDVI)
- **Weather:** OpenWeatherMap API
- **Cache:** Redis
- **Deployment:** Docker Compose

---

**Primary entrypoints:** [backend/main.py](backend/main.py) · [frontend/app.py](frontend/app.py) · [backend/max_accuracy/pipeline.py](backend/max_accuracy/pipeline.py)
