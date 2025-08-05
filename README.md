
# Whitetail Deer Movement Predictor

This web application predicts whitetail deer movement patterns based on user-selected locations, time, season, and environmental data.

## Features

- **Interactive Map:** Select a location by dropping a pin.
- **Dynamic Predictions:** Get movement predictions based on date, time, and season.
- **Visual Overlays:** View predicted travel corridors, bedding zones, and feeding areas.
- **Stand Rating:** A 0-10 score to quickly assess a location's potential.
- **Weather Integration:** Real-time weather data from OpenWeatherMap.
- **Terrain Analysis:** Uses the Open-Elevation API for terrain data.

## Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** Python, Streamlit
- **Mapping:** Folium
- **Data:** Pandas, GeoPandas
- **Deployment:** Docker

## Setup and Running

### Prerequisites

- Docker and Docker Compose
- An OpenWeatherMap API key

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd deer-movement-predictor
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenWeatherMap API key
   ```

3. **Deploy with Docker (Development):**
   ```bash
   # Using PowerShell on Windows:
   .\deploy.ps1 dev
   
   # Or using traditional docker-compose:
   docker-compose up --build
   ```

4. **Deploy for Production:**
   ```bash
   # Using PowerShell on Windows:
   .\deploy.ps1 prod
   
   # Or using docker-compose:
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
   ```

5. **Access the application:**
   - **Frontend (Streamlit):** [http://localhost:8501](http://localhost:8501)
   - **Backend API Docs (FastAPI):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

### Docker Commands

```bash
# Check deployment status
.\deploy.ps1 status

# View logs
.\deploy.ps1 logs

# Cleanup containers
.\deploy.ps1 cleanup

# Manual commands
docker-compose ps                    # Check container status
docker-compose logs -f              # Follow logs
docker-compose exec backend bash    # Access backend container
```

### Monitoring (Optional)

Start monitoring stack:
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

Access monitoring:
- **Prometheus:** [http://localhost:9090](http://localhost:9090)
- **Grafana:** [http://localhost:3000](http://localhost:3000) (admin/admin123)
- **cAdvisor:** [http://localhost:8080](http://localhost:8080)

## Future Enhancements

- **Machine Learning:** Integrate a machine learning model (e.g., Random Forest) to improve prediction accuracy.
- **More Data Sources:** Add more data layers like vegetation from Google Earth Engine.
- **User Accounts:** Allow users to save and manage their favorite locations.
